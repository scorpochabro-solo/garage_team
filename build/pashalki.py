# -*- coding: utf-8 -*-
"""Easter eggs («пасхалки») for the homepage, drawn from the real workshop on Krasnaya Sloboda:
    * tach_icon()  — a tiny tachometer in the hero «Оставить заявку» button: the needle revs on hover / press;
    * wall()       — a strip of the lounge's red-brick wall: the V8 coffee table photo (tap: its pistons light up)
                     and a niche with a pendant lamp above it (tap: the next little car-themed object);
    * v8_gauge()   — a fixed «back to top» button with a line-art V8 whose crank turns with the scroll.
Styles: src/assets/css/pashalki.css, behaviour: src/assets/js/pashalki.js."""
import math

from . import data as D

esc = D.esc

BRICK = "/assets/img/real/brick-wall.webp"          # perspective-corrected close-up of the lounge wall, 1600×641
TABLE = "/assets/img/real/v8-table-top.webp"        # the V8 coffee table from above, 1600×1280

# The four real pistons that hold up the glass, in % of the table photo, in the order they "fire" on tap.
TABLE_PISTONS = [(31.9, 12.4), (15.3, 44.7), (78.5, 59.8), (85.6, 24.9)]
TABLE_TAGS = [("блок V8", 50.5, 44.0), ("поршни", 31.9, 12.4)]

# Objects in the niche: line-art after the little things in the real niche of the office (a retro petrol pump, a wheel,
# a tin sign with a van, a boxed model car — drawn as the estate from the services map). 80×64 viewBox, standing on y=62.
NICHE_ITEMS = [
    ("бензоколонка", """<path d="M27 60V20a4 4 0 0 1 4-4h14a4 4 0 0 1 4 4v40"/><path d="M31 11a7 5.5 0 0 1 14 0v2H31z"/><path d="M31 8.5h14M35 13v3M41 13v3"/>
      <rect x="31" y="21" width="14" height="10" rx="1.5"/><path d="M38 30l3-6"/><path d="M27 38h22M27 42h22"/>
      <path d="M49 26h4a3 3 0 0 1 3 3v22a3 3 0 0 0 6 0V36l-3-3"/><path d="M23 62h30"/>"""),
    ("колесо", """<circle cx="40" cy="36" r="25"/><circle cx="40" cy="36" r="17"/><circle cx="40" cy="36" r="13.5"/>
      <circle cx="40" cy="36" r="3.2"/><path d="M40.0 32.0L40.0 23.0M43.8 34.8L52.4 32.0M42.4 39.2L47.6 46.5M37.6 39.2L32.4 46.5M36.2 34.8L27.6 32.0"/>
      <path d="M60.1 40.0L64.0 40.8M57.0 47.4L60.4 49.6M51.4 53.0L53.6 56.4M44.0 56.1L44.8 60.0M36.0 56.1L35.2 60.0M28.6 53.0L26.4 56.4M23.0 47.4L19.6 49.6M19.9 40.0L16.0 40.8M19.9 32.0L16.0 31.2M23.0 24.6L19.6 22.4M28.6 19.0L26.4 15.6M36.0 15.9L35.2 12.0M44.0 15.9L44.8 12.0M51.4 19.0L53.6 15.6M57.0 24.6L60.4 22.4M60.1 32.0L64.0 31.2"/>"""),
    ("фургон", """<path d="M9 52V31c0-6 3-9 9-9h40c7 0 11 4 13 10l3 10v8c0 1.2-.8 2-2 2h-5.3a7.8 7.8 0 0 0-13.4 0H28.7a7.8 7.8 0 0 0-13.4 0H9z"/>
      <path d="M9 40h65"/><path d="M15 27h10v9H15zM30 27h10v9H30zM45 27h10v9H45zM60 27h4c2 0 3.5 1.5 4.2 4l1 5H60z"/>
      <circle cx="22" cy="56" r="5.8"/><circle cx="60" cy="56" r="5.8"/><path d="M40 22v-3h20v3M70 45h3"/>"""),
    ("машинка", """<path d="M5 51v-7c0-3 2-5 5-5.6L24 36l9-8c1.5-1.3 3-2 5-2h28c3 0 4.5 1.5 5.4 4.5L74 42v7c0 1.2-.8 2-2 2h-4.1a8 8 0 0 0-13.8 0H25.9a8 8 0 0 0-13.8 0H5z"/>
      <path d="M27 36l8-7h11v7zM50 29h16l2.5 7H50z"/><circle cx="19" cy="55" r="6.2"/><circle cx="61" cy="55" r="6.2"/>
      <path d="M36 42h6M5 44.5h3"/>"""),
]


