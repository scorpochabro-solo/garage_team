# -*- coding: utf-8 -*-
"""«Арки»: the arched windows and doorways of the real building (ул. Красная слобода, 9) as a design motif.

  inside_section()  «Как у нас» — four real photos framed as arched windows: black steel frame, a fan-light
                    with radial bars like the office windows, a brick arch ring drawn around each opening
  door()            the facade photo as an arched doorway in the contacts block
  wall()            the brick arch ring, jambs and sill around an opening (also around the director's portrait)

Geometry: every opening is a true semicircle on top of a rectangle (border-radius 999px 999px 0 0 makes the radius
exactly half the width). The ring and the fan-light are drawn in a coordinate system where the window radius is 100,
positioned in % of the opening's width, so they stay concentric at any size (see src/assets/css/arki.css).
"""
import math
import re

from . import data as D

esc = D.esc
_SHORT = re.compile(r"(?<![\w-])([А-Яа-яЁё]{1,2}) ")


def nb(text):
    """Escaped text with a no-break space after one- and two-letter words, so «в», «с», «на» never end a line."""
    return _SHORT.sub("\\1\u00a0", esc(text))


# the window radius is 100; the brick ring sits 6 units off the frame and is 14 units deep (arki.css: jambs at 3% and 10%)
RING_IN, RING_OUT, RING_JOINTS = 106, 120, 25

# (photo for the lightbox, arch crop, alt, label, caption) — captions only name what is visible in the photo
INSIDE = [
    ("workshop", "workshop", "Ремонтный зал автосервиса Гараж: стальные колонны, балки перекрытия и подъёмники",
     "Ремонтный зал", "Стальные колонны и балки, кирпич в глубине зала"),
    ("office-arches", "office", "Офис автосервиса Гараж: арочные окна в кирпичной стене и чёрные лампы-купола над столами",
     "Офис", "Арочные окна и лампы-купола над столами"),
    ("office-niche-lamps", "niche", "Ниша в кирпичной стене с автомобильными мелочами",
     "Ниша в стене", "Кирпичная кладка, в нише\u00a0— автомобильные мелочи"),
    ("v8-table", "v8", "Журнальный столик со стеклянной столешницей на блоке двигателя V8",
     "Столик V8", "Стеклянная столешница на блоке двигателя с поршнями"),
]


def ring_svg(cls="arch__ring"):
    """Brick arch ring: two arcs and radial joints between them, viewBox centred on the spring line."""
    r0, r1, n = RING_IN, RING_OUT, RING_JOINTS
    joints = []
    for k in range(1, n):
        a = math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        joints.append(f"M{-c * r0:.2f} {-s * r0:.2f}L{-c * r1:.2f} {-s * r1:.2f}")
    d = f"M{-r1} 0A{r1} {r1} 0 0 1 {r1} 0M{-r0} 0A{r0} {r0} 0 0 1 {r0} 0" + "".join(joints)
    w = r1 + 2
    return (f'<svg class="{cls}" viewBox="{-w} {-w} {2 * w} {w}" aria-hidden="true" focusable="false">'
            f'<path d="{d}"/></svg>')


def wall():
    """The wall around an opening: the ring as SVG, the jambs and the sill as the span's ::before/::after."""
    return f'<span class="arch__wall" aria-hidden="true">{ring_svg()}</span>'


def _bars_svg():
    """Fan-light of the office windows: a transom on the spring line and three radial bars (45°, 90°, 135°)."""
    k = 100 - 100 * math.cos(math.pi / 4)
    return ('<svg class="arch__bars" viewBox="0 0 200 100" aria-hidden="true" focusable="false">'
            f'<path d="M-4 100H204M100 100V-4M100 100L{k:.2f} {k:.2f}M100 100L{200 - k:.2f} {k:.2f}"/></svg>')


def _arch(i, full, crop, alt, label, caption):
    return f"""<figure class="arch" style="--i:{i}">
        <div class="arch__opening">
          <span class="arch__glow" aria-hidden="true"></span>
          {wall()}
          <a class="arch__win" href="/assets/img/real/{full}.webp" data-lightbox="inside">
            <img class="arch__img" src="/assets/img/real/arch/{crop}.webp" alt="{esc(alt)}" width="640" height="1120" loading="lazy" decoding="async">
            <span class="arch__veil" aria-hidden="true"></span>
            {_bars_svg()}
          </a>
        </div>
        <figcaption class="arch__cap"><span class="arch__n">{i + 1:02d}</span><b>{nb(label)}</b><span>{nb(caption)}</span></figcaption>
      </figure>"""


INSIDE_ASIDE = ("Кирпичное здание с арочными окнами: ремонтный зал со стальными колоннами и офис "
                "с кирпичными стенами. Нажмите на окно, чтобы открыть фото целиком.")
DOOR_CAPTION = "Кирпичное здание, ворота в чёрном портале, над ними вывеска GARAGE TEAM"


def inside_section():
    arches = "".join(_arch(i, *row) for i, row in enumerate(INSIDE))
    return f"""<section class="section inside" id="inside" aria-labelledby="inside-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// Красная слобода, 9</p><h2 class="h2 sec-head__title" id="inside-title">Как у нас</h2></div>
      <p class="sec-head__aside">{nb(INSIDE_ASIDE)}</p>
    </div>
    <div class="inside__row" data-arcade>
      {arches}
    </div>
  </div>
</section>"""


def door():
    """The facade as an arched doorway next to the address: what the building looks like from the street."""
    # art-directed: a tall doorway in the desktop column, a squarer one when the block is a single column
    return f"""<figure class="arch arch--door reveal" style="--d:120ms">
      <div class="arch__opening">
        {wall()}
        <div class="arch__win">
          <picture><source media="(max-width: 900px)" srcset="/assets/img/real/arch/facade.webp"><img class="arch__img" src="/assets/img/real/arch/facade-tall.webp" alt="Фасад автосервиса Гараж: кирпичное здание, чёрный портал ворот и вывеска Garage Team над ними" width="560" height="1005" loading="lazy" decoding="async"></picture>
        </div>
      </div>
      <figcaption class="arch__cap"><span class="arch__n">Ориентир</span><span>{nb(DOOR_CAPTION)}</span></figcaption>
    </figure>"""
