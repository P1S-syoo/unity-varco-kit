"""스크린샷에서 카카오 로드뷰 커버리지 '선'(얇은 파란 라인) 픽셀을 찾는다.

마커 핀(굵은 파란 덩어리)과 구분하기 위해, 후보 픽셀에서
가로/세로 파란 런 길이가 모두 얇은(<=14px) 지점만 선으로 인정한다.
"""
import sys
from PIL import Image


def is_blue(px, x, y, w, h):
    if not (0 <= x < w and 0 <= y < h):
        return False
    R, G, B = px[x, y]
    return R <= 100 and 105 <= G <= 195 and B >= 230


def run_len(px, x, y, dx, dy, w, h, cap=30):
    n = 0
    while n < cap and is_blue(px, x + dx * (n + 1), y + dy * (n + 1), w, h):
        n += 1
    return n


def find_line(path, cx_ratio=0.62, cy_ratio=0.5, min_x=420, margin=60):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    px = img.load()
    cx, cy = int(w * cx_ratio), int(h * cy_ratio)
    best, bestd = None, 1e18
    for y in range(margin, h - margin, 3):
        for x in range(min_x, w - margin, 3):
            if not is_blue(px, x, y, w, h):
                continue
            horiz = run_len(px, x, y, 1, 0, w, h) + run_len(px, x, y, -1, 0, w, h) + 1
            vert = run_len(px, x, y, 0, 1, w, h) + run_len(px, x, y, 0, -1, w, h) + 1
            # 선: 한 축은 길어도 되지만 두꺼운 덩어리(양축 15px+)는 마커로 간주
            if min(horiz, vert) > 14:
                continue
            d = (x - cx) ** 2 + (y - cy) ** 2
            if d < bestd:
                bestd, best = d, (x, y)
    return (w, h) + (best if best else (None, None))


if __name__ == "__main__":
    print(find_line(sys.argv[1]))
