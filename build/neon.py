# -*- coding: utf-8 -*-
"""«Неон»: the mint neon of the workshop sign as one system across the site — no photos, CSS and inline SVG only.

    material_css()  the red-brick wall as a CSS material: two tiles of the same running-bond wall, one at dusk and one
                    lit by the mint tubes, generated here and put into the CSS bundle (build.py) as data URIs
    notfound()      the 404 scene: a brick wall, «404» bent from mint tubes, one tube of the last digit broken,
                    the light of the tubes on the wall
    footer_sign()   the GARAGE TEAM sign of the workshop hall (the tubes of build/svet.py) hanging on a brick strip
                    at the top of the footer; it switches on when the footer scrolls into view

Every tube is drawn in layers of strokes — a wide faint halo, a glow, the tube body and a white-hot core — instead of a
blur filter (the recipe of «Свет ламп», build/svet.py). Under the lit tubes lies the unlit glass: a pale tube with a
highlight and black-painted ends where the tube turns into the wall; it is what is seen while a tube is dark.
Only opacity is animated: the lit layers are separate <svg> / <div> boxes, so the browser can fade them on the GPU.
Styles: src/assets/css/neon.css (also the neon underline of the header menu), behaviour: src/assets/js/neon.js.
"""
from __future__ import annotations

import math
import random
import re
from functools import lru_cache
from typing import NamedTuple
from urllib.parse import quote

from . import svet

# ---------- the brick wall ----------
# One running-bond tile: COURSES courses of PER_COURSE bricks, every other course shifted by half a brick.
# Old hand-made bricks (the office wall on Красная слобода): lengths vary a little, the corners are not quite square,
# the joints are thin light-grey mortar. Units are CSS pixels at scale 1 (neon.css scales the tile per screen size).
COURSE = 20            # course height: brick face + joint
JOINT = 3              # mortar joint
MODULE = 69            # brick length + joint
PER_COURSE = 8
COURSES = 12
TILE_W, TILE_H = MODULE * PER_COURSE, COURSE * COURSES
SEED = 9               # the wall must look the same on every build

# Colours of the tile at dusk: brick faces (their spread) and the mortar.
# Measured on the office photos (real/brick-wall.jpg, lamp light: bricks ≈ #603c29, mortar ≈ #aea594) and darkened
# for an evening wall with no lamp over it.
DUSK = {"brick": (66, 34, 25), "spread": 0.16, "mortar": (96, 90, 82)}
# The same wall in the light of the tubes: mint light (64, 240, 192) reflected by red brick and by grey mortar.
# Red brick returns little of it (the faces only turn a duller brown), the light-grey mortar a lot: the joints glow mint.
MINT = (64, 240, 192)
ALBEDO = {"brick": (0.4, 0.14, 0.11), "mortar": (0.74, 0.7, 0.64)}
LIT_LEVEL = 0.62       # how strong the neon light is on the wall right next to the tubes
SHADES = 9             # brick colours are quantised: bricks of one shade share one <path>, so the tile stays small


def _lit(rgb: tuple[int, int, int], albedo: tuple[float, float, float]) -> tuple[int, int, int]:
    """A dusk colour plus the mint light it reflects."""
    return tuple(min(255, round(c + m * a * LIT_LEVEL)) for c, m, a in zip(rgb, MINT, albedo))


def _hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(rgb)


def _num(v: float) -> str:
    """Shortest form of a coordinate with one decimal: 12.0 -> 12, 0.5 -> .5, -0.5 -> -.5, -0.04 -> 0"""
    r = round(v, 1)
    if r == 0:                      # also -0.0: never write "-0"
        return "0"
    s = f"{r:.1f}".rstrip("0").rstrip(".")
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


class Brick(NamedTuple):
    shade: int                                   # 0 … SHADES-1, dark to light
    corners: tuple[tuple[float, float], ...]     # four corners, clockwise from the top left


