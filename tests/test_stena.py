# -*- coding: utf-8 -*-
"""«Стена направлений» (build/stena.py, src/assets/css/stena.css, src/assets/js/stena.js): /services.html shows the
28 directions as brick-shaped links, keeps every link and text of the old cards, varies every brick deterministically,
uses no images and keeps the painted lettering AA-readable on every brick.  Run: python3 -m unittest discover -s tests"""
import ast
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import stena as S  # noqa: E402
from build.icons import CATEGORY_ICONS  # noqa: E402
from build.services import _card_text, _plural, render_services_index  # noqa: E402

CSS = (ROOT / "src" / "assets" / "css" / "stena.css").read_text(encoding="utf-8")
JS = (ROOT / "src" / "assets" / "js" / "stena.js").read_text(encoding="utf-8")
SLUGS = [S.slug_of(c["href"]) for c in D.CATEGORIES]


def text_of(fragment: str) -> str:
    """Visible text: tags out, entities decoded, soft hyphens and no-break spaces as a reader sees them."""
    plain = html.unescape(re.sub(r"<[^>]+>", " ", fragment)).replace("­", "").replace(" ", " ")
    return re.sub(r"\s+", " ", plain).strip()


def element(page: str, start: str, tag: str) -> str:
    """The element that starts with `start`, up to the first closing `tag` after it (no nested element of that tag)."""
    i = page.index(start)
    end = page.index(f"</{tag}>", i)
    return page[i:end + len(tag) + 3]


