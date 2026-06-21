# VARCO API 엔드포인트 카탈로그

Base URL: `https://openapi.ai.nc.com`
인증: 모든 요청 헤더에 `OPENAPI_KEY: <발급받은 키>` 포함. 누락/오류 시 401.

> 각 엔드포인트의 전체 스펙(파라미터 표, 기본값, 가능값, 응답 예시)은 같은 폴더의 개별 md 파일 참조.

## Sound (Game AI) — JSON body, 오디오는 base64 문자열

| 행동 | Method | Endpoint | 필수 파라미터 | 옵션 파라미터 | 응답 | 상세 |
|---|---|---|---|---|---|---|
| 텍스트→효과음 생성 | POST | `/sound/varco/v1/api/text2sound` | `prompt` | `version`(v1/v2), `num_sample`(1~3) | `[{audio}]` 배열 | sound-text2sound.md |
| 사운드 변형 생성 | POST | `/sound/varco/v1/api/variation` | `source`(b64) | `num_sample`(1~5), `strength`(0~3), `include{begin,end}` | `[{audio}]` 배열 | sound-variation.md |
| 모노→스테레오 변환 | POST | `/sound/varco/v1/api/mono2stereo` | `source`(b64) | - | `{audio}` | sound-mono2stereo.md |
| 무한루프 사운드 생성 | POST | `/sound/varco/v1/api/looping` | `source`(b64) | `preserve{begin,end}` | `{audio}` | sound-looping.md |
| 스타일 변환(참조 오디오) | POST | `/sound/varco/v1/api/conversion` | `source`, `reference`(b64) | `ratio`(0~2), `enhance`(bool) | `{audio}` | sound-conversion.md |
| 노이즈 제거 | POST | `/sound/varco/v1/api/enhance` | `source`(b64) | - | `{audio}` (44100Hz 16bit WAV b64) | sound-enhance.md |

## 3D (Game AI) — 비동기 작업 (요청 → 폴링 → 다운로드)

| 행동 | Method | Endpoint | 필수 | 옵션 | 응답 | 상세 |
|---|---|---|---|---|---|---|
| 이미지→3D 생성 요청 | POST | `/3d/varco/v1/image-to-3d` (multipart) | `image`(PNG 파일) | `target_face_type`(tri/quad), `target_face_num`(1000~300000), `generate_texture`(bool), `seed`(-1=랜덤) | 202 `{requestId, requestTime, message}` | 3d-image-to-3d.md |
| 작업 상태 조회 | GET | `/inference/result/{requestId}` | path: `requestId` | - | 202 processing / 200 `{status:"succeeded", model_url}` / 500 failed. GLB, model_url 유효기간 7일 | 3d-image-to-3d.md |

## SyncFace (Game AI) — JSON body

| 행동 | Method | Endpoint | 필수 | 옵션 (기본값) | 응답 | 상세 |
|---|---|---|---|---|---|---|
| 음성→표정 애니메이션(블렌드셰이프) | POST | `/fa/asfa/v1.1/blendshape` | `id`, `audio`(b64) | `fps`(30), `lip_style`(balanced/clear/minimal/moderate), `face_style`(natural/energetic/stoic/timid), `emotion`(neutral/angry/happy/sad/surprise), `neck`(on/off), `eye`(on/off) | ARKit 52 blendshape weight matrix JSON (`weightMat`[numFrames×numPoses], `faceNames`) | voice-to-face.md |

## Translation (Media AI) — JSON body

| 행동 | Method | Endpoint | 필수 | 옵션 | 응답 | 상세 |
|---|---|---|---|---|---|---|
| 텍스트 번역(용어집 기반) | POST | `/mt/chat-content/v1/translate` | `TID`, `svc`("varco-translation"), `source_text`, `target_lang` | `provider`(chat/content), `source_lang`(ko,en,ja,tw,cn,de,ru,es,pt,fr) | `{..., target_text}` | translate.md |

## Voice (Media AI) — JSON body

