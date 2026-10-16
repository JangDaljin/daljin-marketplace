#!/usr/bin/env python3
"""tokens.json 의 의미 색 토큰 조합에 대해 WCAG 대비를 라이트와 다크 모두 검사한다.

사용법: python3 contrast.py design/<컨셉>/tokens.json [--json]
종료 코드: 실패한 조합이 있으면 1, 없으면 0.
"""
import json
import re
import sys

# (글자 토큰, 바탕 토큰, 최소 대비)
PAIRS = [
    ("color.text.primary", "color.bg.canvas", 4.5),
    ("color.text.primary", "color.bg.surface", 4.5),
    ("color.text.primary", "color.bg.surface-raised", 4.5),
    ("color.text.primary", "color.bg.subtle", 4.5),
    ("color.text.secondary", "color.bg.canvas", 4.5),
    ("color.text.secondary", "color.bg.surface", 4.5),
    ("color.text.disabled", "color.bg.surface", 3.0),
    ("color.text.link", "color.bg.surface", 4.5),
    ("color.text.inverse", "color.action.primary", 4.5),
    ("color.action.primary-text", "color.action.primary", 4.5),
    ("color.action.primary-text", "color.action.primary-hover", 4.5),
    ("color.action.primary-text", "color.action.primary-pressed", 4.5),
    ("color.action.secondary-text", "color.action.secondary", 4.5),
    ("color.action.primary", "color.bg.surface", 3.0),
    ("color.border.default", "color.bg.surface", 3.0),
    ("color.border.strong", "color.bg.surface", 3.0),
    ("color.status.success-text", "color.status.success-bg", 4.5),
    ("color.status.warning-text", "color.status.warning-bg", 4.5),
    ("color.status.error-text", "color.status.error-bg", 4.5),
    ("color.status.info-text", "color.status.info-bg", 4.5),
]

ALIAS = re.compile(r"^\{([^}]+)\}$")


def get(tokens, path):
    node = tokens
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def resolve(tokens, value, depth=0):
    if depth > 10:
        raise ValueError(f"별칭이 너무 깊다: {value}")
    m = ALIAS.match(str(value).strip())
    if not m:
        return value
    target = get(tokens, m.group(1))
    if target is None or "$value" not in target:
        raise KeyError(f"별칭 대상이 없다: {value}")
    return resolve(tokens, target["$value"], depth + 1)


def value_for(tokens, path, mode):
    node = get(tokens, path)
    if node is None or "$value" not in node:
        return None
    raw = node["$value"]
    if mode == "dark":
        raw = node.get("$extensions", {}).get("daljin", {}).get("dark", raw)
    return resolve(tokens, raw)


def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 8:
        h = h[:6]
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(rgb):
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(hex_to_rgb(a)), luminance(hex_to_rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    tokens = json.load(open(args[0], encoding="utf-8"))

    rows = []
    failed = 0
    for mode in ("light", "dark"):
        for fg, bg, minimum in PAIRS:
            fv, bv = value_for(tokens, fg, mode), value_for(tokens, bg, mode)
            if fv is None or bv is None:
                rows.append({"mode": mode, "fg": fg, "bg": bg, "ratio": None, "min": minimum, "pass": None})
                continue
            ratio = contrast(fv, bv)
            ok = ratio >= minimum
            failed += 0 if ok else 1
            rows.append({"mode": mode, "fg": fg, "bg": bg, "fgValue": fv, "bgValue": bv,
                         "ratio": round(ratio, 2), "min": minimum, "pass": ok})

    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"{'모드':<6} {'글자':<34} {'바탕':<30} {'대비':>6} {'기준':>5} 결과")
        for r in rows:
            if r["ratio"] is None:
                result, ratio = "토큰 없음", "-"
            else:
                result, ratio = ("통과" if r["pass"] else "실패"), f"{r['ratio']:.2f}"
            print(f"{r['mode']:<6} {r['fg']:<34} {r['bg']:<30} {ratio:>6} {r['min']:>5} {result}")
        missing = sum(1 for r in rows if r["ratio"] is None)
        print(f"\n실패 {failed}개, 토큰 없음 {missing}개, 전체 {len(rows)}개")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
