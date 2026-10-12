# -*- coding: utf-8 -*-
"""«Что сказал мастер?» — a glossary of the words a client hears from a mechanic, in plain Russian (/slovar/).

The terms, the systems and the service pages they may link to are data in build/slovar_terms.py (the format is in its
docstring); this module checks them and renders the page.

The whole glossary is plain HTML: <dl> per system, <dfn> for the term, an id per term for deep links (/slovar/#grm),
an index from А to Я with cross-references, and JSON-LD DefinedTermSet. Without JavaScript all of it is readable and
the links work; src/assets/js/slovar.js adds the instant search, the system and letter filters, lights up the term of a
deep link and puts the term into the message of the call-back modal. The one line under the answer of «Что стучит?» on
the home page (build/stuk.py) leads here.

The build fails (ValueError from check()) on a link to a page that does not exist or matches FORBIDDEN, a duplicate id,
an unknown system, an empty or overlong definition, a price, or a «see» pointing nowhere.

Wording rules (the owner confirms every text, notes/perk-slovar.md): general automotive knowledge, hedged with
«обычно», «часто», «может»; nothing about what «Гараж» does beyond the links to its service pages; no prices, no terms
of work, no brands; sensitive topics (lambda probe, catalyst, particulate filter, AdBlue) — neutral definitions only.
"""
from __future__ import annotations

import json
import re
from collections import Counter

from . import data as D
from . import schema
from .icons import icon
from .layout import document, page_hero
from .slovar_terms import CATEGORIES, PAGES, TERMS, Category, Term

esc = D.esc

PATH = "/slovar/"
SEO_KEY = "slovar"
TITLE = "Словарь автомеханика: термины автосервиса простыми словами | Гараж"
# defaults; data/page_seo.json («slovar») wins, like for the other pages that are not services
DESCRIPTION = ("Что сказал мастер? Словарь автомеханика простыми словами: ГРМ, ШРУС, сайлентблок, ТНВД, лямбда-зонд — "
               "что это такое и на что жалуются, когда деталь изнашивается.")
H1 = "Что сказал мастер?"
CRUMB = "Словарь автомеханика"
EYEBROW = "Простыми словами"
TERMS_RANGE = (45, 60)
MAX_SENTENCES = 3
MAX_LINKS = 2
MAX_SEE = 3
# never a target of the glossary (sensitive services): a link there fails the build
FORBIDDEN = ("udalenie", "cip-tuning", "ksenon", "tehosmotr")
_ID = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")
_PRICE = re.compile(r"₽|\bруб", re.I)
_SENTENCE_END = re.compile(r"[.!?…](?=\s|$)")


CAT_BY_KEY = {c.key: c for c in CATEGORIES}
BY_ID = {t.id: t for t in TERMS}
# ids the page shell already uses (build/layout.py) — a term or a section must not take them
RESERVED_IDS = {"main", "mobile-menu", "modal-call", "modal-call-title", "modal-login", "modal-login-title", "lightbox",
                "ukazatel", "gl-q", "gl-status", "gl-cats-label", "gl-abc-label", "gl-cta-title", "ukazatel-title"}


# ---------- text helpers ----------
def plural(n: int, one: str, few: str, many: str) -> str:
    """plural(21, 'термин', 'термина', 'терминов') -> 'термин'"""
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    if n == 1:
        return one
    return few if 2 <= n <= 4 else many


def _fold(s: str) -> str:
    """Lower case, ё as е: the key for sorting, letters and comparisons (the search in slovar.js does the same)."""
    return s.lower().replace("ё", "е")


def initial(s: str) -> str:
    """The index letter of a word: a Cyrillic letter, or 'latin' for ABS, EGR, VIN…"""
    ch = _fold(s.strip())[:1]
    return ch if "а" <= ch <= "я" else "latin"


def sentences(text: str) -> int:
    return len(_SENTENCE_END.findall(text.strip()))


