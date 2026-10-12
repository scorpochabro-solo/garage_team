# -*- coding: utf-8 -*-
"""Tests for «Шинный калькулятор» (build/shiny.py): the maths against numbers counted by hand, rounding, markup.
Run: python3 -m unittest discover -s tests"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build import data as D  # noqa: E402
from build import shiny as S  # noqa: E402


class MathsTest(unittest.TestCase):
    def test_outer_diameter_by_hand(self):
        # rim inches × 25.4 + 2 × width × profile / 100, in hundredths of a millimetre
        self.assertEqual(S.outer(205, 55, 16), 63190)      # 406.4 + 2 × 112.75 = 631.9
        self.assertEqual(S.outer(215, 50, 17), 64680)      # 431.8 + 2 × 107.5 = 646.8
        self.assertEqual(S.outer(195, 65, 15), 63450)      # 381.0 + 2 × 126.75 = 634.5
        self.assertEqual(S.outer(175, 70, 13), 57520)      # 330.2 + 2 × 122.5 = 575.2
        self.assertEqual(S.outer(265, 70, 16), 77740)      # 406.4 + 2 × 185.5 = 777.4

    def test_default_pair(self):
        r = S.compare((205, 55, 16), (215, 50, 17))
        self.assertEqual((r["od_a"], r["od_b"], r["od_d"]), (6319, 6468, 149))
        self.assertEqual((S.dec(r["side_a"]), S.dec(r["side_b"]), S.signed_tenths(r["side_d"])), ("112,8", "107,5", "\u22125,3"))
        self.assertEqual(S.signed_tenths(r["clearance"]), "+7,5")          # half of 14.9 mm
        self.assertEqual(r["pct"], 2.4)                                    # 14.9 / 631.9 = 2.358 %
        self.assertEqual([v for _, v in r["speeds"]], [61.4, 92.1, 112.6])  # × 646.8 / 631.9
        self.assertEqual(S.verdict(r)[0], "ok")
        self.assertEqual(S.headline(r), "Колесо больше на 14,9\u00a0мм")

    def test_more_than_three_percent(self):
        bigger = S.compare((205, 55, 16), (215, 55, 17))                  # 668.3 mm: +36.4 mm, +5.76 %
        self.assertEqual((S.signed_tenths(bigger["od_d"]), bigger["pct"]), ("+36,4", 5.8))
        self.assertEqual([v for _, v in bigger["speeds"]], [63.5, 95.2, 116.3])
        self.assertEqual(S.verdict(bigger), ("over", S.TEXTS["over"], S.TEXTS["over-more"]))
        smaller = S.compare((205, 55, 16), (175, 65, 14))                 # 583.1 mm: -48.8 mm, -7.72 %
        self.assertEqual((S.signed_tenths(smaller["od_d"]), smaller["pct"]), ("\u221248,8", -7.7))
        self.assertEqual(S.verdict(smaller), ("over", S.TEXTS["over"], S.TEXTS["over-less"]))

    def test_limit_is_compared_as_shown(self):
        # the verdict follows the shown percent: 225/60 R15 is 651.0 mm, +19.1 mm = +3.02 %, shown «+3,0 %» — within 3 %
        r = S.compare((205, 55, 16), (225, 60, 15))
        self.assertEqual((S.signed_float(r["pct"]), S.verdict(r)[0]), ("+3,0", "ok"))
        # 205/60 R16 is 652.4 mm, +20.5 mm = +3.24 %
        self.assertEqual(S.verdict(S.compare((205, 55, 16), (205, 60, 16)))[0], "over")
        r = S.compare((195, 65, 15), (205, 55, 16))                       # -2.6 mm, -0.4 %
        self.assertEqual((S.signed_tenths(r["od_d"]), r["pct"], S.verdict(r)[0]), ("\u22122,6", -0.4, "ok"))

    def test_same_size(self):
        r = S.compare((205, 55, 16), (205, 55, 16))
        self.assertEqual((r["od_d"], r["pct"], S.verdict(r)[0], S.headline(r)), (0, 0.0, "same", S.TEXTS["head-same"]))
        self.assertEqual(S.cta_message((205, 55, 16), (205, 55, 16)), "Шиномонтаж: шины 205/55 R16.")

    def test_rounding_half_away_from_zero(self):
        self.assertEqual((S.tenths(11275), S.tenths(-525), S.tenths(745), S.tenths(0)), (1128, -53, 75, 0))   # 112.75 -> 112.8
        self.assertEqual((S.round1(2.25), S.round1(-2.25), S.round1(0.04)), (2.3, -2.3, 0.0))

    def test_shown_columns_add_up(self):
        # the difference is the difference of the shown values, for every pair of sizes
        for a in [(w, p, d) for w in S.WIDTHS[::4] for p in S.PROFILES[::3] for d in S.RIMS[::4]]:
            for b in [(205, 55, 16), (335, 25, 24), (135, 85, 12)]:
                r = S.compare(a, b)
                self.assertEqual(r["od_d"], r["od_b"] - r["od_a"])
                self.assertEqual(r["side_d"], r["side_b"] - r["side_a"])

    def test_cta_message(self):
        self.assertEqual(S.cta_message((205, 55, 16), (215, 50, 17)), "Шиномонтаж: хочу поставить 215/50 R17 вместо 205/55 R16.")


class MarkupTest(unittest.TestCase):
    def test_only_on_the_tyre_page(self):
        self.assertEqual(S.block(D.BY_PATH["/services/hranenie-sin.html"]), "")
        self.assertIn('id="shiny"', S.block(D.BY_PATH[S.PAGE]))

    def test_links_are_existing_pages(self):
        html = S.block(D.BY_PATH[S.PAGE])
        for href in re.findall(r'<a [^>]*href="([^"]+)"', html):
            self.assertIn(href, D.BY_PATH)

    def test_selects_and_defaults(self):
        html = S.block(D.BY_PATH[S.PAGE])
        self.assertEqual(html.count('<option value="'), 2 * (len(S.WIDTHS) + len(S.PROFILES) + len(S.RIMS)))
        self.assertEqual(len(S.WIDTHS), 21)                               # 135 … 335
        self.assertIn('data-o="odA">631,9<', html)
        self.assertIn('data-o="odB">646,8<', html)
        self.assertIn('data-o="v1">92,1<', html)

    def test_marking_parts_are_buttons(self):
        html = S.block(D.BY_PATH[S.PAGE])
        self.assertEqual(len(re.findall(r'<button class="shiny-mark__part', html)), 6)
        self.assertEqual(html.count('aria-pressed="true"'), 1)


if __name__ == "__main__":
    unittest.main()
