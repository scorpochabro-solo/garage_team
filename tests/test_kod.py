# -*- coding: utf-8 -*-
"""«Расшифровка кода ошибки» (build/kod.py, src/assets/js/kod.js): the code table as data, the structure rules of
SAE J2012, the markup, the link from «Что горит на панели?», and the parser/decoder of the script run in node
(skipped when node is not installed).  Run: python3 -m unittest discover -s tests"""
import html
import itertools
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import kod as K  # noqa: E402
from build import pribory as P  # noqa: E402

NODE = shutil.which("node")
SCRIPT = ROOT / "tests" / "kod_decode.cjs"
PAGE_SVC = D.BY_PATH[K.PAGE]
ROWS = [r for _, _, rows in K.GROUPS for r in rows]


def all_texts():
    """Every phrase a visitor can read in the block: the table and the structure texts."""
    out = [t for r in ROWS for t in r[1:3]]
    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from walk(v)
        elif isinstance(x, str):
            yield x
    out += list(walk(K.TEXTS))
    out += [K.TAG, K.TITLE, K.INTRO, K.INTRO_JS, *K.SCREEN, K.FIELD, K.HINT, K.GO, K.EXAMPLES_LABEL, K.CTA,
            K.CHECK_LABEL, K.LAMP_LINK, K.REF_TITLE, K.REF_INTRO, K.REF_INTRO_JS, K.URGE]
    out += [t for pair in K.LEGEND for t in pair] + [title for _, title, _ in K.GROUPS]
    return out


class TableTest(unittest.TestCase):
    def test_70_to_100_unique_well_formed_generic_codes(self):
        codes = [r[0] for r in ROWS]
        self.assertTrue(70 <= len(codes) <= 100, len(codes))
        self.assertEqual(len(codes), len(set(codes)), "a code is listed twice")
        for c in codes:
            self.assertRegex(c, r"^[PBCU][0-3][0-9A-F]{3}$")
            self.assertEqual(K.kind(c), "generic", f"{c}: only generic SAE codes belong in the table")
        self.assertEqual(set(K.CODES), set(codes))

    def test_decimal_numbering_of_the_families(self):
        # oxygen sensors run P0130–P0141 and P0150–P0161 (P0139 is followed by P0140, not P013A); knock P0325–P0333
        for n in list(range(130, 142)) + list(range(150, 162)) + [325, 326, 327, 328, 330, 331, 332, 333] + list(range(300, 309)):
            self.assertIn(f"P0{n}", K.CODES)
        self.assertFalse([c for c in K.CODES if re.match(r"^P01[3-6][A-F]$", c)])
        self.assertIn("банк 1, датчик 2 — после катализатора", K.CODES["P0137"]["name"])
        self.assertIn("банк 2, датчик 1 — до катализатора", K.CODES["P0151"]["name"])
        self.assertIn("подогрева", K.CODES["P0141"]["name"])
        self.assertIn("подогрева", K.CODES["P0161"]["name"])

    def test_a_number_never_starts_a_line_alone(self):
        for code, name, *_ in ROWS:
            self.assertNotRegex(name, r"\b(банк|датчик|цилиндре|детонации) \d", code)
        self.assertIn("(банк 1)", K.CODES["P0171"]["name"])
        self.assertIn("датчика детонации 2 (банк 2)", K.CODES["P0330"]["name"])

    def test_texts_are_filled_without_a_final_period(self):
        for code, name, what, _, urge in ROWS:
            self.assertTrue(name.strip() and what.strip(), code)
            self.assertNotIn(name[-1], ".;", code)
            self.assertNotIn(what[-1], ".;", code)
            self.assertIsInstance(urge, bool)

    def test_links_are_existing_allowed_pages(self):
        for key, path in K.PAGES.items():
            self.assertIn(path, D.BY_PATH, key)
            self.assertFalse(any(bad in path for bad in K.FORBIDDEN), path)
            self.assertNotEqual(path, K.PAGE, "no link to the page itself")
        for code, _, _, page, _ in ROWS:
            self.assertTrue(page is None or page in K.PAGES, code)
        self.assertEqual(set(K.FORBIDDEN) >= {"udalenie", "cip-tuning", "ksenon", "tehosmotr"}, True)

    def test_a_forbidden_or_missing_page_is_a_build_error(self):
        with mock.patch.dict(K.PAGES, {"bad": "/services/cip-tuning/udalenie-i-pereprogrammirovanie-sazevyh-filtrov.html"}):
            with self.assertRaises(ValueError):
                K._page("bad")
        with mock.patch.dict(K.PAGES, {"bad": "/services/remont-vyhlopnoj-sistemy/udalenie-katalizatora.html"}):
            with self.assertRaises(ValueError):
                K._page("bad")
        with mock.patch.dict(K.PAGES, {"bad": "/services/net-takoj-stranicy.html"}):
            with self.assertRaises(ValueError):
                K._page("bad")
        with mock.patch.dict(K.PAGES, {"bad": K.PAGE}):
            with self.assertRaises(ValueError):
                K._page("bad")

    def test_a_broken_table_fails_the_build(self):
        group = K.GROUPS[0][2]
        for bad in [("P0101", "дубль", "что-то", "inj", False), ("p0999", "строчная", "что-то", "inj", False),
                    ("P1234", "код производителя", "что-то", "inj", False), ("P0999", "точка в конце.", "что-то", "inj", False)]:
            with self.subTest(bad=bad[0]), mock.patch.object(K, "GROUPS", [(K.GROUPS[0][0], K.GROUPS[0][1], group + [bad])] + K.GROUPS[1:]):
                with self.assertRaises(ValueError):
                    K.check()
        K.check()

    def test_no_prices_no_removal_advice_no_safety_verdicts(self):
        # word starts: «трубку» is not «руб»
        banned = re.compile(r"₽|\b(?:руб|удал|отключ|прошив|прошит|заглуш|обманк|эмулятор|нельзя|опасн|гарант|бесплатн|скидк)",
                            re.I)
        for text in all_texts():
            self.assertIsNone(banned.search(str(text)), text)

    def test_catalyst_and_oxygen_codes_lead_to_repair_not_to_removal(self):
        for code in ["P0420", "P0422", "P0430", "P0133", "P0401", "P0402"]:
            e = K.entry(code)
            self.assertTrue(e["href"])
            self.assertNotRegex(e["href"], r"udalenie|otklucenie|cip-tuning")


