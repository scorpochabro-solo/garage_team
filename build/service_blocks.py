# -*- coding: utf-8 -*-
"""Blocks of a detailed service page, rendered from data/content/<slug>.json (format in build/content.py).

Text fields that are plain text (headings, questions, step titles) are escaped here; fields documented as
inline HTML were checked against a tag whitelist at load time and are inserted as they are.
"""
from __future__ import annotations

import html as _html
import re

from . import data as D
from .icons import icon

esc = D.esc


def _block(tag: str, anchor: str, h2: str, inner: str, modifier: str = "") -> str:
    cls = f"svc-block svc-block--{modifier} reveal" if modifier else "svc-block reveal"
    return f"""<section class="{cls}" aria-labelledby="{anchor}">
      <div class="block-title"><span class="tag-num">// {tag}</span><h2 class="h3" id="{anchor}">{esc(h2)}</h2></div>
      {inner}
    </section>"""


def _intro(block: dict) -> str:
    return f'<p class="svc-block__intro">{block["intro"]}</p>' if block.get("intro") else ""


def _note(block: dict) -> str:
    return f'<p class="svc-block__note">{icon("info", "ic--sm")}<span>{block["note"]}</span></p>' if block.get("note") else ""


def lead(content: dict, flags_html: str, image_html: str = "") -> str:
    """image_html: the picture of the original page's description, kept next to the new lead."""
    paragraphs = "".join(f"<p>{p}</p>" for p in content["lead"])
    mod = " intro--img" if image_html else ""
    return f"""<div class="intro{mod} reveal"><div class="intro__text">{paragraphs}<div class="intro__flags">{flags_html}</div></div>{image_html}</div>"""


def symptoms(content: dict) -> str:
    b = content.get("symptoms")
    if not b:
        return ""
    items = "".join(f'<li><span class="svc-signs__ic">{icon("hazard")}</span><span>{x}</span></li>' for x in b["items"])
    return _block("признаки", "b-symptoms", b["h2"], f'{_intro(b)}<ul class="svc-signs">{items}</ul>{_note(b)}')


def includes(content: dict) -> str:
    b = content.get("includes")
    if not b:
        return ""
    items = "".join(f'<li>{icon("check", "ic--sm")}<span>{x}</span></li>' for x in b["items"])
    return _block("состав работ", "b-includes", b["h2"], f'{_intro(b)}<ul class="svc-checks">{items}</ul>{_note(b)}')


def steps(content: dict) -> str:
    b = content.get("steps")
    if not b:
        return ""
    items = "".join(f'<li><h3 class="svc-steps__title">{esc(x["title"])}</h3><p>{x["text"]}</p></li>' for x in b["items"])
    return _block("порядок", "b-steps", b["h2"], f'{_intro(b)}<ol class="svc-steps">{items}</ol>{_note(b)}')


def price_factors(content: dict) -> str:
    b = content.get("price_factors")
    if not b:
        return ""
    items = "".join(f"<li>{x}</li>" for x in b["items"])
    return _block("стоимость", "b-price-factors", b["h2"], f'{_intro(b)}<ul class="svc-factors">{items}</ul>{_note(b)}')


def sections(content: dict) -> str:
    parts = content.get("sections") or []
    if not parts:
        return ""
    body = "".join(f"<h2>{esc(s['h2'])}</h2>{s['html']}" for s in parts)
    return f'<article class="prose prose--article svc-article reveal">{body}</article>'


def faq(content: dict) -> str:
    b = content.get("faq")
    if not b:
        return ""
    items = "".join(
        f'<details class="faq__item"><summary class="faq__q"><span>{esc(x["q"])}</span>{icon("plus", "faq__ic")}</summary>'
        f'<div class="faq__a">{x["a"]}</div></details>'
        for x in b["items"])
    return _block("вопросы", "b-faq", b["h2"], f'<div class="faq">{items}</div>', "faq")


def related(content: dict, is_category: bool) -> str:
    paths = content.get("related") or []
    if not paths:
        return ""
    links = "".join(
        f'<a class="sibling" href="{p}"><span>{esc(D.BY_PATH[p].get("nav_name") or D.BY_PATH[p]["h1"])}</span>{icon("arrow")}</a>'
        for p in paths)
    return f"""<div class="reveal">
      <div class="block-title"><span class="tag-num">// связано</span><h2 class="h3">{"Смежные направления" if is_category else "Часто делают вместе"}</h2></div>
      <div class="sibling-grid">{links}</div>
    </div>"""


def staff(content: dict) -> str:
    names = content.get("staff") or []
    if not names:
        return ""
    team = {t["name"]: t for t in D.SITE.get("team", [])}
    cards = "".join(
        f'<figure class="svc-staff__card"><img src="{D.img(team[n]["photo"])}" alt="{esc(n)}, {esc(team[n]["position"])}" width="96" height="96" loading="lazy" decoding="async">'
        f'<figcaption><b>{esc(n)}</b><span>{esc(team[n]["position"])}</span></figcaption></figure>'
        for n in names)
    return f"""<div class="svc-staff reveal">
      <div class="block-title"><span class="tag-num">// мастер</span><h2 class="h3">Кто этим занимается</h2></div>
      <div class="svc-staff__grid">{cards}</div>
    </div>"""


def plain(fragment: str) -> str:
    """Inline HTML -> text, for structured data."""
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()
