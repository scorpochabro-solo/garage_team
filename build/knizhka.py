# -*- coding: utf-8 -*-
"""«Моя машина» — the car's service book in the visitor's own browser (page /moya-mashina/).

What the page does (src/assets/js/knizhka.js, src/assets/css/knizhka.css):
- the passport: make, model, year, engine size, VIN (optional, checked and normalised), current mileage and the date
  it was entered;
- the log of works: date, mileage, quick marks (WORKS) and free text, a note; edit and delete (asks first);
- the next service from the owner's own interval, «every … km or … months, whichever comes first», counted from the
  last entry marked «ТО»: what is left in km and days, two gauges, an estimated date and a calendar reminder (.ics,
  made in the browser). No interval is suggested anywhere: the numbers come from the owner's service book;
- «Записаться»: the call modal (G.openModal) with the car and the chosen works; a JSON copy, import (merge or
  replace), print, delete everything.
Everything is kept in one localStorage key of this browser (STORAGE_KEY) and sent nowhere.

This module holds the markup and every phrase. Static phrases are in the HTML (search engines and the owner read
them there); the ones the script puts together (states, errors, messages) go to the page as JSON in data-kn-conf.
Two hooks used by build/layout.py: footer_link() (the footer) and fill_button() (the request form, «Заполнить из
«Моей машины»»: shown by knizhka.js only when a car is saved in this browser). The page itself is registered in
build/static_pages.py (render_moya_mashina), its title and description are data/page_seo.json → "moya_mashina".
"""
from __future__ import annotations

import json

from . import data as D
from .icons import icon

esc = D.esc

PATH = "/moya-mashina/"
SEO_KEY = "moya_mashina"
TO_PAGE = "/services/planovoe-to.html"   # «Что входит в плановое ТО» under «Записаться»: an existing service page
STORAGE_KEY = "garage.knizhka.v1"   # the same constant is KEY in knizhka.js (tests/test_knizhka.py checks)

# defaults for data/page_seo.json → "moya_mashina" (that file wins)
TITLE = "Сервисная книжка автомобиля в браузере — «Моя машина» | Гараж"
DESCRIPTION = ("Сервисная книжка в браузере: паспорт машины, журнал работ и расчёт, сколько осталось до ТО по вашему "
               "интервалу. Данные хранятся только в вашем браузере.")
H1 = "Моя машина"
H1_SUB = "сервисная книжка в браузере"
EYEBROW = "Без регистрации и приложений"
LEAD = ("Записывайте, что и когда делали с машиной, и смотрите, сколько осталось до следующего ТО. "
        "Всё хранится только в этом браузере.")
PRIVACY = "Данные хранятся только в этом браузере и никуда не отправляются."
PRIVACY_MORE = "Мы их не видим. Чтобы не потерять записи, время от времени сохраняйте копию файлом."

# quick marks of a log entry and of «Записаться»: key, label, words for the message («Хочу записаться: ТО, фильтры.»)
WORKS = [
    ("to", "ТО", "ТО"),
    ("oil", "Замена масла", "замена масла"),
    ("filters", "Фильтры", "фильтры"),
    ("brakes", "Тормоза", "тормоза"),
    ("tires", "Шины", "шины"),
    ("diag", "Диагностика", "диагностика"),
]

