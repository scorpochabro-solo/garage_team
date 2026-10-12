# -*- coding: utf-8 -*-
"""«Краска на кирпиче»: the big numerals of the site as ghost signs — old paint on a brick wall.

The «360» of «Почему выбирают Гараж» and the «-5%» of the promo ticket on the first screen are painted in cream
on a small brick wall, in the materials of the building on Красная слобода, 9: red brick with white-grey joints,
a field of black paint (like the brickwork around the gate), under it the old green paint that still flakes off
the upper floor, and the cream numerals on top. The joints show through every coat, the black has flaked in
places down to the green or to the brick, the cream is thinner in patches and in streaks that run down the wall.

Only vectors. write_assets() writes the files below at build time from a fixed seed, so every build writes the
same bytes; kraska.css uses them as backgrounds and masks (each is rastered once by the browser and cached):
  brick-day.svg, brick-night.svg  the wall: running bond, the colour of every brick, worn arrises, burnt ends,
                                  traces of limewash, a mottled face (night: a smaller tile for the small ticket)
  relief.svg                      one pair of courses: the form of the bricks — lit top arris, shaded underside,
                                  joints in shadow. It lies over the paint too, so the paint follows the brick
  grain.svg                       the porous surface: dark pits where dirt collected, in patches (a repeating tile)
  joints.svg                      paint mask shared by the coats: how much paint every brick face and every stretch
                                  of joint kept (each coat adds its own floor in kraska.css)
  wear-<coat>.svg                 paint masks from noise (feTurbulence, computed once): flakes, pits of a dry brush
                                  on porous brick, uneven fading stretched downwards like rain streaks. The black
                                  mostly flakes where the cream did, so a flake in the cream shows the black and goes
                                  down to the brick at its deepest; the old green flaked on its own long before
  brush.svg                       the front of a dry brush: the mask of the one-time «paint appears» reveal

layers() is the decorative markup inside a host (aria-hidden); the numeral is the host's own element, which keeps
its text and its old look in browsers without CSS masks. The numbers are also in the visible text next to it.
"""
from __future__ import annotations

import colorsys
import random
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

HOST = "kraska"                      # the block that becomes a painted wall: class="kraska kraska--day|night"
PAINT = "kraska__paint"              # class of the host's numeral: the cream coat
ASSET_DIR = ("assets", "kraska")     # dist/assets/kraska/, kraska.css points at /assets/kraska/<file>
SEED = 2011                          # the year the workshop opened: the same wall on every build

# ---------- the wall, in CSS px at --kr-scale: 1 ----------
# a Russian brick is 250 × 65 mm with 10–12 mm joints; kraska.css repeats the module tiles at the same scale
BRICK_W, BRICK_H, JOINT = 68, 18, 4
MODULE, COURSE = BRICK_W + JOINT, BRICK_H + JOINT          # 72 × 22: one brick and its joints
DAY_TILE = (13, 16)                  # bricks × courses: 936 × 352, larger than the biggest card, so it never repeats
NIGHT_TILE = (8, 12)                 # 576 × 264 (× 1.25 in the hero: 720 × 330, larger than the ticket)
WEAR_TILE = (480, 300)               # the noise of the flakes, in CSS px (the stitched tile repeats unseen)
MORTAR = "#c4bcaf"                   # white-grey joints, weathered


class Coat(NamedTuple):
    flakes: float                    # the coat has flaked off where its flake noise is above this
    pits: float                      # … and is thin in the pores where the fine noise is above this
    fade: tuple[float, float]        # alpha where the coat is thinnest … where it is whole
    seed: int                        # its own pits and fading (and its own part of the flake noise)
    shared: float                    # how much of its flake noise is the one shared by all coats (1: all, 0: none)


# Thresholds are values of fractalNoise, measured in Chromium: median 0.50, 10 % of the values above 0.65, 5 % above
# 0.70, 1 % above 0.77 (the same for every frequency used here); a blend of 0.7 shared + 0.3 own noise is narrower:
# 5 % above 0.65, 1 % above 0.71. The black mostly flakes where the cream did (so a flake in the cream shows the black
# and its deepest part goes down to the brick), but not along the same outline; the old green flaked on its own,
# long before the black was painted over it.
# How much paint the joints kept is the joint map (joints.svg) plus a floor per coat in kraska.css (the solid layer
# of its mask: 0.45 cream, 0.8 black, 0.35 green).
COATS = {
    "paint": Coat(0.665, 0.70, (0.42, 0.88), 31, 1.0),   # cream numerals: thin, dry-brushed, faded in streaks
    "field": Coat(0.670, 0.74, (0.84, 0.97), 47, 0.7),   # the black field: thick paint, a few deep flakes
    "green": Coat(0.540, 0.72, (0.75, 0.95), 59, 0.0),   # the old green: patches left in the flakes of black
}
JOINT_MAP_TILE = (9, 16)             # bricks × courses of the joint map: 648 × 352
FLAKE_FREQ, FLAKE_OCTAVES = 0.03, 4           # flakes 3–30 px across
PIT_FREQ, PIT_LEFT = 0.62, 0.5                # pores of 1–3 px, where the brush left half of the paint
STREAK_FREQ = (0.028, 0.0045)                 # thinner paint in streaks: narrow across, long down the wall


