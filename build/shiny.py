# -*- coding: utf-8 -*-
"""«Шинный калькулятор» on the tyre-fitting page (block id="shiny", after the lead).

Two tyre sizes «ширина/профиль R диаметр» are compared by pure geometry of the marking:
sidewall = width × profile / 100, outer diameter = rim inches × 25.4 + 2 × sidewall. Lengths are whole numbers of
hundredths of a millimetre (205 × 55 → 11 275 = 112,75 мм) and are shown in tenths, rounded half away from zero;
a difference is the difference of the shown values, so the columns always add up. Percent and speeds are floats
rounded the same way. src/assets/js/shiny.js repeats these few formulas line for line.

Python renders the default pair — numbers, verdict and drawing — so the block is complete before the script starts.
The drawing constants, the speeds, the 3 % limit and every phrase live here and reach the script through data-*
attributes; the allowed sizes are the options of the selects.
"""
from __future__ import annotations

import json
import math

from . import data as D
from .icons import icon

esc = D.esc

PAGE = "/services/sinomontaz.html"
ALIGNMENT = "/services/shod-razval-regulirovka-i-diagnostika.html"

WIDTHS = list(range(135, 336, 10))      # мм: 135, 145 … 335
PROFILES = list(range(25, 86, 5))       # % of the width: 25 … 85
RIMS = list(range(12, 25))              # inches: R12 … R24
DEFAULT_NOW = (205, 55, 16)
DEFAULT_NEW = (215, 50, 17)
SPEEDS = (60, 90, 110)
LIMIT = 3.0                             # % of the diameter: the usual rule of thumb, not a norm
METER = 6.0                             # the deviation scale runs from −6 % to +6 %

# drawing, in viewBox units: side view of both wheels on one ground line, front view (tread) to the right of it
VIEW_W, VIEW_H = 440, 330
GROUND = 298
TOP = 30                                # the band above is kept for the «вид сбоку / вид спереди» labels
SIDE_X = 146
FRONT_X = 360
SCALE_MIN_MM = 700                      # the scale changes only for wheels taller than this (rounded up to 100 мм)
BAR_X, BAR_Y = 16, 317                  # 100 мм scale bar under the ground line; its label is HTML, right of the bar

NBSP = "\u00a0"
MINUS = "\u2212"

# «Как читать маркировку»: one example from a real sidewall, general knowledge only
MARKING = [
    ("w", "205", "Ширина", "В миллиметрах, от одной боковины шины до другой."),
    ("p", "55", "Профиль", f"Высота боковины в процентах от ширины: 55{NBSP}% от 205{NBSP}мм — это около 113{NBSP}мм. "
                           "Чем меньше число, тем ниже боковина."),
    ("c", "R", "Конструкция", "Радиальная: нити корда идут от одного борта шины к другому. Такие почти все современные "
                              "легковые шины. R — это не радиус, как часто думают."),
    ("d", "16", "Посадочный диаметр", f"Диаметр диска, на который ставится шина, в дюймах: 16″ — это 406{NBSP}мм."),
    ("l", "91", "Индекс нагрузки", f"Какой вес выдерживает одна шина: 91 — до 615{NBSP}кг."),
    ("s", "V", "Индекс скорости", f"На какую максимальную скорость рассчитана шина: V — до 240{NBSP}км/ч."),
]
# every phrase the script may put on the page: rendered here and handed to shiny.js as data-* of the block
TEXTS = {
    "head-more": "Колесо больше на",
    "head-less": "Колесо меньше на",
    "head-same": "Диаметр не меняется",
    "same": "Размеры одинаковые — диаметр колеса, клиренс и спидометр не изменятся.",
    "ok": f"Разница в пределах 3{NBSP}% — обычно такую замену считают допустимой.",
    "over": f"Разница больше 3{NBSP}% — это заметно.",
    "over-more": "Спидометр будет показывать меньше реальной скорости, а колесо может задевать подкрылок или детали подвески.",
    "over-less": "Спидометр будет показывать больше реальной скорости, а клиренс уменьшится.",
    "err-parse": "Не получилось разобрать размер. Напишите как на шине, например 205/55 R16.",
    "err-range": f"Такого размера нет в списке: ширина от 135 до 335{NBSP}мм, профиль от 25 до 85, диаметр от R12 до R24.",
    "msg": "Шиномонтаж: хочу поставить {new} вместо {now}.",
    "msg-same": "Шиномонтаж: шины {now}.",
    "live": "{new} вместо {now}: {diff}. Если спидометр показывает 90 км/ч, на самом деле {v90} км/ч. {verdict}",
}
FOOTNOTE_SPEED = "Реальная скорость — если с нынешними шинами спидометр показывал точно."
FOOTNOTE_SCALE = "В масштабе, по размерам из маркировки: у шин разных производителей реальные размеры немного отличаются."
MAKER_NOTE = "Допустимые размеры для вашей машины указаны производителем: на табличке в проёме водительской двери или в инструкции."


