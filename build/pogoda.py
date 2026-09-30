# -*- coding: utf-8 -*-
"""«Пора переобуваться?» — the tyre-change hint from the live weather forecast, home-page section #pogoda (right before
«Готова ли машина к зиме?»).

The browser fetches the 10-day forecast for Nizhny Novgorod from Open-Meteo (free, no key, CORS allowed) only when the
section comes near the screen, keeps it in localStorage for two hours, checks its shape strictly and answers «пора ли
менять резину» by the usual rule of thumb (src/assets/js/pogoda.js):
  autumn (Sep–Nov)  winter tyres when the daily mean stays at +7 °C or below for STREAK days in a row (the past days
                    count), or when a night frost comes (the daily minimum at 0 °C or below): «Пора на зимнюю» when that
                    is today or tomorrow, «Скоро пора» with the date when it is later in the forecast, «Пока рано» else;
  spring (Mar–May)  the mirror, and more careful: summer tyres from the day after which every day of the forecast is
                    above +7 °C and frost-free, at least STREAK such days;
  summer, winter    a calm neutral state.
The days are drawn as min–max bars with the daily mean against the 0 °C line and the +7 °C guide line.

Every threshold, every phrase and the request address live here and reach the script as one JSON (#pogoda-data), so the
page and the script cannot disagree; tests/pogoda_verdict.cjs runs the script's own verdict in node on test forecasts.
Without JavaScript — and while the forecast loads, or when it cannot be had — the section shows the rule of thumb and
the booking button. Wording: general knowledge with «обычно», no prices, no promises, no laws and no dates of them.
"""
from __future__ import annotations

import json
from urllib.parse import urlencode

from . import data as D
from .icons import icon

esc = D.esc

# ---------- the forecast ----------
API = "https://api.open-meteo.com/v1/forecast"
SOURCE = ("Open-Meteo.com", "https://open-meteo.com/")
LICENCE = ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/deed.ru")   # Open-Meteo data: attribution required
TZ = "Europe/Moscow"
# short name in the script -> Open-Meteo daily variable and the unit the answer must come in
VARIABLES = {
    "min": ("temperature_2m_min", "°C"),
    "max": ("temperature_2m_max", "°C"),
    "mean": ("temperature_2m_mean", "°C"),
    "precip": ("precipitation_sum", "mm"),
    "snow": ("snowfall_sum", "cm"),
}
FORECAST_DAYS = 10          # today and nine more
PAST_DAYS = 3               # for the trend: a cold spell that began before today counts
MIN_DAYS = 7                # the answer needs at least this many forecast days from today
LIMITS = {"t": (-60, 50), "precip": (0, 500), "snow": (0, 300)}   # °C, mm, cm: anything outside is a broken answer

# ---------- the rule of thumb (general knowledge; the owner may tune the numbers) ----------
THRESHOLD = 7               # °C, daily mean: at or below it a day counts as cold (the upper end of «+5…+7 °C»)
BAND_LOW = 5                # °C: the lower end of that band, shaded on the chart
FROST = 0                   # °C: a daily minimum at or below it is a night frost
STREAK = 3                  # days in a row that make a cold (or a warm) spell
NOW_DAYS = 1                # the change comes today or tomorrow: «Пора…»; later in the forecast: «Скоро пора» + the date
SNOW_MIN = 0.1              # cm of fresh snow that mark a day with a snowflake
PRECIP_MIN = 1              # mm: from here a day's precipitation is named for screen readers
SEASONS = {"autumn": (9, 10, 11), "spring": (3, 4, 5), "summer": (6, 7, 8), "winter": (12, 1, 2)}

# ---------- the browser ----------
CACHE_KEY = "garage.pogoda.v1"
CACHE_MINUTES = 120         # a stored forecast is used for two hours, and only on the same Moscow day
STALE_HOURS = 12            # the network fails: a stored forecast up to this old is shown, with its time
TIMEOUT_MS = 8000
SCALE_DEFAULT = (-5, 15)    # °C: where the guide lines stand before the forecast is there

# ---------- pages the section links to ----------
BOOK_PAGE = "/services/sinomontaz.html"
STORAGE_PAGE = "/services/hranenie-sin.html"
# never a target of this section (sensitive services): a link here fails the build, as in build/stuk.py
FORBIDDEN = ("udalenie", "cip-tuning", "ksenon", "tehosmotr")