# phrases the script assembles; {name} is filled in by knizhka.js, p… are plural forms (one, few, many)
TEXTS = {
    # storage
    "storeOff": ("Браузер не даёт сохранять данные — так бывает в режиме инкогнито или когда сайтам запрещено "
                 "хранить данные. Книжка работает, но записи пропадут, когда вы закроете вкладку. Сохраните копию файлом."),
    "storeFull": "Не получилось сохранить: в браузере кончилось место для данных сайтов. Сохраните копию файлом.",
    "storeBroken": "Сохранённая книжка не читается. Если у вас есть копия файлом — загрузите её.",
    # passport
    "noCar": "Паспорт не заполнен",
    "noCarHint": "Впишите марку и модель — они попадут в заявку и в напоминание.",
    "none": "не указан",
    "kmAt": "пробег на {date}",
    "kmNone": "пробег не указан",
    "kmSr": "Пробег {km}\u00a0км на {date}",
    "kmHintNew": "Дата запишется сама — сегодняшняя.",
    "kmHintAt": "Записан {date}. Если впишете новый, дата станет сегодняшней.",
    "errBrand": "Укажите марку",
    "errModel": "Укажите модель",
    "errYear": "Год — четыре цифры, от 1900 до {max}",
    "errKm": "Пробег — целое число километров, не больше 2 000 000",
    "errKmLess": "Меньше, чем записано раньше ({km}\u00a0км). Если тогда ошиблись — поправьте в паспорте.",
    "vinLength": "В VIN 17 знаков, а здесь {n}",
    "vinIoq": "В VIN не бывает букв I, O и Q — возможно, это цифры 1 и 0",
    "vinChars": "В VIN только латинские буквы и цифры",
    "vinFixed": "Русские буквы заменены на такие же латинские",
    "carSaved": "Паспорт сохранён",
    "kmSaved": "Пробег записан",
    # the interval and the next service
    "errInterval": "Впишите километры, месяцы или и то и другое",
    "errIntervalKm": "Километры — от 100 до 200 000",
    "errIntervalMonths": "Месяцы — от 1 до 120",
    "intervalSaved": "Интервал сохранён",
    "rule": "каждые {km}\u00a0км или {months} — что наступит раньше",
    "ruleKm": "каждые {km}\u00a0км",
    "ruleMonths": "каждые {months}",
    "headOk": "Примерно {date}",
    "headSoon": "Скоро: примерно {date}",
    "headOver": "Пора на ТО",
    "headGuess": "Похоже, пора на ТО",
    "headKm": "Осталось {km}\u00a0км",
    "headNoKm": "Не хватает пробега",
    "subBoth": "Раньше наступит срок по {by}.",
    "subOne": "Считаем по {by}.",
    "byKm": "пробегу",
    "byTime": "времени",
    "subOverKm": "Пробег больше интервала на {km}\u00a0км.",
    "subKmReached": "Пробег дошёл до интервала.",
    "subOverTime": "Срок прошёл {days} назад.",
    "subToday": "Срок — сегодня.",
    "subNoDate": "Дату посчитаем, когда станет понятен ваш средний пробег.",
    "left": "Осталось",
    "overKm": "Больше интервала на",
    "overTime": "Просрочено на",
    "today": "Сегодня",
    "meterKm": "Пройдено {used} из {all}\u00a0км",
    "meterTime": "Прошло {used} из {all}",
    "noKmInterval": "Интервал по пробегу не задан.",
    "noTimeInterval": "Интервал по времени не задан.",
    "noBaseKm": "В записи о последнем ТО нет пробега — впишите его, чтобы считать по километрам.",
    "noteRate": "Дату по пробегу считаем по вашему среднему: около {km}\u00a0км в день.",
    "noteNoRate": ("Чтобы оценить дату по пробегу, обновляйте пробег: нужно хотя бы две недели поездок "
                   "после ТО."),
    "noteGuess": "По вашему среднему пробегу срок по километрам уже подошёл. Обновите пробег — пересчитаем.",
    "icsNoDate": "Напоминание в календарь можно будет добавить, когда станет понятна дата.",
    "icsSummary": "ТО: {car}",
    "icsSummaryNoCar": "ТО по сервисной книжке",
    "icsDesc": ("Примерная дата из «Моей машины» на сайте автосервиса «Гараж». Интервал: {rule}. "
                "Последнее ТО: {last}. Записаться: {phone}."),
    "icsAlarm": "Завтра ТО: {car}",
    "icsFile": "napominanie-to.ics",
    "icsDone": "Откройте файл {file}, чтобы добавить напоминание в календарь",
    # the log
    "entryNew": "Новая запись",
    "entryEdit": "Изменить запись",
    "errDate": "Укажите дату",
    "errFuture": "Дата не может быть позже сегодняшней",
    "errWhat": "Отметьте работу или опишите, что сделано",
    "errFull": "В журнале уже 2000 записей — больше не поместится",
    "added": "Запись добавлена",
    "addedKm": "Запись добавлена, пробег в паспорте обновлён",
    "saved": "Запись сохранена",
    "deleted": "Запись удалена",
    "edit": "Изменить",
    "remove": "Удалить",
    "editAria": "Изменить запись от {date}",
    "removeAria": "Удалить запись от {date}",
    "stamp": "ТО",
    "tagsAria": "Что сделано",
    "entryKmNone": "пробег не указан",
    "delTitle": "Удалить запись?",
    "delText": "Запись от {date} исчезнет из журнала. Отменить это нельзя.",
    "delOk": "Удалить",
    # «Записаться»
    "bookWorks": "Хочу записаться: {works}.",
    "bookNone": "Хочу записаться в автосервис.",
    "bookCar": "Машина: {car}.",
    "bookLast": "Последнее ТО: {last}.",
    "carKm": "пробег {km}\u00a0км",
    # the copy, import, delete everything, print
    "jsonFile": "moya-mashina-{date}.json",
    "jsonDone": "Копия сохранена: {file}",
    "importTitle": "Загрузить книжку из файла?",
    "importAsk": "В файле: {what}. Объединить с книжкой в этом браузере или заменить её?",
    "importNoCar": "машина не указана",
    "importMerge": "Объединить",
    "importReplace": "Заменить",
    "importDone": "Книжка загружена: {n}",
    "importMerged": "Готово, добавлено: {n}",
    "importNothing": "Новых записей в файле нет",
    "importSkipped": "Пропущено неполных записей: {n}",
    "import_format": "Это не файл «Моей машины»",
    "import_newer": "Файл сохранён более новой версией книжки — обновите страницу и попробуйте снова",
    "import_big": "В файле слишком много записей",
    "importBroken": "Файл повреждён: это не JSON",
    "importLarge": "Файл слишком большой — это не копия книжки",
    "importRead": "Не получилось прочитать файл",
    "wipeTitle": "Удалить все данные?",
    "wipeText": ("Паспорт машины, журнал и интервал ТО удалятся из этого браузера. Вернуть их можно будет только "
                 "из копии файлом."),
    "wipeOk": "Удалить всё",
    "wipeDone": "Все данные удалены",
    "cancel": "Отмена",
    "noDownload": "Этот браузер не умеет сохранять файлы",
    "printTitle": "Сервисная книжка",
    "printRule": "Интервал ТО: {rule}",
    "printNext": "Следующее ТО: {text}",
    "printLeft": "осталось {what}",
    "printLog": "Журнал работ",
    "printEmpty": "Записей пока нет.",
    "printFoot": "Распечатано {date} · {url} · автосервис «Гараж», {phone}",
    "printCols": ["Дата", "Пробег, км", "Что сделано", "Заметка", "Отметка сервиса"],
    "pDays": ["день", "дня", "дней"],
    "pMonths": ["месяц", "месяца", "месяцев"],
    "pEntries": ["запись", "записи", "записей"],
}

