#!/usr/bin/env python3
"""문서 작성 원칙 중 기계로 판별할 수 있는 항목을 점검한다.

사용법: lint.py <파일>... (파일 대신 - 를 주면 표준 입력을 읽는다)
위반이 하나라도 있으면 종료 코드 1을 돌려준다.
"""
import re
import sys

HANGUL = re.compile(r"[가-힣]")

BOLD = re.compile(r"\*\*(?!\s)[^*\n]+?(?<!\s)\*\*|__(?!\s)[^_\n]+?(?<!\s)__")
ITALIC = re.compile(
    r"(?<![*\w])\*(?![\s*])[^*\n]+?(?<![\s*])\*(?![*\w])"
    r"|(?<![_\w])_(?![\s_])[^_\n]+?(?<![\s_])_(?![_\w])"
)

SYMBOL_CHARS = "→←↑↓↔⇒⇐⇔—–―※★☆✓✔✗✘·•●○■□◆◇▶▷◀▲▼「」『』《》〈〉【】“”‘’…"
SYMBOL = re.compile(
    "[" + re.escape(SYMBOL_CHARS) + "]"
    r"|[\U0001F300-\U0001FAFF☀-➿⬀-⯿]"
    r"|->|=>|<-"
)

# 영어 소문자 단어 바로 뒤에 한글이 붙은 경우: "call한다", "deploy하면"
MIXED_ATTACHED = re.compile(r"(?<![A-Za-z0-9_.-])[a-z][a-z]+(?=[가-힣])")
# 한글 문장 안에 따로 떨어진 영어 소문자 단어
MIXED_STANDALONE = re.compile(r"(?<![\w./:@#-])[a-z]{3,}(?![\w./:@-])")

REFER = re.compile(
    r"(참조|참고)\s*(하세요|하십시오|해\s*주세요|하면\s*된다|하시면|바랍니다|할\s*것|한다)"
    r"|자세한\s*(내용|사항)은"
)

INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
URL = re.compile(r"https?://\S+")
HTML_COMMENT = re.compile(r"<!--.*?-->")

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
NUMBERED = re.compile(r"^\d+(\.\d+)*\.?\s")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s")
TABLE_ROW = re.compile(r"^\s*\|")
FENCE = re.compile(r"^\s*(```|~~~)")

LONG_DOC_CHARS = 500


def strip_inline(line):
    line = HTML_COMMENT.sub("", line)
    line = INLINE_CODE.sub("", line)
    line = LINK_TARGET.sub("]", line)
    return URL.sub("", line)


def is_toc(title):
    return NUMBERED.sub("", title).strip() == "목차"


def kind(line):
    if not line.strip():
        return "blank"
    if HEADING.match(line):
        return "heading"
    if LIST_ITEM.match(line):
        return "list"
    if TABLE_ROW.match(line):
        return "table"
    if line.startswith(("    ", "\t")):
        return "indent"
    return "prose"


def lint(text):
    issues = []

    def add(no, cat, msg, excerpt=""):
        issues.append((no, cat, msg, excerpt.strip()[:60]))

    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break

    body = []  # (줄 번호, 원문, 종류) 코드 블록은 "code" 한 줄로 대신한다
    in_code = False
    for i in range(start, len(lines)):
        line = lines[i]
        if FENCE.match(line):
            if not in_code:
                body.append((i + 1, line, "code"))
            in_code = not in_code
            continue
        if in_code:
            continue
        body.append((i + 1, line, kind(line)))

    headings = []
    prev_kind = "blank"
    blank_run = 0
    for idx, (no, line, k) in enumerate(body):
        if k == "blank":
            blank_run += 1
            if blank_run == 2:
                add(no, "빈 줄", "빈 줄이 두 줄 이상 겹쳐 있다")
            prev_kind = k
            continue
        blank_run = 0

        if k == "heading":
            level, title = HEADING.match(line).groups()
            headings.append((no, len(level), title.strip()))
            if prev_kind != "blank" and idx > 0:
                add(no, "빈 줄", "제목 앞에 빈 줄이 없다", line)
            nxt = body[idx + 1] if idx + 1 < len(body) else None
            if nxt and nxt[2] != "blank":
                add(no, "빈 줄", "제목 뒤에 빈 줄이 없다", line)
        elif k in ("list", "table", "code") and prev_kind == "prose":
            add(no, "빈 줄", "문단과 목록, 표, 코드 사이에 빈 줄이 없다", line)
        elif k == "prose" and prev_kind in ("list", "table"):
            add(no, "빈 줄", "목록이나 표 뒤에 빈 줄 없이 문단이 이어진다", line)
        elif k == "prose" and prev_kind == "prose":
            prev_line = body[idx - 1][1].rstrip()
            if re.search(r"[다요]\.$|[.?!]$", prev_line):
                add(no, "빈 줄", "앞 줄이 문장으로 끝났는데 빈 줄 없이 이어진다. 문단을 나누려면 한 줄 띄운다", line)
        prev_kind = k

        if k == "code":
            continue
        clean = strip_inline(line)

        for m in BOLD.finditer(clean):
            add(no, "강조", "굵게 강조를 쓰지 않는다", m.group())
        no_bold = BOLD.sub("", clean)
        for m in ITALIC.finditer(no_bold):
            add(no, "강조", "기울임 강조를 쓰지 않는다", m.group())

        for m in SYMBOL.finditer(clean):
            add(no, "기호", f"특수 기호 '{m.group()}'를 말로 풀어 쓴다", clean)

        if HANGUL.search(clean):
            attached = set()
            for m in MIXED_ATTACHED.finditer(clean):
                attached.add(m.start())
                add(no, "혼용", f"영어 '{m.group()}'에 한글이 붙어 있다. 한국어로 바꾼다", clean)
            for m in MIXED_STANDALONE.finditer(clean):
                if m.start() not in attached:
                    add(no, "혼용", f"영어 '{m.group()}'를 대신할 한국어가 있는지 확인한다", clean)

        if REFER.search(clean):
            add(no, "참조", "참조만 안내하지 말고 내용을 직접 가져와 쓴다", clean)

    # 글자 수는 공백을 포함해 세고, 코드 블록과 머리말은 세지 않는다
    chars = sum(len(line.strip()) for _, line, k in body if k not in ("blank", "code"))
    is_long = chars >= LONG_DOC_CHARS
    if is_long:
        has_toc = any(is_toc(t) for _, _, t in headings)
        if not has_toc:
            add(1, "목차", f"긴 글({chars}자)인데 목차가 없다")
        for no, level, title in headings:
            if level >= 2 and not is_toc(title) and not NUMBERED.match(title):
                add(no, "목차", "제목에 1, 1.1 같은 번호가 없다", title)

    return sorted(issues)


def main(argv):
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    total = 0
    for path in argv:
        text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
        for no, cat, msg, excerpt in lint(text):
            suffix = f" | {excerpt}" if excerpt else ""
            print(f"{path}:{no}: [{cat}] {msg}{suffix}")
            total += 1
    print(f"위반 {total}건" if total else "위반 없음", file=sys.stderr)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
