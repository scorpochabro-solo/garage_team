# -*- coding: utf-8 -*-
"""Homepage renderer."""
import json

from . import data as D
from . import otkryto, schema
from .icons import icon, icon_for_href
from .layout import document, request_section, reviews_section, green_note, slider_nav
from .pribory import pribory_section
from .stuk import stuk_section
from .zima import zima_section

esc = D.esc
S = D.SITE

# Тексты первого экрана. Каждая строка заголовка — отдельная строка на экране; зелёным красятся строки из HERO_ACCENT_FROM и ниже.
HERO_EYEBROW = "Complete car care · since 2011"
HERO_LINES = ["Автосервис", "в Нижнем", "Новгороде"]
HERO_ACCENT_FROM = 1
HERO_SUB = ("Ремонт и обслуживание автомобилей любых марок с 2011 года. Коммерческая техника до 5,5 т, "
            "запчасти в наличии и под заказ, гарантия на работы до 360 дней*.")


def hero():
    # a dimmed background: on a phone the 800px copy looks the same and is the first-screen image three times lighter
    photo = D.img("/data/images/gallerymain/BV5A0791.jpg")
    title = "".join(
        f'<span class="hero__line{" hero__line--accent" if i >= HERO_ACCENT_FROM else ""}"><span style="--i:{i}">{esc(t)}</span></span>'
        for i, t in enumerate(HERO_LINES)
    )
    promo_text = S["promo_text"].replace("<br>", " ")
    facts = f"""<ul class="hero__facts" aria-label="Факты о компании">
      <li><b>{D.FOUNDED}</b><span>год основания компании</span></li>
      <li><b><span data-countup="{len(D.CATEGORIES)}">{len(D.CATEGORIES)}</span></b><span>направлений услуг</span></li>
      <li><b><span data-countup="360">360</span> <i>дн.</i></b><span>гарантия на работы*</span></li>
      <li><b>5,5 <i>т</i></b><span>коммерческая техника</span></li>
    </ul>"""
    return f"""<section class="hero" id="top" aria-labelledby="hero-title">
  <div class="hero__bg" aria-hidden="true">
    <picture><source media="(max-width: 640px)" srcset="{photo.replace('.webp', '-800.webp')}"><img class="hero__photo" src="{photo}" alt="" width="1600" height="1067" fetchpriority="high" decoding="async"></picture>
    <div class="hero__grid grid-bg"></div>
    <div class="hero__veil"></div>
    <div class="hero__glow"></div>
  </div>
  <div class="wrap hero__in">
    <div class="hero__copy">
      <p class="eyebrow" lang="en">{esc(HERO_EYEBROW)}</p>
      <h1 class="h-giant hero__title" id="hero-title">{title}</h1>
      <p class="lead hero__sub">{esc(HERO_SUB)}</p>
      <div class="hero__actions">
        <a class="btn btn--primary btn--lg" href="#request">{icon('check')} Оставить заявку</a>
        <button class="btn btn--ghost btn--lg" type="button" data-modal="call" style="--btn-bg:#070807">{icon('phone')} Заказать звонок</button>
        <a class="hero__phone" href="tel:{D.PHONE_TEL}"><b>{esc(D.PHONE)}</b><span>Пн–Пт 9–19 · Сб 9–17</span></a>
      </div>
    </div>
    <aside class="hero__aside">
      <div class="promo-ticket corner reveal">
        <span class="mono accent">Акция</span>
        <p class="promo-ticket__text">{promo_text}</p>
        <a class="btn btn--white btn--sm" href="/registration/">{esc(S['promo_btn'])}</a>
        <span class="promo-ticket__num" aria-hidden="true">-5%</span>
      </div>
      {facts}
    </aside>
  </div>
  <div class="hero__scroll" aria-hidden="true"><span class="mono">листайте</span><i></i></div>
</section>"""