_S = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
# line icons of this page only (24×24, stroke 1.6 as build/icons.py); the shared sprite stays as it is
_ICONS = {
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="1.5"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3M12 14.5v2.5"/>',
    "book": ('<path d="M5.5 3.5H17a1.5 1.5 0 0 1 1.5 1.5v15.5H7.5a2 2 0 0 1-2-2z"/><path d="M5.5 18.5a2 2 0 0 1 2-2h11"/>'
             '<path d="M9 7.5h6M9 10.5h4"/>'),
    "download": '<path d="M12 4v11M7.5 10.5 12 15l4.5-4.5M4.5 16.5v3h15v-3"/>',
    "upload": '<path d="M12 15V4M7.5 8.5 12 4l4.5 4.5M4.5 16.5v3h15v-3"/>',
    "print": '<path d="M7 9V3.5h10V9"/><rect x="3.5" y="9" width="17" height="8" rx="1.5"/><path d="M7 14h10v6.5H7zM17 11.5h.5"/>',
    "trash": '<path d="M4 6.5h16M9.5 6.5V4h5v2.5M6.5 6.5l1 13.5h9l1-13.5M10 10v6.5M14 10v6.5"/>',
    "pencil": '<path d="M15.5 4.5l4 4L9 19H5v-4zM13 7l4 4"/>',
    "odo": '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l3.5-4.5M6.8 12.8l1 .5M12 9v1.2M17.2 12.8l-1 .5"/>',
}


def _svg(name: str, cls: str = "") -> str:
    return f'<svg class="{("ic " + cls).strip()}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><g {_S}>{_ICONS[name]}</g></svg>'


def _sprite() -> str:
    """Symbols for the icons the script draws into the log (edit, delete): <use href="#kn-i-…">."""
    symbols = "".join(f'<symbol id="kn-i-{n}" viewBox="0 0 24 24"><g {_S}>{_ICONS[n]}</g></symbol>' for n in ("pencil", "trash"))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="sprite" aria-hidden="true" focusable="false" '
            f'style="position:absolute;width:0;height:0;overflow:hidden">{symbols}</svg>')


# ---------- hooks for build/layout.py ----------
def footer_link() -> str:
    """The footer (every page): the way to the book."""
    return (f'<a class="kn-foot" href="{PATH}"><span class="kn-foot__ic">{_svg("book")}</span>'
            f'<span class="kn-foot__t"><b>Моя машина</b><small>сервисная книжка в браузере</small></span></a>')


def fill_button() -> str:
    """The request form, step 1 (every page with the form): hidden until knizhka.js finds a saved car."""
    return (f'<button class="kn-fill" type="button" data-kn-fill="{esc("Машина подставлена из «Моей машины»")}" hidden>'
            f'{_svg("book")}<span class="kn-fill__t">Заполнить из «Моей машины»</span>'
            f'<span class="kn-fill__car" data-kn-fill-car></span></button>')


