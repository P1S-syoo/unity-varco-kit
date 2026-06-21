#!/usr/bin/env bash
# 원본 스킬(~/.claude/skills/*)을 이 레포 skills/ 로 동기화한다.
#
# 사용법:
#   bash scripts/sync-skills.sh          # 동기화만 (변경분 status 출력, 커밋 안 함)
#   bash scripts/sync-skills.sh push     # 동기화 + 시크릿 검사 + 커밋 + 푸시
#
# 안전장치: 커밋 직전 실제 API 키 패턴을 스캔해 발견되면 중단한다.
set -euo pipefail

# 동기화 대상 스킬 (레포에 포함하는 6종)
SKILLS=(code-rules unity-ugui-layout github-commit-push unity-varco varco-nano-banana roadview-to-3d)

SRC="$HOME/.claude/skills"
# 레포 루트 = 이 스크립트의 상위 디렉터리
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO/skills"

echo "원본: $SRC"
echo "대상: $DEST"
echo

# 1) 복사 (심링크는 -L 로 실파일까지 복사)
for s in "${SKILLS[@]}"; do
    if [ ! -e "$SRC/$s" ]; then
        echo "  ! 원본 없음, 건너뜀: $s"
        continue
    fi
    rm -rf "${DEST:?}/$s"
    cp -rL "$SRC/$s" "$DEST/$s"
    echo "  ✓ $s"
done

# 2) 잡파일 정리 (파이썬 캐시)
find "$DEST" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -name "*.pyc" -delete 2>/dev/null || true

# 3) 시크릿 가드 — 실제 키 패턴이 있으면 중단
echo
echo "시크릿 스캔 중..."
HITS="$(grep -rnE "sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|gh[pours]_[A-Za-z0-9]{30,}|(OPENAPI_KEY|VARCO_OPENAPI_KEY)[\"' ]*[:=][\"' ]*[A-Za-z0-9]{20,}" "$DEST" 2>/dev/null || true)"
if [ -n "$HITS" ]; then
    echo "  ✗ 실제 키로 의심되는 문자열 발견 — 동기화 중단:"
    echo "$HITS"
    exit 1
fi
echo "  ✓ CLEAN (하드코딩 키 없음)"

cd "$REPO"
echo
echo "=== 변경분 ==="
git status -s skills/

# 4) push 인자가 있을 때만 커밋·푸시
if [ "${1:-}" = "push" ]; then
    if git diff --quiet skills/ && git diff --cached --quiet skills/ && [ -z "$(git ls-files --others --exclude-standard skills/)" ]; then
        echo
        echo "변경 없음 — 커밋할 내용이 없습니다."
        exit 0
    fi
    git add skills/
    git commit -m "chore: 스킬 원본 동기화

~/.claude/skills/ 최신 내용을 레포로 반영.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
    git push origin main
    echo
    echo "✓ 커밋·푸시 완료"
else
    echo
    echo "동기화 완료 (커밋 안 함). 올리려면: bash scripts/sync-skills.sh push"
fi