def _link(key: str) -> tuple[str, str]:
    """(path, page name) of a service page; a missing or forbidden page stops the build."""
    path = PAGES.get(key)
    if path is None:
        raise ValueError(f"slovar: неизвестная страница {key!r}")
    svc = D.BY_PATH.get(path)
    if svc is None:
        raise ValueError(f"slovar: нет страницы услуги {path} ({key})")
    if any(bad in path for bad in FORBIDDEN):
        raise ValueError(f"slovar: словарь не должен вести на {path}")
    return path, svc.get("nav_name") or svc["h1"]


def check(terms: tuple[Term, ...] = TERMS, categories: tuple[Category, ...] = CATEGORIES) -> None:
    """Everything the page relies on; raises ValueError with the term and the reason."""
    lo, hi = TERMS_RANGE
    if not lo <= len(terms) <= hi:
        raise ValueError(f"slovar: терминов {len(terms)}, нужно {lo}–{hi}")
    cat_keys = [c.key for c in categories]
    if len(set(cat_keys)) != len(cat_keys):
        raise ValueError("slovar: разделы повторяются")
    for c in categories:
        if not _ID.match(c.key) or c.key in RESERVED_IDS:
            raise ValueError(f"slovar: плохой id раздела {c.key!r}")
        icon(c.icon)                                  # raises on an unknown icon
        if not c.name.strip() or not c.lead.strip():
            raise ValueError(f"slovar: у раздела {c.key} нет названия или подводки")
    ids = [t.id for t in terms]
    dup = {i for i, n in Counter(ids).items() if n > 1} | (set(ids) & set(cat_keys))
    if dup:
        raise ValueError(f"slovar: id повторяются: {', '.join(sorted(dup))}")
    names = {_fold(t.name): t.id for t in terms}
    if len(names) != len(terms):
        raise ValueError("slovar: названия терминов повторяются")
    for t in terms:
        where = f"slovar: {t.id}"
        if not _ID.match(t.id) or t.id in RESERVED_IDS:
            raise ValueError(f"{where}: id должен быть латиницей через дефис и не занятым страницей")
        if t.cat not in cat_keys:
            raise ValueError(f"{where}: неизвестный раздел {t.cat!r}")
        if not t.name.strip() or not t.text.strip():
            raise ValueError(f"{where}: пустое название или определение")
        if not 1 <= sentences(t.text) <= MAX_SENTENCES or not t.text.strip().endswith((".", "!", "?", "…")):
            raise ValueError(f"{where}: определение — от 1 до {MAX_SENTENCES} законченных предложений")
        if t.wear and not t.wear.strip().endswith((".", "!", "?", "…")):
            raise ValueError(f"{where}: признаки износа — законченные предложения")
        for field in (t.name, t.text, *([t.wear] if t.wear else []), *t.aka, *t.refs):
            if _PRICE.search(field):
                raise ValueError(f"{where}: в словаре не пишем цены")
            if not field or field != field.strip():
                raise ValueError(f"{where}: пустое название или лишние пробелы")
        other = [_fold(x) for x in (*t.aka, *t.refs)]
        if len(set(other)) != len(other) or _fold(t.name) in other:
            raise ValueError(f"{where}: другие названия повторяются")
        for x in other:
            if x in names and names[x] != t.id:
                raise ValueError(f"{where}: «{x}» — название другого термина")
        if len(t.links) > MAX_LINKS or len(set(t.links)) != len(t.links):
            raise ValueError(f"{where}: ссылок на услуги не больше {MAX_LINKS}, без повторов")
        for key in t.links:
            _link(key)
        if len(t.see) > MAX_SEE or len(set(t.see)) != len(t.see):
            raise ValueError(f"{where}: «см. также» — не больше {MAX_SEE}, без повторов")
        for s in t.see:
            if s == t.id or s not in ids:
                raise ValueError(f"{where}: «см. также» ведёт на {s!r}")
    for c in categories:
        if not any(t.cat == c.key for t in terms):
            raise ValueError(f"slovar: в разделе {c.key} нет терминов")


