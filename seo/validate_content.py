#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SEO- и фактологическая проверка подробных текстов страниц услуг.

Проверяет только страницы, у которых есть data/content/<slug>.json, и печатает, сколько ещё без текста.
Структуру файла проверяет сама сборка (build/content.py); здесь — всё, что про качество и SEO:

  ошибки (код выхода 1):
    * нет ядра seo/core/<slug>.json или один главный запрос закреплён за двумя страницами
      (в том числе за магазином, каталогом или главной из data/page_seo.json);
    * главного запроса нет в заголовке вкладки, в H1 или в первых 300 знаках текста;
    * точное вхождение главного запроса занимает больше 2,5 % слов (переспам);
    * «в Нижнем Новгороде» в тексте страницы больше трёх раз;
    * абзац длиннее 120 знаков повторяется на другой странице;
    * в тексте сумма в рублях, которой нет в прайсе этой страницы;
    * слова из стоп-листа;
    * «цена/цены/стоимость» в заголовке вкладки на странице без прайса;
    * текст короче минимума (конкретная работа 3 500 знаков, направление 5 000), вопросов меньше 4;
    * страницы с юридически чувствительными услугами без оговорки о техническом регламенте;
    * в собранной странице dist/ не один H1, битый JSON-LD или другой <title>.
  предупреждения: мало пунктов в блоках, слишком длинный текст.

  python3 seo/validate_content.py              # проверка, таблица по страницам
  python3 seo/validate_content.py --renames    # плюс seo/renames.md: старые и новые названия для владельца
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import data as D  # noqa: E402  (сборка сама проверяет структуру файлов)
from build.content import slug_of_path  # noqa: E402

CORE = ROOT / "seo" / "core"
DIST = ROOT / "dist"
MIN_CHARS_LEAF = 3500
MIN_CHARS_CATEGORY = 5000
MAX_CHARS = 16000
MAX_DENSITY = 0.025
MAX_CITY = 3
MIN_FAQ = 4
DUP_PARAGRAPH = 120
STOP = ["индивидуальный подход", "команда профессионалов", "высокое качество", "высококачественн", "в кратчайшие сроки",
        "доступные цены", "доступными ценами", "лучший автосервис", "лучшие специалисты", "номер один", "№1", "мы рады",
        "современное оборудование", "современным оборудованием", "опытные мастера", "квалифицированные специалисты",
        "широкий спектр", "гибкая система скидок", "не имеет аналогов"]
PRICE = re.compile(r"(\d[\d\s ]*\d|\d)\s?(?:₽|руб)", re.I)
LEGAL = {  # услуги, где нельзя писать о законности без оговорки
    "cip-tuning__udalenie-i-pereprogrammirovanie-sazevyh-filtrov", "cip-tuning__udalenieotklucenie-moceviny-adblue",
    "cip-tuning__udalenie-katalizatorov-i-adaptacia-raboty-lambda-zondov", "cip-tuning__programmnoe-udalenie-osibki-po-lambda-zondam",
    "remont-vyhlopnoj-sistemy__udalenie-katalizatora", "remont-elektrooborudovania-avtomobila__ustanovka-ksenona",
}
LEGAL_MARK = re.compile(r"ТР ТС 018/2011|технического регламента|техническому регламенту|техрегламент", re.I)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(s).lower().replace("ё", "е")).strip()


def flat(s: str) -> str:
    """norm() plus hyphens inside words as spaces: «чип-тюнинг» and «чип тюнинг» are the same query for a search engine."""
    return re.sub(r"(?<=\w)[-‐](?=\w)", " ", norm(s))


