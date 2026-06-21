# 카카오맵 로드뷰 자동화 레시피 (2026-06-11 실증)

Playwright MCP(`browser_run_code_unsafe`, `browser_take_screenshot`) 기준. 모든 좌표는 1920×1080 뷰포트.

## 0. 함정 목록 (필독)

| 함정 | 증상 | 대처 |
|---|---|---|
| `/link/roadview/lat,lng` 딥링크 | 데스크톱에서 좌표 무시, 이전 위치 유지 | 장소명 검색으로 이동 |
| `a.rv`는 토글 | 이미 켜진 상태에서 또 클릭하면 꺼짐 | canvas visibility로 상태 확인 후 분기 |
| coach_layer/DimmedLayer | 첫 방문 시 안내 오버레이가 클릭 차단 | `.coach_layer, .inner_coach_layer, .DimmedLayer` remove |
| 마커도 커버리지와 같은 파랑 | 마커 클릭 → 팝업만 열림 | find_line.py(얇은 선 필터) + 마커 반경 110px 제외 + elementFromPoint로 IMG(<120px) 가드. 지도 타일도 IMG지만 256px라 통과 |
| 오버레이 숨김을 지도 상태에서 실행 | 지도 타일까지 사라짐 | 파노라마 상태(canvas visible)에서만 실행 |
| 캔버스 클릭으로 포커스 잡기 | 클릭 지점으로 파노라마가 **이동**해버림 | `canvas.focus()` JS로 포커스, 클릭 금지 |
| 파노라마 로딩 지연 | 검은 화면 캡처 | 중앙 200×200 클립 PNG > 8KB 폴링 (최대 40초) |
| 로드뷰 줌 버튼 | FOV 변화 없음 | 캡처 후 크롭으로 대체 |
| 드래그 회전 | 1회당 ~5°로 비효율 | 키보드 홀드 사용 |
| 장소 핀(검색 진입 시) | 캔버스에 풍선이 그려져 제거 불가 | 커버리지 클릭 진입(3-B)이면 핀 없음. DOM 툴팁(.MediumTooltip)만은 remove 가능 |

## 1. 진입 (핀 없는 권장 경로)

```js
// (1) 검색 및 지도 센터링
await page.goto('https://map.kakao.com/');
await page.waitForTimeout(3000);
const input = page.locator('#search\\.keyword\\.query');
await input.fill('세빛섬');           // 장소명
await input.press('Enter');
await page.waitForTimeout(4000);
await page.evaluate(() => document.querySelector('.placelist .PlaceItem .link_name')?.click());
await page.waitForTimeout(3000);
// (2) 로드뷰 모드 토글 + 안내 레이어 제거
await page.evaluate(() => {
  document.querySelectorAll('.coach_layer, .inner_coach_layer, .DimmedLayer').forEach(e => e.remove());
  document.querySelector('a.rv')?.click();
});
await page.waitForTimeout(3000);
await page.evaluate(() => {
  document.querySelectorAll('.coach_layer, .inner_coach_layer, .DimmedLayer').forEach(e => e.remove());
  // 장소 팝업이 떠있으면 닫기 (마커 클릭 흡수 방지)
  document.querySelectorAll('[class*="close"]').forEach(b => { if (b.offsetWidth > 0 && b.offsetWidth < 60) b.click(); });
});
```

스크린샷 저장 → `python scripts/find_line.py <screenshot.png>` → `(w, h, x, y)` 클릭 좌표 획득 →

```js
// (3) 커버리지 선 클릭 → 파노라마 진입 폴링
await page.mouse.click(X, Y);
for (let i = 0; i < 15; i++) {
  await page.waitForTimeout(2000);
  const vis = await page.evaluate(() => getComputedStyle(document.querySelector('canvas')).visibility);
  if (vis === 'visible') break;
}
// (4) 타일 로딩 폴링 (검은 화면 방지)
for (let i = 0; i < 20; i++) {
  const buf = await page.screenshot({ clip: { x: 860, y: 380, width: 200, height: 200 } });
  if (buf.length > 8000) break;
  await page.waitForTimeout(2000);
}
```

빠른 진입(핀 허용 시): 검색 후 `document.querySelector('.placelist .PlaceItem a.roadview').click()` 한 번으로 파노라마 직행.

## 2. 클린 캡처 (파노라마 상태에서만!)

```js
await page.evaluate(() => {
  const canvas = document.querySelector('#view\\.roadview canvas');
  const root = document.querySelector('#view\\.roadview');
  root.querySelectorAll('.MediumTooltip, [class*="Tooltip"]').forEach(e => e.remove());
  for (const el of document.body.querySelectorAll('div, ul, svg, button, a, span, img')) {
    if (el === canvas || el.contains(canvas) || (canvas && canvas.contains(el))) continue;
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0 && r.width < 700 && r.height < 700) {
      const cs = getComputedStyle(el);
      if (cs.position === 'absolute' || cs.position === 'fixed') el.style.setProperty('visibility', 'hidden', 'important');
    }
  }
});
```

주소 오버레이(.info_roadview)는 회전/이동 후 재출현할 수 있어 캡처 직전마다 재실행한다.
바닥의 흰 이동 화살표와 도로명 워터마크는 캔버스 렌더라 숨길 수 없음 → 크롭으로 제외.

## 3. 회전 / 이동 / 프레이밍

```js
// 회전: JS 포커스 후 키 홀드 (약 7°/초. ArrowLeft=반시계, ArrowRight=시계)
await page.evaluate(() => document.querySelector('#view\\.roadview canvas').focus());
await page.keyboard.down('ArrowLeft');
await page.waitForTimeout(3000);   // ≈ 20~25°
await page.keyboard.up('ArrowLeft');
await page.waitForTimeout(3000);   // 관성 정지 + 타일 선명화 대기
```

- **회전마다 스크린샷으로 방향을 시각 확인**한다 — 각도 추정은 부정확하므로 2~3회로 나눠 수렴시킨다.
- 이동: 바닥 흰 화살표를 스크린샷에서 눈으로 찾아 클릭(파노라마 1스텝 이동). 이동 후 로딩 폴링+오버레이 재숨김 필수.
- 피사체는 반드시 **화면 중앙**에 — 파노라마 가장자리는 투영 왜곡+블러.

## 4. 크롭 → 3D

```bash
# 피사체 크롭 (preview 좌표 × 스케일로 박스 계산)
python -c "from PIL import Image; img=Image.open('cap.png'); img.crop((272,360,680,626)).save('subject.png')"
# 업스케일(선택) + 저폴리 3D 생성 + GLB 다운로드
python scripts/roadview_to_3d.py subject.png out.glb --faces 10000 --upscale 2
```
