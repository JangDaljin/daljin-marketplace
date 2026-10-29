---
name: design
description: 모든 디자인 작업에 적용하는 공통 규칙. 작업 순서와 승인 게이트(팔레트 승인 전 레이아웃 금지, 아티팩트 승인 전 Figma 금지, 전달 점검표 통과 전 핸드오프 금지), 디자인 작업 폴더와 토큰 파일(W3C Design Tokens), 토큰 이름 규칙, 기본 화면 폭과 경계선(모바일 768 미만, 태블릿 768 이상, PC 1280 이상), Figma 파일 구조, 외부 스킬(frontend-design, ui-ux-pro-max, hallmark, emil) 사용 규칙, 디자이너가 하지 않는 일(구현 코드)을 정한다. 팔레트, 레이아웃, Figma 반영 작업을 시작할 때, "/designer:design" 요청 시 사용. 단계별 스킬(designer:palette, designer:layout, designer:figma-sync, designer:handoff)과 함께 쓴다.
---

# 디자인 공통 규칙

모든 디자인 작업에 적용하는 규칙이다. 단계별 방법은 `designer:palette`, `designer:layout`, `designer:figma-sync`, `designer:handoff` 에 있다. 이 스킬과 단계별 스킬이 부딪히면 사용자에게 묻는다.

## 0. 프로젝트 규칙 우선

- 작업 중인 프로젝트에 이미 디자인 시스템, 토큰 파일, Figma 파일, 브랜드 가이드가 있으면 그것을 따르고 이 스킬의 같은 항목은 무시한다.
- 작업을 시작할 때 `design/` 폴더와 기존 토큰 파일이 있는지 먼저 확인한다. 있으면 이어서 작업하고, 이 스킬과 다른 점은 사용자에게 알린다.

## 1. 작업 순서와 승인 게이트

디자인은 팔레트, 레이아웃, Figma 반영, 핸드오프 순서로 진행한다. 단계마다 아티팩트로 증명하고 사용자 승인을 받은 뒤에만 다음 단계로 간다.

| 단계 | 스킬 | 증명물 | 다음 단계 조건 |
| --- | --- | --- | --- |
| 1 | `designer:palette` | 색 팔레트 아티팩트 | 사용자가 팔레트를 승인 |
| 2 | `designer:layout` | 화면, 컴포넌트 레이아웃 아티팩트 | 토큰 검사와 `designer:ui-review` 통과, 사용자가 레이아웃을 승인 |
| 3 | `designer:figma-sync` | Figma 파일 | 아티팩트와 Figma 가 일치 |
| 4 | `designer:handoff` | 전달 명세 `handoff.md` | 전달 점검표를 모두 통과 |

- 승인된 팔레트가 없으면 레이아웃을 만들지 않는다. 사용자가 레이아웃부터 요청해도 팔레트 단계로 돌아가 승인을 먼저 받는다.
- 아티팩트 승인이 없으면 Figma 에 아무것도 올리지 않는다.
- 승인은 사용자가 "승인", "확정", "이걸로 가자" 처럼 분명히 말한 것만 인정한다. "좋네" 같은 반응은 승인으로 보지 않고 확정할지 다시 묻는다.
- 승인 뒤 바뀌면 바뀐 단계부터 다시 승인받고, 그 이후 단계의 결과물(아티팩트, Figma)도 다시 맞춘다.
- 승인된 결과물에 없는 색, 간격, 글자 크기를 다음 단계에서 새로 만들지 않는다. 필요하면 앞 단계로 돌아가 토큰을 추가하고 승인받는다.

## 2. 디자인 작업 폴더

프로젝트 루트의 `design/<컨셉>/` 아래에 모든 결과물을 둔다. 컨셉 이름은 kebab-case 다. 사용자가 다른 위치를 지정하면 그곳을 쓴다.

| 파일 | 내용 | 만드는 단계 |
| --- | --- | --- |
| `tokens.json` | 색, 간격, 글자, 모서리 토큰. 모든 단계의 단일 원본 | palette, layout |
| `palette.html` | 팔레트 아티팩트 | palette |
| `layout-<화면>.html` | 화면 레이아웃 아티팩트 | layout |
| `component-<이름>.html` | 컴포넌트 상태 아티팩트 | layout |
| `figma.md` | Figma 파일 URL, 페이지와 노드 id, 마지막 동기화 시각 | figma-sync |
| `handoff.md` | 개발자에게 넘기는 전달 명세. 디자이너가 쓴다 | handoff |
| `implementation.md` | 개발자가 쓰는 대응과 진행 기록. 디자이너는 읽기만 한다 | 개발자(`developer:implement-design`) |

