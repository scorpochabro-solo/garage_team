# -*- coding: utf-8 -*-
"""Services index and per-service pages."""
import re

from . import data as D
from . import schema
from . import service_blocks as B
from . import shiny
from . import stena
from .icons import icon, icon_for_href
from .images import RESPONSIVE_WIDTHS, scaled_size
from .layout import (document, page_hero, phone_aside, contact_card, side_index, green_note,
                     reviews_section, request_section)

esc = D.esc
FLAGS = ["Любые марки", "Гарантия до 360 дней*", "Запчасти в наличии и под заказ", "Коммерческая техника до 5,5 т"]
# Cover photos are generated illustrations, not shots of the workshop: the label says so to the visitor.
PHOTO_LABEL = "иллюстрация"
# main column: full width minus gutters below the 1000px breakpoint, up to 1000px next to the sidebar
PHOTO_SIZES = "(max-width: 1000px) calc(100vw - 2.2rem), 1000px"


def _src_exists(url):
    rel = D.img(url).lstrip("/")
    if not rel.startswith("assets/img/"):
        return False
    src_rel = rel[len("assets/img/"):]
    base = D.SRC / "assets" / "img"
    stem = src_rel.rsplit(".", 1)[0]
    return any((base / f"{stem}{ext}").exists() for ext in (".jpg", ".jpeg", ".png", ".webp"))


# the site's phone as the texts write it: «(831) 416-16-77», sometimes with «+7»
_PHONE_TEXT = re.compile(r"(?:\+7\s?)?\(831\)\s?416-16-77")
_TAG = re.compile(r"(<[^>]+>)")


def _link_phones(html_fragment):
    """A phone number written as plain text becomes a tel: link: on a phone it is one tap to call.
    Only text between tags is touched, and nothing inside an existing link."""
    out, in_link = [], 0
    for part in _TAG.split(html_fragment):
        if part.startswith("<"):
            if re.match(r"<a[\s>]", part, re.I):
                in_link += 1
            elif re.match(r"</a\s*>", part, re.I):
                in_link = max(0, in_link - 1)
            out.append(part)
        elif in_link or "416-16-77" not in part:
            out.append(part)
        else:
            out.append(_PHONE_TEXT.sub(lambda m: f'<a class="tel" href="tel:{D.PHONE_TEL}">{m.group(0)}</a>', part))
    return "".join(out)


def _fix_img_src(html_fragment):
    html_fragment = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', lambda m: m.group(0) if _src_exists(m.group(1)) else "", html_fragment)
    return re.sub(r'src="([^"]+)"', lambda m: f'src="{D.img(m.group(1))}"', html_fragment)


# ---------- services index ----------
def _card_text(href):
    """Short text for a direction card: first sentence of the new lead if the page has content, else the old intro."""
    content = D.CONTENT.get(href)
    if not content:
        return D.DESCR.get(href, "")
    first = B.plain(content["lead"][0])
    sentence = re.split(r"(?<=[.!?])\s", first, maxsplit=1)[0]
    return sentence if len(sentence) <= 220 else sentence[:217].rsplit(" ", 1)[0] + "…"


def _directions():
    """The 28 directions for «Стена направлений» (build/stena.py): number, link, name, count, works or short text."""
    items = []
    for i, c in enumerate(D.CATEGORIES):
        n = len(c["subs"])
        count = f'{n} {_plural(n, "услуга", "услуги", "услуг")}' if n else "направление"
        items.append(stena.Direction(i + 1, c["href"], c["name"], count, tuple((s["href"], s["name"]) for s in c["subs"]),
                                     "" if n else _card_text(c["href"])))
    return items