# ---------- the index: terms and cross-references from А to Я ----------
def _sort_key(s: str) -> tuple[int, str]:
    f = _fold(s)
    return (1 if initial(s) == "latin" else 0, f)


def _is_near(alias: str, name: str) -> bool:
    """A cross-reference that would stand next to its own term in the index adds nothing («рейка» → «Рулевая рейка»)."""
    a, n = _fold(alias), _fold(name)
    return a in n or n in a or a[:4] == n[:4]


def index_entries(terms: tuple[Term, ...] = TERMS) -> list[tuple[str, str, Term | None, Term]]:
    """[(letter, label, None, term) for a term | (letter, alias, term, term) for a cross-reference], sorted А…Я, then A–Z."""
    rows = []
    for t in terms:
        rows.append((initial(t.name), t.name, None, t))
        for alias in (*t.aka, *t.refs):
            if not _is_near(alias, t.name):
                rows.append((initial(alias), alias, t, t))
    return sorted(rows, key=lambda r: _sort_key(r[1]))


def letters(terms: tuple[Term, ...] = TERMS) -> list[str]:
    """Index letters in order: the Cyrillic ones that begin a term, a synonym or a cross-reference, then 'latin'."""
    found = {initial(x) for t in terms for x in (t.name, *t.aka, *t.refs)}
    cyr = sorted(x for x in found if x != "latin")
    return cyr + (["latin"] if "latin" in found else [])


def _letter_label(letter: str) -> str:
    return "A–Z" if letter == "latin" else letter.upper()


# ---------- markup ----------
_S = 'fill="none" stroke-linecap="round" stroke-linejoin="round"'
# the neon sign of the hero: a speech bubble and a question mark bent from one mint tube, drawn three times
# (halo, glow, bright core) instead of a blur filter, like the «GARAGE TEAM» sign of «Свет ламп»
_TUBE = ("M40 14H180a26 26 0 0 1 26 26v74a26 26 0 0 1-26 26H92L44 176l14-36H40a26 26 0 0 1-26-26V40a26 26 0 0 1 26-26z"
         "M88 64c0-16 10.5-25 23-25s23 8.5 23 21-10 18-17 22.5c-4.5 3-6 6.5-6 12.5v4")


def _sign() -> str:
    return f"""<div class="gl-sign" aria-hidden="true">
      <span class="gl-sign__spill"></span>
      <svg class="gl-sign__svg" viewBox="0 0 220 190" focusable="false">
        <defs><path id="gl-tube" d="{_TUBE}"/><path id="gl-dot" d="M111 117.5v.5"/></defs>
        <g class="gl-sign__glass" {_S} stroke="rgba(170,255,228,.16)" stroke-width="3"><use href="#gl-tube"/><use href="#gl-dot"/></g>
        <g class="gl-sign__lit" {_S}>
          <use href="#gl-tube" stroke="rgba(52,232,184,.13)" stroke-width="16"/><use href="#gl-dot" stroke="rgba(52,232,184,.13)" stroke-width="18"/>
          <use href="#gl-tube" stroke="rgba(64,240,192,.38)" stroke-width="7"/><use href="#gl-dot" stroke="rgba(64,240,192,.38)" stroke-width="10"/>
          <use href="#gl-tube" stroke="#8dffe0" stroke-width="2.8"/><use href="#gl-dot" stroke="#8dffe0" stroke-width="6.5"/>
          <use href="#gl-tube" stroke="#f4fffb" stroke-width="1.1"/><use href="#gl-dot" stroke="#f4fffb" stroke-width="3"/>
        </g>
        <path class="gl-sign__clip" d="M70 11v6M150 11v6M203 77h6M11 77h6"/>
      </svg>
    </div>"""


def _num(ci: int, ti: int | None = None) -> str:
    return f"{ci + 1:02d}" if ti is None else f"{ci + 1:02d}.{ti + 1:02d}"


