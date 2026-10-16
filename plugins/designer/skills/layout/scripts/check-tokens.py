#!/usr/bin/env python3
"""레이아웃 HTML 이 토큰 값만 쓰는지 검사한다.

사용법: python3 check-tokens.py design/<컨셉>/tokens.json <html 파일>...
검사: CSS 변수 선언 블록(:root 계열 선택자) 밖의 색 값(hex, rgb, hsl, oklch)과
      토큰에 없는 px 값. 0px, 1px(경계선) 은 허용한다.
종료 코드: 위반이 있으면 1.
"""
import json
import re
import sys

COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab)\(")
PX = re.compile(r"(?<![\w.-])(\d+(?:\.\d+)?)px\b")
ROOT_BLOCK = re.compile(r":root[^{]*\{[^}]*\}", re.S)
MEDIA_ROOT = re.compile(r"@media[^{]*\{\s*(?::root[^{]*\{[^}]*\}\s*)+\}", re.S)
ALLOWED_PX = {"0", "1"}


def collect_px(node, out):
    if isinstance(node, dict):
        if "$value" in node and isinstance(node["$value"], str):
            m = re.fullmatch(r"(\d+(?:\.\d+)?)px", node["$value"].strip())
            if m:
                out.add(m.group(1))
        for v in node.values():
            collect_px(v, out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    tokens = json.load(open(sys.argv[1], encoding="utf-8"))
    allowed = set(ALLOWED_PX)
    collect_px(tokens, allowed)

    violations = 0
    for path in sys.argv[2:]:
        text = open(path, encoding="utf-8").read()
        # 줄 번호를 유지하기 위해 지운 블록은 같은 수의 줄바꿈으로 바꾼다
        blank = lambda m: "\n" * m.group(0).count("\n")
        stripped = MEDIA_ROOT.sub(blank, text)
        stripped = ROOT_BLOCK.sub(blank, stripped)
        lines = stripped.splitlines()
        for i, line in enumerate(lines, 1):
            for m in COLOR.finditer(line):
                print(f"{path}:{i}: 색 값 직접 사용 {m.group(0)}")
                violations += 1
            for m in PX.finditer(line):
                if m.group(1) not in allowed:
                    print(f"{path}:{i}: 토큰에 없는 길이 {m.group(0)}")
                    violations += 1
    print(f"\n위반 {violations}개")
    sys.exit(1 if violations else 0)


if __name__ == "__main__":
    main()