- 아티팩트 HTML 은 `tokens.json` 에서 만든다. HTML 에 색 값을 직접 쓰지 않고 CSS 변수(`--color-primary-500`)로만 쓴다. 변수 선언 블록만 토큰 값을 가진다.
- 아티팩트는 Artifact 도구로 올려 사용자에게 링크를 준다. 같은 파일을 다시 올려 같은 URL 을 유지한다.

## 3. 토큰 파일과 이름 규칙

토큰은 W3C Design Tokens 형식의 `tokens.json` 한 파일에 둔다. 상세 구조와 예시는 `references/tokens.md` 에 있다.

- 이름은 `<분류>.<역할>.<단계>` 로 짓고 소문자와 숫자만 쓴다: `color.primary.500`, `space.4`, `font.size.body`
- Figma Variables 에서는 점을 빗금으로 바꾼다: `color/primary/500`
- 색은 원시 토큰과 의미 토큰으로 나눈다.
  - 원시 토큰: 색상 단계. `color.primary.50` 부터 `950`, `color.neutral.*`, `color.success.*`, `color.warning.*`, `color.error.*`, `color.info.*`
  - 의미 토큰: 쓰임새. `color.bg.*`, `color.text.*`, `color.border.*`, `color.action.*`. 값은 항상 원시 토큰의 별칭(`{color.primary.500}`)이다.
- 레이아웃과 컴포넌트는 의미 토큰만 쓴다. 원시 토큰을 직접 쓰지 않는다.
- 라이트와 다크는 의미 토큰 하나에 두 값을 둔다. `$value` 가 라이트, `$extensions.daljin.dark` 가 다크다. 원시 토큰에는 모드가 없다.
- 승인 상태는 `$extensions.daljin.status` 에 적는다: `draft`, `approved`. 승인 날짜도 함께 적는다.

## 4. 화면 폭과 경계선

프로젝트에 정의가 없으면 모바일, 태블릿, PC 세 구간을 기본으로 쓰고, 화면 레이아웃은 세 구간을 모두 만든다. 하나만 만들고 끝내지 않는다.

| 구간 | 뷰포트 범위 | 디자인 프레임 폭 |
| --- | --- | --- |
| 모바일 | 768px 미만 | 375px |
| 태블릿 | 768px 이상 1280px 미만 | 768px |
| PC | 1280px 이상 | 1440px |

- 경계선은 `breakpoint.tablet`(768px), `breakpoint.pc`(1280px) 토큰으로 `tokens.json` 에 둔다.
- 프로젝트가 다른 경계선이나 구간 수를 정했으면 그것을 따르고, 이 표는 무시한다.
- 컴포넌트는 폭에 따라 모양이 바뀔 때만 구간별로 만든다. 바뀌지 않으면 하나만 만든다.

## 5. 접근성 기준

- 본문 글자와 배경의 대비는 4.5:1 이상(WCAG AA). 큰 글자(24px 이상 또는 19px 이상 굵게)와 UI 요소 경계는 3:1 이상.
- 라이트와 다크 모두 기준을 통과해야 승인 요청을 낸다. 통과하지 못한 조합은 숨기지 않고 아티팩트에 표시하고 대안을 함께 낸다.
- 색만으로 상태를 구분하지 않는다. 아이콘, 글자, 모양을 함께 둔다.

## 6. Figma 파일 구조

Figma 파일은 디자인 모음집이다. 시안이나 실험은 올리지 않고 승인된 것만 올린다. 상세 구조는 `references/figma-structure.md` 에 있다.

| 페이지 | 내용 |
| --- | --- |
| `Foundations` | 색, 글자, 간격, 모서리 토큰을 보여 주는 프레임 |
| `Components` | 컴포넌트와 variants |
| `Screens` | 화면 프레임. 기기 폭별로 나란히 |

- 토큰은 Variables 로 올린다. 컬렉션은 `Color`(모드 `Light`, `Dark`), `Space`, `Radius`, `Type`.
- 프레임과 컴포넌트 이름은 `화면/구간 폭` 또는 `컴포넌트/상태` 로 짓는다: `Home/Mobile 375`, `Home/Tablet 768`, `Home/PC 1440`, `TransactionItem/Pressed`
- 컴포넌트 색은 Variables 를 바인딩한다. 값을 직접 넣지 않는다.

## 7. 외부 스킬

디자인 안목과 검토 지식은 외부 스킬에서 빌려 쓴다. 이 스킬과 단계별 스킬이 유일한 진행자이고, 외부 스킬은 단계마다 불러 쓰는 자문이다.

