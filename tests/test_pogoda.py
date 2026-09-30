# -*- coding: utf-8 -*-
"""«Пора переобуваться?» (build/pogoda.py, src/assets/js/pogoda.js): the markup and its links, the config the script
reads, and the script's own verdict on test forecasts — autumn, spring, summer, winter, the edges of the rule and broken
answers of the API.  Run: python3 -m unittest discover -s tests"""
import html
import json
import re
import shutil
import subprocess
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import pogoda as P  # noqa: E402

NODE = shutil.which("node")
SCRIPT = ROOT / "tests" / "pogoda_verdict.cjs"
FIXTURE = ROOT / "tests" / "fixtures" / "pogoda-2026-09-30.json"
NB = "\u00a0"


def api(today: str, days: list, past: list | None = None) -> dict:
    """An Open-Meteo answer: past days, then today and the forecast. A day is (min, max, mean) or
    (min, max, mean, snow cm). The past defaults to PAST_DAYS mild days."""
    past = [(6, 14, 10)] * P.PAST_DAYS if past is None else past
    rows = past + days
    start = date.fromisoformat(today) - timedelta(days=len(past))
    col = {k: [] for k in P.VARIABLES}
    for r in rows:
        col["min"].append(r[0])
        col["max"].append(r[1])
        col["mean"].append(r[2])
        col["snow"].append(r[3] if len(r) > 3 else 0.0)
        col["precip"].append(r[3] * 0.7 if len(r) > 3 else 0.0)
    return {
        "latitude": 56.3125, "longitude": 44.0, "timezone": P.TZ,
        "daily_units": {"time": "iso8601", **{name: unit for name, unit in P.VARIABLES.values()}},
        "daily": {"time": [(start + timedelta(days=i)).isoformat() for i in range(len(rows))],
                  **{P.VARIABLES[k][0]: v for k, v in col.items()}},
    }


def run(cases=(), **extra) -> dict:
    """Everything through the real script in node, with the real config of the page."""
    payload = {"config": P.config(), "cases": list(cases), **extra}
    out = subprocess.run([NODE, str(SCRIPT)], input=json.dumps(payload, ensure_ascii=False), capture_output=True,
                         text=True, check=True, env={"TZ": "America/Los_Angeles", "PATH": ""})   # the machine's zone must not matter
    return json.loads(out.stdout)


def plain(s: str) -> str:
    return s.replace(NB, " ")


WARM = (6, 14, 10)      # a mild autumn day: mean above +7, no frost
COLD = (1, 6, 4)        # mean +4, no frost
FROSTY = (-2, 5, 2)     # a night frost


class MarkupTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = P.pogoda_section()
        visible = re.sub(r"<script\b.*?</script>", " ", cls.html, flags=re.S)   # the JSON for the script is not text
        cls.text = html.unescape(re.sub(r"<[^>]+>", " ", visible))

    def test_section_and_its_place_before_zima(self):
        self.assertTrue(self.html.startswith('<section class="section section--black pogoda-sec" id="pogoda" aria-labelledby="pogoda-title">'))
        self.assertIn(f'<h2 class="h2 sec-head__title" id="pogoda-title">{P.TITLE}</h2>', self.html)
        from build.home import render_home
        page = render_home()
        ids = re.findall(r'<section[^>]* id="([^"]+)"', page)
        self.assertEqual(ids[ids.index("pogoda") - 1: ids.index("pogoda") + 2], ["stuk", "pogoda", "zima"])

    def test_without_javascript_the_rule_and_the_booking_are_there(self):
        self.assertIn(html.unescape(P._fill(P.RULE)), self.text)
        self.assertIn(P.BIG_CAPTION, self.text)
        self.assertIn(f'href="tel:{D.PHONE_TEL}"', self.html)               # <noscript>: the phone instead of the modal
        self.assertIn("<noscript>", self.html)
        book = re.search(r'<button class="btn btn--primary pogoda-card__book"[^>]*>', self.html).group(0)
        self.assertIn('data-modal="call"', book)
        preset = json.loads(html.unescape(re.search(r'data-preset="([^"]+)"', book).group(1)))
        self.assertEqual(preset, {"message": P.MESSAGES["any"]})

    def test_links_are_existing_service_pages_and_never_sensitive(self):
        hrefs = re.findall(r'<a [^>]*href="(/[^"]*)"', self.html)
        self.assertEqual(hrefs, [P.BOOK_PAGE, P.STORAGE_PAGE])
        for href in hrefs:
            self.assertIn(href, D.BY_PATH)
            self.assertFalse(any(bad in href for bad in P.FORBIDDEN), href)

    def test_a_missing_or_sensitive_page_fails_the_build(self):
        with self.assertRaises(ValueError):
            P._page("/services/cip-tuning.html")
        with self.assertRaises(ValueError):
            P._page("/services/diagnostika/udalenie-katalizatora.html")
        with self.assertRaises(ValueError):
            P._page("/services/net-takoj-stranicy.html")
        with mock.patch.object(P, "STORAGE_PAGE", "/services/tehosmotr.html"), self.assertRaises(ValueError):
            P.pogoda_section()

    def test_attribution_and_the_hedge(self):
        self.assertIn(f'<a href="{P.SOURCE[1]}" target="_blank" rel="noopener">Open-Meteo.com</a>', self.html)
        self.assertIn(f'<a href="{P.LICENCE[1]}" target="_blank" rel="noopener">CC BY 4.0</a>', self.html)
        self.assertIn("прогноз может меняться", self.text)

    def test_no_prices_no_laws(self):
        # every phrase of the section, on the page and in the script (the month names for dates are not phrases)
        phrases = " ".join([self.text, *P.config()["texts"].values(), *P.MESSAGES.values()]).lower()
        for bad in ("₽", "руб", "цен", "закон", "штраф", "пдд", "запрещ", "обязател", "декабр", "феврал", "гарант"):
            self.assertNotIn(bad, phrases)

    def test_the_page_json_is_the_config(self):
        blob = re.search(r'<script type="application/json" id="pogoda-data">(.*?)</script>', self.html, re.S).group(1)
        self.assertEqual(json.loads(blob), json.loads(json.dumps(P.config())))

    def test_chart_starts_hidden_with_guides_at_the_default_scale(self):
        self.assertIn('data-pg-days hidden', self.html)
        self.assertIn("--p0:0.2500;--pb:0.5000;--pt:0.6000", self.html)   # 0, +5, +7 °C on −5…+15


class ConfigTest(unittest.TestCase):
    def test_request(self):
        url = urlparse(P.api_url())
        self.assertEqual(f"{url.scheme}://{url.netloc}{url.path}", P.API)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        self.assertEqual((float(q["latitude"]), float(q["longitude"])), D.COORDS)
        self.assertEqual(q["daily"].split(","), ["temperature_2m_min", "temperature_2m_max", "temperature_2m_mean", "precipitation_sum", "snowfall_sum"])
        self.assertEqual((q["timezone"], q["forecast_days"], q["past_days"]), ("Europe/Moscow", "10", "3"))

    def test_rule_numbers_go_into_the_texts(self):
        cfg = P.config()
        self.assertEqual(P.THR, f"+7{NB}°C")
        self.assertEqual(P.BAND, f"+5…+7{NB}°C")
        for key, text in cfg["texts"].items():
            self.assertNotIn("{thr}", text, key)
            self.assertNotIn("{band}", text, key)
        self.assertEqual(sorted(int(m) for m in cfg["seasons"]), list(range(1, 13)))

    def test_a_broken_rule_stops_the_build(self):
        for name, value in (("STREAK", 1), ("THRESHOLD", -1), ("SEASONS", {"autumn": (9, 10, 11)}), ("FORECAST_DAYS", 20)):
            with self.subTest(name=name), mock.patch.object(P, name, value), self.assertRaises(ValueError):
                P.config()

    def test_seasons(self):
        self.assertEqual([P.season_of(m) for m in (1, 3, 5, 6, 8, 9, 11, 12)],
                         ["winter", "spring", "spring", "summer", "summer", "autumn", "autumn", "winter"])