# ---------- page parts ----------
def h1_html() -> str:
    """«Моя машина» and, as a neon line under it, what it is (the search engines read both as the heading)."""
    return f'{esc(H1)} <span class="kn-h1-sub">{esc(H1_SUB)}</span>'   # the space keeps the two apart for screen readers


def _chips(name: str, legend: str, hide_legend: bool = False, describedby: str = "") -> str:
    items = "".join(
        f'<label class="kn-chip"><input type="checkbox" name="{name}" value="{key}" autocomplete="off">'
        f'<span>{esc(label)}</span></label>' for key, label, _ in WORKS)
    legend_cls = "sr-only" if hide_legend else "field__label kn-chips__legend"
    desc = f' aria-describedby="{describedby}"' if describedby else ""
    return (f'<fieldset class="kn-chips"{desc}><legend class="{legend_cls}">{esc(legend)}</legend>'
            f'<div class="kn-chips__row">{items}</div></fieldset>')


_CAR = ('<svg class="kn-bay__car" viewBox="0 0 240 100" aria-hidden="true" focusable="false"><g fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M18 76 14 64Q14 55 24 52L60 47Q72 33 86 29L136 27Q150 27 160 36L172 46 206 51Q224 54 226 64V72Q226 76 220 76H200'
        'A18 18 0 0 0 164 76H76A18 18 0 0 0 40 76Z"/>'
        '<path d="M68 46Q77 36 88 33L110 32V46ZM116 32 136 31Q146 31 154 38L161 46H116ZM113 49V70M60 49H172M210 57 221 59M16 59 22 58"/>'
        '<circle cx="58" cy="76" r="13"/><circle cx="58" cy="76" r="5"/><circle cx="182" cy="76" r="13"/><circle cx="182" cy="76" r="5"/>'
        '<path d="M4 90H236" stroke-dasharray="2 6" stroke-width="1.2"/></g></svg>')


def _start() -> str:
    """First visit: the garage bay with its shutter down and the invitation; «Завести книжку» rolls the shutter up."""
    steps = [
        ("Паспорт", "марка, модель, год, VIN и пробег"),
        ("Журнал", "что и когда делали, с пробегом и заметками"),
        ("Следующее ТО", "сколько осталось по интервалу из вашей книжки — и напоминание в календарь"),
        ("Копия и печать", "чтобы не потерять записи и показать их мастеру"),
    ]
    items = "".join(f'<li><span class="kn-start__n">{i:02d}</span><span><b>{esc(t)}</b> — {esc(d)}</span></li>'
                    for i, (t, d) in enumerate(steps, 1))
    return f"""<div class="kn-start" data-kn-start>
      <div class="kn-bay" aria-hidden="true">
        <i class="kn-bay__cord"></i><i class="kn-bay__lamp"></i><i class="kn-bay__light"></i>
        <p class="kn-bay__sign">Моя машина</p>
        <div class="kn-bay__door">
          <div class="kn-bay__inside">{_CAR}</div>
          <div class="kn-bay__shutter"><span class="kn-bay__no">Бокс 01</span></div>
        </div>
      </div>
      <div class="kn-start__panel">
        <p class="eyebrow">// Бортовой журнал</p>
        <h2 class="kn-start__title" id="kn-start-title">Заведите книжку своей машины</h2>
        <div class="kn-start__intro" data-kn-intro>
          <p class="kn-start__lead">Как бумажная сервисная книжка, только всегда под рукой и сама считает, когда следующее ТО.</p>
          <ol class="kn-start__list">{items}</ol>
          <div class="kn-start__actions">
            <button class="btn btn--primary btn--lg" type="button" data-kn-go>{icon("plus")} Завести книжку</button>
            <button class="btn btn--ghost" type="button" data-kn-import>{_svg("upload")} Загрузить из файла</button>
          </div>
        </div>
        <div class="kn-slot" data-kn-slot="start">{_car_form()}</div>
      </div>
    </div>"""


