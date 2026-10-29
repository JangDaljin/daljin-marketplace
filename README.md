# daljin-marketplace

Claude Code와 Codex에서 사용하는 플러그인 모음이에요.

플러그인 하나가 직업 하나를 맡아요.

| 플러그인 | 하는 일 |
| --- | --- |
| writer | 사람이 읽는 한국어 문서를 작성 원칙에 맞춰 쓰고 점검해요 |
| developer | 코드 탐색, 문서 조회, 협업 도구 연결을 모아 서버와 프론트엔드 개발을 도와요. 프론트엔드는 designer가 넘긴 디자인을 그대로 shadcn/ui 위에 구현해요 |
| librarian | 개인 지식베이스에서 필요한 지식을 찾고, 작업이 끝나면 정리해 넣어요 |
| designer | 색 팔레트와 레이아웃을 아티팩트로 먼저 보여 주고 승인받은 뒤 Figma에 디자인 모음집으로 올리고, 전달 명세를 써서 개발자에게 넘겨요 |

Claude Code에서는 다음 명령으로 설치해요.

    claude plugin marketplace add JangDaljin/daljin-marketplace
    claude plugin install writer@daljin-marketplace

designer는 외부 디자인 스킬(frontend-design, ui-ux-pro-max, hallmark, emil-skills)을 의존성으로 같이 설치해요. developer에는 외부 디자인 스킬이 없어요. 이 마켓플레이스가 원본 저장소를 그대로 가리키고, 코드는 복사하지 않아요. ui-ux-pro-max 검색에는 Python 3이 필요해요.

    claude plugin install designer@daljin-marketplace
Codex에서는 마켓플레이스를 등록한 뒤 원하는 플러그인을 설치해요. 아래는 `plugin add`를 지원하는 Codex CLI 기준이에요.

    codex plugin marketplace add JangDaljin/daljin-marketplace
    codex plugin add writer@daljin-marketplace
    codex plugin add librarian@daljin-marketplace
    codex plugin add developer@daljin-marketplace
    codex plugin add designer@daljin-marketplace

앱에서는 플러그인 화면에서 이 저장소를 마켓플레이스로 추가하고 필요한 플러그인을 선택해도 돼요. 설치 후 새 대화에서 작업을 요청하면 해당 스킬을 사용할 수 있어요.

Codex 카탈로그는 `.agents/plugins/marketplace.json`에 있고, 각 플러그인의 `plugin.json`과 `mcp.json`은 [OpenAI 공식 패키징 형식](https://developers.openai.com/plugins/build/plugins)을 따라요. Claude Code 설정은 `.claude-plugin/`과 `.mcp.json`에 따로 두고, `skills/`와 스크립트는 공유해요.

Codex에서는 Claude의 외부 플러그인 의존성을 자동 설치하지 않아요. writer와 함께 librarian을 설치하고, k-skill이나 designer의 외부 디자인 스킬이 필요하면 각 원본 저장소에서 Codex용 스킬 설치 방법을 확인해 별도로 설치해 주세요. Codex 카탈로그에는 이 저장소가 직접 관리하는 네 플러그인만 있어요.

스크립트 실행에는 Python 3, librarian에는 `sh`와 Git이 필요해요. Windows에서는 Git Bash나 WSL을 준비해 주세요. 스킬의 `<이 SKILL.md가 있는 폴더>` 표시는 실제 설치된 스킬 폴더의 절대 경로로 바꿔 실행해요.

developer의 Codex MCP는 Serena의 `codex` 컨텍스트를 사용해요. MCP에 따라 `uvx`, Node.js의 `npx`, `codegraph` 명령과 `CONTEXT7_API_KEY`, `GITHUB_ACCESS_TOKEN`, `HF_TOKEN` 환경 변수 또는 서비스 로그인이 필요해요. Slack은 Claude용 OAuth 클라이언트 설정을 공유하지 않고 Codex에서 연결과 인증을 진행해요.

librarian의 세션 시작 훅은 로컬 Codex 데스크톱에서 훅 정의를 검토하고 신뢰한 뒤 사용해요. 훅을 지원하지 않거나 신뢰하지 않은 환경에서는 작업 전에 search를, 재사용할 지식이 남은 작업 뒤에는 update를 직접 요청해 주세요. developer의 리뷰어 Markdown은 Codex 에이전트 설정으로 자동 등록되지 않으며, 스킬에 적힌 리뷰 지침을 읽어 리뷰해요.
