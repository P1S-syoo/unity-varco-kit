# unity-varco-kit

유니티 게임 개발과 **NC VARCO 생성형 AI** 연동을 위한 [Claude Code](https://claude.com/claude-code) 스킬 묶음입니다. 스킬 6종을 하나의 마켓플레이스 플러그인으로 제공합니다.

> 한강오염탐사(OilBean) 등 유니티 프로젝트를 만들며 다듬은 실전 스킬들입니다.

## 설치

```
/plugin marketplace add P1S-syoo/unity-varco-kit
/plugin install unity-varco-kit@unity-varco-kit
```

설치 후 Claude Code를 재시작하면 6개 스킬이 자동 트리거(키워드 감지) 또는 `/` 명령으로 동작합니다.

## 포함 스킬

| 스킬 | 용도 |
|---|---|
| **code-rules** | 유니티 C# 코딩 컨벤션·작업 절차 — K&R 스타일, try-catch + 한글 로그, 한글 한 줄 주석, 디자인패턴 decision tree, codegraph 동기화. C# 코드를 한 줄이라도 만들면 자동 적용. |
| **unity-ugui-layout** | 코드 기반 uGUI 게임 UI 제작 — HUD·패널·메뉴·게이지, UITheme 디자인 토큰, 앵커/레이아웃, 한글(CJK) tofu □ 깨짐 수정. |
| **github-commit-push** | 안전한 Git 커밋·푸시 절차 — .meta 짝 검사, 시크릿/대용량 사전 점검, conventional commit + 한글 메시지, 원자적 커밋 분리. |
| **unity-varco** | VARCO API 인게임 연동 — 효과음 생성(text2sound), 사운드 변형/루프/노이즈 제거, TTS, 음성 변환, 음성→표정 애니(SyncFace), 번역, image-to-3D, 이미지 편집(가상 착장/인페인트/배경 교체/업스케일). |
| **varco-nano-banana** | VARCO nano_banana로 2D 이미지 에셋 생성 — UI 아이콘·버튼·패널 배경·HUD·스프라이트·일러스트·배경. |
| **roadview-to-3d** | 카카오맵 로드뷰 캡처 → VARCO image-to-3d → 게임용 저폴리 GLB 생성 파이프라인. |

## VARCO API 키 설정

VARCO 계열 스킬(`unity-varco`, `varco-nano-banana`, `roadview-to-3d`)은 [NC VARCO API](https://api.varco.ai) 키가 필요합니다. **키는 코드/에셋에 하드코딩하지 않고 환경변수로 주입**합니다.

```powershell
# Windows (사용자 환경변수에 영구 등록)
setx VARCO_OPENAPI_KEY "발급받은_키"
```

- 유니티 런타임/에디터: `VarcoSecrets.cs`가 `VARCO_OPENAPI_KEY` 환경변수를 자동 로드합니다.
- 파이썬 스크립트(nano-banana / roadview): 요청 헤더 `OPENAPI_KEY`에 키를 사용합니다.

## 이미 클론/포크하신 분께 (히스토리 재작성 안내)

`2026-06-21`에 문서 예시용 API 키 문자열 하나를 git 히스토리 전체에서 제거하기 위해
**히스토리를 재작성하고 force-push** 했습니다. (실사용 불가능한 마스킹된 더미였지만,
공개 레포에 키 형태 문자열을 남기지 않기 위함입니다.)

그 이전에 받으신 분은 로컬 히스토리가 원격과 갈라져 있으므로 아래 중 하나로 맞춰주세요.

```bash
# 방법 A — 로컬 변경이 없을 때 (간단·권장)
git fetch origin
git reset --hard origin/main

# 방법 B — 가장 확실 (다시 클론)
#   기존 폴더 삭제 후
git clone https://github.com/P1S-syoo/unity-varco-kit.git
```

> 로컬에서 작업한 커밋이 있다면 `reset --hard` 전에 `git branch backup-old`로 백업한 뒤,
> 필요한 커밋만 `git cherry-pick`으로 새 `main` 위에 다시 얹으세요.

플러그인 사용자(`/plugin install`로 설치만 한 경우)는 별도 조치가 필요 없습니다.
`/plugin marketplace update unity-varco-kit` 한 번이면 최신 상태로 갱신됩니다.

## 라이선스

[MIT](./LICENSE)
