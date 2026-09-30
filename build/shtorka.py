# -*- coding: utf-8 -*-
"""«Рольворота между страницами» (shtorka): a steel roller shutter between pages.

Cross-document view transitions (src/assets/css/shtorka.css): leaving a page, the shutter rolls down over the content
area under the header; the next page is revealed as it rolls back up. The top line, the header and the phone call bar
keep their place (each has its own view-transition-name), so only the content between them is shuttered.

Two hooks in the page shell (layout.document()):
- head(): what has to be ready before the new page's first frame, which is when its state is captured.
  The inline script (src/assets/js/shtorka.js) listens for `pagereveal`; in the deferred site.js it would come too
  late on long pages. `<link rel=expect>` holds that first frame until the shutter element is parsed, so the header
  and the shutter are in the DOM when the script measures them (they come in the first ~30 KB of every page).
- markup(): the shutter itself, right after the header. display: none except while an incoming «shtorka» transition
  is captured and running; its live snapshot is what rolls down and up.
"""
import re
from functools import lru_cache
from pathlib import Path

ELEMENT_ID = "shtorka"
JS_PATH = Path(__file__).resolve().parent.parent / "src" / "assets" / "js" / "shtorka.js"

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_LINE_COMMENT = re.compile(r"^\s*//.*$", re.M)


@lru_cache(maxsize=None)
def inline_js() -> str:
    """shtorka.js without comments and indentation: it is repeated in every page's <head>.
    The source keeps comments only as /* … */ blocks and whole // lines, so no string or regex is touched."""
    src = _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", JS_PATH.read_text(encoding="utf-8")))
    code = "\n".join(line.strip() for line in src.splitlines() if line.strip())
    if "</script" in code.lower() or "<!--" in code:
        raise ValueError("shtorka.js: не может быть встроен в <script> как есть")
    return code


def head() -> str:
    return (f'<link rel="expect" href="#{ELEMENT_ID}" blocking="render">\n'
            f"<script>{inline_js()}</script>")


def markup() -> str:
    return f'<div class="shtorka" id="{ELEMENT_ID}" aria-hidden="true"><i class="shtorka__bar"></i></div>'