def _car_form() -> str:
    return f"""<form class="kn-form kn-carform" data-kn-car-form novalidate hidden aria-labelledby="kn-c-title">
          <p class="kn-form__title" id="kn-c-title" tabindex="-1">Данные машины</p>
          <div class="form-grid form-grid--2">
            <div class="field"><label class="field__label" for="kn-c-brand">Марка <span class="req">*</span></label><input class="input" id="kn-c-brand" name="brand" type="text" maxlength="40" autocomplete="off" autocapitalize="words" enterkeyhint="next" placeholder="Как в СТС" required aria-describedby="kn-c-brand-err"><span class="field__error" id="kn-c-brand-err">{esc(TEXTS["errBrand"])}</span></div>
            <div class="field"><label class="field__label" for="kn-c-model">Модель <span class="req">*</span></label><input class="input" id="kn-c-model" name="model" type="text" maxlength="40" autocomplete="off" autocapitalize="words" enterkeyhint="next" placeholder="Как в СТС" required aria-describedby="kn-c-model-err"><span class="field__error" id="kn-c-model-err">{esc(TEXTS["errModel"])}</span></div>
            <div class="field"><label class="field__label" for="kn-c-year">Год выпуска</label><input class="input" id="kn-c-year" name="year" type="text" inputmode="numeric" maxlength="4" autocomplete="off" enterkeyhint="next" aria-describedby="kn-c-year-err"><span class="field__error" id="kn-c-year-err"></span></div>
            <div class="field"><label class="field__label" for="kn-c-engine">Объём двигателя, л</label><input class="input" id="kn-c-engine" name="engine" type="text" inputmode="decimal" maxlength="24" autocomplete="off" enterkeyhint="next" placeholder="Например, 1,6"></div>
            <div class="field span-2"><label class="field__label" for="kn-c-vin">VIN</label><input class="input kn-mono" id="kn-c-vin" name="vin" type="text" maxlength="24" autocomplete="off" autocorrect="off" autocapitalize="characters" spellcheck="false" enterkeyhint="next" aria-describedby="kn-c-vin-hint kn-c-vin-err"><span class="field__hint" id="kn-c-vin-hint">Необязательно. 17 знаков из СТС или с таблички на кузове. <span class="kn-vin-note" data-kn-vin-note hidden>{esc(TEXTS["vinFixed"])}</span></span><span class="field__error" id="kn-c-vin-err"></span></div>
            <div class="field span-2"><label class="field__label" for="kn-c-km">Пробег сейчас, км</label><input class="input" id="kn-c-km" name="km" type="text" inputmode="numeric" maxlength="9" autocomplete="off" enterkeyhint="done" aria-describedby="kn-c-km-hint kn-c-km-err"><span class="field__hint" id="kn-c-km-hint" data-kn-km-hint>{esc(TEXTS["kmHintNew"])}</span><span class="field__error" id="kn-c-km-err"></span></div>
          </div>
          <div class="kn-form__actions"><button class="btn btn--ghost" type="button" data-kn-car-cancel>Отмена</button><button class="btn btn--primary" type="submit">{icon("check")} Сохранить</button></div>
        </form>"""


def _plate() -> str:
    """The passport as a riveted steel plate: make and model, year, engine, VIN, a mechanical odometer."""
    return f"""<section class="kn-car" aria-labelledby="kn-car-title">
        <div class="kn-plate" data-kn-plate tabindex="-1">
          <div class="kn-plate__top">
            <h2 class="kn-plate__label" id="kn-car-title">Паспорт машины</h2>
            <button class="kn-link" type="button" data-kn-car-edit>{_svg("pencil")}<span>Изменить</span></button>
          </div>
          <p class="kn-plate__name" data-kn-name></p>
          <p class="kn-plate__hint" data-kn-name-hint hidden>{esc(TEXTS["noCarHint"])}</p>
          <dl class="kn-plate__specs">
            <div><dt>Год</dt><dd data-kn-year></dd></div>
            <div><dt>Двигатель</dt><dd data-kn-engine></dd></div>
            <div class="kn-plate__vin"><dt>VIN</dt><dd data-kn-vin></dd></div>
          </dl>
          <div class="kn-plate__odo">
            <div class="kn-odo" data-kn-odo aria-hidden="true"><span class="kn-odo__drums" data-kn-drums></span><span class="kn-odo__u">км</span></div>
            <p class="sr-only" data-kn-odo-sr></p>
            <p class="kn-odo__cap"><span data-kn-odo-cap></span> <button class="kn-link" type="button" data-kn-odo-open>{_svg("odo")}<span>Обновить пробег</span></button></p>
          </div>
          <form class="kn-odoform" data-kn-odo-form novalidate hidden>
            <div class="field">
              <label class="field__label" for="kn-o-km">Пробег сейчас, км</label>
              <div class="kn-odoform__row"><input class="input" id="kn-o-km" name="km" type="text" inputmode="numeric" maxlength="9" autocomplete="off" enterkeyhint="done" aria-describedby="kn-o-km-err"><button class="btn btn--primary" type="submit">Записать</button><button class="btn btn--ghost kn-odoform__x" type="button" data-kn-odo-cancel aria-label="Не обновлять пробег">{icon("close")}</button></div>
              <span class="field__error" id="kn-o-km-err"></span>
            </div>
          </form>
        </div>
        <div class="kn-slot" data-kn-slot="book"></div>
      </section>"""