# ---------- maths ----------
def sidewall(width: int, profile: int) -> int:
    """hundredths of a millimetre"""
    return width * profile


def rim(diameter: int) -> int:
    return diameter * 2540


def outer(width: int, profile: int, diameter: int) -> int:
    return rim(diameter) + 2 * sidewall(width, profile)


def tenths(h: int) -> int:
    """hundredths -> tenths of a millimetre, half away from zero"""
    return (1 if h >= 0 else -1) * ((abs(h) + 5) // 10)


def round1(x: float) -> float:
    """float -> one decimal, half away from zero (JS: the same expression with Math.floor)"""
    return math.copysign(math.floor(abs(x) * 10 + 0.5) / 10, x) if x else 0.0


def compare(now: tuple, new: tuple) -> dict:
    """Everything the block shows. Lengths in tenths of a millimetre, pct and speeds as floats."""
    od_a, od_b = outer(*now), outer(*new)
    diff = od_b - od_a
    return {
        "od_a": tenths(od_a), "od_b": tenths(od_b), "od_d": tenths(od_b) - tenths(od_a),
        "side_a": tenths(sidewall(*now[:2])), "side_b": tenths(sidewall(*new[:2])),
        "side_d": tenths(sidewall(*new[:2])) - tenths(sidewall(*now[:2])),
        "width_d": new[0] - now[0],
        "clearance": tenths(diff // 2),                         # od is always even: 2540·d + 2·w·p
        "pct": round1(diff / od_a * 100),
        "speeds": [(v, round1(v * od_b / od_a)) for v in SPEEDS],
        "same": tuple(now) == tuple(new),
    }


# ---------- formatting: decimal comma, real minus, no-break space before the unit ----------
def dec(t: int) -> str:
    """tenths -> «631,9» (no sign)"""
    t = abs(t)
    return f"{t // 10},{t % 10}"


def signed_tenths(t: int) -> str:
    return "0" if t == 0 else ("+" if t > 0 else MINUS) + dec(t)


def signed_float(x: float) -> str:
    return signed_tenths(int(round(x * 10)))


def signed_int(n: int) -> str:
    return "0" if n == 0 else ("+" if n > 0 else MINUS) + str(abs(n))


def size_label(size: tuple) -> str:
    w, p, d = size
    return f"{w}/{p} R{d}"


def headline(r: dict) -> str:
    if r["od_d"] == 0:
        return TEXTS["head-same"]
    return f"{TEXTS['head-more' if r['od_d'] > 0 else 'head-less']} {dec(r['od_d'])}{NBSP}мм"


def verdict(r: dict) -> tuple[str, str, str]:
    """(state, lead in bold, what follows); state: same | ok | over"""
    if r["same"]:
        return "same", TEXTS["same"], ""
    if abs(r["pct"]) <= LIMIT:
        return "ok", TEXTS["ok"], ""
    return "over", TEXTS["over"], TEXTS["over-more" if r["pct"] > 0 else "over-less"]


def cta_message(now: tuple, new: tuple) -> str:
    key = "msg-same" if tuple(now) == tuple(new) else "msg"
    return TEXTS[key].format(now=size_label(now), new=size_label(new))


def meter_pos(pct: float) -> float:
    """Marker on the −6…+6 % scale: 0…100 (% of the track), clamped at the ends."""
    return (max(-METER, min(METER, pct)) + METER) / (2 * METER) * 100


# ---------- drawing ----------
def scale(od_a: int, od_b: int) -> float:
    """viewBox units per millimetre: both wheels to one scale; it steps only when a wheel is taller than 700 мм."""
    top_mm = max(SCALE_MIN_MM, math.ceil(max(od_a, od_b) / 10000) * 100)
    return (GROUND - TOP) / top_mm


def _f(x: float) -> str:
    return f"{x:.3f}".rstrip("0").rstrip(".")


def transforms(now: tuple, new: tuple) -> dict:
    """SVG transform of every moving part, by its data-t name (shiny.js builds the same strings)."""
    od_a, od_b = outer(*now), outer(*new)
    s = scale(od_a, od_b)
    ra, rb = od_a / 200 * s, od_b / 200 * s                   # tyre radius, viewBox units
    rim_a, rim_b = rim(now[2]) / 200 * s, rim(new[2]) / 200 * s
    return {
        "tyre-b": f"translate({SIDE_X} {_f(GROUND - rb)}) scale({_f(rb / 100)})",
        "rim-b": f"translate({SIDE_X} {_f(GROUND - rb)}) scale({_f(rim_b / 100)})",
        "tyre-a": f"translate({SIDE_X} {_f(GROUND - ra)}) scale({_f(ra / 100)})",
        "rim-a": f"translate({SIDE_X} {_f(GROUND - ra)}) scale({_f(rim_a / 100)})",
        "front-b": f"translate({FRONT_X} {GROUND}) scale({_f(new[0] * s)} {_f(od_b / 100 * s)})",
        "front-a": f"translate({FRONT_X} {GROUND}) scale({_f(now[0] * s)} {_f(od_a / 100 * s)})",
        "top-b": f"translate(0 {_f(GROUND - 2 * rb)})",
        "top-a": f"translate(0 {_f(GROUND - 2 * ra)})",
        "bar": f"translate({BAR_X} {BAR_Y}) scale({_f(100 * s)} 1)",
    }


def _svg(now: tuple, new: tuple) -> str:
    t = transforms(now, new)
    # the new rim in its own units (radius 100): five tapered spokes, hub, five lug nuts
    spokes = "".join(f'<path class="shiny-svg__spoke" transform="rotate({i * 72})" d="M-7 -19 L-13 -84 Q0 -88 13 -84 L7 -19 Z"/>'
                     for i in range(5))
    lugs = "".join(f'<circle class="shiny-svg__lug" transform="rotate({i * 72 + 36}) translate(0 -12)" r="2.6"/>' for i in range(5))
    grooves = "".join(f'<line class="shiny-svg__groove" x1="{x}" y1="-0.985" x2="{x}" y2="-0.015"/>' for x in (-0.3, -0.1, 0.1, 0.3))
    unit_rect = '<rect x="-0.5" y="-1" width="1" height="1" rx="0.1" ry="0.035"/>'

    def part(cls, name, inner):
        return f'<g class="{cls}" data-t="{name}" transform="{t[name]}">{inner}</g>'

    data = (f'data-ground="{GROUND}" data-top="{TOP}" data-side="{SIDE_X}" data-front="{FRONT_X}" '
            f'data-min="{SCALE_MIN_MM}" data-bar="{BAR_X} {BAR_Y}"')
    return (f'<svg class="shiny-svg" viewBox="0 0 {VIEW_W} {VIEW_H}" {data} aria-hidden="true" focusable="false">'
            f'<defs><pattern id="shiny-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="6"/></pattern></defs>'
            f'<line class="shiny-svg__proj shiny-svg__proj--a" data-t="top-a" transform="{t["top-a"]}" x1="{SIDE_X}" y1="0" x2="{FRONT_X + 64}" y2="0"/>'
            f'<line class="shiny-svg__proj" data-t="top-b" transform="{t["top-b"]}" x1="{SIDE_X}" y1="0" x2="{FRONT_X + 64}" y2="0"/>'
            + part("shiny-svg__tyre", "tyre-b", '<circle r="100"/><circle class="shiny-svg__tread" r="93"/>')
            + part("shiny-svg__rim", "rim-b", f'<circle r="100"/><circle class="shiny-svg__lip" r="88"/>{spokes}'
                                              f'<circle class="shiny-svg__hub" r="19"/>{lugs}<circle class="shiny-svg__bore" r="5.5"/>')
            + part("shiny-svg__front", "front-b", unit_rect + grooves)
            + part("shiny-svg__ghost", "tyre-a", '<circle r="100"/>')
            + part("shiny-svg__ghost shiny-svg__ghost--rim", "rim-a", '<circle r="100"/>')
            + part("shiny-svg__ghost", "front-a", unit_rect)
            + f'<rect class="shiny-svg__earth" x="8" y="{GROUND}" width="{VIEW_W - 16}" height="7"/>'
            + f'<line class="shiny-svg__floor" x1="8" y1="{GROUND}" x2="{VIEW_W - 8}" y2="{GROUND}"/>'
            + f'<path class="shiny-svg__bar" data-t="bar" transform="{t["bar"]}" d="M0 -3V3M0 0H1M1 -3V3"/>'
            + "</svg>")


# ---------- markup ----------
def _options(values, current, fmt=str) -> str:
    return "".join(f'<option value="{v}"{" selected" if v == current else ""}>{fmt(v)}</option>' for v in values)


def _size_fields(key: str, legend: str, size: tuple) -> str:
    w, p, d = size
    return f"""<fieldset class="shiny__size shiny__size--{key}" data-size="{key}">
          <legend class="shiny__legend"><span class="shiny__swatch" aria-hidden="true"></span>{esc(legend)}</legend>
          <div class="shiny__typed">
            <label class="sr-only" for="shiny-{key}-text">{esc(legend)}: размер шины, например 205/55 R16</label>
            <input class="shiny__text" id="shiny-{key}-text" type="text" value="{esc(size_label(size))}" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" enterkeyhint="done" maxlength="24" aria-describedby="shiny-{key}-err" data-text>
            <svg class="shiny__pen" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4"/></svg>
          </div>
          <p class="shiny__err" id="shiny-{key}-err" data-err hidden>{esc(TEXTS["err-parse"])}</p>
          <div class="shiny__selects">
            <label class="shiny__field"><span>Ширина</span><select class="select" data-part="w" aria-label="{esc(legend)}: ширина, мм">{_options(WIDTHS, w)}</select></label>
            <span class="shiny__slash" aria-hidden="true">/</span>
            <label class="shiny__field"><span>Профиль</span><select class="select" data-part="p" aria-label="{esc(legend)}: профиль, %">{_options(PROFILES, p)}</select></label>
            <label class="shiny__field"><span>Диаметр</span><select class="select" data-part="d" aria-label="{esc(legend)}: посадочный диаметр">{_options(RIMS, d, lambda v: f"R{v}")}</select></label>
          </div>
        </fieldset>"""


def _results(now: tuple, new: tuple, r: dict) -> str:
    ticks = "".join(f'<span style="left:{meter_pos(v):g}%">{signed_int(v)}</span>' for v in (-6, -3, 0, 3, 6))
    return f"""<div class="shiny__out">
            <p class="shiny__label">Разница диаметров</p>
            <p class="shiny__head"><span class="shiny__pct" data-o="pct">{signed_float(r['pct'])}{NBSP}%</span><span class="shiny__say" data-o="head">{esc(headline(r))}</span></p>
            <div class="shiny__meter" aria-hidden="true">
              <div class="shiny__track"><span class="shiny__zone"></span></div>
              <div class="shiny__rail"><span class="shiny__pos" data-o="meter" style="transform:translateX({meter_pos(r['pct']):.2f}%)"><i></i></span></div>
              <div class="shiny__ticks">{ticks}</div>
            </div>
            <table class="shiny__table">
              <caption class="sr-only">Размеры колеса сейчас и после замены, в миллиметрах</caption>
              <thead><tr><td></td><th scope="col">Сейчас</th><th scope="col">Хочу</th><th scope="col">Разница</th></tr></thead>
              <tbody>
                <tr><th scope="row">Наружный диаметр</th><td data-o="odA">{dec(r['od_a'])}</td><td data-o="odB">{dec(r['od_b'])}</td><td data-o="odD">{signed_tenths(r['od_d'])}{NBSP}мм</td></tr>
                <tr><th scope="row">Высота боковины</th><td data-o="sA">{dec(r['side_a'])}</td><td data-o="sB">{dec(r['side_b'])}</td><td data-o="sD">{signed_tenths(r['side_d'])}{NBSP}мм</td></tr>
                <tr><th scope="row">Ширина шины</th><td data-o="wA">{now[0]}</td><td data-o="wB">{new[0]}</td><td data-o="wD">{signed_int(r['width_d'])}{NBSP}мм</td></tr>
                <tr><th scope="row">Клиренс</th><td colspan="2" class="shiny__hint">половина разницы диаметров</td><td data-o="cD">{signed_tenths(r['clearance'])}{NBSP}мм</td></tr>
              </tbody>
            </table>
          </div>"""


def _speed(r: dict) -> str:
    shown = "".join(f"<td>{v}</td>" for v, _ in r["speeds"])
    real = "".join(f'<td data-o="v{i}">{dec(int(round(x * 10)))}</td>' for i, (_, x) in enumerate(r["speeds"]))
    return f"""<div class="shiny__speed">
            <table class="shiny__table shiny__table--speed">
              <caption class="shiny__label">Спидометр, км/ч</caption>
              <tbody>
                <tr><th scope="row">Показывает</th>{shown}</tr>
                <tr><th scope="row">На самом деле</th>{real}</tr>
              </tbody>
            </table>
            <p class="shiny__foot">{esc(FOOTNOTE_SPEED)}</p>
          </div>"""


def _verdict(r: dict) -> str:
    state, lead, more = verdict(r)
    return f"""<div class="shiny__verdict" data-state="{state}" data-o="verdict">
          <span class="shiny__verdict-ic" aria-hidden="true">{icon('check')}{icon('hazard')}</span>
          <p><b data-o="verdict-text">{esc(lead)}</b> <span data-o="verdict-more">{esc(more)}</span> {esc(MAKER_NOTE)}</p>
        </div>"""


def _marking() -> str:
    parts, panels = [], []
    for i, (key, text, name, about) in enumerate(MARKING):
        on = i == 0
        parts.append(f'<button class="shiny-mark__part{" is-active" if on else ""}" type="button" data-mark="{key}" '
                     f'aria-pressed="{"true" if on else "false"}" aria-controls="shiny-mark-{key}">'
                     f'<span class="sr-only">{esc(name)}: </span>{esc(text)}</button>')
        if key == "w":
            parts.append('<span class="shiny-mark__sep" aria-hidden="true">/</span>')
        elif key == "p":
            parts.append('<span class="shiny-mark__gap" aria-hidden="true"></span>')
        elif key == "d":
            parts.append('<span class="shiny-mark__gap" aria-hidden="true"></span><span class="shiny-mark__break" aria-hidden="true"></span>')
        panels.append(f'<div class="shiny-mark__about" id="shiny-mark-{key}" data-about="{key}"{"" if on else " hidden"}>'
                      f'<p class="shiny-mark__name"><b>{esc(text)}</b>{esc(name)}</p><p>{esc(about)}</p></div>')
    return f"""<div class="shiny-mark reveal">
        <h3 class="shiny-mark__title">Как читать маркировку</h3>
        <p class="shiny-mark__hint">Нажмите на часть надписи с боковины шины.</p>
        <div class="shiny-mark__wall">
          <div class="shiny-mark__line" role="group" aria-label="Маркировка шины 205/55 R16 91V">{"".join(parts)}<span class="shiny-mark__bar" aria-hidden="true"></span></div>
        </div>
        <div class="shiny-mark__panel" aria-live="polite">{"".join(panels)}</div>
      </div>"""


def block(svc: dict) -> str:
    """The calculator on the tyre-fitting page; empty for every other service page."""
    if svc["path"] != PAGE:
        return ""
    now, new = DEFAULT_NOW, DEFAULT_NEW
    r = compare(now, new)
    preset = esc(json.dumps({"message": cta_message(now, new)}, ensure_ascii=False))
    align = D.BY_PATH.get(ALIGNMENT)
    align_link = (f'<a class="link-arrow link-arrow--inline shiny__more" href="{ALIGNMENT}">{esc(align.get("nav_name") or align["h1"])} {icon("arrow")}</a>'
                  if align else "")
    swap = '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 8h15M15 4l4 4-4 4M20 16H5M9 12l-4 4 4 4"/></svg>'
    texts = " ".join(f'data-{k}="{esc(v)}"' for k, v in TEXTS.items())
    config = f'data-speeds="{" ".join(map(str, SPEEDS))}" data-limit="{LIMIT:g}" data-meter="{METER:g}"'
    # the section itself never moves: .reveal shifts an element by 22px, and a link to #shiny would then land short of it
    return f"""<section class="shiny" id="shiny" aria-labelledby="shiny-title" data-shiny {config} {texts}>
      <div class="block-title"><span class="tag-num">// калькулятор</span><h2 class="h3" id="shiny-title">Шинный калькулятор</h2></div>
      <p class="shiny__intro">Сравните размер шин, которые стоят сейчас, с теми, что хотите поставить: калькулятор покажет, как изменятся диаметр колеса, клиренс и показания спидометра.</p>
      <div class="shiny__panel reveal">
        <div class="shiny__sizes">
          {_size_fields("a", "Сейчас стоит", now)}
          <div class="shiny__swapbox"><button class="shiny__swap" type="button" data-swap aria-label="Поменять размеры местами" title="Поменять местами">{swap}</button></div>
          {_size_fields("b", "Хочу поставить", new)}
        </div>
        <div class="shiny__main">
          <figure class="shiny__figure">
            <div class="shiny__stage">
              {_svg(now, new)}
              <span class="shiny__view shiny__view--side" aria-hidden="true">вид сбоку</span>
              <span class="shiny__view shiny__view--front" aria-hidden="true">вид спереди</span>
              <span class="shiny__view shiny__view--bar" aria-hidden="true">100 мм</span>
            </div>
            <figcaption class="shiny__keys">
              <span class="shiny__key shiny__key--a"><i aria-hidden="true"></i>Сейчас <b data-o="labelA">{esc(size_label(now))}</b></span>
              <span class="shiny__key shiny__key--b"><i aria-hidden="true"></i>Хочу <b data-o="labelB">{esc(size_label(new))}</b></span>
              <span class="shiny__keys-note">{esc(FOOTNOTE_SCALE)}</span>
            </figcaption>
          </figure>
          {_results(now, new, r)}
          {_speed(r)}
          <div class="shiny__act">
            {_verdict(r)}
            <div class="shiny__cta">
              <button class="btn btn--primary" type="button" data-modal="call" data-preset='{preset}' data-cta>{icon('phone')} Записаться на шиномонтаж</button>
              {align_link}
            </div>
          </div>
        </div>
        <p class="sr-only" aria-live="polite" data-live></p>
      </div>
      {_marking()}
    </section>"""
