---
name: figma-sync
description: 승인된 토큰과 레이아웃 아티팩트를 Figma MCP 로 Figma 파일에 올리고, 올라간 결과를 다시 읽어 아티팩트와 대조하는 3단계 스킬. Variables(Color Light/Dark, Space, Radius, Type), Foundations·Components·Screens 페이지 구조, 이름 규칙, figma.md 기록을 다룬다. "Figma에 올려줘", "Variables 만들어줘", "피그마 반영", "피그마랑 비교해줘", "/designer:figma-sync" 요청 시 사용. 승인되지 않은 결과물은 올리지 않는다.
---

# Figma 반영

승인된 결과물만 Figma 에 올려 디자인 모음집을 만든다. 공통 규칙(Figma 파일 구조, Variables 컬렉션, 이름 규칙, 승인 게이트)은 `designer:design` 스킬과 `designer:design` 의 `references/figma-structure.md` 를 따른다.

## 1. 시작 조건

- `tokens.json` 이 `approved` 여야 한다.
- 올릴 화면과 컴포넌트 HTML 상단에 `approved:` 주석이 있어야 한다. 없는 파일은 올리지 않고 사용자에게 어떤 파일이 빠졌는지 알린다.
- Figma 파일 URL 을 확인한다. `design/<컨셉>/figma.md` 에 있으면 그 파일을, 없으면 사용자에게 묻는다. 새 파일을 만들어야 하면 사용자가 Figma 에서 빈 파일을 만들어 URL 을 알려 달라고 한다.

## 2. Figma MCP 확인

1. `figma` MCP 가 인증되어 있는지 확인한다. 안 되어 있으면 인증 도구를 호출하고 사용자가 브라우저에서 승인하도록 안내한다.
2. 인증 뒤 사용할 수 있는 도구 목록을 확인한다. 도구 이름과 쓰기 가능 범위는 Figma 쪽 버전에 따라 바뀌므로 이 문서에 박지 않고 매번 목록으로 확인한다.
   - 읽기: 디자인 컨텍스트, 스크린샷, 메타데이터, Variables 정의를 읽는 도구
   - 쓰기: Variables 를 만들거나 프레임과 컴포넌트를 생성하는 도구. Figma 데스크톱 앱이 열려 있어야 동작하는 도구가 있다
3. 쓰기 도구가 없거나 일부만 있으면 3절의 대체 경로를 쓰고, 무엇을 자동으로 했고 무엇을 사용자가 손으로 해야 하는지 분명히 알린다. 할 수 있는 척하지 않는다.

## 3. 올리기

순서는 Variables, Foundations, Components, Screens 다. 앞 단계가 끝나야 뒤 단계에서 바인딩할 수 있다.

### 3.1 Variables

- `tokens.json` 을 `references/figma-structure.md` 의 컬렉션과 모드로 옮긴다. 토큰 이름의 점만 빗금으로 바꾼다.
- 의미 색은 모드별로 원시 변수 별칭으로 넣는다. 값을 풀어서 넣지 않는다.
- 쓰기 도구가 없으면 Tokens Studio 가 읽는 형식의 JSON 을 `design/<컨셉>/figma-tokens.json` 으로 만들어 주고, Figma 의 Tokens Studio 플러그인으로 가져오는 방법을 안내한다.

### 3.2 Foundations

- `Colors`, `Typography`, `Spacing`, `Radius` 프레임을 만든다. 각 칸은 Variables 를 바인딩하고 토큰 이름을 글자로 적는다.

### 3.3 Components

- `component-<이름>.html` 의 variant 를 그대로 컴포넌트 세트로 만든다. variant 속성 이름은 HTML 에 적힌 것과 같게 한다.
- 색, 간격, 모서리, 글자 크기는 모두 Variables 바인딩이다.
- 쓰기 도구가 없으면 HTML 을 Figma 로 가져오는 플러그인(html.to.design 등)으로 가져온 뒤, 사용자가 Variables 바인딩만 손으로 하도록 체크리스트를 준다.

### 3.4 Screens

- `layout-<화면>.html` 의 세 구간을 `화면/Mobile 375`, `화면/Tablet 768`, `화면/PC 1440` 프레임으로 만든다. 한 화면의 프레임은 같은 섹션에 가로로 나란히 둔다.
- 화면 안에서 컴포넌트는 3.3 에서 만든 컴포넌트 인스턴스를 쓴다. 다시 그리지 않는다.

## 4. 대조

올린 뒤 반드시 다시 읽어 아티팩트와 비교한다.

1. Variables 정의를 읽어 `tokens.json` 과 이름, 값, 모드가 모두 같은지 확인한다. 다른 것은 표로 보고한다.
2. 화면 프레임 스크린샷을 읽어 아티팩트와 나란히 보고 다른 점(순서, 간격, 색)을 적는다.
3. 다른 점은 Figma 쪽을 고친다. 아티팩트가 틀린 것이면 `designer:layout` 으로 돌아가 아티팩트를 고치고 다시 승인받은 뒤 Figma 를 맞춘다.
4. 차이가 없을 때까지 반복하고, 결과를 사용자에게 보고한다.

## 5. 기록

- `design/<컨셉>/figma.md` 에 파일 URL, 페이지와 프레임의 노드 id, 마지막 동기화 시각을 `references/figma-structure.md` 형식으로 적는다.
- 보고에는 올린 것, 손으로 해야 할 것, 아티팩트와 다른 점이 남아 있는지를 넣는다.

## 6. 변경 반영

토큰이나 레이아웃이 바뀌어 다시 올릴 때는 바뀐 것만 고친다. 전체를 지우고 다시 만들지 않는다. 바뀐 토큰이 어느 컴포넌트와 화면에 쓰이는지 Variables 참조로 먼저 찾아 사용자에게 영향 범위를 알린 뒤 반영한다.