def _meter(kind: str, label: str) -> str:
    return f"""<div class="kn-meter" data-kn-meter="{kind}">
            <p class="kn-meter__label">{esc(label)}</p>
            <div class="kn-meter__body" data-body>
              <p class="kn-meter__value"><span class="kn-meter__pre" data-pre></span> <b data-val></b></p>
              <div class="kn-meter__track" role="meter" aria-label="{esc(label)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" data-track><i class="kn-meter__fill"></i><i class="kn-meter__mark"></i></div>
              <p class="kn-meter__ends"><span data-a></span><span data-b></span></p>
            </div>
            <p class="kn-meter__none" data-none hidden></p>
          </div>"""


def _next() -> str:
    """The next service: the owner's interval, two gauges (km, time), the estimated date, calendar, «Записаться на ТО»."""
    return f"""<section class="kn-next" data-kn-next data-state="setup" aria-labelledby="kn-next-title">
        <div class="kn-next__top">
          <h2 class="kn-next__label" id="kn-next-title">Следующее ТО</h2>
          <p class="kn-next__rule" data-kn-rule hidden><span data-kn-rule-text></span> <button class="kn-link" type="button" data-kn-interval-edit>{_svg("pencil")}<span>Изменить</span></button></p>
        </div>
        <div class="kn-next__main" data-kn-main hidden>
          <p class="kn-next__head" data-kn-head tabindex="-1"></p>
          <p class="kn-next__sub" data-kn-sub></p>
          <div class="kn-meters">
            {_meter("km", "По пробегу")}
            {_meter("time", "По времени")}
          </div>
          <p class="kn-next__note" data-kn-note></p>
          <div class="kn-next__actions">
            <button class="btn btn--ghost kn-ics" type="button" data-kn-ics>{icon("calendar")} <span>Добавить напоминание в календарь</span> <small aria-hidden="true">.ics</small></button>
            <button class="btn btn--primary" type="button" data-kn-book-to>{icon("phone")} Записаться на ТО</button>
          </div>
          <p class="kn-next__note kn-next__note--ics" data-kn-ics-note hidden></p>
        </div>
        <div class="kn-next__need" data-kn-need hidden>
          <p class="kn-next__head">Отметьте последнее ТО</p>
          <p class="kn-next__sub">Добавьте в журнал запись с отметкой «ТО» — от её даты и пробега начнётся отсчёт.</p>
          <button class="btn btn--primary" type="button" data-kn-add-to>{icon("plus")} Добавить запись о ТО</button>
        </div>
        <form class="kn-interval" data-kn-interval novalidate>
          <p class="kn-next__head kn-interval__head" data-kn-interval-head>Когда следующее ТО?</p>
          <p class="kn-interval__lead">Впишите интервал из сервисной книжки или инструкции к машине — у разных машин он разный. Посчитаем, что наступит раньше.</p>
          <div class="kn-interval__row">
            <span class="kn-interval__w">Каждые</span>
            <span class="kn-interval__f"><label class="sr-only" for="kn-i-km">Интервал ТО, километров</label><input class="input" id="kn-i-km" name="km" type="text" inputmode="numeric" maxlength="7" autocomplete="off" enterkeyhint="next" aria-describedby="kn-i-err"><span class="kn-interval__u" aria-hidden="true">км</span></span>
            <span class="kn-interval__w">или каждые</span>
            <span class="kn-interval__f kn-interval__f--m"><label class="sr-only" for="kn-i-months">Интервал ТО, месяцев</label><input class="input" id="kn-i-months" name="months" type="text" inputmode="numeric" maxlength="3" autocomplete="off" enterkeyhint="done" aria-describedby="kn-i-err"><span class="kn-interval__u" aria-hidden="true">мес.</span></span>
          </div>
          <p class="kn-interval__hint">Можно заполнить что-то одно.</p>
          <p class="kn-interval__err" id="kn-i-err" data-kn-interval-err hidden></p>
          <div class="kn-form__actions"><button class="btn btn--ghost btn--sm" type="button" data-kn-interval-cancel hidden>Отмена</button><button class="btn btn--primary btn--sm" type="submit">{icon("check")} Сохранить интервал</button></div>
        </form>
      </section>"""


