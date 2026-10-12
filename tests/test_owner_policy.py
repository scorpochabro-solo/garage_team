"""Confirmed owner decisions must stay consistent across shared data and service copy."""
import json
import unittest
from pathlib import Path

from build import data as D


ROOT = Path(__file__).resolve().parents[1]


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)


class OwnerPolicyTest(unittest.TestCase):
    def test_service_copy_has_no_old_saturday_schedule_or_shop_vin_promise(self):
        for path in (ROOT / "data/content").glob("*.json"):
            with self.subTest(page=path.name):
                text = " ".join(strings(json.loads(path.read_text())))
                self.assertNotRegex(text, r"суббот.{0,35}17:00")
                self.assertNotRegex(text, r"(?:подбер|подбор|подбира).{0,60}по VIN")
                self.assertNotIn("с 2011 года", text)
                self.assertNotIn("магазине запчастей", text)

    def test_public_price_tables_removed(self):
        for page in D.SERVICES:
            with self.subTest(page=page["path"]):
                self.assertFalse(page.get("price_rows"))
                self.assertFalse(page.get("price_heads"))

    def test_only_verified_director_portrait_is_assigned(self):
        site = json.loads((ROOT / "data/site.json").read_text())
        portraits = [person["name"] for person in site["team"] if person.get("photo")]
        self.assertEqual(portraits, ["Александр Шишов"])
        self.assertEqual(len(site["team"]), 10)