def _term(t: Term, ci: int, ti: int) -> str:
    cat = CAT_BY_KEY[t.cat]
    marks = " ".join(sorted({initial(x) for x in (t.name, *t.aka, *t.refs)}))
    aka = ""
    if t.aka:
        items = ", ".join(f'<span data-f="n">{esc(a)}</span>' for a in t.aka)
        aka = f'<span class="gl-term__aka"><span class="gl-term__label">ещё говорят</span> {items}</span>'
    wear = (f'<dd class="gl-term__wear"><span class="gl-term__label">Признаки износа</span> <span data-f="t">{esc(t.wear)}</span></dd>'
            if t.wear else "")
    foot = ""
    if t.links:
        links = "".join(f'<a class="gl-go" href="{p}">{esc(n)}{icon("arrow-up-right")}</a>' for p, n in map(_link, t.links))
        foot = f'<dd class="gl-term__go"><span class="gl-term__label">Услуги</span> {links}</dd>'
    see = ""
    if t.see:
        refs = "".join(f'<a class="gl-see" href="#{s}">{esc(BY_ID[s].name)}</a>' for s in t.see)
        see = f'<dd class="gl-term__see"><span class="gl-term__label">См. также</span> {refs}</dd>'
    refs_attr = f' data-refs="{esc(json.dumps(list(t.refs), ensure_ascii=False))}"' if t.refs else ""
    return f"""<div class="gl-term" id="{t.id}" data-cat="{cat.key}" data-l="{marks}"{refs_attr} tabindex="-1">
          <dt class="gl-term__head"><span class="gl-term__n" aria-hidden="true">{_num(ci, ti)}</span><dfn class="gl-term__name" data-f="n">{esc(t.name)}</dfn>{aka}</dt>
          <dd class="gl-term__def"><p data-f="t">{esc(t.text)}</p></dd>
          {wear}{foot}{see}
        </div>"""


def _section(ci: int, c: Category) -> str:
    terms = [t for t in TERMS if t.cat == c.key]
    n = len(terms)
    entries = "\n        ".join(_term(t, ci, i) for i, t in enumerate(terms))
    return f"""<section class="gl-cat" id="{c.key}" aria-labelledby="{c.key}-title" data-gl-section="{c.key}">
      <header class="gl-cat__head">
        <span class="gl-cat__num" aria-hidden="true">{_num(ci)}</span>
        <div class="gl-cat__title">
          <span class="gl-cat__ic">{icon(c.icon)}</span>
          <h2 class="gl-cat__h" id="{c.key}-title">{esc(c.name)}</h2>
          <span class="gl-cat__count" data-gl-count data-total="{n}">{n} {plural(n, "термин", "термина", "терминов")}</span>
        </div>
        <p class="gl-cat__lead">{esc(c.lead)}</p>
      </header>
      <dl class="gl-list">
        {entries}
      </dl>
    </section>"""


def _cta_button(cls: str, label: str, message: str, kind: str) -> str:
    """The call-back modal with a ready message (core.js reads data-preset); without JS the link opens the request page.
    slovar.js rewrites the message with the term the visitor is looking at (kind 'term') or the word that was not found
    ('query')."""
    preset = esc(json.dumps({"message": message}, ensure_ascii=False))
    return (f'<a class="btn btn--primary {cls}" href="/call/request/" data-modal="call" data-preset="{preset}" '
            f'data-gl-cta="{kind}">{icon("phone")} <span>{esc(label)}</span></a>')


MESSAGE = "Хочу записаться на диагностику (со страницы «Что сказал мастер?» — словарь автомеханика)."


