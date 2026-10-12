#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сырые данные Wordstat для семантического ядра каждой страницы услуг.

Берёт фразы из seo/seeds.json и для каждой страницы сохраняет seo/raw/<slug>.json:
  seeds: частота фразы, до 300 запросов с её словами и похожие запросы (associations);
  alts:  частота альтернативных формулировок и их 20 главных уточнений.
Регион 47 (Нижний Новгород).

Квота Search API — 100 запросов Wordstat в час на весь аккаунт, и она общая с проектом ПРАКТИК/seo-agent.
Поэтому сборщик:
  * держит темп --per-hour (по умолчанию 70), оставляя запас соседнему проекту;
  * при ответе «квота исчерпана» (HTTP 429) ждёт --cooldown минут и продолжает, а не падает;
  * альтернативную формулировку, которая уже есть в уточнениях основной фразы, берёт оттуда без запроса;
  * ответы кэшируются в seo/wordstat_cache.json на 30 дней, готовые страницы без --force пропускаются.
При HTTP 401/403 (ключ не принят) останавливается сразу.

Запуск (python из venv соседнего проекта, там есть httpx и yaml):
  PY="/Users/scorpocha/рабочее/ПРАКТИК/seo-agent/.venv/bin/python"
  $PY seo/collect_core.py                     # все страницы, которых ещё нет в seo/raw
  $PY seo/collect_core.py --only remont-dvigatela --force
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT = Path(os.environ.get("SEO_AGENT_DIR", HERE.parent.parent / "ПРАКТИК" / "seo-agent"))
sys.path.insert(0, str(AGENT / "tools"))

import httpx  # noqa: E402  (есть в venv seo-agent, им пользуется сам клиент)
import wordstat as ws  # noqa: E402  (клиент из seo-agent, ключ читается из его .env и не печатается)

ws.CACHE = HERE / "wordstat_cache.json"
REGIONS = ["47"]
SEED_PHRASES = 300
ALT_PHRASES = 20
RAW = HERE / "raw"
MAX_COOLDOWNS = 14          # сколько раз подряд можно ждать сброса квоты, прежде чем сдаться
NET_RETRIES = 6             # обрывы TLS и таймауты: сеть на этой машине бывает нестабильной


def log(msg: str) -> None:
    print(f"{datetime.now():%H:%M:%S} {msg}", flush=True)


def norm(phrase: str) -> str:
    return " ".join(phrase.lower().replace("ё", "е").split())


class PacedClient:
    """Обёртка над ws.Client: темп запросов, ожидание сброса квоты, счётчик реальных вызовов API."""

    def __init__(self, per_hour: int, cooldown_min: int) -> None:
        self.client = ws.Client(regions=REGIONS)
        self.gap = 3600.0 / per_hour
        self.cooldown = cooldown_min * 60
        self.last_call = 0.0
        self.api_calls = 0

    def _is_cached(self, phrase: str, n: int) -> bool:
        key = f"top:{' '.join(phrase.split())[:400].lower()}:{n}:{','.join(self.client.regions)}:{','.join(self.client.devices)}"
        return self.client._cached(key) is not None  # noqa: SLF001  (тот же проект, тот же формат ключа)

    def top(self, phrase: str, n: int) -> dict:
        if self._is_cached(phrase, n):
            return self.client.top(phrase, n)
        cooldowns = 0
        net_errors = 0
        while True:
            wait = self.last_call + self.gap - time.time()
            if wait > 0:
                time.sleep(wait)
            self.last_call = time.time()
            try:
                result = self.client.top(phrase, n)
                self.api_calls += 1
                return result
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                net_errors += 1
                if net_errors > NET_RETRIES:
                    raise ws.WordstatError(f"сеть недоступна: {exc}") from exc
                pause = 15 * net_errors
                log(f"сетевая ошибка ({type(exc).__name__}), повтор через {pause} с, попытка {net_errors} из {NET_RETRIES}")
                time.sleep(pause)
                continue
            except ws.WordstatError as exc:
                msg = str(exc)
                if "HTTP 401" in msg or "HTTP 403" in msg:
                    raise
                if "HTTP 429" not in msg and "исчерпаны попытки" not in msg:
                    raise
                cooldowns += 1
                if cooldowns > MAX_COOLDOWNS:
                    raise
                log(f"квота Wordstat исчерпана, жду {self.cooldown // 60} мин (попытка {cooldowns} из {MAX_COOLDOWNS})")
                time.sleep(self.cooldown)


def from_seed_results(alt: str, seeds: list[dict]) -> dict | None:
    """Альтернатива уже есть среди уточнений основной фразы: частота известна без отдельного запроса."""
    target = norm(alt)
    for s in seeds:
        if norm(s["phrase"]) == target:
            return {"phrase": alt, "total": s["total"], "results": s["results"][:ALT_PHRASES], "associations": [], "from": "seed"}
        for r in s["results"]:
            if norm(r["phrase"]) == target:
                return {"phrase": alt, "total": r["count"], "results": [], "associations": [], "from": "seed-results"}
    return None


def collect_page(api: PacedClient, page: dict) -> dict:
    seeds = [api.top(s, SEED_PHRASES) for s in page["seeds"]]
    alts = []
    for alt in page["alts"]:
        known = from_seed_results(alt, seeds)
        alts.append(known if known else api.top(alt, ALT_PHRASES))
    return {"slug": page["slug"], "path": page["path"], "h1": page["h1"], "region": REGIONS[0],
            "collected": date.today().isoformat(), "seeds": seeds, "alts": alts}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", default=[], metavar="SLUG")
    ap.add_argument("--force", action="store_true", help="пересобрать файл, даже если он уже есть (кэш API всё равно используется)")
    ap.add_argument("--per-hour", type=int, default=70, help="не больше стольких запросов к API в час (квота аккаунта 100)")
    ap.add_argument("--cooldown", type=int, default=10, help="минут ждать после ответа «квота исчерпана»")
    args = ap.parse_args()

    pages = json.loads((HERE / "seeds.json").read_text(encoding="utf-8"))["pages"]
    if args.only:
        unknown = set(args.only) - {p["slug"] for p in pages}
        if unknown:
            print(f"нет таких страниц в seeds.json: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        pages = [p for p in pages if p["slug"] in args.only]
    RAW.mkdir(exist_ok=True)
    todo = [p for p in pages if args.force or not (RAW / f"{p['slug']}.json").exists()]
    log(f"страниц к сбору: {len(todo)} из {len(pages)}, темп до {args.per_hour} запросов в час")
    api = PacedClient(args.per_hour, args.cooldown)
    for i, page in enumerate(todo, 1):
        try:
            data = collect_page(api, page)
        except ws.WordstatError as exc:
            log(f"[{i}/{len(todo)}] {page['slug']}: остановка, ошибка Wordstat: {str(exc)[:200]}")
            log("собранное сохранено, повторный запуск продолжит с этой страницы")
            return 1
        (RAW / f"{page['slug']}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        main_total = data["seeds"][0]["total"] if data["seeds"] else "—"
        log(f"[{i}/{len(todo)}] {page['slug']}: {main_total} (запросов к API за запуск: {api.api_calls})")
    log(f"готово, запросов к API за запуск: {api.api_calls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
