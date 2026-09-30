# -*- coding: utf-8 -*-
"""«Ворота»: the contacts scene of the homepage.

The real facade at dusk: the sign over the gate lights up, the roller shutter in the black portal rolls up as the page
scrolls, the camera walks through the gate into the workshop. Two framings of the same place: the wide photo for
desktops, tablets and phones in landscape, the tall one for phones held upright (<picture> + the same media query
in vorota.css).

Everything drawn over a photo (shutter, dusk, sign light) is positioned from the pixel coordinates below, measured on
the original JPEGs, and rendered in % of a box that has the photo's own aspect ratio — so it stays glued to the gate
at every screen width. Animation: src/assets/js/vorota.js; styles: src/assets/css/vorota.css.
"""
from . import data as D
from .icons import icon

esc = D.esc

TALL_MEDIA = "(max-width: 700px) and (orientation: portrait)"  # same query as the tall framing in vorota.css

# Pixel coordinates on the original photos (src/assets/img/real/*.jpg).
# opening — the gate opening right under the roller housing (TL, TR, BR, BL; the right jamb leans a little);
# sign — the «GARAGE TEAM · car service» board, its left edge follows the rounded «G».
GATE_ART = {
    "wide": {
        "photo": "facade-wide", "size": (2400, 1800), "widths": (800, 1600),
        "opening": [(1352, 968), (2090, 968), (2110, 1562), (1352, 1548)],
        "sign": [(1440, 822), (1440, 765), (1442, 735), (1446, 710), (1452, 690), (1462, 677), (1947, 628), (1928, 778)],
    },
    "tall": {
        "photo": "facade-sky", "size": (1800, 2400), "widths": (800, 1200),
        "opening": [(825, 1598), (1548, 1598), (1570, 2255), (825, 2245)],
        "sign": [(919, 1452), (919, 1390), (920, 1370), (922, 1350), (926, 1330), (932, 1312), (940, 1304), (1390, 1275), (1381, 1426)],
    },
}
PHOTO_ALT = ("Фасад автосервиса «Гараж»: старое здание из красного кирпича, въезд в мастерскую в чёрном портале "
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


def gate_scene(route):
    wide, tall = GATE_ART["wide"], GATE_ART["tall"]
    hours = "Пн–Пт 9–19 · Сб 9–17"
    return f"""<div class="gate" data-gate>
    <div class="gate__stage">
      <div class="gate__world">
        <picture>
          <source media="{TALL_MEDIA}" srcset="{_srcset(tall['photo'], tall['widths'])}" sizes="140vw" width="{tall['widths'][1]}" height="{tall['widths'][1] * 4 // 3}">
          <img class="gate__photo" src="/assets/img/real/{wide['photo']}.webp" srcset="{_srcset(wide['photo'], wide['widths'])}" sizes="(orientation: portrait) 170vw, 100vw" width="1600" height="1200" alt="{esc(PHOTO_ALT)}" loading="lazy" decoding="async">
        </picture>
        {_art("wide")}
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
          <p class="gate__addr"><b>ул. Красная слобода, 9</b><span class="mono">{hours}</span></p>
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
