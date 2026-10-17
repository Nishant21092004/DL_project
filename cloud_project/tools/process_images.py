#!/usr/bin/env python3
"""Process raw image-search downloads into product image folders.

Reads tools/img_manifest.txt (slug|query), finds matching downloads in
image-search/, validates them, center-crops to 4:3, resizes to 800x600 and
saves as JPEG into assets/products/<slug>/<n>.jpg (up to 4 per product).
Prints a report of products with fewer than 3 usable images.
"""
import glob
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "..", "image-search")
OUT_DIR = os.path.join(ROOT, "assets", "products")
MANIFEST = os.path.join(ROOT, "tools", "img_manifest.txt")

TARGET_W, TARGET_H = 800, 600  # 4:3


def slugify(q: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
    return s


def valid_image(path: str):
    """Return (ok, width, height)."""
    try:
        if os.path.getsize(path) < 4000:
            return False, 0, 0
        with Image.open(path) as im:
            w, h = im.size
        if w < 200 or h < 200:
            return False, w, h
        return True, w, h
    except Exception:
        return False, 0, 0


def process(src: str, dst: str):
    with Image.open(src) as im:
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")
        w, h = im.size
        # center-crop to 4:3
        target_ratio = TARGET_W / TARGET_H
        if w / h > target_ratio:
            new_w = int(h * target_ratio)
            x = (w - new_w) // 2
            im = im.crop((x, 0, x + new_w, h))
        else:
            new_h = int(w / target_ratio)
            y = (h - new_h) // 2
            im = im.crop((0, y, w, y + new_h))
        im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
        im.save(dst, "JPEG", quality=80, optimize=True, progressive=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    report = {}
    problems = []
    with open(MANIFEST) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    for line in lines:
        slug, query = line.split("|", 1)
        prefix = slugify(query)[:30]
        pattern = os.path.join(RAW_DIR, prefix + "*")
        files = []
        for path in glob.glob(pattern):
            m = re.match(r".*-(\d+)\.(jpg|jpeg|png|webp)$", path, re.I)
            if m:
                files.append((int(m.group(1)), path))
        files.sort()
        out_dir = os.path.join(OUT_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        saved = 0
        for n, path in files:
            if saved >= 4:
                break
            ok, w, h = valid_image(path)
            if not ok:
                continue
            dst = os.path.join(out_dir, f"{saved + 1}.jpg")
            try:
                process(path, dst)
                saved += 1
            except Exception as e:
                print(f"  ! error processing {path}: {e}", file=sys.stderr)
        report[slug] = saved
        if saved < 3:
            problems.append((slug, saved, query))
    print(json.dumps({"total": len(report), "problems": len(problems)}))
    for slug, n, q in problems:
        print(f"PROBLEM {slug}: {n} images (query: {q})")
    # also write report file
    with open(os.path.join(ROOT, "tools", "img_report.json"), "w") as f:
        json.dump(report, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
