# -*- coding: utf-8 -*-
"""Tests for build/pashalki.py (easter eggs on the homepage).  Run: python3 -m unittest discover -s tests"""
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import pashalki as P  # noqa: E402


class V8GaugeTest(unittest.TestCase):
    def test_css_keyframes_match_the_formula(self):
        # the keyframes are pasted into the stylesheet; after changing the geometry run `python3 -m build.pashalki` again
        css = (ROOT / "src" / "assets" / "css" / "pashalki.css").read_text(encoding="utf-8")
        self.assertIn(P.v8_keyframes(), css)

    def test_piston_stroke_is_twice_the_throw(self):
        s = []
        for k in range(360):
            piston, _ = P._v8_parts(k)[0][0]
            s.append(-float(piston[len("translateY("):-len("px)")]))
        self.assertTrue(math.isclose(max(s) - min(s), 2 * P.V8_R, abs_tol=0.02))

    def test_button_starts_hidden_and_has_a_russian_name(self):
        html = P.v8_gauge()
        self.assertIn('aria-label="Наверх страницы"', html)
        self.assertIn(" hidden>", html)   # shown by the script on desktops only


class WallTest(unittest.TestCase):
    def test_every_niche_object_is_named(self):
        html = P.wall()
        self.assertEqual(html.count('class="niche__item'), len(P.NICHE_ITEMS))
        names = [n for n, _ in P.NICHE_ITEMS]
        self.assertIn('data-names="' + "|".join(names) + '"', html)

    def test_decorations_are_hidden_from_screen_readers(self):
        html = P.wall()
        for cls in ("wall__bg", "xray", "lamp", "niche__hole"):
            self.assertRegex(html, rf'class="{cls}"[^>]*aria-hidden="true"')


if __name__ == "__main__":
    unittest.main()
