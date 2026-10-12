# -*- coding: utf-8 -*-
"""«Неон» (build/neon.py, src/assets/css/neon.css, src/assets/js/neon.js): the neon 404, the footer sign, the tubes of
the «Свет ламп» sign shared through build/svet.py, the brick wall material, the rules of the animation.
Run: python3 -m unittest discover -s tests"""
import html
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import layout, neon, static_pages, svet  # noqa: E402
from build.css_tools import guard_hover  # noqa: E402

RASTER = re.compile(r"\.(?:png|jpe?g|webp|gif|avif|bmp|tiff?)\b|data:image/(?!svg\+xml)", re.I)


def code_of(path: Path) -> str:
    """The file without its comments: the rules below are about what the browser gets, not about the notes in it."""
    text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    return re.sub(r"^\s*//.*$", "", text, flags=re.M)


CSS = code_of(ROOT / "src" / "assets" / "css" / "neon.css")
JS = code_of(ROOT / "src" / "assets" / "js" / "neon.js")


def section(page: str, cls: str) -> str:
    m = re.search(rf'<section class="{cls}".*?</section>', page, re.S)
    if not m:
        raise AssertionError(f"нет секции {cls}")
    return m.group(0)


class NotFoundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = static_pages.render_404()
        cls.scene = section(cls.page, "neon-404")

    def test_the_404_is_the_neon_scene(self):
        self.assertIn('aria-labelledby="notfound-title"', self.scene)
        self.assertIn('<h1 class="h2" id="notfound-title"', self.scene)
        sign = re.search(r'<div class="neon-404__sign"([^>]*)>', self.scene)
        self.assertIsNotNone(sign)
        self.assertIn('aria-hidden="true"', sign.group(1))
        # the glass, the lit tubes and the broken tube: three drawings over one another, all decorative
        for cls in ("neon-404__glass", "neon-404__lit", "neon-404__tube"):
            self.assertRegex(self.scene, rf'<svg class="{cls}" viewBox="-26 -26 552 252" focusable="false">')

    def test_digits_are_tubes_and_one_of_them_is_broken(self):
        steady, broken = neon.tubes_404()
        self.assertEqual(len(steady), 4)                     # «4»: two tubes, «0»: one, «4»: the bar tube
        for t in steady:
            self.assertIn(f'<path d="{t.d}"/>', self.scene)
        self.assertIn(f'<path id="neon-404-broken" d="{broken.d}"/>', self.scene)
        x = neon.LAST_FOUR_X + neon.STEM_X
        self.assertEqual(broken.d, f"M{x} 0L{x} {neon.DIGIT_H}")   # the stem of the last «4»
        # the broken tube is lit in its own drawing only, so it can flicker alone
        lit = re.search(r'<svg class="neon-404__lit".*?</svg>', self.scene, re.S).group(0)
        tube = re.search(r'<svg class="neon-404__tube".*?</svg>', self.scene, re.S).group(0)
        self.assertNotIn("#neon-404-broken\"", lit)
        self.assertIn('href="#neon-404-broken"', tube)
        self.assertNotIn('href="#neon-404-steady"', tube)

    def test_texts_and_links_are_kept(self):
        text = html.unescape(self.scene)
        self.assertIn("Страница не найдена", text)
        self.assertIn("Возможно, адрес изменился. Загляните в услуги или позвоните нам — поможем.", text)
        links = re.findall(r'<a class="btn[^"]*" href="([^"]+)">([^<]+)</a>', self.scene)
        self.assertEqual(links, [("/", "На главную"), ("/services.html", "Все услуги"), (f"tel:{D.PHONE_TEL}", D.PHONE)])
        self.assertIn('noindex', self.page)

    def test_no_raster_images_in_the_scene(self):
        self.assertNotRegex(self.scene, r"<img\b|<image\b|url\(")
        self.assertNotRegex(self.scene, RASTER)


class FooterSignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.footer = layout.footer()
        cls.strip = re.search(r'<div class="neon-strip".*?</div>\s*</div>', cls.footer, re.S).group(0)

    def test_the_footer_has_the_neon_sign_on_every_page(self):
        self.assertIn('data-neon-sign aria-hidden="true"', self.strip)
        self.assertRegex(self.strip, rf'<svg class="neon-sign__glass" viewBox="{svet.NEON_VIEWBOX}" focusable="false">')
        self.assertRegex(self.strip, rf'<svg class="neon-sign__lit" viewBox="{svet.NEON_VIEWBOX}" focusable="false">')
        for page in (static_pages.render_about(), static_pages.render_contacts(), static_pages.render_404()):
            self.assertEqual(page.count("data-neon-sign"), 1)
        # the rest of the footer is intact
        for part in ('class="footer__watermark"', 'class="footer__grid"', 'class="footer__bottom"', D.PHONE, D.EMAIL):
            self.assertIn(part, self.footer)

    def test_it_is_the_sign_of_svet_py(self):
        tubes = svet.neon_tubes()
        for d in tubes.letters:
            self.assertIn(f'<path d="{neon.compact_path(d)}"/>', self.strip)
        self.assertIn(f'<path id="neon-sign-mint" d="{neon.compact_path(tubes.frame)}"/>', self.strip)
        self.assertIn(f'<path id="neon-sign-script" d="{neon.compact_path(tubes.script)}"/>', self.strip)

    def test_compact_path_only_rounds(self):
        self.assertEqual(neon.compact_path("M 182.8 390.21 L 98.46 -0.04 C 1 2 3 4 5.06 -0.5"),
                         "M182.8 390.2L98.5 0C1 2 3 4 5.1 -.5")
        tubes = svet.neon_tubes()
        for d in (*tubes.letters, tubes.frame, tubes.script):
            a = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", d)]
            b = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", neon.compact_path(d))]
            self.assertEqual(len(a), len(b))
            self.assertLessEqual(max(abs(x - y) for x, y in zip(a, b)), 0.05 + 1e-9)
            self.assertEqual(re.sub(r"[^A-Za-z]", "", d), re.sub(r"[^A-Za-z]", "", neon.compact_path(d)))

    def test_no_raster_images_in_the_strip(self):
        self.assertNotRegex(self.strip, r"<img\b|<image\b")
        self.assertNotRegex(self.strip, RASTER)


class SvetHelperTest(unittest.TestCase):
    def test_the_helper_gives_the_tubes_of_the_logo(self):
        tubes = svet.neon_tubes()
        self.assertEqual(len(tubes.letters), 12)            # G A R A G E, T E A M and the two bars
        for d in (*tubes.letters, tubes.frame, tubes.script):
            self.assertRegex(d, r"^M [\d.]+ [\d.]+ ")
        self.assertIs(svet.neon_tubes(), tubes)              # read once per build

    def test_the_hero_sign_is_still_drawn_from_it(self):
        room = svet.room()
        tubes = svet.neon_tubes()
        self.assertIn(f'<svg class="svet-neon" viewBox="{svet.NEON_VIEWBOX}" aria-hidden="true" focusable="false">', room)
        for d in tubes.letters:
            self.assertIn(f'<path d="{d}"/>', room)
        self.assertIn(f'<g id="svet-neon-mint" fill="none" stroke-linejoin="round"><path d="{tubes.frame}"/></g>', room)
        self.assertIn(f'<path id="svet-neon-script" d="{tubes.script}"/>', room)
        self.assertEqual(room.count('class="svet-neon__lit"'), 1)


class TubeTest(unittest.TestCase):
    def test_a_bend_is_an_arc_and_the_ends_are_painted(self):
        t = neon.bent_tube([(0, 0), (0, 100), (100, 100)], r=20)
        self.assertEqual(t.d, "M0 0L0 80A20 20 0 0 0 20 100L100 100")
        self.assertEqual(t.ends, "M0 0L0 7M100 100L93 100")

    def test_bends_that_do_not_fit_are_a_build_error(self):
        with self.assertRaises(ValueError):
            neon.bent_tube([(0, 0), (0, 30), (30, 30)], r=40)
        with self.assertRaises(ValueError):
            neon.bent_tube([(0, 0)])


