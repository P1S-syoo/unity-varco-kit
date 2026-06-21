---
name: unity-varco
description: NC AI의 VARCO API(https://api.varco.ai)를 유니티 인게임에서 활용하기 위한 스킬. 효과음 생성(text2sound), 사운드 변형/루프/노이즈제거, TTS 음성 합성, 음성 변환(voice conversion), 음성→표정 애니메이션(SyncFace 블렌드셰이프), 텍스트 번역, 이미지→3D 모델 생성, 이미지 편집(가상 착장/인페인트/배경교체/업스케일) 등을 호출한다. 사용자가 VARCO, 바르코, AI 효과음, AI 보이스, TTS, 음성변환, 립싱크/페이셜 애니메이션, 인게임 번역, image-to-3d 등을 언급하거나 유니티에서 생성형 AI API 연동이 필요하면 — "VARCO"를 직접 말하지 않아도 — 반드시 이 스킬을 사용한다.
---

# unity-varco — VARCO API 유니티 연동

NC AI의 VARCO API Platform을 유니티 게임 런타임에서 호출하기 위한 스킬.
조사 시점: 2026-06-10, API 레퍼런스 기준 (https://api.varco.ai/ko/reference).

## 핵심 정보

- **Base URL**: `https://openapi.ai.nc.com`
- **인증**: 모든 요청 헤더에 `OPENAPI_KEY: <키>` — 누락/오류 시 401
- **키 보안**: 클라이언트 빌드에 하드코딩 금지. 서버 경유 또는 보안 설정에서 주입할 것 (키 유출 = 크레딧 무단 사용)
- **과금**: 호출당 크레딧 차감. 요금은 https://api.varco.ai/ko/docs/pricing 참조

## 무엇을 할 수 있나 (행동 카탈로그)

| 분류 | 행동 | 스크립트 / 메서드 |
|---|---|---|
| Sound | 텍스트로 효과음 생성 (1~3개 샘플) | `VarcoSound.TextToSound` |
| Sound | 기존 사운드의 변형 버전 생성 | `VarcoSound.Variation` |
| Sound | 모노 → 스테레오 변환 | `VarcoSound.MonoToStereo` |
| Sound | 끊김 없는 루프(BGM/환경음) 생성 | `VarcoSound.Looping` |
| Sound | 참조 오디오 스타일로 변환 | `VarcoSound.Conversion` |
| Sound | 노이즈 제거 | `VarcoSound.Enhance` |
| 3D | 이미지 1장 → 3D 모델(GLB) 생성 (비동기) | `VarcoImageTo3D.Request` → `WaitForModelUrl` → `DownloadModel` |
| SyncFace | 음성 → ARKit 52 블렌드셰이프 표정 애니메이션 | `VarcoSyncFace.GenerateBlendshape`, `VarcoBlendshapeResult.ApplyFrame` |
| Voice | TTS 음성 합성 (lite/standard, 화자/속도/피치) | `VarcoTts.Synthesize`, `GetVoicesJson` |
| Voice | 음성 변환 (프리셋/커스텀 화자, 일반/연기체) | `VarcoVoiceConversion.Convert`, `ConvertCustom`, `GetVoicesJson` |
| Translation | 게임 채팅/콘텐츠 번역 (10개 언어) | `VarcoTranslate.Translate` |
| Fashion | 가상 착장 (의상/악세사리/헤드스왑) | `VarcoFashion.TryOnClothes`, `TryOnAccessories`, `Headswap` |
| Fashion | 이미지 편집 (지우기/인페인트/텍스처/시점/로고/배경) | `VarcoFashion.Eraser`, `InpaintText`, `InpaintImage`, `ReplaceTexture`, `Perspective`, `Graphic`, `Background` |
| Fashion | 이미지 업스케일 (2~6배) | `VarcoFashion.Upscale` |

레퍼런스 미공개(도큐먼트만 존재): Chatbot, Gentle Words(욕설 순화), Safety. 필요 시 https://api.varco.ai/ko/docs 재확인.

## 작업 흐름

1. **엔드포인트 스펙 확인** — `references/endpoint-catalog.md`에서 해당 행동의 파라미터/제약을 본다. 더 깊은 스펙(가능값, 응답 예시)은 `references/<페이지명>.md` 개별 파일.
2. **스크립트 복사** — `scripts/`의 C# 파일을 유니티 프로젝트(`Assets/Scripts/Varco/` 권장)로 복사한다. `VarcoApiClient.cs` + `VarcoAudioUtil.cs`는 공통 필수, 나머지는 쓰는 행동만.
3. **키 설정** — 게임 초기화 시 `VarcoApiClient.ApiKey = "<발급키>";` 1회 설정.
4. **호출** — 모든 메서드는 `async Task` 기반, 실패 시 null 반환 + 한글 에러 로그. 메인 스레드에서 `await` 가능.

```csharp
// 예시: NPC 대사 TTS 재생
VarcoApiClient.ApiKey = mySecureKey;
AudioClip clip = await VarcoTts.Synthesize("어서 오세요, 모험가님!", speakerUuid);
if (clip != null) {
    audioSource.PlayOneShot(clip);
}
```

```csharp
// 예시: 효과음 생성 후 루프 처리
AudioClip[] samples = await VarcoSound.TextToSound("sword slash metallic", numSample: 3);
AudioClip loop = await VarcoSound.Looping(samples[0]);
```

## 주의사항 / 제약

- **오디오 입출력은 base64 WAV** — `VarcoAudioUtil`이 AudioClip ↔ WAV base64 변환을 담당. 업로드는 16bit PCM으로 인코딩, 다운로드 디코딩은 PCM 16/24/32bit + **IEEE float 32bit** 지원(실측: TTS lite 응답이 float32 WAV였음). 음성 변환류 입력은 **최대 60초**.
- **TTS `text`는 최대 1,200바이트(UTF-8)**, SSML 입력 가능(SSML 사용 시 다른 옵션 무시). `voice`(speaker_uuid)는 화자 목록 API로 먼저 조회해야 한다. 화자 목록 응답 스키마(실측): `[{"speaker_uuid", "speaker_name", "saas_name", "description"}]`.
- **Image to 3D만 비동기 작업** (202 + requestId → 폴링). `model_url`(GLB) 유효기간 7일. GLB 런타임 로드는 glTFast 등 별도 임포터 필요. 입력은 PNG만.
- **SyncFace 응답의 weightMat은 2차원 배열**이라 JsonUtility로 파싱 불가 → `VarcoSyncFace.cs`는 Newtonsoft.Json 필요 (`com.unity.nuget.newtonsoft-json` 패키지).
- **Fashion 계열은 multipart/form-data, 응답은 PNG 바이트** → Texture2D 변환까지 스크립트가 처리. Headswap은 100x100~3500x3500, Upscale 입력은 최대 2048x2048.
- **Translate는 `TID`(트랜잭션 ID)와 `svc: "varco-translation"` 필수** — 스크립트가 자동 생성/설정.
- WebGL 빌드는 CORS 정책에 따라 직접 호출이 막힐 수 있으니 서버 프록시를 고려한다.
- 에러 공통: 400(입력 제약 위반), 401(키 오류), 422(파라미터 검증 실패), 500(서버 오류).

## 스크립트 구성 (scripts/)

| 파일 | 역할 |
|---|---|
| `VarcoApiClient.cs` | 공통 코어: 인증 헤더, JSON/multipart/GET 전송, 다운로드, 배열 JSON 파서 |
| `VarcoAudioUtil.cs` | AudioClip ↔ WAV base64 변환 |
| `VarcoSound.cs` | 효과음 생성/변형/스테레오/루프/스타일변환/노이즈제거 (6개 행동) |
| `VarcoTts.cs` | TTS 합성 + 화자 목록 (lite/standard) |
| `VarcoVoiceConversion.cs` | 음성 변환 프리셋/커스텀 × 일반/연기체 + 화자 목록 |
| `VarcoSyncFace.cs` | 블렌드셰이프 생성 + SkinnedMeshRenderer 적용 헬퍼 |
| `VarcoTranslate.cs` | 텍스트 번역 |
| `VarcoImageTo3D.cs` | 3D 생성 요청/폴링/다운로드 |
| `VarcoFashion.cs` | 가상 착장/이미지 편집/업스케일 (11개 행동) |

## 검증 이력

2026-06-10 OilBean 프로젝트(Unity 6000.3.11f1)에서 실 API 호출 E2E 검증 완료: Translate(en→ko) ✓, TTS 화자 목록 ✓, TTS lite 합성 → AudioClip 변환 → wav 저장 ✓. API 키는 유저 환경변수 `VARCO_OPENAPI_KEY`로 관리하고 `VarcoSecrets.LoadApiKey()`가 자동 로드한다(스크립트 포함).

## 스펙이 문서와 다를 때

API가 422/400을 반환하면 `references/`의 해당 md에서 파라미터 표(기본값·가능값·필수 여부)를 다시 확인하고, 그래도 불일치하면 https://api.varco.ai/ko/reference 에서 최신 버전을 재조사한다 (이 문서는 2026-06 스냅샷이며, 사이트는 SPA라 일반 fetch로 안 보이고 GraphQL `GetNavigationTree` → `/api/markdown?url=<markdownUrl>`로 원문을 받을 수 있다).