def tach_icon():
    """24×24 tachometer that replaces the check mark of the hero CTA. The arc runs 240° from 0 to the red zone."""
    return ('<svg class="ic tach" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round">'
            '<path class="tach__arc" d="M4.64 17.25A8.5 8.5 0 1 1 19.36 17.25" stroke-width="1.7"/>'
            '<path class="tach__red" d="M20.37 11.52A8.5 8.5 0 0 1 19.36 17.25" stroke-width="3.2"/>'
            '<path class="tach__needle" d="M12 13V6.2" stroke-width="1.9"/>'
            '<circle cx="12" cy="13" r="1.9" fill="currentColor" stroke="none"/></svg>')


def _piston_glyph():
    # line-art piston for the table photo: crown with two ring grooves, skirt, pin, the connecting rod and its big end
    return ('<svg class="xray__piston" viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M5.5 2.5h13v10h-13z"/><path d="M5.5 5h13M5.5 7h13"/><circle cx="12" cy="10" r="1.4"/>'
            '<path d="M10.6 11.4l-.8 5.8M13.4 11.4l.8 5.8"/><circle cx="12" cy="19.6" r="2.9"/></svg>')


def wall():
    rings = "".join(
        f'<span class="xray__ring" style="--x:{x}%;--y:{y}%;--d:{i * 140}ms">{_piston_glyph()}</span>'
        for i, (x, y) in enumerate(TABLE_PISTONS))
    tags = "".join(
        f'<span class="xray__tag" style="--x:{x}%;--y:{y}%;--d:{500 + i * 160}ms">{esc(t)}</span>'
        for i, (t, x, y) in enumerate(TABLE_TAGS))
    items = "".join(
        f'<svg class="niche__item niche__item--{i + 1}{" is-active" if i == 0 else ""}" viewBox="0 0 80 64" aria-hidden="true">{svg}</svg>'
        for i, (_, svg) in enumerate(NICHE_ITEMS))
    names = "|".join(n for n, _ in NICHE_ITEMS)
    total = len(NICHE_ITEMS)
    small = lambda u: u.replace(".webp", "-800.webp")  # noqa: E731
    # the back of the niche is the same wall photo as the strip, so it costs no extra download
    brick_pic = lambda cls: (f'<picture><source media="(max-width: 640px)" srcset="{small(BRICK)}">'  # noqa: E731
                             f'<img class="{cls}" src="{BRICK}" alt="" width="1600" height="641" loading="lazy" decoding="async"></picture>')
    return f"""<section class="wall" id="lounge" aria-labelledby="wall-title">
  <div class="wall__bg" aria-hidden="true">
    {brick_pic("wall__photo")}
    <div class="wall__shade"></div>
  </div>
  <div class="wrap wall__in">
    <div class="wall__plaque reveal">
      <p class="eyebrow">// Зона ожидания</p>
      <h2 class="wall__title" id="wall-title">Пока ждёте машину</h2>
      <p class="wall__text">Кирпичные стены, чёрные лампы, кожаные кресла, журналы и приставка. Журнальный столик стоит на блоке V8, а в стене есть ниша с автомобильными мелочами.</p>
      <p class="wall__hint mono"><span class="wall__hint-hover">Наведите на фото, нажмите на нишу</span><span class="wall__hint-touch">Нажмите на фото и на нишу</span></p>
    </div>
    <figure class="frame reveal" style="--d:120ms">
      <button class="frame__btn" type="button" aria-pressed="false" aria-label="Журнальный столик на блоке V8: показать поршни" data-xray>
        <img class="frame__photo" src="{TABLE}" srcset="{small(TABLE)} 800w, {TABLE} 1600w" sizes="(max-width: 640px) 48vw, 360px" alt="" width="1600" height="1280" loading="lazy" decoding="async">
        <span class="xray" aria-hidden="true"><span class="xray__veil"></span><span class="xray__scan"></span>{rings}{tags}</span>
      </button>
      <figcaption class="frame__plate mono">Столик · блок V8</figcaption>
    </figure>
    <div class="niche-spot reveal" style="--d:240ms">
      <div class="lamp" aria-hidden="true"><div class="lamp__sway">
        <span class="lamp__cord"></span>
        <svg class="lamp__shade" viewBox="0 0 120 92"><defs><linearGradient id="lamp-enamel" x1="0" x2="1"><stop offset="0" stop-color="#2a2c2a"/><stop offset=".28" stop-color="#3b3e3b"/><stop offset=".55" stop-color="#121312"/><stop offset="1" stop-color="#0b0c0b"/></linearGradient></defs>
          <rect x="52" y="0" width="16" height="9" rx="2" fill="#151615"/><path d="M53 9h14l3 11H50z" fill="#1b1c1b"/>
          <path d="M50 20h20c5 0 9 2 12 6 9 11 16 27 20 52H18c4-25 11-41 20-52 3-4 7-6 12-6z" fill="url(#lamp-enamel)"/>
          <path d="M16 78h88l1 5H15z" fill="#0f100f"/><ellipse class="lamp__bulb" cx="60" cy="84" rx="42" ry="5.5"/></svg>
        <span class="lamp__light"></span>
      </div></div>
      <button class="niche" type="button" aria-label="Ниша в стене: показать следующую вещицу" aria-describedby="niche-caption" data-niche data-names="{names}">
        <span class="niche__rim" aria-hidden="true"></span>
        <span class="niche__hole" aria-hidden="true">{brick_pic("niche__back")}<span class="niche__depth"></span><span class="niche__glow"></span>{items}<span class="niche__sill"></span></span>
      </button>
      <p class="niche__caption mono" id="niche-caption" aria-live="polite"><span data-niche-n>01</span> / {total:02d} · <span data-niche-name>{esc(NICHE_ITEMS[0][0])}</span></p>
    </div>
  </div>
</section>"""


