# -*- coding: utf-8 -*-
"""«Готова ли машина к зиме?» — seasonal checklist on the home page (#zima).

Ten items, each a real checkbox with a line icon, a short name, one «why» sentence and a link to an existing service
page. The ticks drive an instrument-style gauge (src/assets/js/zima.js); the unticked items become the message of the
call-back modal or the text of the request form. The tenth item depends on the engine: spark plugs for petrol,
glow plugs and the fuel filter for diesel (a switch in the gauge card), so the count stays 10 either way.
Seasonal: to take the section off the home page, remove zima_section() from render_home() in build/home.py.
"""
import json
import math

from . import data as D
from .icons import icon

esc = D.esc

_S = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
# line icons in the style of build/icons.py (24×24, stroke 1.6) that the shared set does not have; used only here
_ICONS = {
    "battery": f'<g {_S}><rect x="3" y="7.5" width="18" height="12" rx="1.5"/><path d="M6.5 7.5V5.5h3v2M14.5 7.5V5.5h3v2"/><path d="M6.5 13.5h4M8.5 11.5v4M13.5 13.5h4"/></g>',
    "coolant": f'<g {_S}><path d="M10.8 12.3V4.4a1.2 1.2 0 0 1 2.4 0v7.9a2.7 2.7 0 1 1-2.4 0z"/><path d="M13.2 6.5h2.2M13.2 9.3h2.2"/><path d="M2.5 20c1.3 0 1.3-1 2.6-1s1.3 1 2.6 1 1.3-1 2.6-1"/><path d="M13.7 20c1.3 0 1.3-1 2.6-1s1.3 1 2.6 1 1.3-1 2.6-1"/></g>',
    "washer": f'<g {_S}><path d="M3.5 19 5.4 9.6c4.4-1.5 8.8-1.5 13.2 0L20.5 19"/><path d="M12 19v-2.6"/><path d="M12 14.2v0M12 11.6v0M9.9 14.6v0M8 12.6v0M14.1 14.6v0M16 12.6v0" stroke-width="1.9"/></g>',
    "wiper": f'<g {_S}><path d="M3.5 19 5.4 9.6c4.4-1.5 8.8-1.5 13.2 0L20.5 19"/><path d="M12 18.6 7.6 11.2"/><path d="M6.9 12.4l1.4-2.4" stroke-width="2.2"/><circle cx="12" cy="18.6" r="1"/></g>',
    "defrost": f'<g {_S}><path d="M3.5 18.5 5.3 8c4.5-1.6 8.9-1.6 13.4 0l1.8 10.5c-5.7 1.3-11.3 1.3-17 0z"/><path d="M8.6 16c-.9-.9-.9-1.8 0-2.7s.9-1.8 0-2.7M12 16c-.9-.9-.9-1.8 0-2.7s.9-1.8 0-2.7M15.4 16c-.9-.9-.9-1.8 0-2.7s.9-1.8 0-2.7"/></g>',
    "plug": f'<g {_S}><path d="M12 2.5v2"/><rect x="10.2" y="4.5" width="3.6" height="5.5" rx="1"/><path d="M8.3 10h7.4v3H8.3z"/><path d="M9.6 13v4.6h4.8V13"/><path d="M12 17.6v2.9h2.3"/></g>',
    "oilcan": f'<g {_S}><path d="M5 11h9l6.5-2.3L14 15.2V17H5z"/><path d="M8.3 11V9h3v2"/><path d="M5 12.4 2.7 11.6v2.9L5 15.3"/><path d="M20.2 13.2c-.6.9-.9 1.4-.9 1.9a.9.9 0 0 0 1.8 0c0-.5-.3-1-.9-1.9z"/></g>',
    "snow": f'<g {_S}><path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"/><path d="M9.8 3.9 12 6l2.2-2.1M9.8 20.1 12 18l2.2 2.1M4.3 10.3l2.9-.9-.7-2.9M19.7 13.7l-2.9.9.7 2.9M6.5 17.4l.7-2.9-2.9-.9M17.5 6.6l-.7 2.9 2.9.9"/></g>',
}