def render_services_index():
    directions = _directions()
    total = len(D.SERVICES)
    lead = (f"{len(D.CATEGORIES)} направлений и {total} видов работ: от компьютерной диагностики до кузовного ремонта и хранения шин. "
            "Сервис и ремонт любых марок, обслуживание коммерческой техники до 5,5 тонн.")
    hero = page_hero(D.PAGE_SEO.get("services", {}).get("h1", "Наши услуги"), [("Главная", "/"), ("Услуги", None)], eyebrow="Автосервис Гараж", lead=lead,
                     aside=phone_aside("Записаться на приём"), mark_icon="maintenance")
    body = f"""{hero}
<section class="section section--tight" aria-label="Список услуг">
  <div class="wrap">
    <div class="filter reveal">
      <div class="filter__input">{icon('search')}<input class="input" type="search" placeholder="Найти услугу: ГРМ, тормоза, кондиционер…" aria-label="Поиск по услугам" data-filter autocomplete="off"></div>
      <span class="filter__count" data-filter-count>{len(D.CATEGORIES)} направлений</span>
    </div>
    {stena.wall(directions)}
    <p class="empty-state">Ничего не нашли. Позвоните нам — подскажем: <a class="accent" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a></p>
    {stena.index(directions)}
  </div>
</section>
<div class="wrap" style="padding-bottom:var(--section-y)">{green_note()}</div>
{request_section("Оставить запрос")}"""
    title, desc = D.page_meta(
        "services", "Услуги автосервиса в Нижнем Новгороде — все направления и цены | Автосервис Гараж",
        f"{len(D.CATEGORIES)} направлений ремонта и обслуживания автомобилей в Нижнем Новгороде: диагностика, двигатель, ходовая, "
        f"тормоза, электрика, кузов, покраска, ТО. Цены и запись по телефону {D.PHONE}.")
    return document(title, desc, "/services.html", body, body_class="page-services")


def _plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


# ---------- single service ----------
# Who answers the page (content field "contact"): the workshop books a repair, the parts shop picks a part.
CONTACT = {
    "service": {"button": "Записаться на приём", "message": "Записаться: {name}",
                "note": "Стоимость работ уточняйте у менеджера — назовём цену после уточнения модели и объёма работ."},
    "shop": {"button": "Заказать звонок", "message": "Подбор запчастей: {name}",
             "note": "Наличие и цену детали уточняйте у менеджера магазина: назовите марку, модель и год выпуска машины, "
                     "а если знаете — номер детали."},
}


def _contact_block(svc, mode, preset):
    """One call to action per page: after the price table, or instead of it with a note when the page has no prices."""
    if svc.get("price_rows"):
        return f"""<div class="cta-inline reveal">
      <button class="btn btn--primary" type="button" data-modal="call" data-preset='{preset}'>{icon('phone')} {esc(mode['button'])}</button>
      <span class="cta-inline__or">или позвонить нам</span>
      <a class="cta-inline__phone" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a>
    </div>"""
    return f"""<div class="cta-inline reveal">
      <span>{esc(mode['note'])}</span>
      <a class="cta-inline__phone" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a>
      <button class="btn btn--primary btn--sm" type="button" data-modal="call" data-preset='{preset}'>{icon('phone')} Заказать звонок</button>
    </div>"""


def _price_block(svc, h2="Цены"):
    rows = svc.get("price_rows") or []
    heads = svc.get("price_heads") or ["Ремонт", "Иномарки", "ВАЗ"]
    if not rows:
        return ""
    trs = []
    for r in rows:
        # the old site left the name empty where the page has a single price row: the row is the page's own work
        name = str(r[0]).strip() or svc.get("nav_name") or svc["h1"]
        cells = [f"<td>{esc(name)}</td>"]
        for i, cell in enumerate(r[1:], 1):
            p = D.fmt_price(cell)
            label = f' data-label="{esc(heads[i])}"' if i < len(heads) else ""
            cells.append(f'<td{label}><span class="price">{esc(p)}</span></td>' if p else f'<td{label}><span class="price price--muted">по запросу</span></td>')
        trs.append("<tr>" + "".join(cells) + "</tr>")
    ths = "".join(f"<th>{esc(h)}</th>" for h in heads)
    return f"""<div class="price-block reveal">
      <div class="block-title"><span class="tag-num">// прайс</span><h2 class="h3">{esc(h2)}</h2></div>
      <table class="price-table"><thead><tr>{ths}</tr></thead><tbody>{"".join(trs)}</tbody></table>
      <div class="price-block__foot"><span>Цены указаны за работу; точную стоимость уточняйте по телефону {esc(D.PHONE)}.</span><button class="btn btn--primary btn--sm" type="button" data-modal="call">{icon('phone')} Записаться</button></div>
    </div>"""


