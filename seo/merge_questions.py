#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает вопросы владельцу из seo/owner-questions/<группа>.md в один файл seo/owner-questions.md.

В файлах групп каждая страница начинается с заголовка «## <slug>», под ним — вопросы списком.
В общем файле страницы идут в порядке меню сайта (направление, затем его работы) с названием и адресом страницы,
в начале — сколько вопросов и по скольким страницам. Неизвестный slug останавливает сборку: вопрос не должен потеряться.

  python3 seo/merge_questions.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402
from build.content import slug_of_path  # noqa: E402

SRC = ROOT / "seo" / "owner-questions"
OUT = ROOT / "seo" / "owner-questions.md"
QUESTION = re.compile(r"^\s*[-*] ", re.M)


def read_sections() -> dict[str, list[str]]:
    """{slug: [markdown blocks from every group file that asks about this page]}"""
    sections: dict[str, list[str]] = {}
    for file in sorted(SRC.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        for m in re.finditer(r"^## +(\S+)[^\n]*\n(.*?)(?=^## |^# |\Z)", text, re.S | re.M):
            body = m.group(2).strip()
            if body:
                sections.setdefault(m.group(1), []).append(body)
    return sections


def page_order() -> list[tuple[str, str, str, bool]]:
    """[(slug, path, name, is_direction)] in the order of the site menu."""
    out = []
    for cat in D.CATEGORIES:
        out.append((slug_of_path(cat["href"]), cat["href"], cat["name"], True))
        for sub in cat["subs"]:
            out.append((slug_of_path(sub["href"]), sub["href"], sub["name"], False))
    return out


def main() -> int:
    sections = read_sections()
    order = page_order()
    known = {slug for slug, *_ in order}
    unknown = sorted(set(sections) - known)
    if unknown:
        print(f"нет таких страниц на сайте: {', '.join(unknown)}", file=sys.stderr)
        return 1

    body = []
    n_questions = 0
    for slug, path, name, is_direction in order:
        if slug not in sections:
            continue
        text = "\n\n".join(sections[slug])
        n_questions += len(QUESTION.findall(text))
        heading = "##" if is_direction else "###"
        body.append(f"{heading} {name}\n\n`{path}`\n\n{text}\n")
    pages = len(sections)
    head = [
        "# Вопросы владельцу по страницам услуг",
        "",
        f"{n_questions} вопросов по {pages} страницам. Собрано из `seo/owner-questions/*.md` скриптом `seo/merge_questions.py`,",
        "правьте файлы групп, а этот файл пересобирайте.",
        "",
        "Ответы нужны, чтобы дописать страницы фактами: на сайте сейчас нет ничего, что не подтверждено данными старого сайта,",
        "прайсом или общими техническими знаниями. Где ответ меняет текст, это сказано в самом вопросе.",
        "",
    ]
    OUT.write_text("\n".join(head) + "\n" + "\n".join(body), encoding="utf-8")
    print(f"записано {OUT.relative_to(ROOT)}: {n_questions} вопросов, {pages} страниц")
    return 0


if __name__ == "__main__":
    sys.exit(main())
