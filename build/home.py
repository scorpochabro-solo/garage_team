# -*- coding: utf-8 -*-
"""Homepage renderer."""
import json
import math

from . import data as D
from . import schema
from .icons import icon, icon_for_href
from .layout import document, request_section, reviews_section, green_note, slider_nav

esc = D.esc
S = D.SITE

# Тексты первого экрана. Каждая строка заголовка — отдельная строка на экране; зелёным красятся строки из HERO_ACCENT_FROM и ниже.
HERO_EYEBROW = "Complete car care · since 2011"
HERO_LINES = ["Автосервис", "в Нижнем", "Новгороде"]
HERO_ACCENT_FROM = 1
HERO_SUB = ("Ремонт и обслуживание автомобилей любых марок с 2011 года. Коммерческая техника до 5,5 т, "
            "запчасти в наличии и под заказ, гарантия на работы до 360 дней*.")


# «Кладка»: the first screen is the real brick wall of the building, lit from above like the office under its pendant lamps.
# Up to 1000px (one column) a portrait crop of the office wall: the wide close-up would show two bricks per screen there.
HERO_WALL = "/assets/img/real/brick-texture.webp"          # 1600×708; the left third, under the dark veil, softened (−57 KB)
HERO_WALL_PHONE = "/assets/img/real/brick-wall.webp"       # 640×730
LOUNGE_WALL = "/assets/img/real/brick-lounge.webp"         # 1090×355, the half bricks of the advantages grid
HERO_WALL_CAPTION = "Кирпичная стена · ул. Красная слобода, 9"


