"""로드뷰 캡처 PNG → (선택)업스케일 → VARCO image-to-3d → GLB 다운로드.

usage:
  python roadview_to_3d.py <input.png> <output.glb> [--faces 10000] [--upscale 2] [--seed 42]

환경변수 VARCO_OPENAPI_KEY 필요.
"""
import argparse
import io
import json
import os
import sys
import time

import requests

BASE = "https://openapi.ai.nc.com"


def get_key():
    key = os.environ.get("VARCO_OPENAPI_KEY", "").strip()
    if not key:
        sys.exit("VARCO_OPENAPI_KEY 환경변수가 없습니다")
    return key


def upscale(png_bytes, factor, key):
    """이미지를 factor배 업스케일한 PNG bytes 반환."""
    r = requests.post(
        f"{BASE}/fashion/upscale/v1/super-resolution",
        headers={"OPENAPI_KEY": key},
        files={"image": ("input.png", png_bytes, "image/png")},
        data={"scale_factor": str(factor)},
        timeout=300,
    )
    if r.status_code != 200:
        sys.exit(f"업스케일 실패: HTTP {r.status_code} {r.text[:300]}")
    return r.content


def request_3d(png_bytes, faces, seed, key):
    """3D 생성 요청 후 requestId 반환."""
    r = requests.post(
        f"{BASE}/3d/varco/v1/image-to-3d",
        headers={"OPENAPI_KEY": key},
        files={"image": ("input.png", png_bytes, "image/png")},
        data={
            "target_face_type": "tri",
            "target_face_num": str(faces),
            "generate_texture": "true",
            "seed": str(seed),
        },
        timeout=120,
    )
    if r.status_code not in (200, 202):
        sys.exit(f"3D 생성 요청 실패: HTTP {r.status_code} {r.text[:300]}")
    data = r.json()
    print("요청 수락:", json.dumps(data, ensure_ascii=False))
    return data["requestId"]


def wait_model_url(request_id, key, poll_sec=10, timeout_sec=1800):
    """폴링으로 완료 대기 후 model_url 반환."""
    waited = 0
    while waited < timeout_sec:
        r = requests.get(
            f"{BASE}/inference/result/{request_id}",
            headers={"OPENAPI_KEY": key},
            timeout=60,
        )
        try:
            data = r.json()
        except ValueError:
            data = {"status": f"http {r.status_code}"}
        status = data.get("status", "?")
        print(f"[{waited}s] status={status}")
        if status == "succeeded":
            return data["model_url"]
        if status == "failed":
            sys.exit("3D 생성 작업 실패")
        time.sleep(poll_sec)
        waited += poll_sec
    sys.exit("폴링 타임아웃")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--faces", type=int, default=10000)
    ap.add_argument("--upscale", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    key = get_key()
    with open(args.input, "rb") as f:
        png = f.read()
    print(f"입력: {args.input} ({len(png)} bytes), faces={args.faces}")

    if args.upscale >= 2:
        print(f"업스케일 x{args.upscale} 진행...")
        png = upscale(png, args.upscale, key)
        up_path = os.path.splitext(args.input)[0] + f"_x{args.upscale}.png"
        with open(up_path, "wb") as f:
            f.write(png)
        print(f"업스케일 저장: {up_path} ({len(png)} bytes)")

    rid = request_3d(png, args.faces, args.seed, key)
    url = wait_model_url(rid, key)
    print("model_url:", url)
    glb = requests.get(url, headers={"OPENAPI_KEY": key}, timeout=600).content
    with open(args.output, "wb") as f:
        f.write(glb)
    print(f"GLB 저장 완료: {args.output} ({len(glb)} bytes)")


if __name__ == "__main__":
    main()
