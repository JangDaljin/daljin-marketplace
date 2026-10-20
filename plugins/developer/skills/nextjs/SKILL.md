---
name: nextjs
description: Next.js(App Router) + React + TypeScript + Tailwind + shadcn/ui 프론트엔드를 개인 규약대로 만들고 고치는 하네스. 기술 스택, Next 16 변경점(async params와 cookies, proxy, Turbopack, next lint 제거), 새 프로젝트 셋업(pnpm, shadcn init, ESLint flat config, Vitest, Playwright, husky), 폴더 구조, 서버와 클라이언트 컴포넌트 경계, 데이터 호출과 인증 쿠키, 테스트, 검증 순서를 정한다. Next.js 프로젝트를 새로 만들거나 이 규약을 따르는 프론트 레포에서 화면과 컴포넌트를 추가·수정할 때, "/developer:nextjs" 요청 시 사용.
---

# Next.js 하네스

Next.js 프론트엔드 작업을 시작 전 준비, 구현, 검증, 마무리 순서로 진행한다.

공통 규칙(작업 흐름, 디자인 원본은 Figma, shadcn/ui 우선, 접근성, 모션, UI 글)은 `developer:frontend` 스킬에 있다. 이 하네스를 쓸 때 그 스킬도 함께 불러 따른다. Figma 를 코드로 옮기는 절차는 `developer:handoff` 다. 이 문서는 그 규칙을 Next.js 로 구현하는 방법만 적는다.

작업 중인 프로젝트에 정의된 규칙(문서, 린트와 빌드 설정, Pages Router 나 npm 같은 기존 선택, 이미 쓰는 컴포넌트 라이브러리)이 있으면 그 규칙이 최우선이다(`frontend` 스킬 0절). 다른 점은 사용자에게 알리고 프로젝트를 하네스에 맞게 바꾸지 않는다.

## 기술 스택

| 영역 | 선택 |
| --- | --- |
| 프레임워크 | Next.js 최신 안정 버전, App Router. Pages Router 는 쓰지 않는다 |
| 언어 | TypeScript(`strict`), React 최신 안정 버전 |
| 스타일 | Tailwind CSS v4. 디자인 토큰은 `globals.css` 의 CSS 변수로만 |
| 컴포넌트 | shadcn/ui(`components.json`, `components/ui/`). 아이콘은 lucide-react |
| 상태 | 서버 컴포넌트와 URL 상태 우선. 클라이언트 전역 상태가 꼭 필요할 때만 zustand |
| 데이터 호출 | 서버 컴포넌트에서 `fetch`. 클라이언트에서 필요하면 Route Handler 를 거친다 |
| 그 밖의 UI 유틸 | 차트 recharts, 가상 스크롤 @tanstack/react-virtual, 드래그 @dnd-kit, 날짜 date-fns. 표에 없는 것은 사용자에게 묻는다 |
| 폼 | react-hook-form + zod. 서버 검증은 Server Action 안에서 같은 zod 스키마 |
| 토스트 | sonner |
| 테스트 | Vitest + Testing Library(컴포넌트), Playwright(E2E) |
| 린트, 포맷 | ESLint flat config + typescript-eslint + `@stylistic` + `@next/eslint-plugin-next` + `eslint-plugin-jsx-a11y`. Prettier, Biome 은 쓰지 않는다 |
| 패키지 매니저 | pnpm. npm, yarn 은 쓰지 않는다 |
| Git 훅 | husky `pre-push` |

라이브러리 API 가 버전마다 달라지는 부분(Next 설정 키, shadcn/ui CLI, Tailwind v4 설정)은 작성 전에 context7 MCP 로 설치된 버전의 문서를 확인한다. Next.js 는 `node_modules/next/dist/docs/` 에 공식 문서가 동봉되어 있으니 그것을 먼저 읽는다.

## Next 16 에서 반드시 걸리는 것

학습 데이터와 다른 부분이다. 코드를 쓰기 전에 확인한다.

- `cookies()`, `headers()`, `draftMode()`, `params`, `searchParams` 는 모두 async 다. 항상 `await` 한다. 타입은 `npx next typegen` 이 만드는 `PageProps<'/경로'>` 를 쓴다.
- `middleware.ts` 는 `proxy.ts` 로, 함수명도 `proxy` 다. 런타임은 Node 고정이다. matcher 가 없으면 정적 파일까지 모든 요청에 실행되므로 negative matcher 로 제외한다.
- Turbopack 이 기본이다. 커스텀 webpack 설정이 있으면 빌드가 실패한다.
- `next lint` 가 없다. ESLint 를 직접 돌리고 `next build` 는 린트하지 않는다.
- `revalidateTag` 는 두 번째 인자가 필수다. 즉시 반영은 Server Action 안의 `updateTag`.
- Parallel route 슬롯에는 `default.tsx` 가 필수다.
- Route Handler 는 기본으로 캐시되지 않는다.
- Server Function 과 Route Handler 는 자기 라우트로 가는 POST 라, proxy 에서 그 경로를 제외하면 인증도 같이 빠진다. 인증 확인은 proxy 에만 맡기지 않고 서버 코드에서도 한다.

## 1. 시작 전 준비

### 1.1 새 프로젝트

