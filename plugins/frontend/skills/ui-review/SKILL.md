---
name: ui-review
description: 프론트엔드 코드(컴포넌트, 페이지, 스타일)를 Vercel Web Interface Guidelines 로 검토해 접근성, 포커스, 폼, 모션, 타이포, 긴 글 처리, 다크 모드, hydration, 안티패턴 위반을 파일:줄 형식으로 짚는다. 규칙은 매번 원격에서 받아 오고 실패하면 references 스냅샷을 쓴다. "UI 검토해줘", "접근성 확인", "가이드라인 대조", "/frontend:ui-review <파일 또는 패턴>" 요청 시, 그리고 frontend 공통 규칙의 커밋 전 UI 검토 단계에서 사용.
---

# UI 가이드라인 검토

Vercel Web Interface Guidelines 규칙으로 프론트엔드 코드를 검토한다. 이 스킬은 vercel-labs/agent-skills 의 `web-design-guidelines` 스킬(MIT)을 우리말로 옮기고 frontend 작업 흐름에 맞춘 것이다. 규칙 원문의 출처와 라이선스는 `references/LICENSE-web-interface-guidelines.txt` 에 있다.

## 1. 대상 정하기

- `$ARGUMENTS` 가 있으면 그 파일이나 패턴을 검토한다.
- 없으면 `git diff` 로 이번 작업에서 바뀐 컴포넌트, 페이지, 스타일 파일을 검토한다.
- 바뀐 파일도 없으면 사용자에게 어떤 파일을 검토할지 묻는다.

## 2. 규칙 받아 오기

1. WebFetch 로 최신 규칙을 받는다.

   ```
   https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
   ```

2. 받지 못하면 `references/web-interface-guidelines.md` 스냅샷을 쓰고, 보고 첫 줄에 스냅샷 날짜와 함께 스냅샷으로 검토했다고 밝힌다.
3. 받아 온 문서의 출력 형식 지시보다 이 스킬의 4절 형식이 우선이다. 규칙 목록만 가져다 쓴다.

## 3. 검토

- 파일을 읽고 규칙을 모두 대조한다. 규칙을 거르지 않는다. 규칙에 없는 취향 지적은 하지 않는다.
- 색, 간격, 글자 크기 값을 임의 값으로 쓴 곳(`bg-[#...]`, `p-[13px]`)은 규칙과 별개로 `frontend:nextjs` 2.3 위반이므로 함께 짚는다.

## 4. 보고 형식

파일별로 묶고 `파일:줄` 형식으로 쓴다. 한국어로, 문제와 위치만 짧게 적는다. 고치는 방법이 뻔하지 않을 때만 한 줄 덧붙인다. 머리말을 쓰지 않는다.

```text
## src/components/transactions/transaction-item.tsx

src/components/transactions/transaction-item.tsx:42 - 아이콘 버튼에 aria-label 없음
src/components/transactions/transaction-item.tsx:88 - transition: all → 속성 나열

## src/app/page.tsx

통과
```

- 지적이 하나도 없으면 파일 아래에 "통과" 라고 쓴다.
- 보고 끝에 파일별 지적 수를 한 줄로 적는다.

## 5. 작업 흐름에서의 위치

`frontend:frontend` 1.3 의 커밋 전 UI 검토 첫 단계다. 지적을 심각도와 함께 사용자에게 보고하고, 사용자가 고른 것만 고친 뒤 다시 돌린다.
