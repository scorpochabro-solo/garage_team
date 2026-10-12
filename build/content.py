# -*- coding: utf-8 -*-
"""Detailed service-page content from data/content/<slug>.json.

The slug is the page path without "/services/" and ".html", with "/" replaced by "__":
    /services/remont-dvigatela.html                  -> remont-dvigatela
    /services/remont-dvigatela/zamena-remna-grm.html -> remont-dvigatela__zamena-remna-grm

A page without a content file keeps the old rendering, so pages can be filled one batch at a time.
Every file is checked here at build time: a broken file stops the build with the file name and the reason.

File format (all text is Russian, inline HTML only where noted):
{
  "h1": "Замена ремня ГРМ",                        page heading
  "nav_name": "Замена ремня ГРМ",                  name in menus, lists, breadcrumbs
  "title": "…",                                     <title>, up to 70 characters
  "meta_description": "…",                          120–170 characters
  "lead": ["paragraph", "paragraph"],               inline HTML allowed
  "price_h2": "Цены на замену ремня ГРМ",           optional heading of the price table
  "price_factors": {"h2": "…", "intro": "…", "items": ["…"], "note": "…"},
  "symptoms":      {"h2": "…", "intro": "…", "items": ["…"]},
  "includes":      {"h2": "…", "intro": "…", "items": ["…"]},
  "steps":         {"h2": "…", "intro": "…", "items": [{"title": "…", "text": "…"}]},
  "sections":      [{"h2": "…", "html": "<p>…</p><ul><li>…</li></ul>"}],
  "faq":           {"h2": "…", "items": [{"q": "…", "a": "…"}]},
  "related":       ["/services/…html"],
  "staff":         ["Имя Фамилия"],                 people from data/site.json whose role matches the work
  "contact":       "shop"                           who answers the page: "service" (default, booking a repair)
                                                   or "shop" (the parts shop: its button, note and opening hours)
}
Blocks other than h1, nav_name, title, meta_description and lead are optional.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path

INLINE_TAGS = {"strong", "em", "b", "i", "a", "br", "span", "nobr"}
BLOCK_TAGS = {"p", "ul", "ol", "li", "h3", "blockquote"}
VOID_TAGS = {"br"}
TITLE_MAX = 70
CONTACT_MODES = ("service", "shop")
DESCRIPTION_RANGE = (120, 170)


class ContentError(ValueError):
    """A content file is malformed; the message names the file and the field."""


def slug_of_path(path: str) -> str:
    if not (path.startswith("/services/") and path.endswith(".html")):
        raise ContentError(f"не страница услуги: {path}")
    return path[len("/services/"):-len(".html")].replace("/", "__")


class _TagChecker(HTMLParser):
    def __init__(self, allowed: set[str]) -> None:
        super().__init__(convert_charrefs=True)
        self.allowed = allowed
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed:
            self.errors.append(f"тег <{tag}> не разрешён")
            return
        if tag == "a":
            href = dict(attrs).get("href") or ""
            if not href.startswith(("/", "tel:", "mailto:", "https://")):
                self.errors.append(f"ссылка {href!r}: нужен путь от корня сайта, tel:, mailto: или https://")
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"закрывающий </{tag}> не на своём месте")
            return
        self.stack.pop()

    def close(self) -> None:
        super().close()
        if self.stack:
            self.errors.append(f"не закрыты теги: {', '.join(self.stack)}")


def _check_html(value: str, where: str, allowed: set[str]) -> None:
    checker = _TagChecker(allowed)
    checker.feed(value)
    checker.close()
    if checker.errors:
        raise ContentError(f"{where}: {'; '.join(checker.errors)}")


def _text(d: dict, key: str, where: str, *, html: bool = False, required: bool = True) -> None:
    value = d.get(key)
    if value is None and not required:
        return
    if not isinstance(value, str) or not value.strip():
        raise ContentError(f"{where}.{key}: нужна непустая строка")
    if html:
        _check_html(value, f"{where}.{key}", INLINE_TAGS)


def _list_block(d: dict, key: str, where: str, item_check) -> None:
    block = d.get(key)
    if block is None:
        return
    if not isinstance(block, dict):
        raise ContentError(f"{where}.{key}: нужен объект с h2 и items")
    _text(block, "h2", f"{where}.{key}")
    _text(block, "intro", f"{where}.{key}", html=True, required=False)
    _text(block, "note", f"{where}.{key}", html=True, required=False)
    items = block.get("items")
    if not isinstance(items, list) or not items:
        raise ContentError(f"{where}.{key}.items: нужен непустой список")
    for i, item in enumerate(items):
        item_check(item, f"{where}.{key}.items[{i}]")


def _inline_item(item, where: str) -> None:
    if not isinstance(item, str) or not item.strip():
        raise ContentError(f"{where}: нужна непустая строка")
    _check_html(item, where, INLINE_TAGS)


def _step_item(item, where: str) -> None:
    if not isinstance(item, dict):
        raise ContentError(f"{where}: нужен объект с title и text")
    _text(item, "title", where)
    _text(item, "text", where, html=True)


def _faq_item(item, where: str) -> None:
    if not isinstance(item, dict):
        raise ContentError(f"{where}: нужен объект с q и a")
    _text(item, "q", where)
    _text(item, "a", where, html=True)


def _check_lengths(d: dict, where: str) -> None:
    if len(d["title"]) > TITLE_MAX:
        raise ContentError(f"{where}.title: {len(d['title'])} знаков, максимум {TITLE_MAX}")
    lo, hi = DESCRIPTION_RANGE
    if not lo <= len(d["meta_description"]) <= hi:
        raise ContentError(f"{where}.meta_description: {len(d['meta_description'])} знаков, нужно {lo}–{hi}")


def validate(d: dict, where: str, known_paths: set[str], team: set[str]) -> None:
    """Structure only; the SEO checks (lengths of texts, keywords, duplicates) live in seo/validate_content.py."""
    for key in ("h1", "nav_name", "title", "meta_description"):
        _text(d, key, where)
    _check_lengths(d, where)
    lead = d.get("lead")
    if not isinstance(lead, list) or not lead:
        raise ContentError(f"{where}.lead: нужен непустой список абзацев")
    for i, p in enumerate(lead):
        _inline_item(p, f"{where}.lead[{i}]")
    _text(d, "price_h2", where, required=False)
    for key in ("price_factors", "symptoms", "includes"):
        _list_block(d, key, where, _inline_item)
    _list_block(d, "steps", where, _step_item)
    _list_block(d, "faq", where, _faq_item)
    sections = d.get("sections", [])
    if not isinstance(sections, list):
        raise ContentError(f"{where}.sections: нужен список")
    for i, s in enumerate(sections):
        if not isinstance(s, dict):
            raise ContentError(f"{where}.sections[{i}]: нужен объект с h2 и html")
        _text(s, "h2", f"{where}.sections[{i}]")
        _text(s, "html", f"{where}.sections[{i}]")
        _check_html(s["html"], f"{where}.sections[{i}].html", INLINE_TAGS | BLOCK_TAGS)
    for i, path in enumerate(d.get("related", [])):
        if path not in known_paths:
            raise ContentError(f"{where}.related[{i}]: нет такой страницы {path}")
    for i, name in enumerate(d.get("staff", [])):
        if name not in team:
            raise ContentError(f"{where}.staff[{i}]: {name!r} нет в команде data/site.json")
    if d.get("contact", "service") not in CONTACT_MODES:
        raise ContentError(f"{where}.contact: {d['contact']!r}, можно {' или '.join(CONTACT_MODES)}")
    unknown = set(d) - {"h1", "nav_name", "title", "meta_description", "lead", "price_h2", "price_factors", "symptoms",
                        "includes", "steps", "sections", "faq", "related", "staff", "contact", "_note"}
    if unknown:
        raise ContentError(f"{where}: неизвестные поля {', '.join(sorted(unknown))}")


PAGE_SEO_FIELDS = {"main", "h1", "title", "meta_description"}


def load_page_seo(file: Path, known_keys: set[str]) -> dict[str, dict]:
    """{page key: {title, meta_description, h1?, main?}} for the pages that are not services (data/page_seo.json)."""
    if not file.exists():
        return {}
    try:
        d = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContentError(f"{file.name}: битый JSON: {exc}") from exc
    out: dict[str, dict] = {}
    for key, v in d.items():
        if key.startswith("_"):
            continue
        where = f"{file.name}: {key}"
        if key not in known_keys:
            raise ContentError(f"{where}: нет такой страницы, есть {', '.join(sorted(known_keys))}")
        if not isinstance(v, dict):
            raise ContentError(f"{where}: нужен объект с title и meta_description")
        for field in ("title", "meta_description"):
            _text(v, field, where)
        for field in ("main", "h1"):
            _text(v, field, where, required=False)
        _check_lengths(v, where)
        unknown = set(v) - PAGE_SEO_FIELDS
        if unknown:
            raise ContentError(f"{where}: неизвестные поля {', '.join(sorted(unknown))}")
        out[key] = v
    return out


def load_all(content_dir: Path, known_paths: set[str], team: set[str]) -> dict[str, dict]:
    """{page path: content} for every data/content/*.json; unknown slugs and malformed files stop the build."""
    if not content_dir.exists():
        return {}
    by_slug = {slug_of_path(p): p for p in known_paths if p.startswith("/services/")}
    out: dict[str, dict] = {}
    for file in sorted(content_dir.glob("*.json")):
        path = by_slug.get(file.stem)
        if path is None:
            raise ContentError(f"{file.name}: нет страницы услуги со slug {file.stem!r}")
        try:
            d = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ContentError(f"{file.name}: битый JSON: {exc}") from exc
        validate(d, file.name, known_paths, team)
        out[path] = d
    return out
