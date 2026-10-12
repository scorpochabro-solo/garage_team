# -*- coding: utf-8 -*-
"""Tests for build/css_tools.py.  Run: python3 -m unittest discover -s tests"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build.css_tools import guard_hover, split_selectors  # noqa: E402


def squash(css: str) -> str:
    """Whitespace-insensitive form: the transform may reflow spaces around braces, which CSS ignores."""
    return " ".join(re.sub(r"\s*([{}])\s*", r" \1 ", css).split())


class GuardHoverTest(unittest.TestCase):
    def test_hover_rule_moves_into_hover_media(self):
        out = squash(guard_hover(".btn:hover { color: red; }"))
        self.assertEqual(out, "@media (hover: hover) { .btn:hover { color: red; } }")

    def test_mixed_selector_list_is_split_and_keeps_its_order(self):
        out = squash(guard_hover(".a { x: 1; }\n.nav:hover, .nav.is-active { color: #fff; }\n.b { y: 2; }"))
        self.assertEqual(out, ".a { x: 1; } .nav.is-active { color: #fff; } "
                              "@media (hover: hover) { .nav:hover { color: #fff; } } .b { y: 2; }")

    def test_rule_inside_media_gets_nested_hover_media(self):
        out = squash(guard_hover("@media (max-width: 640px) { .x:hover { a: b; } .y { c: d; } }"))
        self.assertEqual(out, "@media (max-width: 640px) { @media (hover: hover) { .x:hover { a: b; } } .y { c: d; } }")

    def test_rules_already_inside_hover_media_are_untouched(self):
        css = "@media (hover: hover) { .h:hover .l { opacity: 1; } }"
        self.assertEqual(squash(guard_hover(css)), squash(css))

    def test_negated_hover_stays_for_touch(self):
        css = ".item:not(.is-active):not(:hover) { opacity: .5; }"
        self.assertEqual(squash(guard_hover(css)), squash(css))

    def test_keyframes_font_face_and_statements_are_untouched(self):
        css = ('@charset "utf-8";\n@font-face{font-family:X;src:url(\'a.woff2\')}\n'
               "@keyframes k { from { opacity: 0; } to { opacity: 1; } }")
        self.assertEqual(squash(guard_hover(css)), squash(css))

    def test_strings_and_comments_with_braces_and_commas(self):
        css = '/* a { b } */ .q:hover::after { content: "a{b},c:hover"; background: url("data:x;utf8,<svg/>"); }'
        raw = guard_hover(css)
        self.assertTrue(squash(raw).startswith("/* a { b } */ @media (hover: hover) { .q:hover::after {"))
        self.assertIn('content: "a{b},c:hover";', raw)          # the string itself is not touched
        self.assertIn('url("data:x;utf8,<svg/>")', raw)

    def test_commas_inside_functional_pseudo_classes_do_not_split(self):
        self.assertEqual(split_selectors(".a:is(.b, .c):hover, .d"), [".a:is(.b, .c):hover", ".d"])

    def test_idempotent(self):
        css = ".a:hover, .a:focus-visible { x: 1; } @media (max-width: 9px) { .b:hover { y: 2; } }"
        once = guard_hover(css)
        self.assertEqual(squash(guard_hover(once)), squash(once))

    def test_broken_css_fails_loudly(self):
        with self.assertRaises(ValueError):
            guard_hover(".a { color: red;")


if __name__ == "__main__":
    unittest.main()
