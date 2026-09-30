# -*- coding: utf-8 -*-
"""«Стена направлений»: on /services.html the 28 service directions are laid as the red-brick wall of the workshop.

    Direction        one direction: its number, link, name, count («6 услуг» / «направление»), works or short text
    wall(items)      a steel beam, two black dome pendants over a plain course, then one brick-shaped link per direction
                     in running bond. The mortar, the half-bricks at the course ends and the plain bricks are the wall's
                     own background (src/assets/css/stena.css), so the list holds only the 28 links.
    index(items)     «Все услуги по направлениям»: every direction with its works as links, or its short text — the content
                     of the old cards. The search above the wall filters this list (pages.js) and the wall mirrors it
                     (src/assets/js/stena.js): a brick stays while its direction is found.
    variation(slug)  the look of one brick — clay, a fire-flashed end, soot clouds, the speckle's offset, worn corners,
                     pits, chips, a hairline crack, a mortar smear, old green paint — decided here from sha-256 of the slug:
                     the same on every build and machine, never random in the browser.

No photos and no raster images: the bricks are CSS gradients, the grain is tiles of SVG dots (grain_style()), the wear is
inline SVG. SVG turbulence noise was tried and dropped: Chrome recomputes an SVG filter on every re-raster, so lifting one
brick cost 100+ ms.
The lettering colour and the strongest light on a brick are in stena.css; tests/test_stena.py checks every brick's clay
against them for WCAG AA.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from urllib.parse import quote

from . import data as D
from .icons import icon, icon_for_href

esc = D.esc

# ---------- clay ----------
# Deep reds and browns of the old brick in the evening light, darker than the lit brick of the photos (181, 85, 58):
# cream lettering has to keep 4.5:1 on every one of them, with the lamp light and a smear on top (tests/test_stena.py).
CLAYS = (
    (139, 58, 38),   # red
    (125, 50, 34),   # deep red
    (146, 66, 41),   # orange-red, the lightest
    (117, 49, 35),   # brown-red
    (131, 59, 45),   # rose-brown
    (104, 42, 31),   # clinker, overburnt
    (137, 68, 45),   # warm terracotta
    (97, 39, 33),    # purple-brown, the darkest
    (143, 62, 48),   # faded red
)
JITTER = 4           # each channel moves by up to ±4 from its clay
SMEAR_RGB = (236, 229, 216)
SMEAR_STOPS = (0.1, 0.04, 0.0)     # opacity of the smear's radial gradient: centre, middle, edge
SMEAR_OPACITY = (0.3, 0.5)         # the range of a smear's own opacity
SMEAR_MAX = SMEAR_STOPS[0] * SMEAR_OPACITY[1]   # the strongest smear on a face (tests: the lettering stays AA over it)

# words too long for a phone brick get a soft hyphen at the natural joint
_SOFT = {"автокондиционеров": "авто\u00adкондиционеров"}
_SHORT = re.compile(r"(?<![\w-])([А-Яа-яЁё]{1,2}) ")


@dataclass(frozen=True)
class Direction:
    n: int                 # 1-based number, as the old cards had it
    href: str
    name: str
    count: str             # «6 услуг», «4 услуги», «1 услуга» or «направление»
    subs: tuple = ()       # ((href, name), …) — the works of the direction
    text: str = ""         # the short text of a direction without works

    @property
    def label(self) -> str:
        return f"{self.n:02d} · {self.count}"

    @property
    def slug(self) -> str:
        return slug_of(self.href)


def slug_of(href: str) -> str:
    """/services/remont-dvigatela.html -> remont-dvigatela (the same key build/icons.py uses)."""
    return href.strip("/").replace("services/", "").split("/")[0].replace(".html", "")


# ---------- deterministic variation ----------
class _Seed:
    """Numbers in [0, 1) from sha-256 of a key: identical on every machine and Python version (no hash(), no random)."""

    def __init__(self, key: str):
        self._key = key.encode("utf-8")
        self._block = b""
        self._pos = 32
        self._round = 0

    def next(self) -> float:
        if self._pos >= 32:
            self._block = hashlib.sha256(self._key + b":" + str(self._round).encode("ascii")).digest()
            self._round += 1
            self._pos = 0
        value = int.from_bytes(self._block[self._pos:self._pos + 4], "big") / 2 ** 32
        self._pos += 4
        return value

    def uniform(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.next()

    def chance(self, p: float) -> bool:
        return self.next() < p

    def pick(self, seq):
        return seq[min(len(seq) - 1, int(self.next() * len(seq)))]


@dataclass(frozen=True)
class Look:
    clay: tuple            # (r, g, b)
    burn: float            # darkness of the fire-flashed end, 0 = none
    burn_dir: int          # 90: the left end is dark, 270: the right end
    grain: tuple           # where the grain tiles start on this face, px
    blotches: tuple        # ((x %, y %, width %, height %, darkness), …) — soot and firing clouds on the face
    radii: tuple           # 4 horizontal + 4 vertical corner radii, px: a hand-made brick is never quite square
    inset: tuple           # top, right, bottom, left: the face sits up to 1.5px inside its bed (irregular joints)
    pits: tuple            # ((x %, y %, r px, opacity), …)
    chips: tuple           # ((corner, size px), …), corner in tl / tr / bl / br
    crack: tuple | None    # (x %, from the top edge?, ((dx, dy), …) px)
    smear: tuple | None    # (x %, y %, rx %, ry %, opacity) — a smear of mortar near the bottom edge
    paint: tuple | None    # (corner, ((x, y), …) px from that corner, opacity) — a flake of old green paint, as on the facade


def _flake(s: _Seed, size: float) -> tuple:
    """An angular flake of paint: seven points around a centre a little inside the corner, px."""
    cx, cy = size * 0.55, size * 0.45
    points = []
    for k in range(7):
        a = 2 * math.pi * k / 7 + s.uniform(-0.25, 0.25)
        r = size * s.uniform(0.45, 0.8)
        points.append((round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a) * 0.7, 1)))
    return tuple(points)


def variation(slug: str) -> Look:
    """The look of the brick for this slug. Pure: the same slug always gives the same brick."""
    s = _Seed(f"stena:{slug}")
    base = s.pick(CLAYS)
    clay = tuple(max(0, min(255, round(c + s.uniform(-JITTER, JITTER)))) for c in base)
    burn = round(s.uniform(0.22, 0.5), 2) if s.chance(0.5) else 0.0
    burn_dir = 90 if s.chance(0.5) else 270
    grain = (round(s.uniform(0, 97)), round(s.uniform(0, 83)))   # where the grain tiles start on this face
    blotches = tuple((round(s.uniform(4, 96)), round(s.uniform(6, 94)), round(s.uniform(16, 52)), round(s.uniform(45, 120)),
                      round(s.uniform(0.16, 0.42), 2)) for _ in range(3))
    radii = tuple(round(s.uniform(1.5, 5.5), 1) for _ in range(4)) + tuple(round(s.uniform(1.0, 4.0), 1) for _ in range(4))
    inset = tuple(round(s.pick((0, 0, 0.5, 1, 1.5)), 1) for _ in range(4))
    pits = tuple((round(s.uniform(4, 96)), round(s.uniform(10, 90)), round(s.uniform(0.6, 1.5), 1), round(s.uniform(0.35, 0.65), 1))
                 for _ in range(3 + int(s.next() * 6)))
    corners = [c for c in ("tl", "tr", "bl", "br") if s.chance(0.22)][:2]
    chips = tuple((c, round(s.uniform(4, 10), 1)) for c in corners)
    crack = None
    if s.chance(0.4):
        down = s.chance(0.5)
        steps = tuple((round(s.uniform(-2.2, 2.2), 1), round(s.uniform(3.0, 6.5), 1)) for _ in range(3 + int(s.next() * 3)))
        crack = (round(s.uniform(14, 86), 1), down, steps)
    smear = None
    if s.chance(0.3):
        smear = (round(s.uniform(12, 88), 1), round(s.uniform(78, 104), 1), round(s.uniform(14, 34), 1),
                 round(s.uniform(18, 34), 1), round(s.uniform(*SMEAR_OPACITY), 2))
    paint = None
    if s.chance(0.15):
        paint = (s.pick(("tl", "tr", "bl", "br")), _flake(s, s.uniform(12, 22)), round(s.uniform(0.3, 0.45), 2))
    return Look(clay, burn, burn_dir, grain, blotches, radii, inset, pits, chips, crack, smear, paint)


def hex_of(rgb: tuple) -> str:
    return "#" + "".join(f"{c:02x}" for c in rgb)


def _num(v: float) -> str:
    """Short numbers for inline styles and SVG: 1.0 -> 1, 0.5 -> .5, -0.25 -> -.25."""
    text = f"{v:.2f}".rstrip("0").rstrip(".")
    if text in ("", "-0"):
        return "0"
    if text.startswith("0."):
        return text[1:]
    if text.startswith("-0."):
        return "-" + text[2:]
    return text


def style(look: Look) -> str:
    """Inline custom properties of a brick (stena.css reads them)."""
    h, v = look.radii[:4], look.radii[4:]
    radius = " ".join(f"{_num(x)}px" for x in h) + " / " + " ".join(f"{_num(x)}px" for x in v)
    inset = " ".join(f"{_num(x)}px" if x else "0" for x in look.inset)
    props = [f"--b:{hex_of(look.clay)}", f"--gx:{look.grain[0]}px", f"--gy:{look.grain[1]}px"]
    for k, (x, y, w, h, a) in enumerate(look.blotches, 1):
        props.append(f"--m{k}:{x}% {y}%;--m{k}s:{w}% {h}%;--m{k}a:{_num(a)}")
    props += [f"--r:{radius}", f"--ins:{inset}"]
    if look.burn:
        props.append(f"--burn:{_num(look.burn)};--burn-dir:{look.burn_dir}deg")
    return ";".join(props)


def _corner(corner: str) -> str:
    """Position of a nested <svg> at a corner of the brick: its content is drawn in px from that corner."""
    return f'x="{"100%" if corner[1] == "r" else "0"}" y="{"100%" if corner[0] == "b" else "0"}"'


def _flip(corner: str) -> str:
    """Shapes are drawn for the top-left corner; the other corners mirror them inwards."""
    if corner == "tl":
        return ""
    return f' transform="scale({-1 if corner[1] == "r" else 1} {-1 if corner[0] == "b" else 1})"'


def wear_svg(look: Look) -> str:
    """Pits, chipped corners, a crack, a smear and old paint: percent positions, px sizes, so nothing stretches."""
    parts = []
    if look.smear:
        x, y, rx, ry, o = look.smear
        parts.append(f'<ellipse cx="{_num(x)}%" cy="{_num(y)}%" rx="{_num(rx)}%" ry="{_num(ry)}%" fill="url(#stena-smear)" opacity="{_num(o)}"/>')
    if look.paint:
        corner, points, o = look.paint
        d = "M" + "L".join(f"{_num(px)} {_num(py)}" for px, py in points) + "Z"
        parts.append(f'<svg {_corner(corner)} overflow="visible"><path class="brick__paint" d="{d}"{_flip(corner)} opacity="{_num(o)}"/></svg>')
    if look.pits:
        dots = "".join(f'<circle cx="{_num(x)}%" cy="{_num(y)}%" r="{_num(r)}" opacity="{_num(o)}"/>' for x, y, r, o in look.pits)
        parts.append(f'<g class="brick__pits">{dots}</g>')
    for corner, size in look.chips:
        # a chip bitten out of the corner: an irregular wedge, drawn for the top-left corner and mirrored
        k = [_num(round(size * f, 1)) for f in (1, 0.55, 0.32, 0.28, 0.62, 0.9)]
        d = f"M0 0H{k[0]}L{k[1]} {k[2]}L{k[3]} {k[4]}L0 {k[5]}Z"
        parts.append(f'<svg {_corner(corner)} overflow="visible"><path class="brick__chip" d="{d}"{_flip(corner)}/></svg>')
    if look.crack:
        x, down, steps = look.crack
        sign = 1 if down else -1
        d = "M0 0" + "".join(f"l{_num(dx)} {_num(sign * dy)}" for dx, dy in steps)
        parts.append(f'<svg x="{_num(x)}%" y="{"0" if down else "100%"}" overflow="visible"><path class="brick__crack" d="{d}"/></svg>')
    return f'<svg class="brick__wear" aria-hidden="true" focusable="false">{"".join(parts)}</svg>'


# ---------- grain: dots at scattered places, drawn once as small SVG tiles the bricks and the mortar repeat ----------
# Two tiles of co-prime sizes over each other never line up into a visible grid. Plain shapes only: no SVG filters
# (a filter is recomputed on every re-raster in Chrome).
GRAIN_TILES = (
    ("clay-a", (72, 56), 26, 8),
    ("clay-b", (97, 83), 24, 6),
    ("sand", (46, 38), 20, 12),
)


# a dot is a zero-length segment with a round cap: «M x y h0» draws a circle of the stroke's width
_PORES = ((1.0, 0.5), (1.5, 0.38), (2.1, 0.26))   # (diameter px, opacity): small dark pores are the darkest
_GRAINS = ((0.9, 0.22), (1.4, 0.12))              # light sand grains


def _grain_tile(key: str, size: tuple, dark: int, light: int) -> str:
    """A tile of pores (dark) and grains (light), seamless: a dot on an edge is drawn again on the opposite edge."""
    s = _Seed(f"stena-grain:{key}")
    w, h = size

    def paths(n: int, buckets: tuple, colour: str) -> str:
        spots = [[] for _ in buckets]
        for _ in range(n):
            x, y, k = s.uniform(0, w), s.uniform(0, h), int(s.next() * len(buckets))
            r = buckets[k][0] / 2
            for dx in (0, -w, w):
                for dy in (0, -h, h):
                    if -r <= x + dx <= w + r and -r <= y + dy <= h + r:
                        spots[k].append(f"M{_num(round(x + dx, 1))} {_num(round(y + dy, 1))}h0")
        return "".join(f"<path d='{''.join(d)}' stroke='{colour}' stroke-width='{_num(width)}' stroke-opacity='{_num(a)}'/>"
                       for d, (width, a) in zip(spots, buckets) if d)

    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' stroke-linecap='round'>"
           f"{paths(dark, _PORES, '#140603')}{paths(light, _GRAINS, '#fff0dc')}</svg>")
    # percent-encoded apostrophes: the URI then needs no escaping inside the HTML attribute
    return 'url("data:image/svg+xml,' + quote(svg, safe=" =/:.,-()") + '")'


def grain_style() -> str:
    """Custom properties with the grain tiles, set on the wall: --grain-clay-a, --grain-clay-b, --grain-sand."""
    return ";".join(f"--grain-{key}:{_grain_tile(key, size, dark, light)}" for key, size, dark, light in GRAIN_TILES)


def _lettering(name: str) -> str:
    """The name as it is painted: escaped, a no-break space after one- and two-letter words («и ходовой»),
    a soft hyphen in the words that would not fit a phone brick."""
    text = _SHORT.sub("\\1\u00a0", esc(name))
    for word, soft in _SOFT.items():
        text = text.replace(word, soft)
    return text


# ---------- markup ----------
def _defs() -> str:
    """Shared by every brick and lamp on the page: the smear's gradient, the enamel of the dome and the dome itself."""
    rgb = "rgb({}, {}, {})".format(*SMEAR_RGB)
    smear_stops = "".join(f'<stop offset="{_num(k / (len(SMEAR_STOPS) - 1))}" stop-color="{rgb}" stop-opacity="{_num(a)}"/>'
                          for k, a in enumerate(SMEAR_STOPS))
    return f"""<svg class="sprite" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">
      <defs>
        <radialGradient id="stena-smear">{smear_stops}</radialGradient>
        <linearGradient id="stena-enamel" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#141515"/><stop offset=".18" stop-color="#474a4a"/><stop offset=".33" stop-color="#171818"/><stop offset=".8" stop-color="#0b0c0c"/><stop offset=".95" stop-color="#252626"/><stop offset="1" stop-color="#111212"/></linearGradient>
      </defs>
      <symbol id="stena-lamp" viewBox="0 0 64 54">
        <rect x="26.5" y="0" width="11" height="9" rx="2" fill="#1c1d1d"/>
        <rect x="22.5" y="7.5" width="19" height="3.5" rx="1.2" fill="#0e0f0f" stroke="rgba(255,255,255,.14)" stroke-width=".5"/>
        <path d="M23 11C12.5 12.5 7.5 19.5 6.5 28.5L3 49.5h58l-3.5-21C56.5 19.5 51.5 12.5 41 11z" fill="url(#stena-enamel)"/>
        <path d="M23 11C12.5 12.5 7.5 19.5 6.5 28.5L3 49.5" fill="none" stroke="rgba(255,255,255,.1)" stroke-width=".7"/>
        <ellipse cx="32" cy="49.8" rx="29.4" ry="3.3" fill="#8e918c"/>
        <ellipse cx="32" cy="50.2" rx="28" ry="2.6" fill="#332d27"/>
      </symbol>
    </svg>"""