def _hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


def _num(v: float) -> str:
    """Compact coordinates: one decimal, no trailing zeros ("12", "3.5", "-0.8")."""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _svg(w: int, h: int, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f"{body}</svg>\n")


def _ramp(threshold: float, softness: float = 0.035, above: bool = False) -> str:
    """feColorMatrix alpha row that reads the noise from R: 1 where it is below the threshold (or above it, with
    above=True), 0 on the other side, a soft edge `softness` wide in between."""
    k = 1 / softness
    if above:
        return f"{k:.2f} 0 0 0 {0.5 - k * threshold:.3f}"
    return f"{-k:.2f} 0 0 0 {0.5 + k * threshold:.3f}"


# ---------- bricks ----------
def _palette(rng: random.Random) -> list[tuple[str, int]]:
    """Brick colours of the facade: mostly orange-red around the measured #b5553a, some burnt darker,
    a few pale and a few weathered to grey-brown. [(colour, weight)]"""
    kinds = (   # (count, weight, hue, saturation, lightness ranges)
        (8, 9, (9, 15), (0.44, 0.55), (0.39, 0.47)),
        (3, 5, (7, 11), (0.38, 0.48), (0.29, 0.35)),
        (2, 4, (14, 19), (0.48, 0.58), (0.48, 0.53)),
        (2, 3, (12, 20), (0.18, 0.28), (0.38, 0.44)),
    )
    return [(_hex(rng.uniform(*h), rng.uniform(*s), rng.uniform(*l)), weight)
            for count, weight, h, s, l in kinds for _ in range(count)]


def _brick_path(x: float, y: float, rng: random.Random) -> str:
    """A brick face with worn arrises: corners knocked off by up to 2.4 px and the long edges a little uneven,
    all inside the brick, so the joints keep their width."""
    cut = [rng.choice((0.0, rng.uniform(0.5, 1.3), rng.uniform(0.9, 2.4))) for _ in range(4)]   # tl, tr, br, bl
    x1, y1 = x + BRICK_W, y + BRICK_H
    top = rng.uniform(0, 0.7)            # a worn stretch of the top arris
    bottom = rng.uniform(0, 0.6)
    mid = x + rng.uniform(0.25, 0.75) * BRICK_W
    pts = [(x + cut[0], y), (mid, y + top), (x1 - cut[1], y), (x1, y + cut[1]), (x1, y1 - cut[2]),
           (x1 - cut[2], y1), (mid, y1 - bottom), (x + cut[3], y1), (x, y1 - cut[3]), (x, y + cut[0])]
    out = []
    for p in pts:
        if not out or p != out[-1]:
            out.append(p)
    if out[0] == out[-1]:
        out.pop()
    return "M" + "L".join(f"{_num(px)} {_num(py)}" for px, py in out) + "Z"


