# -*- coding: utf-8 -*-
"""Tests for the phone auto-link on service pages (build/services.py).  Run: python3 -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build.services import _link_phones  # noqa: E402

LINK = '<a class="tel" href="tel:+78314161677">'


class LinkPhonesTest(unittest.TestCase):
    def test_plain_number_in_text_becomes_a_call_link(self):
        self.assertEqual(_link_phones("<p>Звоните (831) 416-16-77 сейчас.</p>"),
                         f"<p>Звоните {LINK}(831) 416-16-77</a> сейчас.</p>")

    def test_number_with_country_code(self):
        self.assertIn(f"{LINK}+7 (831) 416-16-77</a>", _link_phones("<li>Тел. +7 (831) 416-16-77</li>"))

    def test_existing_link_is_left_alone(self):
        html = '<p><a href="tel:+78314161677">(831) 416-16-77</a> и <a href="/x"><b>(831) 416-16-77</b></a></p>'
        self.assertEqual(_link_phones(html), html)

    def test_attributes_are_not_touched(self):
        html = '<button data-preset=\'{"message":"(831) 416-16-77"}\' aria-label="(831) 416-16-77">Позвонить</button>'
        self.assertEqual(_link_phones(html), html)

    def test_text_after_a_closed_link_is_linked(self):
        out = _link_phones('<p><a href="/a">текст</a>, тел. (831) 416-16-77</p>')
        self.assertIn(f"{LINK}(831) 416-16-77</a>", out)

    def test_other_numbers_are_not_links(self):
        html = "<p>от 1 500 ₽, 603155, 416-16-78</p>"
        self.assertEqual(_link_phones(html), html)


if __name__ == "__main__":
    unittest.main()