def _entry_form() -> str:
    return f"""<form class="kn-form kn-entryform" data-kn-entry-form novalidate hidden aria-labelledby="kn-e-title">
          <p class="kn-form__title" id="kn-e-title" data-kn-entry-title tabindex="-1">{esc(TEXTS["entryNew"])}</p>
          <div class="form-grid form-grid--2">
            <div class="field"><label class="field__label" for="kn-e-date">Дата <span class="req">*</span></label><input class="input" id="kn-e-date" name="date" type="date" required aria-describedby="kn-e-date-err"><span class="field__error" id="kn-e-date-err"></span></div>
            <div class="field"><label class="field__label" for="kn-e-km">Пробег, км</label><input class="input" id="kn-e-km" name="km" type="text" inputmode="numeric" maxlength="9" autocomplete="off" aria-describedby="kn-e-km-err"><span class="field__error" id="kn-e-km-err"></span></div>
            <div class="field span-2">{_chips("works", "Что сделано", describedby="kn-e-works-err")}<span class="field__error" id="kn-e-works-err">{esc(TEXTS["errWhat"])}</span></div>
            <div class="field span-2"><label class="field__label" for="kn-e-text">Подробности</label><textarea class="textarea" id="kn-e-text" name="text" rows="3" maxlength="600" placeholder="Например: масло и масляный фильтр, воздушный фильтр салона"></textarea></div>
            <div class="field span-2"><label class="field__label" for="kn-e-note">Заметка</label><input class="input" id="kn-e-note" name="note" type="text" maxlength="300" autocomplete="off" placeholder="Например: где делали, номера запчастей"></div>
          </div>
          <div class="kn-form__actions"><button class="btn btn--ghost" type="button" data-kn-entry-cancel>Отмена</button><button class="btn btn--primary" type="submit">{icon("check")} Сохранить запись</button></div>
        </form>"""


def _log() -> str:
    return f"""<section class="kn-log" aria-labelledby="kn-log-title">
        <div class="kn-log__head">
          <h2 class="kn-log__title" id="kn-log-title">Журнал работ</h2>
          <span class="kn-log__count" data-kn-count></span>
          <button class="btn btn--primary btn--sm" type="button" data-kn-add aria-expanded="false">{icon("plus")} Добавить запись</button>
        </div>
        {_entry_form()}
        <div class="kn-log__list" data-kn-list></div>
        <div class="kn-log__empty" data-kn-empty>
          <p class="kn-log__empty-t">Записей пока нет</p>
          <p>Начните с последнего ТО: дата, пробег и отметка «ТО» — от этой записи посчитаем следующее.</p>
          <button class="btn btn--ghost" type="button" data-kn-add-to>{icon("plus")} Добавить запись о ТО</button>
        </div>
      </section>"""


def _side() -> str:
    if TO_PAGE not in D.BY_PATH:
        raise ValueError(f"knizhka: нет страницы услуги {TO_PAGE}")
    return f"""<div class="kn-side">
        <section class="kn-card kn-booking" aria-labelledby="kn-booking-title">
          <h2 class="kn-card__title" id="kn-booking-title">Записаться в «Гараж»</h2>
          <p class="kn-card__text">Отметьте работы — машина из паспорта сама подставится в заявку на звонок.</p>
          {_chips("book-works", "Работы для записи", hide_legend=True)}
          <button class="btn btn--primary btn--block" type="button" data-kn-book>{icon("phone")} Записаться</button>
          <a class="kn-card__more" href="{TO_PAGE}">Что входит в плановое ТО {icon("arrow-up-right")}</a>
        </section>
        <section class="kn-card kn-backup" aria-labelledby="kn-backup-title">
          <h2 class="kn-card__title" id="kn-backup-title">Копия и печать</h2>
          <p class="kn-card__text">Книжка живёт только в этом браузере: если очистить его или сменить телефон, записи пропадут, а Safari на iPhone сам стирает данные сайтов, на которые давно не заходили. Сохраните копию файлом — её можно загрузить здесь же или на другом устройстве.</p>
          <div class="kn-tools">
            <button class="kn-tool" type="button" data-kn-export>{_svg("download")}<span>Сохранить копию</span><small>.json</small></button>
            <button class="kn-tool" type="button" data-kn-import>{_svg("upload")}<span>Загрузить из файла</span><small>.json</small></button>
            <button class="kn-tool" type="button" data-kn-print>{_svg("print")}<span>Распечатать</span><small>или в PDF</small></button>
            <button class="kn-tool kn-tool--danger" type="button" data-kn-wipe>{_svg("trash")}<span>Удалить все данные</span><small>из этого браузера</small></button>
          </div>
        </section>
      </div>"""