NBSP = "\u00a0"
MINUS = "\u2212"


def temp(value: float, unit: bool = True) -> str:
    """7 -> «+7 °C» (unit=False: «+7°»), -3 -> «−3 °C», 0 -> «0 °C»: whole degrees, a real minus, no break before °C."""
    n = int(round(value))
    sign = "+" if n > 0 else (MINUS if n < 0 else "")
    return f"{sign}{abs(n)}{NBSP + '°C' if unit else '°'}"


def _plain(value: float) -> str:
    """7 -> «+7»: the number of temp() without the degree sign"""
    return temp(value, unit=False)[:-1]


THR = temp(THRESHOLD)                                   # «+7 °C»
BAND = f"{_plain(BAND_LOW)}…{THR}"                      # «+5…+7 °C»

# ---------- texts ----------
EYEBROW = "// Шины по погоде"
TITLE = "Пора переобуваться?"
ASIDE = "Смотрим прогноз погоды для Нижнего Новгорода на 10 дней и по простому правилу подсказываем, пора ли менять резину."
STATUS = "Когда переобуваться"
BIG_CAPTION = "среднесуточная температура, при которой обычно меняют резину"
RULE = ("Зимнюю резину обычно ставят, когда среднесуточная температура несколько дней подряд держится около {band} "
        "и ниже или начинаются ночные заморозки. Летнюю — весной, когда среднесуточная устойчиво выше {thr} "
        "и заморозки прошли.")
BOOK = "Записаться на шиномонтаж"
BOOK_PHONE = "Записаться: {phone}"                    # without JavaScript the button is a phone link
CHART_TITLE = "Температура по дням, °C"
LEGEND = {"range": "мин–макс", "mean": "средняя за сутки", "snow": "снег"}
LIST_LABEL = "Прогноз по дням"
SOURCE_LINE = "Прогноз: {source} ({licence}) · прогноз может меняться"
# every phrase the script may put on the page; {thr} and {band} are filled here, the rest by pogoda.js
TEXTS = {
    "status-loading": "Загружаем прогноз…",
    "status-ready": "Нижний Новгород · прогноз на {n}",
    "status-stale": "Нижний Новгород · прогноз от {when}",
    "status-error": "Прогноз не загрузился",
    "autumn-now": "Пора на зимнюю",
    "autumn-soon": "Скоро пора",
    "autumn-early": "Пока рано",
    "spring-now": "Пора на летнюю",
    "spring-soon": "Скоро пора",
    "spring-early": "Пока рано",
    "summer": "Сезон летней резины",
    "winter": "Сезон зимней резины",
    "kick-today": "уже сейчас",
    "kick-tomorrow": "с завтрашнего дня",
    "kick-autumn-soon": "на зимнюю — с {date}",
    "kick-spring-soon": "на летнюю — с {date}",
    "kick-autumn-early": "переобуваться на зимнюю",
    "kick-spring-early": "снимать зимнюю резину",
    "in-days": "через {n}",
    "from-today": "С сегодняшнего дня",
    "from-tomorrow": "С завтрашнего дня",
    "from-date": "С {date}",
    "on-today": "Сегодня",
    "on-tomorrow": "Завтра",
    "day-today": "сегодня",
    "day-tomorrow": "завтра",
    "in-a-row": "{n} подряд",
    "till-end": "до конца прогноза",
    "why-cold-since": "Среднесуточная температура уже {n} подряд не выше {thr}.",
    "why-cold-from": "{from} среднесуточная температура по прогнозу не выше {thr} — {span}.",
    "why-frost": "{on} по прогнозу заморозки: ночью до {min}.",
    "why-frost-also": "Заморозки по прогнозу — {day}, ночью до {min}.",
    "why-warm": "В ближайшие {n} среднесуточная температура выше {thr}, заморозков в прогнозе нет.",
    "why-short": "Среднесуточная температура опускается до {thr} и ниже лишь ненадолго, заморозков в прогнозе нет.",
    "why-warm-from": "{from} среднесуточная температура по прогнозу выше {thr}, заморозков нет.",
    "why-spring-frost": "По прогнозу ещё будут заморозки: ночью до {min}.",
    "why-spring-cold": "Среднесуточная температура по прогнозу ещё опускается до {low}.",
    "why-summer": "Зимнюю резину обычно ставят осенью, когда среднесуточная температура несколько дней держится около {band} и ниже.",
    "why-winter": "Летнюю резину обычно ставят весной, когда среднесуточная температура устойчиво выше {thr} и заморозки прошли.",
    "note-rebound": "С {date}, по прогнозу, снова теплеет — до {max} днём.",
    "msg-loading": "Загружаем прогноз погоды…",
    "msg-error": "Не удалось загрузить прогноз. Проверьте интернет и попробуйте ещё раз.",
    "msg-offline": "Нет подключения к интернету — прогноз загрузится, когда связь появится.",
    "retry": "Попробовать ещё раз",
    "updated": " · обновлён в {time}",
    "updated-stale": " · от {when}, свежий не загрузился",
    "today": "сегодня",
    "sr-day": "{day}: от {min} до {max}, в среднем {mean}{marks}.",
    "sr-today": "Сегодня, {date}",
    "sr-snow": ", снег",
    "sr-frost": ", заморозки",
    "sr-precip": ", осадки {mm} мм",
}
# the comment of the call-back modal: the season decides which tyres the visitor most likely wants
MESSAGES = {
    "autumn": "Шиномонтаж: хочу переобуться на зимнюю резину.",
    "spring": "Шиномонтаж: хочу переобуться на летнюю резину.",
    "any": "Шиномонтаж: хочу записаться на сезонную замену шин.",
}
MONTHS = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря")
WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
WEEKDAYS_FULL = ("понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье")
DAY_FORMS = ("день", "дня", "дней")


