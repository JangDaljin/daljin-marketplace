---
name: design-library
description: 프론트엔드 구현에 쓰는 스타일링과 컴포넌트 라이브러리 규칙. Tailwind CSS v4 와 shadcn/ui 를 기본으로, 설치(shadcn init, components.json), components/ui 취급, 컴포넌트 추가·조합·신규 작성 순서, 디자인 토큰을 CSS 변수와 Tailwind 테마로 옮기는 규칙과 shadcn/ui 테마 변수 대응표, 다크 모드, 임의 값 금지, 모션 변수, UI 유틸 라이브러리 목록을 정한다. 컴포넌트를 추가하거나 스타일을 쓰거나 토큰을 코드로 옮길 때, "/developer:design-library" 요청 시 사용. 프레임워크 하네스(developer:nextjs)와 함께 쓴다.
---

# 디자인 라이브러리: Tailwind + shadcn/ui

프론트엔드 구현의 스타일링과 컴포넌트 라이브러리 규칙이다. 프레임워크와 무관하게 적용되고, 프레임워크 고유 내용은 하네스(`developer:nextjs`)에 있다. 공통 작업 흐름과 디자인 원본 원칙은 `developer:frontend` 를 따른다.

작업 중인 프로젝트가 이미 다른 컴포넌트 라이브러리(MUI, Chakra, Ant Design 등)나 다른 스타일링 방식을 쓰고 있으면 그것이 우선이다(`developer:frontend` 0절). 바꾸자고 제안하지 않는다.

## 1. 스택

| 영역 | 선택 |
| --- | --- |
| 스타일링 | Tailwind CSS v4. 디자인 토큰은 CSS 변수로만 |
| 컴포넌트 | shadcn/ui(`components.json`, `components/ui/`) |
| 아이콘 | lucide-react |
| 토스트 | sonner |
| 폼 | react-hook-form + zod |
| 차트 | recharts |
| 가상 스크롤 | @tanstack/react-virtual |
| 드래그 | @dnd-kit |
| 날짜 | date-fns |

표에 없는 UI 유틸이 필요하면 손수 만들지 말고 사용자에게 어떤 라이브러리를 쓸지 묻는다. 라이브러리 API 는 작성 전에 context7 MCP 로 설치된 버전의 문서를 확인한다.

## 2. 설치

1. Tailwind v4 를 프레임워크 하네스가 정한 방법으로 넣는다.
2. `pnpm dlx shadcn@latest init` 으로 shadcn/ui 를 넣는다. 스타일과 기본 색은 중립으로 두고, 실제 값은 3절대로 디자인 토큰으로 채운다.
3. `components.json` 의 경로(`components/ui`, `lib/utils`)는 하네스의 폴더 구조와 맞춘다.

## 3. 토큰을 코드로 옮기기

디자인 원본(Figma Variables 또는 `tokens.json`)의 토큰을 `globals.css` 의 CSS 변수로 옮기고, 컴포넌트는 그 변수와 Tailwind 테마 토큰만 쓴다.

1. 토큰 이름의 빗금이나 점을 하이픈으로 바꾸고 `--` 를 붙인다: `color/bg/canvas` 와 `color.bg.canvas` 는 모두 `--color-bg-canvas`. Light 값은 `:root`, Dark 값은 `.dark`(또는 프로젝트의 다크 선택자)에 둔다.
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
3. 경계선 토큰(`breakpoint/tablet`, `breakpoint/pc`)은 Tailwind 테마 `screens` 로 등록한다. 기본은 `md` 768px, `xl` 1280px.
4. 글자 크기, 간격, 모서리 토큰은 Tailwind 테마에 등록해 `text-body`, `p-4`, `rounded-md` 처럼 토큰 이름으로 쓴다.
5. 모션 토큰(`motion/duration/*`, `motion/easing/*`)은 `--motion-duration-fast`, `--motion-easing-enter` 같은 CSS 변수로 두고 transition 과 animation 에서 그 변수만 쓴다.

## 4. 스타일 규칙

- 색, 간격, 글자, 모서리, 모션은 3절의 변수와 테마 토큰만 쓴다. 임의 값(`bg-[#2F6FED]`, `p-[13px]`, `duration-[180ms]`)을 쓰지 않는다.
- 다크 모드는 CSS 변수가 바뀌는 것으로 끝낸다. 컴포넌트에 `dark:` 변형을 늘어놓지 않는다.
- 클래스 조합은 `cn()` 유틸로 한다. 조건부 클래스를 문자열로 잇지 않는다.
- 전역 CSS 는 `globals.css` 의 토큰과 Tailwind 레이어 설정뿐이다. 컴포넌트별 CSS 파일을 만들지 않는다.

## 5. 컴포넌트 규칙

- 필요한 컴포넌트는 먼저 shadcn/ui 에서 찾아 `pnpm dlx shadcn@latest add <이름>` 으로 추가한다.
- 없으면 shadcn/ui 컴포넌트를 조합해 기능 컴포넌트를 만든다. 그래도 안 될 때만 새로 만들되 shadcn/ui 와 같은 구조(`cva` variant, `cn`, Radix 또는 Base UI 프리미티브, `forwardRef` 와 `asChild`)로 쓴다.
- `components/ui/` 아래 shadcn/ui 가 생성한 파일은 CLI 로 다시 생성할 수 있어야 하므로 손으로 크게 고치지 않는다. 변형이 필요하면 감싸는 컴포넌트를 만들거나 `cva` variant 를 추가한다.
- 디자인 원본의 variant(`State=Pressed`, `Size=Sm`)는 shadcn/ui variant 나 상태로 옮긴다. 대응은 `developer:handoff` 가 `design/<컨셉>/handoff.md` 에 적고, 같은 원본 컴포넌트를 두 군데서 다르게 옮기지 않는다.
- 다른 컴포넌트 라이브러리는 프로젝트가 이미 쓰고 있을 때만 쓴다. 새로 들이기 전에 사용자에게 묻는다.