def _photo_block(svc):
    photo = D.PHOTOS.get(svc["path"])
    if not photo:
        return ""
    width, height = scaled_size(photo["src"])
    narrow = RESPONSIVE_WIDTHS["photo"]
    url = f"/assets/img/photo/{photo['slug']}"
    return f"""<figure class="svc-photo reveal">
      <a class="svc-photo__link" href="{url}.webp" data-lightbox="svc" aria-label="Открыть крупнее: {esc(photo['alt'])}">
        <img src="{url}.webp" srcset="{url}-{narrow}.webp {narrow}w, {url}.webp {width}w" sizes="{PHOTO_SIZES}" alt="{esc(photo['alt'])}" width="{width}" height="{height}" fetchpriority="high" decoding="async">
      </a>
      <figcaption class="svc-photo__tag">// {PHOTO_LABEL}</figcaption>
    </figure>"""


def _gallery_block(svc):
    if not svc.get("gallery"):
        return ""
    items = "".join(
        f'<a href="{D.img(g["full"])}" data-lightbox="svc"><img src="{D.img(g["full"])}" alt="{esc(svc["h1"])} — фото работ {i + 1}" width="680" height="450" loading="lazy" decoding="async"></a>'
        for i, g in enumerate(svc["gallery"])
    )
    return f"""<div class="reveal">
      <div class="block-title"><span class="tag-num">// фото</span><h2 class="h3">Фото работ</h2></div>
      <div class="gallery-grid">{items}</div>
    </div>"""


def _siblings_block(svc, cat, is_cat):
    if cat and cat["subs"]:
        title = "Что входит в направление" if is_cat else f"Ещё по направлению «{cat['name']}»"
        links = []
        for s in cat["subs"]:
            current = s["href"] == svc["path"]
            cls = " is-current" if current else ""
            tag = "span" if current else "a"
            href = "" if current else f' href="{s["href"]}"'
            links.append(f'<{tag} class="sibling{cls}"{href}><span>{esc(s["name"])}</span>{icon("check") if current else icon("arrow")}</{tag}>')
        if not is_cat:
            links.append(f'<a class="sibling" href="{cat["href"]}"><span><b>Все услуги направления</b></span>{icon("arrow-up-right")}</a>')
        return f"""<div class="reveal">
      <div class="block-title"><span class="tag-num">// {len(cat['subs']):02d}</span><h2 class="h3">{esc(title)}</h2></div>
      <div class="sibling-grid">{"".join(links)}</div>
    </div>"""
    # category without sub-services: show neighbouring directions
    idx = next((i for i, c in enumerate(D.CATEGORIES) if c["href"] == svc["path"]), 0)
    neighbours = [D.CATEGORIES[(idx + k) % len(D.CATEGORIES)] for k in range(1, 5)]
    links = "".join(f'<a class="sibling" href="{c["href"]}"><span>{esc(c["name"])}</span>{icon("arrow")}</a>' for c in neighbours)
    return f"""<div class="reveal">
      <div class="block-title"><span class="tag-num">// смежные</span><h2 class="h3">Смежные направления</h2></div>
      <div class="sibling-grid">{links}</div>
    </div>"""


