# -*- coding: utf-8 -*-
"""«Свет ламп»: the first screen as the office of the real workshop — a dark red-brick wall, two black enamel
dome pendants that light it, and between them the «GARAGE TEAM» neon sign from the end of the workshop hall.

    wall()   decorative layers inside .hero__bg: the brick photo, the light pools under the lamps, the shade that keeps
             the headline readable, the night / hand-lamp layers of the dark room and the glow of the neon
    room()   the lamps (real toggle buttons) and the neon sign
    mini()   the same pendant, small, over the «Приезжайте в Гараж» heading: it lights up when the heading scrolls in

Behaviour is in src/assets/js/svet.js, styles in src/assets/css/svet.css. Without JavaScript the room is simply lit.
"""
import re
from pathlib import Path

from . import data as D

esc = D.esc
ROOT = Path(__file__).resolve().parent.parent

# lamp i hangs at --x % of the hero width; the pool of light on the wall below it has the same index
LAMPS = 2


def _lamp_symbol():
    """The pendant from the office photos: a short neck, a collar, a black enamel bell with a soft sheen,
    a thin metal lip and the diffuser seen from below. 104 × 92, the lit diffuser is an HTML layer on top."""
    return """<defs>
    <linearGradient id="svet-enamel" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#151616"/><stop offset=".17" stop-color="#454747"/><stop offset=".31" stop-color="#171818"/>
      <stop offset=".78" stop-color="#0b0c0c"/><stop offset=".95" stop-color="#232424"/><stop offset="1" stop-color="#121313"/>
    </linearGradient>
    <linearGradient id="svet-neck" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#1a1b1b"/><stop offset=".3" stop-color="#3a3c3c"/><stop offset=".55" stop-color="#121313"/><stop offset="1" stop-color="#0c0d0d"/>
    </linearGradient>
</defs>
<symbol id="svet-lamp" viewBox="0 0 104 92">
  <rect x="35.5" y="0" width="33" height="19" rx="3" fill="url(#svet-neck)"/>
  <rect x="30.5" y="16.5" width="43" height="6" rx="2" fill="#0e0f0f" stroke="rgba(255,255,255,.16)" stroke-width=".6"/>
  <path d="M34 23C19 25 11 35 9.5 49L4 85h96L94.5 49C93 35 85 25 70 23z" fill="url(#svet-enamel)"/>
  <path d="M34 23C19 25 11 35 9.5 49L4 85" fill="none" stroke="rgba(255,255,255,.1)" stroke-width=".8"/>
  <rect x="49.5" y="73" width="5" height="7" rx=".8" fill="#6e716d"/>
  <ellipse cx="52" cy="85.6" rx="48.4" ry="5.6" fill="#9a9d98"/>
  <ellipse cx="52" cy="86.1" rx="46.4" ry="4.6" fill="#35302a"/>
</symbol>"""


# ---------- the neon sign: the tubes follow the logo's own outlines (src/assets/logo/logo.svg) ----------
# The logo is a PDF export: the letters exist only as clip paths. These are the inner letter shapes the tubes trace:
# G A R A G E, T E A M, the bar over GARAGE and the bar under it.
_LETTER_CLIPS = (30, 32, 50, 34, 36, 38, 48, 40, 42, 44, 28, 46)


def _neon_paths():
    svg = (ROOT / "src" / "assets" / "logo" / "logo.svg").read_text(encoding="utf-8")
    clips = dict(re.findall(r'<clipPath id="clip-(\d+)"><path[^>]* d="([^"]+)"', svg))
    body = svg.split("</defs>", 1)[-1]
    drawn = re.findall(r'<path([^>]*)/>', body)

    def d_of(attrs):
        return re.search(r' d="([^"]+)"', attrs).group(1).strip()

    try:
        letters = [clips[str(i)].strip() for i in _LETTER_CLIPS]
        frame = next(d_of(a) for a in drawn if 'fill="rgb(0%, 0%, 0%)"' in a)
        # «CAR SERVICE» is the long green path on the left; the other green paths are the ® mark at the right edge
        script = next(d_of(a) for a in drawn if "39.61%" in a and float(re.search(r' d="M ([\d.]+)', a).group(1)) < 400)
    except (KeyError, StopIteration, AttributeError) as exc:
        raise SystemExit(f"svet: в logo.svg не нашлись контуры для неоновой вывески ({exc})")
    return letters, frame, script