def _rail() -> str:
    total = len(TERMS)
    cats = [f'<button class="gl-chip" type="button" aria-pressed="true" data-cat="" tabindex="0">'
            f'<span class="gl-chip__i gl-chip__i--all" aria-hidden="true"></span><span class="gl-chip__t">Все</span>'
            f'<span class="gl-chip__n" data-n>{total}</span></button>']
    for i, c in enumerate(CATEGORIES):
        n = sum(1 for t in TERMS if t.cat == c.key)
        cats.append(f'<button class="gl-chip" type="button" aria-pressed="false" data-cat="{c.key}" tabindex="-1">'
                    f'<span class="gl-chip__i" aria-hidden="true">{_num(i)}</span><span class="gl-chip__t">{esc(c.name)}</span>'
                    f'<span class="gl-chip__n" data-n>{n}</span></button>')
    abc = []
    for i, L in enumerate(letters()):
        label = ' aria-label="Латиница: ABS, EGR, VIN и другие"' if L == "latin" else ""
        abc.append(f'<button class="gl-abc__b" type="button" aria-pressed="false" data-letter="{L}"{label} '
                   f'tabindex="{0 if i == 0 else -1}">{_letter_label(L)}</button>')
    words = f'{total} {plural(total, "термин", "термина", "терминов")}'
    return f"""<div class="gl__rail">
      <div class="gl-bar">
        <form class="gl-search" role="search" action="{PATH}" method="get" data-gl-form>
          <label class="sr-only" for="gl-q">Поиск по словарю</label>
          <span class="gl-search__ic">{icon("search")}</span>
          <input class="input gl-search__input" id="gl-q" name="q" type="search" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="search" placeholder="Например, «граната»" aria-describedby="gl-status" data-gl-q>
          <button class="gl-search__clear" type="button" data-gl-clear hidden>{icon("close")}<span class="sr-only">Очистить поиск</span></button>
        </form>
        <p class="gl-status" id="gl-status" data-gl-status>{words}</p>
      </div>
      <div class="gl-side">
        <div class="gl-group">
          <p class="gl-group__label" id="gl-cats-label">Системы</p>
          <div class="gl-chips" role="toolbar" aria-labelledby="gl-cats-label" data-gl-cats>{"".join(cats)}</div>
        </div>
        <div class="gl-group gl-group--abc">
          <p class="gl-group__label" id="gl-abc-label">По алфавиту</p>
          <div class="gl-abc" role="toolbar" aria-labelledby="gl-abc-label" data-gl-abc>{"".join(abc)}</div>
        </div>
        <div class="gl-mini">
          <p class="gl-mini__label">Нашли?</p>
          {_cta_button("btn--sm gl-mini__btn", "Записаться на диагностику", MESSAGE, "term")}
          <p class="gl-cta-note" data-gl-cta-note hidden></p>
        </div>
      </div>
      <p class="sr-only" role="status" aria-live="polite" aria-atomic="true" data-gl-live></p>
    </div>"""


def _empty() -> str:
    return f"""<div class="gl-empty" data-gl-empty hidden>
      <p class="gl-empty__mark" aria-hidden="true">?</p>
      <p class="gl-empty__title">Такого слова в словаре пока нет</p>
      <p class="gl-empty__text">Проверьте, нет ли опечатки, или попробуйте другое название — например, «граната» вместо «ШРУС». Если это слово сказал мастер, закажите звонок: ваш вопрос уже будет в комментарии.</p>
      <div class="gl-empty__actions">
        <button class="btn btn--ghost" type="button" data-gl-reset>{icon("close")} Сбросить поиск</button>
        {_cta_button("", "Заказать звонок", MESSAGE, "query")}
      </div>
    </div>"""


