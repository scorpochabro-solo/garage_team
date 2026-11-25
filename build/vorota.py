# -*- coding: utf-8 -*-
"""«Ворота»: the contacts scene of the homepage.

The real facade at dusk: the sign over the gate lights up, the roller shutter in the black portal rolls up as the page
scrolls, the camera walks through the gate into the workshop. Three framings of the November facade shoot share breakpoints with vorota.css.

Everything drawn over a photo (shutter, dusk, sign light) is positioned from the pixel coordinates below, measured on
the original JPEGs, and rendered in % of a box that has the photo's own aspect ratio — so it stays glued to the gate
at every screen width. Animation: src/assets/js/vorota.js; styles: src/assets/css/vorota.css.
"""
from . import data as D
from .icons import icon

esc = D.esc

TALL_MEDIA = "(max-width: 700px) and (orientation: portrait)"  # same query as the tall framing in vorota.css

# Coordinates measured on proportionally scaled crops of the three camera frames.
GATE_ART = {
    "wide": {
        "photo": "arrival-wide", "size": (678, 381), "widths": (800, 1600),
        "opening": [(399, 156), (570, 160), (577, 321), (396, 326)],
        "sign": [(430, 144), (432, 118), (436, 108), (548, 110), (546, 146)],
    },
    "tablet": {
        "photo": "arrival-tablet", "size": (508, 381), "widths": (800, 1600),
        "opening": [(271, 159), (441, 163), (450, 322), (268, 328)],
        "sign": [(303, 144), (306, 117), (310, 108), (425, 111), (421, 147)],
    },
    "tall": {
        "photo": "arrival-tall", "size": (286, 381), "widths": (800, 1200),
        "opening": [(92, 186), (265, 190), (273, 351), (86, 359)],
        "sign": [(124, 171), (126, 147), (131, 136), (242, 140), (238, 175)],
    },
}
PHOTO_ALT = ("Фасад автосервиса «Гараж»: старое здание из красного кирпича, ворота в чёрном портале "
             "под вывеской Garage Team")
INSIDE_ALT = "Мастерская изнутри: подъёмники, стальные колонны и кирпичные стены, в глубине — светящаяся вывеска Garage Team"


def _pct(v, total):
    return f"{v / total * 100:.3f}%"


def _place(points, size):
    """Inline style for an element covering the bounding box of `points`: position in % of the photo box plus
    `--clip`, the polygon itself in % of that element."""
    (w, h), xs, ys = size, [p[0] for p in points], [p[1] for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    clip = ", ".join(f"{(x - x0) / (x1 - x0) * 100:.2f}% {(y - y0) / (y1 - y0) * 100:.2f}%" for x, y in points)
    return (f"left:{_pct(x0, w)};top:{_pct(y0, h)};width:{_pct(x1 - x0, w)};height:{_pct(y1 - y0, h)};"
            f"--clip:polygon({clip})")


def _spill(opening, size):
    """Light from the open gate on the ground: a trapezoid from the threshold to the bottom edge of the photo."""
    w, h = size
    (_, _), (_, _), (xr, yr), (xl, yl) = opening
    span = xr - xl
    return _place([(xl, yl), (xr, yr), (min(w, xr + span * 0.3), h), (max(0, xl - span * 0.3), h)], size)


def _glow(sign, size):
    """Halo of the lit sign: an ellipse around the board, twice as wide and three times as tall."""
    w, h = size
    xs, ys = [p[0] for p in sign], [p[1] for p in sign]
    cx, cy, bw, bh = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys)
    return f"left:{_pct(cx - bw, w)};top:{_pct(cy - bh * 1.5, h)};width:{_pct(bw * 2, w)};height:{_pct(bh * 3, h)}"


