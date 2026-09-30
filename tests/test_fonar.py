# -*- coding: utf-8 -*-
"""Tests for «Фонарь по кирпичу» (build/fonar.py, fonar.css, fonar.js).  Run: python3 -m unittest discover -s tests"""
import random
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import fonar as F  # noqa: E402
from build.home import render_home  # noqa: E402
from build.layout import page_hero  # noqa: E402
from build.static_pages import render_404  # noqa: E402

CSS = ROOT / "src" / "assets" / "css"
JS = ROOT / "src" / "assets" / "js"
RASTER = re.compile(r"\.(png|jpe?g|webp|gif|avif|bmp|tiff?)\b|image/(png|jpe?g|webp|gif|avif)", re.I)
SVG_NS = "{http://www.w3.org/2000/svg}"


def token(file, name):
    m = re.search(rf"{re.escape(name)}:\s*([^;]+);", (CSS / file).read_text(encoding="utf-8"))
    return m.group(1).strip()


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def over(base, col, alpha):
    return tuple(x + (y - x) * alpha for x, y in zip(base, col))


class PatternTest(unittest.TestCase):
    """The wall tile drawn at build time."""

    @classmethod
    def setUpClass(cls):
        cls.svg = F.tile_svg()
        cls.root = ET.fromstring(cls.svg)
        cls.paths = cls.root.findall(f"{SVG_NS}path")

    def rects(self, path):
        return [tuple(map(int, m)) for m in re.findall(r"M(\d+) (\d+)h(\d+)v(\d+)h-\d+z", path.get("d"))]

    def test_is_one_svg_tile_of_running_bond(self):
        self.assertEqual(self.root.tag, f"{SVG_NS}svg")
        self.assertEqual((self.root.get("width"), self.root.get("height")), (str(F.TILE_W), str(F.TILE_H)))
        self.assertEqual(self.root.get("shape-rendering"), "crispEdges")
        self.assertGreaterEqual(len(self.paths), 1 + 4, "mortar and several brick tones")
        self.assertEqual(F.TILE_W, F.MODULE * F.PER_COURSE)
        self.assertEqual(F.COURSES % 2, 0, "running bond repeats every two courses")

    def test_brick_and_mortar_cover_the_tile_exactly_once(self):
        grid = bytearray(F.TILE_W * F.TILE_H)
        for path in self.paths:
            for x, y, w, h in self.rects(path):
                self.assertTrue(0 <= x and x + w <= F.TILE_W and 0 <= y and y + h <= F.TILE_H, (x, y, w, h))
                for yy in range(y, y + h):
                    for xx in range(x, x + w):
                        grid[yy * F.TILE_W + xx] += 1
        self.assertEqual(set(grid), {1}, "no gaps, no overlaps: the tile repeats seamlessly")

    def test_odd_courses_are_shifted_by_half_a_brick(self):
        rows = F.courses(random.Random(F.SEED))
        self.assertEqual(len(rows), F.COURSES)
        for c in range(0, F.COURSES, 2):
            shift = (rows[c + 1][0] - rows[c][0]) % F.MODULE
            half = F.MODULE // 2
            self.assertLessEqual(abs(shift - half), 2 * (F.SHIFT + F.WANDER), f"course {c + 1}: shift {shift}")
            gaps = [(b - a) % F.TILE_W for a, b in zip(rows[c], rows[c][1:] + rows[c][:1])]
            self.assertTrue(all(abs(g - F.MODULE) <= 2 * F.WANDER for g in gaps), gaps)

    def test_colours_come_from_the_tokens_under_the_lamp(self):
        lamp = tuple(int(v) for v in token("arki.css", "--arch-lamp-rgb").split(","))
        brick = tuple(int(v) for v in token("arki.css", "--brick-rgb").split(","))
        fills = [p.get("fill") for p in self.paths]
        self.assertIn("rgb({},{},{})".format(*F._lit(brick, lamp)), fills)
        self.assertIn("rgb({},{},{})".format(*F._lit(F.MORTAR_RGB, lamp)), fills)

    def test_same_wall_on_every_build(self):
        self.assertEqual(self.svg, F.tile_svg())

    def test_the_brightest_joint_keeps_the_dimmest_text_readable(self):
        """Under the middle of the lamp the wall lies on --black (fonar.css); even a mortar joint there, with the
        lamp's own glow, must keep --text-3 above WCAG AA (4.5 : 1) and close to what it has on plain black."""
        black = hexrgb(token("tokens.css", "--black"))
        text3 = hexrgb(token("tokens.css", "--text-3"))
        lamp = tuple(int(v) for v in token("arki.css", "--arch-lamp-rgb").split(","))
        glow = float(re.search(r"rgba\(var\(--arch-lamp-rgb\), ([\d.]+)\)", (CSS / "fonar.css").read_text(encoding="utf-8")).group(1))
        joint = over(over(black, lamp, glow), F._lit(F.MORTAR_RGB, lamp), F.MORTAR_ALPHA)
        brightest_brick = max((over(over(black, lamp, glow), F._lit(F._mix(F._token("--brick-rgb"), F._token("--brick-deep-rgb"), t), lamp), F.BRICK_ALPHA * k)
                               for _, t, k in F.TONES), key=lum)
        for bg in (joint, brightest_brick):
            self.assertGreaterEqual(contrast(text3, bg), 4.6)
        self.assertGreaterEqual(contrast(text3, joint) / contrast(text3, black), 0.9, "the lamp takes at most 10% of the contrast")
        self.assertGreater(lum(joint), lum(brightest_brick), "white-grey mortar is lighter than the brick, as in the building")