# key, icon, name, why (one sentence of general knowledge), service page, words for the message («проверить …»), engine
ITEMS = [
    ("tires", "tire", "Зимние шины",
     "На холоде летняя резина твердеет и хуже держит дорогу, а у зимней важны остаток протектора и возраст.",
     "/services/sinomontaz.html", "зимние шины", None),
    ("battery", "battery", "Аккумулятор",
     "Мороз снижает отдачу аккумулятора, а холодный двигатель провернуть труднее — слабая батарея обычно подводит первой.",
     "/services/remont-elektrooborudovania-avtomobila.html", "аккумулятор", None),
    ("antifreeze", "coolant", "Антифриз",
     "Проверяют уровень и морозостойкость: антифриз, разбавленный водой, может замёрзнуть в сильный мороз.",
     "/services/remont-i-promyvka-sistem-ohlazdenia/zamena-ohlazdausej-zidkosti.html", "антифриз", None),
    ("washer", "washer", "Жидкость омывателя",
     "Летнюю жидкость меняют на незамерзающую до первых заморозков, иначе она может замёрзнуть в бачке и трубках.",
     "/services/planovoe-to.html", "жидкость омывателя", None),
    ("wipers", "wiper", "Щётки стеклоочистителя",
     "Старая резина щёток дубеет и оставляет полосы — в слякоть и снегопад это мешает обзору.",
     "/services/planovoe-to.html", "щётки стеклоочистителя", None),
    ("oil", "oilcan", "Масло в двигателе",
     "Проверяют уровень и срок замены: свежее масло подходящей вязкости облегчает пуск холодного двигателя.",
     "/services/remont-dvigatela/zamena-masla-v-dvigatele.html", "масло в двигателе", None),
    ("brakes", "brake", "Тормоза",
     "На скользкой дороге тормоза должны работать одинаково с обеих сторон: проверяют колодки, диски и жидкость.",
     "/services/diagnostika/diagnostika-tormoznoj-sistemy.html", "тормоза", None),
    ("lights", "headlight", "Свет и фары",
     "Зимой темнеет рано: все лампы должны гореть, а фары — быть чистыми и правильно отрегулированными.",
     "/services/remont-elektrooborudovania-avtomobila/zamena-lampocek-osvesenia.html", "свет и фары", None),
    ("heater", "defrost", "Печка и обдув стёкол",
     "Забитый салонный фильтр ослабляет поток воздуха — печке труднее справиться с запотевшими стёклами.",
     "/services/zapravka-i-remont-avtokondicionerov/zamena-filtra-kondicionera.html", "печку и обдув стёкол", None),
    ("plugs", "plug", "Свечи зажигания",
     "Изношенные свечи хуже поджигают смесь, и в мороз бензиновый двигатель заводится тяжелее.",
     "/services/remont-promyvka-inzektorov-i-monovpryskov/zamena-svecej.html", "свечи зажигания", "petrol"),
    ("glow", "diesel", "Свечи накаливания и топливный фильтр",
     "Свечи накаливания помогают дизелю завестись в холод, а забитый фильтр хуже пропускает загустевшее топливо.",
     "/services/remont-dizela.html", "свечи накаливания и топливный фильтр", "diesel"),
]
ENGINES = [("petrol", "Бензин"), ("diesel", "Дизель")]
DEFAULT_ENGINE = "petrol"
TIP = "Переобуваться обычно советуют, когда среднесуточная температура держится около +5…+7 °C."

# ---------- the gauge: a 240° instrument dial drawn once at build time ----------
VB_W, VB_H = 320, 232
CX, CY = 160, 158
START, SWEEP = -120, 240          # degrees, clockwise from 12 o'clock
SEGMENTS = 10                     # one per item; a lit segment = one more item in order
R_SEG, SEG_W, SEG_GAP = 128, 10, 2.2
R_TICK_OUT, R_TICK_MINOR, R_TICK_MAJOR = 116, 111, 105
R_RING = 92
NEEDLE = (66, 121)                # inner and outer radius: the needle orbits the readout instead of crossing it


