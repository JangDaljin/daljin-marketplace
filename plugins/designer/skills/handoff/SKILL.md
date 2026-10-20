---
name: handoff
description: 승인된 디자인을 개발자가 판단 없이 구현할 수 있게 넘기는 4단계 스킬. 전달 점검표(토큰과 모션 값, 컴포넌트 상태와 최악 데이터, 화면과 구간, 로딩·빈·오류 상태, 문구, Figma 노드 id)로 빠진 것을 찾아 앞 단계로 돌려보내고, 전달 명세 design/<컨셉>/handoff.md 를 쓴다. "개발자한테 넘기자", "핸드오프", "전달 준비", "구현 넘겨도 돼?", "/designer:handoff" 요청 시, 그리고 designer:figma-sync 가 끝난 뒤 사용. 개발자 쪽 받는 절차는 developer:implement-design 이다.
---

# 핸드오프 (넘기기)

승인되고 Figma 에 반영된 디자인을 개발자에게 넘긴다. 개발자(`developer:implement-design`)는 여기서 넘긴 것만 보고 구현하며 디자인 판단을 하지 않는다. 그러므로 빠진 결정이 있으면 넘기지 않고 앞 단계로 돌아간다. 공통 규칙은 `designer:design` 을 따른다.

## 1. 시작 조건

- `tokens.json` 이 `approved` 이고, 넘길 화면과 컴포넌트가 승인 주석을 가지며, `figma.md` 에 Figma 반영 기록이 있어야 한다.
- Figma 를 쓰지 않는 프로젝트면 승인된 아티팩트와 `tokens.json` 만으로 넘긴다. 그 사실을 명세에 적는다.

## 2. 전달 점검표

항목마다 결과물의 어디에 있는지 확인한다. 하나라도 없으면 넘기지 않고 해당 단계(`designer:palette`, `designer:layout`, `designer:figma-sync`)로 돌아가 채운 뒤 다시 승인받는다.

| 항목 | 있어야 할 곳 | 없으면 |
| --- | --- | --- |
| 색, 간격, 글자, 모서리, 경계선 토큰 | `tokens.json`, Figma Variables | palette 또는 layout |
| 모션 토큰과 어느 전환에 쓰는지 | `tokens.json` 의 `motion.*`, 아티팩트 요소 옆 주석, Figma 컴포넌트 설명 | layout 4절 |
| 컴포넌트 상태(default, hover, pressed, disabled, 필요 시 selected, error) | `component-*.html`, Figma variants | layout 5절 |
| 최악 데이터 상태 | `component-*.html` 마지막 변형, Figma `State=WorstCase` | layout 5절 |
| 화면의 세 구간(모바일, 태블릿, PC) | `layout-*.html`, Figma `화면/구간 폭` 프레임 | layout 4절 |
| 로딩, 빈 상태, 오류 상태 | `layout-*.html` 아래쪽, Figma 화면 variant | layout 4절 |
| 라이트와 다크 | 모든 아티팩트의 전환 버튼, Figma `Color` 모드 | palette 또는 layout |
| UI 문구(버튼, 빈 상태, 오류 메시지) | 아티팩트 본문. 자리표시 글이 아닌 실제 문구 | layout 4절 |
| Figma 노드 id | `figma.md` | figma-sync 5절 |

- 의도적으로 정하지 않은 것(예: 서버 응답 시간에 따라 달라지는 로딩 길이)은 "미결정" 으로 명세에 적고 개발자가 물어볼 사람을 적는다. 모르고 빠뜨린 것과 구분한다.
- 점검표 밖이라도 개발자가 구현하다 판단해야 할 것이 보이면 지금 결정해 결과물에 적는다.

## 3. 전달 명세 쓰기

`design/<컨셉>/handoff.md` 를 다음 형식으로 쓴다. 개발자는 이 파일부터 읽는다.

```markdown
# 전달 명세

컨셉: household-ledger
넘긴 날: 2026-10-20
원본 순서: Figma(https://www.figma.com/design/<fileKey>/<name>) → design/household-ledger/tokens.json 과 승인 아티팩트

## 넘기는 것

| 종류 | 이름 | 위치 | 상태 |
| --- | --- | --- | --- |
| 토큰 | color, space, radius, font, motion, breakpoint | tokens.json, Figma Variables(Color·Space·Radius·Type·Motion) | 승인 2026-10-18 |
| 컴포넌트 | TransactionItem | Figma 56:78, component-transaction-item.html | 상태 5개 + WorstCase |
| 화면 | Home | Figma 90:12·90:13·90:14, layout-home.html | 세 구간, 로딩·빈·오류 포함 |

## 모션

| 전환 | 토큰 |
| --- | --- |
| 거래 아이템 눌림 | motion.duration.fast, motion.easing.move |
| 시트 열림 | motion.duration.normal, motion.easing.enter |

## 미결정

| 항목 | 이유 | 물어볼 사람 |
| --- | --- | --- |
| 거래 목록 한 페이지 개수 | 서버 응답 크기에 따라 다름 | 백엔드 담당 |

## 이번에 넘기지 않는 것

설정 화면(디자인 미승인)
```

- 넘기지 않는 것을 분명히 적는다. 개발자가 그 화면을 만들지 않게 하기 위해서다.
- 넘긴 뒤 디자인이 바뀌면 바뀐 항목만 갱신하고 날짜를 올린다. 개발자가 `implementation.md` 에 기록한 대응은 건드리지 않는다.

## 4. 넘기기

- 명세 링크와 함께 넘긴 것, 미결정 사항, 넘기지 않는 것을 사용자에게 한 번에 보고한다.
- 개발자가 구현 중 디자인 질문을 올리면(사용자가 전달) 코드에서 해결하게 두지 않고 결과물을 고쳐 다시 넘긴다. 작은 변경도 앞 단계 승인을 거친다.
