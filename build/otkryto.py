# -*- coding: utf-8 -*-
"""«Открыто сейчас» and «Как добраться»: the live opening status, the week with today marked, the route, the address
to copy and the contact card for the phone.

The hours are D.HOURS (the workshop) and D.SHOP_HOURS (the parts shop) and nothing else. week() turns them into seven
days of minutes, the markup carries that as JSON in data-oc, and src/assets/js/otkryto.js computes the status in Moscow
time; without JS the plain hours stay on the page. D.HOURS does not list Sunday, so Sunday counts as closed; a value
that is not a time range makes a day with a note (the shop's «по предварительной записи»), unless it says the day is off
(«выходной»).
vcard_lines() builds the vCard 3.0 of «Сохранить в контакты» from the same constants; the browser joins the lines into
the file (CRLF) when the button is pressed, so no .vcf is published.
"""
from __future__ import annotations

import json
import re

from . import data as D
from .icons import icon

esc = D.esc

DAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
DAYS_FULL = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
# the day labels of D.HOURS / D.SHOP_HOURS (the same set as build/schema.py knows), Monday = 0
_LABEL_DAYS = {"Понедельник – пятница": (0, 1, 2, 3, 4), "Суббота": (5,), "Воскресенье": (6,)}
_RANGE = re.compile(r"^(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})$")
_CLOSED = {"выходной", "выходной день", "закрыто", "не работаем"}   # a day written out as closed is closed, not a note
# a cell of the week is too narrow for a note: its short form there (the status and screen readers get the full text)
_NOTE_SHORT = {"по предварительной записи": "по записи"}
_ADDRESS = re.compile(r"^(\d{6}), г\. ([^,]+), (.+)$")   # «603155, г. Нижний Новгород, ул. Красная слобода, 9»

ROUTE_URL = f"https://yandex.ru/maps/?rtext=~{D.COORDS[0]}%2C{D.COORDS[1]}&rtt=auto"   # by car from where you are
HOLIDAYS = "В праздничные дни график может отличаться — уточняйте по телефону."
VCARD_FILE = "garage.vcf"
COPY_DONE = "Адрес скопирован"
VCARD_DONE = f"Откройте файл {VCARD_FILE}, чтобы добавить «{D.BRAND}» в\u00a0контакты"   # no line break after «в»


# ---------- hours ----------
def week(hours: list[tuple[str, str]]) -> list:
    """[(days label, "9:00 – 19:00" or a note)] -> 7 days from Monday: [opens, closes] in minutes, {"note": …} or None."""
    days: list = [None] * 7
    for label, value in hours:
        if label not in _LABEL_DAYS:
            raise ValueError(f"неизвестные дни в часах работы: {label!r}")
        m = _RANGE.match(value.strip())
        if m:
            h1, m1, h2, m2 = map(int, m.groups())
            spec = [h1 * 60 + m1, h2 * 60 + m2]
            if not 0 <= spec[0] < spec[1] <= 24 * 60:
                raise ValueError(f"часы работы: {value!r}")
        elif value.strip().lower() in _CLOSED:
            spec = None
        else:
            spec = {"note": value.strip()}
        for d in _LABEL_DAYS[label]:
            days[d] = spec
    return days


def hm(minutes: int) -> str:
    """540 -> «9:00»"""
    return f"{minutes // 60}:{minutes % 60:02d}"


