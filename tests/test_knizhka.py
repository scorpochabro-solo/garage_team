# -*- coding: utf-8 -*-
"""«Моя машина» (build/knizhka.py, src/assets/js/knizhka.js + knizhka-ui.js): the page and its hooks, the build and the
sitemap, and — through node (tests/knizhka_logic.cjs) — the script's own logic: the VIN check, the months and days of
the next service, the calendar file, the check of a loaded copy.  Run: python3 -m unittest discover -s tests"""
import contextlib
import html
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import knizhka as K  # noqa: E402
from build import layout  # noqa: E402
from build.static_pages import PAGES  # noqa: E402

NODE = shutil.which("node")
SCRIPT = ROOT / "tests" / "knizhka_logic.cjs"
JS = [ROOT / "src" / "assets" / "js" / n for n in ("knizhka.js", "knizhka-ui.js")]
FORBIDDEN = ("udalenie", "cip-tuning", "ksenon", "tehosmotr")
KEYS = [k for k, _, _ in K.WORKS]


def js(*calls):
    """[result] of G.knizhka calls; the machine's zone is Los Angeles (daylight saving) and must not matter."""
    out = subprocess.run([NODE, str(SCRIPT), json.dumps(calls, ensure_ascii=False)], capture_output=True, text=True,
                         check=True, env={"TZ": "America/Los_Angeles", "PATH": ""}).stdout
    rows = json.loads(out)
    for row in rows:
        if not row["ok"]:
            raise AssertionError(row["error"])
    return [row["value"] for row in rows]


def one(fn, *args):
    return js([fn, *args])[0]


def entry(id_, date, km, works, text="", note="", t=1):
    return {"id": id_, "date": date, "km": km, "works": works, "text": text, "note": note, "created": t, "updated": t}


def book(car_km=84500, km_date="2026-09-30", reminder=None, entries=None):
    return {"format": "garage-knizhka", "version": 1, "id": "book-test",
            "car": {"brand": "Kia", "model": "Rio", "year": 2017, "engine": "1,6", "vin": "", "km": car_km, "kmDate": km_date},
            "reminder": reminder or {"km": 15000, "months": 12},
            "entries": entries if entries is not None else [
                entry("last-to", "2026-05-12", 70000, ["to", "oil"], t=2),
                entry("tires", "2026-06-20", 74000, ["tires"], t=3),
                entry("old-to", "2025-05-01", 55000, ["to"], t=1),        # older «ТО» later in the list
            ]}


def unfold(text):
    """RFC 5545 3.1: a CRLF followed by a space joins two lines."""
    return text[:-2].replace("\r\n ", "").split("\r\n")


def ics_unescape(value):
    return re.sub(r"\\(.)", lambda m: "\n" if m.group(1) in "nN" else m.group(1), value)


