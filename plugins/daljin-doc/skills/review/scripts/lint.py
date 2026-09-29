#!/usr/bin/env python3
"""문서 작성 원칙 중 기계로 판별할 수 있는 항목을 점검한다.

사용법: lint.py [--long-form] <파일>... (파일 대신 - 를 주면 표준 입력을 읽는다)
--long-form 을 주면 길게 풀어 쓰는 글로 보고 한 줄에 한 문장 검사를 건너뛴다.
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

# 영어 단어에 "하다", "되다"를 붙여 동사로 쓴 경우: "call해요", "deploy돼요"
MIXED_VERB = re.compile(r"(?<![A-Za-z0-9_.-])[A-Za-z]+(?=(하|해|했|합|함|되|돼|됐|됩|됨)[가-힣]*)")

# "~한다", "~이다" 같은 딱딱한 끝맺음. "~합니다", "~습니다"는 제외한다.
PLAIN_ENDING = re.compile(r"(?<=[가-힣])(?<![니습])다(?=[.!?]?\s*$)")

# 한글 뒤에 오는 마침표, 물음표, 느낌표를 문장 끝으로 본다
SENTENCE_END = re.compile(r"(?<=[가-힣])[.?!](?=\s|$)")

REFER = re.compile(
    r"(참조|참고)\s*(하세요|하십시오|해\s*주세요|하면\s*돼요|하면\s*된다|하시면|바랍니다|한다)"
    r"|자세한\s*(내용|사항)은"
)

INLINE_CODE = re.compile(r"`[^`\n]+`")
LINK_TARGET = re.compile(r"\]\([^)]*\)")
URL = re.compile(r"https?://\S+")
HTML_COMMENT = re.compile(r"<!--.*?-->")

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
NUMBERED = re.compile(r"^\d+(\.\d+)*\.?\s")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s+")
TABLE_ROW = re.compile(r"^\s*\|")
TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}")
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


def text_units(line, k):
    """끝맺음과 문장 수를 검사할 글 조각을 돌려준다."""
    if k == "heading":
        return [HEADING.match(line).group(2)]
    if k == "list":
        return [LIST_ITEM.sub("", line, count=1)]
    if k == "table":
        if TABLE_SEPARATOR.match(line):
            return []
        return [c for c in line.strip().strip("|").split("|")]
    return [line]


def lint(text, long_form=False):
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
                add(no, "빈 줄", "빈 줄이 두 줄 이상 겹쳐 있어요")
            prev_kind = k
            continue
        blank_run = 0

        if k == "heading":
            level, title = HEADING.match(line).groups()
            headings.append((no, len(level), title.strip()))
            if prev_kind != "blank" and idx > 0:
                add(no, "빈 줄", "제목 앞에 빈 줄이 없어요", line)
            nxt = body[idx + 1] if idx + 1 < len(body) else None
            if nxt and nxt[2] != "blank":
                add(no, "빈 줄", "제목 뒤에 빈 줄이 없어요", line)
        elif k in ("list", "table", "code") and prev_kind == "prose":
            add(no, "빈 줄", "문단과 목록, 표, 코드 사이에 빈 줄이 없어요", line)
        elif k == "prose" and prev_kind in ("list", "table"):
            add(no, "빈 줄", "목록이나 표 뒤에 빈 줄 없이 문단이 이어져요", line)
        prev_kind = k

        if k == "code":
            continue

        for m in INLINE_CODE.finditer(HTML_COMMENT.sub("", line)):
            add(no, "코드 표기", "백틱으로 감싼 코드 표기를 쓰지 않아요. 그냥 글자로 쓰고, 입력할 명령은 코드 블록으로 보여 줘요", m.group())

        clean = strip_inline(line)

        for m in BOLD.finditer(clean):
            add(no, "강조", "굵게 강조를 쓰지 않아요", m.group())
        for m in ITALIC.finditer(BOLD.sub("", clean)):
            add(no, "강조", "기울임 강조를 쓰지 않아요", m.group())

        for m in SYMBOL.finditer(clean):
            add(no, "기호", f"특수 기호 '{m.group()}'는 말로 풀어 써요", clean)

        for m in MIXED_VERB.finditer(clean):
            add(no, "혼용", f"영어 '{m.group()}'에 '하다'나 '되다'를 붙이지 않고 한국어 동사로 써요", clean)

        if REFER.search(clean):
            add(no, "참조", "참조만 안내하지 말고 필요한 부분을 직접 옮겨 써요", clean)

        if k in ("indent",):
            continue
        for unit in text_units(clean, k):
            unit = unit.strip()
            if not HANGUL.search(unit):
                continue
            if PLAIN_ENDING.search(unit):
                add(no, "말투", "'~한다', '~이다'로 끝내지 않고 '~해요', '~예요'처럼 부드럽게 끝내요", unit)
            if not long_form and len(SENTENCE_END.findall(unit)) >= 2:
                add(no, "한 줄", "한 줄에 문장이 여러 개예요. 한 줄에 하나씩 나눠 써요", unit)

    chars = sum(len(line.strip()) for _, line, k in body if k not in ("blank", "code"))
    if chars >= LONG_DOC_CHARS:
        if not any(is_toc(t) for _, _, t in headings):
            add(1, "목차", f"긴 글({chars}자)인데 목차가 없어요")
        for no, level, title in headings:
            if level >= 2 and not is_toc(title) and not NUMBERED.match(title):
                add(no, "목차", "제목에 1, 1.1 같은 번호가 없어요", title)

    return sorted(issues)


def main(argv):
    long_form = "--long-form" in argv
    paths = [a for a in argv if a != "--long-form"]
    if not paths:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    total = 0
    for path in paths:
        text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
        for no, cat, msg, excerpt in lint(text, long_form):
            suffix = f" | {excerpt}" if excerpt else ""
            print(f"{path}:{no}: [{cat}] {msg}{suffix}")
            total += 1
    print(f"위반 {total}건" if total else "위반 없음", file=sys.stderr)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
