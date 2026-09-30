# -*- coding: utf-8 -*-
"""«Когда удобно приехать?» (build/vremya.py, src/assets/js/vremya.js): the days of the window at fixed moments of the
Moscow clock, the line in the message (put in, replaced, taken out), the markup in the request form and the call-back
modal.  Run: python3 -m unittest discover -s tests"""
import html
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import layout as L  # noqa: E402
from build import otkryto as O  # noqa: E402
from build import vremya as V  # noqa: E402

NODE = shutil.which("node")
SCRIPT = ROOT / "tests" / "vremya_cases.cjs"
FRI_1830 = "2026-10-02T18:30:00+03:00"   # Friday, the last half hour of the day
SAT_EVENING = "Удобно приехать: сб, 3 октября, вечером (15–17)"
MON_MORNING = "Удобно приехать: пн, 5 октября, утром (9–12)"


def run(*cases, conf=None):
    """The results of tests/vremya_cases.cjs; the machine's time zone must not matter, so node runs in Los Angeles."""
    job = {"conf": conf or V.config(V.TEXTS["where_form"]), "cases": list(cases)}
    out = subprocess.run([NODE, str(SCRIPT), json.dumps(job, ensure_ascii=False)], capture_output=True, text=True,
                         check=True, env={"TZ": "America/Los_Angeles", "PATH": ""}).stdout
    return json.loads(out)


def days(at, conf=None):
    return run({"op": "days", "at": at}, conf=conf)[0]


def parts(day):
    """[«morning 9–12», …] of one day of the window"""
    return [f"{key} {hours}" for key, hours, _ in day["parts"]]


def with_line(text, line):
    return run({"op": "with", "text": text, "line": line})[0]


def config_of(markup):
    return json.loads(html.unescape(re.search(r'data-vremya="([^"]+)"', markup).group(1)))


def picker_of(markup):
    """the picker's own markup: from its root to the end of the live region, its last element"""
    start = markup.index('<div class="vr')
    return markup[start:markup.index("data-vr-live></p></div>", start) + len("data-vr-live></p></div>")]


