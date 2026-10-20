# Figma 파일 구조

Figma 파일 하나가 컨셉 하나의 디자인 모음집이다. 승인된 것만 올린다.

## 페이지

| 페이지 | 프레임 | 내용 |
| --- | --- | --- |
| `Foundations` | `Colors` | 원시 색 단계를 행으로, 의미 토큰을 라이트와 다크 두 열로 보여 준다. 각 칸에 토큰 이름을 글자로 적는다 |
| | `Typography` | 글자 크기 토큰별 예문 |
| | `Spacing` | 간격 토큰을 막대로 |
| | `Radius` | 모서리 토큰을 사각형으로 |
| `Components` | 컴포넌트마다 프레임 하나 | 컴포넌트 세트와 variants. 상태(default, hover, pressed, disabled)를 variant 속성으로 |
| `Screens` | 화면마다 섹션 하나 | 구간별 프레임을 모바일, 태블릿, PC 순서로 가로로 나란히. 이름은 `화면/구간 폭` |

## Variables

| 컬렉션 | 모드 | 변수 이름 예 | 타입 |
| --- | --- | --- | --- |
| `Color` | `Light`, `Dark` | `color/primary/500`, `color/bg/canvas` | Color |
| `Space` | 없음 | `space/4` | Number |
| `Radius` | 없음 | `radius/md` | Number |
| `Type` | 없음 | `font/size/body` | Number |
| `Motion` | 없음 | `motion/duration/fast`, `motion/easing/enter` | Number, String |

- 원시 색은 두 모드에 같은 값을 넣는다. 의미 색은 모드별로 원시 변수의 별칭을 넣는다.
- 토큰 이름의 점을 빗금으로 바꾼다. 그 밖의 이름 변경은 하지 않는다.
- 컴포넌트와 화면의 색, 간격, 모서리, 글자 크기는 모두 Variables 바인딩이다. 값을 직접 넣지 않는다.

## 이름 규칙

| 대상 | 규칙 | 예 |
| --- | --- | --- |
| 화면 프레임 | `화면/구간 폭` | `Home/Mobile 375`, `Home/Tablet 768`, `Home/PC 1440` |
| 컴포넌트 | PascalCase | `TransactionItem` |
| variant 속성 | `State`, `Size`, `Type` | `State=Pressed`, `State=WorstCase` |
| Foundations 프레임 | 영어 명사 | `Colors` |

## figma.md 기록 형식

동기화할 때마다 `design/<컨셉>/figma.md` 를 갱신한다.

```markdown
# Figma

파일: https://www.figma.com/design/<fileKey>/<name>
마지막 동기화: 2026-10-16 15:20 (Asia/Seoul)

| 대상 | 노드 id | 비고 |
| --- | --- | --- |
| Foundations/Colors | 12:34 | |
| Components/TransactionItem | 56:78 | variants 3개 |
| Screens/Home/Mobile 375 | 90:12 | |
| Screens/Home/Tablet 768 | 90:13 | |
| Screens/Home/PC 1440 | 90:14 | |
```
