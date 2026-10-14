#!/bin/sh
# SessionStart 훅. 지식베이스 사용 규칙을 세션 맥락에 넣는다.
# 표준 출력이 그대로 세션 맥락이 된다.

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$(sh "$DIR/kb-root.sh")" || {
  echo "[librarian] 개인 지식베이스(daljin-knowledge-base)를 찾지 못했다. 필요하면 사용자에게 git@github.com:JangDaljin/daljin-knowledge-base.git 을 ~/development/daljin-knowledge-base 에 복제할지 묻는다."
  exit 0
}
ROOT="$(echo "$OUT" | sed -n 1p)"

MODE_NOTE="로컬 작업 복제본이라 읽고 쓸 수 있다."
# 다른 기기에서 push 한 내용을 받는다. fast-forward 만 하고, 실패하면 건너뛴다.
# 커밋 안 된 변경과 겹치는 파일이 있으면 git 이 pull 을 거부하므로 작업 중인 내용은 덮어쓰지 않는다.
if [ "$(git -C "$ROOT" branch --show-current 2>/dev/null)" = "main" ]; then
  BEFORE="$(git -C "$ROOT" rev-parse HEAD)"
  if GIT_TERMINAL_PROMPT=0 git -C "$ROOT" \
      -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=5 \
      pull --ff-only --quiet >/dev/null 2>&1; then
    AFTER="$(git -C "$ROOT" rev-parse HEAD)"
    if [ "$BEFORE" != "$AFTER" ]; then
      N="$(git -C "$ROOT" rev-list --count "$BEFORE..$AFTER")"
      MODE_NOTE="$MODE_NOTE 세션 시작 시 원격에서 커밋 ${N}개를 받아 최신화했다."
    fi
  else
    MODE_NOTE="$MODE_NOTE 세션 시작 시 원격 최신화(git pull --ff-only)에 실패했다. 네트워크 문제이거나 로컬과 원격이 갈라졌을 수 있다. 최신 내용이 중요한 작업이면 사용자에게 알린다."
  fi
fi

cat <<EOF
[librarian] 개인 지식베이스(daljin-knowledge-base) 사용 규칙

지식베이스 위치는 $ROOT 이다. $MODE_NOTE

1. 읽기: 사용자의 질문이나 작업에 배경 지식이 필요하면 먼저 librarian:search 스킬로 지식베이스를 찾는다. 업무 배경은 knowledge/work/ 에, 개인 기술 노트는 knowledge/personal/ 에 있다. 근거가 있으면 문서 경로를 인용하고, 없으면 없다고 말한다. 지식베이스에 있는 것처럼 지어내지 않는다.
2. 갱신: 코드, 조사, 의사결정 같은 작업을 마치면 기본 동작으로 librarian:update 스킬을 호출해 재사용할 가치가 있는 내용을 지식베이스에 정리한다. 갱신 후에는 어느 서가의 어떤 파일에 무엇을 넣었는지 사용자에게 짧게 알린다.
3. 원격 반영: 지식베이스를 push 하기 전에는 반드시 사용자에게 먼저 묻고 승인받은 뒤에만 push 한다.
4. 결정 ID: F-004 같은 결정이나 피드백 ID를 사용자에게 언급할 때는 그 항목의 내용도 함께 보여준다.
EOF
