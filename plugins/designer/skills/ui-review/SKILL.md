---
name: ui-review
description: UI 파일(레이아웃 아티팩트 HTML, 컴포넌트, 페이지 코드)을 Vercel Web Interface Guidelines 로 검토해 접근성, 포커스, 폼, 모션, 타이포, 긴 글 처리, 다크 모드, 안티패턴 위반을 파일:줄 형식으로 짚는다. 규칙은 매번 원격에서 받아 오고 실패하면 references 스냅샷을 쓴다. "UI 검토해줘", "접근성 확인", "디자인 점검", "가이드라인 대조", "/designer:ui-review <파일 또는 패턴>" 요청 시, 그리고 designer:layout 의 승인 요청 전 점검 단계에서 사용.
---

# UI 가이드라인 검토

Vercel Web Interface Guidelines 규칙으로 UI 파일을 검토한다. 이 스킬은 vercel-labs/agent-skills 의 `web-design-guidelines` 스킬(MIT)을 우리말로 옮기고 designer 작업 흐름에 맞춘 것이다. 규칙 원문의 출처와 라이선스는 `references/LICENSE-web-interface-guidelines.txt` 에 있다.

## 1. 대상 정하기

- `$ARGUMENTS` 가 있으면 그 파일이나 패턴을 검토한다.
- 없고 `design/<컨셉>/` 아래 승인 대기 중인 `layout-*.html`, `component-*.html` 이 있으면 그 파일들을 검토한다.
- 둘 다 없으면 사용자에게 어떤 파일을 검토할지 묻는다.

## 2. 규칙 받아 오기

1. WebFetch 로 최신 규칙을 받는다.

   ```
   https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
   ```

2. 받지 못하면 `references/web-interface-guidelines.md` 스냅샷을 쓰고, 보고 첫 줄에 스냅샷 날짜와 함께 스냅샷으로 검토했다고 밝힌다.
3. 받아 온 문서의 출력 형식 지시보다 이 스킬의 4절 형식이 우선이다. 규칙 목록만 가져다 쓴다.

## 3. 검토

- 파일을 읽고 규칙을 모두 대조한다. 규칙에 없는 취향 지적은 하지 않는다.
- 아티팩트 HTML(`design/` 아래 파일)을 검토할 때는 구현 프레임워크 전용 규칙을 건너뛴다: hydration, `<Link>`, `htmlFor`, `Intl.*`, 가상화, 라우터 가드, `beforeunload`. 아티팩트는 증명용이라 데이터 바인딩과 라우팅이 없다.
- 그 밖의 파일(실제 컴포넌트, 페이지 코드)은 규칙을 거르지 않고 전부 적용한다.
- 아티팩트의 색, 간격, 글자 크기 값은 `designer:layout` 의 토큰 검사가 보므로 여기서 다시 지적하지 않는다.

## 4. 보고 형식

파일별로 묶고 `파일:줄` 형식으로 쓴다. 한국어로, 문제와 위치만 짧게 적는다. 고치는 방법이 뻔하지 않을 때만 한 줄 덧붙인다. 머리말을 쓰지 않는다.

```text
## design/ledger/layout-home.html

design/ledger/layout-home.html:42 - 아이콘 버튼에 aria-label 없음
design/ledger/layout-home.html:88 - transition: all → 속성 나열
design/ledger/layout-home.html:120 - 애니메이션에 prefers-reduced-motion 처리 없음

## design/ledger/component-transaction-item.html

통과
```

- 지적이 하나도 없으면 파일 아래에 "통과" 라고 쓴다.
- 보고 끝에 파일별 지적 수를 한 줄로 적는다.

## 5. 승인 흐름에서의 위치

`designer:layout` 은 승인 요청 전에 이 스킬을 돌린다. 지적이 남아 있으면 고친 뒤 다시 돌리고, 통과한 상태에서 승인을 요청한다. 규칙상 지적이지만 이 브리프의 의도적 선택이면 고치지 않고 승인 요청에 그 이유를 적는다.