def _pt(r, a):
    rad = math.radians(a)
    return CX + r * math.sin(rad), CY - r * math.cos(rad)


def _arc(r, a0, a1):
    x0, y0 = _pt(r, a0)
    x1, y1 = _pt(r, a1)
    large = 1 if a1 - a0 > 180 else 0
    return f"M{x0:.2f} {y0:.2f}A{r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}"


def _dial_svg():
    step = SWEEP / SEGMENTS
    spans = [(START + i * step + SEG_GAP / 2, START + (i + 1) * step - SEG_GAP / 2) for i in range(SEGMENTS)]
    track = "".join(_arc(R_SEG, a0, a1) for a0, a1 in spans)
    segs = "".join(f'<path class="zima-dial__seg" d="{_arc(R_SEG, a0, a1)}"/>' for a0, a1 in spans)
    minor, major = [], []
    for j in range(SEGMENTS * 5 + 1):
        a = START + j * step / 5
        is_major = j % 5 == 0
        x0, y0 = _pt(R_TICK_MAJOR if is_major else R_TICK_MINOR, a)
        x1, y1 = _pt(R_TICK_OUT, a)
        (major if is_major else minor).append(f"M{x0:.2f} {y0:.2f}L{x1:.2f} {y1:.2f}")
    lo, hi = _pt(R_SEG, START), _pt(R_SEG, START + SWEEP)
    r_in, r_out = NEEDLE
    return f"""<svg class="zima-dial__svg" viewBox="0 0 {VB_W} {VB_H}" aria-hidden="true" focusable="false">
        <defs><linearGradient id="zima-grad" gradientUnits="userSpaceOnUse" x1="{lo[0]:.0f}" y1="0" x2="{hi[0]:.0f}" y2="0"><stop offset="0" stop-color="#00963d"/><stop offset="1" stop-color="#1fc463"/></linearGradient></defs>
        <path class="zima-dial__ring" d="{_arc(R_RING, START, START + SWEEP)}"/>
        <path class="zima-dial__tick" d="{''.join(minor)}"/>
        <path class="zima-dial__tick zima-dial__tick--major" d="{''.join(major)}"/>
        <path class="zima-dial__track" d="{track}"/>
        {segs}
        <g transform="translate({CX} {CY})"><g class="zima-dial__needle" style="transform:rotate({START}deg)"><path d="M-2.2 -{r_in}L-0.7 -{r_out}H0.7L2.2 -{r_in}Z"/></g></g>
      </svg>"""


def _ic(name):
    """A line icon: this module's own set first, then the shared sprite."""
    if name in _ICONS:
        return f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{_ICONS[name]}</svg>'
    return icon(name)


def _item(key, ic, name, why, href, acc, engine, engine_on):
    svc = D.BY_PATH.get(href)
    if svc is None:
        raise ValueError(f"zima: нет страницы услуги {href}")
    link_name = svc.get("nav_name") or svc["h1"]
    eng = f' data-engine="{engine}"' if engine else ""
    hidden = " hidden" if engine and engine != engine_on else ""
    return f"""<li class="zima-item" data-key="{key}" data-acc="{esc(acc)}"{eng}{hidden}>
          <label class="zima-item__main">
            <input class="zima-item__input" type="checkbox" value="{key}" autocomplete="off" aria-labelledby="zima-n-{key}" aria-describedby="zima-w-{key}">
            <span class="zima-item__box" aria-hidden="true">{icon('check')}</span>
            <span class="zima-item__name" id="zima-n-{key}">{esc(name)}</span>
            <span class="zima-item__ic">{_ic(ic)}</span>
            <span class="zima-item__why" id="zima-w-{key}">{esc(why)}</span>
          </label>
          <a class="zima-item__link" href="{href}">{esc(link_name)} {icon('arrow-up-right')}</a>
        </li>"""


