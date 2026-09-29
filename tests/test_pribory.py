# -*- coding: utf-8 -*-
"""Tests for the warning-light section of the home page (build/pribory.py).  Run: python3 -m unittest discover -s tests"""
import html
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import data as D  # noqa: E402
from build import pribory as P  # noqa: E402


class PriboryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = P.pribory_section()

    def test_every_lamp_has_its_symbol_tone_and_texts(self):
        self.assertTrue(12 <= len(P.LAMPS) <= 16)
        for lamp in P.LAMPS:
            self.assertIn(lamp["key"], P.SYMBOLS)
            self.assertIn(lamp["tone"], P.TONES)
            for field in ("name", "short", "look", "means", "todo"):
                self.assertTrue(lamp[field].strip(), f"{lamp['key']}: пустое поле {field}")

    def test_links_go_to_existing_pages_and_never_to_removal_pages(self):
        for lamp in P.LAMPS:
            self.assertTrue(1 <= len(lamp["links"]) <= 3, lamp["key"])
            for path in lamp["links"]:
                self.assertIn(path, D.BY_PATH)
                self.assertNotRegex(path, r"udalenie|otklucenie|cip-tuning")

    def test_a_removal_page_is_a_build_error(self):
        with self.assertRaises(ValueError):
            P._links(["/services/cip-tuning/udalenie-i-pereprogrammirovanie-sazevyh-filtrov.html"])

    def test_all_explanations_are_in_the_html_for_search_and_no_js(self):
        text = html.unescape(self.html)
        for lamp in P.LAMPS:
            self.assertIn(f'id="pribory-{lamp["key"]}"', self.html)
            self.assertIn(lamp["means"], text)
            self.assertIn(lamp["todo"], text)

    def test_lamps_are_labelled_toggle_buttons(self):
        buttons = re.findall(r"<button class=\"lamp\"[^>]*>", self.html)
        self.assertEqual(len(buttons), len(P.LAMPS))
        for b in buttons:
            self.assertIn('type="button"', b)
            self.assertIn('aria-pressed="false"', b)
            self.assertRegex(b, r'aria-label="[А-ЯЁA-Z][^"]+, (красный|жёлтый|синий)"')

    def test_call_back_message_names_the_lamp(self):
        oil = html.unescape(self.html)
        self.assertIn('"message": "Горит индикатор «Давление масла». Хочу записаться на диагностику."', oil)


if __name__ == "__main__":
    unittest.main()