| 행동 | Method | Endpoint | 필수 | 옵션 (기본값) | 응답 | 상세 |
|---|---|---|---|---|---|---|
| TTS 음성 합성 (lite) | POST | `/tts/lite/v1/api/synthesize` | `voice`(speaker_uuid) | `text`(최대 1200바이트, SSML 가능), `language`(korean/english/japanese/taiwanese), `properties{speed,pitch}`, `n_fm_steps`(8~20), `seed`(-1), `return_metadata`, `media_type`(wav/mp3/flac) | `{audio(b64), ssml?, metadata?, media_type?}` | text-to-speech-lite.md |
| TTS 음성 합성 (standard) | POST | `/tts/standard/v1/api/synthesize` | 동일 | 동일 | 동일 | text-to-speech-standard.md |
| TTS 화자 목록 (lite) | GET | `/tts/lite/v1/api/voices/varco` | - | - | 화자 리스트 | text-to-speech-lite.md |
| TTS 화자 목록 (standard) | GET | `/tts/standard/v1/api/voices/varco` | - | - | 화자 리스트 | text-to-speech-standard.md |
| 음성 변환 (프리셋 화자) | POST | `/vc/varco/v1/api/voice-conversion` | `audio`(b64, 최대 60초, WAV/FLAC/MP3), `speaker_uuid` | `audio_name` | `{audio}` (WAV b64) | voice-conversion.md |
| 음성 변환 (커스텀 화자) | POST | `/vc/varco/v1/api/voice-conversion-custom` | `audio`, `speaker_audio`(각 b64, 최대 60초) | `audio_name`, `speaker_name` | `{audio}` | voice-conversion-custom.md |
| 연기체 음성 변환 (프리셋) | POST | `/vc/acting/v1/api/voice-conversion` | `audio`, `speaker_uuid` | `audio_name` | `{audio}` | voice-conversion-acting.md |
| 연기체 음성 변환 (커스텀) | POST | `/vc/acting/v1/api/voice-conversion-custom` | `audio`, `speaker_audio` | `audio_name`, `speaker_name` | `{audio}` | voice-conversion-acting-custom.md |
| VC 화자 목록 | GET | `/vc/varco/v1/api/voices`, `/vc/acting/v1/api/voices` | - | - | 화자 리스트 | voice-conversion.md |

## Art Fashion (Visual AI) — multipart/form-data, 응답은 PNG image bytes

| 행동 | Method | Endpoint | 필수 | 옵션 | 상세 |
|---|---|---|---|---|---|
| 가상 착장(의상) | POST | `/fashion/vton/v1/clothes` | `clothes_image` | `model_image`, `mask_image`, `vton{category(upper_body/lower_body/dresses), generator_seed}`, `clothes_spec{gender, category, part, 치수...}` | vton-clothes.md |
| 가상 착장(악세사리) | POST | `/fashion/vton/v1/accessories` | `model_image` | `bag_image`, `hat_image`, `shoes_image`, `specs{bag_carry_style(hands/shoulder/cross), bag_size(small/medium/large)}` | vton-accessories.md |
| 헤드스왑 | POST | `/fashion/vton-headswap/v1/headswap` | `model_image`, `face_image` (100x100~3500x3500) | `headswap{prompt, generator_seed}` | headswap.md |
| 영역 지우기 | POST | `/fashion/edit/v1/eraser` | `image`, `mask_image` | - | generative-edit-eraser.md |
| 인페인트(텍스트) | POST | `/fashion/edit/v1/inpaint` | `model`(sdxl/nano_banana), `image`, `mask_image`, `prompt` | - | generative-edit-inpaint.md |
| 인페인트(이미지 참조) | POST | `/fashion/edit/v1/inpaint-image` | `image`, `mask_image`, `reference_image`, `reference_mask_image` | - | generative-edit-inpaint-image.md |
| 텍스처 교체 | POST | `/fashion/edit/v1/texture` | `image`, `mask_image`, `texture_image`, `x`, `y`, `width`, `height`, `angle` | - | generative-edit-texture.md |
| 시점 변경 | POST | `/fashion/edit/v1/perspective` | `image`, `view`(front/side/top/back/isometric) | `prompt` | generative-edit-perspective.md |
| 로고 합성 | POST | `/fashion/edit/v1/graphic` | `image`, `graphic_image`, `x`, `y`, `width`, `height`, `angle` | `texture`(embossed/debossed/embroidered/printed/metal) | generative-edit-graphic.md |
| 배경 교체 | POST | `/fashion/edit/v1/background` | `mode`(person/product), `image`(전경+회색(128,128,128) 배경) | `prompt`, `background_prompt`, `season_prompt`, `time_prompt`, `color_prompt`, `lighting_prompt`, `additional_prompt`, `output_aspect_ratio`(1:1 등 10종), `output_image_size`(1K/2K/4K) | generative-edit-background.md |
| 업스케일 | POST | `/fashion/upscale/v1/super-resolution` | `image`(최대 2048x2048) | `scale_factor`(2~6, 기본 4) | upscale.md |

## 레퍼런스 미공개 서비스

도큐먼트에는 존재하지만 API 레퍼런스가 아직 공개되지 않은 서비스 (2026-06 기준):
- **Chatbot** (Content Biz AI)
- **Gentle Words** (Content Protection AI)
- **Safety** (Content Protection AI)
- **PlugIn Sound** (Integrations — 유니티/언리얼 플러그인 안내)

## 공통 에러 코드

| 코드 | 의미 |
|---|---|
| 400 | Bad Request (입력 형식/제약 위반) |
| 401 | Unauthorized (OPENAPI_KEY 누락/오류) — `{"message":"Unauthorized","request_id":...}` |
| 422 | Validation Error (파라미터 검증 실패) |
| 500 | Internal Server Error |