# ---------------------------------------------------------------- the page, the hooks, the texts
class PageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGES[K.PATH]()
        cls.body = K.body()
        m = re.search(r'data-kn-conf="([^"]+)"', cls.body)
        cls.conf = json.loads(html.unescape(m.group(1)))

    def test_registered_with_its_own_title_and_description(self):
        seo = D.PAGE_SEO[K.SEO_KEY]
        self.assertIn(f"<title>{D.esc(seo['title'])}</title>", self.page)
        self.assertIn(f'<meta name="description" content="{D.esc(seo["meta_description"])}">', self.page)
        self.assertLessEqual(len(seo["title"]), 70)
        self.assertTrue(120 <= len(seo["meta_description"]) <= 170)
        self.assertIn(f'<link rel="canonical" href="{D.SITE_URL}{K.PATH}">', self.page)
        self.assertEqual(len(re.findall(r"<h1[\s>]", self.page)), 1)
        self.assertIn(f">{K.H1} <span class=\"kn-h1-sub\">{K.H1_SUB}</span></h1>", self.page)

    def test_main_query_is_in_the_title_and_free(self):
        from seo.validate_content import has_words, norm   # the same check as seo/validate_content.py
        seo = D.PAGE_SEO[K.SEO_KEY]
        self.assertTrue(has_words(seo["title"], seo["main"]))
        cores = [json.loads(f.read_text(encoding="utf-8"))["main"]["phrase"] for f in (ROOT / "seo" / "core").glob("*.json")]
        self.assertNotIn(norm(seo["main"]), {norm(c) for c in cores})

    def test_the_honest_note_and_the_no_js_text_need_no_script(self):
        self.assertIn(K.PRIVACY, html.unescape(self.body))
        nojs = re.search(r"<noscript>(.*?)</noscript>", self.body, re.S).group(1)
        self.assertIn("JavaScript", nojs)
        self.assertIn(f'href="tel:{D.PHONE_TEL}"', nojs)
        self.assertIn('data-knizhka data-state="start"', self.body)
        self.assertRegex(self.body, r'<div class="kn" data-knizhka [^>]*hidden>', "the tool waits for the script")
        self.assertNotIn('class="reveal', self.body, "nothing of the page may stay invisible without JS")

    def test_the_script_gets_every_phrase_and_the_marks(self):
        self.assertEqual(self.conf["texts"], K.TEXTS)
        self.assertEqual([w["key"] for w in self.conf["works"]], KEYS)
        self.assertEqual(self.conf["phone"], D.PHONE)
        code = "\n".join(p.read_text(encoding="utf-8") for p in JS)
        used = set(re.findall(r"\bT\.(\w+)", code)) | set(re.findall(r"\bt\('(\w+)'", code))
        used |= set(re.findall(r"count\([^;]*?, '(p\w+)'\)", code))
        self.assertFalse(used - set(K.TEXTS), "a phrase the script uses is missing in build/knizhka.py TEXTS")
        self.assertIn(f"const KEY = '{K.STORAGE_KEY}';", code)

    def test_marks_are_real_checkboxes_in_both_places(self):
        for name in ("works", "book-works"):
            values = re.findall(rf'<input type="checkbox" name="{name}" value="(\w+)"', self.body)
            self.assertEqual(values, KEYS, name)
        self.assertEqual([label for _, label, _ in K.WORKS], ["ТО", "Замена масла", "Фильтры", "Тормоза", "Шины", "Диагностика"])

    def test_fields_have_labels_and_the_right_keyboards(self):
        for fid in re.findall(r'<input class="input[^"]*" id="(kn-[^"]+)"', self.body):
            self.assertIn(f'for="{fid}"', self.body, fid)
        self.assertRegex(self.body, r'id="kn-c-vin"[^>]*autocapitalize="characters"[^>]*spellcheck="false"')
        for fid in ("kn-c-km", "kn-e-km", "kn-o-km", "kn-i-km", "kn-i-months", "kn-c-year"):
            self.assertRegex(self.body, rf'id="{fid}"[^>]*inputmode="numeric"[^>]*autocomplete="off"', fid)
        self.assertRegex(self.body, r'id="kn-e-date"[^>]*type="date"')

    def test_no_link_to_the_pages_that_are_not_promoted(self):
        own = self.body + K.footer_link() + K.fill_button()      # the shared header and footer are not this feature's
        for href in re.findall(r'href="([^"]+)"', own):
            self.assertFalse(any(f in href for f in FORBIDDEN), href)
            if href.startswith("/services/"):
                self.assertIn(href, D.BY_PATH, "a link to an existing service page")
        self.assertIn(f'href="{K.TO_PAGE}"', self.body)

    def test_no_interval_is_suggested(self):
        """the interval comes from the owner's book: no numbers in its fields and no «every 15 000 km» anywhere"""
        form = re.search(r'<form class="kn-interval".*?</form>', self.body, re.S).group(0)
        self.assertNotIn("value=", form)
        self.assertNotIn("placeholder=", form)
        text = html.unescape(re.sub(r"<[^>]+>", " ", self.body))
        self.assertNotRegex(text, r"кажд\w+\s+\d")


class HooksTest(unittest.TestCase):
    def test_footer_links_the_book_on_every_page(self):
        self.assertIn(f'<a class="kn-foot" href="{K.PATH}">', layout.footer())

    def test_request_form_has_the_hidden_fill_button_in_step_one(self):
        form = layout.request_section()
        panel = re.search(r'data-panel="1">(.*?)data-panel="2"', form, re.S).group(1)
        self.assertRegex(panel, r'<button class="kn-fill" type="button" data-kn-fill="[^"]+" hidden>')
        self.assertLess(panel.index("data-kn-fill"), panel.index('data-mode="select"'))
        for fid in ("text_car_brand", "text_car_model", "text_car_year", "text_car_type", "car_vin"):
            self.assertIn(f'id="{fid}"', form, "the fields the button fills")