@lru_cache(maxsize=1)
def _bricks() -> tuple[Brick, ...]:
    """The bricks of one tile. A brick cut by the right or the left edge is also drawn one tile to the other side, so
    the tile repeats without a seam; the course joints fall on the tile's top and bottom edges."""
    rnd = random.Random(SEED)
    half = JOINT / 2
    out = []
    for c in range(COURSES):
        # lengths vary by a few pixels, the course still closes on exactly TILE_W
        jit = [rnd.uniform(-5, 5) for _ in range(PER_COURSE)]
        mean = sum(jit) / PER_COURSE
        lengths = [MODULE + j - mean for j in jit]
        x = (MODULE / 2 if c % 2 else 0) + rnd.uniform(-4, 4)
        y0, y1 = c * COURSE + half, (c + 1) * COURSE - half
        for length in lengths:
            wob = [(rnd.uniform(-0.7, 0.7), rnd.uniform(-0.5, 0.5)) for _ in range(4)]
            box = ((x + half, y0), (x + length - half, y0), (x + length - half, y1), (x + half, y1))
            corners = tuple((px + dx, py + dy) for (px, py), (dx, dy) in zip(box, wob))
            # most bricks sit near the middle shade, a few are clearly darker (burnt) or lighter
            shade = min(SHADES - 1, max(0, round(rnd.gauss((SHADES - 1) / 2, SHADES / 5.5))))
            for shift in (-TILE_W, 0, TILE_W):
                moved = tuple((px + shift, py) for px, py in corners)
                if max(px for px, _ in moved) > 0 and min(px for px, _ in moved) < TILE_W:
                    out.append(Brick(shade, moved))
            x += length
    return tuple(out)


def _shade_rgb(base: tuple[int, int, int], spread: float, shade: int) -> tuple[int, int, int]:
    """Brick colour of a shade: lighter or darker around the base, the darker ones a touch more purple (burnt)."""
    k = 1 + spread * (shade / (SHADES - 1) * 2 - 1)
    r, g, b = base
    burnt = max(0.0, 1 - k) * 0.6
    return (min(255, round(r * k)), min(255, round(g * k * (1 - burnt * 0.3))), min(255, round(b * k * (1 + burnt * 0.4))))


def brick_tile(lit: bool = False) -> str:
    """The SVG of one tile, at dusk or in the light of the tubes."""
    by_shade: dict[int, list[str]] = {}
    for b in _bricks():
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = b.corners
        by_shade.setdefault(b.shade, []).append(
            f"M{_num(x0)} {_num(y0)}L{_num(x1)} {_num(y1)}L{_num(x2)} {_num(y2)}L{_num(x3)} {_num(y3)}Z")
    mortar = DUSK["mortar"]
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{TILE_W}' height='{TILE_H}'>",
             f"<rect width='{TILE_W}' height='{TILE_H}' fill='{_hex(_lit(mortar, ALBEDO['mortar']) if lit else mortar)}'/>"]
    for shade in sorted(by_shade):
        rgb = _shade_rgb(DUSK["brick"], DUSK["spread"], shade)
        fill = _hex(_lit(rgb, ALBEDO["brick"]) if lit else rgb)
        parts.append(f"<path fill='{fill}' d='{''.join(by_shade[shade])}'/>")
    # every course catches a little light on its top edge and has a shadow under it (the joints are recessed)
    edges = "".join(f"M0 {_num(c * COURSE + JOINT / 2)}h{TILE_W}v1H0Z" for c in range(COURSES))
    shadows = "".join(f"M0 {_num((c + 1) * COURSE - JOINT / 2 - 1.4)}h{TILE_W}v1.4H0Z" for c in range(COURSES))
    parts.append(f"<path fill='#fff' fill-opacity='.05' d='{edges}'/><path fill='#000' fill-opacity='.3' d='{shadows}'/>")
    parts.append("</svg>")
    return "".join(parts)


# The pores and grime of old brick: fine dark specks over the whole wall. A noise texture drawn once into a small
# tile image (a static background, nothing is filtered while the page runs).
GRAIN = 160


def grain_tile() -> str:
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{GRAIN}' height='{GRAIN}'>"
            "<filter id='g' x='0' y='0' width='100%' height='100%'>"
            "<feTurbulence type='fractalNoise' baseFrequency='.6' numOctaves='2' stitchTiles='stitch'/>"
            "<feColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1.4 0 0 0 -.62'/></filter>"
            f"<rect width='{GRAIN}' height='{GRAIN}' filter='url(#g)'/></svg>")