def _index() -> str:
    groups: dict[str, list[str]] = {}
    for letter, label, target, term in index_entries():
        if target is None:
            item = f'<li class="gl-idx__term"><a href="#{term.id}">{esc(label)}</a></li>'
        else:
            item = (f'<li class="gl-idx__ref"><a href="#{term.id}"><span>{esc(label)}</span>'
                    f'<span class="gl-idx__to" aria-hidden="true">→</span><span class="sr-only">, смотрите</span> '
                    f'<span class="gl-idx__name">{esc(term.name)}</span></a></li>')
        groups.setdefault(letter, []).append(item)
    order = letters()
    cols = "".join(f'<div class="gl-idx__group"><h3 class="gl-idx__letter">{_letter_label(L)}</h3><ul>{"".join(groups[L])}</ul></div>'
                   for L in order if L in groups)
    return f"""<section class="section gl-idx" id="ukazatel" aria-labelledby="ukazatel-title">
  <div class="wrap">
    <div class="gl-idx__head">
      <p class="eyebrow">Указатель</p>
      <h2 class="h2 gl-idx__title" id="ukazatel-title">Все слова от А до Я</h2>
      <p class="gl-idx__lead">Жирным — термины словаря, со стрелкой — другие названия: они ведут к нужному термину.</p>
    </div>
    <nav class="gl-idx__cols" aria-label="Указатель от А до Я">{cols}</nav>
  </div>
</section>"""


def _cta() -> str:
    return f"""<section class="gl-cta" aria-labelledby="gl-cta-title">
  <div class="wrap gl-cta__in">
    <div class="gl-cta__copy">
      <p class="eyebrow">Нашли?</p>
      <h2 class="h2 gl-cta__title" id="gl-cta-title">Запишитесь на&nbsp;диагностику</h2>
      <p class="gl-cta__text">Хотите проверить узел, о котором говорил мастер? Закажите звонок — или позвоните сами.</p>
    </div>
    <div class="gl-cta__actions">
      {_cta_button("btn--lg", "Записаться на диагностику", MESSAGE, "term")}
      <a class="gl-cta__phone" href="tel:{D.PHONE_TEL}"><small>или позвоните</small>{esc(D.PHONE)}</a>
      <p class="gl-cta-note" data-gl-cta-note hidden></p>
    </div>
  </div>
</section>"""


def jsonld(description: str = DESCRIPTION) -> str:
    url = D.SITE_URL + PATH
    set_id = url + "#slovar"
    terms = []
    for t in TERMS:
        node = {"@type": "DefinedTerm", "@id": f"{url}#{t.id}", "name": t.name, "description": t.text, "url": f"{url}#{t.id}"}
        if t.aka:
            node["alternateName"] = list(t.aka)
        terms.append(node)
    term_set = {"@type": "DefinedTermSet", "@id": set_id, "name": "Словарь автомеханика", "description": description,
                "url": url, "inLanguage": "ru", "publisher": schema.org_ref(), "hasDefinedTerm": terms}
    return schema.dump([term_set, schema.breadcrumbs([("Главная", "/"), (CRUMB, None)], url)])


_ID_ATTR = re.compile(r'\sid="([^"]+)"')


def render() -> str:
    check()
    seo = D.PAGE_SEO.get(SEO_KEY, {})
    title, description = D.page_meta(SEO_KEY, TITLE, DESCRIPTION)
    total = len(TERMS)
    lead = (f"{total} {plural(total, 'слово', 'слова', 'слов')}, которые слышат в автосервисе, — простыми словами: что это "
            "такое, зачем оно нужно и на что жалуются, когда деталь изнашивается.")
    hero = page_hero(seo.get("h1", H1), [("Главная", "/"), (CRUMB, None)], eyebrow=EYEBROW, lead=esc(lead), aside=_sign())
    sections = "\n    ".join(_section(i, c) for i, c in enumerate(CATEGORIES))
    body = f"""{hero}
<section class="gl-sec" aria-label="{esc(CRUMB)}">
  <div class="wrap gl" data-gl>
    {_rail()}
    <div class="gl__list">
    {_empty()}
    {sections}
    <button class="gl-more" type="button" data-gl-more hidden></button>
    </div>
  </div>
</section>
{_index()}
{_cta()}"""
    html = document(title, description, PATH, body, body_class="page-slovar", jsonld=jsonld(description))
    dup = sorted(i for i, n in Counter(_ID_ATTR.findall(html)).items() if n > 1)
    if dup:
        raise ValueError(f"slovar: на странице повторяются id: {', '.join(dup)}")
    return html
