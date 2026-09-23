#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Компактный просмотр сырых данных Wordstat (seo/raw/<slug>.json) для выбора ядра страницы.

  python3 seo/core_view.py diagnostika diagnostika__komputernaa-diagnostika   # конкретные страницы
  python3 seo/core_view.py --prefix diagnostika                               # все страницы направления
  python3 seo/core_view.py --n 40 --prefix remont-dvigatela

Показывает: частоту основной фразы, главные уточнения без шума, вопросы людей (для FAQ),
похожие запросы (синонимы) и частоты альтернативных названий.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"

NOISE = re.compile(
    r"своими руками|видео|youtube|ютуб|форум|схем[аы]|фото|инструкц|драйв|drive2|авито|avito|отзыв|"
    r"москв|спб|санкт|петербург|питер|казан|самар|екатеринбург|новосибирск|краснодар|воронеж|челябинск|"
    r"ростов|уф[аеы]\b|перм|дзержинск|кстово|арзамас|выкс|балахн|богородск|павлово|городец|чебоксар|"
    r"владимир|ярославл|минск|беларус|украин|скачать|бесплатно|игр[аы]|мультик|рисун|раскраск|тест\b|"
    r"вакансии|работа\b|обучени|курс[ыа]?\b|книг|pdf",
    re.I)
QUESTION = re.compile(r"^(как|сколько|когда|через сколько|что|почему|зачем|нужно ли|можно ли|стоит ли|какой|какая|какие|где|чем|надо ли)\b", re.I)


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def show(path: Path, n: int) -> None:
    d = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n=== {d['slug']}  | H1 сейчас: «{d['h1']}»")
    for s in d["seeds"]:
        res = s["results"]
        clean = [r for r in res if not NOISE.search(r["phrase"]) and not QUESTION.search(r["phrase"])]
        questions = [r for r in res if QUESTION.search(r["phrase"]) and not NOISE.search(r["phrase"])]
        print(f"  основная «{s['phrase']}»: {fmt(s['total'])}")
        print("    уточнения: " + "; ".join(f"{r['phrase']} {fmt(r['count'])}" for r in clean[1:n + 1]))
        if questions:
            print("    вопросы:   " + "; ".join(f"{r['phrase']} {fmt(r['count'])}" for r in questions[:12]))
        if s.get("associations"):
            print("    похожие:   " + "; ".join(f"{r['phrase']} {fmt(r['count'])}" for r in s["associations"][:12]))
    if d["alts"]:
        print("  альтернативы: " + "; ".join(f"{a['phrase']} {fmt(a['total'])}" for a in d["alts"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--prefix", help="все страницы, slug которых начинается с этого")
    ap.add_argument("--n", type=int, default=25, help="сколько уточнений показывать")
    a = ap.parse_args()
    files = [RAW / f"{s}.json" for s in a.slugs]
    if a.prefix:
        files += sorted(RAW.glob(f"{a.prefix}*.json"))
    missing = [f.stem for f in files if not f.exists()]
    if missing:
        print("ещё не собрано: " + ", ".join(missing), file=sys.stderr)
    for f in files:
        if f.exists():
            show(f, a.n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