def _courses(cols: int, rows: int) -> Iterator[tuple[int, int, int | None]]:
    """(x, y, x of the wrapped copy or None) of every brick of a tile in running bond; the brick that crosses the
    right edge of a shifted course is drawn again at the left edge (same colour and shape): the tile has no seam."""
    width = cols * MODULE
    for r in range(rows):
        shift = 0 if r % 2 == 0 else -(MODULE // 2)
        for c in range(cols + (1 if shift else 0)):
            x = c * MODULE + shift
            if x < 0:
                continue
            yield x, r * COURSE, (x - width if x + BRICK_W > width else None)


def _mark(x: float, y: float, w: float, h: float) -> str:
    """A rectangle 0.8 px inside the brick outline (burnt end, limewash)."""
    return f"M{_num(x + 0.8)} {_num(y + 0.8)}h{_num(w - 1.6)}v{_num(h - 1.6)}h{_num(1.6 - w)}z"


def brick_svg(cols: int, rows: int, seed: int) -> str:
    """The wall tile: mortar, every brick in its own colour (bricks of one colour share a path), burnt ends and
    limewash on some of them, and a mottled face clipped to the bricks."""
    rng = random.Random(seed)
    palette = _palette(rng)
    colours, weights = [c for c, _ in palette], [w for _, w in palette]
    faces = {c: [] for c in colours}
    burnt, lime = [], []
    for x, y, wrap_x in _courses(cols, rows):
        colour = rng.choices(colours, weights)[0]
        shape = rng.getstate()
        faces[colour].append(_brick_path(x, y, rng))
        marks = []
        roll = rng.random()
        if roll < 0.16:      # a burnt end: the side of the brick that was nearest the fire in the kiln
            part = BRICK_W * rng.uniform(0.18, 0.4)
            marks.append((burnt, x if rng.random() < 0.5 else x + BRICK_W - part, y, part, BRICK_H))
        elif roll < 0.26:    # traces of old limewash, like on the bricks of the facade
            part, tall = BRICK_W * rng.uniform(0.2, 0.55), BRICK_H * rng.uniform(0.35, 0.7)
            marks.append((lime, x + rng.uniform(0, BRICK_W - part), y + BRICK_H - tall, part, tall))
        for target, mx, my, mw, mh in marks:
            target.append(_mark(mx, my, mw, mh))
        if wrap_x is not None:   # the same brick again at the left edge of the tile
            after = rng.getstate()
            rng.setstate(shape)
            faces[colour].append(_brick_path(wrap_x, y, rng))
            rng.setstate(after)
            for target, mx, my, mw, mh in marks:
                target.append(_mark(mx - x + wrap_x, my, mw, mh))
    w, h = cols * MODULE, rows * COURSE
    used = [(i, c, d) for i, (c, d) in enumerate(faces.items()) if d]
    body = [f'<rect width="{w}" height="{h}" fill="{MORTAR}"/>']
    body += [f'<path id="f{i}" fill="{c}" d="{"".join(d)}"/>' for i, c, d in used]
    if burnt:
        body.append(f'<path fill="#2b0e06" fill-opacity=".2" d="{"".join(burnt)}"/>')
    if lime:
        body.append(f'<path fill="#efe9de" fill-opacity=".22" d="{"".join(lime)}"/>')
    # the face of a hand-made brick is not flat: darker and lighter blotches, only on the bricks (clipped to them)
    clip = "".join(f'<use href="#f{i}"/>' for i, _c, _d in used)
    body.append(
        f'<clipPath id="c">{clip}</clipPath>'
        f'<filter id="m" x="0" y="0" width="{w}" height="{h}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">'
        f'<feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="3" seed="{seed}" stitchTiles="stitch" result="n"/>'
        '<feColorMatrix in="n" values="0 0 0 0 .16  0 0 0 0 .06  0 0 0 0 .03  -2.4 0 0 0 1.08" result="dark"/>'
        '<feColorMatrix in="n" values="0 0 0 0 1  0 0 0 0 .86  0 0 0 0 .74  0 1.6 0 0 -.9" result="light"/>'
        '<feMerge><feMergeNode in="dark"/><feMergeNode in="light"/></feMerge></filter>'
        f'<rect width="{w}" height="{h}" clip-path="url(#c)" filter="url(#m)"/>')
    return _svg(w, h, "".join(body))


# ---------- the module tiles: one pair of courses (72 × 44), repeated over the whole wall ----------
def _module_bricks() -> list[tuple[int, int, int, bool, bool]]:
    """Brick faces of one pair of courses, clipped to the tile: [(x0, x1, y0, real left end, real right end)].
    In the shifted course one brick runs across the tile edge: its two pieces have no end at the edge."""
    half = MODULE // 2
    return [(0, BRICK_W, 0, True, True), (0, half - JOINT, COURSE, False, True), (half, MODULE, COURSE, True, False)]


def relief_svg() -> str:
    """Light from above: the top arris of a brick catches it, its face darkens towards the bottom, the brick above
    throws a shadow into the bed joint, the head joints are shaded on one side. It lies over the paint as well."""
    lit, faces, bed = [], [], []
    for x0, x1, y0, left_end, right_end in _module_bricks():
        a, b = x0 + (0.8 if left_end else 0), x1 - (0.8 if right_end else 0)
        lit.append(f"M{_num(a)} {_num(y0 + 0.7)}H{_num(b)}")
        faces.append(f"M{x0} {y0}h{x1 - x0}v{BRICK_H}h{x0 - x1}z")
        bed.append(f"M{x0} {y0 + BRICK_H}h{x1 - x0}v1.6h{x0 - x1}z")
    head = f"M{BRICK_W} 0h1.2v{BRICK_H}h-1.2zM{MODULE // 2 - JOINT} {COURSE}h1.2v{BRICK_H}h-1.2z"
    body = ('<linearGradient id="s" x1="0" y1="0" x2="0" y2="22" gradientUnits="userSpaceOnUse" spreadMethod="repeat">'
            '<stop offset="0" stop-color="#fff" stop-opacity=".05"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset=".8" stop-color="#1c0c06" stop-opacity=".1"/><stop offset="1" stop-color="#1c0c06" stop-opacity=".18"/>'
            '</linearGradient>'
            f'<path fill="url(#s)" d="{"".join(faces)}"/>'
            f'<path fill="#1c0c06" fill-opacity=".3" d="{"".join(bed)}{head}"/>'
            f'<path fill="none" stroke="#fff3e2" stroke-opacity=".09" stroke-width="1.4" d="{"".join(lit)}"/>')
    return _svg(MODULE, 2 * COURSE, body)


def joint_map_svg(cols: int, rows: int, seed: int) -> str:
    """Paint mask shared by the coats: how much paint each part of the wall kept. The faces of the bricks hold nearly
    all of it (each brick a little differently), every stretch of joint lost a different part of it — from nothing to
    all. kraska.css adds a floor per coat to it, so the black keeps more of its paint in the joints than the cream."""
    rng = random.Random(seed)
    face_levels, joint_levels = (1.0, 0.95, 0.9, 0.84), (0.0, 0.3, 0.6, 0.85)
    faces = {a: [] for a in face_levels}
    joints = {a: [] for a in joint_levels}
    for x, y, wrap_x in _courses(cols, rows):
        face, head, bed = rng.choice(face_levels), rng.choice(joint_levels), rng.choice(joint_levels)
        for bx in (x,) if wrap_x is None else (x, wrap_x):
            faces[face].append(f"M{bx} {y}h{BRICK_W}v{BRICK_H}h-{BRICK_W}z")
            joints[head].append(f"M{bx + BRICK_W} {y}h{JOINT}v{BRICK_H}h-{JOINT}z")
            joints[bed].append(f"M{bx} {y + BRICK_H}h{MODULE}v{JOINT}h-{MODULE}z")
    body = "".join(f'<path fill-opacity="{a:g}" d="{"".join(d)}"/>'
                   for a, d in (*faces.items(), *joints.items()) if d and a > 0)
    return _svg(cols * MODULE, rows * COURSE, body)


def grain_svg() -> str:
    """The porous surface of brick, mortar and paint alike: dark pits where dirt collected, in patches rather than
    evenly (256 px tile)."""
    return _svg(256, 256, (
        '<filter id="g" x="0" y="0" width="256" height="256" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">'
        '<feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="2" seed="7" stitchTiles="stitch" result="n"/>'
        f'<feColorMatrix in="n" values="0 0 0 0 .1  0 0 0 0 .05  0 0 0 0 .03  {_ramp(0.28, 0.05)}" result="pits"/>'
        '<feTurbulence type="fractalNoise" baseFrequency=".035" numOctaves="2" seed="8" stitchTiles="stitch" result="c"/>'
        f'<feColorMatrix in="c" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  {_ramp(0.56, 0.1, above=True)}" result="patches"/>'
        '<feComposite in="pits" in2="patches" operator="in" result="dirt"/>'
        '<feComponentTransfer in="dirt"><feFuncA type="linear" slope=".36"/></feComponentTransfer></filter>'
        '<rect width="256" height="256" filter="url(#g)"/>'))


def _flake_noise(c: Coat) -> tuple[str, str]:
    """(filter primitives, name of the result) of the coat's flake noise: the noise shared by all coats, a noise of its
    own, or a blend of both. To blend, each noise is made opaque first, so the values blend (not values × alpha);
    a single noise is read as it is (feColorMatrix un-premultiplies its input, which gives the same values)."""
    def turbulence(seed: int, name: str) -> str:
        return (f'<feTurbulence type="fractalNoise" baseFrequency="{FLAKE_FREQ}" numOctaves="{FLAKE_OCTAVES}" '
                f'seed="{seed}" stitchTiles="stitch" result="{name}"/>')

    if c.shared >= 1:
        return turbulence(SEED, "n"), "n"
    if c.shared <= 0:
        return turbulence(c.seed + 3, "n"), "n"
    opaque = "1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0 1"
    return (turbulence(SEED, "a0") + f'<feColorMatrix in="a0" values="{opaque}" result="a"/>'
            + turbulence(c.seed + 3, "b0") + f'<feColorMatrix in="b0" values="{opaque}" result="b"/>'
            + f'<feComposite in="a" in2="b" operator="arithmetic" k2="{c.shared:g}" k3="{1 - c.shared:g}" result="n"/>'), "n"


def wear_svg(coat: str) -> str:
    """Paint mask of a coat: flakes × fading, minus the pits. The cream and the black use the same flake noise (seed,
    frequency, tile), only the threshold differs, so a flake in the cream goes down through the black. The pits are
    only where the coat is thin (the streaks of the fading), so they gather in weathered patches instead of peppering
    it evenly. The graph is kept short: the browser evaluates it once per image, each result a texture of tile size."""
    c = COATS[coat]
    w, h = WEAR_TILE
    fx, fy = STREAK_FREQ
    thin, full = c.fade
    noise, n = _flake_noise(c)
    # the streak noise (10–90 % of its values between 0.35 and 0.65) mapped linearly onto thin … full
    slope = (full - thin) / 0.3
    return _svg(w, h, (
        f'<filter id="w" x="0" y="0" width="{w}" height="{h}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB">'
        f'{noise}<feColorMatrix in="{n}" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  {_ramp(c.flakes)}" result="flakes"/>'
        f'<feTurbulence type="fractalNoise" baseFrequency="{fx} {fy}" numOctaves="3" seed="{c.seed + 1}" stitchTiles="stitch" result="s"/>'
        f'<feColorMatrix in="s" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  {slope:.3f} 0 0 0 {thin - 0.35 * slope:.3f}" result="fade"/>'
        '<feComposite in="flakes" in2="fade" operator="in" result="paint"/>'
        f'<feColorMatrix in="s" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  {_ramp(0.47, 0.1)}" result="weathered"/>'
        f'<feTurbulence type="fractalNoise" baseFrequency="{PIT_FREQ}" numOctaves="2" seed="{c.seed}" stitchTiles="stitch" result="p"/>'
        f'<feColorMatrix in="p" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  {_ramp(c.pits, 0.05, above=True)}" result="pores"/>'
        f'<feComposite in="pores" in2="weathered" operator="arithmetic" k1="{1 - PIT_LEFT:g}" result="holes"/>'
        '<feComposite in="paint" in2="holes" operator="out"/></filter>'
        f'<rect width="{w}" height="{h}" filter="url(#w)"/>'))


def brush_svg(seed: int) -> str:
    """Mask of the one-time reveal: the front of a dry brush. Opaque on the left half, then 40 bristle streaks of
    different lengths, transparent after them. kraska.css stretches it to 16 em × the height of the host and moves the
    front across the numeral once, left to right; 16 em is wider than any host, so the mask covers the whole host at
    every moment (WebKit leaves the area outside a non-repeating mask layer uncomposited)."""
    rng = random.Random(seed)
    bands, rows = [], 40
    for i in range(rows):
        end = 800 + rng.uniform(4, 60) * (0.55 + 0.45 * rng.random())
        bands.append(f"M0 {i * 2.5:g}H{_num(end)}v2.5H0z")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="100" viewBox="0 0 1600 100" '
            f'preserveAspectRatio="none"><path d="{"".join(bands)}"/></svg>\n')


