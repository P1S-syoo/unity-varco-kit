#!/usr/bin/env python3
"""VARCO nano_banana 2D 이미지 에셋 생성기.

VARCO 에 전용 text-to-image 엔드포인트는 없다. 대신 generative-edit 의 inpaint
엔드포인트(`POST /fashion/edit/v1/inpaint`)에 **전체(흰) 마스크**를 주면 입력 이미지
전체가 prompt 로 다시 그려져 사실상 text-to-image 로 동작한다. 이 스크립트는 그
레시피를 단일/배치로 감싼다.

핵심:
- 출력 해상도 = 입력 base 이미지 해상도. 그래서 width/height 로 출력 크기를 정한다.
- base 색(--bg)은 생성물의 배경 톤을 편향시킨다. UI 패널 위에 얹을 거면 패널색을,
  투명 PNG 가 필요하면 키잉하기 쉬운 단색(예: 마젠타)을 쓴다.
- 응답은 알파 없는 RGB PNG. 투명이 필요하면 --alpha 로 코너색 키잉을 한다.

사용 예:
  # 단일
  python nano_banana_gen.py --prompt "flat teal battery HUD icon" \
      --out out/battery.png --width 512 --height 512 --bg 0d1f24

  # 배치(매니페스트)
  python nano_banana_gen.py --manifest assets.json --outdir out

인증: 환경변수 VARCO_OPENAPI_KEY (헤더 OPENAPI_KEY 로 전송).
"""
import argparse
import io
import json
import os
import sys
import time

import requests
from PIL import Image

BASE = "https://openapi.ai.nc.com"
ENDPOINT = "/fashion/edit/v1/inpaint"


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def get_key():
    key = os.environ.get("VARCO_OPENAPI_KEY")
    if not key:
        sys.exit("VARCO_OPENAPI_KEY 환경변수 없음 — VARCO OpenAPI 키를 설정하세요.")
    return key


def keyout_background(img, tol=18):
    """코너 색을 배경으로 보고 그 색에 가까운 픽셀의 알파를 0으로. 단색 배경 아이콘용.
    글로우/안티에일리어싱 경계는 부분적으로 남을 수 있으니 단색 배경일 때만 권장."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    br = sum(c[0] for c in corners) // 4
    bg_ = sum(c[1] for c in corners) // 4
    bb = sum(c[2] for c in corners) // 4
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if abs(r - br) <= tol and abs(g - bg_) <= tol and abs(b - bb) <= tol:
                px[x, y] = (r, g, b, 0)
    return img


def generate(prompt, out_path, width=1024, height=1024, bg="808080",
             model="nano_banana", style="", alpha=False, alpha_tol=18,
             retries=2, timeout=180):
    """nano_banana(또는 sdxl) inpaint 를 전체 마스크로 호출해 PNG 1장 생성·저장."""
    key = get_key()
    full_prompt = prompt if not style else f"{prompt}. {style}"

    base = Image.new("RGB", (width, height), hex_to_rgb(bg))
    mask = Image.new("L", (width, height), 255)  # 255 = 전체 재생성
    base_buf, mask_buf = io.BytesIO(), io.BytesIO()
    base.save(base_buf, format="PNG")
    mask.save(mask_buf, format="PNG")

    files = {
        "image": ("base.png", base_buf.getvalue(), "image/png"),
        "mask_image": ("mask.png", mask_buf.getvalue(), "image/png"),
    }
    data = {"model": model, "prompt": full_prompt}
    headers = {"OPENAPI_KEY": key}

    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(BASE + ENDPOINT, headers=headers, files=files,
                              data=data, timeout=timeout)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content))
                if alpha:
                    img = keyout_background(img, alpha_tol)
                os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                img.save(out_path)
                print(f"OK  {out_path}  {img.size} {img.mode}  ({len(r.content)}B)")
                return True
            # 429/5xx 는 재시도, 4xx 는 즉시 실패
            last_err = f"status={r.status_code} body={r.text[:200]}"
            if r.status_code < 500 and r.status_code != 429:
                break
        except requests.RequestException as e:
            last_err = str(e)
        if attempt < retries:
            time.sleep(2 * (attempt + 1))
    print(f"FAIL {out_path}  {last_err}", file=sys.stderr)
    return False


def run_manifest(path, outdir, default_model, default_style):
    """매니페스트 JSON 배치 실행. 형식:
       {"defaults": {"width":512,"height":512,"bg":"0d1f24","model":"nano_banana",
                     "style":"...","alpha":false},
        "items": [{"name":"battery","prompt":"...","width":512, ...}, ...]}"""
    with open(path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    d = spec.get("defaults", {})
    items = spec.get("items", [])
    ok = 0
    for it in items:
        name = it["name"]
        out_path = os.path.join(outdir, f"{name}.png")
        if generate(
            prompt=it["prompt"],
            out_path=out_path,
            width=it.get("width", d.get("width", 1024)),
            height=it.get("height", d.get("height", 1024)),
            bg=it.get("bg", d.get("bg", "808080")),
            model=it.get("model", d.get("model", default_model)),
            style=it.get("style", d.get("style", default_style)),
            alpha=it.get("alpha", d.get("alpha", False)),
            alpha_tol=it.get("alpha_tol", d.get("alpha_tol", 18)),
        ):
            ok += 1
    print(f"\n배치 완료: {ok}/{len(items)} 성공 → {outdir}")
    return ok == len(items)


def main():
    ap = argparse.ArgumentParser(description="VARCO nano_banana 이미지 생성기")
    ap.add_argument("--prompt")
    ap.add_argument("--out")
    ap.add_argument("--manifest", help="배치 매니페스트 JSON 경로")
    ap.add_argument("--outdir", default="out", help="배치 출력 폴더")
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--bg", default="808080", help="base 배경색 hex (예: 0d1f24)")
    ap.add_argument("--model", default="nano_banana", choices=["nano_banana", "sdxl"])
    ap.add_argument("--style", default="", help="모든 prompt 뒤에 붙일 공통 스타일 문구")
    ap.add_argument("--alpha", action="store_true", help="코너색 키잉으로 배경 투명화")
    ap.add_argument("--alpha-tol", type=int, default=18)
    a = ap.parse_args()

    if a.manifest:
        ok = run_manifest(a.manifest, a.outdir, a.model, a.style)
        sys.exit(0 if ok else 1)
    if not (a.prompt and a.out):
        ap.error("단일 모드는 --prompt 와 --out 이 필요합니다 (또는 --manifest 사용).")
    ok = generate(a.prompt, a.out, a.width, a.height, a.bg, a.model,
                  a.style, a.alpha, a.alpha_tol)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
