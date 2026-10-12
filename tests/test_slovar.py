# -*- coding: utf-8 -*-
"""«Что сказал мастер?» (build/slovar.py): the glossary data, the page, and the page in the sitemap.
Run: python3 -m unittest discover -s tests"""
import contextlib
import html
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import layout  # noqa: E402
from build import slovar as S  # noqa: E402
from build.static_pages import PAGES as STATIC_PAGES  # noqa: E402

SENSITIVE = ("lambda-zond", "katalizator", "sazhevyj-filtr", "adblue", "egr")


class DataTest(unittest.TestCase):
    def test_number_of_terms(self):
        lo, hi = S.TERMS_RANGE
        self.assertTrue(lo <= len(S.TERMS) <= hi, len(S.TERMS))
        S.check()   # the build's own check passes

    def test_ids_are_unique_latin_slugs_and_free(self):
        ids = [t.id for t in S.TERMS] + [c.key for c in S.CATEGORIES]
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertRegex(i, r"^[a-z][a-z0-9-]*[a-z0-9]$")
            self.assertNotIn(i, S.RESERVED_IDS)

    def test_every_term_is_in_a_known_system_and_no_system_is_empty(self):
        keys = {c.key for c in S.CATEGORIES}
        for t in S.TERMS:
            self.assertIn(t.cat, keys, t.id)
        for c in S.CATEGORIES:
            self.assertGreaterEqual(sum(1 for t in S.TERMS if t.cat == c.key), 3, c.key)

    def test_definitions_are_filled_in_and_short(self):
        for t in S.TERMS:
            self.assertTrue(t.name.strip() and t.text.strip(), t.id)
            self.assertTrue(1 <= S.sentences(t.text) <= 3, f"{t.id}: {S.sentences(t.text)} sentences")
            self.assertRegex(t.text, r"[.!?…]$", t.id)
            if t.wear:
                self.assertRegex(t.wear, r"[.!?…]$", t.id)
            for other in (*t.aka, *t.refs):
                self.assertTrue(other.strip(), t.id)

    def test_no_prices_terms_or_promises(self):
        for t in S.TERMS:
            text = " ".join((t.name, t.text, t.wear, *t.aka, *t.refs))
            self.assertNotRegex(text, r"₽|\bруб|гаранти|скидк|бесплатн", t.id)

    def test_links_go_to_existing_pages_and_never_to_the_forbidden_ones(self):
        linked = 0
        for t in S.TERMS:
            self.assertLessEqual(len(t.links), S.MAX_LINKS, t.id)
            for key in t.links:
                path, name = S._link(key)
                self.assertIn(path, D.BY_PATH, t.id)
                self.assertTrue(name, t.id)
                for bad in S.FORBIDDEN:
                    self.assertNotIn(bad, path, t.id)
                linked += 1
        self.assertGreater(linked, len(S.TERMS))

    def test_a_forbidden_or_missing_page_stops_the_build(self):
        with self.assertRaises(ValueError):
            S._link("no-such-page")
        bad = "/services/cip-tuning/udalenie-i-pereprogrammirovanie-sazevyh-filtrov.html"
        self.assertIn(bad, D.BY_PATH, "the forbidden page exists on the site, the glossary must not link to it")
        with mock.patch.dict(S.PAGES, {"dpf_off": bad}):
            terms = S.TERMS[:-1] + (S.TERMS[-1]._replace(links=("dpf_off",)),)
            with self.assertRaises(ValueError):
                S.check(terms)
        with mock.patch.dict(S.PAGES, {"gone": "/services/net-takoj-stranicy.html"}):
            terms = S.TERMS[:-1] + (S.TERMS[-1]._replace(links=("gone",)),)
            with self.assertRaises(ValueError):
                S.check(terms)

    def test_check_refuses_broken_data(self):
        first = S.TERMS[0]
        cases = {
            "duplicate id": S.TERMS + (first,),
            "unknown system": (first._replace(cat="kuzov"),) + S.TERMS[1:],
            "empty definition": (first._replace(text=""),) + S.TERMS[1:],
            "four sentences": (first._replace(text="Раз. Два. Три. Четыре."),) + S.TERMS[1:],
            "a price": (first._replace(wear="Стоит от 1000 ₽."),) + S.TERMS[1:],
            "see nowhere": (first._replace(see=("net-takogo",)),) + S.TERMS[1:],
            "see itself": (first._replace(see=(first.id,)),) + S.TERMS[1:],
            "too few terms": S.TERMS[:10],
        }
        for what, terms in cases.items():
            with self.subTest(what), self.assertRaises(ValueError):
                S.check(terms)

    def test_see_also_points_to_other_terms(self):
        ids = {t.id for t in S.TERMS}
        for t in S.TERMS:
            self.assertLessEqual(len(t.see), S.MAX_SEE)
            for s in t.see:
                self.assertIn(s, ids, t.id)
                self.assertNotEqual(s, t.id)

    def test_sensitive_terms_are_plain_definitions(self):
        for tid in SENSITIVE:
            t = S.BY_ID[tid]
            text = " ".join((t.text, t.wear)).lower()
            self.assertNotRegex(text, r"удал|отключ|заглуш|закон|штраф|техосмотр|регламент[аеу]? тр|прошивк", tid)

    def test_index_has_every_term_once_and_is_sorted(self):
        rows = S.index_entries()
        own = [r[3].id for r in rows if r[2] is None]
        self.assertEqual(sorted(own), sorted(t.id for t in S.TERMS))
        keys = [(1 if r[0] == "latin" else 0, r[1].lower().replace("ё", "е")) for r in rows]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(S.letters()[-1], "latin")
        for letter, label, target, term in rows:
            self.assertEqual(S.initial(label), letter)
            if target is not None:
                self.assertFalse(S._is_near(label, term.name), label)

    def test_plural(self):
        forms = ("термин", "термина", "терминов")
        self.assertEqual([S.plural(n, *forms) for n in (1, 2, 5, 11, 21, 22, 60, 101, 112)],
                         ["термин", "термина", "терминов", "терминов", "термин", "термина", "терминов", "термин", "терминов"])


class PageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = S.render()

    def test_every_term_is_a_dfn_with_its_id(self):
        for t in S.TERMS:
            self.assertIn(f'<div class="gl-term" id="{t.id}"', self.html)
        self.assertEqual(self.html.count("<dfn "), len(S.TERMS))
        self.assertEqual(self.html.count('<dl class="gl-list">'), len(S.CATEGORIES))
        text = html.unescape(self.html)
        for t in S.TERMS:
            self.assertIn(t.text, text, "the definitions are in the HTML, for search engines and without JS")

    def test_one_h1_and_unique_ids(self):
        self.assertEqual(len(re.findall(r"<h1[\s>]", self.html)), 1)
        ids = re.findall(r'\sid="([^"]+)"', self.html)
        self.assertEqual(len(ids), len(set(ids)))

    def test_json_ld_defined_term_set(self):
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', self.html, re.S)
        self.assertEqual(len(blocks), 1)
        graph = json.loads(blocks[0])["@graph"]
        term_set = next(n for n in graph if n["@type"] == "DefinedTermSet")
        self.assertEqual([n["name"] for n in term_set["hasDefinedTerm"]], [t.name for t in S.TERMS])
        self.assertTrue(all(n["@type"] == "DefinedTerm" and n["url"].startswith(D.SITE_URL + S.PATH + "#")
                            for n in term_set["hasDefinedTerm"]))
        self.assertTrue(any(n["@type"] == "BreadcrumbList" for n in graph))

    def test_every_link_on_the_page_is_a_real_page(self):
        main = self.html.split('<main id="main">', 1)[1].split("</main>", 1)[0]   # the glossary, not the site's footer
        for href in set(re.findall(r'href="(/services/[^"]+)"', main)):
            self.assertIn(href, D.BY_PATH)
            self.assertFalse(any(bad in href for bad in S.FORBIDDEN), href)
        anchors = set(re.findall(r'href="#([^"]+)"', self.html)) - {"main"}
        ids = set(re.findall(r'\sid="([^"]+)"', self.html))
        self.assertFalse(anchors - ids, "every #link has its target on the page")

    def test_call_back_buttons_carry_a_message(self):
        presets = re.findall(r'data-gl-cta="[a-z]+"|data-preset="([^"]+)"', self.html)
        messages = [json.loads(html.unescape(p))["message"] for p in presets if p]
        self.assertGreaterEqual(len(messages), 3)
        self.assertTrue(all(m.startswith("Хочу записаться на диагностику") for m in messages))

    def test_title_description_from_page_seo(self):
        seo = D.PAGE_SEO[S.SEO_KEY]
        self.assertLessEqual(len(seo["title"]), 70)
        self.assertTrue(120 <= len(seo["meta_description"]) <= 170)
        self.assertIn(f"<title>{html.escape(seo['title'], quote=True)}</title>", self.html)
        self.assertIn(f'<link rel="canonical" href="{D.SITE_URL}{S.PATH}">', self.html)

    def test_links_carry_the_base_path(self):
        try:
            D.set_base("/v/slovar")
            page = D.rebase(S.render())
        finally:
            D.set_base("")
        self.assertNotRegex(page, r'href="/services/')
        self.assertIn('href="/v/slovar/services/remont-hodovoj/zamena-srusa.html"', page)
        self.assertIn('href="/v/slovar/call/request/"', page)

    def test_registered_and_linked_from_the_footer(self):
        self.assertIn(S.PATH, STATIC_PAGES)
        self.assertIn(f'href="{S.PATH}"', layout.footer())


class SitemapTest(unittest.TestCase):
    """build.py itself (the photos step stubbed out): the page is written and listed in sitemap.xml."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "site"
        argv = sys.argv
        sys.argv = ["build.py", "--out", str(cls.out)]
        try:
            spec = importlib.util.spec_from_file_location("garage_build_script", ROOT / "build.py")
            build = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(build)
            build.process_images = lambda *a, **k: (0, 0)   # the photos do not matter here and take most of the time
            build.make_logo_assets = lambda *a, **k: None
            with contextlib.redirect_stdout(io.StringIO()):
                build.main()
        finally:
            sys.argv = argv
            D.set_base("")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_page_is_in_the_sitemap(self):
        sitemap = (self.out / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"<loc>{D.SITE_URL}{S.PATH}</loc>", sitemap)
        self.assertTrue((self.out / "slovar" / "index.html").exists())

    def test_the_home_page_links_to_it(self):
        home = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn('class="stuk__more"', home)
        self.assertIn(f'href="{S.PATH}"', home)

    def test_styles_and_script_are_in_the_bundle(self):
        css = (self.out / "assets" / "css" / "site.css").read_text(encoding="utf-8")
        js = (self.out / "assets" / "js" / "site.js").read_text(encoding="utf-8")
        self.assertIn(".gl-term", css)
        self.assertIn("[data-gl]", js)


if __name__ == "__main__":
    unittest.main()
