---
name: handoff
description: 디자이너가 Figma에 정돈한 디자인 모음집을 Figma MCP로 읽어 코드로 옮기는 절차. Figma Variables를 CSS 변수와 shadcn/ui 테마 변수로, Figma 컴포넌트를 shadcn/ui 컴포넌트와 기능 컴포넌트로, 화면 프레임을 라우트로 옮기고, 대응표를 design/<컨셉>/handoff.md에 기록하며, 구현 화면 스크린샷을 Figma 프레임과 대조한다. "Figma 보고 구현해줘", "디자인 반영", "토큰 옮겨줘", "피그마랑 비교", "/developer:handoff <Figma URL 또는 화면 이름>" 요청 시 사용.
---

# Figma 핸드오프

디자이너의 Figma 파일을 읽어 코드로 옮긴다. 공통 규칙(디자인 원본은 Figma, shadcn/ui 우선)은 `developer:frontend` 스킬, 구현 방법은 하네스(`developer:nextjs`)를 따른다.

## 1. 원본 찾기

- `design/<컨셉>/figma.md` 가 있으면 거기 적힌 파일 URL 과 노드 id 를 쓴다. `$ARGUMENTS` 에 Figma URL 이 있으면 그것을 쓴다. 둘 다 없으면 사용자에게 묻는다.
- `design/<컨셉>/tokens.json` 이 있으면 Figma Variables 와 함께 읽어 서로 같은지 확인한다. 다르면 Figma 를 원본으로 보고 사용자에게 알린다.
- `figma` MCP 가 인증되어 있지 않으면 인증 도구를 호출하고 사용자가 브라우저에서 승인하게 안내한다.

## 2. 읽기

Figma MCP 읽기 도구를 쓴다. 도구 이름은 Figma 쪽 버전에 따라 바뀌므로 목록으로 확인한다.

| 읽을 것 | 도구 | 쓰임 |
| --- | --- | --- |
| Variables 정의 | 변수 정의 도구(`get_variable_defs` 류) | 3절 토큰 |
| 프레임 구조와 스타일 | 디자인 컨텍스트 또는 메타데이터 도구 | 4절 컴포넌트와 화면 |
| 프레임 이미지 | 스크린샷 도구 | 5절 대조 |

- 한 번에 파일 전체를 읽지 않는다. 구현할 화면의 노드와 그 화면이 쓰는 컴포넌트, Variables 만 읽는다.
- Figma MCP 가 코드 스니펫을 내놓더라도 그대로 붙여 넣지 않는다. 구조와 값만 참고하고 하네스 규칙대로 다시 쓴다.

## 3. 토큰 옮기기

Figma Variables 컬렉션 `Color`(모드 Light, Dark), `Space`, `Radius`, `Type` 을 `globals.css` 의 CSS 변수로 옮긴다.

1. 변수 이름의 빗금을 하이픈으로 바꾸고 `--` 를 붙인다: `color/bg/canvas` 는 `--color-bg-canvas`. Light 값은 `:root`, Dark 값은 `.dark`(또는 프로젝트의 다크 선택자)에 둔다.
2. shadcn/ui 가 요구하는 테마 변수는 위 변수를 가리키는 별칭으로 둔다. 값을 두 번 적지 않는다.

   | shadcn/ui 변수 | 디자이너 토큰 |
   | --- | --- |
   | `--background`, `--foreground` | `color/bg/canvas`, `color/text/primary` |
   | `--card`, `--card-foreground` | `color/bg/surface`, `color/text/primary` |
   | `--popover`, `--popover-foreground` | `color/bg/surface-raised`, `color/text/primary` |
   | `--primary`, `--primary-foreground` | `color/action/primary`, `color/action/primary-text` |
   | `--secondary`, `--secondary-foreground` | `color/action/secondary`, `color/action/secondary-text` |
   | `--muted`, `--muted-foreground` | `color/bg/subtle`, `color/text/secondary` |
   | `--accent`, `--accent-foreground` | `color/bg/subtle`, `color/text/primary` |
   | `--destructive` | `color/status/error` |
   | `--border`, `--input` | `color/border/default` |
   | `--ring` | `color/border/strong` |
   | `--radius` | `radius/md` |

   디자이너 토큰에 해당 역할이 없으면 사용자에게 알리고 임의로 채우지 않는다. `success`, `warning`, `info` 처럼 shadcn/ui 에 없는 상태색은 `--success` 같은 추가 변수로 둔다.
3. 경계선 변수(`breakpoint/tablet`, `breakpoint/pc`)는 Tailwind 테마 `screens` 로 등록한다.
4. 글자 크기, 간격, 모서리 토큰도 Tailwind 테마에 등록해 `text-body`, `p-4`, `rounded-md` 처럼 토큰 이름으로 쓴다.

## 4. 컴포넌트와 화면 옮기기

1. Figma `Components` 페이지의 컴포넌트마다 대응을 정한다.
   - shadcn/ui 에 같은 역할이 있으면 그 컴포넌트를 CLI 로 추가하고 쓴다. Figma 의 variant(`State=Pressed`, `Size=Sm`)는 shadcn/ui variant 나 상태로 옮긴다.
   - 없으면 shadcn/ui 컴포넌트를 조합한 기능 컴포넌트를 `components/<기능>/` 에 Figma 이름 그대로 만든다.
   - 조합으로도 안 되면 새로 만들되 shadcn/ui 와 같은 구조로 쓴다.
2. Figma `Screens` 의 화면마다 라우트를 정한다. 구간별 프레임(Mobile 375, Tablet 768, PC 1440)은 하나의 반응형 라우트로 합친다.
3. 대응을 `design/<컨셉>/handoff.md` 에 적는다. 형식은 5절 아래 예시다. 이미 적힌 대응은 바꾸지 않고 따른다. 바꿔야 하면 사용자에게 알린다.
4. 구현은 하네스 규칙대로 한다. 색, 간격, 글자는 3절의 변수만 쓴다.

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