# ---------- V8 back-to-top gauge ----------
# The engine is a static drawing (block, sleeves, heads) plus five moving parts — two pistons, two rods and the crank.
# They are driven by the page's scroll position itself (CSS scroll-driven animations of transform): the compositor turns
# the crank, the main thread does nothing per frame. The keyframes below come from the slider-crank formula.
V8_C = (32, 43)       # crank centre in the 64×64 drawing
V8_R = 5              # crank throw
V8_L = 14.5           # connecting rod length
V8_BANKS = (-45, 45)  # bank angles from vertical, degrees
V8_THETA0 = 20        # crank angle at the top of the page: both pistons visibly apart
V8_STEP = 15          # degrees between keyframes


def _v8_parts(theta):
    """CSS transforms of the moving parts for a crank angle, inside their bank (origin at the crank centre, the bank axis
    pointing up): [(piston, rod) per bank], and the crank's own transform."""
    out = []
    for b in V8_BANKS:
        phi = math.radians(theta - b)
        px, py = V8_R * math.sin(phi), V8_R * math.cos(phi)
        s = py + math.sqrt(V8_L ** 2 - px ** 2)                # piston pin: rides the bank axis
        alpha = math.degrees(math.asin(-px / V8_L))            # rod: from the crank pin up to the piston pin
        out.append((f"translateY({-s:.2f}px)", f"translate({px:.2f}px, {-py:.2f}px) rotate({alpha:.1f}deg)"))
    return out, f"translate({V8_C[0]}px, {V8_C[1]}px) rotate({theta}deg)"