def _dialog() -> str:
    """One confirm window for delete, delete everything and import (merge or replace); buttons come from the script."""
    return f"""<dialog class="modal kn-dialog" id="kn-dialog" aria-labelledby="kn-dialog-title" aria-describedby="kn-dialog-text">
  <div class="modal__panel">
    <button class="modal__close" type="button" data-close aria-label="Закрыть">{icon("close")}</button>
    <h2 class="modal__title" id="kn-dialog-title"></h2>
    <p class="modal__lead" id="kn-dialog-text"></p>
    <div class="kn-dialog__actions" data-kn-dialog-actions></div>
  </div>
</dialog>"""


def _nojs() -> str:
    return f"""<noscript>
      <div class="kn-nojs">
        <p class="kn-nojs__title">Книжке нужен JavaScript</p>
        <p>Он считает, сколько осталось до ТО, и хранит записи в вашем браузере. Включите JavaScript в настройках браузера — и книжка заработает. А записаться можно и так — позвоните нам:</p>
        <a class="btn btn--primary" href="tel:{D.PHONE_TEL}">{icon("phone")} {esc(D.PHONE)}</a>
      </div>
    </noscript>"""


def _about() -> str:
    """How it works, visible without JS: what the page is, how the next service is counted, where the data lives."""
    steps = [
        ("Паспорт машины", "Марка, модель, год, объём двигателя, VIN и пробег с датой. VIN проверяем на опечатки: "
                           "17 знаков, латинские буквы и цифры, без I, O и Q; русские буквы, похожие на латинские, "
                           "заменяем сами."),
        ("Журнал работ", "Дата, пробег и что сделано: быстрые отметки «ТО», «Замена масла», «Фильтры», «Тормоза», "
                         "«Шины», «Диагностика», свои подробности и заметки. Записи можно исправить и удалить."),
        ("Следующее ТО", "Вы вписываете интервал из своей сервисной книжки: «каждые … км или … месяцев». От последней "
                         "записи с отметкой «ТО» считаем, что наступит раньше, и показываем, сколько осталось. Дату "
                         "можно добавить в календарь телефона — с напоминанием накануне."),
        ("Где хранятся данные", "Только в этом браузере на этом устройстве. На сервер ничего не отправляется, мы эти "
                                "данные не видим. Поэтому книжка сама не переедет на другой телефон — для этого есть "
                                "копия файлом. Данные машины попадают в заявку, только когда вы сами нажмёте "
                                "«Записаться» и отправите форму."),
    ]
    items = "".join(f'<li class="kn-how__item"><span class="kn-how__n">{i:02d}</span><h3 class="kn-how__t">{esc(t)}</h3>'
                    f'<p>{esc(d)}</p></li>' for i, (t, d) in enumerate(steps, 1))
    return f"""<section class="section section--tight kn-about" aria-labelledby="kn-about-title">
  <div class="wrap">
    <div class="sec-head">
      <div><p class="eyebrow">// Как это устроено</p><h2 class="h2 sec-head__title" id="kn-about-title">Книжка, которая<br>считает сама</h2></div>
      <p class="sec-head__aside">Как бумажная сервисная книжка: паспорт машины и журнал работ. Только ещё подсказывает, когда следующее ТО, и не теряется в бардачке.</p>
    </div>
    <ol class="kn-how">{items}</ol>
  </div>
</section>"""


def conf_json() -> str:
    """data-kn-conf: the phrases and the quick marks for knizhka.js."""
    works = [{"key": k, "label": label, "phrase": phrase} for k, label, phrase in WORKS]
    conf = {"texts": TEXTS, "works": works, "phone": D.PHONE}
    return esc(json.dumps(conf, ensure_ascii=False, separators=(",", ":")))


def body() -> str:
    """Everything below the page hero: the tool (hidden until the script starts it), the explanation, the dialog."""
    return f"""<section class="kn-sec">
  {_sprite()}
  <div class="wrap">
    <p class="kn-privacy">{_svg("lock")}<span><b>{esc(PRIVACY)}</b> {esc(PRIVACY_MORE)}</span></p>
    {_nojs()}
    <div class="kn" data-knizhka data-state="start" data-kn-conf="{conf_json()}" hidden>
      <div class="kn-alert" data-kn-alert role="alert" hidden></div>
      {_start()}
      <div class="kn-desk" data-kn-desk hidden>
      {_plate()}
      {_next()}
      {_log()}
      {_side()}
      </div>
      <div class="kn-print" data-kn-sheet></div>
      <input type="file" accept=".json,application/json" data-kn-file hidden tabindex="-1" aria-hidden="true">
    </div>
  </div>
</section>
{_about()}
{_dialog()}"""