def _short(minutes: int) -> str:
    """540 -> «9», 570 -> «9:30»: the week's cells are narrow"""
    return str(minutes // 60) if minutes % 60 == 0 else hm(minutes)


def compact(hours: list[tuple[str, str]], sep: str = " · ", lower: bool = False) -> str:
    """«Пн–Пт 9:00–19:00 · Сб 9:00–17:00»: runs of days with the same hours; closed days are left out."""
    days, parts, i = week(hours), [], 0
    while i < 7:
        j = i
        while j + 1 < 7 and days[j + 1] == days[i]:
            j += 1
        spec = days[i]
        if spec is not None:
            name = DAYS[i] if i == j else f"{DAYS[i]}–{DAYS[j]}"
            value = f"{hm(spec[0])}–{hm(spec[1])}" if isinstance(spec, list) else spec["note"]
            parts.append(f"{name.lower() if lower else name} {value}")
        i = j + 1
    return sep.join(parts)


def _data(hours: list[tuple[str, str]]) -> str:
    """data-oc: the week for otkryto.js"""
    return esc(json.dumps({"week": week(hours)}, ensure_ascii=False, separators=(",", ":")))


_DOT = '<i class="oc__dot" aria-hidden="true"></i>'


# ---------- status in the header and the mobile menu ----------
def topline_item() -> str:
    """Desktop top line: the plain hours without JS, «● Открыто · до 19:00» with it; leads to the hours on /contacts/.
    data-oc-brief: the short closed form («Закрыто · до завтра, 9:00»), never longer than the plain hours it replaces."""
    return (f'<a class="topline__item oc" href="/contacts/#hours" data-oc="{_data(D.HOURS)}" data-oc-brief>{icon("clock")}{_DOT}'
            f'<span class="oc__text">{esc(compact(D.HOURS))}</span><span class="sr-only">, часы работы</span></a>')


def menu_item() -> str:
    """Mobile menu, under the phone number: the status above the plain hours, which stay as they were without JS."""
    lines = "<br>".join(f"{esc(d)}: {esc(h)}" for d, h in D.HOURS)
    return (f'<div class="oc oc-menu" data-oc="{_data(D.HOURS)}">{icon("clock")}{_DOT}'
            f'<p><b class="oc__text" hidden></b><span>{lines}</span></p></div>')


def inline(hours: list[tuple[str, str]], cls: str = "") -> str:
    """One line inside another block (the «Ворота» scene under the address): «● Открыто · до 19:00» with JS,
    the plain hours («Пн–Пт 9:00–19:00 · Сб 9:00–17:00») without it."""
    return (f'<span class="oc{" " + cls if cls else ""}" data-oc="{_data(hours)}">{_DOT}'
            f'<span class="oc__text">{esc(compact(hours))}</span></span>')


# ---------- the week ----------
def schedule(hours: list[tuple[str, str]], title: str | None = None, label: str = "Часы работы по дням недели",
             holidays: bool = True, big: bool = False) -> str:
    """The status line, the seven days (otkryto.js marks today) and the holiday note.
    title: the status line's text without JS; without a title the line appears only with JS."""
    cells = []
    for i, spec in enumerate(week(hours)):
        if isinstance(spec, list):
            short, full, cls = f"{_short(spec[0])}–{_short(spec[1])}", f"с {hm(spec[0])} до {hm(spec[1])}", ""
        elif spec:
            short, full, cls = _NOTE_SHORT.get(spec["note"], spec["note"]), spec["note"], " is-note"
        else:
            short, full, cls = "—", "закрыто", " is-off"
        cells.append(f'<li class="oc-week__day{cls}" data-day="{i}"><span class="oc-week__d" aria-hidden="true">{DAYS[i]}</span>'
                     f'<span class="oc-week__t" aria-hidden="true">{esc(short)}</span>'
                     f'<span class="sr-only">{DAYS_FULL[i]}: {esc(full)}</span></li>')
    line = (f'<p class="oc oc-now"{"" if title else " hidden"}>{_DOT}<span class="oc__text">{esc(title or "")}</span></p>')
    note = f'<p class="oc-note">{esc(HOLIDAYS)}</p>' if holidays else ""
    return (f'<div class="oc-sched{" oc-sched--big" if big else ""}" data-oc="{_data(hours)}">{line}'
            f'<ol class="oc-week" aria-label="{esc(label)}">{"".join(cells)}</ol>{note}</div>')


# ---------- «Как добраться» ----------
_S = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
_ICONS = {
    "route": '<path d="M20.5 3.5 3.8 10.4l7.1 2.7 2.7 7.1z"/>',
    "copy": ('<rect x="8.5" y="8.5" width="12" height="12" rx="1.5"/>'
             '<path d="M15.5 8.5V5A1.5 1.5 0 0 0 14 3.5H5A1.5 1.5 0 0 0 3.5 5v9A1.5 1.5 0 0 0 5 15.5h3.5"/>'),
    "contact-add": '<circle cx="9.5" cy="8" r="4"/><path d="M2.5 20.5a7 7 0 0 1 14 0"/><path d="M19.5 8v6M16.5 11h6"/>',
}


def _svg(name: str, cls: str = "") -> str:
    """Icons of this block only, inline (the shared sprite in build/icons.py stays as it is)."""
    return f'<svg class="{("ic " + cls).strip()}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><g {_S}>{_ICONS[name]}</g></svg>'


def actions(row: bool = False) -> str:
    """The route in Yandex Maps (a phone opens the app), copy the address, save the contact.
    The two buttons need JS: they are hidden until otkryto.js shows them. row: tiles as rows on a wide screen (/contacts/)."""
    vcard = esc(json.dumps(vcard_lines(), ensure_ascii=False, separators=(",", ":")))
    return f"""<div class="oc-go{" oc-go--row" if row else ""}" role="group" aria-labelledby="oc-go-title">
  <p class="oc-go__title" id="oc-go-title">Как добраться</p>
  <div class="oc-go__grid">
    <a class="oc-go__btn oc-go__btn--main" href="{esc(ROUTE_URL)}" target="_blank" rel="noopener">{_svg("route")}<span class="oc-go__label">Маршрут</span><span class="oc-go__tag">Яндекс Карты</span></a>
    <button class="oc-go__btn" type="button" data-oc-copy="{esc(D.ADDRESS_FULL)}" data-oc-toast="{esc(COPY_DONE)}" hidden>{_svg("copy", "oc-go__ic")}{icon("check", "oc-go__ok")}<span class="oc-go__label">Скопировать адрес</span></button>
    <button class="oc-go__btn" type="button" data-oc-vcard="{vcard}" data-oc-file="{VCARD_FILE}" data-oc-toast="{esc(VCARD_DONE)}" hidden>{_svg("contact-add")}<span class="oc-go__label">Сохранить в&nbsp;контакты</span><span class="oc-go__tag" aria-hidden="true">.vcf</span></button>
  </div>
</div>"""


# ---------- vCard 3.0 (RFC 2426) ----------
def _vc(text: str) -> str:
    """A text value: backslash, comma, semicolon and line breaks escaped."""
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def _fold(line: str, limit: int = 75) -> list[str]:
    """RFC 2425 5.8.1: at most 75 octets a line, the rest goes on in lines starting with a space.
    A UTF-8 letter or an escape («\\,») is never cut in two."""
    out, cur, size = [], "", 0
    for tok in re.findall(r"\\.|.", line, flags=re.S):
        n = len(tok.encode("utf-8"))
        if size + n > limit:
            out.append(cur)
            cur, size = " ", 1
        cur += tok
        size += n
    out.append(cur)
    return out


def vcard_lines() -> list[str]:
    """The card of «Сохранить в контакты»: escaped and folded lines, joined with CRLF by otkryto.js.
    X-ABShowAs makes an iPhone show it as a company (by ORG); Android shows FN."""
    m = _ADDRESS.match(D.ADDRESS_FULL)
    if not m:
        raise ValueError(f"адрес для vCard: {D.ADDRESS_FULL!r}")
    postcode, city, street = m.groups()
    lat, lon = D.COORDS
    note = (f"Автосервис: {compact(D.HOURS, ', ', lower=True)}\n"
            f"Магазин запчастей: {compact(D.SHOP_HOURS, ', ', lower=True)}")
    props = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        "N:;;;;",
        f"FN:{_vc(f'Автосервис «{D.BRAND}»')}",
        f"ORG:{_vc(D.BRAND)}",
        "X-ABShowAs:COMPANY",
        f"TEL;TYPE=WORK,VOICE:{D.PHONE_TEL}",
        f"EMAIL;TYPE=INTERNET,WORK:{D.EMAIL}",
        f"ADR;TYPE=WORK:;;{_vc(street)};{_vc(city)};;{postcode};Россия",
        f"URL:{D.SITE_URL}",
        f"GEO:{lat};{lon}",
        f"NOTE:{_vc(note)}",
        "END:VCARD",
    ]
    return [part for prop in props for part in _fold(prop)]
