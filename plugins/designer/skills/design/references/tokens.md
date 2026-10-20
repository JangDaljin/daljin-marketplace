# tokens.json 구조

W3C Design Tokens 형식(Design Tokens Community Group Format Module)을 따른다. 그룹은 중첩 객체, 토큰은 `$type` 과 `$value` 를 가진 객체다.

```json
{
  "$extensions": {
    "daljin": {
      "concept": "household-ledger",
      "status": "draft",
      "approvedAt": null
    }
  },
  "color": {
    "primary": {
      "50":  { "$type": "color", "$value": "#EEF3FE" },
      "500": { "$type": "color", "$value": "#2F6FED" },
      "600": { "$type": "color", "$value": "#265BC4" },
      "950": { "$type": "color", "$value": "#0B1A3D" }
    },
    "neutral": {
      "0":   { "$type": "color", "$value": "#FFFFFF" },
      "50":  { "$type": "color", "$value": "#F7F8FA" },
      "900": { "$type": "color", "$value": "#15181E" },
      "950": { "$type": "color", "$value": "#0B0D11" }
    },
    "bg": {
      "canvas": {
        "$type": "color",
        "$value": "{color.neutral.50}",
        "$extensions": { "daljin": { "dark": "{color.neutral.950}" } }
      },
      "surface": {
        "$type": "color",
        "$value": "{color.neutral.0}",
        "$extensions": { "daljin": { "dark": "{color.neutral.900}" } }
      }
    },
    "text": {
      "primary": {
        "$type": "color",
        "$value": "{color.neutral.900}",
        "$extensions": { "daljin": { "dark": "{color.neutral.50}" } }
      }
    },
    "action": {
      "primary": {
        "$type": "color",
        "$value": "{color.primary.500}",
        "$extensions": { "daljin": { "dark": "{color.primary.400}" } }
      },
      "primary-text": {
        "$type": "color",
        "$value": "{color.neutral.0}",
        "$extensions": { "daljin": { "dark": "{color.neutral.950}" } }
      }
    }
  },
  "breakpoint": {
    "tablet": { "$type": "dimension", "$value": "768px" },
    "pc":     { "$type": "dimension", "$value": "1280px" }
  },
  "space": {
    "1": { "$type": "dimension", "$value": "4px" },
    "2": { "$type": "dimension", "$value": "8px" },
    "4": { "$type": "dimension", "$value": "16px" }
  },
  "radius": {
    "sm": { "$type": "dimension", "$value": "6px" },
    "md": { "$type": "dimension", "$value": "12px" }
  },
  "font": {
    "family": {
      "sans": { "$type": "fontFamily", "$value": ["Pretendard", "system-ui", "sans-serif"] }
    },
    "size": {
      "caption": { "$type": "dimension", "$value": "12px" },
      "body":    { "$type": "dimension", "$value": "16px" },
      "title-3": { "$type": "dimension", "$value": "20px" },
      "title-2": { "$type": "dimension", "$value": "24px" },
      "title-1": { "$type": "dimension", "$value": "32px" }
    }
  }
}
```

## 색 의미 토큰 목록

팔레트 단계에서 최소한 이 의미 토큰을 모두 정한다. 라이트와 다크 값을 둘 다 둔다.

| 그룹 | 토큰 | 뜻 |
| --- | --- | --- |
| `color.bg` | `canvas` | 화면 바탕 |
| | `surface` | 카드, 시트 바탕 |
| | `surface-raised` | 떠 있는 요소(모달, 드롭다운) 바탕 |
| | `subtle` | 구분용 옅은 바탕(목록 호버, 입력 바탕) |
| `color.text` | `primary` | 본문 |
| | `secondary` | 보조 설명 |
| | `disabled` | 비활성 |
| | `inverse` | 짙은 바탕 위 글자 |
| | `link` | 링크 |
| `color.border` | `default` | 기본 경계 |
| | `strong` | 강조 경계, 포커스 |
| `color.action` | `primary`, `primary-hover`, `primary-pressed`, `primary-text` | 주 행동 버튼 |
| | `secondary`, `secondary-text` | 보조 행동 |
| `color.status` | `success`, `warning`, `error`, `info` 와 각 `*-bg`, `*-text` | 상태 표시 |

## 별칭 해석

- `{color.primary.500}` 은 같은 파일의 `color.primary.500.$value` 를 가리킨다.
- 의미 토큰은 반드시 별칭이다. 의미 토큰에 색 값을 직접 쓰지 않는다. 필요한 색이 원시 단계에 없으면 원시 토큰을 추가한다.
- 다크 값은 `$extensions.daljin.dark` 에 별칭으로 둔다. 없으면 라이트 값을 그대로 쓴다.

## shadcn/ui 대응 기록

프론트엔드가 shadcn/ui 로 구현하므로 의미 토큰에는 대응하는 shadcn/ui 테마 변수를 적는다. 토큰 이름은 바꾸지 않는다.

```json
"canvas": {
  "$type": "color",
  "$value": "{color.neutral.50}",
  "$extensions": { "daljin": { "dark": "{color.neutral.950}", "shadcn": "background" } }
}
```

대응표는 `figma-structure.md` 의 shadcn/ui 대응 절에 있다.

## CSS 변수 이름

아티팩트 HTML 에서는 토큰 이름의 점을 하이픈으로 바꾸고 `--` 를 붙인다: `color.bg.canvas` 는 `--color-bg-canvas`. 라이트 값은 `:root` 에, 다크 값은 `:root[data-theme="dark"]` 와 `@media (prefers-color-scheme: dark)` 안의 `:root:not([data-theme="light"])` 에 선언한다.
