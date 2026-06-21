---
name: varco-nano-banana
description: >-
  VARCO nano_banana(구글 이미지 생성 모델)로 게임/앱용 2D 이미지 에셋을 만든다 —
  UI 아이콘·버튼·패널 배경·HUD 요소·스프라이트·일러스트·배경 그림 등. VARCO 에는
  전용 text-to-image 가 없고 generative-edit inpaint 에 전체 마스크를 주면 t2i 로
  동작하는데, 이 스킬이 그 레시피를 단일/배치로 감싼다. 사용자가 "이미지/아이콘/
  스프라이트/UI 에셋/배경 만들어줘", "VARCO/나노바나나로 그려줘", "2D 에셋 뽑아줘",
  "텍스처/일러스트 생성" 등을 말하거나, 게임 UI·2D 아트 에셋을 절차적으로 다량
  생성해야 하면 — "nano_banana"나 "VARCO"를 직접 말하지 않아도 — 이 스킬을 쓴다.
  (오디오·TTS·음성변환·image-to-3D 는 unity-varco 스킬 담당.)
---

# varco-nano-banana — VARCO nano_banana 2D 이미지 에셋 생성

NC AI VARCO 의 generative-edit **inpaint** 엔드포인트를 이용해 2D 이미지(아이콘, 버튼,
패널 배경, HUD 요소, 스프라이트, 배경 일러스트 등)를 생성한다.

## 왜 inpaint 인가 (핵심 원리)

VARCO 에는 단독 text-to-image API 가 없다. 대신:

> `POST /fashion/edit/v1/inpaint` 에 **입력 이미지 전체를 덮는 흰색 마스크**를 주면,
> 그 영역 전체가 `prompt` 로 새로 그려진다 = 사실상 text-to-image.

- **출력 해상도 = 입력 base 이미지 해상도.** 그래서 base 의 width/height 가 곧 결과 크기.
- **base 배경색(`bg`)이 결과 배경 톤을 편향**시킨다. 패널 위에 얹을 거면 패널색(예
  딥 청록 `0d1f24`)을, 투명 PNG 가 필요하면 키잉하기 쉬운 단색을 쓴다.
- 모델은 `nano_banana`(구글, 깔끔한 아이콘·일러스트에 강함) 또는 `sdxl`.
- 응답은 **알파 없는 RGB PNG**. 투명이 필요하면 후처리 키잉(아래) 필요.

전체 스펙(파라미터·에러코드·과금)은 `references/api.md` 참조.

## 사전 준비

1. **API 키** — VARCO OpenAPI 키를 환경변수 `VARCO_OPENAPI_KEY` 에 둔다. 헤더
   `OPENAPI_KEY` 로 전송된다(스크립트가 자동). 키는 코드/레포에 하드코딩 금지.
2. **의존성** — Python 3.9+, `requests`, `Pillow`.
   `pip install requests pillow`
3. **접근 확인(선택, 무과금)** — 키·네트워크 점검은 GET 으로:
   `GET https://openapi.ai.nc.com/tts/lite/v1/api/voices/varco` (헤더 OPENAPI_KEY) → 200 이면 OK.

## 단일 생성

```bash
python scripts/nano_banana_gen.py \
  --prompt "flat game UI icon of a glowing battery, teal cyan accent, centered, minimal" \
  --out out/battery.png --width 512 --height 512 --bg 0d1f24
```

투명 배경 아이콘(단색 배경 위 생성 후 키잉):

```bash
python scripts/nano_banana_gen.py \
  --prompt "small coral sprite, side view, clean edges" \
  --out out/coral.png --width 512 --height 512 --bg ff00ff --alpha --alpha-tol 24
```

## 배치 생성 (권장 — 다량 에셋)

에셋이 여러 개면 매니페스트 JSON 하나로 한 번에 돌린다. `defaults` 에 공통값을 두고
`items` 에서 개별 항목만 덮어쓴다. **`style` 공통 문구로 톤을 통일**하는 게 핵심 —
한 게임의 UI 가 따로 노는 걸 막는다.

```json
{
  "defaults": {
    "width": 512, "height": 512, "bg": "0d1f24", "model": "nano_banana",
    "style": "flat game UI icon, dystopian underwater sci-fi HUD, teal cyan accent (#2EC4B6), dark deep-teal background, minimal, crisp, centered, consistent line weight",
    "alpha": false
  },
  "items": [
    { "name": "icon_battery",  "prompt": "a glowing battery cell" },
    { "name": "icon_research", "prompt": "a microscope / sample analysis" },
    { "name": "panel_bg", "prompt": "subtle dark panel background with faint hex grid and vignette",
      "width": 1024, "height": 640, "style": "dark deep-teal UI panel texture, very subtle, low contrast, no text" }
  ]
}
```

```bash
python scripts/nano_banana_gen.py --manifest assets.json --outdir out
```

각 항목은 `out/<name>.png` 로 저장된다.

## 프롬프트 작성 팁 (일관된 게임 UI 에셋)

좋은 결과의 80% 는 프롬프트와 일관성에서 나온다:

- **공통 `style` 문구를 모든 에셋에 적용**해 색·선 굵기·시점·톤을 통일한다.
- 시각 스펙을 구체적으로: `flat` / `isometric` / `pixel-art`, `centered`,
  `minimal`, `crisp vector-like`, 색은 hex 로 명시(`teal #2EC4B6`).
- 배경을 명시: `on dark deep-teal background` 또는 (투명용) `on solid magenta background`.
- UI 요소엔 보통 `no text, no letters` 를 넣어 글자 깨짐을 막는다.
- 아이콘은 정사각(512/1024), 배너·패널은 가로로 긴 비율로.

## 투명 PNG 가이드

inpaint 응답엔 알파가 없다. 두 가지 경로:

1. **그대로 합성** — 에셋이 패널 위에 놓이고 배경이 패널색과 같으면, `bg` 를 패널색으로
   두고 그대로 쓴다(자연스럽게 섞임). 별도 키잉 불필요.
2. **키잉** — 오버레이 아이콘은 `--bg ff00ff` 같은 단색 위에 생성하고 `--alpha` 로
   코너색을 투명화. 글로우/안티에일리어싱 경계는 일부 남을 수 있으니 단색 배경 +
   또렷한 실루엣 에셋에만 권장. 더 정밀히 빼려면 외부 매트 도구를 쓴다.

## 주의

- **과금** — inpaint 호출당 크레딧 차감. 대량 생성 전 매니페스트를 검토하고, 프롬프트는
  소수로 먼저 시험한 뒤 확정한다.
- **결정성 없음** — 같은 프롬프트도 호출마다 다르다(시드 파라미터 미지원). 마음에 드는
  결과가 나올 때까지 재생성하거나 후보를 여러 장 뽑아 고른다.
- **에러** — 401(키 오류) / 400(입력 위반) / 422(검증 실패) / 5xx(서버, 스크립트가 재시도).
  자세한 건 `references/api.md`.
- Unity 등 게임에 넣을 땐 임포트 설정(스프라이트 모드·압축·픽셀당 유닛)을 별도로 맞춘다.
