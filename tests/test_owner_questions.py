# -*- coding: utf-8 -*-
"""Tests for the questionnaire source parser (seo/owner_questions_pdf.py).  Run: python3 -m unittest discover -s tests

The PDF tool needs reportlab, fonttools and pypdf, which the site build does not; without them the tests are skipped.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "seo"))

try:
    import owner_questions_pdf as oq
except SystemExit:          # the tool exits with an install hint when a library is missing
    oq = None

SOURCE = """# Анкета

## Общие вопросы

### Мастера

- Кто что делает?

| Сотрудник | верно | поправка |
|---|---|---|
| Юрий Андреев | [ ] | ___ |

## Ремонт двигателя

- Как устроен капремонт?
  - сами;
  - подрядчик.
- Делаете ли эти работы?

| Работа | да | нет | комментарий |
|---|---|---|---|
| **Работы, которых нет на сайте** | | | |
| Замена цепи ГРМ | ( ) | ( ) | ___ |
| Регулировка клапанов | ( ) | ( ) | ___ |
"""


@unittest.skipIf(oq is None, "нет reportlab / fonttools / pypdf")
class ParseQuestionsTest(unittest.TestCase):
    def test_table_belongs_to_the_question_before_it(self):
        general, engine = oq.parse_questions(SOURCE)
        self.assertEqual(general.name, oq.GENERAL)
        text_q, table_q = engine.pages[0].questions
        self.assertEqual(text_q.subs, ["сами;", "подрядчик."])
        self.assertEqual(text_q.grid, [])
        self.assertEqual(table_q.grid[0], ["Работа", "да", "нет", "комментарий"])
        self.assertEqual(len(table_q.grid), 4)            # the |---| line is not a row

    def test_subheading_is_not_an_answer_row(self):
        table_q = oq.parse_questions(SOURCE)[1].pages[0].questions[1]
        self.assertTrue(oq.is_group_row(table_q.grid[1]))
        self.assertEqual([r[0] for r in table_q.answer_rows()], ["Замена цепи ГРМ", "Регулировка клапанов"])

    def test_column_kinds(self):
        general, engine = oq.parse_questions(SOURCE)
        masters, works = general.pages[0].questions[0], engine.pages[0].questions[1]
        self.assertEqual([oq.column_kind(masters, c) for c in range(3)], ["text", "check", "field"])
        self.assertEqual([oq.column_kind(works, c) for c in range(4)], ["text", "choice", "choice", "field"])

    def test_counts_text_questions_and_marked_rows(self):
        stats = oq.count(oq.parse_questions(SOURCE), n_renames=5)
        self.assertEqual((stats.text, stats.rows, stats.directions, stats.renames), (1, 3, 1, 5))

    def test_row_with_a_missing_cell_is_rejected(self):
        broken = SOURCE.replace("| Регулировка клапанов | ( ) | ( ) | ___ |", "| Регулировка клапанов | ( ) | ___ |")
        with self.assertRaises(SystemExit):
            oq.parse_questions(broken)

    def test_mixed_cells_in_one_column_are_rejected(self):
        broken = SOURCE.replace("| Регулировка клапанов | ( ) | ( ) | ___ |", "| Регулировка клапанов | ( ) | ___ | ___ |")
        with self.assertRaises(SystemExit):
            oq.parse_questions(broken)

    def test_table_without_a_question_is_rejected(self):
        with self.assertRaises(SystemExit):
            oq.parse_questions("## Раздел\n\n| А | да |\n|---|---|\n| x | ( ) |\n")

    def test_plural(self):
        self.assertEqual([oq.plural(n, "вопрос", "вопроса", "вопросов") for n in (1, 3, 11, 18, 21, 205)],
                         ["вопрос", "вопроса", "вопросов", "вопросов", "вопрос", "вопросов"])

    def test_short_source_parses(self):
        directions = oq.parse_questions((ROOT / "seo" / "owner-questions-short.md").read_text(encoding="utf-8"))
        self.assertEqual(directions[0].name, oq.GENERAL)
        self.assertGreater(oq.count(directions, 0).rows, 0)

    def test_every_rename_is_a_site_page(self):
        order = oq.site_order()
        renames = oq.parse_renames((ROOT / "seo" / "renames.md").read_text(encoding="utf-8"))
        self.assertTrue(renames)
        self.assertEqual([r["path"] for r in renames if r["path"] not in order], [])


if __name__ == "__main__":
    unittest.main()