def assets() -> dict[str, str]:
    """{file name: SVG} of everything kraska.css uses."""
    files = {
        "brick-day.svg": brick_svg(*DAY_TILE, SEED),
        "brick-night.svg": brick_svg(*NIGHT_TILE, SEED + 1),
        "relief.svg": relief_svg(),
        "grain.svg": grain_svg(),
        "joints.svg": joint_map_svg(*JOINT_MAP_TILE, SEED + 2),
        "brush.svg": brush_svg(SEED + 3),
    }
    for name in COATS:
        files[f"wear-{name}.svg"] = wear_svg(name)
    return files


def write_assets(dist: Path) -> int:
    """Writes the SVG files into dist/assets/kraska/; returns their total size in bytes."""
    out = dist.joinpath(*ASSET_DIR)
    out.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, svg in assets().items():
        (out / name).write_text(svg, encoding="utf-8")
        total += len(svg.encode("utf-8"))
    return total


def layers(night: bool = False) -> str:
    """The paint and the surface of the wall inside a host (decorative, hidden from screen readers): the old green,
    the black field, the relief over the paint and, in the dark hero, the light of the lamp above."""
    light = '<span class="kraska__light"></span>' if night else ""
    return ('<span class="kraska__wall" aria-hidden="true"><span class="kraska__green"></span>'
            f'<span class="kraska__field"></span><span class="kraska__relief"></span>{light}</span>')