@unittest.skipUnless(NODE, "node is not installed")
class VerdictTest(unittest.TestCase):
    def one(self, api_answer, today=None):
        case = {"name": "x", "api": api_answer}
        if today is not None:
            case["today"] = today
        row = run([case])["cases"][0]
        self.assertTrue(row["ok"], row.get("error"))
        for key in ("title", "kick", "chip", "why", "note", "live", "message"):
            self.assertNotIn("undefined", row[key], key)
            self.assertNotIn("{", row[key], key)
        return row

    # ---------- autumn ----------
    def test_real_answer_of_2026_09_30(self):
        r = self.one(json.loads(FIXTURE.read_text(encoding="utf-8")))
        self.assertEqual((r["today"], r["season"], r["state"], r["cause"]), ("2026-09-30", "autumn", "soon", "cold"))
        self.assertEqual((r["from"], r["frost"], r["run"], r["rebound"]), ("2026-10-02", "2026-10-03", ["2026-10-02", "2026-10-05"], "2026-10-06"))
        self.assertEqual((r["title"], plain(r["kick"]), plain(r["chip"])), ("Скоро пора", "на зимнюю — с 2 октября, пт", "через 2 дня"))
        self.assertEqual(plain(r["why"]), "С 2 октября среднесуточная температура по прогнозу не выше +7 °C — 4 дня подряд. "
                                          "Заморозки по прогнозу — 3 октября, ночью до 0 °C.")
        self.assertEqual(plain(r["note"]), "С 6 октября, по прогнозу, снова теплеет — до +15 °C днём.")
        self.assertEqual((r["tone"], r["message"]), ("winter", P.MESSAGES["autumn"]))
        self.assertEqual(r["scale"], {"lo": -2, "hi": 18})

    def test_cold_from_today_to_the_end(self):
        r = self.one(api("2026-10-15", [COLD] * 10))
        self.assertEqual((r["state"], r["cause"], r["from"], r["frost"]), ("now", "cold", "2026-10-15", None))
        self.assertEqual((r["title"], r["kick"], r["chip"]), ("Пора на зимнюю", "уже сейчас", ""))
        self.assertEqual(plain(r["why"]), "С сегодняшнего дня среднесуточная температура по прогнозу не выше +7 °C — до конца прогноза.")
        self.assertEqual((r["note"], r["rebound"]), ("", None))

    def test_a_cold_spell_that_began_before_today_counts(self):
        r = self.one(api("2026-10-15", [COLD] + [WARM] * 9, past=[COLD] * 3))
        self.assertEqual((r["state"], r["from"], r["run"]), ("now", "2026-10-15", ["2026-10-12", "2026-10-15"]))
        self.assertEqual(plain(r["why"]), "Среднесуточная температура уже 4 дня подряд не выше +7 °C.")
        self.assertEqual((r["rebound"], plain(r["note"])), ("2026-10-16", "С 16 октября, по прогнозу, снова теплеет — до +14 °C днём."))

    def test_a_spell_that_ended_before_today_does_not(self):
        r = self.one(api("2026-10-15", [WARM] * 10, past=[COLD] * 3))
        self.assertEqual((r["state"], r["cause"], r["run"]), ("early", "warm", None))

    def test_frost_tomorrow_is_now(self):
        r = self.one(api("2026-10-15", [WARM, (-1, 12, 8)] + [WARM] * 8))
        self.assertEqual((r["state"], r["cause"], r["from"], r["kick"]), ("now", "frost", "2026-10-16", "с завтрашнего дня"))
        self.assertEqual(plain(r["why"]), "Завтра по прогнозу заморозки: ночью до −1 °C.")

    def test_frost_later_is_soon_with_the_date(self):
        r = self.one(api("2026-10-15", [WARM] * 5 + [(-2, 11, 8)] + [WARM] * 4))
        self.assertEqual((r["state"], r["cause"], r["from"]), ("soon", "frost", "2026-10-20"))
        self.assertEqual((plain(r["kick"]), plain(r["chip"])), ("на зимнюю — с 20 октября, вт", "через 5 дней"))
        self.assertEqual(plain(r["why"]), "20 октября по прогнозу заморозки: ночью до −2 °C.")
        self.assertIn("через 5 дней", plain(r["live"]))

    def test_frost_first_then_a_cold_spell(self):
        r = self.one(api("2026-10-15", [WARM] * 3 + [(-1, 12, 8)] + [WARM] + [COLD] * 3 + [WARM] * 2))
        self.assertEqual((r["state"], r["cause"], r["from"], r["run"]), ("soon", "frost", "2026-10-18", ["2026-10-20", "2026-10-22"]))
        self.assertEqual(plain(r["why"]), "18 октября по прогнозу заморозки: ночью до −1 °C. "
                                          "С 20 октября среднесуточная температура по прогнозу не выше +7 °C — 3 дня подряд.")

    def test_warm_autumn_is_early(self):
        r = self.one(api("2026-09-10", [WARM] * 10))
        self.assertEqual((r["state"], r["cause"], r["title"], r["kick"]), ("early", "warm", "Пока рано", "переобуваться на зимнюю"))
        self.assertEqual(plain(r["why"]), "В ближайшие 10 дней среднесуточная температура выше +7 °C, заморозков в прогнозе нет.")
        self.assertEqual((r["tone"], r["message"]), ("summer", P.MESSAGES["autumn"]))

    def test_short_cold_spells_are_early(self):
        r = self.one(api("2026-10-15", [COLD, COLD, WARM, COLD, WARM, COLD, COLD, WARM, WARM, WARM]))
        self.assertEqual((r["state"], r["cause"]), ("early", "short"))
        self.assertEqual(plain(r["why"]), "Среднесуточная температура опускается до +7 °C и ниже лишь ненадолго, заморозков в прогнозе нет.")

    def test_a_spell_cut_by_the_end_of_the_forecast(self):
        self.assertEqual(self.one(api("2026-10-15", [WARM] * 8 + [COLD] * 2))["state"], "early")      # two days: unknown
        r = self.one(api("2026-10-15", [WARM] * 7 + [COLD] * 3))
        self.assertEqual((r["state"], r["from"]), ("soon", "2026-10-22"))
        self.assertTrue(plain(r["why"]).endswith("— до конца прогноза."))

    def test_edges_of_the_numbers(self):
        # the mean exactly at the threshold is cold; a hair above it is not
        self.assertEqual(self.one(api("2026-10-15", [(3, 11, 7.0)] * 3 + [WARM] * 7))["state"], "now")
        self.assertEqual(self.one(api("2026-10-15", [(3, 11, 7.05)] * 3 + [WARM] * 7))["state"], "early")
        # a minimum exactly at 0 °C is a frost; +0.05 is not
        self.assertEqual(self.one(api("2026-10-15", [(0.0, 11, 8)] + [WARM] * 9))["cause"], "frost")
        self.assertEqual(self.one(api("2026-10-15", [(0.05, 11, 8)] + [WARM] * 9))["state"], "early")
        # two days after tomorrow is no longer «now»
        self.assertEqual(self.one(api("2026-10-15", [WARM, WARM, FROSTY] + [WARM] * 7))["state"], "soon")

    def test_snow_and_frost_are_named_for_the_chart(self):
        r = self.one(api("2026-11-10", [(-6, -1, -3, 2.5)] * 10))
        self.assertEqual((r["state"], r["cause"], r["from"], r["frost"]), ("now", "cold", "2026-11-10", "2026-11-10"))
        self.assertEqual(plain(r["why"]), "С сегодняшнего дня среднесуточная температура по прогнозу не выше +7 °C — до конца прогноза. "
                                          "Заморозки по прогнозу — сегодня, ночью до −6 °C.")

    # ---------- spring ----------
    def test_spring_warm_is_now(self):
        r = self.one(api("2026-04-20", [WARM] * 10, past=[COLD] * 3))
        self.assertEqual((r["season"], r["state"], r["from"], r["title"], r["kick"]), ("spring", "now", "2026-04-20", "Пора на летнюю", "уже сейчас"))
        self.assertEqual((r["tone"], r["message"]), ("summer", P.MESSAGES["spring"]))

    def test_spring_frost_today_then_warm_is_now_from_tomorrow(self):
        r = self.one(api("2026-04-20", [FROSTY] + [WARM] * 9))
        self.assertEqual((r["state"], r["from"], r["kick"]), ("now", "2026-04-21", "с завтрашнего дня"))
        self.assertEqual(plain(r["why"]), "С завтрашнего дня среднесуточная температура по прогнозу выше +7 °C, заморозков нет.")

    def test_spring_soon_after_the_last_frost(self):
        r = self.one(api("2026-04-20", [WARM, WARM, FROSTY] + [WARM] * 7))
        self.assertEqual((r["state"], r["from"], plain(r["chip"])), ("soon", "2026-04-23", "через 3 дня"))
        self.assertEqual(plain(r["kick"]), "на летнюю — с 23 апреля, чт")
        self.assertEqual(plain(r["why"]), "С 23 апреля среднесуточная температура по прогнозу выше +7 °C, заморозков нет.")

    def test_spring_frost_near_the_end_is_early(self):
        r = self.one(api("2026-04-20", [WARM] * 8 + [(-1, 9, 5), WARM]))
        self.assertEqual((r["state"], r["cause"], r["title"], r["kick"]), ("early", "frost", "Пока рано", "снимать зимнюю резину"))
        self.assertEqual(plain(r["why"]), "По прогнозу ещё будут заморозки: ночью до −1 °C.")
        self.assertEqual(r["tone"], "winter")

    def test_spring_cold_without_frost_is_early(self):
        r = self.one(api("2026-03-25", [COLD] * 10))
        self.assertEqual((r["state"], r["cause"]), ("early", "cold"))
        self.assertEqual(plain(r["why"]), "Среднесуточная температура по прогнозу ещё опускается до +4 °C.")

    # ---------- summer, winter, the edges of the seasons ----------
    def test_summer_and_winter_are_calm(self):
        r = self.one(api("2026-07-15", [(15, 28, 21)] * 10))
        self.assertEqual((r["state"], r["title"], r["kick"], r["chip"], r["tone"], r["message"]),
                         ("summer", "Сезон летней резины", "", "", "summer", P.MESSAGES["any"]))
        self.assertIn("осенью", r["why"])
        r = self.one(api("2027-01-20", [(-15, -8, -11, 1.0)] * 10))
        self.assertEqual((r["state"], r["title"], r["tone"], r["message"]), ("winter", "Сезон зимней резины", "winter", P.MESSAGES["any"]))
        self.assertIn("весной", r["why"])

    def test_the_month_of_today_decides(self):
        rows = run([{"name": d, "api": api(d, [WARM] * 10)} for d in
                    ("2026-08-31", "2026-09-01", "2026-11-30", "2026-12-01", "2027-02-28", "2027-03-01", "2027-05-31", "2027-06-01")])["cases"]
        self.assertEqual([r["season"] for r in rows], ["summer", "autumn", "autumn", "winter", "winter", "spring", "spring", "summer"])

    # ---------- broken answers: never drawn ----------
    def test_broken_answers(self):
        good = api("2026-10-15", [WARM] * 10)

        def broken(**change):
            a = json.loads(json.dumps(good))
            for path, value in change.items():
                node = a
                *keys, last = path.split("__")
                for k in keys:
                    node = node[k]
                if value is ...:
                    del node[last]
                else:
                    node[last] = value
            return a

        t_min, t_mean = P.VARIABLES["min"][0], P.VARIABLES["mean"][0]
        seq = good["daily"][t_min]
        cases = {
            "a list": [good],
            "null": None,
            "a string": "<html>",
            "an API error": {"error": True, "reason": "Parameter 'daily' is invalid"},
            "another time zone": broken(timezone="UTC"),
            "another place": broken(latitude=10.0),
            "no daily": broken(daily=...),
            "no units": broken(daily_units=...),
            "Fahrenheit": broken(daily_units__temperature_2m_max="°F"),
            "a short column": broken(**{f"daily__{t_mean}": good["daily"][t_mean][:-1]}),
            "a missing column": broken(daily__snowfall_sum=...),
            "a gap in the dates": broken(daily__time=good["daily"]["time"][:5] + ["2026-10-30"] + good["daily"]["time"][6:]),
            "no such date": broken(daily__time=["2026-02-27", "2026-02-28", "2026-02-29"] + good["daily"]["time"][3:]),
            "a date as a number": broken(daily__time=[20261012] + good["daily"]["time"][1:]),
            "a temperature as text": broken(**{f"daily__{t_min}": ["5"] + seq[1:]}),
            "99 degrees": broken(**{f"daily__{t_min}": seq[:4] + [99] + seq[5:]}),
            "min above max": broken(**{f"daily__{t_min}": seq[:4] + [20] + seq[5:]}),
            "mean outside": broken(**{f"daily__{t_mean}": good["daily"][t_mean][:4] + [30] + good["daily"][t_mean][5:]}),
            "a hole inside": broken(**{f"daily__{t_min}": seq[:6] + [None] + seq[7:]}),
            "negative rain": broken(daily__precipitation_sum=[-1] + good["daily"]["precipitation_sum"][1:]),
            "too few days": api("2026-10-15", [WARM] * 5),
            "too many days": api("2026-10-15", [WARM] * 11),
            "all empty at the end": broken(**{f"daily__{t_min}": seq[:6] + [None] * 7}),
        }
        rows = run([{"name": k, "api": v} for k, v in cases.items()])["cases"]
        for row in rows:
            with self.subTest(case=row["name"]):
                self.assertFalse(row["ok"], row)
                self.assertTrue(row["error"])

    def test_empty_days_at_the_end_are_cut_off(self):
        a = api("2026-10-15", [WARM] * 10)
        for name, _ in P.VARIABLES.values():
            a["daily"][name][-2:] = [None, None]
        r = self.one(a)
        self.assertEqual(r["days"], P.PAST_DAYS + 8)
        a = api("2026-10-15", [WARM] * 10)
        a["daily"]["snowfall_sum"][5] = None                    # no snowfall known: fine
        self.assertTrue(self.one(a)["ok"])