def hero():
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
    return f"""<section class="hero hero--brick" id="top" aria-labelledby="hero-title">
  <div class="hero__bg" aria-hidden="true">
    <picture><source media="(max-width: 1000px)" srcset="{HERO_WALL_PHONE}" width="640" height="730"><img class="hero__photo" src="{HERO_WALL}" alt="" width="1600" height="708" fetchpriority="high" decoding="async"></picture>
    <div class="hero__veil"></div>
    <div class="hero__lamp"></div>
    <div class="hero__glow"></div>
  </div>
  <p class="hero__caption" aria-hidden="true">{esc(HERO_WALL_CAPTION)}</p>
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


# «Кладка»: the director's photo is an arched window of the office: a round head whose top is a ring of bricks laid on
# edge, flush with the sides of the photo like the brick arches over the windows, with light mortar in the joints.
# Drawn once at build time over the photo, in units of its width (100; the photo is 4:5, so the view box is 100×125).
ARCH_DEPTH = 5.5      # one brick on edge
ARCH_JOINT = 0.45     # radial joints, at mid-depth
ARCH_BED = 0.6        # mortar bed between the ring and the photo
ARCH_BRICKS = 37      # odd: a keystone at the top
ARCH_TONES = (0, 1, 0, 2, 0, 1, 2, 0)    # three close kiln shades (kladka.css .arch .t0–.t2), stepped so no pattern shows


def arch_svg():
    cx = cy = ro = 50.0                   # the round head: a half circle over the full width of the photo
    ri = ro - ARCH_DEPTH
    rb = ri - ARCH_BED
    gap = ARCH_JOINT / ((ri + ro) / 2)    # radians
    step = math.pi / ARCH_BRICKS

    def pt(r, a):
        return f"{cx + r * math.cos(a):.2f} {cy - r * math.sin(a):.2f}"

    def ring(r0, r1, a0, a1):
        return f"M{pt(r0, a0)} L{pt(r1, a0)} A{r1} {r1} 0 0 1 {pt(r1, a1)} L{pt(r0, a1)} A{r0} {r0} 0 0 0 {pt(r0, a0)}Z"

    parts = [f'<path class="mortar" d="{ring(rb, ro, math.pi, 0)}"/>']
    for i in range(ARCH_BRICKS):
        # the springers stand flush on the sides of the photo: no joint on their outer ends
        a0 = math.pi - i * step - (gap / 2 if i else 0)
        a1 = math.pi - (i + 1) * step + (gap / 2 if i < ARCH_BRICKS - 1 else 0)
        parts.append(f'<path class="t{ARCH_TONES[(i * 3) % len(ARCH_TONES)]}" d="{ring(ri, ro, a0, a1)}"/>')
    return '<svg class="arch" viewBox="0 0 100 125" aria-hidden="true" focusable="false">' + "".join(parts) + "</svg>"


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
    # «Кладка»: on a wide screen the cards are laid in running bond, three bricks per course, joints in mortar colour.
    # The middle course is shifted by half a brick, so it starts and ends with a half brick — there the real wall of the
    # client lounge shows through. Decorative only: the halves are hidden below 1000px, where the grid has 2 or 1 columns.
    # a half is ~210px tall with the strip cropped to cover it, so the image is drawn ~650px wide: the 800px copy at 1x
    half = (f'<span class="adv__half adv__half--{{}}" aria-hidden="true"><img src="{LOUNGE_WALL}" '
            f'srcset="{LOUNGE_WALL.replace(".webp", "-800.webp")} 800w, {LOUNGE_WALL} 1090w" sizes="660px" alt="" '
            f'width="1090" height="355" loading="lazy" decoding="async"></span>')
    cells[3:3] = [half.format("start")]
    cells[6:6] = [half.format("end")]
    d = S["director"]
    return f"""<section class="section theme-paper section--paper" id="advantages" aria-labelledby="adv-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// 02 — Преимущества</p><h2 class="h2 sec-head__title" id="adv-title">Почему выбирают<br>Гараж</h2></div>
      <p class="sec-head__aside">Полный цикл: диагностика, ремонт, запчасти, кузов и дополнительное оборудование — в одном месте, с {D.FOUNDED} года.</p>
    </div>
    <div class="adv__grid adv__grid--bond">{"".join(cells)}</div>
    <p class="adv__note">{esc(S['advantages_note'])}</p>

    <div class="director reveal" id="director">
      <div class="director__window">
        <div class="director__photo">
          <img src="{D.img(d['photo'])}" alt="{esc(d['name'])}, {esc(d['position'])}" width="800" height="1000" loading="lazy" decoding="async">
          <span class="badge director__badge">{icon('shield', 'ic--sm')} генеральный директор</span>
        </div>
        {arch_svg()}
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
    route = f"https://yandex.ru/maps/?rtext=~{lat}%2C{lon}"
    hours = "<br>".join(f"{esc(d)}: {esc(h)}" for d, h in D.HOURS)
    return f"""<section class="section section--black" id="contacts" aria-labelledby="contacts-title">
  <div class="wrap contacts">
    <div class="reveal">
      <p class="eyebrow">// 06 — Контакты</p>
      <h2 class="h2 sec-head__title" id="contacts-title">Приезжайте<br>в Гараж</h2>
      <ul class="contacts__list">
        <li class="contacts__item">{icon('pin')}<div><b>{esc(D.ADDRESS_FULL)}</b><span>Автосервис и магазин запчастей</span></div></li>
        <li class="contacts__item">{icon('phone')}<div><a class="big" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a><span>Звоните по телефонам горячей линии</span></div></li>
        <li class="contacts__item">{icon('clock')}<div><b>Часы работы</b><span>{hours}</span></div></li>
        <li class="contacts__item">{icon('mail')}<div><a class="big" href="mailto:{D.EMAIL}" style="font-size:1.2rem">{D.EMAIL}</a><span>Ответим в рабочие часы</span></div></li>
      </ul>
      <div class="row" style="margin-top:2rem"><a class="btn btn--primary" href="{route}" target="_blank" rel="noopener">{icon('pin')} Схема проезда</a><a class="btn btn--ghost is-on-dark" href="/contacts/">Страница контактов {icon('arrow')}</a></div>
    </div>
    <div class="map reveal">
      <iframe src="{map_src}" title="Карта: ул. Красная слобода, 9, Нижний Новгород" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>
      <a class="map__label" href="{route}" target="_blank" rel="noopener">{icon('pin')} ул. Красная слобода, 9 — построить маршрут</a>
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
        advantages(),
        gallery(),
        team(),
        reviews_section(paper=True),
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
