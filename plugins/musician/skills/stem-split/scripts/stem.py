#!/usr/bin/env python3
"""유튜브 주소나 로컬 오디오 파일에서 demucs 로 원하는 악기 소리를 뽑거나 뺀다.

사용법:
  python3 stem.py check
  python3 stem.py run <유튜브 주소|오디오 파일> [--stem 이름 ...] [--minus]
                      [--quality normal|high] [--model 이름]
                      [--format mp3|wav|flac] [--bitrate 320]
                      [--out 폴더] [--keep-all] [--max-minutes 20]

진행 기록은 표준 오류로, 결과는 표준 출력 마지막 줄에 JSON 한 줄로 낸다.
종료 코드: 0 성공, 1 실행 실패, 2 필요한 도구 없음, 3 입력 오류.
표준 라이브러리만 쓴다. yt-dlp 와 demucs 는 명령으로 부른다.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STEMS_4 = ("vocals", "drums", "bass", "other")
STEMS_6 = STEMS_4 + ("guitar", "piano")
SIX_ONLY = ("guitar", "piano")
DEFAULT_OUT = Path.home() / "Music" / "musician"
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

QUALITY_NOTES = {
    "guitar": "guitar 는 6 stem 모델로 분리하며 품질이 보통이다. 다른 악기가 조금 섞일 수 있다.",
    "piano": "piano 는 6 stem 모델로 분리하며 번짐과 잡음이 많다.",
    "other": "other 는 보컬, 드럼, 베이스(6 stem 이면 기타, 피아노)를 뺀 나머지 전부가 섞인 소리다.",
}


def log(message: str) -> None:
    print(f"[stem] {message}", file=sys.stderr, flush=True)


def emit(result: dict, code: int) -> None:
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(code)


def fail(code: int, error: str, **extra) -> None:
    emit({"ok": False, "error": error, **extra}, code)


# ---------------------------------------------------------------- 도구 점검

def probe(command: str, args: list[str]) -> dict | None:
    path = shutil.which(command)
    if not path:
        return None
    if not args:
        return {"path": path}
    try:
        done = subprocess.run([path, *args], capture_output=True, text=True, timeout=30)
        lines = (done.stdout or done.stderr).strip().splitlines()
        return {"path": path, "version": lines[0] if lines else ""}
    except (OSError, subprocess.TimeoutExpired):
        return {"path": path, "version": ""}


def detect_tools() -> dict:
    return {
        "yt-dlp": probe("yt-dlp", ["--version"]),
        "ffmpeg": probe("ffmpeg", ["-version"]),
        "deno": probe("deno", ["--version"]),
        "node": probe("node", ["--version"]),
        # demucs 는 버전 확인에 torch 를 읽어 느리므로 경로만 본다.
        "demucs": probe("demucs", []),
    }


def install_hints(missing: list[str]) -> dict:
    system = platform.system()
    if system == "Darwin":
        table = {
            "yt-dlp": "brew install yt-dlp  (deno 도 함께 설치된다)",
            "ffmpeg": "brew install ffmpeg",
            "js-runtime": "brew install deno",
            "demucs": "uv tool install demucs --with numpy  (uv 가 없으면 brew install uv)",
        }
    elif system == "Windows":
        table = {
            "yt-dlp": 'uv tool install "yt-dlp[default]"  (uv 가 없으면 winget install astral-sh.uv)',
            "ffmpeg": "winget install Gyan.FFmpeg",
            "js-runtime": "winget install DenoLand.Deno",
            "demucs": "uv tool install demucs --with numpy",
        }
    else:
        table = {
            "yt-dlp": 'uv tool install "yt-dlp[default]"',
            "ffmpeg": "배포판 패키지 관리자로 설치 (예: sudo apt install ffmpeg)",
            "js-runtime": "curl -fsSL https://deno.land/install.sh | sh",
            "demucs": "uv tool install demucs --with numpy",
        }
    return {name: table[name] for name in missing}


def missing_tools(tools: dict, need_download: bool, fmt: str) -> list[str]:
    missing = []
    if need_download:
        if not tools["yt-dlp"]:
            missing.append("yt-dlp")
        if not tools["ffmpeg"]:
            missing.append("ffmpeg")
        if not (tools["deno"] or tools["node"]):
            missing.append("js-runtime")
    if fmt == "flac" and not tools["ffmpeg"] and "ffmpeg" not in missing:
        missing.append("ffmpeg")
    if not tools["demucs"]:
        missing.append("demucs")
    return missing


def js_runtime_args(tools: dict) -> list[str]:
    # yt-dlp 는 deno 만 기본으로 켠다. deno 가 없고 node 만 있으면 node 를 직접 켠다.
    if tools["deno"]:
        return []
    if tools["node"]:
        return ["--js-runtimes", "node"]
    return []


def cmd_check() -> None:
    tools = detect_tools()
    missing = missing_tools(tools, need_download=True, fmt="mp3")
    if not tools["ffmpeg"] and "ffmpeg" not in missing:
        missing.append("ffmpeg")
    result = {
        "ok": not missing,
        "tools": tools,
        "js_runtime": "deno" if tools["deno"] else ("node" if tools["node"] else None),
        "missing": missing,
        "install": install_hints(missing),
    }
    emit(result, 0 if not missing else 2)


# ---------------------------------------------------------------- 입력 준비

def slugify(text: str, limit: int = 60) -> str:
    text = re.sub(r"[^\w\-]+", "-", text).strip("-_")
    text = re.sub(r"-{2,}", "-", text)
    return text[:limit].rstrip("-_") or "track"


def run_logged(cmd: list[str]) -> int:
    log("실행: " + " ".join(cmd))
    sys.stderr.flush()
    # 하위 명령의 출력은 모두 표준 오류로 보내 표준 출력에는 결과 JSON 만 남긴다.
    return subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr).returncode


def fetch_metadata(url: str, tools: dict) -> dict:
    cmd = [tools["yt-dlp"]["path"], "--no-playlist", "--skip-download", "-J",
           *js_runtime_args(tools), url]
    log("영상 정보 확인: " + url)
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        fail(1, "영상 정보를 가져오지 못했다.",
             detail=done.stderr.strip().splitlines()[-5:],
             hint="주소를 확인하고, yt-dlp 를 최신으로 올린다(brew upgrade yt-dlp 또는 uv tool upgrade yt-dlp). "
                  "JS 런타임(deno)이 없으면 설치한다.")
    return json.loads(done.stdout)


def prepare_download(url: str, out: Path, max_minutes: float, tools: dict) -> tuple[Path, Path, dict, bool]:
    info = fetch_metadata(url, tools)
    if info.get("_type") == "playlist":
        fail(3, "재생목록은 지원하지 않는다. 영상 하나의 주소를 준다.")
    if info.get("is_live") or info.get("live_status") in ("is_live", "is_upcoming"):
        fail(3, "라이브 방송이나 예정된 방송은 내려받지 않는다.")
    duration = info.get("duration") or 0
    if max_minutes > 0 and duration > max_minutes * 60:
        fail(3, f"영상 길이가 {duration / 60:.1f}분으로 제한 {max_minutes:g}분을 넘는다.",
             duration_sec=duration,
             hint="정말 처리할 영상이면 --max-minutes 를 늘리거나 0 으로 주고 다시 실행한다.")

    folder = out / f"{slugify(info.get('title') or 'track')}-{info.get('id', 'unknown')}"
    folder.mkdir(parents=True, exist_ok=True)
    meta = {
        "source_type": "youtube",
        "url": url,
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "duration_sec": duration,
    }

    source = folder / "source.wav"
    if source.exists():
        log(f"이미 받은 음원을 다시 쓴다: {source}")
        return folder, source, meta, False

    cmd = [tools["yt-dlp"]["path"], "--no-playlist", "-f", "bestaudio/best",
           "-x", "--audio-format", "wav", "-o", str(folder / "source.%(ext)s"),
           *js_runtime_args(tools), url]
    if run_logged(cmd) != 0 or not source.exists():
        fail(1, "음원을 내려받지 못했다.",
             hint="yt-dlp 를 최신으로 올리고 다시 시도한다. 연령 제한이나 지역 제한 영상은 받을 수 없다.")
    return folder, source, meta, True


def prepare_local(path_text: str, out: Path) -> tuple[Path, Path, dict, bool]:
    source = Path(path_text).expanduser().resolve()
    if not source.is_file():
        fail(3, f"오디오 파일을 찾을 수 없다: {source}")
    folder = out / slugify(source.stem)
    folder.mkdir(parents=True, exist_ok=True)
    meta = {"source_type": "file", "path": str(source), "title": source.name}
    return folder, source, meta, False


# ---------------------------------------------------------------- 분리

def choose_model(stems: list[str], quality: str, model: str | None) -> tuple[str, list[str]]:
    notes = []
    wants_six = any(s in SIX_ONLY for s in stems)
    if model:
        if wants_six and not model.endswith("_6s"):
            fail(3, f"{', '.join(s for s in stems if s in SIX_ONLY)} 는 6 stem 모델(htdemucs_6s)에서만 나온다.")
        return model, notes
    if wants_six:
        if quality == "high":
            notes.append("--quality high 는 6 stem 모델에는 적용되지 않는다. htdemucs_6s 로 분리했다.")
        return "htdemucs_6s", notes
    return ("htdemucs_ft" if quality == "high" else "htdemucs"), notes


def separate(source: Path, work: Path, model: str, minus_stem: str | None,
             fmt: str, bitrate: int, demucs_path: str) -> bool:
    """demucs 를 돌린다. 기본 장치로 실패하면 CPU 로 한 번 더 시도한다. CPU 로 다시 했는지 돌려준다."""
    base = [demucs_path, "-n", model, "-o", str(work), "--filename", "{stem}.{ext}"]
    if minus_stem:
        base += ["--two-stems", minus_stem]
    if fmt == "mp3":
        base += ["--mp3", "--mp3-bitrate", str(bitrate)]
    elif fmt == "flac":
        base += ["--flac"]

    if run_logged([*base, str(source)]) == 0:
        return False
    log("기본 장치로 실패해서 CPU 로 다시 시도한다.")
    shutil.rmtree(work, ignore_errors=True)
    if run_logged([*base, "-d", "cpu", str(source)]) == 0:
        return True
    fail(1, "demucs 분리에 실패했다.",
         hint="위 표준 오류 기록을 확인한다. 처음 실행이면 모델 내려받기에 네트워크가 필요하다. "
              "numpy 가 없다는 오류면 uv tool install --force demucs --with numpy 로 다시 설치한다.")
    return True


def cmd_run(args: argparse.Namespace) -> None:
    requested = list(dict.fromkeys(args.stem or []))
    stems = list(requested)
    if args.minus and len(stems) != 1:
        fail(3, "--minus 는 뺄 악기를 --stem 으로 하나만 준다.")

    model, notes = choose_model(stems, args.quality, args.model)
    available = STEMS_6 if model.endswith("_6s") else STEMS_4
    if not stems:
        stems = list(available)
    unknown = [s for s in stems if s not in available]
    if unknown:
        fail(3, f"{model} 모델에 없는 악기다: {', '.join(unknown)}", available=list(available))

    is_url = bool(URL_RE.match(args.input))
    tools = detect_tools()
    missing = missing_tools(tools, need_download=is_url, fmt=args.format)
    if missing:
        fail(2, "필요한 도구가 없다.", missing=missing, install=install_hints(missing))

    out = Path(args.out).expanduser().resolve()
    if is_url:
        folder, source, meta, downloaded = prepare_download(args.input, out, args.max_minutes, tools)
    else:
        folder, source, meta, downloaded = prepare_local(args.input, out)

    work = folder / "_work"
    shutil.rmtree(work, ignore_errors=True)
    started = time.monotonic()
    log(f"분리 시작: 모델 {model}, 형식 {args.format}")
    cpu_retry = separate(source, work, model, stems[0] if args.minus else None,
                         args.format, args.bitrate, tools["demucs"]["path"])
    elapsed = round(time.monotonic() - started, 1)

    produced = work / model
    wanted = [f"no_{stems[0]}"] if args.minus else stems
    outputs = []
    for name in wanted:
        src = produced / f"{name}.{args.format}"
        if not src.exists():
            fail(1, f"demucs 결과에 {src.name} 가 없다.", produced=[p.name for p in produced.glob("*")])
        dst = folder / src.name
        src.replace(dst)
        outputs.append(str(dst))

    all_dir = None
    if args.keep_all and any(produced.iterdir()):
        all_dir = folder / "_all"
        shutil.rmtree(all_dir, ignore_errors=True)
        produced.replace(all_dir)
    shutil.rmtree(work, ignore_errors=True)

    if args.minus:
        notes.append(f"no_{stems[0]} 는 원곡에서 {stems[0]} 를 뺀 소리다.")
    notes += [QUALITY_NOTES[s] for s in requested if s in QUALITY_NOTES and not args.minus]
    if cpu_retry:
        notes.append("GPU 에서 실패해 CPU 로 분리했다. Apple Silicon 에서 torch 가 오래됐으면 "
                     "uv tool install --force demucs --with numpy 로 다시 설치해 GPU 를 쓸 수 있다.")

    meta.update({
        "model": model,
        "stems": stems,
        "minus": args.minus,
        "format": args.format,
        "mp3_bitrate": args.bitrate if args.format == "mp3" else None,
        "outputs": outputs,
        "all_stems_dir": str(all_dir) if all_dir else None,
        "elapsed_sec": elapsed,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    emit({
        "ok": True,
        "folder": str(folder),
        "source": str(source),
        "downloaded": downloaded,
        "model": model,
        "format": args.format,
        "outputs": outputs,
        "all_stems_dir": str(all_dir) if all_dir else None,
        "elapsed_sec": elapsed,
        "notes": notes,
    }, 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="유튜브 주소나 오디오 파일에서 악기 소리를 뽑거나 뺀다.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="필요한 도구가 설치됐는지 확인한다.")

    run = sub.add_parser("run", help="내려받기와 분리를 실행한다.")
    run.add_argument("input", help="유튜브 영상 주소 또는 로컬 오디오 파일 경로")
    run.add_argument("--stem", action="append", choices=STEMS_6,
                     help="뽑을 악기. 여러 번 줄 수 있다. 주지 않으면 모델의 모든 악기")
    run.add_argument("--minus", action="store_true", help="--stem 으로 준 악기 하나를 뺀 나머지를 만든다")
    run.add_argument("--quality", choices=("normal", "high"), default="normal",
                     help="high 면 htdemucs_ft 를 쓴다. 4배쯤 느리다")
    run.add_argument("--model", help="demucs 모델 이름을 직접 지정한다")
    run.add_argument("--format", choices=("mp3", "wav", "flac"), default="mp3")
    run.add_argument("--bitrate", type=int, default=320, help="mp3 비트레이트(kbps). 기본 320")
    run.add_argument("--out", default=str(DEFAULT_OUT), help=f"결과 폴더. 기본 {DEFAULT_OUT}")
    run.add_argument("--keep-all", action="store_true", help="요청하지 않은 악기도 _all 폴더에 남긴다")
    run.add_argument("--max-minutes", type=float, default=20,
                     help="이보다 긴 영상은 거부한다. 0 이면 제한 없음. 기본 20")

    args = parser.parse_args()
    if args.command == "check":
        cmd_check()
    else:
        cmd_run(args)


if __name__ == "__main__":
    main()
