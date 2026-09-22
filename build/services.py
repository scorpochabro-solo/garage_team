# -*- coding: utf-8 -*-
"""Services index and per-service pages."""
import re

from . import data as D
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


def _fix_img_src(html_fragment):
    html_fragment = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', lambda m: m.group(0) if _src_exists(m.group(1)) else "", html_fragment)
    return re.sub(r'src="([^"]+)"', lambda m: f'src="{D.img(m.group(1))}"', html_fragment)


# ---------- services index ----------
def render_services_index():
    cards = []
    for i, c in enumerate(D.CATEGORIES):
        subs = "".join(f'<a href="{s["href"]}">{esc(s["name"])}</a>' for s in c["subs"])
        count = f'{len(c["subs"])} {_plural(len(c["subs"]), "услуга", "услуги", "услуг")}' if c["subs"] else "направление"
        cards.append(f"""<article class="cat-card reveal" data-title="{esc(c['name'])}" style="--d:{(i % 6) * 40}ms">
      <a class="cat-card__head" href="{c['href']}">
        <span class="cat-card__icon">{icon(icon_for_href(c['href']))}</span>
        <span><span class="cat-card__title">{esc(c['name'])}</span><span class="cat-card__count">{i + 1:02d} · {count}</span></span>
      </a>
      {f'<div class="cat-card__subs">{subs}</div>' if subs else f'<p class="muted" style="font-size:.9rem">{esc(D.DESCR.get(c["href"], ""))}</p>'}
      <a class="link-arrow link-arrow--inline cat-card__more" href="{c['href']}">Подробнее {icon('arrow')}</a>
    </article>""")
    total = len(D.SERVICES)
    lead = (f"{len(D.CATEGORIES)} направлений и {total} видов работ: от компьютерной диагностики до кузовного ремонта и хранения шин. "
            "Сервис и ремонт любых марок, обслуживание коммерческой техники до 5,5 тонн.")
    hero = page_hero("Наши услуги", [("Главная", "/"), ("Наши услуги", None)], eyebrow="Автосервис Гараж", lead=lead,
                     aside=phone_aside("Записаться на приём"), mark_icon="maintenance")
    body = f"""{hero}
<section class="section section--tight" aria-label="Список услуг">
  <div class="wrap">
    <div class="filter reveal">
      <div class="filter__input">{icon('search')}<input class="input" type="search" placeholder="Найти услугу: ГРМ, тормоза, кондиционер…" aria-label="Поиск по услугам" data-filter autocomplete="off"></div>
      <span class="filter__count" data-filter-count>{len(D.CATEGORIES)} направлений</span>
    </div>
    <div class="cat-grid">{"".join(cards)}</div>
    <p class="empty-state">Ничего не нашли. Позвоните нам — подскажем: <a class="accent" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a></p>
  </div>
</section>
<div class="wrap" style="padding-bottom:var(--section-y)">{green_note()}</div>
{request_section("Оставить запрос")}"""
    title = "Услуги автосервиса в Нижнем Новгороде — все направления и цены | Автосервис Гараж"
    desc = (f"{len(D.CATEGORIES)} направлений ремонта и обслуживания автомобилей в Нижнем Новгороде: диагностика, двигатель, ходовая, "
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
def _price_block(svc):
    rows = svc.get("price_rows") or []
    heads = svc.get("price_heads") or ["Ремонт", "Иномарки", "ВАЗ"]
    if not rows:
        return f"""<div class="cta-inline reveal">
      <span>Стоимость работ уточняйте у менеджера — назовём цену после уточнения модели и объёма работ.</span>
      <a class="cta-inline__phone" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a>
      <button class="btn btn--primary btn--sm" type="button" data-modal="call">{icon('phone')} Заказать звонок</button>
    </div>"""
    trs = []
    for r in rows:
        cells = [f"<td>{esc(r[0])}</td>"]
        for cell in r[1:]:
            p = D.fmt_price(cell)
            cells.append(f'<td><span class="price">{esc(p)}</span></td>' if p else '<td><span class="price price--muted">по запросу</span></td>')
        trs.append("<tr>" + "".join(cells) + "</tr>")
    ths = "".join(f"<th>{esc(h)}</th>" for h in heads)
    return f"""<div class="price-block reveal">
      <div class="block-title"><span class="tag-num">// прайс</span><h2 class="h3">Цены</h2></div>
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
    icon_key = icon_for_href(svc["path"] if is_cat else (cat["href"] if cat else svc["path"]))
    descr_html, generated = D.description_for(svc)

    crumbs = [("Главная", "/"), ("Услуги", "/services.html")]
    if cat and not is_cat:
        crumbs.append((cat["name"], cat["href"]))
    crumbs.append((svc["h1"], None))

    if is_cat:
        n = len(cat["subs"]) if cat else 0
        eyebrow = f"Направление · {n} {_plural(n, 'вид работ', 'вида работ', 'видов работ')}" if n else "Направление услуг"
    else:
        eyebrow = cat["name"] if cat else "Услуга"

    preset = D.esc('{"message":"Записаться: ' + svc["h1"].replace('"', "'") + '"}')
    hero = page_hero(svc["h1"], crumbs, eyebrow=eyebrow, aside=phone_aside("Записаться на приём", preset), mark_icon=icon_key)

    # intro
    flags = "".join(f'<span class="chip">{icon("check", "ic--sm")} {esc(f)}</span>' for f in FLAGS)
    if generated:
        intro = f"""<div class="intro reveal"><div class="intro__text"><p>{esc(descr_html)}</p><div class="intro__flags">{flags}</div></div></div>"""
    else:
        imgs = re.findall(r'<img src="([^"]+)"', descr_html)
        text_html = _fix_img_src(descr_html)
        img_html = f'<div class="intro__img"><img src="{D.img(imgs[0])}" alt="{esc(svc["h1"])}" width="600" height="400" loading="lazy"></div>' if imgs else ""
        intro = f"""<div class="intro{' intro--img' if imgs else ''} reveal"><div class="intro__text">{text_html}<div class="intro__flags">{flags}</div></div>{img_html}</div>"""

    cta = f"""<div class="cta-inline reveal">
      <button class="btn btn--primary" type="button" data-modal="call" data-preset='{preset}'>{icon('phone')} Записаться на приём</button>
      <span class="cta-inline__or">или позвонить нам</span>
      <a class="cta-inline__phone" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a>
    </div>"""

    article = ""
    if svc.get("article_html"):
        article = f'<article class="prose prose--article reveal">{_fix_img_src(svc["article_html"])}</article>'

    # без прайса блок цены сам является призывом позвонить, второй такой же ниже не нужен
    blocks = [_photo_block(svc), intro, _price_block(svc), cta if svc.get("price_rows") else "", _gallery_block(svc), article,
              _siblings_block(svc, cat, is_cat)]
    main = "\n".join(x for x in blocks if x)
    side = f"""<aside class="svc-page__side">{side_index(cat['href'] if cat else None)}{contact_card()}</aside>"""

    body = f"""{hero}
<section class="wrap svc-page">
  <div class="svc-page__main">{main}</div>
  {side}
</section>
<div class="wrap" style="padding-bottom:var(--section-y)">{green_note()}</div>
{reviews_section(paper=True)}
{request_section("Оставить запрос")}"""

    best = D.price_from(svc)
    price_txt = f" Цены от {D.fmt_amount(best)}." if best else ""
    title = f"{svc['h1']} в Нижнем Новгороде — цены, запись | Автосервис Гараж"
    desc = (D.strip_tags(descr_html)[:200] + price_txt + f" Тел. {D.PHONE}.")
    return document(title, desc, svc["path"], body, body_class="page-service")
