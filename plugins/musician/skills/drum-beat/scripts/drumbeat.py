#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.14"
# dependencies = [
#     "beat-this>=1.1.0",
#     "torch>=2.6",
#     "torchaudio>=2.6",
#     "numpy>=2",
#     "soundfile>=0.12",
#     "scipy>=1.13",
#     "soxr>=0.5",
# ]
# ///
"""유튜브 주소나 오디오 파일에서 드럼만 분리하고, 스틱 클릭으로 카운트인과 빈 구간의 박을 넣는다.

규칙
  1. 드럼 앞에는 항상 카운트인 4박이 온전히 들어간다. 드럼이 곡 첫 박보다 먼저 들어오면(픽업) 4박씩 앞당긴다.
  2. 카운트인 뒤부터 드럼 첫 타격 직전 박까지 매 박 클릭을 넣는다. 드럼이 곡 중간에 들어와도 빈 구간을 두지 않는다.

사용법 (의존성은 uv 가 이 파일 머리말을 읽어 설치한다)
  uv run --script drumbeat.py check
  uv run --script drumbeat.py run <유튜브 주소|오디오 파일> --name "가수 - 제목"
        [--format mp3|wav|flac] [--bitrate 320] [--out 폴더]
        [--tempo-factor 0.5|2] [--shift N] [--max-minutes 20]

결과 폴더 (<out>/<제목>-<영상 ID>/, 로컬 파일은 <out>/<파일 이름>/)
  source.wav                    원곡 (stem-split 과 같은 폴더, 같은 파일을 쓴다)
  stems/htdemucs_ft/drums.wav   분리한 드럼
  beats.json                    beat_this 가 찾은 박과 마디 첫 박
  analysis.json                 BPM, 박자, 첫 박, 드럼 시작, 클릭 위치, 규칙 검사
  <가수 - 제목>(드럼).<형식>      최종 결과
  check_원곡+카운트인.mp3         원곡에 같은 클릭을 붙인 확인용
단계마다 결과가 있으면 다시 쓰므로 --tempo-factor 나 --shift 로 고쳐 다시 돌리면 금방 끝난다.

박을 잘못 잡았을 때 고치는 옵션
  --tempo-factor 0.5   BPM 이 두 배로 잡혔을 때(8분음표를 박으로 잡음)
  --tempo-factor 2     BPM 이 절반으로 잡혔을 때
  --shift N            마디 첫 박을 N 박 뒤로(음수면 앞으로) 옮긴다

진행 기록은 표준 오류로, 결과는 표준 출력 마지막 줄에 JSON 한 줄로 낸다.
종료 코드: 0 성공, 1 실행 실패, 2 필요한 도구 없음, 3 입력 오류, 4 규칙 검사 실패.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import soxr
from scipy import signal as sps

DEFAULT_OUT = Path.home() / "Music" / "musician"
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

SR = 44100            # demucs 출력 샘플레이트
MODEL = "htdemucs_ft"
COUNT_IN = 4          # 카운트인 박 수
LEAD = 1.0            # 첫 클릭 앞 여유(초)
FIT_BEATS = 16        # 곡 앞부분 템포를 맞출 때 쓰는 첫 박 이후 박 수
REFINE_BEATS = 32     # 곡 앞부분을 어택 기준으로 미세 조정할 때 쓰는 박 수
AFTER_ENTRY = 16      # 인트로 격자를 맞출 때 드럼이 들어온 뒤 더 쓰는 박 수
LOCAL_BEATS = 8       # 템포가 흔들리는 곡에서 박마다 앞뒤로 쓰는 박 수
DRUM_DB = -20.0       # 드럼 시작 판정 레벨(드럼 최대 대비). 낮추면 심벌 스웰이나 새어 들어온 소리에서 멈춘다
CLICK_GAIN = 0.8      # 드럼 최대 레벨 대비 클릭 최대 레벨
MAX_GAP_BEATS = 1.3   # 마지막 클릭과 드럼 시작 사이 허용 간격(박). 넘으면 빈 구간이 남은 것이다


def log(msg: str) -> None:
    print(f"[drumbeat] {msg}", file=sys.stderr, flush=True)


def emit(result: dict, code: int) -> None:
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(code)


def fail(code: int, error: str, **extra) -> None:
    emit({"ok": False, "error": error, **extra}, code)


def run(cmd: list[str]) -> int:
    log("실행: " + " ".join(cmd))
    sys.stderr.flush()
    # 하위 명령의 출력은 모두 표준 오류로 보내 표준 출력에는 결과 JSON 만 남긴다.
    return subprocess.run(cmd, stdout=sys.stderr, stderr=sys.stderr).returncode


# ---------------------------------------------------------------- 0. 도구 점검

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
        "demucs": probe("demucs", []),
    }


def install_hints(missing: list[str]) -> dict:
    system = platform.system()
    if system == "Darwin":
        table = {
            "yt-dlp": "brew install yt-dlp  (deno 도 함께 설치된다)",
            "ffmpeg": "brew install ffmpeg",
            "js-runtime": "brew install deno",
            "demucs": "uv tool install demucs --with numpy",
        }
    elif system == "Windows":
        table = {
            "yt-dlp": 'uv tool install "yt-dlp[default]"',
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


def missing_tools(tools: dict, need_download: bool) -> list[str]:
    missing = []
    if need_download:
        if not tools["yt-dlp"]:
            missing.append("yt-dlp")
        if not (tools["deno"] or tools["node"]):
            missing.append("js-runtime")
    # ffmpeg 는 yt-dlp 변환, 로컬 파일 변환, mp3 저장에 모두 쓴다.
    if not tools["ffmpeg"]:
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
    missing = missing_tools(tools, need_download=True)
    emit({
        "ok": not missing,
        "tools": tools,
        "js_runtime": "deno" if tools["deno"] else ("node" if tools["node"] else None),
        "missing": missing,
        "install": install_hints(missing),
    }, 0 if not missing else 2)


# ---------------------------------------------------------------- 1. 입력 준비

def slugify(text: str, limit: int = 60) -> str:
    text = re.sub(r"[^\w\-]+", "-", text).strip("-_")
    text = re.sub(r"-{2,}", "-", text)
    return text[:limit].rstrip("-_") or "track"


def output_name(name: str) -> str:
    """결과 파일 이름. '가수 - 제목' 표기를 그대로 두고 파일 이름에 못 쓰는 글자만 뺀다."""
    return re.sub(r"\s+", " ", re.sub(r"[\\/:*?\"<>|]", "", name)).strip() or "track"


def prepare_download(url: str, out: Path, max_minutes: float, tools: dict) -> tuple[Path, Path, dict, bool]:
    cmd = [tools["yt-dlp"]["path"], "--no-playlist", "--skip-download", "-J", *js_runtime_args(tools), url]
    log("영상 정보 확인: " + url)
    done = subprocess.run(cmd, capture_output=True, text=True)
    if done.returncode != 0:
        fail(1, "영상 정보를 가져오지 못했다.",
             detail=done.stderr.strip().splitlines()[-5:],
             hint="주소를 확인하고, yt-dlp 를 최신으로 올린다. JS 런타임(deno)이 없으면 설치한다.")
    info = json.loads(done.stdout)
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
    meta = {"source_type": "youtube", "url": url, "id": info.get("id"), "title": info.get("title"),
            "channel": info.get("channel") or info.get("uploader"), "duration_sec": duration}

    src = folder / "source.wav"
    if src.exists():
        log(f"원곡 재사용: {src}")
        return folder, src, meta, False
    cmd = [tools["yt-dlp"]["path"], "--no-playlist", "-f", "bestaudio/best", "-x", "--audio-format", "wav",
           "-o", str(folder / "source.%(ext)s"), *js_runtime_args(tools), url]
    if run(cmd) != 0 or not src.exists():
        fail(1, "음원을 내려받지 못했다.",
             hint="yt-dlp 를 최신으로 올리고 다시 시도한다. 연령 제한이나 지역 제한 영상은 받을 수 없다.")
    return folder, src, meta, True


def prepare_local(path_text: str, out: Path, tools: dict) -> tuple[Path, Path, dict, bool]:
    given = Path(path_text).expanduser().resolve()
    if not given.is_file():
        fail(3, f"오디오 파일을 찾을 수 없다: {given}")
    folder = out / slugify(given.stem)
    folder.mkdir(parents=True, exist_ok=True)
    meta = {"source_type": "file", "path": str(given), "title": given.stem}
    src = folder / "source.wav"
    if src.exists():
        log(f"원곡 재사용: {src}")
        return folder, src, meta, False
    # mp3, m4a 등 어떤 형식이 와도 같은 방식으로 읽도록 wav 로 바꿔 둔다.
    cmd = [tools["ffmpeg"]["path"], "-hide_banner", "-loglevel", "error", "-y", "-i", str(given),
           "-vn", "-c:a", "pcm_s16le", str(src)]
    if run(cmd) != 0 or not src.exists():
        fail(1, f"오디오 파일을 wav 로 바꾸지 못했다: {given}")
    return folder, src, meta, False


# ---------------------------------------------------------------- 2. 드럼 분리

def separate(src: Path, d: Path, demucs_path: str) -> Path:
    drums = d / "stems" / MODEL / "drums.wav"
    if drums.exists():
        log(f"드럼 재사용: {drums}")
        return drums
    base = [demucs_path, "-n", MODEL, "--float32", "--filename", "{stem}.{ext}", "-o", str(d / "stems")]
    if run([*base, str(src)]) != 0:
        log("기본 장치로 실패해서 CPU 로 다시 시도한다.")
        if run([*base, "-d", "cpu", str(src)]) != 0:
            fail(1, "demucs 분리에 실패했다.",
                 hint="표준 오류 기록을 확인한다. 처음 실행이면 모델 내려받기에 네트워크가 필요하다. "
                      "numpy 가 없다는 오류면 uv tool install --force demucs --with numpy 로 다시 설치한다.")
    if not drums.exists():
        fail(1, f"드럼 분리 결과가 없다: {drums}")
    return drums


def load(path: Path, sr: int = SR) -> np.ndarray:
    x, file_sr = sf.read(str(path), dtype="float32", always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    if file_sr != sr:
        x = soxr.resample(x, file_sr, sr)
    return x.astype(np.float32)


# ---------------------------------------------------------------- 3. 박 찾기

def track_beats(mix: np.ndarray, d: Path) -> tuple[np.ndarray, np.ndarray]:
    cache = d / "beats.json"
    if cache.exists():
        log(f"박 재사용: {cache}")
        data = json.loads(cache.read_text())
    else:
        from beat_this.inference import Audio2Beats

        log("beat_this 로 박과 마디 첫 박을 찾는 중")
        beats, downbeats = Audio2Beats(checkpoint_path="final0", device="cpu", dbn=False)(mix, SR)
        data = {"beats": [float(b) for b in beats], "downbeats": [float(b) for b in downbeats]}
        cache.write_text(json.dumps(data))
    return np.asarray(data["beats"]), np.asarray(data["downbeats"])


def rms_10ms(x: np.ndarray) -> np.ndarray:
    mono = x.mean(axis=1)
    win = int(SR * 0.01)
    n = len(mono) // win
    return np.sqrt((mono[: n * win].reshape(n, win) ** 2).mean(axis=1))


def music_onset(mix: np.ndarray, rel_db: float = -40.0) -> float:
    """원곡에서 소리가 처음 나는 시각. 최대 RMS 대비 rel_db 를 처음 넘는 10ms 구간."""
    rms = rms_10ms(mix)
    return float(np.argmax(rms > rms.max() * 10 ** (rel_db / 20)) * 0.01)


def drum_entry(drums: np.ndarray) -> float:
    """드럼이 처음 또렷하게 치는 시각. 다른 악기가 새어 들어온 작은 소리나 점점 커지는 심벌 스웰은
    박이 아니어서, 드럼 최대 대비 DRUM_DB 를 넘고 뒤 2초 안에 그런 구간이 3개 이상 있는 첫 지점을 고른다."""
    rms = rms_10ms(drums)
    loud = rms > rms.max() * 10 ** (DRUM_DB / 20)
    ahead = np.convolve(loud.astype(int), np.ones(200, int), mode="full")[199:]
    idx = np.flatnonzero(loud & (ahead >= 3))
    return float(idx[0] * 0.01) if len(idx) else float("inf")


def sequential_beats(beats: np.ndarray, period: float) -> tuple[np.ndarray, np.ndarray]:
    """앞 박과의 간격으로 박 번호를 이어 붙인다. 중복 검출은 버리고, 빠진 박은 번호를 건너뛴다.
    곡 전체 박 간격의 중앙값은 20ms 단위라 실제와 달라서, 그 값으로 번호를 매기면 곡 중간부터 밀린다."""
    ks, ts = [0], [float(beats[0])]
    for t in beats[1:]:
        dk = int(round((t - ts[-1]) / period))
        if dk <= 0:
            continue
        ks.append(ks[-1] + dk)
        ts.append(float(t))
    return np.asarray(ks), np.asarray(ts)


def onset_flux(mono: np.ndarray, t0: float, t1: float) -> tuple[np.ndarray, np.ndarray]:
    """짧은 창(512샘플, 1.5ms 간격) 스펙트럼 플럭스. 창이 길면 타격음 어택을 일찍 잡는다."""
    seg = mono[int(t0 * SR): int(t1 * SR)].astype(np.float32)
    _, tt, z = sps.stft(seg, fs=SR, nperseg=512, noverlap=512 - 64, boundary="even", padded=False)
    spec = np.log1p(100 * np.abs(z))
    flux = np.concatenate([[0.0], np.maximum(np.diff(spec, axis=1), 0).sum(axis=0)])
    flux = np.convolve(flux, np.exp(-0.5 * (np.arange(-4, 5) / 1.5) ** 2), mode="same")
    return tt + t0, flux


def refine_grid(mono: np.ndarray, a: float, period: float, n: int,
                shift_ms: float = 40.0, end_ms: float | None = None) -> tuple[float, float]:
    """박 격자 a + k*period (k=0..n-1)를 실제 음 어택에 맞춘다.

    beat_this 는 20ms 단위로 박을 내서 위치가 10~20ms 어긋날 수 있다. 격자 위치를 ±shift_ms,
    박 간격을 조금씩 바꿔 격자 위 플럭스 합이 가장 큰 조합을 고른다. end_ms 를 주면 마지막 박이
    ±end_ms 안에서만 움직이도록 박 간격 범위를 정한다(긴 구간용). 0 이면 박 간격은 고정한다.
    """
    t0 = max(0.0, a - 0.5)
    t1 = min(len(mono) / SR, a + n * period + 0.5)
    tt, flux = onset_flux(mono, t0, t1)
    k = np.arange(n)
    shifts = np.arange(-shift_ms, shift_ms + 0.01, 0.5) / 1000
    if end_ms == 0:
        scales = np.array([1.0])
    else:
        span = 0.005 if end_ms is None else end_ms / 1000 / max(n * period, 1e-9)
        scales = np.linspace(1 - span, 1 + span, 61)
    best = (-1.0, 0.0, 1.0)
    for scale in scales:
        pos = a + shifts[:, None] + k[None, :] * period * scale
        score = np.interp(pos, tt, flux).sum(axis=1)
        i = int(score.argmax())
        if score[i] > best[0]:
            best = (float(score[i]), float(shifts[i]), float(scale))
    return a + best[1], period * best[2]


def analyze(beats: np.ndarray, downbeats: np.ndarray, mix: np.ndarray, drums: np.ndarray,
            tempo_factor: float, shift: int) -> dict:
    if len(beats) < FIT_BEATS or len(downbeats) < 2:
        fail(1, "박을 충분히 찾지 못했다.", hint="박이 뚜렷하지 않은 곡이거나 너무 짧은 음원이다.")
    warnings: list[str] = []
    mono = mix.mean(axis=1)

    # 마디 첫 박은 곡 전체에서 가장 많이 나오는 박 위치를 따른다. 조용한 인트로에서는
    # beat_this 가 첫 박을 한두 박 어긋나게 내기도 해서, 맨 앞 첫 박을 그대로 믿지 않는다.
    ks0, ts0 = sequential_beats(beats, float(np.median(np.diff(beats))))
    db_k = np.array([ks0[int(np.argmin(np.abs(ts0 - t)))] for t in downbeats])
    gaps = np.diff(db_k)
    bpb = int(np.bincount(gaps[gaps > 0]).argmax())  # 마디당 박 수(가장 흔한 값)
    phase = int(np.bincount(db_k % bpb).argmax())
    good = downbeats[db_k % bpb == phase]
    if good[0] != downbeats[0]:
        warnings.append(f"beat_this 의 맨 앞 마디 첫 박({downbeats[0]:.2f}초)이 곡 전체와 어긋나 {good[0]:.2f}초부터 맞췄습니다.")

    i0 = int(np.argmin(np.abs(beats - good[0]))) + shift
    if not 0 <= i0 < len(beats) - FIT_BEATS:
        fail(3, f"--shift {shift} 를 적용할 수 없다.")

    # 1) 곡 앞부분: 첫 마디 첫 박부터 FIT_BEATS 박을 직선으로 맞추고 어택 기준으로 미세 조정한다.
    seg = beats[i0: i0 + FIT_BEATS]
    t_med = float(np.median(np.diff(seg)))
    k = np.round((seg - seg[0]) / t_med)
    t_fit, a = np.polyfit(k, seg, 1)
    resid_ms = float(np.std(seg - (a + k * t_fit)) * 1000)
    a_tracker = float(a)
    a, t_fit = refine_grid(mono, float(a), float(t_fit), REFINE_BEATS)

    # 2) 곡의 첫 박: 소리가 시작되는 마디의 첫 박. 소리가 마디 뒤쪽 절반에서 시작하면
    #    못갖춘마디로 보고 다음 마디 첫 박으로 한다. 그러면 픽업은 카운트인 끝 박들과 겹친다.
    onset = music_onset(mix)
    bar = bpb * t_fit
    m = -int(np.floor((onset - a) / bar))          # 소리가 시작되는 마디가 a 보다 몇 마디 앞인지
    if (onset - (a - m * bar)) / t_fit > bpb / 2:
        m -= 1
    first_db = float(a - m * bar)
    if m >= 2:
        warnings.append(f"beat_this 가 박을 못 잡은 앞부분 {m}마디를 같은 템포로 이어 붙였습니다. 인트로에 템포가 있는지 확인하세요.")

    # 3) 곡 전체 박 번호. first_db 를 0번 박으로 맞춘다.
    ks, ts = sequential_beats(beats, t_fit)
    gp, _ = np.polyfit(ks, ts, 1)
    k_rel = ks - ks[int(np.argmin(np.abs(ts - beats[i0])))] + m * bpb

    # 4) 드럼이 나오기 전 구간이 있으면 그 구간 내내 맞는 격자를 다시 구한다.
    entry = drum_entry(drums)
    drums_found = bool(np.isfinite(entry))
    if not drums_found:
        warnings.append("분리한 드럼에서 또렷한 타격을 찾지 못해 곡 끝까지 클릭을 넣었습니다. 드럼이 없는 곡인지 확인하세요.")
    grid_mode, local = "start", None
    if entry > first_db + 2 * t_fit:
        sel = (ts >= first_db - 0.5 * t_fit) & (ts <= entry + AFTER_ENTRY * t_fit)
        p, q = np.polyfit(k_rel[sel], ts[sel], 1)
        r = ts[sel] - (q + k_rel[sel] * p)
        if r.std() <= 0.02 and np.abs(r).max() <= 0.09:
            n = int(k_rel[sel].max()) + 1
            first_db, t_fit = refine_grid(mono, float(q), float(p), n, shift_ms=30, end_ms=30)
            grid_mode = "steady"
        else:
            grid_mode = "local"
            local = (k_rel, ts)
            warnings.append(f"드럼 전 구간의 템포가 일정하지 않아(오차 {r.std() * 1000:.0f}ms) 박마다 앞뒤 {LOCAL_BEATS}박으로 맞췄습니다.")

    period = t_fit / tempo_factor  # 클릭 간격

    def beat_time(j: float) -> float:
        """first_db 기준 j번째 클릭 위치."""
        if local is None:
            return first_db + j * period
        kk = j / tempo_factor
        near = np.abs(local[0] - kk) <= LOCAL_BEATS
        pp, qq = np.polyfit(local[0][near], local[1][near], 1)
        return float(qq + kk * pp)

    # 규칙 1, 2: 클릭은 곡 첫 박 앞 4박에서 시작해 드럼 첫 타격 직전 박까지 매 박 넣는다.
    # 드럼이 곡 첫 박보다 먼저 들어와도(픽업) 드럼 앞에 카운트인 4박이 온전히 남도록
    # 시작을 4박씩 앞당긴다.
    stop = entry - 0.25 * period
    start_j = -COUNT_IN
    while beat_time(start_j + COUNT_IN - 1) >= stop:
        start_j -= COUNT_IN
    if start_j < -COUNT_IN:
        warnings.append(f"드럼이 곡 첫 박보다 먼저 들어와 카운트인을 {-COUNT_IN - start_j}박 앞당겼습니다.")
    clicks: list[float] = []
    j = start_j
    while (t := beat_time(j)) < stop and t < len(mix) / SR:
        clicks.append(t)
        j += 1
    count_in, intro = clicks[:COUNT_IN], clicks[COUNT_IN:]
    start = min(clicks[0] - LEAD, onset - 0.05)  # 원곡 기준 출력 시작 시각(음수면 앞에 무음을 덧붙임)

    bpm = 60 / period
    song_bpm = 60 / gp * tempo_factor
    if abs(song_bpm - bpm) / bpm > 0.01:
        warnings.append(f"곡 전체 템포({song_bpm:.2f})와 앞부분 템포({bpm:.2f})가 1% 넘게 다릅니다.")

    # 드럼이 들어온 뒤 16박에서 박마다 ±60ms 안의 가장 강한 드럼 타격을 찾아
    # 클릭 격자와의 차이 중앙값을 남긴다(진단용). 사람이 친 드럼은 박마다 ±30ms쯤 흔들린다.
    entry_check_ms = None
    if intro and drums_found:
        j0 = int(np.ceil((entry - first_db) / period))
        grid = np.array([beat_time(j) for j in range(j0, j0 + 16)])
        grid = grid[grid < len(mix) / SR - 0.2]
        if len(grid):
            tt, fl = onset_flux(drums.mean(axis=1), grid[0] - 0.2, grid[-1] + 0.2)
            devs = []
            for g in grid:
                near = (tt > g - 0.06) & (tt < g + 0.06)
                if near.any() and fl[near].max() >= 0.3 * fl.max():
                    devs.append(tt[near][int(np.argmax(fl[near]))] - g)
            if devs:
                entry_check_ms = round(float(np.median(devs)) * 1000, 1)

    # 규칙 검사. 카운트인 4박이 드럼 앞에 온전히 있고, 마지막 클릭 뒤 드럼까지 빈 박이 없어야 한다.
    gap_beats = (entry - clicks[-1]) / period if drums_found and clicks else None
    rules = {
        "count_in_beats": len(count_in),
        "count_in_before_drums": len(count_in) == COUNT_IN and (not drums_found or count_in[-1] < stop),
        "gap_after_last_click_beats": round(gap_beats, 2) if gap_beats is not None else None,
        "gap_filled": gap_beats is None or gap_beats <= MAX_GAP_BEATS,
    }
    rules["ok"] = rules["count_in_beats"] == COUNT_IN and rules["count_in_before_drums"] and rules["gap_filled"]

    return {
        "bpm": round(bpm, 3),
        "bpm_song_fit": round(song_bpm, 3),
        "beats_per_bar": bpb,
        "tempo_factor": tempo_factor,
        "shift": shift,
        "fit_residual_ms": round(resid_ms, 2),
        "start_refine_shift_ms": round((a - a_tracker) * 1000, 1),
        "music_onset_sec": round(onset, 3),
        "tracker_first_downbeat_sec": round(float(beats[i0]), 3),
        "bars_extended_back": m,
        "first_downbeat_sec": round(first_db, 4),
        "drum_entry_sec": round(entry, 2) if drums_found else None,
        "grid_mode": grid_mode,
        "drum_entry_check_ms": entry_check_ms,
        "count_in_sec": [round(c, 4) for c in count_in],
        "intro_click_count": len(intro),
        "last_click_sec": round(clicks[-1], 3),
        "click_times_sec": [round(c, 4) for c in clicks],
        "output_start_sec": round(start, 4),
        "rules": rules,
        "warnings": warnings,
    }


def drum_profile(drums: np.ndarray, beats: np.ndarray, a: dict) -> dict:
    """마디 안 박 위치별 킥·스네어 세기. 마디 첫 박을 제대로 잡았는지 확인하는 진단용."""
    bpb = a["beats_per_bar"]
    first = a["first_downbeat_sec"]
    period = 60 / a["bpm"] * a["tempo_factor"]  # 트래커 박 간격
    mono = drums.mean(axis=1)
    bands = {
        "kick": sps.butter(4, 120, "lowpass", fs=SR, output="sos"),
        "snare": sps.butter(4, [180, 1500], "bandpass", fs=SR, output="sos"),
    }
    out = {}
    for name, sos in bands.items():
        env = np.abs(sps.sosfilt(sos, mono))
        w = int(SR * 0.03)
        prof = np.zeros(bpb)
        cnt = np.zeros(bpb)
        for t in beats:
            pos = int(round((t - first) / period)) % bpb
            c = int(t * SR)
            if c - w < 0 or c + w >= len(env):
                continue
            prof[pos] += env[c - w: c + w].max()
            cnt[pos] += 1
        prof = prof / np.maximum(cnt, 1)
        out[name] = [round(float(v / prof.max()), 2) for v in prof] if prof.max() > 0 else []
    return out


# ---------------------------------------------------------------- 4. 클릭 합성과 저장

def stick_click(sr: int = SR) -> np.ndarray:
    """드럼 스틱끼리 부딪히는 소리. 짧은 나무 공명 몇 개와 잡음 어택을 섞는다."""
    rng = np.random.default_rng(7)
    n = int(sr * 0.09)
    t = np.arange(n) / sr
    modes = [(2050, 0.022, 1.0), (3150, 0.015, 0.65), (4700, 0.009, 0.4), (6600, 0.005, 0.25)]
    tone = sum(amp * np.exp(-t / tau) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
               for f, tau, amp in modes)
    noise = rng.standard_normal(n) * np.exp(-t / 0.003)
    noise = sps.sosfilt(sps.butter(2, [1500, 10000], "bandpass", fs=sr, output="sos"), noise)
    x = tone / np.abs(tone).max() + 0.6 * noise / np.abs(noise).max()
    ramp = int(sr * 0.0004)
    x[:ramp] *= np.linspace(0, 1, ramp)
    x /= np.abs(x).max()
    return np.stack([x, x], axis=1).astype(np.float32)


def place(track: np.ndarray, a: dict, click_peak: float) -> np.ndarray:
    """원곡 시간축 트랙을 출력 시간축으로 옮기고 클릭을 얹는다."""
    start = int(round(a["output_start_sec"] * SR))
    if start < 0:
        y = np.concatenate([np.zeros((-start, 2), np.float32), track])
    else:
        y = track[start:].copy()
    click = stick_click() * click_peak
    for c in a["click_times_sec"]:
        p = int(round(c * SR)) - start
        seg = y[p: p + len(click)]
        seg += click[: len(seg)]
    peak = np.abs(y).max()
    if peak > 0.98:
        y *= 0.98 / peak
    return y


def export(y: np.ndarray, path: Path, title: str, fmt: str, bitrate: int, ffmpeg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "wav":
        sf.write(str(path), y, SR, subtype="PCM_16")
    elif fmt == "flac":
        sf.write(str(path), y, SR, format="FLAC", subtype="PCM_16")
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp = Path(f.name)
        try:
            sf.write(str(tmp), y, SR, subtype="FLOAT")
            code = run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp),
                        "-c:a", "libmp3lame", "-b:a", f"{bitrate}k", "-metadata", f"title={title}", str(path)])
        finally:
            tmp.unlink(missing_ok=True)
        if code != 0:
            fail(1, f"mp3 로 저장하지 못했다: {path}")
    log(f"저장: {path}")


# ---------------------------------------------------------------- main

def cmd_run(args: argparse.Namespace) -> None:
    is_url = bool(URL_RE.match(args.input))
    tools = detect_tools()
    missing = missing_tools(tools, need_download=is_url)
    if missing:
        fail(2, "필요한 도구가 없다.", missing=missing, install=install_hints(missing))

    out_root = Path(args.out).expanduser().resolve()
    if is_url:
        d, src, meta, downloaded = prepare_download(args.input, out_root, args.max_minutes, tools)
    else:
        d, src, meta, downloaded = prepare_local(args.input, out_root, tools)
    name = args.name or meta.get("title") or "track"

    drums_path = separate(src, d, tools["demucs"]["path"])
    mix = load(src)
    drums = load(drums_path)
    n = min(len(mix), len(drums))
    mix, drums = mix[:n], drums[:n]

    beats, downbeats = track_beats(mix, d)
    a = analyze(beats, downbeats, mix, drums, args.tempo_factor, args.shift)
    a["drum_profile"] = drum_profile(drums, beats, a)
    (d / "analysis.json").write_text(json.dumps(a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {key: v for key, v in a.items() if key != "click_times_sec"}
    if not a["rules"]["ok"]:
        fail(4, "카운트인 규칙을 지키지 못해 결과 파일을 만들지 않았다.", folder=str(d), **summary)

    out = d / f"{output_name(name)}(드럼).{args.format}"
    check = d / "check_원곡+카운트인.mp3"
    ffmpeg = tools["ffmpeg"]["path"]
    export(place(drums, a, CLICK_GAIN * float(np.abs(drums).max())), out, f"{name}(드럼)",
           args.format, args.bitrate, ffmpeg)
    export(place(mix, a, CLICK_GAIN * float(np.abs(mix).max())), check, f"{name} (확인용)",
           "mp3", 320, ffmpeg)

    emit({
        "ok": True,
        "output": str(out),
        "check": str(check),
        "folder": str(d),
        "downloaded": downloaded,
        "name": name,
        "format": args.format,
        "mp3_bitrate": args.bitrate if args.format == "mp3" else None,
        "source": meta,
        **summary,
    }, 0)


def main() -> None:
    p = argparse.ArgumentParser(description="드럼만 분리하고 카운트인 클릭을 붙인 드럼 비트를 만든다.")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="필요한 도구가 설치됐는지 확인한다.")
    r = sub.add_parser("run", help="내려받기, 드럼 분리, 박 찾기, 클릭 합성을 실행한다.")
    r.add_argument("input", help="유튜브 영상 주소 또는 로컬 오디오 파일 경로")
    r.add_argument("--name", help='결과 파일 이름에 쓸 곡 이름. 예: "가수 - 제목". 없으면 영상 제목')
    r.add_argument("--format", choices=("mp3", "wav", "flac"), default="mp3")
    r.add_argument("--bitrate", type=int, default=320, help="mp3 비트레이트(kbps). 기본 320")
    r.add_argument("--out", default=str(DEFAULT_OUT), help=f"결과 폴더. 기본 {DEFAULT_OUT}")
    r.add_argument("--tempo-factor", type=float, default=1.0,
                   help="BPM 이 두 배로 잡혔으면 0.5, 절반으로 잡혔으면 2")
    r.add_argument("--shift", type=int, default=0, help="마디 첫 박을 N 박 뒤로(음수면 앞으로) 옮긴다")
    r.add_argument("--max-minutes", type=float, default=20,
                   help="이보다 긴 영상은 거부한다. 0 이면 제한 없음. 기본 20")
    args = p.parse_args()
    if args.command == "check":
        cmd_check()
    else:
        cmd_run(args)


if __name__ == "__main__":
    main()