class HookTest(unittest.TestCase):
    """The zones of the wall on the pages, the generated CSS and the registration in build.py."""

    @classmethod
    def setUpClass(cls):
        cls.home = render_home()

    def test_dark_sections_of_the_home_page_are_zones(self):
        tags = {m.group(1): m.group(0) for m in re.finditer(r"<section[^>]*\bid=\"([^\"]+)\"[^>]*>", self.home)}
        zones = {i for i, t in tags.items() if F.ATTR in t}
        self.assertEqual(zones, {"services", "pribory", "inside", "gallery", "team", "stuk", "zima", "contacts"})
        for free in ("top", "advantages", "reviews", "request"):   # own hand lamp, paper, paper, the form
            self.assertNotIn(F.ATTR, tags[free], free)
        self.assertIn('data-fonar-after=".gate"', tags["contacts"], "only the wall below the «Ворота» photo")

    def test_inner_pages_page_hero_and_404_are_zones(self):
        self.assertRegex(page_hero("Заголовок", [("Главная", "/"), ("Раздел", None)]), r'^<section data-fonar class="page-hero"')
        self.assertRegex(render_404(), r'<section data-fonar class="wrap notfound"')

    def test_mark_adds_the_hook_once_and_escapes(self):
        html = '<section class="x"><section class="y"></section></section>'
        out = F.mark(html, after='a[b="c"]')
        self.assertTrue(out.startswith('<section data-fonar data-fonar-after="a[b=&quot;c&quot;]" class="x">'))
        self.assertEqual(out.count(F.ATTR + " "), 1)
        with self.assertRaises(ValueError):
            F.mark("<div></div>")

    def test_generated_css_is_the_svg_tile_inline(self):
        css = F.css()
        m = re.search(r'\.fonar__wall\{background:url\("data:image/svg\+xml,([^"]+)"\) 0 0/(\d+)px (\d+)px repeat\}', css)
        self.assertIsNotNone(m, css[:200])
        self.assertEqual(unquote(m.group(1)), F.tile_svg())
        self.assertEqual((int(m.group(2)), int(m.group(3))), (F.TILE_W, F.TILE_H))
        self.assertNotIn('"', unquote(m.group(1)), "the SVG may not close the CSS string")

    def test_registered_in_the_build(self):
        src = (ROOT / "build.py").read_text(encoding="utf-8")
        self.assertIn('"fonar.css"', re.search(r"CSS_ORDER = \[[^\]]+\]", src).group(0))
        self.assertIn('"fonar.js"', re.search(r"JS_ORDER = \[[^\]]+\]", src).group(0))
        self.assertRegex(src, r"css = fonts_css\(\) \+ fonar\.css\(\) \+")

    def test_moving_layers_take_no_var(self):
        """The pool, the wall and the warm patch are restyled on the frames they move: plain values only."""
        css = (CSS / "fonar.css").read_text(encoding="utf-8")
        for sel in (".fonar__beam", ".fonar__wall", ".fonar__pool"):
            for body in re.findall(rf"(?m)^{re.escape(sel)}[^{{,]*\{{([^}}]*)\}}", css):
                self.assertNotIn("var(", body, sel)

    def test_script_is_for_a_mouse_only_and_respects_reduced_motion(self):
        js = (JS / "fonar.js").read_text(encoding="utf-8")
        self.assertIn("matchMedia('(hover: hover) and (pointer: fine)')", js)
        self.assertIn("matchMedia('(prefers-reduced-motion: reduce)')", js)
        self.assertIn("pointerType === 'touch'", js)
        self.assertNotIn("requestAnimationFrame", js.split("*/", 1)[1], "no frame loop: the compositor animates the legs")

    def test_no_raster_images(self):
        for text in (F.css(), (CSS / "fonar.css").read_text(encoding="utf-8"), (JS / "fonar.js").read_text(encoding="utf-8"),
                     (ROOT / "build" / "fonar.py").read_text(encoding="utf-8")):
            self.assertIsNone(RASTER.search(text))
        self.assertEqual(F.css().count("url("), 1, "one image: the inline SVG tile")
        self.assertFalse([p for p in (ROOT / "src").rglob("*fonar*") if p.suffix.lower() not in (".css", ".js")])


if __name__ == "__main__":
    unittest.main()