def _lamp(k: int) -> str:
    return f"""<span class="stena__lamp stena__lamp--{k}">
          <span class="stena__cord"></span>
          <svg class="stena__dome" viewBox="0 0 64 54" focusable="false"><use href="#stena-lamp"/></svg>
          <span class="stena__bulb"></span>
        </span>"""


def _brick(i: int, total: int, d: Direction) -> str:
    """--i orders the laying; --k (0 at the top, 1 at the bottom) takes the brick into the shade far from the lamps."""
    look = variation(d.slug)
    depth = _num(i / max(1, total - 1))
    return (f'<li class="stena__slot" style="--i:{i};--k:{depth}"><a class="brick" href="{d.href}" style="{style(look)}">'
            f'{wear_svg(look)}'
            f'<span class="brick__name">{_lettering(d.name)}</span> '
            f'<span class="brick__label">{esc(d.label)}</span>'
            f'{icon(icon_for_href(d.href), "brick__icon")}'
            f'</a></li>')


def wall(items: list) -> str:
    """The wall: a list of the directions' links, each a brick. Decoration around it is aria-hidden."""
    bricks = "\n        ".join(_brick(i, len(items), d) for i, d in enumerate(items))
    return f"""<div class="stena reveal" data-stena style="{esc(grain_style())}">
      {_defs()}
      <div class="stena__beam" aria-hidden="true"></div>
      <ul class="stena__wall" role="list">
        {bricks}
      </ul>
      <div class="stena__plinth" aria-hidden="true"></div>
      <div class="stena__light" aria-hidden="true"></div>
      <div class="stena__lamps" aria-hidden="true">{_lamp(1)}{_lamp(2)}</div>
    </div>"""


