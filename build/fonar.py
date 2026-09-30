# -*- coding: utf-8 -*-
"""«Фонарь по кирпичу»: the dark sections of the site are an old red-brick wall at night. The wall shows only where
the visitor's hand lamp (the mouse) passes: running bond, white-grey mortar, the brick of the building on Красная слобода.

    tile_svg()  one panel of the wall as SVG: 6 bricks × 8 courses, head joints wandering a little, bricks of several
                tones (a seeded random, so every build draws the same wall). Colours come from the tokens in arki.css
                (--brick-rgb, --brick-deep-rgb) as seen under the lamp (--arch-lamp-rgb)
    css()       the generated part of the stylesheet: the wall's rule with the tile inline (an SVG data URI) and its
                size; build.py puts it in front of the static CSS, like the @font-face rules. No image files
    mark()      the hook: data-fonar on a <section> makes it a zone of the wall (build/home.py, build/layout.py,
                build/static_pages.py); `after` names an element inside the section that is not wall (the «Ворота» photo
                scene in #contacts): the lamp lights the wall only below it

The layers, the light and its motion are in src/assets/js/fonar.js (created only with a mouse), styles in fonar.css.
"""
from __future__ import annotations

import random
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from . import data as D

ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "src" / "assets" / "css" / "arki.css"   # --brick-rgb, --brick-deep-rgb, --arch-lamp-rgb

ATTR = "data-fonar"

# ---------- the tile: a course is one row of bricks with the bed joint above it ----------
COURSE = 20          # px
MODULE = 68          # px, a brick and its head joint: a 250 × 65 mm brick with 10–12 mm joints is 3.4 : 1
JOINT = 3            # px, bed and head joints (old lime mortar, wide)
PER_COURSE = 6       # bricks per course in one tile
COURSES = 8          # courses in one tile: even, so the half-brick shift of running bond repeats
TILE_W = MODULE * PER_COURSE   # 408
TILE_H = COURSE * COURSES      # 160
SHIFT = 3            # px: a hand-laid course never starts exactly half a brick in…
WANDER = 2           # px: …and its head joints are never exactly a brick apart
SEED = 1911          # any fixed number: the same wall on every build

MORTAR_RGB = (228, 220, 208)   # white-grey lime mortar
# alpha of the tile in the middle of the lamp, where the wall is on the --black ground (fonar.css). The mortar is the
# brightest thing on the wall: at 0.06 it keeps the dimmest text of the site (--text-3 #7c827c) above 4.6 : 1 even on
# a joint right under the cursor (5.1 : 1 without the lamp; measured 4.60–4.64 in WebKit and Chromium, 4.9 on the brick
# faces); the bricks are darker than the joints, as in the building. tests/test_fonar.py holds this line
MORTAR_ALPHA = 0.06
BRICK_ALPHA = 0.055
# brick tones: (share, mix toward the deep brick 0…1, alpha factor). Old walls are patchy: most bricks are ordinary red,
# some darker, a few burnt almost black, a few washed out
TONES = (
    (0.34, 0.0, 1.00),
    (0.20, 1.0, 0.92),
    (0.16, 0.5, 0.74),
    (0.14, 0.0, 1.18),
    (0.10, 1.0, 0.50),
    (0.06, 0.0, 1.34),
)


@lru_cache(maxsize=None)
def _token(name: str) -> tuple[int, int, int]:
    css = TOKENS.read_text(encoding="utf-8")
    m = re.search(rf"{re.escape(name)}:\s*(\d+),\s*(\d+),\s*(\d+)\s*;", css)
    if not m:
        raise SystemExit(f"fonar: в {TOKENS.name} нет цвета {name} (ожидается «{name}: R, G, B;»)")
    return tuple(int(v) for v in m.groups())


def _mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _lit(rgb, lamp):
    """The colour a surface shows under the lamp: its own colour times the colour of the light."""
    return tuple(round(c * l / 255) for c, l in zip(rgb, lamp))


