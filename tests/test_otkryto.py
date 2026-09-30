# -*- coding: utf-8 -*-
"""«Открыто сейчас» (build/otkryto.py, src/assets/js/otkryto.js): the hours as data, the status at fixed moments of the
Moscow clock, the vCard.  Run: python3 -m unittest discover -s tests"""
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build import otkryto as O  # noqa: E402

NODE = shutil.which("node")
SCRIPT = ROOT / "tests" / "otkryto_status.cjs"


def js_status(hours, *moments):
    """[(state, text in the contacts, text in the top line)] from otkryto.js for moments given in Moscow time."""
    week = json.dumps({"week": O.week(hours)}, ensure_ascii=False)
    out = subprocess.run([NODE, str(SCRIPT), week, *moments], capture_output=True, text=True, check=True,
                         env={"TZ": "America/Los_Angeles", "PATH": ""}).stdout   # the machine's zone must not matter
    return [(r["state"], r["text"], r["brief"]) for r in json.loads(out)]


def parse_vcard(text):
    """A strict little reader: CRLF lines, unfolding, NAME;PARAMS:VALUE, escapes. -> {name: [(params, value)]}"""
    assert text.endswith("\r\n") and "\n" not in text.replace("\r\n", ""), "only CRLF line ends"
    props = {}
    for line in text[:-2].replace("\r\n ", "").split("\r\n"):
        head, value = line.split(":", 1)
        name, *params = head.split(";")
        props.setdefault(name.upper(), []).append((params, value))
    return props


def unescape(value):
    return re.sub(r"\\(.)", lambda m: "\n" if m.group(1) in "nN" else m.group(1), value)


def components(value):
    """ADR / N / ORG: parts split on the semicolons that are not escaped"""
    return [unescape(p) for p in re.split(r"(?<!\\);", value)]


class HoursTest(unittest.TestCase):
    def test_workshop_week(self):
        week = O.week(D.HOURS)
        self.assertEqual(week[:5], [[540, 1140]] * 5)
        self.assertEqual(week[5], [540, 1020])
        self.assertIsNone(week[6], "Sunday is not in D.HOURS: closed")

    def test_shop_sunday_is_a_note(self):
        self.assertEqual(O.week(D.SHOP_HOURS)[6], {"note": "по предварительной записи"})
        self.assertEqual(O.week(D.SHOP_HOURS)[0], [600, 1140])

    def test_a_day_written_as_closed_is_closed(self):
        self.assertIsNone(O.week(D.HOURS + [("Воскресенье", "выходной")])[6])

    def test_bad_hours_are_refused(self):
        with self.assertRaises(ValueError):
            O.week([("Будни", "9:00 – 19:00")])
        with self.assertRaises(ValueError):
            O.week([("Суббота", "19:00 – 9:00")])

    def test_compact_line_is_the_old_top_line(self):
        self.assertEqual(O.compact(D.HOURS), "Пн–Пт 9:00–19:00 · Сб 9:00–17:00")
        self.assertEqual(O.compact(D.SHOP_HOURS, ", ", lower=True),
                         "пн–пт 10:00–19:00, сб 10:00–17:00, вс по предварительной записи")

    def test_markup_carries_the_week_and_keeps_plain_hours(self):
        top = O.topline_item()
        self.assertIn(D.esc(O.compact(D.HOURS)), top, "without JS the top line shows the plain hours")
        data = re.search(r'data-oc="([^"]+)"', top).group(1)
        self.assertEqual(json.loads(data.replace("&quot;", '"'))["week"], O.week(D.HOURS))
        week = O.schedule(D.HOURS)
        self.assertEqual(re.findall(r'data-day="(\d)"', week), [str(i) for i in range(7)])
        self.assertIn(">9–17<", week)
        self.assertIn("воскресенье: закрыто", week)
        self.assertIn("понедельник: с 9:00 до 19:00", week, "screen readers hear words, not a dash")
        self.assertEqual(O.actions().count(" hidden>"), 2, "copy and vCard buttons wait for JS")