INDEX_TITLE = "Все услуги по направлениям"


def index(items: list) -> str:
    """The works of every direction (the links and texts of the old cards). Open on wide screens, folded on phones
    (stena.js); the search opens it. Items keep the old card classes: pages.js filters .cat-card by data-title and
    by the text of .cat-card__subs a."""
    rows = []
    for d in items:
        subs = "".join(f'<a href="{href}">{esc(name)}</a>' for href, name in d.subs)
        body = f'<div class="cat-card__subs">{subs}</div>' if d.subs else f'<p class="stena-index__text">{esc(d.text)}</p>'
        rows.append(f"""<li class="cat-card" data-title="{esc(d.name)}">
          <a class="cat-card__head" href="{d.href}"><span class="stena-index__swatch" style="--b:{hex_of(variation(d.slug).clay)}" aria-hidden="true"></span><span class="stena-index__n">{d.n:02d}</span><span class="cat-card__title">{esc(d.name)}</span></a>
          {body}
        </li>""")
    return f"""<details class="stena-index reveal" data-stena-index open>
      <summary class="stena-index__title"><span>{esc(INDEX_TITLE)}</span>{icon('plus', 'stena-index__ic')}</summary>
      <ul class="stena-index__list" role="list">
        {"".join(rows)}
      </ul>
    </details>"""