def _neon():
    letters, frame, script = _neon_paths()
    tubes = "".join(f'<path d="{d}"/>' for d in letters)
    # every tube is drawn three times — a wide faint halo, a glow and the bright core — instead of a blur filter
    return f"""<svg class="svet-neon" viewBox="92 358 396 138" aria-hidden="true" focusable="false">
  <defs>
    <g id="svet-neon-white" fill="none" stroke-linejoin="round">{tubes}</g>
    <g id="svet-neon-mint" fill="none" stroke-linejoin="round"><path d="{frame}"/></g>
    <path id="svet-neon-script" d="{script}"/>
  </defs>
  <g class="svet-neon__glass">
    <use href="#svet-neon-mint" stroke="rgba(170,255,228,.13)" stroke-width="2"/>
    <use href="#svet-neon-white" stroke="rgba(255,248,240,.14)" stroke-width="2"/>
    <use href="#svet-neon-script" fill="rgba(170,255,228,.1)"/>
  </g>
  <g class="svet-neon__lit">
    <use href="#svet-neon-mint" stroke="rgba(52,232,184,.13)" stroke-width="13"/>
    <use href="#svet-neon-white" stroke="rgba(190,255,236,.10)" stroke-width="11"/>
    <use href="#svet-neon-mint" stroke="rgba(64,240,192,.38)" stroke-width="5.5"/>
    <use href="#svet-neon-white" stroke="rgba(214,255,243,.34)" stroke-width="5"/>
    <use href="#svet-neon-script" fill="#58f2c9" stroke="rgba(64,240,192,.35)" stroke-width="4"/>
    <use href="#svet-neon-mint" stroke="#8dffe0" stroke-width="2.2"/>
    <use href="#svet-neon-white" stroke="#f6fffb" stroke-width="2.2"/>
  </g>
</svg>"""


def wall():
    pools = "".join(f'<div class="svet-pool svet-pool--{i + 1}" data-svet-pool style="--i:{i}"><i></i></div>' for i in range(LAMPS))
    return f"""<div class="svet-wall">
      <div class="svet-wall__brick"></div>
      <div class="svet-wall__shade"></div>
      {pools}
      <div class="svet-wall__scrim"></div>
      <div class="svet-wall__night"></div>
      <canvas class="svet-wall__torch" width="512" height="512"></canvas>
      <div class="svet-wall__neon"></div>
    </div>"""


def room():
    lamps = "".join(
        f"""<div class="svet-lamp svet-lamp--{i + 1}" data-svet-lamp style="--i:{i}">
        <span class="svet-lamp__cord"></span>
        <span class="svet-lamp__cone"></span>
        <button class="svet-lamp__btn" type="button" aria-pressed="true" aria-label="Лампа {i + 1}">
          <svg class="svet-lamp__body" viewBox="0 0 104 92" aria-hidden="true" focusable="false"><use href="#svet-lamp"/></svg>
          <span class="svet-lamp__bulb"></span><span class="svet-lamp__bloom"></span>
        </button>
      </div>"""
        for i in range(LAMPS)
    )
    return f"""<div class="svet-room" data-svet role="group" aria-label="Свет в офисе">
    <svg class="sprite" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">{_lamp_symbol()}</svg>
    <div class="svet-sign">{_neon()}</div>
    {lamps}
    <p class="sr-only" data-svet-status aria-live="polite"></p>
  </div>"""


def mini():
    """Decorative: hangs from the top edge of the contacts section; svet.css switches it on with the .reveal of its block."""
    return """<div class="svet-mini" aria-hidden="true">
        <span class="svet-lamp__cord"></span>
        <span class="svet-mini__glow"></span>
        <svg class="svet-mini__body" viewBox="0 0 104 92" focusable="false"><use href="#svet-lamp"/></svg>
        <span class="svet-lamp__bulb"></span>
      </div>"""
