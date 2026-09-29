#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Static site generator for the garage.team redesign.
    python3 build.py                       # build ./dist for the site root (garage.team)
    python3 build.py --base /garage_team   # build ./dist for a sub-path (GitHub Pages project site)
    python3 build.py --out docs            # build into another folder
    python3 build.py --verbose             # log every image
No dependencies beyond Pillow (image optimization).
"""
import hashlib
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build.css_tools import guard_hover  # noqa: E402
from build.home import render_home  # noqa: E402
from build.images import make_logo_assets, process_images  # noqa: E402
from build.services import render_service, render_services_index  # noqa: E402
from build.static_pages import PAGES  # noqa: E402

SRC = ROOT / "src"
DIST = ROOT / "dist"


def _arg(name, default):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


BASE = _arg("--base", "").rstrip("/")
DIST = ROOT / _arg("--out", "dist")
D.set_base(BASE)
CSS_ORDER = ["tokens.css", "base.css", "components.css", "header.css", "home.css", "zima.css", "car.css", "pages.css", "service.css", "footer.css"]
JS_ORDER = ["core.js", "car.js", "gallery.js", "form.js", "zima.js", "pages.js"]
UNICODE = {
    "latin": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    "cyrillic": "U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116",
    "cyrillic-ext": "U+0460-052F, U+1C80-1C88, U+20B4, U+2DE0-2DFF, U+A640-A69F, U+FE2E-FE2F",
}
FAMILIES = {"manrope": "Manrope", "unbounded": "Unbounded", "jetbrains-mono": "JetBrains Mono"}
# All three are variable fonts: one file per alphabet holds every weight. The range is the font's own weight axis;
# declaring it lets the browser render 500 or 800 from the same file instead of downloading a copy per weight.
WEIGHT_RANGE = {"manrope": "200 800", "unbounded": "200 900", "jetbrains-mono": "100 800"}


def fonts_css():
    out = ["/* self-hosted variable fonts (generated): one file per family and alphabet */"]
    for f in sorted((SRC / "assets" / "fonts").glob("*.woff2")):
        m = re.match(r"(manrope|unbounded|jetbrains-mono)-(latin|cyrillic-ext|cyrillic)\.woff2$", f.name)
        if not m:
            raise SystemExit(f"неизвестный файл шрифта {f.name}: ожидается <семейство>-<алфавит>.woff2")
        fam, subset = m.groups()
        out.append(
            f"@font-face{{font-family:'{FAMILIES[fam]}';font-style:normal;font-weight:{WEIGHT_RANGE[fam]};font-display:swap;"
            f"src:url('{BASE}/assets/fonts/{f.name}') format('woff2');unicode-range:{UNICODE[subset]};}}"
        )
    return "\n".join(out) + "\n"


def write(path, html):
    rel = path.lstrip("/")
    dest = DIST / (rel + "index.html" if rel.endswith("/") or rel == "" else rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(D.rebase(html), encoding="utf-8")
    return dest


def main(verbose=False):
    t0 = time.time()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # assets
    shutil.copytree(SRC / "assets" / "fonts", DIST / "assets" / "fonts")
    (DIST / "assets" / "logo").mkdir(parents=True)
    shutil.copy(SRC / "assets" / "logo" / "logo.svg", DIST / "assets" / "logo" / "logo.svg")
    make_logo_assets(SRC / "assets" / "logo" / "mark.png", DIST)
    n_img, img_bytes = process_images(SRC / "assets" / "img", DIST / "assets" / "img", verbose=verbose)

    # hover styles only where a pointer can hover: on a phone a tapped element stays in :hover (build/css_tools.py)
    css = fonts_css() + D.rebase(guard_hover("\n".join((SRC / "assets" / "css" / n).read_text(encoding="utf-8") for n in CSS_ORDER)))
    (DIST / "assets" / "css").mkdir(parents=True)
    (DIST / "assets" / "css" / "site.css").write_text(css, encoding="utf-8")
    js = D.rebase("\n".join((SRC / "assets" / "js" / n).read_text(encoding="utf-8") for n in JS_ORDER))
    (DIST / "assets" / "js").mkdir(parents=True)
    (DIST / "assets" / "js" / "site.js").write_text(js, encoding="utf-8")
    D.ASSET_VERSION.update(css=hashlib.sha1(css.encode("utf-8")).hexdigest()[:10],
                           js=hashlib.sha1(js.encode("utf-8")).hexdigest()[:10])

    # pages
    urls = []
    write("/", render_home()); urls.append("/")
    write("/services.html", render_services_index()); urls.append("/services.html")
    for svc in D.SERVICES:
        write(svc["path"], render_service(svc)); urls.append(svc["path"])
    for path, fn in PAGES.items():
        write(path, fn())
        if path != "/404.html":
            urls.append(path)

    # sitemap / robots
    today = time.strftime("%Y-%m-%d")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        prio = "1.0" if u == "/" else ("0.9" if u == "/services.html" else "0.7")
        sm.append(f"<url><loc>{D.SITE_URL}{BASE}{u}</loc><lastmod>{today}</lastmod><priority>{prio}</priority></url>")
    sm.append("</urlset>")
    (DIST / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {D.SITE_URL}{BASE}/sitemap.xml\n", encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages: serve files/dirs starting with _ and . as-is

    total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"base='{BASE or '/'}' out={DIST.name} | built {len(urls) + 1} pages, {n_img} images ({img_bytes // 1024} KB), css {len(css) // 1024} KB, js {len(js) // 1024} KB, "
          f"dist {total // 1024 // 1024} MB in {time.time() - t0:.1f}s -> {DIST}")


if __name__ == "__main__":
    main(verbose="--verbose" in sys.argv)
