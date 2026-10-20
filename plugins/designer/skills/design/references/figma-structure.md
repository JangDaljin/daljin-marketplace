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

- 원시 색은 두 모드에 같은 값을 넣는다. 의미 색은 모드별로 원시 변수의 별칭을 넣는다.
- 토큰 이름의 점을 빗금으로 바꾼다. 그 밖의 이름 변경은 하지 않는다.
- 컴포넌트와 화면의 색, 간격, 모서리, 글자 크기는 모두 Variables 바인딩이다. 값을 직접 넣지 않는다.

## 이름 규칙

| 대상 | 규칙 | 예 |
| --- | --- | --- |
| 화면 프레임 | `화면/구간 폭` | `Home/Mobile 375`, `Home/Tablet 768`, `Home/PC 1440` |
| 컴포넌트 | shadcn/ui 에 같은 역할이 있으면 그 이름, 없으면 PascalCase 새 이름 | `Button`, `Card`, `TransactionItem` |
| variant 속성 | shadcn/ui 컴포넌트는 그 variant 이름(`Variant`, `Size`)을 그대로, 그 밖에는 `State`, `Size`, `Type` | `Variant=Destructive`, `Size=Sm`, `State=Pressed` |
| Foundations 프레임 | 영어 명사 | `Colors` |

## shadcn/ui 대응

프론트엔드는 shadcn/ui 로 구현한다. 핸드오프가 이름만 보고 1대1 로 옮길 수 있게 다음을 지킨다.

| shadcn/ui 컴포넌트 | 쓰는 자리 | variant |
| --- | --- | --- |
| `Button` | 모든 버튼 | `Variant`: Default, Secondary, Destructive, Outline, Ghost, Link. `Size`: Default, Sm, Lg, Icon |
| `Card` | 카드, 시트 바탕 | 없음. 내부는 `CardHeader`, `CardContent`, `CardFooter` 프레임 |
| `Input`, `Textarea`, `Select`, `Checkbox`, `RadioGroup`, `Switch` | 폼 요소 | shadcn/ui 상태(default, focus, disabled, invalid) |
| `Dialog`, `Sheet`, `Drawer`, `Popover`, `DropdownMenu` | 겹쳐 뜨는 요소 | 없음 |
| `Tabs`, `Accordion`, `Table`, `Badge`, `Avatar`, `Skeleton`, `Toast`(sonner), `Tooltip` | 각 역할 | shadcn/ui 기본 variant |

- 의미 색 토큰은 shadcn/ui 테마 변수와 대응되게 둔다. `color.bg.canvas` 는 `background`, `color.bg.surface` 는 `card`, `color.text.primary` 는 `foreground`, `color.action.primary` 는 `primary`, `color.action.primary-text` 는 `primary-foreground`, `color.status.error` 는 `destructive`, `color.border.default` 는 `border`, `color.border.strong` 은 `ring`, `radius.md` 는 `--radius`. 토큰 이름을 바꾸지는 않고 `tokens.json` 의 `$extensions.daljin.shadcn` 에 대응 변수 이름을 적는다.
- shadcn/ui 에 없는 컴포넌트(예: `TransactionItem`)는 shadcn/ui 컴포넌트를 조합해 만들 수 있는지 Components 프레임 설명에 적는다(`Card + Badge + Button/Ghost`).

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
