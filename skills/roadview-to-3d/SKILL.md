---
name: roadview-to-3d
description: 카카오맵 로드뷰에서 실제 명소·건물·다리를 브라우저 자동화로 캡처하고 VARCO image-to-3d로 게임용 저폴리 3D 모델(GLB)을 만드는 파이프라인. 사용자가 로드뷰, 거리뷰, 실제 건물/명소를 게임에 넣기, 한강 명소 3D화, 이미지로 3D 만들기, 실사 기반 배경 에셋을 언급하면 — "로드뷰"라는 단어가 없어도 실존 장소를 3D 에셋으로 만들려는 의도가 보이면 — 반드시 이 스킬을 사용한다. 한강오염탐사(OilBean)의 "정화된 한강" 명소 제작이 주 용도.
---

# roadview-to-3d — 로드뷰 명소 → 게임용 3D 에셋

카카오맵 로드뷰에서 실존 명소를 클린 캡처해 VARCO image-to-3d로 GLB를 만드는 파이프라인.
기획 배경·가능성 검토·체크리스트는 `PLAN.md`, 검증된 브라우저 조작 레시피와 함정 목록은 `references/browser-recipes.md` 참조.

## 파이프라인 (행동 단위)

```
1. 명소 선정      → references/hangang-landmarks.md (게임 구역 매핑)
2. 로드뷰 진입    → Playwright MCP + 검색 → 커버리지 클릭 (핀 없는 경로 권장)
3. 프레이밍       → 키보드 회전(JS focus 필수) / 화살표 이동, 매번 스크린샷 시각 확인
4. 클린 캡처      → 오버레이 일괄 숨김 후 1920×1080 스크린샷
5. 피사체 크롭    → PIL로 건물 영역만, 반드시 화면 중앙부에서 (가장자리 블러)
6. 3D 생성        → scripts/roadview_to_3d.py (업스케일 → image-to-3d → GLB)
7. Unity 임포트   → GLB를 Assets로 복사 (glTFast 필요), 폴리곤 확인
```

## 시작하기 전에

- **API 키**: `VARCO_OPENAPI_KEY` 환경변수 필요 (유저 스코프 레지스트리에 저장돼 있음. PowerShell에서 `$env:VARCO_OPENAPI_KEY = (Get-ItemProperty HKCU:\Environment).VARCO_OPENAPI_KEY`로 주입).
- **브라우저**: Playwright MCP 사용. 뷰포트를 1920×1080으로 설정 (`page.setViewportSize`).
- **Python**: Pillow, requests 필요 (`Python311` 경로의 python에 설치돼 있음).

## 단계별 실행

### 2~4단계: 로드뷰 진입과 캡처

`references/browser-recipes.md`의 스니펫을 순서대로 실행한다. 핵심 원칙:

- 진입 경로는 **커버리지 클릭(3-B)** 우선 — 검색 핀이 파노라마 캔버스에 그려지지 않아 클린함. 핀이 피사체와 안 겹치면 `a.roadview` 직행도 무방.
- 커버리지 선 클릭 좌표는 `scripts/find_line.py`(얇은 파란선 탐지 + 마커 회피)로 구한다.
- **모든 상태 전환은 스크린샷으로 확인**한다. 이 파이프라인은 각도·로딩·UI 상태 추정이 자주 틀리므로, "조작 → 캡처 → 눈으로 확인 → 다음 조작" 루프가 기본이다.
- 함정 목록(레시피 문서 0장)을 먼저 읽는다 — 토글 상태, 포커스 클릭 이동, 지도 상태에서의 오버레이 숨김 사고가 단골이다.

### 5단계: 크롭

캡처에서 피사체 박스를 눈으로 정해 PIL로 자른다. 미리보기 좌표 × (실해상도/미리보기폭) 스케일 환산.
크롭이 500px 미만이면 6단계에서 `--upscale 2`를 켠다.

### 6단계: 3D 생성 (폴리곤 예산 준수)

```bash
python scripts/roadview_to_3d.py subject.png out.glb --faces 10000 --upscale 2 --seed 42
```

- **저폴리 우선**: 10,000면(faces)으로 시작한다. 게임이 가벼워야 하므로 기본값을 올리지 않는다.
- **품질 미달 시 단계 상향**: 실루엣 붕괴/구멍/텍스처 뭉개짐이 보이면 같은 seed로 50,000 → 150,000 순서로 재생성해 비교한다. 300,000(API 최대)은 쓰지 않는다.
- 비동기 작업: 요청 → requestId → 폴링(수 분 소요) → model_url(7일 유효) → GLB 다운로드까지 스크립트가 처리.

### 7단계: Unity 확인

GLB를 `Assets/`로 복사하면 glTFast가 임포트한다. 임포트 후 인스펙터에서 버텍스/트라이앵글 수를 확인하고
PLAN.md 폴리곤 예산표와 대조한다. 런타임 로드가 필요하면 unity-varco 스킬의 `VarcoImageTo3D` + glTFast 런타임 API 참조.

## 제약 / 주의

- 카카오 로드뷰 이미지는 **Kakao 저작물** — 프로토타입/내부용. 상용 출시 전 라이선스 검토 필수.
- 카카오맵 UI 개편 시 셀렉터가 깨질 수 있다 — 레시피가 안 맞으면 스크린샷으로 현재 DOM을 재조사해 레시피 문서를 갱신한다.
- image-to-3d는 호출당 크레딧 소모 + 수 분 소요. 같은 피사체 재생성은 seed 고정 후 faces만 변경.
- 로드뷰가 닿지 않는 곳(섬 내부, 수상 구조물 근접)은 물 건너 촬영 + 크롭 + 업스케일로 대응.

## 관련 스킬

- **unity-varco**: VARCO API 전체 카탈로그(이 스킬은 그중 image-to-3d/upscale만 사용). 오염→정화 대비 연출용 이미지 가공(Inpaint/Background)도 unity-varco의 Fashion API로 가능.
