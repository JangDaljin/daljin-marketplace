# daljin-marketplace

달진 개인 전용 Claude Code 플러그인 마켓플레이스다.

## 목차

1. 설치
2. 플러그인
3. `daljin-doc` 플러그인

## 1. 설치

`daljin-doc` 플러그인은 두 플러그인에 의존한다. 하나는 k-skill 마켓플레이스의 `k-skill`이고, 다른 하나는 daljin-librarian 마켓플레이스의 `daljin-kb`다. `daljin-kb`는 참조 자료를 개인 지식베이스에서 찾을 때 쓴다. 두 마켓플레이스를 먼저 등록한 뒤 이 마켓플레이스를 등록하고 설치한다. `daljin-doc`를 설치하면 두 플러그인도 함께 설치된다.

daljin-librarian은 비공개 저장소라 이 기기의 `git` 인증 정보로 받는다. `ssh-agent`에 올린 GitHub SSH 키가 있거나, `gh auth login` 후 `gh auth setup-git`을 실행해 두어야 한다. 인증에 실패하면 `daljin-kb`가 설치되지 않고, 그러면 `daljin-doc` 플러그인도 로드되지 않는다.

```bash
claude plugin marketplace add NomaDamas/k-skill
claude plugin marketplace add JangDaljin/daljin-librarian
claude plugin marketplace add JangDaljin/daljin-marketplace
claude plugin install daljin-doc@daljin-marketplace
```

## 2. 플러그인

| 플러그인 | 내용 |
| --- | --- |
| `daljin-doc` | 문서 작성 원칙, 문서 점검, 참조 자료를 가져오는 MCP |

## 3. `daljin-doc` 플러그인

사람이 읽기 좋은 한국어 문서를 쓰고 점검한다.

| 구성 | 이름 | 하는 일 |
| --- | --- | --- |
| 스킬 | `/daljin-doc:write` | 문서를 쓸 때 따를 작성 원칙과 작성 순서 |
| 스킬 | `/daljin-doc:review` | 쓴 문서를 점검 스크립트와 원칙으로 확인하고 고침 |
| MCP | `context7` | 라이브러리와 프레임워크의 최신 공식 문서를 가져옴 |
| MCP | `markitdown` | PDF, Word, PowerPoint, Excel 파일을 마크다운으로 바꿔 읽음 |

`markitdown`은 `uvx`로 실행하므로 `uv`가 설치되어 있어야 한다. `context7`은 키 없이도 동작하고, 호출 한도를 늘리려면 환경 변수 `CONTEXT7_API_KEY`를 설정한다.

맞춤법과 문체 교정은 k-skill 플러그인의 `korean-spell-check`와 `korean-humanizer` 스킬로 한다. k-skill은 의존성으로 함께 설치되며, 설치되지 않으면 `daljin-doc` 플러그인도 로드되지 않는다.

점검 스크립트는 따로 실행할 수도 있다.

```bash
python3 plugins/daljin-doc/skills/review/scripts/lint.py <파일 경로>
```
