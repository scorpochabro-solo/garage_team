# -*- coding: utf-8 -*-
"""Image pipeline: copies/optimizes src/assets/img -> dist/assets/img (JPEG -> WebP, PNG kept/optimized)."""
import re
from pathlib import Path

from PIL import Image

MAX_SIDE = 1600
WEBP_QUALITY = 82
# Folders shown much smaller than MAX_SIDE: the longest side is capped at the display size × 3 (iPhone screens).
# Review avatars are 56px circles, team photos at most ~210px wide.
FOLDER_MAX_SIDE = {"review": 168, "team": 640}
# Folders whose JPEGs also get a narrow variant "<name>-<width>.webp" for srcset (large cover photos on service pages,
# photos of the building in real/).
RESPONSIVE_WIDTHS = {"photo": 800, "gallerymain": 800, "real": 800}


def scaled_size(src: Path, max_side: int = MAX_SIDE) -> tuple[int, int]:
    """Pixel size the image will have in dist after the MAX_SIDE downscale (reads the header only)."""
    with Image.open(src) as im:
        w, h = im.size
    scale = min(1.0, max_side / max(w, h))
    return max(1, round(w * scale)), max(1, round(h * scale))


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
                side = FOLDER_MAX_SIDE.get(rel.parts[0], MAX_SIDE) if len(rel.parts) > 1 else MAX_SIDE
                if max(im.size) > side:
                    im.thumbnail((side, side), Image.LANCZOS)
                im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
                narrow = RESPONSIVE_WIDTHS.get(rel.parts[0]) if len(rel.parts) > 1 else None
                if narrow and im.width > narrow:
                    small = im.copy()
                    small.thumbnail((narrow, narrow * 4), Image.LANCZOS)
                    small_dest = dest.with_name(f"{dest.stem}-{narrow}.webp")
                    small.save(small_dest, "WEBP", quality=WEBP_QUALITY, method=6)
                    total += small_dest.stat().st_size
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


def make_logo_assets(mark_src: Path, dist_root: Path) -> None:
    """Favicons from the brand mark (the «G» of the Garage Team logo, transparent PNG):
    /favicon.ico (16–48), /assets/logo/favicon.svg (wrapper with an embedded 96px PNG), apple-touch-icon.png (180)."""
    import base64
    import io

    dist_logo = dist_root / "assets" / "logo"
    dist_logo.mkdir(parents=True, exist_ok=True)
    mark = Image.open(mark_src).convert("RGBA")

    def tile(size: int, pad: float) -> Image.Image:
        canvas = Image.new("RGBA", (size, size), (12, 13, 12, 255))
        inner = mark.resize((round(size * (1 - 2 * pad)),) * 2, Image.LANCZOS)
        canvas.paste(inner, ((size - inner.width) // 2,) * 2, inner)
        return canvas

    tile(180, 0.10).save(dist_logo / "apple-touch-icon.png", "PNG", optimize=True)
    tile(64, 0.04).save(dist_root / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    buf = io.BytesIO()
    tile(96, 0.04).save(buf, "PNG", optimize=True)
    png = base64.b64encode(buf.getvalue()).decode()
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96"><clipPath id="r"><rect width="96" height="96" rx="18"/></clipPath>'
           f'<image clip-path="url(#r)" href="data:image/png;base64,{png}" width="96" height="96"/></svg>')
    (dist_logo / "favicon.svg").write_text(svg, encoding="utf-8")