def v8_keyframes():
    """One turn of the crank as keyframes, pasted into src/assets/css/pashalki.css (tests/test_pashalki.py keeps them in sync):
        python3 -m build.pashalki"""
    n = 360 // V8_STEP
    frames = {"v8-piston-0": [], "v8-piston-1": [], "v8-rod-0": [], "v8-rod-1": []}
    for k in range(n + 1):
        at = f"{k * 100 / n:.2f}".rstrip("0").rstrip(".") + "%"
        parts, _ = _v8_parts(V8_THETA0 + k * V8_STEP)
        for i, (piston, rod) in enumerate(parts):
            frames[f"v8-piston-{i}"].append(f"{at} {{ transform: {piston}; }}")
            frames[f"v8-rod-{i}"].append(f"{at} {{ transform: {rod}; }}")
    _, c0 = _v8_parts(V8_THETA0)
    _, c1 = _v8_parts(V8_THETA0 + 360)
    out = [f"@keyframes v8-crank {{ from {{ transform: {c0}; }} to {{ transform: {c1}; }} }}"]
    out += [f"@keyframes {name} {{\n  " + "\n  ".join(lines) + "\n}" for name, lines in frames.items()]
    return "\n".join(out)


def v8_gauge():
    cx, cy = V8_C
    parts, crank = _v8_parts(V8_THETA0)   # the pose without scroll-driven animations or with reduced motion
    sleeves = "".join(f"""<g transform="rotate({b} {cx} {cy})"><path class="v8__sleeve" d="M{cx - 5.5} {cy - 11}V{cy - 28}M{cx + 5.5} {cy - 11}V{cy - 28}"/>
        <path class="v8__head" d="M{cx - 7} {cy - 28}h14v-3.5h-14z"/></g>""" for b in V8_BANKS)
    banks = "".join(
        f'<span class="v8__bank" style="transform:translate({cx}px, {cy}px) rotate({b}deg)">'
        f'<span class="v8__rod v8__rod--{i}" style="transform:{r}"></span>'
        f'<span class="v8__piston v8__piston--{i}" style="transform:{p}"><svg viewBox="-5 -5 10 8" width="10" height="8">'
        f'<path d="M-4.4 -4.2h8.8v6.4h-8.8z"/><path d="M-4.4 -2.2h8.8"/><circle r="1"/></svg></span></span>'
        for i, (b, (p, r)) in enumerate(zip(V8_BANKS, parts)))
    return f"""<button class="v8" type="button" aria-label="Наверх страницы" data-v8 hidden>
  <span class="v8__chip">
    <span class="v8__mech" aria-hidden="true">
      <svg class="v8__svg" viewBox="0 0 64 64" width="64" height="64" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path class="v8__case" d="M{cx - 9.5} {cy + 1}a9.5 9.5 0 0 0 19 0"/>
        <text class="v8__badge" x="{cx}" y="{cy - 22}" text-anchor="middle">V8</text>
        {sleeves}
      </svg>
      {banks}
      <span class="v8__crank" style="transform:{crank}"><svg viewBox="-7 -7 14 14" width="14" height="14"><path d="M0 0V-{V8_R}"/><path d="M-4.5 3.4a5.6 5.6 0 0 0 9 0"/><circle r="2"/></svg></span>
    </span>
    <span class="v8__progress" aria-hidden="true"></span>
  </span>
  <span class="v8__label mono" aria-hidden="true">наверх</span>
</button>"""


if __name__ == "__main__":
    print(v8_keyframes())