class MarkupTest(unittest.TestCase):
    def test_request_form_step_2_under_the_text(self):
        form = L.request_section()
        step2 = form[form.index('data-panel="2"'):form.index('data-panel="3"')]
        self.assertIn('data-vr-for="request_what"', step2)
        self.assertLess(step2.index('id="request_what"'), step2.index('id="vr-rq"'), "under «Или опишите задачу»")
        self.assertLess(step2.index('id="vr-rq"'), step2.index('class="rq__actions"'), "above «Назад» / «Вперёд»")
        self.assertIn('<p class="vr__title" id="vr-rq-title">', step2, "the days are open in the form")

    def test_modal_under_the_comment(self):
        modal = L.call_modal()
        self.assertIn('data-vr-for="call-msg"', modal)
        self.assertLess(modal.index('id="call-msg"'), modal.index('id="vr-call"'))
        self.assertLess(modal.index('id="vr-call"'), modal.index('name="agree"'), "above the consent")
        self.assertIn('class="vr vr--fold span-2"', modal, "a whole row of the modal's grid, folded")
        self.assertIn('aria-expanded="false" aria-controls="vr-call-body" data-vr-toggle', modal)
        self.assertIn('id="vr-call-body" hidden data-vr-body', modal)

    def test_hidden_until_the_script_fills_it(self):
        for markup in (V.in_form(), V.in_modal()):
            self.assertRegex(markup, r'^<div class="vr[^"]*" id="vr-\w+" [^>]* hidden>')
            self.assertIn('data-vr-days></div>', markup, "the days are built by vremya.js")

    def test_the_note_describes_the_group(self):
        for key, markup in (("rq", V.in_form()), ("call", V.in_modal())):
            self.assertIn(f'role="group" aria-labelledby="vr-{key}-title" aria-describedby="vr-{key}-note"', markup)
            self.assertIn(f'<p class="vr__note" id="vr-{key}-note">{D.esc(V.TEXTS["note"])}</p>', markup)
            self.assertIn('aria-live="polite" data-vr-live', markup, "the chosen line is announced")

    def test_no_new_fields_for_the_backend(self):
        for markup in (picker_of(L.request_section()), picker_of(L.call_modal())):
            self.assertNotRegex(markup, r"<(input|select|textarea)\b")
            self.assertNotIn(" name=", markup)
            self.assertEqual(len(re.findall(r"<button\b", markup)), len(re.findall(r'<button [^>]*type="button"', markup)))

    def test_ids_are_unique_on_a_page(self):
        page = L.request_section() + L.call_modal()
        ids = re.findall(r'\sid="([^"]+)"', page)
        self.assertEqual(len(ids), len(set(ids)), [i for i in ids if ids.count(i) > 1])
        for target in re.findall(r'data-vr-for="([^"]+)"', page):
            self.assertIn(f'id="{target}"', page)

    def test_config_is_the_week_of_the_hours(self):
        conf = config_of(V.in_form())
        self.assertEqual(conf["week"], O.week(D.HOURS))
        self.assertIsNone(conf["week"][6], "Sunday is not in D.HOURS: closed")
        self.assertEqual((conf["days"], conf["lead"]), (14, 60))
        self.assertEqual([(p["key"], p["from"], p["to"]) for p in conf["parts"]],
                         [("morning", 0, 720), ("day", 720, 900), ("evening", 900, 1440)])
        self.assertEqual(conf["t"]["where"], "В заявке:")
        self.assertEqual(config_of(V.in_modal())["t"]["where"], "В сообщении:")

    def test_only_the_existing_promise(self):
        promise = "менеджер свяжется с вами в рабочие часы"
        self.assertIn(promise, V.TEXTS["note"])
        form = L.request_section()
        self.assertIn(promise, form[:form.index('id="vr-rq"')], "the site already says it, in the lead of the form")
        for text in V.TEXTS.values():
            self.assertNotRegex(text.lower(), r"₽|руб|свобод|гарант|запис(ан|ь вас)|подтверд|уточнит", text)

    def test_bad_constants_fail_the_build(self):
        with mock.patch.object(V, "PARTS", V.PARTS + (("night", "ночью", "Ночью", 1300, 1200),)):
            with self.assertRaises(ValueError):
                V.config("x")
        with mock.patch.object(V, "PARTS", V.PARTS + (("any", "когда-нибудь", "Когда-нибудь", 0, 60),)):
            with self.assertRaises(ValueError):
                V.config("x")

    def test_registered_in_the_build(self):
        build = (ROOT / "build.py").read_text(encoding="utf-8")
        self.assertRegex(build, r'CSS_ORDER = \[[^\]]*"vremya\.css"')
        self.assertRegex(build, r'JS_ORDER = \[[^\]]*"vremya\.js"')
        form_js = (ROOT / "src" / "assets" / "js" / "form.js").read_text(encoding="utf-8")
        self.assertIn("G.vremya.ownText(comment)", form_js, "step 2: the line alone does not describe the task")