def ticker():
    items = "".join(f'<span class="ticker__item">{esc(c["name"])}</span>' for c in D.CATEGORIES)
    return f'<div class="ticker" aria-hidden="true"><div class="ticker__track">{items}{items}</div></div>'


def _hotspot_payload():
    payload = {}
    for i, h in enumerate(D.HOTSPOTS):
        svc = D.BY_PATH.get(h["href"])
        cat = D.category_of(svc) if svc else None
        best = D.price_from(svc) if svc else None
        payload[h["key"]] = {
            "name": h["name"],
            "cat": (cat["name"] if cat and cat["href"] != h["href"] else "Направление услуг"),
            "blurb": h["blurb"],
            "price": f"от {D.fmt_amount(best)}" if best else "",
            "price_note": "по прайсу, иномарки",
            "href": D.BASE + h["href"],
            "icon": h["icon"],
            "n": i + 1,
        }
    return payload


def services_map():
    left = [h for h in D.HOTSPOTS if h["side"] == "left"]
    right = [h for h in D.HOTSPOTS if h["side"] == "right"]
    bottom = [h for h in D.HOTSPOTS if h["side"] == "bottom"]
    order = {h["key"]: i + 1 for i, h in enumerate(D.HOTSPOTS)}

    def item(h):
        return (f'<a class="svc-item" href="{h["href"]}" data-key="{h["key"]}" data-side="{h["side"]}">'
                f'<span class="svc-item__n">{order[h["key"]]:02d}</span>'
                f'<span class="svc-item__icon">{icon(h["icon"])}</span><span>{esc(h["name"])}</span></a>')

    hotspots = "".join(
        f'<button class="hotspot" type="button" style="--x:{h["x"]}%;--y:{h["y"]}%;--d:{i * 60}ms" data-key="{h["key"]}" aria-label="{esc(h["name"])}">'
        f'<span class="hotspot__ring"></span><span class="hotspot__dot"></span><span class="hotspot__label">{esc(h["name"])}</span></button>'
        for i, h in enumerate(D.HOTSPOTS)
    )
    total_works = len(D.SERVICES)
    payload = json.dumps(_hotspot_payload(), ensure_ascii=False).replace("</", "<\\/")
    return f"""<section class="section svc" id="services" aria-labelledby="services-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// 01 — Что мы делаем</p><h2 class="h2 sec-head__title" id="services-title">Наши услуги</h2></div>
      <p class="sec-head__aside">Наведите на услугу или на точку на автомобиле — покажем, что входит в работу и с какой суммы начинается прайс. Всего {len(D.CATEGORIES)} направлений и {total_works} видов работ.</p>
    </div>
    <div class="svc-stage reveal" data-svc-stage>
      <div class="svc-col svc-col--left">{"".join(item(h) for h in left)}</div>
      <div class="svc-center">
        <div class="car-stage">
          <div class="car-stage__ring" aria-hidden="true"><i></i></div>
          <div class="car-stage__floor" aria-hidden="true"></div>
          <div class="car">
            <img class="car__img" src="/assets/img/car.webp" width="1405" height="980" alt="Автомобиль — интерактивная схема услуг автосервиса Гараж" loading="lazy" decoding="async">
            <img class="car__xray" src="/assets/img/car-xray.webp" width="1405" height="980" alt="" aria-hidden="true" loading="lazy" decoding="async">
            <div class="car__scan" aria-hidden="true"></div>
          </div>
          {hotspots}
        </div>
        <div class="svc-readout-box">
          <div class="svc-readout" data-readout aria-live="polite">
            <div class="svc-readout__icon">{icon('info')}</div>
            <div class="svc-readout__hint">Наведите на услугу или проведите курсором по автомобилю: прицел найдёт узел, здесь появятся описание и стартовая цена. На телефоне нажмите на точку.</div>
          </div>
        </div>
      </div>
      <div class="svc-col svc-col--right">{"".join(item(h) for h in right)}</div>
      <div class="svc-bottom">{"".join(item(h) for h in bottom)}</div>
      <svg class="svc-lines" aria-hidden="true"></svg>
    </div>
    <div class="svc-cta reveal">
      <a class="btn btn--primary btn--lg" href="/services.html">Все {len(D.CATEGORIES)} направлений услуг {icon('arrow')}</a>
      <span class="svc-cta__note">{total_works} видов работ · цены на страницах услуг</span>
    </div>
  </div>
  <script type="application/json" id="svc-data">{payload}</script>
</section>"""