@unittest.skipUnless(NODE, "node is not installed")
class WordsTest(unittest.TestCase):
    def test_temperatures(self):
        out = run(temps=[-0.4, -0.5, -0.6, 0.49, 7, 6.5, -12.5, 12.5, -30])["temps"]
        self.assertEqual([plain(x) for x in out], ["0 °C", "0 °C", "−1 °C", "0 °C", "+7 °C", "+7 °C", "−12 °C", "+13 °C", "−30 °C"])

    def test_plural_days(self):
        self.assertEqual(run(plurals=[1, 2, 4, 5, 10, 11, 14, 21, 22, 25, 101, 111])["plurals"],
                         ["1 день", "2 дня", "4 дня", "5 дней", "10 дней", "11 дней", "14 дней", "21 день", "22 дня", "25 дней", "101 день", "111 дней"])

    def test_moscow_clock_with_and_without_intl(self):
        rows = run(moments=["2026-09-30T20:59:00Z", "2026-09-30T21:00:00Z", "2026-12-31T21:05:00Z", "2026-10-05T08:07:00+03:00"])["moments"]
        want = [("2026-09-30", "23:59"), ("2026-10-01", "0:00"), ("2027-01-01", "0:05"), ("2026-10-05", "8:07")]
        for row, (d, t) in zip(rows, want):
            with self.subTest(moment=row["iso"]):
                self.assertEqual((row["intl"]["date"], row["intl"]["time"]), (d, t))
                self.assertEqual(row["intl"], row["fallback"])


if __name__ == "__main__":
    unittest.main()