def _data_uri(svg: str) -> str:
    # quotes inside the SVG are single, so the URI can sit in url("…"); only characters that break a URL are encoded
    return "data:image/svg+xml," + quote(svg, safe="/ ,.:;=()'-")


def material_css() -> str:
    """CSS custom properties with the wall tiles; build.py puts them at the start of the bundle (neon.css uses them)."""
    return ("/* «Неон»: the brick wall material, generated by build/neon.py */\n"
            f':root{{--neon-brick:url("{_data_uri(brick_tile())}");'
            f'--neon-brick-lit:url("{_data_uri(brick_tile(lit=True))}");'
            f'--neon-grain:url("{_data_uri(grain_tile())}");'
            f"--neon-tile-w:{TILE_W}px;--neon-grain-w:{GRAIN}px}}\n")


# ---------- tubes ----------
Point = tuple[float, float]


class Tube(NamedTuple):
    d: str       # centre line of the glass tube
    ends: str    # the two short pieces at its ends that are painted black: there the tube turns into the wall


def _unit(a: Point, b: Point) -> Point:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if not n:
        raise ValueError(f"неон: две одинаковые точки трубки {a}")
    return dx / n, dy / n


def _pt(p: Point) -> str:
    return f"{_num(p[0])} {_num(p[1])}"


def bent_tube(points: list[Point], r: float = 0, end: float = 7) -> Tube:
    """A glass tube bent along a polyline: straight runs joined by circular bends of radius r (glass is heated and
    bent, a tube has no sharp corners). Both ends are straight runs; `end` units of each are painted black."""
    if len(points) < 2:
        raise ValueError("неон: у трубки меньше двух точек")
    d = [f"M{_pt(points[0])}"]
    runs = [math.dist(a, b) for a, b in zip(points, points[1:])]
    used = [0.0] * len(runs)             # length of every run eaten by the bends at its two ends
    for i, (prev, cur, nxt) in enumerate(zip(points, points[1:], points[2:])):
        u, v = _unit(prev, cur), _unit(cur, nxt)
        turn = math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))
        t = r * math.tan(turn / 2)
        used[i] += t
        used[i + 1] += t
        a = (cur[0] - u[0] * t, cur[1] - u[1] * t)
        b = (cur[0] + v[0] * t, cur[1] + v[1] * t)
        sweep = 1 if u[0] * v[1] - u[1] * v[0] > 0 else 0   # y points down: a right turn is clockwise
        d.append(f"L{_pt(a)}A{_num(r)} {_num(r)} 0 0 {sweep} {_pt(b)}")
    d.append(f"L{_pt(points[-1])}")
    straight = [run - u for run, u in zip(runs, used)]
    if min(straight) < -1e-6 or straight[0] < end or straight[-1] < end:
        raise ValueError(f"неон: изгибы радиусом {r} не помещаются в трубку {points}")
    head, tail = _unit(points[0], points[1]), _unit(points[-1], points[-2])
    p0, p1 = points[0], points[-1]
    ends = (f"M{_pt(p0)}L{_pt((p0[0] + head[0] * end, p0[1] + head[1] * end))}"
            f"M{_pt(p1)}L{_pt((p1[0] + tail[0] * end, p1[1] + tail[1] * end))}")
    return Tube("".join(d), ends)


# ---------- «404» ----------
# The digits are bent from single tubes, as a neon workshop bends them: a «4» is a tube for the diagonal and the bar and
# a tube for the stem (it crosses the bar in front of it), a «0» is one tube around with both ends at the lower left,
# where they go into the wall. Digit height 200 units; the drawing is 500 × 200 plus room for the glow.
DIGIT_H = 200
GAP = 46                      # between the digits
FOUR_W, ZERO_W = 140, 128
STEM_X = 100                  # the stem of a «4», from its left edge
BAR_Y = 138                   # the bar of a «4»
VIEW_404 = (-26, -26, 552, 252)
LAST_FOUR_X = FOUR_W + GAP + ZERO_W + GAP
SPILL = 90                    # how far the light of a single tube reaches over the wall


def _four(x: float) -> list[Tube]:
    return [bent_tube([(x + 86, 10), (x + 4, BAR_Y), (x + FOUR_W, BAR_Y)], r=16),
            bent_tube([(x + STEM_X, 0), (x + STEM_X, DIGIT_H)])]


