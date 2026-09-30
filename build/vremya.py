# -*- coding: utf-8 -*-
"""«Когда удобно приехать?» — a wish for the day and the part of the day, in the request form (step 2, under
«Или опишите задачу для автосервиса») and in the call-back modal (under «Комментарий»).

It is a wish, not a booking: the picker never says a time is free. The choice becomes one line of the text the backend
already receives — request_part[what] in the form, message in the modal, no new fields:
    «Удобно приехать: пт, 2 октября, утром (9–12)»
vremya.js writes that line at the top of the text, replaces it when the choice changes and removes it when the choice
is cleared; the visitor's own words (and the texts «Что стучит?» and «Зима» add) stay as they are.

The days come from D.HOURS and nothing else: otkryto.week() turns it into seven days of minutes (Sunday is not in
D.HOURS, so it is closed). Each part of the day (PARTS) is a window of the clock cut by that day's hours, so on a
weekday the evening is 15–19 and on Saturday 15–17. The markup carries that as JSON in data-vremya; vremya.js counts
the 14 days in Moscow time and drops today's parts that are over. Without JS the picker stays hidden and the form is
exactly as it was.
"""
from __future__ import annotations

import json

from . import data as D
from . import otkryto
from .icons import icon

esc = D.esc

DAYS_AHEAD = 14   # today and the 13 days after it
LEAD = 60         # minutes: today's part of the day is offered while at least an hour of it is left
# (key, word in the message line, title on the chip, window from, to in minutes); the window is cut by the day's hours
PARTS = (
    ("morning", "утром", "Утром", 0, 12 * 60),
    ("day", "днём", "Днём", 12 * 60, 15 * 60),
    ("evening", "вечером", "Вечером", 15 * 60, 24 * 60),
)

# every text of the picker; the owner confirms them (notes/perk-vremya.md)
TEXTS = {
    "title": "Когда удобно приехать?",
    "optional": "необязательно",
    "clear": "Сбросить",
    "clear_sr": "день и время",
    "days_label": "День",
    "parts_label": "Время",
    "note": "Это пожелание, а не запись: менеджер свяжется с вами в рабочие часы.",
    "where_form": "В заявке:",
    "where_modal": "В сообщении:",
    # used by vremya.js
    "prefix": "Удобно приехать:",
    "any": "Любое время",
    "any_line": "в любое время",
    "today": "сегодня",
    "tomorrow": "завтра",
    "closed": "выходной",
    "late": "уже поздно",
    "part_sr": "{word}, с {from} до {to}",
    "expired": "Выбранное время уже прошло — выберите другое.",
    "cleared": "День и время сброшены.",
}
_JS_TEXTS = ("prefix", "any", "any_line", "today", "tomorrow", "closed", "late", "part_sr", "expired", "cleared")


def _check() -> None:
    """A mistake in the constants is a build error, not a picker that quietly offers nonsense."""
    keys = [p[0] for p in PARTS]
    if len(set(keys)) != len(keys) or "any" in keys:
        raise ValueError(f"vremya: ключи частей дня {keys}")
    for key, word, title, start, end in PARTS:
        if not (0 <= start < end <= 24 * 60) or not word.strip() or not title.strip():
            raise ValueError(f"vremya: часть дня {key!r}")
    if not 1 <= DAYS_AHEAD <= 31 or not 0 <= LEAD < 24 * 60:
        raise ValueError("vremya: DAYS_AHEAD или LEAD")
    if not any(otkryto.week(D.HOURS)):
        raise ValueError("vremya: в D.HOURS нет ни одного рабочего дня")


def config(where: str) -> dict:
    """data-vremya: the week of D.HOURS, the parts of the day, the window and the texts vremya.js needs."""
    _check()
    return {
        "week": otkryto.week(D.HOURS),
        "days": DAYS_AHEAD,
        "lead": LEAD,
        "parts": [{"key": k, "word": w, "title": t, "from": a, "to": b} for k, w, t, a, b in PARTS],
        "t": {**{k: TEXTS[k] for k in _JS_TEXTS}, "where": where},
    }


def picker(key: str, target: str, where: str, cls: str = "", fold: bool = False) -> str:
    """The picker for the text field with id `target`. key keeps the ids unique: the request form and the modal share a
    page. Buttons only, no named inputs, so the form posts exactly the fields it posted before.
    fold: the question is a button that opens the days (the modal stays as short as it was for those who only want
    a call). hidden: without JS it is never shown; vremya.js fills in the days and then shows it."""
    data = esc(json.dumps(config(where), ensure_ascii=False, separators=(",", ":")))
    t = {k: esc(v) for k, v in TEXTS.items()}
    title = (f'{icon("calendar")}<span class="vr__tt"><span class="vr__q">{t["title"]}</span>'
             f'<span class="vr__opt">{t["optional"]}</span></span>')
    if fold:
        title = (f'<button class="vr__title vr__toggle" id="vr-{key}-title" type="button" aria-expanded="false" '
                 f'aria-controls="vr-{key}-body" data-vr-toggle>{title}{icon("chevron", "vr__chev")}</button>')
    else:
        title = f'<p class="vr__title" id="vr-{key}-title">{title}</p>'
    classes = " ".join(c for c in ("vr", "vr--fold" if fold else "", cls) if c)
    return (
        f'<div class="{classes}" id="vr-{key}" role="group" aria-labelledby="vr-{key}-title" aria-describedby="vr-{key}-note" '
        f'data-vremya="{data}" data-vr-for="{esc(target)}" hidden>'
        f'<div class="vr__head">{title}</div>'
        f'<div class="vr__body" id="vr-{key}-body"{" hidden" if fold else ""} data-vr-body>'
        f'<div class="vr__days" role="radiogroup" aria-label="{t["days_label"]}" data-vr-days></div>'
        f'<div class="vr__parts" role="radiogroup" aria-label="{t["parts_label"]}" data-vr-parts hidden></div>'
        f'</div>'
        # what went into the text, and «Сбросить» that takes it out again
        f'<div class="vr__status" data-vr-status hidden>{icon("check", "vr__ok")}{icon("hazard", "vr__warn")}'
        f'<div class="vr__sbody"><div class="vr__srow"><span class="vr__where">{esc(where)}</span>'
        f'<button class="vr__clear" type="button" data-vr-clear hidden>{icon("close")}<span>{t["clear"]}</span>'
        f'<span class="sr-only"> {t["clear_sr"]}</span></button></div>'
        f'<p class="vr__line" data-vr-line></p></div></div>'
        f'<p class="vr__note" id="vr-{key}-note">{t["note"]}</p>'   # screen readers hear it on entering the group
        f'<p class="sr-only" aria-live="polite" data-vr-live></p>'
        f'</div>'
    )


def in_form() -> str:
    """Step 2 of the request form, under «Или опишите задачу для автосервиса» (#request_what): the days are open."""
    return picker("rq", "request_what", TEXTS["where_form"])


def in_modal() -> str:
    """The call-back modal, under «Комментарий» (#call-msg): a whole row of its two-column grid, folded."""
    return picker("call", "call-msg", TEXTS["where_modal"], cls="span-2", fold=True)
