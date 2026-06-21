# VARCO inpaint API 레퍼런스 (이미지 생성용)

조사 시점 2026-06, `https://api.varco.ai/ko/reference` 기준. 검증: OilBean 프로젝트에서
nano_banana 전체 마스크 t2i 로 실제 PNG 생성 E2E 확인.

## 엔드포인트

```
POST https://openapi.ai.nc.com/fashion/edit/v1/inpaint
Header:  OPENAPI_KEY: <발급키>
Body:    multipart/form-data
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `model` | string | Yes | `nano_banana` 또는 `sdxl` |
| `image` | bytes(PNG) | Yes | 입력(base) 이미지. **출력 해상도 = 이 이미지 해상도** |
| `mask_image` | bytes(PNG, L) | Yes | 흰색(255)=재생성 영역. 전체 흰색이면 t2i |
| `prompt` | string | Yes | 채울 내용 설명 |

- **응답**: 200 → `image/png` 바이트(알파 없는 RGB). 400 / 422 / 500.
- **시드 파라미터 없음** → 호출마다 결과가 다르다.

## 인접 엔드포인트 (참고)

| 행동 | Endpoint | 비고 |
|---|---|---|
| 인페인트(이미지 참조) | `/fashion/edit/v1/inpaint-image` | 마스크 영역을 reference 이미지로 채움 |
| 영역 지우기 | `/fashion/edit/v1/eraser` | image + mask |
| 배경 교체 | `/fashion/edit/v1/background` | 전경+회색배경 입력, 다양한 prompt 옵션 |
| 업스케일 | `/fashion/upscale/v1/super-resolution` | 입력 최대 2048², scale 2~6 |
| 시점 변경 | `/fashion/edit/v1/perspective` | front/side/top/back/isometric |
| 이미지→3D | `/3d/varco/v1/image-to-3d` | 비동기, GLB. (unity-varco 스킬) |

전체 카탈로그·오디오/TTS/음성/번역/3D 는 `unity-varco` 스킬의 references 참조.

## 인증 점검 (무과금 GET)

```
GET https://openapi.ai.nc.com/tts/lite/v1/api/voices/varco
Header: OPENAPI_KEY: <키>
```
200 이면 키·네트워크 정상. 401 이면 키 문제.

## 에러 코드

| 코드 | 의미 |
|---|---|
| 400 | Bad Request (입력 형식/제약 위반) |
| 401 | Unauthorized (OPENAPI_KEY 누락/오류) |
| 422 | Validation Error (파라미터 검증 실패) |
| 5xx | 서버 오류 (재시도 권장) |

## 과금

호출당 크레딧 차감. 요금표: https://api.varco.ai/ko/docs/pricing
대량 배치 전 프롬프트를 소수로 검증한 뒤 확정할 것.

## 문서가 스펙과 다를 때

VARCO 사이트는 SPA 라 일반 fetch 로 본문이 안 보인다. GraphQL `GetNavigationTree`
→ `/api/markdown?url=<markdownUrl>` 로 원문 markdown 을 받거나, 접근이 막히면
CDP/Playwright 로 브라우저 렌더 후 추출한다.