def _fill(text: str) -> str:
    """The rule's numbers go into a phrase here, once: the script never repeats them. A dash never starts a line:
    it is tied to the word before it."""
    return text.replace("{thr}", THR).replace("{band}", BAND).replace(" — ", NBSP + "— ")


def _check() -> None:
    """The build stops on a rule or a text that cannot work."""
    months = sorted(m for ms in SEASONS.values() for m in ms)
    if months != list(range(1, 13)):
        raise ValueError(f"pogoda: сезоны должны покрывать 12 месяцев ровно по разу, а не {months}")
    if not FROST < BAND_LOW < THRESHOLD:
        raise ValueError("pogoda: нужно FROST < BAND_LOW < THRESHOLD")
    if not 2 <= STREAK < MIN_DAYS <= FORECAST_DAYS <= 16:
        raise ValueError("pogoda: нужно 2 ≤ STREAK < MIN_DAYS ≤ FORECAST_DAYS ≤ 16 (Open-Meteo даёт до 16 дней)")
    if not 0 <= NOW_DAYS < STREAK or not 0 <= PAST_DAYS <= 7:
        raise ValueError("pogoda: NOW_DAYS или PAST_DAYS вне пределов")
    lo, hi = SCALE_DEFAULT
    if not lo < FROST < THRESHOLD < hi:
        raise ValueError("pogoda: линии 0 °C и порога должны быть внутри шкалы по умолчанию")
    titles = {f"{s}-{v}" for s in ("autumn", "spring") for v in ("now", "soon", "early")} | {"summer", "winter"}
    missing = titles - set(TEXTS)
    if missing:
        raise ValueError(f"pogoda: нет текстов {sorted(missing)}")
    for key in titles:
        if "{" in TEXTS[key]:
            raise ValueError(f"pogoda: в заголовке {key} не должно быть подстановок")
    if set(MESSAGES) != {"autumn", "spring", "any"}:
        raise ValueError("pogoda: MESSAGES — ровно autumn, spring, any")


def _page(path: str) -> tuple[str, str]:
    """(path, link text) of a service page; a missing or a sensitive page fails the build."""
    if any(bad in path for bad in FORBIDDEN):
        raise ValueError(f"pogoda: секция не должна вести на {path}")
    svc = D.BY_PATH.get(path)
    if svc is None:
        raise ValueError(f"pogoda: нет страницы услуги {path}")
    return path, svc.get("nav_name") or svc["h1"]


def api_url() -> str:
    """The one request of the section: daily values at the workshop's coordinates, days of the Moscow clock."""
    lat, lon = D.COORDS
    query = {
        "latitude": f"{lat}",
        "longitude": f"{lon}",
        "daily": ",".join(name for name, _ in VARIABLES.values()),
        "timezone": TZ,
        "forecast_days": FORECAST_DAYS,
        "past_days": PAST_DAYS,
    }
    return f"{API}?{urlencode(query, safe=',')}"


