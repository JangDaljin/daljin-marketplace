# daljin-marketplace

달진 전용 Claude Code 플러그인을 모아 둔 저장소다. 지금은 한국어 문서를 쓰고 점검하는 `daljin-doc` 플러그인 하나가 들어 있다.

## 목차

1. 설치
2. 구성
3. 점검 스크립트 직접 실행

## 1. 설치

아래 명령 네 줄을 차례로 실행하면 설치가 끝난다.

```bash
claude plugin marketplace add NomaDamas/k-skill
claude plugin marketplace add JangDaljin/daljin-librarian
claude plugin marketplace add JangDaljin/daljin-marketplace
claude plugin install daljin-doc@daljin-marketplace
```

`daljin-doc`을 설치하면 `k-skill`과 `daljin-kb`도 함께 설치된다. `daljin-doc`이 두 플러그인을 가져다 쓰기 때문이다. `k-skill`로는 맞춤법과 문체를 고치고, `daljin-kb`로는 개인 지식베이스에서 자료를 찾는다. 앞의 두 줄은 두 플러그인이 들어 있는 저장소를 등록하는 명령이다.

daljin-librarian은 비공개 저장소라서 GitHub 로그인 정보가 저장된 컴퓨터에서만 받을 수 있다. 로그인 정보는 다음 두 방법 중 하나로 저장한다.

1. GitHub에 SSH 키를 등록하고, 그 키를 `ssh-agent`에 올려 둔다.
2. `gh auth login`을 실행한 다음 `gh auth setup-git`을 실행한다.

로그인 정보가 없으면 `daljin-kb`를 받지 못하고, 그러면 `daljin-doc`도 쓸 수 없다.

## 2. 구성

| 종류 | 이름 | 하는 일 |
| --- | --- | --- |
| 스킬 | `/daljin-doc:write` | 문서를 쓸 때 지킬 원칙과 쓰는 순서를 알려 준다 |
| 스킬 | `/daljin-doc:review` | 이미 쓴 문서를 점검하고 고친다 |
| MCP | `context7` | 라이브러리와 프레임워크의 최신 공식 문서를 가져온다 |
| MCP | `markitdown` | PDF, Word, PowerPoint, Excel 파일을 읽을 수 있게 마크다운으로 바꾼다 |

`markitdown`을 쓰려면 `uv`가 설치되어 있어야 한다. `context7`은 키 없이도 쓸 수 있고, 호출 횟수 제한을 늘리고 싶을 때만 환경 변수 `CONTEXT7_API_KEY`에 키를 넣는다.

## 3. 점검 스크립트 직접 실행

`/daljin-doc:review`가 쓰는 점검 스크립트는 터미널에서 직접 실행할 수도 있다.

```bash
python3 plugins/daljin-doc/skills/review/scripts/lint.py <파일 경로>
```