1. `pnpm create next-app@latest <이름> --typescript --tailwind --eslint --app --src-dir --use-pnpm` 으로 만든다.
2. `pnpm dlx shadcn@latest init` 으로 shadcn/ui 를 넣는다. 스타일과 기본 색은 묻지 말고 중립으로 두고, 실제 색은 `developer:handoff` 가 Figma 토큰으로 채운다.
3. ESLint flat config 를 기술 스택 표대로 구성하고, Vitest(`vitest.config.ts`, `jsdom`, Testing Library 설정), Playwright(`playwright.config.ts`), husky `pre-push`(검증 명령 순서대로) 를 넣는다.
4. `package.json` 스크립트: `dev`, `build`, `start`, `lint`, `typecheck`(`tsc --noEmit`), `test`(Vitest), `test:e2e`(Playwright).
5. `pnpm lint && pnpm typecheck && pnpm test && pnpm build` 가 통과하는 상태에서 기능 작업을 시작한다.

### 1.2 기존 프로젝트

다음을 확인하고, 빠진 것은 바로 추가하지 말고 사용자에게 추가할지 묻는다.

- App Router 인지, `components.json` 이 있는지, Tailwind 버전
- `pnpm-lock.yaml`, ESLint flat config, husky `pre-push`
- 디자인 토큰이 이미 `globals.css` 에 있는지, 있다면 Figma 와 맞는지(`developer:handoff` 5절)

## 2. 구현

### 2.1 폴더 구조

```
src/
  app/                 라우트. 각 세그먼트에 page, layout, loading, error, (필요시) default
  components/ui/       shadcn/ui 가 생성. CLI 로만 추가하고 손으로 크게 고치지 않는다
  components/<기능>/   기능별 조합 컴포넌트. Figma 컴포넌트 이름과 맞춘다
  lib/                 유틸, API 클라이언트, zod 스키마
  hooks/               클라이언트 훅
  styles/globals.css   Tailwind 진입점과 디자인 토큰 CSS 변수
```

- 컴포넌트 파일 이름은 kebab-case, 컴포넌트 이름은 PascalCase 다. Figma 컴포넌트 `TransactionItem` 은 `components/transactions/transaction-item.tsx` 의 `TransactionItem` 이다.
- 한 파일에 컴포넌트 하나. 변형은 `cva` variant 로 두고 파일을 늘리지 않는다.

### 2.2 서버와 클라이언트 경계

- 기본은 서버 컴포넌트다. 상호작용(이벤트, 상태, 브라우저 API)이 필요한 가장 작은 단위만 `"use client"` 로 뗀다.
- 데이터는 서버 컴포넌트에서 가져와 props 로 내린다. 클라이언트 컴포넌트가 직접 외부 API 를 부르지 않는다.
- 비밀값(API 키, 토큰)은 서버에만 둔다. 클라이언트가 보호된 API 를 써야 하면 Route Handler 가 쿠키에서 토큰을 읽어 대신 부른다.
- 인증 토큰은 httpOnly 쿠키에만 둔다. localStorage 에 두지 않는다.

### 2.3 스타일

- 색, 간격, 글자, 모서리는 `globals.css` 의 CSS 변수(Figma 토큰)와 그것을 가리키는 Tailwind 테마 토큰만 쓴다. 임의 값(`bg-[#2F6FED]`, `p-[13px]`)을 쓰지 않는다.
- 다크 모드는 `data-theme` 속성 또는 `.dark` 클래스로 CSS 변수를 바꾼다. 컴포넌트에 `dark:` 변형을 늘어놓지 않는다.
- 반응형은 Figma 토큰의 경계선을 Tailwind 테마 `screens` 로 등록해 쓴다. 기본은 `md` 768px, `xl` 1280px.

### 2.4 로딩, 오류, 빈 상태

- 라우트마다 `loading.tsx`(Skeleton), `error.tsx` 를 둔다.
- 목록은 빈 상태 컴포넌트를 반드시 가진다. Figma 에 빈 상태 디자인이 없으면 사용자에게 알린다(`frontend` 스킬 2절).

## 3. 테스트

- 컴포넌트 테스트는 Vitest + Testing Library 로 역할(`getByRole`)과 라벨로 요소를 찾는다. 테스트 ID 는 마지막 수단이다.
- 상호작용은 `userEvent` 로 한다. 키보드 조작 경로를 한 번은 테스트한다.
- 화면 흐름(로그인, 주요 작업 하나)은 Playwright E2E 로 쓴다. 외부 API 는 Route Handler 경계에서 모킹한다.
- 스냅샷 테스트는 쓰지 않는다.

## 4. 검증 순서

커밋 전과 `pre-push` 에서 같은 순서로 돌린다. 하나라도 실패하면 커밋하지 않는다.

```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

E2E 는 `pnpm test:e2e` 로 따로 돌리고, 화면 흐름을 바꾼 작업에서는 필수다.

## 5. 마무리

- `frontend` 스킬 1.3 의 UI 검토를 돌린다.
- 핸드오프로 구현한 화면이면 `design/<컨셉>/handoff.md` 의 상태를 갱신한다(`developer:handoff` 6절).
- 커밋 메시지는 `frontend` 스킬 1.5 를 따른다.