class StructureTest(unittest.TestCase):
    def test_kind_by_the_second_character(self):
        cases = {"P0301": "generic", "P2A00": "generic", "P1128": "maker", "P3000": "maker", "P33FF": "maker",
                 "P3400": "generic", "P3FFF": "generic", "B0001": "generic", "B1234": "maker", "B2345": "maker",
                 "B3000": "reserved", "C0035": "generic", "C1234": "maker", "C3000": "reserved", "U0100": "generic",
                 "U1000": "maker", "U2000": "maker", "U3000": "reserved"}
        for code, k in cases.items():
            self.assertEqual(K.kind(code), k, code)

    def test_example_p0301(self):
        x = K.explain("P0301")
        self.assertEqual([p[:2] for p in x["parts"]], [["sys", "P"], ["type", "0"], ["sub", "3"], ["num", "01"]])
        self.assertEqual(x["parts"][2][2], "зажигание и пропуски воспламенения")
        self.assertEqual(x["entry"]["name"], "Пропуски воспламенения в цилиндре 1")
        self.assertTrue(x["entry"]["urge"])
        self.assertEqual(x["entry"]["label"], "Замена свечей зажигания")
        self.assertEqual(x["note"], K.NOTE["known"])

    def test_groups_of_systems_only_where_the_standard_fixes_them(self):
        self.assertEqual(K.explain("P1301")["parts"][2], ["sub", "3", "обычно зажигание и пропуски воспламенения"])
        self.assertEqual(K.explain("P0A80")["parts"][2][2], "гибридная силовая установка")
        self.assertEqual(K.explain("P2A00")["parts"][2][2], "подача топлива и воздуха")
        self.assertEqual(K.explain("U0100")["parts"][2][:2], ["sub", "1"])
        for code, num in [("P0D12", "D12"), ("P1A00", "A00"), ("P3000", "000"), ("P3400", "400"), ("B1234", "234"),
                          ("C0035", "035"), ("U1000", "000"), ("U3000", "000")]:
            parts = K.explain(code)["parts"]
            self.assertEqual([p[0] for p in parts], ["sys", "type", "num"], code)
            self.assertEqual(parts[-1][1], num, code)

    def test_notes_by_kind(self):
        self.assertEqual(K.explain("P1128")["note"], K.NOTE["maker"])
        self.assertEqual(K.explain("P0001")["note"], K.NOTE["unknown"])
        self.assertEqual(K.explain("B3000")["note"], K.NOTE["reserved"])
        self.assertEqual(K.explain("P3000")["parts"][1][2], K.TYPE["p3-maker"])
        self.assertEqual(K.explain("P3400")["parts"][1][2], K.TYPE["p3-generic"])
        self.assertIn("точную расшифровку для вашей машины даст компьютерная диагностика", K.NOTE["unknown"].lower())

    def test_call_back_message(self):
        self.assertEqual(K.cta_message([]), "Хочу записаться на компьютерную диагностику.")
        self.assertEqual(K.cta_message(["P0301", "P0171"]),
                         "Хочу записаться на компьютерную диагностику. Коды ошибок: P0301, P0171.")


class MarkupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = K.block(PAGE_SVC)
        cls.text = html.unescape(cls.html)

    def test_only_on_the_diagnostics_page(self):
        self.assertEqual(K.block(D.BY_PATH["/services/sinomontaz.html"]), "")
        self.assertIn('id="kod"', self.html)
        self.assertNotRegex(self.html, r"<h1[\s>]")
        self.assertEqual(len(re.findall(r"<h2[\s>]", self.html)), 1)

    def test_the_whole_table_is_in_the_html(self):
        for code, name, what, page, urge in ROWS:
            self.assertIn(f'id="kod-{code.lower()}" data-code="{code}"', self.html)
            self.assertIn(name, self.text)
            self.assertIn(what, self.text)
        self.assertEqual(self.html.count('data-code="'), len(ROWS))
        self.assertEqual(self.html.count('data-f="urge"'), sum(1 for r in ROWS if r[4]))

    def test_links_in_the_block(self):
        hrefs = re.findall(r'<a [^>]*href="([^"]+)"', self.html)
        self.assertEqual(len([h for h in hrefs]), sum(1 for r in ROWS if r[3]) + 1)   # + the example card
        for href in hrefs:
            self.assertIn(href, D.BY_PATH)
            self.assertFalse(any(bad in href for bad in K.FORBIDDEN), href)

    def test_texts_json_is_the_texts(self):
        raw = re.search(r"<script type=\"application/json\" data-kod-texts>(.*?)</script>", self.html, re.S).group(1)
        self.assertEqual(json.loads(raw), json.loads(json.dumps(K.TEXTS, ensure_ascii=False)))
        self.assertNotIn("</", raw)

    def test_example_and_controls(self):
        self.assertIn('class="kod-card__tag">Пример<', self.html)
        self.assertIn('aria-label="Код P0301"', self.html)
        self.assertIn('<label class="kod-form__label" for="kod-input">', self.html)
        self.assertIn('aria-live="polite" data-kod-live', self.html)
        self.assertEqual(re.findall(r'data-kod-example="([^"]+)"', self.html), K.EXAMPLES)
        preset = re.search(r'data-preset="([^"]+)" data-kod-cta', self.html).group(1)
        self.assertEqual(json.loads(html.unescape(preset)), {"message": "Хочу записаться на компьютерную диагностику."})
        self.assertEqual(self.html.count("<details"), len(K.GROUPS))


class PriboryLinkTest(unittest.TestCase):
    def test_check_engine_card_leads_to_the_decoder(self):
        section = P.pribory_section()
        link = f'href="{K.PAGE}#{K.ANCHOR}"'
        self.assertEqual(section.count(link), 1)
        card = re.search(r'<article class="lamp-card" id="pribory-engine".*?</article>', section, re.S).group(0)
        self.assertIn(link, card)
        self.assertIn("Есть код ошибки? Расшифруйте", card)


def run_js(job):
    job = {"model": K.model(), **job}
    out = subprocess.run([NODE, str(SCRIPT)], input=json.dumps(job, ensure_ascii=False), capture_output=True,
                         text=True, check=True, env={"PATH": ""})
    return json.loads(out.stdout)