@unittest.skipUnless(NODE, "node is not installed")
class StatusTest(unittest.TestCase):
    def test_the_week_of_the_workshop(self):
        rows = js_status(D.HOURS,
                         "2026-10-05T08:59:00+03:00", "2026-10-05T09:00:00+03:00", "2026-10-09T18:10:00+03:00",
                         "2026-10-09T19:00:00+03:00", "2026-10-10T16:30:00+03:00", "2026-10-10T17:00:00+03:00",
                         "2026-10-11T12:00:00+03:00")
        self.assertEqual(rows, [
            ("closed", "Закрыто · откроемся сегодня в 9:00", "Закрыто · до 9:00"),                 # Mon 8:59
            ("open", "Открыто · до 19:00", "Открыто · до 19:00"),                                   # Mon 9:00
            ("soon", "Скоро закрываемся · до 19:00", "Скоро закрываемся · до 19:00"),               # Fri 18:10
            ("closed", "Закрыто · откроемся завтра в 9:00", "Закрыто · до завтра, 9:00"),          # Fri 19:00
            ("soon", "Скоро закрываемся · до 17:00", "Скоро закрываемся · до 17:00"),               # Sat 16:30
            ("closed", "Закрыто · откроемся в понедельник в 9:00", "Закрыто · до понедельника, 9:00"),  # Sat 17:00
            ("closed", "Закрыто · откроемся завтра в 9:00", "Закрыто · до завтра, 9:00"),          # Sun 12:00
        ])

    def test_edges_of_the_last_hour_and_midnight(self):
        rows = js_status(D.HOURS, "2026-10-05T17:59:00+03:00", "2026-10-05T18:00:00+03:00",
                         "2026-10-05T18:59:00+03:00", "2026-10-05T23:59:00+03:00", "2026-10-06T00:00:00+03:00",
                         "2026-10-05T05:30:00Z")   # 05:30 UTC is 8:30 in Moscow
        self.assertEqual([r[0] for r in rows], ["open", "soon", "soon", "closed", "closed", "closed"])
        self.assertEqual(rows[3][1], "Закрыто · откроемся завтра в 9:00")
        self.assertEqual(rows[4][1], "Закрыто · откроемся сегодня в 9:00")
        self.assertEqual(rows[5][1], "Закрыто · откроемся сегодня в 9:00")

    def test_the_shop(self):
        rows = js_status(D.SHOP_HOURS, "2026-10-05T09:30:00+03:00", "2026-10-05T14:30:00+03:00",
                         "2026-10-05T18:30:00+03:00", "2026-10-10T18:00:00+03:00", "2026-10-11T12:00:00+03:00")
        self.assertEqual(rows, [
            ("closed", "Закрыто · откроемся сегодня в 10:00", "Закрыто · до 10:00"),                   # Mon 9:30
            ("open", "Открыто · до 19:00", "Открыто · до 19:00"),                                       # Mon 14:30
            ("soon", "Скоро закрываемся · до 19:00", "Скоро закрываемся · до 19:00"),                   # Mon 18:30
            ("closed", "Закрыто · завтра по предварительной записи", "Закрыто · завтра по предварительной записи"),  # Sat 18:00
            ("note", "Сегодня · по предварительной записи", "Сегодня · по предварительной записи"),     # Sun 12:00
        ])

    def test_top_line_is_never_longer_than_the_plain_hours(self):
        """the top line was laid out for «Пн–Пт 9:00–19:00 · Сб 9:00–17:00»; every short form must fit in its place"""
        hour = [f"2026-10-{d:02d}T{h:02d}:30:00+03:00" for d in range(5, 12) for h in range(24)]
        longest = max(len(r[2]) for r in js_status(D.HOURS, *hour))
        self.assertLessEqual(longest, len(O.compact(D.HOURS)))


class VCardTest(unittest.TestCase):
    def setUp(self):
        self.lines = O.vcard_lines()
        self.file = "\r\n".join(self.lines) + "\r\n"   # what otkryto.js hands to the Blob

    def test_lines_fit_75_octets_and_keep_letters_whole(self):
        for line in self.lines:
            self.assertLessEqual(len(line.encode("utf-8")), 75, line)
        self.assertTrue(all(line and not line.endswith("\\") for line in self.lines), "no escape cut in two")

    def test_the_card_reads_back(self):
        p = parse_vcard(self.file)
        self.assertEqual(p["BEGIN"][0][1], "VCARD")
        self.assertEqual(p["VERSION"][0][1], "3.0")
        self.assertEqual(unescape(p["FN"][0][1]), "Автосервис «Гараж»")
        self.assertEqual(components(p["ORG"][0][1]), ["Гараж"])
        self.assertEqual(p["TEL"][0], (["TYPE=WORK,VOICE"], D.PHONE_TEL))
        self.assertEqual(p["EMAIL"][0][1], D.EMAIL)
        self.assertEqual(components(p["ADR"][0][1]),
                         ["", "", "ул. Красная слобода, 9", "Нижний Новгород", "", "603155", "Россия"])
        self.assertEqual(p["URL"][0][1], "https://garage.team")
        self.assertEqual(p["GEO"][0][1], f"{D.COORDS[0]};{D.COORDS[1]}")
        self.assertEqual(unescape(p["NOTE"][0][1]),
                         "Автосервис: пн–пт 9:00–19:00, сб 9:00–17:00\n"
                         "Магазин запчастей: пн–пт 10:00–19:00, сб 10:00–17:00, вс по предварительной записи")
        self.assertEqual(p["END"][0][1], "VCARD")

    def test_utf8_without_bom(self):
        data = self.file.encode("utf-8")
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(data.decode("utf-8"), self.file)


if __name__ == "__main__":
    unittest.main()