class BuildTest(unittest.TestCase):
    """build.py itself into a temporary folder (pictures skipped): the page is written and listed in the sitemap."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "dist"
        argv = sys.argv
        sys.argv = ["build.py", "--out", str(out)]
        try:
            spec = importlib.util.spec_from_file_location("_knizhka_build", ROOT / "build.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        finally:
            sys.argv = argv
        mod.process_images = lambda *a, **k: (0, 0)      # the pictures are not what is tested here
        mod.make_logo_assets = lambda *a, **k: None
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mod.main()
        finally:
            D.set_base("")
        cls.out = out

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, rel):
        return (self.out / rel).read_text(encoding="utf-8")

    def test_page_is_built(self):
        page = self.read("moya-mashina/index.html")
        self.assertIn("data-knizhka", page)
        self.assertIn('<script src="/assets/js/site.js?v=', page)

    def test_page_is_in_the_sitemap(self):
        self.assertIn(f"<loc>{D.SITE_URL}{K.PATH}</loc>", self.read("sitemap.xml"))

    def test_hooks_are_on_other_pages(self):
        home = self.read("index.html")
        self.assertIn(f'class="kn-foot" href="{K.PATH}"', home)
        self.assertIn("data-kn-fill", home)
        self.assertIn(f'class="kn-foot" href="{K.PATH}"', self.read("contacts/index.html"))

    def test_bundles_carry_the_book(self):
        code = self.read("assets/js/site.js")
        self.assertIn(f"const KEY = '{K.STORAGE_KEY}';", code)
        self.assertLess(code.index("knizhka: «Моя машина»"), code.index("knizhka-ui: the page"), "the model comes before the page")
        self.assertLess(code.index("G.openModal = "), code.index("knizhka-ui: the page"), "core.js first")
        self.assertIn(".kn-plate", self.read("assets/css/site.css"))

    def test_sub_path_build_rebases_the_links(self):
        D.set_base("/v/knizhka")
        try:
            page = D.rebase(PAGES[K.PATH]())
            footer = D.rebase(layout.footer())
        finally:
            D.set_base("")
        self.assertIn('href="/v/knizhka/moya-mashina/"', footer)
        self.assertNotRegex(page, r'(href|src)="/(?!/|v/knizhka)')


# ---------------------------------------------------------------- the script's logic (node)
@unittest.skipUnless(NODE, "node is not installed")
class VinTest(unittest.TestCase):
    def test_valid_and_normalised(self):
        good = "XW8ZZZ61ZEG061733"
        self.assertEqual(one("checkVin", good), {"value": good, "error": None, "length": 17, "fixed": False})
        self.assertEqual(one("checkVin", " xw8 zzz61z-eg061733 ")["value"], good)
        self.assertIsNone(one("checkVin", "x w\u00a08zzz61z\u2011eg061733")["error"], "spaces of every kind and hyphens go")
        self.assertEqual(one("checkVin", "wvwzzz1jzxw000001")["value"], "WVWZZZ1JZXW000001")

    def test_cyrillic_look_alikes_become_latin(self):
        r = one("checkVin", "ХW8ZZZ61ZЕG061733")                    # Cyrillic Х and Е
        self.assertEqual((r["value"], r["error"], r["fixed"]), ("XW8ZZZ61ZEG061733", None, True))
        self.assertEqual(one("normalizeVin", "авекмнорстух"), "ABEKMHOPCTYX")

    def test_errors(self):
        rows = js(["checkVin", "XW8ZZZ61ZEG06173"], ["checkVin", "XW8ZZZ61ZEG0617333"], ["checkVin", "XW8ZZZ61ZOG061733"],
                  ["checkVin", "XW8ZZZ61ZIG061733"], ["checkVin", "XW8ZZZ61ZQG061733"], ["checkVin", "XW8ZZZ61ZОG061733"],
                  ["checkVin", "XW8ZZZ61Z_G061733"], ["checkVin", "XW8ZZZ61ZЖG061733"])
        self.assertEqual([(r["error"], r["length"]) for r in rows],
                         [("length", 16), ("length", 18), ("ioq", 17), ("ioq", 17), ("ioq", 17), ("ioq", 17), ("chars", 17), ("chars", 17)])

    def test_empty_is_fine(self):
        self.assertEqual(js(["checkVin", ""], ["checkVin", "   "]), [{"value": "", "error": None, "length": 0, "fixed": False}] * 2)


@unittest.skipUnless(NODE, "node is not installed")
class DatesTest(unittest.TestCase):
    def test_month_arithmetic_clamps_to_the_end_of_the_month(self):
        cases = [("2026-01-31", 1, "2026-02-28"), ("2028-01-31", 1, "2028-02-29"), ("2026-03-31", 1, "2026-04-30"),
                 ("2026-08-31", 6, "2027-02-28"), ("2026-12-15", 1, "2027-01-15"), ("2024-02-29", 12, "2025-02-28"),
                 ("2026-05-12", 12, "2027-05-12"), ("2026-01-31", 13, "2027-02-28"), ("2026-11-30", 3, "2027-02-28"),
                 ("2026-10-31", 120, "2036-10-31")]
        self.assertEqual(js(*[["addMonths", d, n] for d, n, _ in cases]), [want for _, _, want in cases])

    def test_days_do_not_drift_with_daylight_saving(self):
        self.assertEqual(js(["daysBetween", "2026-03-07", "2026-03-09"], ["daysBetween", "2026-10-31", "2026-11-02"],
                            ["daysBetween", "2026-01-01", "2027-01-01"], ["daysBetween", "2028-01-01", "2029-01-01"],
                            ["daysBetween", "2026-09-30", "2027-05-12"], ["addDays", "2026-12-31", 1], ["addDays", "2028-02-28", 1],
                            ["addDays", "2026-03-08", 1]),
                         [2, 2, 365, 366, 224, "2027-01-01", "2028-02-29", "2026-03-09"])

    def test_only_real_dates(self):
        self.assertEqual(js(["parseDate", "2026-02-29"], ["parseDate", "2026-13-01"], ["parseDate", "26-01-01"], ["parseDate", "2028-02-29"]),
                         [None, None, None, {"y": 2028, "m": 2, "d": 29}])

    def test_mileage_typed_by_a_person(self):
        self.assertEqual(js(["parseKm", "84 500"], ["parseKm", "84500 км"], ["parseKm", ""], ["parseKm", "12.5"], ["parseKm", "-5"],
                            ["parseKm", "2000001"], ["fmtNum", 84500], ["fmtNum", 1234567]),
                         [84500, 84500, None, "NaN", "NaN", "NaN", "84\u00a0500", "1\u00a0234\u00a0567"])


@unittest.skipUnless(NODE, "node is not installed")
class ForecastTest(unittest.TestCase):
    def test_soon_by_mileage_from_the_last_service(self):
        f = one("forecast", book(), "2026-09-30")
        self.assertEqual(f["base"], {"id": "last-to", "date": "2026-05-12", "km": 70000}, "the latest «ТО» by date, not by order")
        km, time = f["km"], f["time"]
        self.assertEqual((km["due"], km["current"], km["used"], km["left"]), (85000, 84500, 14500, 500))
        self.assertAlmostEqual(km["frac"], 14500 / 15000)
        self.assertAlmostEqual(f["rate"], 14500 / 141)                         # 141 days from 12.05 to 30.09
        self.assertEqual(km["date"], "2026-10-05")                              # 500 km at ~102.8 km a day: 5 days
        self.assertEqual((time["due"], time["left"], time["passed"], time["total"]), ("2027-05-12", 224, 141, 365))
        self.assertEqual((f["date"], f["by"], f["state"]), ("2026-10-05", "km", "soon"))

    def test_ok_and_the_earlier_limit_wins(self):
        f = one("forecast", book(car_km=76000, km_date="2026-07-12"), "2026-07-20")
        self.assertEqual((f["km"]["left"], f["km"]["date"], f["time"]["left"]), (9000, "2026-10-12", 296))
        self.assertEqual((f["date"], f["by"], f["state"]), ("2026-10-12", "km", "ok"))
        f = one("forecast", book(car_km=76000, km_date="2026-07-12", reminder={"km": 15000, "months": 3}), "2026-07-20")
        self.assertEqual((f["date"], f["by"]), ("2026-08-12", "time"))

    def test_over_by_mileage_and_by_time(self):
        f = one("forecast", book(car_km=86200), "2026-09-30")
        self.assertEqual((f["state"], f["km"]["left"], f["km"]["date"]), ("over", -1200, None))
        f = one("forecast", book(car_km=76000, km_date="2026-07-12"), "2027-05-13")
        self.assertEqual((f["state"], f["time"]["left"]), ("over", -1))
        f = one("forecast", book(car_km=76000, km_date="2026-07-12"), "2027-05-12")
        self.assertEqual((f["state"], f["time"]["left"]), ("over", 0), "the due day itself: time for the service")

    def test_an_old_reading_makes_the_estimate_about_now(self):
        f = one("forecast", book(car_km=76000, km_date="2026-07-12"), "2026-11-01")
        self.assertEqual((f["km"]["date"], f["guess"], f["state"], f["date"], f["by"]), ("2026-11-01", True, "soon", "2026-11-01", "km"))

    def test_months_only_and_january_31(self):
        f = one("forecast", book(reminder={"km": None, "months": 6}), "2026-09-30")
        self.assertEqual((f["km"], f["time"]["due"], f["time"]["left"], f["time"]["total"], f["state"]), (None, "2026-11-12", 43, 184, "ok"))
        jan = book(reminder={"km": None, "months": 1}, entries=[entry("jan", "2026-01-31", 60000, ["to"])])
        f = one("forecast", jan, "2026-02-20")
        self.assertEqual((f["time"]["due"], f["time"]["left"], f["date"]), ("2026-02-28", 8, "2026-02-28"))

    def test_km_only_without_a_daily_average_yet(self):
        b = book(reminder={"km": 10000, "months": None}, entries=[entry("fresh", "2026-09-25", 84000, ["to"])])
        f = one("forecast", b, "2026-09-30")
        self.assertEqual((f["km"]["left"], f["rate"], f["date"], f["state"]), (9500, None, None, "ok"))

    def test_states_before_the_count(self):
        self.assertEqual(one("forecast", book(reminder={"km": None, "months": None}), "2026-09-30")["state"], "setup")
        self.assertEqual(one("forecast", book(entries=[entry("t", "2026-06-20", 74000, ["tires"])]), "2026-09-30")["state"], "need-to")
        f = one("forecast", book(reminder={"km": 15000, "months": None}, entries=[entry("t", "2026-05-12", None, ["to"])]), "2026-09-30")
        self.assertEqual((f["state"], f["noBaseKm"]), ("no-km", True))

    def test_the_highest_known_mileage_counts(self):
        f = one("forecast", book(car_km=60000), "2026-09-30")      # the passport is behind the log
        self.assertEqual((f["km"]["current"], f["km"]["used"]), (74000, 4000))


@unittest.skipUnless(NODE, "node is not installed")
class IcsTest(unittest.TestCase):
    EVENT = {"uid": "knizhka-abc123-last-to@garage.team", "stamp": "2026-09-30T10:15:07.123Z", "date": "2026-10-05",
             "summary": "ТО: Kia Rio", "url": "https://garage.team/moya-mashina/", "alarm": "Завтра ТО: Kia Rio",
             "description": "Интервал: каждые 15 000 км или 12 месяцев, что наступит раньше; строка\nс переносом и \\ чертой"}

    @classmethod
    def setUpClass(cls):
        cls.text = one("buildIcs", cls.EVENT)

    def test_crlf_and_75_octets(self):
        self.assertTrue(self.text.endswith("\r\n"))
        self.assertNotIn("\n", self.text.replace("\r\n", ""))
        self.assertNotIn("\r", self.text.replace("\r\n", ""))
        for line in self.text[:-2].split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75, line)
            self.assertFalse(line.startswith("  "), "a continuation never starts with the text's own space")

    def test_the_event(self):
        lines = unfold(self.text)
        self.assertEqual((lines[0], lines[1], lines[-1]), ("BEGIN:VCALENDAR", "VERSION:2.0", "END:VCALENDAR"))
        for want in ("PRODID:-//garage.team//Moya mashina//RU", "UID:knizhka-abc123-last-to@garage.team", "DTSTAMP:20260930T101507Z",
                     "DTSTART;VALUE=DATE:20261005", "DTEND;VALUE=DATE:20261006", "SUMMARY:ТО: Kia Rio",
                     "URL:https://garage.team/moya-mashina/", "TRANSP:TRANSPARENT"):
            self.assertIn(want, lines)
        self.assertEqual(lines.count("BEGIN:VEVENT"), 1)
        alarm = lines[lines.index("BEGIN:VALARM"):lines.index("END:VALARM") + 1]
        self.assertEqual(alarm, ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Завтра ТО: Kia Rio", "TRIGGER:-PT15H", "END:VALARM"])
        self.assertLess(lines.index("END:VALARM"), lines.index("END:VEVENT"))

    def test_text_is_escaped_and_reads_back(self):
        desc = next(line for line in unfold(self.text) if line.startswith("DESCRIPTION:Интервал"))[len("DESCRIPTION:"):]
        self.assertEqual(desc, "Интервал: каждые 15 000 км или 12 месяцев\\, что наступит раньше\\; строка\\nс переносом и \\\\ чертой")
        self.assertEqual(ics_unescape(desc), self.EVENT["description"])

    def test_folding_keeps_letters_and_escapes_whole(self):
        long = dict(self.EVENT, summary="ТО: " + "Ё" * 60 + " 🚗 " + "ж" * 40 + ", готово")
        text = one("buildIcs", long)
        for line in text[:-2].split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75)     # a lone half of the emoji would not even encode
            self.assertFalse(line.endswith("\\"), "an escape is never cut in two")
        self.assertIn("SUMMARY:" + long["summary"].replace(",", "\\,"), unfold(text))
        ascii_lines = one("icsFold", "A" * 200)
        self.assertEqual([len(x) for x in ascii_lines], [75, 75, 52])
        self.assertEqual("".join(x[1:] if i else x for i, x in enumerate(ascii_lines)), "A" * 200)
        cut = one("icsFold", "X" * 74 + "\\," + "Y")
        self.assertEqual(cut, ["X" * 74, " \\,Y"])
        # the break falls on a space of the text: the last letter goes down with it, so no line starts with two spaces
        self.assertEqual(one("icsFold", "X" * 75 + " Y"), ["X" * 74, " X Y"])
        words = one("icsFold", "DESCRIPTION:" + " ".join(["слово"] * 40))
        self.assertFalse(any(x.startswith("  ") for x in words))
        self.assertEqual("".join(x[1:] if i else x for i, x in enumerate(words)), "DESCRIPTION:" + " ".join(["слово"] * 40))


@unittest.skipUnless(NODE, "node is not installed")
class ImportTest(unittest.TestCase):
    def check(self, obj):
        return one("sanitizeBook", obj, KEYS)

    def test_a_good_copy(self):
        r = self.check(book())
        self.assertTrue(r["ok"])
        self.assertEqual((r["dropped"], len(r["book"]["entries"]), r["book"]["reminder"]), (0, 3, {"km": 15000, "months": 12}))
        self.assertEqual(r["book"]["car"]["brand"], "Kia")

    def test_not_a_copy_of_the_book(self):
        for bad in ([], "x", None, {"format": "other", "version": 1}, {"format": "garage-knizhka", "version": "1"},
                    {"format": "garage-knizhka", "version": 0}, {"format": "garage-knizhka", "version": 1, "entries": "x"}):
            self.assertEqual(self.check(bad), {"ok": False, "error": "format"}, bad)
        self.assertEqual(self.check({"format": "garage-knizhka", "version": 2}), {"ok": False, "error": "newer"})
        many = {"format": "garage-knizhka", "version": 1, "entries": [entry(f"e{i:04d}", "2026-01-01", i, ["oil"]) for i in range(2001)]}
        self.assertEqual(self.check(many), {"ok": False, "error": "big"})

    def test_broken_entries_are_dropped_and_the_rest_cleaned(self):
        b = book(entries=[
            entry("bad-date", "2026-02-30", 1000, ["oil"]),
            entry("nothing", "2026-03-01", 1000, []),
            entry("unknown", "2026-03-02", 1000, ["wax"]),
            entry("mixed", "2026-03-03", 1000, ["oil", "wax", "oil", "to"], text="  a\r\n\r\n\r\n b  ", note=" one\n two "),
            entry("mixed", "2026-03-04", -5, [], text="second with the same id"),
            entry("Bad ID!", "2026-03-05", 1.5, ["diag"]),
        ])
        r = self.check(b)
        self.assertEqual(r["dropped"], 3)
        es = r["book"]["entries"]
        self.assertEqual([e["date"] for e in es], ["2026-03-03", "2026-03-04", "2026-03-05"])
        self.assertEqual((es[0]["works"], es[0]["text"], es[0]["note"]), (["to", "oil"], "a\n\nb", "one two"))
        self.assertEqual(len({e["id"] for e in es}), 3, "ids are unique")
        self.assertEqual((es[1]["km"], es[2]["km"]), (None, None), "no negative or broken mileage")
        self.assertRegex(es[2]["id"], r"^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$")
        self.assertNotEqual(es[2]["id"], "Bad ID!")

    def test_the_car_and_the_interval_are_checked(self):
        b = book(reminder={"km": 50, "months": 0})
        b["car"] = {"brand": "  Kia   Rio  " + "x" * 60, "model": "Rio", "year": 1800, "engine": "1,6", "vin": "123", "km": -5, "kmDate": "2026-09-30"}
        r = self.check(b)["book"]
        self.assertEqual(len(r["car"]["brand"]), 40)
        self.assertTrue(r["car"]["brand"].startswith("Kia Rio x"))
        self.assertEqual((r["car"]["year"], r["car"]["vin"], r["car"]["km"], r["car"]["kmDate"]), (None, "", None, None))
        self.assertEqual(r["reminder"], {"km": None, "months": None})
        self.assertIsNone(self.check(dict(book(), car={}))["book"]["car"])
        self.assertIsNone(self.check(dict(book(), reminder={"km": "15000"}))["book"]["reminder"]["km"])

    def test_a_saved_book_reads_back_the_same(self):
        b = self.check(book())["book"]
        again = one("sanitizeBook", one("serial", b, 0), KEYS)["book"]
        self.assertEqual(again, b)

    def test_merge(self):
        cur = self.check(book(car_km=80000, reminder={"km": None, "months": None}, entries=[
            entry("a1", "2026-05-12", 70000, ["to"], text="старый текст", t=5),
            entry("b1", "2026-06-20", 74000, ["tires"], t=6)]))["book"]
        inc = self.check(book(car_km=84500, reminder={"km": 15000, "months": None}, entries=[
            entry("a1", "2026-05-12", 70000, ["to"], text="новый текст", t=9),       # the same entry, edited later
            entry("c1", "2026-06-20", 74000, ["tires"], t=7),                         # the same work, another device
            entry("d1", "2026-08-01", 80000, ["diag"], t=8)]))["book"]
        inc["car"]["vin"] = "XW8ZZZ61ZEG061733"
        m = one("mergeBooks", cur, inc)
        self.assertEqual((m["added"], m["updated"], m["skipped"]), (1, 1, 0))
        self.assertEqual([e["id"] for e in m["book"]["entries"]], ["a1", "b1", "d1"])
        self.assertEqual(m["book"]["entries"][0]["text"], "новый текст")
        self.assertEqual((m["book"]["car"]["vin"], m["book"]["car"]["km"]), ("XW8ZZZ61ZEG061733", 84500), "the same car: gaps filled")
        self.assertEqual(m["book"]["reminder"], {"km": 15000, "months": None})
        other = dict(inc, car=dict(inc["car"], brand="Lada", model="Vesta"))
        self.assertEqual(one("mergeBooks", cur, other)["book"]["car"]["brand"], "Kia", "another car does not replace the passport")


if __name__ == "__main__":
    unittest.main()
