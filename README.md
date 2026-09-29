# daljin-marketplace

달진 전용 Claude Code 플러그인을 모아 둔 저장소예요.
지금은 한국어 문서를 쓰고 점검하는 daljin-doc 플러그인 하나가 들어 있어요.

## 목차

1. 설치
2. 구성
3. 점검 스크립트 직접 실행

## 1. 설치

아래 명령 네 줄을 차례로 실행하면 설치가 끝나요.

```bash
claude plugin marketplace add NomaDamas/k-skill
claude plugin marketplace add JangDaljin/daljin-librarian
claude plugin marketplace add JangDaljin/daljin-marketplace
claude plugin install daljin-doc@daljin-marketplace
```

daljin-doc을 설치하면 k-skill과 daljin-kb도 함께 설치돼요.
daljin-doc이 두 플러그인을 가져다 쓰기 때문이에요.

- k-skill: 맞춤법과 문체 교정
- daljin-kb: 개인 지식베이스에서 자료 찾기

앞의 두 줄은 이 두 플러그인이 들어 있는 저장소를 등록하는 명령이에요.

daljin-librarian은 비공개 저장소라서 GitHub 로그인 정보가 저장된 컴퓨터에서만 받을 수 있어요.
로그인 정보는 다음 두 방법 중 하나로 저장해요.

1. GitHub에 SSH 키를 등록하고, 그 키를 ssh-agent에 올려 둬요.
2. gh auth login을 실행한 다음 gh auth setup-git을 실행해요.

로그인 정보가 없으면 daljin-kb를 받지 못하고, daljin-doc도 쓸 수 없어요.

## 2. 구성

| 종류 | 이름 | 하는 일 |
| --- | --- | --- |
| 스킬 | /daljin-doc:write | 문서를 쓸 때 지킬 원칙과 쓰는 순서 |
| 스킬 | /daljin-doc:review | 이미 쓴 문서의 점검과 교정 |
| MCP | context7 | 라이브러리와 프레임워크의 최신 공식 문서 가져오기 |
| MCP | markitdown | PDF, Word, PowerPoint, Excel 파일을 마크다운으로 바꿔 읽기 |

markitdown을 쓰려면 uv가 설치되어 있어야 해요.
context7은 키 없이도 쓸 수 있어요.
호출 횟수 제한을 늘리고 싶을 때만 환경 변수 CONTEXT7_API_KEY에 키를 넣어요.

## 3. 점검 스크립트 직접 실행

review 스킬이 쓰는 점검 스크립트는 터미널에서 직접 실행할 수도 있어요.

```bash
python3 plugins/daljin-doc/skills/review/scripts/lint.py <파일 경로>
```