def _art(key):
    """Everything drawn over one framing of the facade: dusk (with holes for the gate and the sign), the sign light,
    the light on the ground and the shutter. aria-hidden: the photo's alt describes the place."""
    a = GATE_ART[key]
    w, h = a["size"]
    path = lambda pts: "M" + "L".join(f"{x} {y}" for x, y in pts) + "Z"  # noqa: E731
    grad = f"gate-dusk-{key}"
    return f"""<div class="gate__art gate__art--{key}" aria-hidden="true">
          <svg class="gate__dusk" viewBox="0 0 {w} {h}" preserveAspectRatio="none" focusable="false">
            <defs><linearGradient id="{grad}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{h}">
              <stop offset="0" stop-color="#06080c" stop-opacity=".86"/><stop offset=".3" stop-color="#07090c" stop-opacity=".64"/><stop offset="1" stop-color="#07090c" stop-opacity=".64"/>
            </linearGradient></defs>
            <path fill="url(#{grad})" fill-rule="evenodd" d="M0 0H{w}V{h}H0Z{path(a['opening'])}{path(a['sign'])}"/>
            <path class="gate__sign-dim" fill="url(#{grad})" d="{path(a['sign'])}"/>
            <path class="gate__sign-lit" d="{path(a['sign'])}"/>
          </svg>
          <i class="gate__glow" style="{_glow(a['sign'], a['size'])}"></i>
          <i class="gate__spill" style="{_spill(a['opening'], a['size'])}"></i>
          <div class="gate__opening" style="{_place(a['opening'], a['size'])}"><div class="gate__shutter" data-gate-shutter><i class="gate__bar"></i></div></div>
        </div>"""


def _srcset(name, widths):
    small, full = widths
    return f"/assets/img/real/{name}-{small}.webp {small}w, /assets/img/real/{name}.webp {full}w"


def gate_scene(route, hours=None):
    """route: href of «Схема проезда», already escaped; hours: markup of the line under the address
    (home.py passes the live status of «Открыто сейчас»), the plain hours by default."""
    wide, tablet, tall = (GATE_ART[key] for key in ("wide", "tablet", "tall"))
    hours = hours or '<span class="mono">Пн–Пт 9–19 · Сб 9–17</span>'
    return f"""<div class="gate" data-gate>
    <div class="gate__stage">
      <div class="gate__world">
        <picture>
          <source media="{TALL_MEDIA}" srcset="{_srcset(tall['photo'], tall['widths'])}" sizes="140vw" width="{tall['widths'][1]}" height="{tall['widths'][1] * 4 // 3}">
          <source media="(max-width: 1050px)" srcset="{_srcset(tablet['photo'], tablet['widths'])}" sizes="(orientation: portrait) 170vw, 100vw" width="1600" height="1200">
          <img class="gate__photo" src="/assets/img/real/{wide['photo']}.webp" srcset="{_srcset(wide['photo'], wide['widths'])}" sizes="(orientation: portrait) 170vw, 100vw" width="1600" height="900" alt="{esc(PHOTO_ALT)}" loading="lazy" decoding="async">
        </picture>
        {_art("wide")}
        {_art("tablet")}
        {_art("tall")}
      </div>
      <div class="gate__inside">
        <img src="/assets/img/real/workshop.webp" srcset="{_srcset('workshop', (800, 1600))}" sizes="{TALL_MEDIA} 250vw, (orientation: portrait) 170vw, 100vw" width="1600" height="1200" alt="{esc(INSIDE_ALT)}" loading="lazy" decoding="async">
      </div>
      <div class="gate__veil" aria-hidden="true"></div>
      <div class="gate__copy">
        <div class="wrap">
          <p class="eyebrow">// 06 — Контакты</p>
          <h2 class="h2 sec-head__title" id="contacts-title">Приезжайте<br>в Гараж</h2>
          <p class="gate__addr"><b>ул. Красная слобода, 9</b>{hours}</p>
          <a class="btn btn--primary gate__route" href="{route}" target="_blank" rel="noopener">{icon('pin')} Схема проезда</a>
        </div>
      </div>
      <div class="gate__remote" data-gate-remote hidden>
        <span class="gate__remote-label mono">Ворота</span>
        <span class="gate__remote-meter" aria-hidden="true"><i data-gate-meter></i></span>
        <span class="gate__remote-value mono" data-gate-value aria-hidden="true">0%</span>
        <button class="gate__remote-btn" type="button" data-gate-toggle aria-label="Открыть ворота">{icon('chevron')}</button>
      </div>
    </div>
  </div>"""