- 외부 스킬의 판단 지식(색, 서체, 구조, 모션, 접근성 규칙)만 가져온다. 외부 스킬의 흐름 지시(테마를 고르라, 토큰을 생성하라, 바로 코드를 쓰라, 여러 버전을 스위처로 만들라)는 따르지 않는다. 결과물은 항상 2절의 작업 폴더와 3절의 토큰 형식이다.
- Claude Code에서는 외부 스킬이 designer 의 의존 플러그인으로 함께 설치된다. Codex에서는 원본 저장소의 Codex용 스킬 설치 방법에 따라 별도로 설치한다. 그래도 없으면(의존성 설치 실패) 그 단계를 건너뛰고 사용자에게 필요한 스킬과 설치 방법을 알린다(Claude Code: `claude plugin install <이름>@daljin-marketplace`). 설치를 대신 하지 않는다.
- 외부 스킬끼리 조언이 다르면 접근성 기준(5절)을 먼저 지키고, 그다음은 이 브리프에 더 구체적인 쪽을 고른 뒤 승인 요청에 그 선택을 적는다.

| 스킬 | 설치 | 쓰는 단계 | 쓰지 않는 것 |
| --- | --- | --- | --- |
| `frontend-design:frontend-design` | 의존 플러그인 `frontend-design` | palette 설계 전, layout 아티팩트 전 | 없음 |
| `ui-ux-pro-max:ui-ux-pro-max` | 의존 플러그인 `ui-ux-pro-max`. Python 3 필요 | palette 핵심 색(`--domain color`, `style`), layout 서체(`--domain typography`), 승인 전 점검(`--domain ux`) | 같이 설치되는 `design-system`, `brand`, `slides`, `banner-design`, `ui-styling`, `design` 스킬. 토큰은 우리 형식으로만 만든다 |
| `hallmark:hallmark` | 의존 플러그인 `hallmark` | palette 인터뷰에서 참고 자료가 있을 때 `study`, layout 의 랜딩·마케팅 화면 구조, 승인 전 `audit` | 기본 동사(페이지 생성)와 테마 선택. 21개 테마 중 고르지 않는다 |
| `emil-skills:animate`, `emil-skills:break-ui`, `emil-skills:review-animations`, `emil-skills:mobile-native`, `emil-skills:apple-design` | 의존 플러그인 `emil-skills`(15개가 함께 설치된다) | layout 모션, 컴포넌트 최악 데이터 상태, 승인 전 모션 검토, 모바일 구간 점검 | 나머지 emil 스킬(`write-swift`, `ask-sonner`, `pick-ui-library`, `animate-expo`, `prototype`)은 쓰지 않는다 |
| `designer:ui-review` | designer 내장 | layout 승인 전 점검 | 없음 |

## 8. 디자이너가 하지 않는 일

디자이너의 구현은 디자인 구현(팔레트와 레이아웃 아티팩트, Figma)이다. 그것이 어떤 언어나 컴포넌트 라이브러리로 코드가 되는지는 디자이너의 관심사가 아니다. 컴포넌트와 토큰은 구현 라이브러리가 아니라 역할로 이름 짓는다. 반대로 디자인 판단은 전부 디자이너의 일이다. 개발자는 결과물을 그대로 구현만 하므로, 모션 값, 최악 데이터 상태, 빈 상태 문구처럼 구현에 필요한 디자인 결정은 빠짐없이 결과물(토큰, 아티팩트, Figma)에 적고 `designer:handoff` 의 점검표로 확인한 뒤 넘긴다.

- CSS, React, Tailwind 설정 같은 구현물을 만들지 않는다. 아티팩트 HTML 은 증명용이지 구현물이 아니다.
- 특정 프레임워크나 컴포넌트 라이브러리를 염두에 두고 이름이나 구조를 맞추지 않는다. 그 대응은 개발자 페르소나의 받는 스킬(`developer:implement-design`)이 한다.
- 넘긴 디자인을 코드로 구현하는 일은 개발자 페르소나(`developer:frontend`, `developer:implement-design`)의 일이다. 디자이너는 `designer:handoff` 로 빠짐없이 넘기는 데서 끝낸다.
- 사용자 승인 없이 토큰 값을 바꾸지 않는다.

Codex에서 `플러그인:스킬` 표기는 해당 플러그인의 `skills/<스킬>/SKILL.md`를 뜻한다. Artifact 도구나 `artifact-design`이 없으면 HTML 파일을 저장하고 사용 가능한 로컬 미리보기 또는 브라우저로 보여 준 뒤 같은 승인 절차를 따른다.