# ---------- WCAG 2.x contrast; layers composited in sRGB, as browsers paint them ----------
def _linear(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb) -> float:
    r, g, b = (_linear(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def over(base, top, alpha: float):
    return tuple(x * (1 - alpha) + y * alpha for x, y in zip(base, top))


def css_var(name: str) -> str:
    m = re.search(rf"\s{re.escape(name)}:\s*([^;]+);", CSS)
    if not m:
        raise AssertionError(f"stena.css: нет {name}")
    return m.group(1).split("/*")[0].strip()


def css_rgb(name: str) -> tuple:
    value = css_var(name)
    if value.startswith("#"):
        return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
    return tuple(int(x) for x in re.findall(r"\d+", value)[:3])


class WallMarkupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = render_services_index()
        start = cls.page.index('<div class="stena reveal"')
        cls.wrapper = cls.page[start:cls.page.index('<p class="empty-state">', start)]
        cls.wall = element(cls.page, '<ul class="stena__wall"', "ul")
        cls.index = element(cls.page, '<details class="stena-index', "details")
        cls.bricks = re.findall(r'<li class="stena__slot"[^>]*>(.*?)</li>', cls.wall, re.S)

    def test_all_28_directions_are_links_in_a_list(self):
        self.assertEqual(len(D.CATEGORIES), 28)
        self.assertIn('role="list"', self.wall.split(">", 1)[0])
        self.assertEqual(len(self.bricks), 28)
        self.assertEqual(self.wall.count("<li"), 28, "the list holds the directions and nothing else")
        hrefs = []
        for item in self.bricks:
            self.assertEqual(item.count("<a "), 1, item[:120])
            hrefs.append(re.search(r'<a class="brick" href="([^"]+)"', item).group(1))
        self.assertEqual(hrefs, [c["href"] for c in D.CATEGORIES])

    def test_every_brick_shows_its_name_its_count_and_its_icon(self):
        for i, (item, c) in enumerate(zip(self.bricks, D.CATEGORIES)):
            n = len(c["subs"])
            count = f"{n} {_plural(n, 'услуга', 'услуги', 'услуг')}" if n else "направление"
            self.assertEqual(text_of(item), f"{c['name']} {i + 1:02d} · {count}", "the name first: it names the link")
            self.assertIn(f'<use href="#i-{CATEGORY_ICONS[SLUGS[i]]}"/>', item)
        labels = [text_of(re.search(r'<span class="brick__label">(.*?)</span>', b).group(1)) for b in self.bricks]
        self.assertEqual(labels[0], "01 · 6 услуг")
        self.assertEqual(labels[8], "09 · 4 услуги")
        self.assertEqual(labels[12], "13 · 1 услуга")
        self.assertEqual(labels[15], "16 · направление")

    def test_the_page_keeps_every_link_and_text_of_the_old_cards(self):
        feature = self.wall + self.index
        text = text_of(self.page)
        subs = re.findall(r'<div class="cat-card__subs">(.*?)</div>', self.index, re.S)
        self.assertEqual(sum(s.count("<a ") for s in subs), sum(len(c["subs"]) for c in D.CATEGORIES))
        for c in D.CATEGORIES:
            self.assertEqual(feature.count(f'href="{c["href"]}"'), 2, f"the brick and the list both link {c['href']}")
            for s in c["subs"]:
                self.assertIn(f'<a href="{s["href"]}">{D.esc(s["name"])}</a>', self.index)
            if not c["subs"]:
                self.assertIn(text_of(D.esc(_card_text(c["href"]))), text)

    def test_the_search_still_has_what_pages_js_filters(self):
        self.assertIn("data-filter ", self.page)
        self.assertIn("data-filter-count>28 направлений<", self.page)
        self.assertIn('<p class="empty-state">', self.page)
        cards = re.findall(r'<li class="cat-card" data-title="([^"]+)">', self.index)
        self.assertEqual([html.unescape(t) for t in cards], [c["name"] for c in D.CATEGORIES])
        self.assertNotIn("­", self.index, "the list keeps the names as written (search, SEO)")

    def test_no_images_anywhere_in_the_feature(self):
        for name, markup in (("wall", self.wrapper), ("index", self.index)):
            self.assertNotRegex(markup, r"<(img|picture|image|video|source|canvas)\b", name)
            self.assertNotRegex(markup, r"\.(png|jpe?g|webp|gif|avif|bmp)\b", name)
        self.assertNotRegex(CSS, r"\.(png|jpe?g|webp|gif|avif|bmp)\b")
        urls = re.findall(r'url\((?:"|&quot;)?([^")&]+)', self.wrapper) + re.findall(r'url\("?([^")]+)', CSS)
        self.assertEqual(len([u for u in urls if u.startswith("data:")]), len(S.GRAIN_TILES), "the grain tiles and nothing else")
        for u in urls:
            if u.startswith("#"):
                continue   # a reference to the shared gradient inside the page
            self.assertTrue(u.startswith("data:image/svg+xml,"), u[:60])
            svg = unquote(u.split(",", 1)[1])
            self.assertNotRegex(svg, r"<(image|use|filter|fe[A-Z])|href", "plain shapes: no external refs, no SVG filters")

    def test_decoration_is_hidden_from_screen_readers(self):
        start = self.page.index('<div class="stena reveal"')
        wrapper = self.page[start:self.page.index('<p class="empty-state">', start)]
        for part in ("stena__beam", "stena__plinth", "stena__light", "stena__lamps"):
            self.assertIn(f'<div class="{part}" aria-hidden="true">', wrapper)
        self.assertEqual(self.wall.count('<svg class="brick__wear" aria-hidden="true" focusable="false">'), 28)
        self.assertEqual(self.wall.count('class="ic brick__icon" aria-hidden="true"'), 28)

    def test_lettering_hyphenates_only_what_a_phone_brick_needs(self):
        self.assertIn("Ремонт авто­кондиционеров", self.wall)
        self.assertEqual(self.wall.count("­"), 1)
        self.assertIn("и ходовой", self.wall, "no one-letter word at the end of a painted line")


class VariationTest(unittest.TestCase):
    def test_slugs_are_the_icon_keys(self):
        self.assertEqual(set(SLUGS), set(CATEGORY_ICONS))

    def test_same_slug_same_brick(self):
        for slug in SLUGS:
            a, b = S.variation(slug), S.variation(slug)
            self.assertEqual(a, b)
            self.assertEqual((S.style(a), S.wear_svg(a)), (S.style(b), S.wear_svg(b)))

    def test_stable_across_processes_and_hash_seeds(self):
        code = ("import json, sys; sys.path.insert(0, %r); from build import stena as S; "
                "print(json.dumps([S.grain_style()] + [[S.style(S.variation(s)), S.wear_svg(S.variation(s))] for s in %r]))") % (str(ROOT), SLUGS)
        here = [S.grain_style()] + [[S.style(S.variation(s)), S.wear_svg(S.variation(s))] for s in SLUGS]
        for seed in ("0", "1234"):
            out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                                 env={**os.environ, "PYTHONHASHSEED": seed}).stdout
            self.assertEqual(json.loads(out), here)

    def test_the_seed_is_sha256_of_the_slug(self):
        expected = int.from_bytes(hashlib.sha256(b"stena:diagnostika:0").digest()[:4], "big") / 2 ** 32
        self.assertEqual(S._Seed("stena:diagnostika").next(), expected)

    def test_known_bricks_do_not_drift(self):
        # fixed points: when these change, every brick on the wall changed — do it on purpose and update them
        self.assertEqual(S.style(S.variation("diagnostika")), GOLDEN["diagnostika"])
        self.assertEqual(S.hex_of(S.variation("hranenie-sin").clay), GOLDEN["hranenie-sin"])
        self.assertEqual(hashlib.sha256(S.grain_style().encode("utf-8")).hexdigest()[:16], GOLDEN["grain"])

    def test_the_bricks_differ(self):
        looks = [S.variation(s) for s in SLUGS]
        self.assertGreaterEqual(len({look.clay for look in looks}), 20, "the clay varies brick to brick")
        self.assertEqual(len({look.radii for look in looks}), 28)
        self.assertTrue(any(look.burn for look in looks) and not all(look.burn for look in looks))
        self.assertTrue(any(look.crack for look in looks) and any(look.smear for look in looks) and any(look.chips for look in looks))
        for look in looks:
            self.assertTrue(any(all(abs(x - y) <= S.JITTER for x, y in zip(base, look.clay)) for base in S.CLAYS), look.clay)


GOLDEN = {   # see test_known_bricks_do_not_drift
    "diagnostika": ("--b:#86422b;--gx:72px;--gy:19px;--m1:22% 40%;--m1s:18% 62%;--m1a:.27;--m2:72% 35%;--m2s:51% 58%;--m2a:.39;"
                    "--m3:42% 48%;--m3s:43% 116%;--m3a:.4;--r:2.3px 2.8px 2.7px 4px / 2.3px 1.7px 2.3px 3.4px;--ins:1.5px 0 .5px 0;"
                    "--burn:.37;--burn-dir:90deg"),
    "hranenie-sin": "#5f2524",
    "grain": "db1d0a6c44f33b9b",
}


class LetteringContrastTest(unittest.TestCase):
    """The painted lettering on the brick under the strongest light that can fall under or over it (WCAG AA 4.5:1)."""

    def setUp(self):
        self.paint, self.lit_paint, self.lamp = css_rgb("--paint"), css_rgb("--paint-lit"), css_rgb("--lamp")
        self.pool, self.lit = float(css_var("--pool")), float(css_var("--lit"))

    def worst(self, clay) -> float:
        face = over(clay, S.SMEAR_RGB, S.SMEAR_MAX)                     # a mortar smear under the letters
        normal = contrast(over(face, self.lamp, self.pool), over(self.paint, self.lamp, self.pool))
        pulled = contrast(over(over(face, self.lamp, self.lit), self.lamp, self.pool), over(self.lit_paint, self.lamp, self.pool))
        return min(normal, pulled)

    def test_every_brick_on_the_wall_is_aa(self):
        for slug, c in zip(SLUGS, D.CATEGORIES):
            clay = S.variation(slug).clay
            self.assertGreaterEqual(self.worst(clay), 4.5, f"{c['name']}: {clay}")

    def test_every_possible_clay_is_aa(self):
        # a future direction gets any clay at either end of its jitter
        j = S.JITTER
        for base in S.CLAYS:
            for d in ((r, g, b) for r in (-j, j) for g in (-j, j) for b in (-j, j)):
                clay = tuple(x + dx for x, dx in zip(base, d))
                self.assertGreaterEqual(self.worst(clay), 4.5, clay)

    def test_the_smear_gradient_is_within_its_budget(self):
        stops = [float(x) for x in re.findall(r'stop-opacity="([\d.]+)"', S._defs())]
        self.assertEqual(max(stops), S.SMEAR_STOPS[0])
        self.assertAlmostEqual(S.SMEAR_MAX, max(stops) * max(S.SMEAR_OPACITY))


class BondAndBundleTest(unittest.TestCase):
    def test_running_bond_rules_for_four_three_and_two_a_course(self):
        for n in (4, 3, 2):
            period, first = 2 * n - 1, n + 1
            self.assertIn(f".stena__slot:nth-child({period}n + {first} of :not([hidden])) {{ grid-column: 2 / span 2; }}", CSS)
            self.assertIn(f"repeat({2 * n}, minmax(0, 1fr))", CSS)

    def test_stylesheet_and_script_come_after_the_services_list(self):
        tree = ast.parse((ROOT / "build.py").read_text(encoding="utf-8"))
        orders = {t.id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                  for t in node.targets if isinstance(t, ast.Name) and t.id in ("CSS_ORDER", "JS_ORDER")}
        css, js = orders["CSS_ORDER"], orders["JS_ORDER"]
        self.assertGreater(css.index("stena.css"), css.index("pages.css"), "the list's card styles are overridden")
        self.assertGreater(js.index("stena.js"), js.index("pages.js"), "the wall mirrors the search")

    def test_script_has_no_animation_loop(self):
        self.assertNotRegex(JS, r"requestAnimationFrame|setInterval")


if __name__ == "__main__":
    unittest.main()