def plain(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def stems(phrase: str) -> list[str]:
    """Грубая основа слова: первые 5 букв (достаточно, чтобы «замена ремня грм» нашлась в «замену ремня ГРМ»)."""
    return [w[:5] if len(w) > 5 else w for w in re.findall(r"\w+", norm(phrase))]


def has_words(text: str, phrase: str) -> bool:
    words = re.findall(r"\w+", norm(text))
    return all(any(w.startswith(st) for w in words) for st in stems(phrase))


def body_texts(c: dict) -> list[str]:
    """Все тексты страницы, которые видит человек, кроме заголовка вкладки и описания."""
    out = [c["h1"], *c["lead"]]
    for key in ("price_factors", "symptoms", "includes", "steps", "faq"):
        b = c.get(key)
        if not b:
            continue
        out += [b["h2"], b.get("intro", ""), b.get("note", "")]
        for it in b["items"]:
            out += [it] if isinstance(it, str) else list(it.values())
    for s in c.get("sections", []):
        out += [s["h2"], s["html"]]
    if c.get("price_h2"):
        out.append(c["price_h2"])
    return [plain(x) for x in out if x]


def paragraphs(c: dict) -> list[str]:
    parts = list(c["lead"])
    for s in c.get("sections", []):
        parts += re.findall(r"<(?:p|li)>(.*?)</(?:p|li)>", s["html"], re.S)
    for key in ("symptoms", "includes", "price_factors"):
        if c.get(key):
            parts += [x for x in c[key]["items"] if isinstance(x, str)]
    if c.get("steps"):
        parts += [x["text"] for x in c["steps"]["items"]]
    if c.get("faq"):
        parts += [x["a"] for x in c["faq"]["items"]]
    return [norm(plain(p)) for p in parts if len(plain(p)) >= DUP_PARAGRAPH]


def page_prices(svc: dict) -> set[int]:
    amounts = set()
    for row in svc.get("price_rows") or []:
        for cell in row[1:]:
            p = D.parse_amount(cell)
            if p:
                amounts.add(p[1])
    return amounts


def check_dist(path: str, c: dict) -> list[str]:
    f = DIST / path.lstrip("/")
    if not f.exists():
        return ["нет собранной страницы в dist/: запустите python3 build.py"]
    page = f.read_text(encoding="utf-8")
    errs = []
    if len(re.findall(r"<h1[\s>]", page)) != 1:
        errs.append("в собранной странице не один H1")
    title = re.search(r"<title>(.*?)</title>", page, re.S)
    if not title or html.unescape(title.group(1)) != c["title"]:
        errs.append("title в dist/ не совпадает с файлом (пересоберите сайт)")
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            json.loads(block)
        except json.JSONDecodeError as exc:
            errs.append(f"JSON-LD не разбирается: {exc}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--renames", action="store_true", help="записать seo/renames.md")
    ap.add_argument("--quiet", action="store_true", help="не печатать таблицу, только ошибки")
    ap.add_argument("--only", nargs="+", default=[], metavar="SLUG", help="показать только эти страницы (дубли абзацев всё равно ищутся по всем)")
    ap.add_argument("--prefix", help="показать только страницы, slug которых начинается с этого")
    ap.add_argument("--no-dist", action="store_true", help="не проверять собранные страницы в dist/ (когда сборку делает другой)")
    args = ap.parse_args()

    errors: dict[str, list[str]] = defaultdict(list)
    warnings: dict[str, list[str]] = defaultdict(list)
    rows = []
    mains: dict[str, list[str]] = defaultdict(list)
    for f in sorted(CORE.glob("*.json")):
        core = json.loads(f.read_text(encoding="utf-8"))
        mains[norm(core["main"]["phrase"])].append(f.stem)
    for phrase, slugs in mains.items():
        if len(slugs) > 1:
            for sl in slugs:
                errors[sl].append(f"главный запрос «{phrase}» закреплён и за {', '.join(x for x in slugs if x != sl)}")
    # страницы не услуг (магазин, каталоги, главная): их запросы из data/page_seo.json тоже не должны совпадать с услугами
    for key, seo in D.PAGE_SEO.items():
        main = seo.get("main")
        if not main:
            continue
        where = f"page_seo:{key}"
        for sl in mains.get(norm(main), []):
            errors[where].append(f"главный запрос «{main}» совпадает с главным запросом услуги {sl}")
            errors[sl].append(f"главный запрос «{main}» уже закреплён за страницей {key} (data/page_seo.json)")
        if not has_words(seo["title"], main):
            errors[where].append(f"главного запроса «{main}» нет в title")
        if seo.get("h1") and not has_words(seo["h1"], main):
            errors[where].append(f"главного запроса «{main}» нет в H1")

    seen_paragraphs: dict[str, str] = {}
    for path, c in sorted(D.CONTENT.items()):
        slug = slug_of_path(path)
        svc = D.BY_PATH[path]
        is_cat = path in D.CAT_BY_HREF
        core_file = CORE / f"{slug}.json"
        if not core_file.exists():
            errors[slug].append("нет ядра seo/core/<slug>.json")
            continue
        core = json.loads(core_file.read_text(encoding="utf-8"))
        main = core["main"]["phrase"]
        texts = body_texts(c)
        full = " ".join(texts)
        chars = len(full)

        if not has_words(c["title"], main):
            errors[slug].append(f"главного запроса «{main}» нет в title")
        if not has_words(c["h1"], main):
            errors[slug].append(f"главного запроса «{main}» нет в H1")
        if not has_words(plain(" ".join(c["lead"]))[:300], main):
            errors[slug].append(f"главного запроса «{main}» нет в первых 300 знаках")
        words = flat(full).split()
        exact = len(re.findall(r"(?<!\w)" + re.escape(flat(main)) + r"(?!\w)", flat(full)))
        density = exact * len(main.split()) / max(1, len(words))
        if density > MAX_DENSITY:
            errors[slug].append(f"плотность «{main}» {density:.1%} больше {MAX_DENSITY:.1%}")
        city = len(re.findall(r"в нижнем новгороде", norm(full)))
        if city > MAX_CITY:
            errors[slug].append(f"«в Нижнем Новгороде» {city} раз, максимум {MAX_CITY}")
        allowed = page_prices(svc)
        for m in PRICE.finditer(full):
            amount = int(re.sub(r"\D", "", m.group(1)))
            if amount not in allowed:
                errors[slug].append(f"сумма «{m.group(0)}» не из прайса этой страницы")
        low = norm(full + " " + c["title"] + " " + c["meta_description"])
        for w in STOP:
            if w in low:
                errors[slug].append(f"стоп-слово «{w}»")
        if not svc.get("price_rows") and re.search(r"цен[аы]|стоимост", c["title"], re.I):
            errors[slug].append("«цена» в title, а прайса на странице нет")
        minimum = MIN_CHARS_CATEGORY if is_cat else MIN_CHARS_LEAF
        if chars < minimum:
            errors[slug].append(f"текст {chars} знаков, минимум {minimum}")
        elif chars > MAX_CHARS:
            warnings[slug].append(f"текст {chars} знаков — проверьте, нет ли воды")
        faq_n = len(c["faq"]["items"]) if c.get("faq") else 0
        if faq_n < MIN_FAQ:
            errors[slug].append(f"вопросов {faq_n}, минимум {MIN_FAQ}")
        for key, need in (("symptoms", 4), ("includes", 5), ("steps", 4)):
            n = len(c[key]["items"]) if c.get(key) else 0
            if n < need:
                warnings[slug].append(f"{key}: {n} пунктов, желательно от {need}")
        if slug in LEGAL and not LEGAL_MARK.search(full):
            errors[slug].append("нет оговорки о техническом регламенте (юридически чувствительная услуга)")
        for p in paragraphs(c):
            h = hashlib.sha1(p.encode()).hexdigest()
            if h in seen_paragraphs and seen_paragraphs[h] != slug:
                errors[slug].append(f"абзац повторяет страницу {seen_paragraphs[h]}: «{p[:60]}…»")
            seen_paragraphs.setdefault(h, slug)
        if not args.no_dist:
            errors[slug] += check_dist(path, c)
        rows.append((slug, main, core["main"].get("freq", 0), len(c["title"]), len(c["meta_description"]), chars, faq_n))

    total = len(D.SERVICES)
    if args.only or args.prefix:
        keep = lambda sl: sl in args.only or (args.prefix and sl.startswith(args.prefix))  # noqa: E731
        rows = [r for r in rows if keep(r[0])]
        errors = defaultdict(list, {k: v for k, v in errors.items() if keep(k)})
        warnings = defaultdict(list, {k: v for k, v in warnings.items() if keep(k)})
    if not args.quiet:
        print(f"{'страница':<58} {'главный запрос':<34} {'частота':>7} {'title':>5} {'desc':>4} {'знаков':>6} {'FAQ':>3}")
        for slug, main, freq, tl, dl, chars, fq in rows:
            mark = "✗" if errors.get(slug) else ("!" if warnings.get(slug) else "✓")
            print(f"{mark} {slug[:56]:<56} {main[:34]:<34} {freq:>7} {tl:>5} {dl:>4} {chars:>6} {fq:>3}")
    for slug in sorted(set(errors) | set(warnings)):
        for e in errors.get(slug, []):
            print(f"ОШИБКА  {slug}: {e}")
        for w in warnings.get(slug, []):
            print(f"внимание {slug}: {w}")
    n_err = sum(len(v) for v in errors.values())
    print(f"\nстраниц с текстом: {len(D.CONTENT)} из {total}, без текста: {total - len(D.CONTENT)}; ошибок: {n_err}, "
          f"предупреждений: {sum(len(v) for v in warnings.values())}")

    if args.renames:
        lines = ["# Переименования страниц услуг", "",
                 "Адреса страниц не менялись. Новое название выбрано по спросу в Яндексе (Wordstat, Нижний Новгород, показов в месяц).", "",
                 "| Страница | Было | Стало (H1) | В меню | Главный запрос | Показов |", "|---|---|---|---|---|---:|"]
        for path, c in sorted(D.CONTENT.items()):
            svc = D.BY_PATH[path]
            old = svc.get("h1_original", svc["h1"])
            core_file = CORE / f"{slug_of_path(path)}.json"
            core = json.loads(core_file.read_text(encoding="utf-8")) if core_file.exists() else {"main": {"phrase": "—", "freq": 0}}
            if old == c["h1"] and old == c["nav_name"]:
                continue
            lines.append(f"| `{path}` | {old} | {c['h1']} | {c['nav_name']} | {core['main']['phrase']} | {core['main'].get('freq', 0)} |")
        (ROOT / "seo" / "renames.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("записано seo/renames.md")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