def advantages():
    items = S["advantages"]
    big_idx = next((i for i, t in enumerate(items) if "Гарантия" in t), len(items) - 1)
    cells = [f"""<div class="adv__item adv__item--big reveal">
      <span class="adv__num">// 01</span>
      <p class="adv__text">{esc(items[big_idx])}</p>
      <span class="adv__big" aria-hidden="true">360</span>
    </div>"""]
    n = 2
    for i, t in enumerate(items):
        if i == big_idx:
            continue
        cells.append(f'<div class="adv__item reveal" style="--d:{(n - 1) * 60}ms"><span class="adv__num">// {n:02d}</span><p class="adv__text">{esc(t)}</p></div>')
        n += 1
    d = S["director"]
    return f"""<section class="section theme-paper section--paper" id="advantages" aria-labelledby="adv-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// 02 — Преимущества</p><h2 class="h2 sec-head__title" id="adv-title">Почему выбирают<br>Гараж</h2></div>
      <p class="sec-head__aside">Полный цикл: диагностика, ремонт, запчасти, кузов и дополнительное оборудование — в одном месте, с {D.FOUNDED} года.</p>
    </div>
    <div class="adv__grid">{"".join(cells)}</div>
    <p class="adv__note">{esc(S['advantages_note'])}</p>

    <div class="director reveal" id="director">
      <div class="director__photo">
        <img src="{D.img(d['photo'])}" alt="{esc(d['name'])}, {esc(d['position'])}" width="800" height="1000" loading="lazy" decoding="async">
        <span class="badge director__badge">{icon('shield', 'ic--sm')} генеральный директор</span>
      </div>
      <blockquote class="director__quote">
        {icon('quote', 'ic--quote')}
        <p class="director__text">{esc(d['text'])}</p>
        <footer class="director__who"><div><b>{esc(d['name'])}</b><span>{esc(d['position'])}</span></div></footer>
        <div class="row" style="margin-top:1.6rem"><a class="btn btn--primary btn--sm" href="{D.VK_URL}" target="_blank" rel="noopener">{icon('vk')} Написать отзыв</a><a class="link-arrow" href="/otzyvy.html">Все отзывы {icon('arrow-up-right')}</a></div>
      </blockquote>
    </div>
  </div>
</section>"""


def gallery():
    items = []
    for i, g in enumerate(S["gallery"]):
        full = D.img(g["full"])
        items.append(f"""<a class="gallery__item" href="{full}" data-lightbox="works">
      <img src="{full}" alt="Фото работ автосервиса Гараж, {i + 1}" width="1200" height="800" loading="lazy" decoding="async">
      <span class="gallery__idx">{i + 1:02d} / {len(S['gallery']):02d}</span>
      <span class="gallery__zoom">{icon('zoom')}</span>
    </a>""")
    return f"""<section class="section" id="gallery" aria-labelledby="gallery-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// 03 — Фото работ</p><h2 class="h2 sec-head__title" id="gallery-title">Фото работ</h2></div>
      <div class="row between" style="--gap:1rem"><p class="sec-head__aside">Ремонт двигателей, ходовой, кузова и электрики — как это выглядит в наших боксах.</p>
      {slider_nav("gallery-track", "фото")}</div>
    </div>
    <div class="slider reveal" data-slider><div class="slider__track" id="gallery-track">{"".join(items)}</div></div>
  </div>
</section>"""


