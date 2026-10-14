#!/bin/sh
# 지식베이스 루트를 찾는다.
# 첫 줄에 루트 경로, 둘째 줄에 rw 를 출력한다.
# 찾지 못하면 종료 코드 1을 돌려준다.
#
# 찾는 순서
#   1. 환경 변수 DALJIN_KB_ROOT
#   2. 로컬 작업 복제본 ~/development/daljin-knowledge-base
#   3. 이름 변경 전 경로 ~/development/daljin-librarian

is_kb() { [ -f "$1/knowledge/INDEX.md" ]; }

for CAND in "$DALJIN_KB_ROOT" "$HOME/development/daljin-knowledge-base" "$HOME/development/daljin-librarian"; do
  if [ -n "$CAND" ] && is_kb "$CAND"; then
    printf '%s\nrw\n' "$CAND"
    exit 0
  fi
done

exit 1