def season_of(month: int) -> str:
    """1…12 -> autumn | spring | summer | winter"""
    return next(s for s, months in SEASONS.items() if month in months)


def config() -> dict:
    """Everything pogoda.js needs: the request, the rule, the cache, the words. One JSON in the page."""
    _check()
    return {
        "url": api_url(),
        "at": list(D.COORDS),   # the answer's grid point must lie within half a degree of it
        "tz": TZ,
        "vars": {k: name for k, (name, _) in VARIABLES.items()},
        "units": {name: unit for name, unit in VARIABLES.values()},
        "past": PAST_DAYS, "forecast": FORECAST_DAYS, "minDays": MIN_DAYS,
        "limits": {k: list(v) for k, v in LIMITS.items()},
        "threshold": THRESHOLD, "band": BAND_LOW, "frost": FROST, "streak": STREAK, "nowDays": NOW_DAYS,
        "snowMin": SNOW_MIN, "precipMin": PRECIP_MIN,
        "seasons": {str(m): s for s, months in SEASONS.items() for m in months},
        "cacheKey": CACHE_KEY, "cacheMinutes": CACHE_MINUTES, "staleHours": STALE_HOURS, "timeout": TIMEOUT_MS,
        "months": list(MONTHS), "weekdays": list(WEEKDAYS), "weekdaysFull": list(WEEKDAYS_FULL), "dayForms": list(DAY_FORMS),
        "texts": {k: _fill(v) for k, v in TEXTS.items()},
        "messages": MESSAGES,
    }