@unittest.skipUnless(NODE, "node is not installed")
class ScriptTest(unittest.TestCase):
    PARSE = {
        # input: (codes, [(error key, token, pending)])
        "P0301": (["P0301"], []),
        "p0301": (["P0301"], []),
        "P0 301": (["P0301"], []),
        "P 0 3 0 1": (["P0301"], []),
        "P0-301": (["P0301"], []),
        "Р0301": (["P0301"], []),                 # Cyrillic Р
        "р0301": (["P0301"], []),
        "PO301": (["P0301"], []),                 # letter O for the zero
        "З0301": (["P0301"], []),                 # the Russian key under P
        "Г0100": (["U0100"], []),                 # … under U
        "ｐ０３０１": (["P0301"], []),              # full-width characters
        "P0301.": (["P0301"], []),
        "P0301, P0171; p0420\nU0100": (["P0301", "P0171", "P0420", "U0100"], []),
        "P0301-P0171": (["P0301", "P0171"], []),
        "P0301P0171": (["P0301", "P0171"], []),
        "P0301 P0301 p0301": (["P0301"], []),
        "код ошибки P0420": (["P0420"], []),
        "у меня P0301 и P0171": (["P0301", "P0171"], []),
        "p0a80 p2a00": (["P0A80", "P2A00"], []),
        "": ([], []),
        "привет": ([], []),
        "P4301": ([], [("second", "P4301", False)]),
        "P 4301": ([], [("second", "P 4301", False)]),
        "0301": ([], [("noletter", "0301", True)]),   # still typing
        "0301,": ([], [("noletter", "0301", False)]),
        "P030": ([], [("length", "P030", True)]),
        "P030 ": ([], [("length", "P030", False)]),
        "P03011": ([], [("length", "P03011", False)]),
        "P03G1": ([], [("chars", "P03G1", False)]),
        "A0301": ([], [("letter", "A0301", False)]),
        "Ж0301": ([], [("letter", "Ж0301", False)]),
        "12345": ([], [("other", "12345", False)]),
        "B1S1": ([], [("other", "B1S1", True)]),
        "P4301 P4301": ([], [("second", "P4301", False)]),            # one message for a repeated mistake
        # beside real codes a bare number is a year, a mileage or a scanner's «B1S1», not a mistyped code;
        # a lone «и» is a word, not the letter B
        "P0301 и 0171": (["P0301"], []),
        "Solaris 2015, пробег 120000, P0420": (["P0420"], []),
        "P0133 O2 Sensor Circuit Slow Response (B1S1)": (["P0133"], []),
        "P0301, P03G1": (["P0301"], [("chars", "P03G1", False)]),    # a code-shaped mistake is still shown
    }

    def test_parse(self):
        inputs = list(self.PARSE)
        res = run_js({"parse": inputs})["parse"]
        for raw, got in zip(inputs, res):
            codes, errors = self.PARSE[raw]
            with self.subTest(raw=raw):
                self.assertEqual(got["codes"], codes)
                self.assertEqual([(e["key"], e["token"], e["pending"]) for e in got["errors"]], errors)
                self.assertFalse(got["more"])

    def test_at_most_ten_codes(self):
        many = " ".join(f"P03{n:02d}" for n in range(1, 13))
        got = run_js({"parse": [many]})["parse"][0]
        self.assertEqual(len(got["codes"]), 10)
        self.assertTrue(got["more"])

    def test_explain_is_the_same_in_python_and_javascript(self):
        codes = list(K.CODES)
        codes += ["".join(p) for p in itertools.product("PBCU", "0123", "0123456789ABCDEF", ["00", "7F"])]
        res = run_js({"explain": codes})["explain"]
        for code, got in zip(codes, res):
            self.assertEqual(got, json.loads(json.dumps(K.explain(code), ensure_ascii=False)), code)

    def test_messages_and_error_texts(self):
        res = run_js({"message": [[], ["P0301", "P0171"]],
                      "errors": [{"key": "noletter", "token": "0301", "fix": "P0301"}, {"key": "second", "token": "P4301"},
                                 {"key": "empty"}]})
        self.assertEqual(res["message"], [K.cta_message([]), K.cta_message(["P0301", "P0171"])])
        self.assertEqual(res["errors"], ["«0301»: в начале кода нужна буква — P, B, C или U, например P0301.",
                                         "«P4301»: второй знак кода — только 0, 1, 2 или 3.",
                                         "Введите код ошибки — например, P0301."])


if __name__ == "__main__":
    unittest.main()
