---
name: handoff
description: 디자이너의 결과물(Figma 디자인 모음집, 승인된 아티팩트와 tokens.json, HTML 시안)을 읽어 코드로 옮기는 절차. Figma Variables를 CSS 변수와 shadcn/ui 테마 변수로, Figma 컴포넌트를 shadcn/ui 컴포넌트와 기능 컴포넌트로, 화면 프레임을 라우트로 옮기고, 대응표를 design/<컨셉>/handoff.md에 기록하며, 구현 화면 스크린샷을 Figma 프레임과 대조한다. "Figma 보고 구현해줘", "디자인 반영", "토큰 옮겨줘", "피그마랑 비교", "/developer:handoff <Figma URL 또는 화면 이름>" 요청 시 사용.
---

# Figma 핸드오프

디자이너의 Figma 파일을 읽어 코드로 옮긴다. 공통 규칙(디자인 원본은 Figma, shadcn/ui 우선)은 `developer:frontend` 스킬, 구현 방법은 하네스(`developer:nextjs`)를 따른다.

## 1. 원본 찾기

`developer:frontend` 2절의 순서대로 원본을 정한다.

- Figma: `design/<컨셉>/figma.md` 가 있으면 거기 적힌 파일 URL 과 노드 id 를 쓴다. `$ARGUMENTS` 에 Figma URL 이 있으면 그것을 쓴다. `figma` MCP 가 인증되어 있지 않으면 인증 도구를 호출하고 사용자가 브라우저에서 승인하게 안내한다.
- 아티팩트: Figma 가 없으면 `design/<컨셉>/tokens.json` 과 승인 주석(`approved:`)이 있는 `layout-*.html`, `component-*.html` 을 원본으로 쓴다. 토큰은 `tokens.json` 에서, 구조와 상태는 HTML 에서 읽는다. 승인 주석이 없는 파일은 쓰지 않고 사용자에게 알린다.
- HTML 시안이나 이미지: 둘 다 없고 사용자가 파일을 주면 그것을 원본으로 쓰되, 색과 간격을 먼저 토큰 파일로 뽑아 사용자에게 확인받은 뒤 구현한다.
- Figma 와 `tokens.json` 이 둘 다 있으면 서로 같은지 확인한다. 다르면 Figma 를 원본으로 보고 사용자에게 알린다.
- 아무것도 없으면 구현하지 않고 `designer` 페르소나로 디자인을 먼저 만들게 안내한다.

## 2. 읽기

원본이 Figma 면 Figma MCP 읽기 도구를 쓴다. 도구 이름은 Figma 쪽 버전에 따라 바뀌므로 목록으로 확인한다. 원본이 아티팩트면 `tokens.json` 과 HTML 을 그대로 읽는다.

| 읽을 것 | 도구 | 쓰임 |
| --- | --- | --- |
| Variables 정의 | 변수 정의 도구(`get_variable_defs` 류) | 3절 토큰 |
| 프레임 구조와 스타일 | 디자인 컨텍스트 또는 메타데이터 도구 | 4절 컴포넌트와 화면 |
| 프레임 이미지 | 스크린샷 도구 | 5절 대조 |

- 한 번에 파일 전체를 읽지 않는다. 구현할 화면의 노드와 그 화면이 쓰는 컴포넌트, Variables 만 읽는다.
- Figma MCP 가 코드 스니펫을 내놓더라도 그대로 붙여 넣지 않는다. 구조와 값만 참고하고 하네스 규칙대로 다시 쓴다.

## 3. 토큰 옮기기

원본의 토큰(Figma Variables 컬렉션 `Color`, `Space`, `Radius`, `Type`, `Motion` 또는 `tokens.json`)을 `developer:design-library` 3절의 규칙대로 CSS 변수와 Tailwind 테마로 옮긴다. shadcn/ui 테마 변수 대응표도 그 절에 있다. 원본에 없는 역할의 값은 임의로 채우지 않고 사용자에게 알린다.

## 4. 컴포넌트와 화면 옮기기

1. 원본의 컴포넌트(Figma `Components` 페이지 또는 `component-*.html`)마다 대응을 정한다. 라이브러리 컴포넌트를 고르고 조합하고 새로 만드는 순서는 `developer:design-library` 5절을 따른다. 기능 컴포넌트는 `components/<기능>/` 에 원본 이름 그대로 만든다.
2. 원본의 화면(Figma `Screens` 또는 `layout-*.html`)마다 라우트를 정한다. 구간별 프레임(Mobile 375, Tablet 768, PC 1440)은 하나의 반응형 라우트로 합친다.
3. 대응을 `design/<컨셉>/handoff.md` 에 적는다. 형식은 6절의 예시다. 이미 적힌 대응은 바꾸지 않고 따른다. 바꿔야 하면 사용자에게 알린다.
4. 구현은 하네스와 `developer:design-library` 규칙대로 한다. 색, 간격, 글자, 모션은 3절에서 옮긴 변수만 쓴다.

## 5. 대조

구현 뒤 반드시 Figma 와 나란히 본다.

1. 구현 화면을 Chrome DevTools MCP(또는 Playwright)로 세 구간 폭에서 스크린샷 찍는다. 라이트와 다크 둘 다.
2. Figma 스크린샷 도구로 같은 프레임 이미지를 받는다.
3. 다른 점을 적는다: 정보 구조와 순서, 간격, 색, 글자 크기, 상태 표현.
4. 코드가 틀린 것은 고친다. Figma 가 틀렸거나 구현이 불가능하면 코드에서 고치지 않고 사용자에게 알린다.
5. 차이가 없거나 남은 차이가 모두 보고된 상태에서 `frontend` 스킬 1.3 의 UI 검토로 넘어간다.

## 6. 기록

`design/<컨셉>/handoff.md` 를 다음 형식으로 갱신한다.

```markdown
# 핸드오프

Figma: https://www.figma.com/design/<fileKey>/<name>
마지막 동기화: 2026-10-20 14:00 (Asia/Seoul)

## 토큰

globals.css 에 반영. shadcn/ui 변수 대응은 developer:handoff 3절 표 기준. 추가 변수: --success, --warning, --info

## 컴포넌트

| Figma | 코드 | 비고 |
| --- | --- | --- |
| Button | shadcn/ui Button | Variant=Destructive → variant="destructive" |
| TransactionItem | components/transactions/transaction-item.tsx | Card + Badge + Button(ghost) 조합 |

## 화면

| Figma | 라우트 | 상태 | 남은 차이 |
| --- | --- | --- | --- |
| Home | / | 구현 완료 2026-10-20 | 없음 |
```
