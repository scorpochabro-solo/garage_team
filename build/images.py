# -*- coding: utf-8 -*-
"""Image pipeline: copies/optimizes src/assets/img -> dist/assets/img (JPEG -> WebP, PNG kept/optimized)."""
import re
from pathlib import Path

from PIL import Image

MAX_SIDE = 1600
WEBP_QUALITY = 82


def _dest_for(rel: Path) -> Path:
    name = rel.name.replace(" ", "_")
    if re.search(r"\.(jpe?g)$", name, re.I):
        name = re.sub(r"\.(jpe?g)$", ".webp", name, flags=re.I)
    return rel.with_name(name)


def process_images(src_root: Path, dist_root: Path, verbose=False):
    """Returns (count, total_bytes)."""
    count = 0
    total = 0
    for src in sorted(src_root.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(src_root)
        if "_262x262" in src.name:  # old thumbnails: we render from full-size images
            continue
        dest = dist_root / _dest_for(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
            count += 1
            total += dest.stat().st_size
            continue
        ext = src.suffix.lower()
        try:
            if ext in (".jpg", ".jpeg"):
                im = Image.open(src)
                im = im.convert("RGB")
                if max(im.size) > MAX_SIDE:
                    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
                im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
            elif ext == ".png":
                im = Image.open(src)
                if src.name in ("car.png", "car-xray.png"):
                    # keep alpha, also emit a lossy webp for the page (much smaller)
                    im.save(dest, "PNG", optimize=True)
                    im.save(dest.with_suffix(".webp"), "WEBP", quality=88, method=6)
                else:
                    im.save(dest, "PNG", optimize=True)
            else:
                dest.write_bytes(src.read_bytes())
        except Exception as exc:  # corrupted file etc.
            print(f"  ! image skipped {rel}: {exc}")
            continue
        count += 1
        total += dest.stat().st_size
        if verbose:
            print(f"  img {rel} -> {dest.relative_to(dist_root)} ({dest.stat().st_size // 1024} KB)")
    return count, total


def make_logo_assets(logo_src: Path, dist_logo: Path):
    """favicon.svg (green badge w/ embedded logo) + apple-touch-icon.png from the white logo."""
    dist_logo.mkdir(parents=True, exist_ok=True)
    import base64
    png = base64.b64encode(logo_src.read_bytes()).decode()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="12" fill="#0c0d0c"/>'
           f'<image href="data:image/png;base64,{png}" x="4" y="14" width="56" height="28" preserveAspectRatio="xMidYMid meet"/>'
           '<rect x="0" y="58" width="64" height="6" fill="#00963d"/></svg>')
    (dist_logo / "favicon.svg").write_text(svg, encoding="utf-8")
    im = Image.open(logo_src).convert("RGBA")
    canvas = Image.new("RGBA", (180, 180), (12, 13, 12, 255))
    logo = im.copy()
    logo.thumbnail((150, 90), Image.LANCZOS)
    canvas.paste(logo, ((180 - logo.width) // 2, (180 - logo.height) // 2), logo)
    canvas.save(dist_logo / "apple-touch-icon.png", "PNG", optimize=True)