@unittest.skipUnless(NODE, "node is not installed")
class DaysTest(unittest.TestCase):
    def test_friday_half_past_six(self):
        w = days(FRI_1830)
        self.assertEqual([d["date"] for d in (w[0], w[-1])], ["2026-10-02", "2026-10-15"])
        self.assertEqual(len(w), 14)
        today, sat, sun, mon = w[:4]
        self.assertEqual((today["state"], today["tag"], today["parts"]), ("late", "сегодня", []),
                         "19:00 is in half an hour: nothing of today is offered")
        self.assertEqual(today["sr"], "пятница, 2 октября, сегодня, уже поздно")
        self.assertEqual((sat["state"], sat["tag"], sat["sr"]), ("open", "завтра", "суббота, 3 октября, завтра"))
        self.assertEqual(parts(sat), ["morning 9–12", "day 12–15", "evening 15–17"], "Saturday closes at 17")
        self.assertEqual((sun["state"], sun["tag"], sun["sr"]), ("closed", "выходной", "воскресенье, 4 октября, выходной"))
        self.assertEqual(parts(mon), ["morning 9–12", "day 12–15", "evening 15–19"])
        self.assertEqual((mon["wd"], mon["num"], mon["tag"]), ("пн", "05", "окт"))
        self.assertEqual(mon["parts"][0][2], "утром, с 9 до 12", "screen readers hear words, not a dash")
        self.assertEqual([d["date"] for d in w if d["state"] == "closed"], ["2026-10-04", "2026-10-11"])

    def test_sunday(self):
        w = days("2026-10-04T12:00:00+03:00")
        self.assertEqual((w[0]["state"], w[0]["sr"]), ("closed", "воскресенье, 4 октября, сегодня, выходной"))
        self.assertEqual((w[1]["tag"], parts(w[1])), ("завтра", ["morning 9–12", "day 12–15", "evening 15–19"]))
        self.assertEqual((w[-1]["date"], parts(w[-1])[-1]), ("2026-10-17", "evening 15–17"))

    def test_today_parts_end_an_hour_before_their_end(self):
        moments = ["08:00", "11:00", "11:01", "14:00", "14:01", "18:00", "18:01", "23:59"]   # Monday, 5 October
        got = run(*[{"op": "days", "at": f"2026-10-05T{m}:00+03:00"} for m in moments])
        every = ["morning 9–12", "day 12–15", "evening 15–19"]
        self.assertEqual([(m, parts(w[0]), w[0]["state"]) for m, w in zip(moments, got)], [
            ("08:00", every, "open"),
            ("11:00", every, "open"),          # an hour of the morning is left
            ("11:01", every[1:], "open"),
            ("14:00", every[1:], "open"),
            ("14:01", every[2:], "open"),
            ("18:00", every[2:], "open"),
            ("18:01", [], "late"),
            ("23:59", [], "late"),
        ])

    def test_saturday_closes_at_five(self):
        self.assertEqual(parts(days("2026-10-03T16:00:00+03:00")[0]), ["evening 15–17"])
        self.assertEqual(days("2026-10-03T16:01:00+03:00")[0]["state"], "late")

    def test_moscow_time_not_the_machine_clock(self):
        # node runs in Los Angeles: the day turns at midnight in Moscow, 21:00 UTC
        before = days("2026-10-04T20:59:00Z")[0]
        after = days("2026-10-04T21:00:00Z")[0]
        self.assertEqual((before["date"], before["state"]), ("2026-10-04", "closed"))
        self.assertEqual((after["date"], after["tag"], len(after["parts"])), ("2026-10-05", "сегодня", 3))

    def test_month_and_year_boundaries(self):
        oct_nov = days("2026-10-25T10:00:00+03:00")   # a Sunday
        self.assertEqual(oct_nov[-1]["date"], "2026-11-07")
        self.assertEqual([d["tag"] for d in oct_nov[2:9]], ["окт", "окт", "окт", "окт", "окт", "выходной", "ноя"])
        self.assertEqual((oct_nov[7]["date"], oct_nov[7]["sr"]), ("2026-11-01", "воскресенье, 1 ноября, выходной"))
        self.assertEqual((oct_nov[8]["date"], oct_nov[8]["sr"]), ("2026-11-02", "понедельник, 2 ноября"))
        new_year = days("2026-12-25T10:00:00+03:00")
        self.assertEqual([new_year[0]["date"], new_year[-1]["date"]], ["2026-12-25", "2027-01-07"])
        self.assertEqual(next(d for d in new_year if d["date"] == "2027-01-01")["sr"], "пятница, 1 января")
        leap = [d["date"] for d in days("2028-02-20T10:00:00+03:00")]
        self.assertIn("2028-02-29", leap)
        self.assertEqual(leap[-1], "2028-03-04")

    def test_a_day_with_a_note_offers_any_time(self):
        conf = V.config("x")
        conf["week"][6] = {"note": "по предварительной записи"}
        sun = days("2026-10-03T12:00:00+03:00", conf=conf)[1]
        self.assertEqual((sun["state"], sun["parts"]), ("open", []))
        self.assertEqual(sun["sr"], "воскресенье, 4 октября, завтра, по предварительной записи")