def render_service(svc):
    is_cat = svc["path"] in D.CAT_BY_HREF
    cat = D.category_of(svc)
    content = D.CONTENT.get(svc["path"])
    icon_key = icon_for_href(svc["path"] if is_cat else (cat["href"] if cat else svc["path"]))
    descr_html, generated = D.description_for(svc)
    page_name = svc.get("nav_name") or svc["h1"]

    crumbs = [("Главная", "/"), ("Услуги", "/services.html")]
    if cat and not is_cat:
        crumbs.append((cat["name"], cat["href"]))
    crumbs.append((page_name, None))

    if is_cat:
        n = len(cat["subs"]) if cat else 0
        eyebrow = f"Направление · {n} {_plural(n, 'вид работ', 'вида работ', 'видов работ')}" if n else "Направление услуг"
    else:
        eyebrow = cat["name"] if cat else "Услуга"

    is_shop = bool(content) and content.get("contact") == "shop"
    mode = CONTACT["shop" if is_shop else "service"]
    preset = D.esc('{"message":"' + mode["message"].format(name=page_name.replace('"', "'")) + '"}')
    hero = page_hero(svc["h1"], crumbs, eyebrow=eyebrow, aside=phone_aside(mode["button"], preset), mark_icon=icon_key)

    flags = "".join(f'<span class="chip">{icon("check", "ic--sm")} {esc(f)}</span>' for f in FLAGS)
    cta = _contact_block(svc, mode, preset)
    article = ""
    if svc.get("article_html"):
        article = f'<article class="prose prose--article reveal">{_fix_img_src(svc["article_html"])}</article>'

    if content:
        # the new lead replaces the original description text, but its picture stays (unless the page has a cover photo)
        orig_imgs = [] if generated or svc["path"] in D.PHOTOS else [u for u in re.findall(r'<img src="([^"]+)"', descr_html) if _src_exists(u)]
        lead_img = (f'<div class="intro__img"><img src="{D.img(orig_imgs[0])}" alt="{esc(svc["h1"])}" width="600" height="400" loading="lazy"></div>'
                    if orig_imgs else "")
        blocks = [_photo_block(svc), B.lead(content, flags, lead_img), shiny.block(svc), _price_block(svc, content.get("price_h2") or "Цены"), B.price_factors(content),
                  cta, B.symptoms(content), B.includes(content), B.steps(content), B.sections(content), article, B.faq(content),
                  B.staff(content), _gallery_block(svc),
                  # a direction without sub-pages lists its neighbours automatically; the hand-picked «related» list replaces that
                  "" if (is_cat and cat and not cat["subs"] and content.get("related")) else _siblings_block(svc, cat, is_cat),
                  B.related(content, is_cat)]
    else:
        if generated:
            intro = f"""<div class="intro reveal"><div class="intro__text"><p>{esc(descr_html)}</p><div class="intro__flags">{flags}</div></div></div>"""
        else:
            imgs = re.findall(r'<img src="([^"]+)"', descr_html)
            text_html = _fix_img_src(descr_html)
            img_html = f'<div class="intro__img"><img src="{D.img(imgs[0])}" alt="{esc(svc["h1"])}" width="600" height="400" loading="lazy"></div>' if imgs else ""
            intro = f"""<div class="intro{' intro--img' if imgs else ''} reveal"><div class="intro__text">{text_html}<div class="intro__flags">{flags}</div></div>{img_html}</div>"""
        blocks = [_photo_block(svc), intro, _price_block(svc), cta, _gallery_block(svc), article,
                  _siblings_block(svc, cat, is_cat)]
    main = _link_phones("\n".join(x for x in blocks if x))
    side = f"""<aside class="svc-page__side">{side_index(cat['href'] if cat else None)}{contact_card(shop=is_shop)}</aside>"""

    body = f"""{hero}
<section class="wrap svc-page">
  <div class="svc-page__main">{main}</div>
  {side}
</section>
<div class="wrap" style="padding-bottom:var(--section-y)">{green_note()}</div>
{reviews_section(paper=True)}
{request_section("Оставить запрос")}"""

    best = D.price_from(svc)
    if content:
        title, desc = content["title"], content["meta_description"]
    else:
        price_txt = f" Цены от {D.fmt_amount(best)}." if best else ""
        title = f"{svc['h1']} в Нижнем Новгороде — цены, запись | Автосервис Гараж"
        desc = (D.strip_tags(descr_html)[:200] + price_txt + f" Тел. {D.PHONE}.")
    page_url = D.SITE_URL + svc["path"]
    graph = [schema.service(svc["h1"], page_name, desc, page_url, best, provider=schema.shop_ref() if is_shop else None),
             schema.breadcrumbs(crumbs, page_url)]
    if content and content.get("faq"):
        graph.append(schema.faq([(x["q"], B.plain(x["a"])) for x in content["faq"]["items"]]))
    photo = D.PHOTOS.get(svc["path"])
    og_image = f"/assets/img/photo/{photo['slug']}.webp" if photo else None
    return document(title, desc, svc["path"], body, body_class="page-service", og_image=og_image, jsonld=schema.dump(graph))