class BrickMaterialTest(unittest.TestCase):
    def test_material_is_svg_only_and_the_same_on_every_build(self):
        css = neon.material_css()
        self.assertEqual(css, neon.material_css())
        uris = re.findall(r'url\("([^"]+)"\)', css)
        self.assertEqual(len(uris), 3)                       # bricks at dusk, bricks in neon light, grain
        for u in uris:
            self.assertTrue(u.startswith("data:image/svg+xml,"), u[:40])
        self.assertNotRegex(css, RASTER)
        self.assertIn(f"--neon-tile-w:{neon.TILE_W}px", css)

    def test_running_bond_that_tiles_without_a_seam(self):
        bricks = neon._bricks()
        by_course = {}
        for b in bricks:
            course = int(b.corners[0][1] // neon.COURSE)
            by_course.setdefault(course, []).append(b)
        self.assertEqual(sorted(by_course), list(range(neon.COURSES)))
        for c, row in by_course.items():
            starts = sorted(min(x for x, _ in b.corners) for b in row if min(x for x, _ in b.corners) >= 0)
            # even courses start near 0, odd ones about half a brick further (plus the hand-laid wobble)
            first = starts[0] % neon.MODULE
            expected = neon.MODULE / 2 if c % 2 else 0
            self.assertLessEqual(min(abs(first - expected), abs(first - expected - neon.MODULE)), 9, (c, first))
            # a brick cut by the right edge has its twin one tile to the left, and the other way round
            def key(points, dx=0.0):
                return tuple((round(x + dx, 3), round(y, 3)) for x, y in points)
            corners = [key(o.corners) for o in row]
            for b in row:
                xs = [x for x, _ in b.corners]
                if max(xs) > neon.TILE_W:
                    self.assertIn(key(b.corners, -neon.TILE_W), corners)
                if min(xs) < 0:
                    self.assertIn(key(b.corners, neon.TILE_W), corners)
            # and the course is closed: from 0 to the tile's width every x is covered by a brick or a joint
            spans = sorted((min(x for x, _ in b.corners), max(x for x, _ in b.corners)) for b in row)
            self.assertLessEqual(spans[0][0], neon.JOINT, (c, spans[0]))
            self.assertGreaterEqual(spans[-1][1], neon.TILE_W - neon.JOINT, (c, spans[-1]))
            for (_, end), (start, _) in zip(spans, spans[1:]):
                self.assertLess(start - end, neon.JOINT + 1.6, (c, end, start))   # a joint, never a gap


class StylesAndScriptTest(unittest.TestCase):
    def test_keyframes_animate_opacity_only(self):
        frames = re.findall(r"@keyframes\s+([\w-]+)\s*\{(.*?\})\s*\}", CSS, re.S)
        self.assertGreaterEqual(len(frames), 6)
        for name, body in frames:
            props = set(re.findall(r"([\w-]+)\s*:", body))
            self.assertEqual(props, {"opacity"}, name)

    def test_no_blur_or_filters(self):
        self.assertNotRegex(CSS, r"(?<![\w-])(filter|backdrop-filter)\s*:")
        self.assertNotIn("blur(", CSS)
        self.assertNotIn("text-shadow", CSS)

    def test_reduced_motion_stops_every_neon_animation(self):
        # the element each animation runs on: the last compound of every selector that sets animation: neon-…
        animated = set()
        for selectors, _ in re.findall(r"([^{}]+)\{([^{}]*animation:\s*neon-[^{}]*)\}", CSS):
            for sel in re.split(r",(?![^()]*\))", selectors):
                subject = re.split(r"\s+(?![^()]*\))", sel.strip())[-1]
                animated |= {c for c in re.findall(r"\.([\w-]+)", subject) if not c.startswith("is-")}
        self.assertEqual(animated, {"neon-404__lit", "neon-404__walllit", "neon-404__tube", "neon-404__spill",
                                    "neon-sign__lit", "neon-strip__lit", "nav__label"})
        block = re.search(r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}", CSS, re.S).group(1)
        self.assertIn("animation: none !important", block)
        for cls in animated:
            self.assertIn(f".{cls}", block)

    def test_the_keyboard_keeps_its_tube_on_touch_devices(self):
        # the build moves :hover rules into @media (hover: hover); :focus-visible must stay outside it
        out = guard_hover(CSS)
        outside = re.sub(r"@media \(hover: hover\) \{ .*? \} \}", "", out)
        self.assertIn(".nav__link:focus-visible .nav__label::after", outside)
        self.assertNotIn(".nav__link:hover .nav__label::after", outside)

    def test_script_styles_and_markup_use_no_raster_images(self):
        self.assertNotRegex(CSS, RASTER)
        self.assertNotRegex(JS, RASTER)
        for out in (neon.material_css(), neon.notfound(""), neon.footer_sign()):
            self.assertNotRegex(out, RASTER)
        # and the feature brought no picture files: nothing named after it among the site's images
        self.assertEqual([p for p in (ROOT / "src" / "assets").rglob("*") if "neon" in p.name.lower() and p.suffix not in (".css", ".js")], [])

    def test_menu_labels_keep_their_text_and_links(self):
        nav = re.search(r'<nav class="nav".*?</nav>', layout.header(), re.S).group(0)
        self.assertEqual(re.findall(r'<a class="nav__link" href="([^"]+)"><span class="nav__label">([^<]+)</span></a>', nav),
                         [(h, n) for n, h in D.NAV])


if __name__ == "__main__":
    unittest.main()