def _zero(x: float) -> list[Tube]:
    w, h = ZERO_W, DIGIT_H
    return [bent_tube([(x, 126), (x, 0), (x + w, 0), (x + w, h), (x, h), (x, 142)], r=50)]


def tubes_404() -> tuple[list[Tube], Tube]:
    """(the tubes that burn steadily, the broken one): the broken tube is the stem of the last «4»."""
    *steady, broken = _four(0) + _zero(FOUR_W + GAP) + _four(LAST_FOUR_X)
    return steady, broken


# The layers of a lit mint tube, back to front: (stroke, width). A halo and a glow instead of a blur, then the glass
# body and its white-hot core. Widths are in units of the 404 drawing (a tube is 5.4 units, ≈ 6 px on a desktop).
LIT_404 = (("rgba(64,240,192,.035)", 44), ("rgba(64,240,192,.07)", 26), ("rgba(64,240,192,.15)", 13),
           ("rgba(86,246,204,.42)", 8.2), ("#43f1c1", 5.4), ("#f0fffb", 2.3))
# The unlit glass under them: its shadow on the wall (the tube stands a few centimetres off the bricks, the room light
# falls from above), the pale glass and a highlight along the upper side.
GLASS_404 = (('transform="translate(2.5 5.5)"', "rgba(8,4,3,.5)", 6.4), ("", "rgba(206,255,240,.15)", 5.6),
             ('transform="translate(-.9 -1.3)"', "rgba(255,255,255,.3)", 1.1))
PAINT = (("", "#0f1311", 6.2), ('transform="translate(-.9 -1.3)"', "rgba(255,255,255,.14)", 1))


def _uses(ref: str, layers) -> str:
    return "".join(f'<use href="#{ref}" stroke="{stroke}" stroke-width="{_num(w)}"/>' for stroke, w in layers)


def _painted(ref: str) -> str:
    return "".join(f'<use href="#{ref}" {t} stroke="{s}" stroke-width="{_num(w)}"/>' for t, s, w in PAINT)


