# daljin-marketplace

Claude Code 플러그인 모음이에요.

플러그인 하나가 직업 하나를 맡아요.

| 플러그인 | 하는 일 |
| --- | --- |
| writer | 사람이 읽는 한국어 문서를 작성 원칙에 맞춰 쓰고 점검해요 |
| developer | 코드 탐색, 문서 조회, 협업 도구 연결을 모아 서버와 프론트엔드 개발을 도와요. 프론트엔드는 designer의 결과물(Figma, 아티팩트, HTML)을 그대로 shadcn/ui 위에 구현해요 |
| librarian | 개인 지식베이스에서 필요한 지식을 찾고, 작업이 끝나면 정리해 넣어요 |
| designer | 색 팔레트와 레이아웃을 아티팩트로 먼저 보여 주고 승인받은 뒤 Figma에 디자인 모음집으로 올려요 |

    claude plugin marketplace add JangDaljin/daljin-marketplace
    claude plugin install writer@daljin-marketplace

designer는 외부 디자인 스킬(frontend-design, ui-ux-pro-max, hallmark, emil-skills)을 의존성으로 같이 설치해요. developer에는 외부 디자인 스킬이 없어요. 이 마켓플레이스가 원본 저장소를 그대로 가리키고, 코드는 복사하지 않아요. ui-ux-pro-max 검색에는 Python 3이 필요해요.

    claude plugin install designer@daljin-marketplace
