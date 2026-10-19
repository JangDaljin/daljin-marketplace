# daljin-marketplace

Claude Code 플러그인 모음이에요.

플러그인 하나가 직업 하나를 맡아요.

| 플러그인 | 하는 일 |
| --- | --- |
| writer | 사람이 읽는 한국어 문서를 작성 원칙에 맞춰 쓰고 점검해요 |
| developer | 코드 탐색, 문서 조회, 협업 도구 연결을 모아 개발 작업을 도와요 |
| librarian | 개인 지식베이스에서 필요한 지식을 찾고, 작업이 끝나면 정리해 넣어요 |
| designer | 색 팔레트와 레이아웃을 아티팩트로 먼저 보여 주고 승인받은 뒤 Figma에 디자인 모음집으로 올려요 |

    claude plugin marketplace add JangDaljin/daljin-marketplace
    claude plugin install writer@daljin-marketplace

designer는 외부 디자인 스킬을 같이 써요. 의존 마켓플레이스를 먼저 등록하고, 플러그인이 아닌 스킬 두 가지는 사용자 레벨에 설치해요.

    claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
    claude plugin install designer@daljin-marketplace
    npx skills add nutlope/hallmark -g -a claude-code
    npx skills add emilkowalski/skills -g -a claude-code -s animate,break-ui,review-animations,mobile-native,apple-design
