#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wordstat-проверка формулировок для garage.team.

Использует клиент Wordstat из соседнего проекта (ПРАКТИК/seo-agent, Yandex Cloud Search API).
Ключ читается из .env того проекта и нигде не печатается. Кэш ведётся свой: seo/wordstat_cache.json.

Запуск (python из venv того проекта, там есть httpx и yaml):
  PY="/Users/scorpocha/рабочее/ПРАКТИК/seo-agent/.venv/bin/python"
  $PY seo/wordstat_check.py                      # все группы, отчёт в seo/wordstat-report.md
  $PY seo/wordstat_check.py --top "автосервис"   # что дописывают к фразе (регион Нижний Новгород)
  $PY seo/wordstat_check.py --freq "фраза 1" "фраза 2"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT = Path(os.environ.get("SEO_AGENT_DIR", HERE.parent.parent / "ПРАКТИК" / "seo-agent"))
sys.path.insert(0, str(AGENT / "tools"))

import wordstat as ws  # noqa: E402  (клиент из seo-agent)

ws.CACHE = HERE / "wordstat_cache.json"  # свой кэш, чужой не трогаем

NN = ["47"]        # Нижний Новгород
RU = ["225"]       # Россия: для фраз, где город назван словами

GROUPS: list[tuple[str, list[str], list[str]]] = [
    ("Главное слово для заголовка · спрос в Нижнем Новгороде, город в запросе не назван", NN, [
        "автосервис", "автотехцентр", "техцентр", "сто", "станция техобслуживания", "автомастерская",
        "ремонт автомобилей", "ремонт авто", "ремонт машин", "обслуживание автомобилей",
        "техобслуживание автомобиля", "ремонт иномарок", "автосервис рядом",
    ]),
    ("Запрос с названием города · вся Россия", RU, [
        "автосервис нижний новгород", "автотехцентр нижний новгород", "сто нижний новгород",
        "ремонт автомобилей нижний новгород", "ремонт авто нижний новгород", "техцентр нижний новгород",
    ]),
    ("Названия услуг · спрос в Нижнем Новгороде", NN, [
        "диагностика автомобиля", "компьютерная диагностика автомобиля", "ремонт двигателя", "ремонт акпп",
        "ремонт коробки передач", "ремонт ходовой", "ремонт подвески", "сход развал", "развал схождение",
        "кузовной ремонт", "покраска авто", "шиномонтаж", "заправка кондиционера авто", "автоэлектрик",
        "чип тюнинг", "замена масла", "замена ремня грм", "замена тормозных колодок", "ремонт глушителя",
        "техосмотр", "полировка авто", "химчистка салона авто", "хранение шин", "автозапчасти",
        "запчасти для иномарок",
    ]),
    ("Пары названий и отдельные ниши · спрос в Нижнем Новгороде", NN, [
        "автоэлектрика", "ремонт электрооборудования автомобиля", "ремонт трансмиссии", "заправка кондиционера",
        "заправка автокондиционера", "химчистка салона", "замена масла в двигателе", "замена масла в акпп",
        "ремонт тормозной системы", "ремонт рулевой рейки", "ремонт фар", "ремонт турбин", "ремонт дизельных двигателей",
        "ремонт выхлопной системы", "грузовой автосервис", "ремонт газели",
        "ремонт коммерческого транспорта", "автосервис гараж", "сто авто",
    ]),
]


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def run_groups() -> str:
    out: list[str] = ["# Wordstat: спрос по формулировкам garage.team", "",
                      "Показы в месяц, широкое соответствие (все запросы, где есть слова фразы). Источник: Yandex Cloud Search API.", ""]
    for title, regions, phrases in GROUPS:
        client = ws.Client(regions=regions)
        rows: list[tuple[int, str]] = []
        for ph in phrases:
            try:
                rows.append((client.freq(ph), ph))
            except ws.WordstatError as e:
                msg = str(e)
                rows.append((-1, f"{ph} (ошибка: {msg[:70]})"))
                if "HTTP 401" in msg or "HTTP 403" in msg:
                    raise
        rows.sort(reverse=True)
        out += [f"## {title}", "", "| Показов/мес | Фраза |", "|---:|---|"]
        out += [f"| {fmt(n) if n >= 0 else '—'} | {ph} |" for n, ph in rows]
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", help="показать уточнения к фразе")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--freq", nargs="+", help="частота произвольных фраз")
    ap.add_argument("--russia", action="store_true", help="считать по всей России, а не по Нижнему Новгороду")
    a = ap.parse_args()
    regions = RU if a.russia else NN
    try:
        if a.top:
            r = ws.Client(regions=regions).top(a.top, a.n)
            print(f"«{r['phrase']}»: {fmt(r['total'])} показов/мес, регион {regions[0]}")
            for x in r["results"]:
                print(f"  {fmt(x['count']):>9}  {x['phrase']}")
            if r["associations"]:
                print("  похожие:", "; ".join(f"{x['phrase']} ({fmt(x['count'])})" for x in r["associations"][:10]))
            return 0
        if a.freq:
            c = ws.Client(regions=regions)
            for ph in a.freq:
                print(f"{fmt(c.freq(ph)):>9}  {ph}")
            return 0
        report = run_groups()
        (HERE / "wordstat-report.md").write_text(report + "\n", encoding="utf-8")
        print(report)
        return 0
    except ws.WordstatError as e:
        print(f"[ERR] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