def _svg(cls: str, body: str, view=VIEW_404) -> str:
    vb = " ".join(_num(v) for v in view)
    return (f'<svg class="{cls}" viewBox="{vb}" focusable="false">'
            f'<g fill="none" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


def _box(x0: float, y0: float, x1: float, y1: float, view=VIEW_404) -> str:
    """Inline style placing an element over a region of the drawing, in % of the drawing's box."""
    vx, vy, vw, vh = view
    return (f"left:{(x0 - vx) / vw * 100:.2f}%;top:{(y0 - vy) / vh * 100:.2f}%;"
            f"width:{(x1 - x0) / vw * 100:.2f}%;height:{(y1 - y0) / vh * 100:.2f}%")


def sign_404() -> str:
    """The «404» sign: the glass (always there), the lit tubes and, on its own layer, the broken tube with its light."""
    steady, broken = tubes_404()
    paths = "".join(f'<path d="{t.d}"/>' for t in steady)
    defs = (f'<defs><g id="neon-404-steady">{paths}</g><path id="neon-404-broken" d="{broken.d}"/>'
            f'<path id="neon-404-ends" d="{"".join(t.ends for t in steady)}"/>'
            f'<path id="neon-404-broken-ends" d="{broken.ends}"/></defs>')
    glass = "".join(f'<use href="#{ref}" {t} stroke="{s}" stroke-width="{_num(w)}"/>'
                    for t, s, w in GLASS_404 for ref in ("neon-404-steady", "neon-404-broken"))
    # the broken tube lights its own patch of wall (SPILL units around it): it goes dark with the tube
    stem_x = LAST_FOUR_X + STEM_X
    spill = _box(stem_x - SPILL, -SPILL / 2, stem_x + SPILL, DIGIT_H + SPILL / 2)
    _, _, vw, vh = VIEW_404
    return f"""<div class="neon-404__sign" aria-hidden="true" style="aspect-ratio:{_num(vw)} / {_num(vh)};--ar:{vw / vh:.4f}">
      <span class="neon-404__walllit"></span>
      <span class="neon-404__spill" style="{spill}"></span>
      {_svg("neon-404__glass", defs + glass + _painted("neon-404-ends") + _painted("neon-404-broken-ends"))}
      {_svg("neon-404__lit", _uses("neon-404-steady", LIT_404) + _painted("neon-404-ends"))}
      {_svg("neon-404__tube", _uses("neon-404-broken", LIT_404) + _painted("neon-404-broken-ends"))}
    </div>"""


def notfound(content: str) -> str:
    """The 404 page body: the brick wall with the neon «404», then `content` — ready HTML: the heading (with
    id="notfound-title"), the text and the links of build/static_pages.py — on a darker patch of the same wall."""
    return f"""<section class="neon-404" data-neon-404 aria-labelledby="notfound-title">
  <div class="neon-404__wall" aria-hidden="true"></div>
  <div class="wrap notfound">
    {sign_404()}
    <div class="neon-404__copy">
  {content}
    </div>
  </div>
</section>"""


# ---------- the GARAGE TEAM sign in the footer ----------
# The tubes are those of the «Свет ламп» sign (build/svet.py, traced from the logo), so the footer shows the same sign
# as the workshop hall and the first screen: white letter tubes, a mint frame, «CAR SERVICE» filled mint.
# The layers follow the recipe of svet.py, with a highlight on the unlit glass: the sign is dark until it scrolls in.
SIGN_GLASS = ('<use href="#neon-sign-mint" stroke="rgba(170,255,228,.13)" stroke-width="2"/>'
              '<use href="#neon-sign-white" stroke="rgba(255,248,240,.14)" stroke-width="2"/>'
              '<use href="#neon-sign-script" fill="rgba(170,255,228,.1)"/>'
              '<use href="#neon-sign-mint" transform="translate(-.35 -.45)" stroke="rgba(255,255,255,.16)" stroke-width=".5"/>'
              '<use href="#neon-sign-white" transform="translate(-.35 -.45)" stroke="rgba(255,255,255,.16)" stroke-width=".5"/>')
SIGN_LIT = ('<use href="#neon-sign-mint" stroke="rgba(52,232,184,.13)" stroke-width="13"/>'
            '<use href="#neon-sign-white" stroke="rgba(190,255,236,.10)" stroke-width="11"/>'
            '<use href="#neon-sign-mint" stroke="rgba(64,240,192,.38)" stroke-width="5.5"/>'
            '<use href="#neon-sign-white" stroke="rgba(214,255,243,.34)" stroke-width="5"/>'
            '<use href="#neon-sign-script" fill="#58f2c9" stroke="rgba(64,240,192,.35)" stroke-width="4"/>'
            '<use href="#neon-sign-mint" stroke="#8dffe0" stroke-width="2.2"/>'
            '<use href="#neon-sign-white" stroke="#f6fffb" stroke-width="2.2"/>')
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def compact_path(d: str) -> str:
    """Path data with one decimal and no spaces around the commands (the footer sign is on every page):
    'M 182.8 390.21 L 182.8 390.17' -> 'M182.8 390.2L182.8 390.2'."""
    d = _NUMBER.sub(lambda m: _num(float(m.group())), d)
    return re.sub(r"\s*([A-Za-z])\s*", r"\1", " ".join(d.split()))


@lru_cache(maxsize=1)
def footer_sign() -> str:
    """The brick strip at the top of the footer with the sign hanging on two wires (decorative: aria-hidden).
    The same on every page (no URLs in it), so it is built once per build."""
    tubes = svet.neon_tubes()
    letters = "".join(f'<path d="{compact_path(d)}"/>' for d in tubes.letters)
    defs = (f'<defs><g id="neon-sign-white">{letters}</g><path id="neon-sign-mint" d="{compact_path(tubes.frame)}"/>'
            f'<path id="neon-sign-script" d="{compact_path(tubes.script)}"/></defs>')
    view = tuple(float(v) for v in svet.NEON_VIEWBOX.split())
    _, _, vw, vh = view
    return f"""<div class="neon-strip" data-neon-sign aria-hidden="true" style="--sign-k:{vh / vw:.4f}">
    <div class="neon-strip__sign" style="aspect-ratio:{_num(vw)} / {_num(vh)}">
      <span class="neon-strip__lit"></span>
      {_svg("neon-sign__glass", defs + SIGN_GLASS, view)}
      {_svg("neon-sign__lit", SIGN_LIT, view)}
    </div>
  </div>"""