@unittest.skipUnless(NODE, "node is not installed")
class LineTest(unittest.TestCase):
    def test_the_line(self):
        cases = [{"op": "line", "at": FRI_1830, "date": d, "part": p} for d, p in
                 [("2026-10-03", "evening"), ("2026-10-05", "morning"), ("2026-10-05", "any"), ("2026-10-05", None)]]
        self.assertEqual(run(*cases), [SAT_EVENING, MON_MORNING, "Удобно приехать: пн, 5 октября, в любое время",
                                       "Удобно приехать: пн, 5 октября"])

    def test_put_in_at_the_top_keeping_the_text(self):
        self.assertEqual(with_line("", SAT_EVENING), SAT_EVENING + "\n", "a tap under the line starts a new one")
        self.assertEqual(with_line("Стук в передней подвеске", SAT_EVENING), f"{SAT_EVENING}\nСтук в передней подвеске")

    def test_replaced_where_it_is_and_taken_out(self):
        text = f"{SAT_EVENING}\nСтук в передней подвеске"
        self.assertEqual(with_line(text, MON_MORNING), f"{MON_MORNING}\nСтук в передней подвеске")
        self.assertEqual(with_line(text, ""), "Стук в передней подвеске")
        self.assertEqual(with_line(SAT_EVENING + "\n", ""), "")

    def test_the_visitors_text_is_kept_to_the_character(self):
        own = "Стук\n\n  спереди справа  \nпосле мойки\n"
        self.assertEqual(with_line(with_line(own, SAT_EVENING), ""), own)
        self.assertEqual(with_line(with_line(with_line(own, SAT_EVENING), MON_MORNING), ""), own)

    def test_texts_of_other_helpers_stay(self):
        stuk = "Стук при проезде неровностей. Возможные причины: стойки стабилизатора, шаровые опоры."
        zima = "Подготовка к зиме: проверить аккумулятор, шины."
        # «Что стучит?» and «Зима» append their text at the end; the line stays on top and is replaced there
        self.assertEqual(with_line(f"{SAT_EVENING}\n{stuk}\n{zima}", MON_MORNING), f"{MON_MORNING}\n{stuk}\n{zima}")
        # a line that ended up in the middle is taken out there and put back on top
        self.assertEqual(with_line(f"{stuk}\n{SAT_EVENING}\n{zima}", MON_MORNING), f"{MON_MORNING}\n{stuk}\n{zima}")

    def test_lines_that_only_look_alike_are_the_visitors(self):
        for own in ("Удобно приехать после обеда", "Удобно приехать: в субботу", "удобно приехать: пт, 2 октября",
                    SAT_EVENING + " или в понедельник", "Удобно приехать: сб, 3 октября, вечером (15-17)"):
            self.assertEqual(with_line(own, ""), own)
            self.assertEqual(with_line(own, MON_MORNING), f"{MON_MORNING}\n{own}")

    def test_a_line_with_spaces_or_twice_is_still_one_line(self):
        self.assertEqual(with_line(f"  {SAT_EVENING}   \nСтук", ""), "Стук")
        self.assertEqual(with_line(f"{SAT_EVENING}\n{SAT_EVENING}\nСтук", MON_MORNING), f"{MON_MORNING}\nСтук")

    def test_the_text_sets_the_choice(self):
        got = run(*[{"op": "parse", "at": FRI_1830, "text": t} for t in (
            f"{SAT_EVENING}\nСтук",                                   # our line: Saturday evening
            "Удобно приехать: пн, 5 октября",                         # a day without a part
            "Стук\nУдобно приехать: пн, 5 октября, в любое время",    # anywhere in the text
            "Удобно приехать: чт, 1 октября, утром (9–12)",          # a day already gone (a restored form)
            "Удобно приехать: пт, 2 октября, вечером (15–19)",       # today, too late
            "Удобно приехать: сб, 3 октября, вечером (15–19)",       # Saturday closes at 17
            "Удобно приехать: вс, 4 октября",                        # closed
            "Стук в подвеске",
        )])
        self.assertEqual(got, [{"date": "2026-10-03", "part": "evening"}, {"date": "2026-10-05", "part": None},
                               {"date": "2026-10-05", "part": "any"}, {"invalid": True}, {"invalid": True},
                               {"invalid": True}, {"invalid": True}, None])


if __name__ == "__main__":
    unittest.main()