def _wrap(x: int, y: int, w: int, h: int) -> list[tuple[int, int, int, int]]:
    """A rectangle of the tile; the part that runs off the right edge continues at the left (the tile repeats)."""
    x %= TILE_W
    if x + w <= TILE_W:
        return [(x, y, w, h)]
    return [(x, y, TILE_W - x, h), (0, y, w - (TILE_W - x), h)]


def courses(rng: random.Random) -> list[list[int]]:
    """x of the head joints of every course (sorted, in [0, TILE_W)): odd courses start half a brick in, give or take
    SHIFT px, and every joint wanders by up to WANDER px, so the bond is regular but not ruled."""
    rows = []
    for c in range(COURSES):
        shift = (MODULE // 2 if c % 2 else 0) + rng.randint(-SHIFT, SHIFT)
        rows.append(sorted((shift + k * MODULE + rng.randint(-WANDER, WANDER)) % TILE_W for k in range(PER_COURSE)))
    return rows


def _path(rects) -> str:
    return "".join(f"M{x} {y}h{w}v{h}h{-w}z" for x, y, w, h in rects)


def tile_svg() -> str:
    brick, deep, lamp = _token("--brick-rgb"), _token("--brick-deep-rgb"), _token("--arch-lamp-rgb")
    rng = random.Random(SEED)
    mortar, tones = [], [[] for _ in TONES]
    weights = [t[0] for t in TONES]
    for c, joints in enumerate(courses(rng)):
        y = c * COURSE
        mortar.append((0, y, TILE_W, JOINT))                       # bed joint over the course
        for k, j in enumerate(joints):
            mortar += _wrap(j, y + JOINT, JOINT, COURSE - JOINT)    # head joint
            end = joints[k + 1] if k + 1 < len(joints) else joints[0] + TILE_W
            tone = rng.choices(range(len(TONES)), weights=weights)[0]
            tones[tone] += _wrap(j + JOINT, y + JOINT, end - j - JOINT, COURSE - JOINT)
    rgb = lambda c: "rgb({},{},{})".format(*c)  # noqa: E731
    parts = [f"<path fill='{rgb(_lit(MORTAR_RGB, lamp))}' fill-opacity='{MORTAR_ALPHA:.3f}' d='{_path(mortar)}'/>"]
    for (_, t, k), rects in zip(TONES, tones):
        if rects:
            parts.append(f"<path fill='{rgb(_lit(_mix(brick, deep, t), lamp))}' fill-opacity='{BRICK_ALPHA * k:.3f}' d='{_path(rects)}'/>")
    # crispEdges: brick and mortar share edges; anti-aliasing both would leave hairline seams between them
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{TILE_W}' height='{TILE_H}' viewBox='0 0 {TILE_W} {TILE_H}' "
            f"shape-rendering='crispEdges'>{''.join(parts)}</svg>")


def data_uri() -> str:
    return "data:image/svg+xml," + quote(tile_svg(), safe="=:/,.'()-")


def css() -> str:
    """The wall's own rule with the tile written out: the wall is animated while the light travels and the browser
    restyles it on those frames, so a value taken through var() would be substituted and parsed anew every time
    (the 2.7 KB tile included). fonar.js reads the tile's size back from background-size."""
    return (f"/* «Фонарь по кирпичу»: the wall, generated by build/fonar.py (the rest is in fonar.css) */\n"
            f'.fonar__wall{{background:url("{data_uri()}") 0 0/{TILE_W}px {TILE_H}px repeat}}\n')


def mark(section_html: str, after: str | None = None) -> str:
    """The section becomes a zone of the wall. `after`: a selector inside the section; the lamp lights only below it."""
    if not section_html.lstrip().startswith("<section"):
        raise ValueError("fonar.mark(): ожидается разметка секции, начинающаяся с <section")
    attrs = f" {ATTR}" + (f' {ATTR}-after="{D.esc(after)}"' if after else "")
    return section_html.replace("<section", "<section" + attrs, 1)