def team():
    cards = []
    for i, m in enumerate(S["team"]):
        lead = " member--lead" if i == 0 else ""
        cards.append(f"""<article class="member{lead} reveal" style="--d:{i * 50}ms">
      <div class="member__photo"><img src="{D.img(m['photo'])}" alt="{esc(m['name'])} — {esc(m['position'])}" width="900" height="1200" loading="lazy" decoding="async"><span class="member__n">{i + 1:02d}</span></div>
      <h3 class="member__name">{esc(m['name'])}</h3>
      <p class="member__role">{esc(m['position'])}</p>
    </article>""")
    return f"""<section class="section section--black" id="team" aria-labelledby="team-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// 04 — Наша команда</p><h2 class="h2 sec-head__title" id="team-title">Наша команда</h2></div>
      <p class="sec-head__aside">{len(S['team'])} специалистов: диагносты, мотористы, электрики, мастера по ходовой, кузову и доп. оборудованию.</p>
    </div>
    <div class="team__grid">{"".join(cards)}</div>
  </div>
</section>"""


def contacts_strip():
    lat, lon = D.COORDS
    map_src = f"https://yandex.ru/map-widget/v1/?ll={lon}%2C{lat}&z=16&pt={lon}%2C{lat}%2Cpm2gnm&text={esc('Нижний Новгород, улица Красная Слобода, 9')}"
    return f"""<section class="section section--black" id="contacts" aria-labelledby="contacts-title">
  <div class="wrap contacts">
    <div class="reveal">
      <p class="eyebrow">// 06 — Контакты</p>
      <h2 class="h2 sec-head__title" id="contacts-title">Приезжайте<br>в Гараж</h2>
      <ul class="contacts__list">
        <li class="contacts__item">{icon('pin')}<div><b>{esc(D.ADDRESS_FULL)}</b><span>Автосервис и магазин запчастей</span></div></li>
        <li class="contacts__item">{icon('phone')}<div><a class="big" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a><span>Звоните по телефонам горячей линии</span></div></li>
        <li class="contacts__item">{icon('clock')}{otkryto.schedule(D.HOURS, title="Часы работы")}</li>
        <li class="contacts__item">{icon('mail')}<div><a class="big" href="mailto:{D.EMAIL}" style="font-size:1.2rem">{D.EMAIL}</a><span>Ответим в рабочие часы</span></div></li>
      </ul>
      {otkryto.actions()}
      <a class="link-arrow link-arrow--inline oc-go__more" href="/contacts/">Страница контактов {icon('arrow')}</a>
    </div>
    <div class="map reveal">
      <iframe src="{map_src}" title="Карта: ул. Красная слобода, 9, Нижний Новгород" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>
      <a class="map__label" href="{esc(otkryto.ROUTE_URL)}" target="_blank" rel="noopener">{icon('pin')} ул. Красная слобода, 9 — построить маршрут</a>
    </div>
  </div>
</section>"""


def jsonld():
    return schema.dump(schema.org())


def render_home():
    body = "\n".join([
        hero(),
        ticker(),
        services_map(),
        pribory_section(),
        advantages(),
        gallery(),
        team(),
        reviews_section(paper=True),
        stuk_section(),
        zima_section(),
        request_section("Оставить запрос"),
        green_note_wrap(),
        contacts_strip(),
    ])
    title, desc = D.page_meta(
        "home", "Автосервис в Нижнем Новгороде — ремонт автомобилей любых марок, запчасти, ТО | Гараж",
        "Автосервис «Гараж» в Нижнем Новгороде, ул. Красная слобода, 9. Ремонт и обслуживание автомобилей любых марок, запчасти для иномарок "
        "в наличии и под заказ, гарантия до 360 дней. Тел. (831) 416-16-77.")
    return document(title, desc, "/", body, body_class="page-home", jsonld=jsonld())


def green_note_wrap():
    return f'<div class="wrap" style="padding-bottom:var(--section-y)">{green_note()}</div>'
