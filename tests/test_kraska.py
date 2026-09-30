# -*- coding: utf-8 -*-
"""«Краска на кирпиче» (build/kraska.py, src/assets/css/kraska.css): the painted numerals are decoration, the numbers
stay in the text a screen reader reads, the feature adds no raster image, the generated SVG files fit the CSS that
tiles them.  Run: python3 -m unittest discover -s tests"""
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import kraska as K  # noqa: E402
from build.home import advantages, hero  # noqa: E402

CSS = (ROOT / "src" / "assets" / "css" / "kraska.css").read_text(encoding="utf-8")
RASTER = re.compile(r"\.(png|jpe?g|webp|gif|avif|bmp)\b|data:image/(?!svg)|<image\b", re.I)
SVG_NS = "{http://www.w3.org/2000/svg}"


class Page(HTMLParser):
    """The text a screen reader gets (outside aria-hidden subtrees) and every element as (tag, attrs, own text,
    inside aria-hidden)."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.stack, self.readable, self.elements = [], [], []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = attrs.get("aria-hidden") == "true" or any(e[3] for e in self.stack)
        element = [tag, attrs, [], hidden]
        self.elements.append(element)
        if tag not in self.VOID:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        while self.stack:
            if self.stack.pop()[0] == tag:
                break

    def handle_data(self, data):
        if self.stack:
            self.stack[-1][2].append(data)
        if not any(e[3] for e in self.stack):
            self.readable.append(data)

    def text(self):
        return " ".join(" ".join(self.readable).split())

    def with_class(self, cls):
        return [e for e in self.elements if cls in e[1].get("class", "").split()]


class MarkupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adv = Page(advantages())
        cls.hero = Page(hero())

    def test_the_numbers_stay_in_the_text_a_screen_reader_reads(self):
        self.assertIn("Гарантия на выполненные работы до 360 дней*", self.adv.text())
        self.assertIn("скидку 5%", self.hero.text())

    def test_both_hosts_are_painted_walls(self):
        for page, tone in ((self.adv, "day"), (self.hero, "night")):
            hosts = page.with_class(K.HOST)
            self.assertEqual(len(hosts), 1, tone)
            self.assertIn(f"{K.HOST}--{tone}", hosts[0][1]["class"].split())

    def test_painted_numerals_are_hidden_from_screen_readers(self):
        # (page, painted numeral, its own class, how often a screen reader meets the numeral in the text)
        for page, number, own, readable in ((self.adv, "360", "adv__big", 1), (self.hero, "-5%", "promo-ticket__num", 0)):
            paint = page.with_class(K.PAINT)
            self.assertEqual(len(paint), 1)
            _tag, attrs, text, hidden = paint[0]
            self.assertTrue(hidden)
            self.assertEqual(attrs.get("aria-hidden"), "true")
            self.assertIn(own, attrs["class"].split(), "the numeral keeps its own class (its look without masks)")
            self.assertEqual("".join(text).strip(), number)
            self.assertEqual(page.text().count(number), readable, "the painted copy is not read out a second time")

    def test_the_layers_are_hidden_and_hold_no_text(self):
        for night in (False, True):
            page = Page(K.layers(night=night))
            wall = page.with_class("kraska__wall")
            self.assertEqual(len(wall), 1)
            self.assertEqual(wall[0][1].get("aria-hidden"), "true")
            self.assertEqual(page.text(), "")
            self.assertEqual(bool(page.with_class("kraska__light")), night)
            self.assertFalse(any(e[0] in ("img", "picture", "image", "svg") for e in page.elements))


class NoRasterTest(unittest.TestCase):
    def test_generated_files_are_only_svg_without_raster_images(self):
        files = K.assets()
        self.assertTrue(files)
        for name, svg in files.items():
            self.assertTrue(name.endswith(".svg"), name)
            self.assertIsNone(RASTER.search(svg), name)
            root = ET.fromstring(svg)
            self.assertEqual(root.tag, SVG_NS + "svg", name)
            self.assertEqual(list(root.iter(SVG_NS + "image")), [], name)
            for el in root.iter():   # references stay inside the file (clip paths reuse its own bricks)
                for attr in ("href", "{http://www.w3.org/1999/xlink}href"):
                    if attr in el.attrib:
                        self.assertTrue(el.attrib[attr].startswith("#"), f"{name}: {el.attrib[attr]}")

    def test_css_points_only_at_generated_svg_files(self):
        self.assertIsNone(RASTER.search(CSS))
        urls = re.findall(r"url\(([^)]*)\)", CSS)
        self.assertTrue(urls)
        names = set(K.assets())
        for u in urls:
            m = re.fullmatch(r"'/assets/kraska/([a-z-]+\.svg)'", u)
            self.assertIsNotNone(m, f"{u}: only root-relative, single-quoted URLs are rebased by D.rebase()")
            self.assertIn(m.group(1), names)

    def test_no_image_files_come_with_the_feature(self):
        """The only source file of the feature under src/ is its stylesheet (the walls are generated at build time);
        "pokraska.jpg" is the photo of the paint shop, not ours."""
        own = re.compile(r"(?<![a-z])kraska(?![a-z])")
        found = [p.relative_to(ROOT / "src").as_posix() for p in (ROOT / "src").rglob("*") if own.search(p.relative_to(ROOT / "src").as_posix())]
        self.assertEqual(found, ["assets/css/kraska.css"])


class GeometryTest(unittest.TestCase):
    def size(self, name):
        root = ET.fromstring(K.assets()[name])
        return int(root.get("width")), int(root.get("height"))

    def test_tiles_repeat_without_a_seam(self):
        for _cols, rows in (K.DAY_TILE, K.NIGHT_TILE, K.JOINT_MAP_TILE):
            self.assertEqual(rows % 2, 0, "running bond: an even number of courses")
        self.assertEqual(self.size("relief.svg"), (K.MODULE, 2 * K.COURSE))

    def test_a_wall_is_one_tile_wide(self):
        """No brick repeats inside a sign: the big card is at most 2/3 of the 1400 px container, the ticket at most
        the aside column (0.7 of 2 fractions of 1400 − 56 px) with bricks × 1.25."""
        self.assertGreaterEqual(K.DAY_TILE[0] * K.MODULE, 1400 * 2 // 3)
        self.assertGreaterEqual(K.NIGHT_TILE[0] * K.MODULE * 1.25, (1400 - 56) * 0.35)

    def test_css_tiles_the_files_at_their_own_size(self):
        """A mask whose joints do not lie on the joints of the bricks would stripe the paint: the sizes in the CSS
        must be the sizes of the files."""
        for name in ("brick-day.svg", "brick-night.svg", "joints.svg", "relief.svg"):
            w, h = self.size(name)
            self.assertIn(f"calc({w}px * var(--kr-scale)) calc({h}px * var(--kr-scale))", CSS, name)
        w, h = self.size("wear-paint.svg")
        self.assertIn(f"--kr-wear-size: {w}px {h}px;", CSS)
        self.assertEqual(CSS.count(f"{w}px {h}px"), 1, "the size of the wear tile is written once, as --kr-wear-size")
        for coat in (r"\.kraska__green", r"\.kraska__field", r"\.kraska \.kraska__paint"):
            rule = re.search(r"^\s*" + coat + r" \{(.*?)\}", CSS, re.S | re.M).group(1)
            self.assertEqual(rule.count("var(--kr-wear-size)"), 2, f"{coat}: -webkit-mask-size and mask-size")
        self.assertIn("256px 256px", CSS)
        self.assertEqual(self.size("grain.svg"), (256, 256))

    def test_the_cream_and_the_black_share_their_flakes_the_green_does_not(self):
        shared = f'baseFrequency="{K.FLAKE_FREQ}" numOctaves="{K.FLAKE_OCTAVES}" seed="{K.SEED}"'
        files = K.assets()
        self.assertIn(shared, files["wear-paint.svg"])
        self.assertIn(shared, files["wear-field.svg"])
        self.assertNotIn(shared, files["wear-green.svg"])

    def test_the_same_wall_on_every_build(self):
        self.assertEqual(K.assets(), K.assets())

    def test_written_files_are_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            total = K.write_assets(Path(tmp))
            written = sorted(p.name for p in Path(tmp, *K.ASSET_DIR).iterdir())
        self.assertEqual(written, sorted(K.assets()))
        self.assertLess(total, 80 * 1024)


class BasePathTest(unittest.TestCase):
    def tearDown(self):
        D.set_base("")

    def test_css_urls_carry_the_base(self):
        D.set_base("/v/kraska")
        css = D.rebase(CSS)
        self.assertNotIn("url('/assets/", css)
        self.assertEqual(css.count("url('/v/kraska/assets/kraska/"), CSS.count("url('/assets/kraska/"))


if __name__ == "__main__":
    unittest.main()