def zima_section():
    total = sum(1 for it in ITEMS if it[6] in (None, DEFAULT_ENGINE))
    items = "\n        ".join(_item(*it, engine_on=DEFAULT_ENGINE) for it in ITEMS)
    engines = "".join(
        f'<label class="radio"><input type="radio" name="zima-engine" value="{v}" autocomplete="off"{" checked" if v == DEFAULT_ENGINE else ""}><span>{esc(t)}</span></label>'
        for v, t in ENGINES)
    cells = "<i></i>" * SEGMENTS
    preset = esc(json.dumps({"message": "Подготовка к зиме"}, ensure_ascii=False))
    return f"""<section class="section section--black zima-sec" id="zima" aria-labelledby="zima-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// Сезонный чек-лист</p><h2 class="h2 sec-head__title" id="zima-title">Готова ли машина<br>к зиме?</h2></div>
      <p class="sec-head__aside">Десять пунктов, которые обычно проверяют перед холодами. Отметьте то, что уже в порядке, а остальное одним нажатием добавьте в заявку.</p>
    </div>
    <div class="zima is-empty" data-zima>
      <div class="zima__gauge reveal">
        <div class="zima-gauge">
          <div class="zima-gauge__head">
            <span class="zima-gauge__label">{_ic('snow')} Готовность к зиме</span>
            <button class="zima-gauge__reset" type="button" data-zima-reset disabled>Сбросить<span class="sr-only"> все отметки</span></button>
          </div>
          <div class="zima-dial" role="progressbar" aria-label="Готовность к зиме" aria-valuemin="0" aria-valuemax="{total}" aria-valuenow="0" aria-valuetext="Отмечено 0 из {total}">
            <div class="zima-dial__glow" aria-hidden="true"></div>
            {_dial_svg()}
            <b class="zima-dial__pct" aria-hidden="true"><span data-zima-pct>0</span><small>%</small></b>
            <span class="zima-dial__count" aria-hidden="true"><span data-zima-count>0</span> из {total}</span>
            <span class="zima-dial__end zima-dial__end--lo" aria-hidden="true">не готова</span>
            <span class="zima-dial__end zima-dial__end--hi" aria-hidden="true">готова</span>
          </div>
          <div class="zima-status">
            <p class="zima-status__title">{icon('check', 'zima-status__ok')}<span data-zima-title>Отметьте, что в порядке</span></p>
            <p class="zima-status__text" data-zima-text>Стрелка покажет, насколько машина готова к холодам.</p>
          </div>
          <div class="zima-engine" role="radiogroup" aria-labelledby="zima-engine-label">
            <span class="zima-engine__label" id="zima-engine-label">Двигатель</span>
            <div class="radio-group">{engines}</div>
          </div>
          <p class="sr-only" aria-live="polite" data-zima-live></p>
        </div>
      </div>
      <div class="zima__list reveal" style="--d:80ms">
        <ul class="zima-list" aria-label="Что проверить перед зимой">
        {items}
        </ul>
        <p class="zima__tip">{icon('info')}<span>{esc(TIP)}</span></p>
        <div class="zima-mini" aria-hidden="true">
          <span class="zima-mini__label">Готовность</span>
          <span class="zima-mini__bar">{cells}</span>
          <b class="zima-mini__pct"><span data-zima-mini>0</span>%</b>
        </div>
      </div>
      <div class="zima__actions reveal" style="--d:140ms">
        <button class="btn btn--primary zima__book" type="button" data-modal="call" data-preset="{preset}" data-zima-book>{icon('phone')} <span>Записаться на подготовку к&nbsp;зиме</span></button>
        <a class="btn btn--ghost zima__add" href="#request" data-zima-add>{icon('plus')} <span>Добавить в заявку</span></a>
        <p class="zima__store">Отметки сохраняются только в этом браузере</p>
      </div>
    </div>
  </div>
</section>"""
