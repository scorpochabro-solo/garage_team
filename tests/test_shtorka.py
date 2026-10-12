# -*- coding: utf-8 -*-
"""«Рольворота между страницами» (build/shtorka.py, src/assets/css/shtorka.css, src/assets/js/shtorka.js): the
view-transition opt-in and its reduced-motion guard, compositor-only keyframes, the shell hooks, the inline head script.
The motion itself is checked in real browsers (Playwright, see notes/fishka-shtorka.md).
Run: python3 -m unittest discover -s tests"""
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
from build import layout as L  # noqa: E402
from build import shtorka as S  # noqa: E402
from build.css_tools import _items, guard_hover  # noqa: E402

NODE = shutil.which("node")
CSS = (ROOT / "src" / "assets" / "css" / "shtorka.css").read_text(encoding="utf-8")
BUILD_PY = (ROOT / "build.py").read_text(encoding="utf-8")


def blocks(css, conditions=()):
    """(conditions, prelude, body) of every block, depth first: conditions are the enclosing at-rule preludes."""
    for item in _items(css):
        if item[0] != "block":
            continue
        _, prelude, body = item
        yield conditions, prelude, body
        if prelude.startswith("@") and prelude.split(None, 1)[0].lower() in ("@media", "@supports"):
            yield from blocks(body, conditions + (prelude,))


def declarations(body):
    return [(p.strip(), v.strip()) for p, _, v in (d.partition(":") for d in body.split(";")) if p.strip()]


def order(name):
    return re.search(name + r"\s*=\s*\[([^\]]*)\]", BUILD_PY).group(1)


class OptInTest(unittest.TestCase):
    def opt_ins(self, css):
        return [(cond, body) for cond, prelude, body in blocks(css) if prelude.lower() == "@view-transition"]

    def test_the_css_opts_in_to_cross_document_view_transitions(self):
        rules = self.opt_ins(CSS)
        self.assertEqual(len(rules), 1)
        self.assertIn(("navigation", "auto"), declarations(rules[0][1]))

    def test_reduced_motion_disables_it(self):
        # the only opt-in lives under «no-preference»: with reduced motion there is no transition at all
        for cond, _ in self.opt_ins(CSS):
            self.assertTrue(any("prefers-reduced-motion: no-preference" in c for c in cond), cond)
            self.assertFalse(any("prefers-reduced-motion: reduce" in c for c in cond), cond)
        # and nothing else in the bundle opts in
        bundle = "\n".join((ROOT / "src" / "assets" / "css" / n.strip().strip('"')).read_text(encoding="utf-8")
                           for n in order("CSS_ORDER").split(","))
        self.assertEqual(len(self.opt_ins(bundle)), 1)

    def test_without_javascript_there_is_no_opt_in(self):
        (cond, _), = self.opt_ins(CSS)
        self.assertTrue(any("scripting: enabled" in c for c in cond), cond)

    def test_the_build_keeps_the_opt_in(self):
        # the bundle goes through guard_hover(); the at-rule must come out whole, still under its media query
        self.assertEqual(self.opt_ins(guard_hover(CSS)), self.opt_ins(CSS))

    def test_stylesheet_is_in_the_bundle_and_the_head_script_is_not_in_site_js(self):
        self.assertIn('"shtorka.css"', order("CSS_ORDER"))
        self.assertNotIn("shtorka.js", order("JS_ORDER"))   # inlined in <head>; in site.js it would run twice


class AnimationTest(unittest.TestCase):
    def test_keyframes_animate_only_compositor_properties(self):
        frames = [(p, b) for _, p, b in blocks(CSS) if p.startswith("@keyframes")]
        self.assertGreaterEqual(len(frames), 5)
        for prelude, body in frames:
            for _, _, step in blocks(body):
                for prop, _ in declarations(step):
                    self.assertIn(prop, ("transform", "opacity", "animation-timing-function"), prelude)

    def test_the_whole_transition_is_at_most_650_ms(self):
        (value,) = re.findall(r"--shtorka-t:\s*(\d+)ms", CSS)
        self.assertLessEqual(int(value), 650)

    def test_root_custom_properties_do_not_change_with_the_transition(self):
        # an inherited value set on :root only while the transition runs restyles every element of the page twice
        root_only = re.compile(r"(:root|html)(:[\w-]+(\([^)]*\))?)+")
        checked = 0
        for _, prelude, body in blocks(CSS):
            for selector in prelude.split(","):
                subject = selector.split("::")[0].strip()
                if "active-view-transition" in subject and root_only.fullmatch(subject):
                    checked += 1
                    self.assertFalse([p for p, _ in declarations(body) if p.startswith("--")], selector)
        self.assertGreater(checked, 0)


class ShellTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = L.document("Заголовок", "Описание", "/x.html", "<p>страница</p>")

    def test_every_named_element_is_unique_in_the_shell(self):
        # a view-transition-name used twice makes the browser abort every transition, silently
        names = dict(re.findall(r"\.([\w-]+)\s*\{\s*view-transition-name:\s*([\w-]+)", CSS))
        self.assertEqual(set(names.values()), {"site-topline", "site-header", "site-callbar"})
        for cls in names:
            self.assertEqual(len(re.findall(rf'class="{cls}[" ]', self.html)), 1, cls)

    def test_one_hidden_shutter_between_the_header_and_the_content(self):
        self.assertEqual(self.html.count('id="shtorka"'), 1)
        self.assertIn('<div class="shtorka" id="shtorka" aria-hidden="true">', self.html)
        self.assertLess(self.html.index('<header class="site-header"'), self.html.index('id="shtorka"'))
        self.assertLess(self.html.index('id="shtorka"'), self.html.index('<main id="main">'))

    def test_head_holds_the_first_frame_for_the_shutter_and_runs_the_script_before_the_stylesheet(self):
        head = self.html[:self.html.index("</head>")]
        self.assertIn('<link rel="expect" href="#shtorka" blocking="render">', head)
        # a script after a stylesheet waits for it: the inline one must come first, it touches no styles
        self.assertLess(head.index("<script>"), head.index('rel="stylesheet"'))
        self.assertIn(S.inline_js(), head)

    def test_rebasing_for_a_sub_path_leaves_the_head_script_alone(self):
        try:
            D.set_base("/v/shtorka")
            self.assertEqual(D.rebase(S.head()), S.head())
            self.assertIn('href="/v/shtorka/assets/css/site.css', D.rebase(self.html))
        finally:
            D.set_base("")

    def test_inline_script_has_no_comments(self):
        js = S.inline_js()
        self.assertNotIn("/*", js)
        self.assertFalse([ln for ln in js.splitlines() if ln.lstrip().startswith("//")])
        self.assertIn("pagereveal", js)
        self.assertIn("pageswap", js)

    @unittest.skipUnless(NODE, "node is not installed")
    def test_inline_script_is_valid_javascript(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shtorka-inline.js"
            path.write_text(S.inline_js(), encoding="utf-8")
            run = subprocess.run([NODE, "--check", str(path)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