def data_json() -> str:
    """#pogoda-data: the config for pogoda.js (and for tests/pogoda_verdict.cjs); «</» cannot end the script element."""
    return json.dumps(config(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


# ---------- markup ----------
_S = 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
# a snowflake in the line style of build/icons.py, drawn for 12–16 px: six arms with a pair of ticks each.
# pogoda.js copies the legend's one into the days with snow.
SNOW_SVG = (f'<svg class="ic pogoda-snow" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><g {_S}>'
            '<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"/>'
            '<path d="M9.6 4.6 12 7l2.4-2.4M9.6 19.4 12 17l2.4 2.4M3.9 10.8l3.3-.8-.9-3.3M20.1 13.2l-3.3.8.9 3.3'
            'M6.3 17.3l.9-3.3-3.3-.8M17.7 6.7l-.9 3.3 3.3.8"/></g></svg>')


def _pos(t: float) -> str:
    """A temperature on the default scale, 0 (bottom) … 1 (top): the empty chart before the forecast comes."""
    lo, hi = SCALE_DEFAULT
    return f"{(t - lo) / (hi - lo):.4f}"


def _card() -> str:
    """The verdict card. Without the forecast it shows the rule of thumb (the big «+5…+7 °C»); pogoda.js swaps the face."""
    preset = esc(json.dumps({"message": MESSAGES["any"]}, ensure_ascii=False))
    book, book_name = _page(BOOK_PAGE)
    storage, storage_name = _page(STORAGE_PAGE)
    links = "".join(f'<a class="pogoda-card__link" href="{href}">{icon(ic)}<span>{esc(name)}</span>{icon("arrow-up-right", "pogoda-card__go")}</a>'
                    for href, name, ic in ((book, book_name, "tire"), (storage, storage_name, "storage")))
    return f"""<div class="pogoda-card reveal" data-pg-card>
        <p class="pogoda-card__status"><i class="pogoda-card__dot" aria-hidden="true"></i><span data-pg-status>{esc(STATUS)}</span></p>
        <div class="pogoda-card__faces">
          <div class="pogoda-card__face pogoda-card__face--rule" data-pg-rule>
            <p class="pogoda-card__big" aria-hidden="true"><b>{esc(_plain(BAND_LOW))}</b><span>…</span><b>{esc(_plain(THRESHOLD))}</b><small>°C</small></p>
            <p class="pogoda-card__cap"><span class="sr-only">{esc(BAND)} — </span>{esc(BIG_CAPTION)}</p>
          </div>
          <div class="pogoda-card__face pogoda-card__face--live" data-pg-face hidden>
            <p class="pogoda-card__verdict" tabindex="-1" data-pg-verdict><span class="pogoda-card__title" data-pg-title></span> <span class="pogoda-card__kick" data-pg-kick></span></p>
            <p class="pogoda-card__chip" data-pg-chip hidden>{icon('calendar')}<span data-pg-chip-text></span></p>
            <p class="pogoda-card__why" data-pg-why></p>
            <p class="pogoda-card__note" data-pg-note hidden></p>
          </div>
        </div>
        <p class="pogoda-card__rule">{icon('info')}<span>{esc(_fill(RULE))}</span></p>
        <div class="pogoda-card__cta">
          <button class="btn btn--primary pogoda-card__book" type="button" data-modal="call" data-preset="{preset}" data-pg-book>{icon('phone')} <span>{esc(BOOK)}</span></button>
          <noscript><a class="btn btn--primary pogoda-card__book" href="tel:{D.PHONE_TEL}">{icon('phone')} <span>{esc(BOOK_PHONE.format(phone=D.PHONE))}</span></a></noscript>
          <div class="pogoda-card__links">{links}</div>
        </div>
      </div>"""


def _chart() -> str:
    """The chart: guide lines, the empty day list (pogoda.js fills it), the source. Hidden without JavaScript."""
    source = f'<a href="{SOURCE[1]}" target="_blank" rel="noopener">{esc(SOURCE[0])}</a>'
    licence = f'<a href="{LICENCE[1]}" target="_blank" rel="noopener">{esc(LICENCE[0])}</a>'
    line = esc(SOURCE_LINE).replace("{source}", source).replace("{licence}", licence)
    legend = (f'<span class="pogoda-key pogoda-key--range"><i></i>{esc(LEGEND["range"])}</span>'
              f'<span class="pogoda-key pogoda-key--mean"><i></i>{esc(LEGEND["mean"])}</span>'
              f'<span class="pogoda-key pogoda-key--snow">{SNOW_SVG}{esc(LEGEND["snow"])}</span>')
    guides = f"--p0:{_pos(FROST)};--pb:{_pos(BAND_LOW)};--pt:{_pos(THRESHOLD)}"
    return f"""<figure class="pogoda-chart reveal" style="--d:80ms" data-pg-chart>
        <figcaption class="pogoda-chart__head">
          <span class="pogoda-chart__title">{esc(CHART_TITLE)}</span>
          <span class="pogoda-chart__legend" aria-hidden="true">{legend}</span>
        </figcaption>
        <div class="pogoda-plot" style="{guides}" data-pg-plot>
          <div class="pogoda-plot__guides" aria-hidden="true">
            <i class="pogoda-plot__band"></i>
            <i class="pogoda-plot__line pogoda-plot__line--thr"><b>{esc(temp(THRESHOLD, unit=False))}</b></i>
            <i class="pogoda-plot__line pogoda-plot__line--zero"><b>{esc(temp(FROST, unit=False))}</b></i>
          </div>
          <ol class="pogoda-days" aria-label="{esc(LIST_LABEL)}" data-pg-days hidden></ol>
          <div class="pogoda-plot__msg" data-pg-msg>
            <p class="pogoda-plot__text" tabindex="-1" data-pg-msg-text>{esc(TEXTS["msg-loading"])}</p>
            <button class="btn btn--ghost btn--sm pogoda-plot__retry" type="button" data-pg-retry hidden>{esc(TEXTS["retry"])}</button>
          </div>
        </div>
        <p class="pogoda-chart__src">{line}<span data-pg-updated></span></p>
      </figure>"""


def pogoda_section() -> str:
    """The section of the home page (build/home.py puts it right before zima_section())."""
    return f"""<section class="section section--black pogoda-sec" id="pogoda" aria-labelledby="pogoda-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">{esc(EYEBROW)}</p><h2 class="h2 sec-head__title" id="pogoda-title">{esc(TITLE)}</h2></div>
      <p class="sec-head__aside">{esc(ASIDE)}</p>
    </div>
    <div class="pogoda" data-pogoda data-state="static" data-tone="neutral">
      {_card()}
      {_chart()}
      <p class="sr-only" role="status" aria-live="polite" aria-atomic="true" data-pg-live></p>
    </div>
  </div>
  <script type="application/json" id="pogoda-data">{data_json()}</script>
</section>"""
