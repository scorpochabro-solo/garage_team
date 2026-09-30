# -*- coding: utf-8 -*-
"""Static pages: about, contacts, payment, delivery, parts, catalogs, search, call/*, registration, agreement, reviews, 404."""
import re

from . import arki, knizhka, otkryto, schema
from . import data as D
from .icons import icon
from .layout import (document, page_hero, phone_aside, contact_card, green_note, reviews_section,
                     request_section, review_card)

esc = D.esc
# the old site's pages with the new titles and descriptions from data/page_seo.json on top
P = {key: {**page, **D.PAGE_SEO.get(key, {})} for key, page in D.SITE["pages"].items()}


def _split_h1(body_html):
    """Return (h1 text, body without h1/hr/outer wrappers)."""
    m = re.search(r"<h1>(.*?)</h1>", body_html, re.S)
    h1 = D.strip_tags(m.group(1)) if m else ""
    rest = re.sub(r"<h1>.*?</h1>", "", body_html, count=1, flags=re.S)
    rest = re.sub(r"<hr>", "", rest)
    rest = re.sub(r"^\s*(<div>\s*)+", "", rest)
    rest = re.sub(r"(\s*</div>)+\s*$", "", rest)
    rest = re.sub(r'href="/contacts"', 'href="/contacts/"', rest)
    rest = re.sub(r'src="([^"]+)"', lambda mm: f'src="{D.img(mm.group(1))}"', rest)
    return h1, rest.strip()


def _side(extra=""):
    return f'<aside class="page-grid__side">{contact_card()}{extra}</aside>'


def _facts_card():
    return f"""<div class="card card--solid">
  <div class="footer__title">Коротко о нас</div>
  <ul class="hours">
    <li><span>Работаем с</span><span>{D.FOUNDED} г.</span></li>
    <li><span>Направлений услуг</span><span>{len(D.CATEGORIES)}</span></li>
    <li><span>Видов работ</span><span>{len(D.SERVICES)}</span></li>
    <li><span>Гарантия на работы</span><span>до 360 дней*</span></li>
    <li><span>Коммерческая техника</span><span>до 5,5 т</span></li>
  </ul>
</div>"""


# ---------- about ----------
def render_about():
    h1, rest = _split_h1(P["about"]["body_html"])
    hero = page_hero(h1, [("Главная", "/"), ("О компании", None)], eyebrow="О компании", aside=phone_aside("Заказать звонок"), mark_icon="shield")
    body = f"""{hero}
<section class="wrap page-grid">
  <article class="prose reveal">{rest}</article>
  {_side(_facts_card())}
</section>
<div class="wrap" style="padding-bottom:var(--section-y)">{green_note()}</div>
{reviews_section(paper=True)}
{request_section("Оставить запрос")}"""
    return document(P["about"]["title"], P["about"]["meta_description"], "/about/", body, body_class="page-about")


# ---------- contacts ----------
def render_contacts():
    lat, lon = D.COORDS
    map_src = f"https://yandex.ru/map-widget/v1/?ll={lon}%2C{lat}&z=16&pt={lon}%2C{lat}%2Cpm2gnm&text={esc('Нижний Новгород, улица Красная Слобода, 9')}"
    hero = page_hero("Контакты", [("Главная", "/"), ("Контакты", None)], eyebrow="Как нас найти", aside=phone_aside("Заказать звонок"), mark_icon="steering",
                     lead=f"{esc(D.ADDRESS_FULL)}. Автосервис и магазин запчастей «Гараж».")
    body = f"""{hero}
<section class="wrap page-grid">
  <div class="stack" style="--gap:2.5rem">
    <ul class="info-list reveal">
      <li>{icon('pin')}<div><b>Адрес</b><span>{esc(D.ADDRESS_FULL)}</span></div></li>
      <li>{icon('phone')}<div><b>Телефон</b><a href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a></div></li>
      <li>{icon('mail')}<div><b>E-mail</b><a href="mailto:{D.EMAIL}">{D.EMAIL}</a></div></li>
      <li>{icon('vk')}<div><b>Мы в соцсетях</b><a href="{D.VK_URL}" target="_blank" rel="noopener">vk.com/garagebest</a></div></li>
    </ul>
    <div class="reveal">{otkryto.actions(row=True)}</div>
    <div class="reveal" id="hours">
      <div class="block-title"><span class="tag-num">// часы</span><h2 class="h3">Часы работы автосервиса</h2></div>
      {otkryto.schedule(D.HOURS, big=True)}
    </div>
    <div class="reveal">
      <div class="block-title"><span class="tag-num">// магазин</span><h2 class="h3">Магазин запчастей</h2></div>
      {otkryto.schedule(D.SHOP_HOURS, label="Часы работы магазина по дням недели", holidays=False, big=True)}
    </div>
    <div class="find">
      {arki.door()}
      <div class="map reveal">
        <iframe src="{map_src}" title="Карта: ул. Красная слобода, 9, Нижний Новгород" loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"></iframe>
        <a class="map__label" href="{esc(otkryto.ROUTE_URL)}" target="_blank" rel="noopener">{icon('pin')} Схема проезда — построить маршрут</a>
      </div>
    </div>
  </div>
  {_side()}
</section>
{request_section("Оставить запрос")}"""
    return document(P["contacts"]["title"], P["contacts"]["meta_description"], "/contacts/", body, body_class="page-contacts")


# ---------- payment / delivery ----------
def render_oplata():
    h1, rest = _split_h1(P["oplata"]["body_html"])
    hero = page_hero(h1, [("Главная", "/"), ("Оплата", None)], eyebrow="Оплата", aside=phone_aside("Заказать звонок"), mark_icon="ruble")
    body = f"""{hero}
<section class="wrap page-grid">
  <article class="prose reveal">{rest}</article>
  {_side(f'<a class="card card--link" href="/delivery.html"><div class="card__icon">{icon("parts")}</div><b class="h4">Доставка запчастей</b><p class="muted" style="margin-top:.4rem;font-size:.9rem">Бесплатно при заказе от 5000 ₽, по городу — 300 ₽.</p></a>')}
</section>
{request_section("Оставить заявку на запчасти или услуги автосервиса")}"""
    return document(P["oplata"]["title"], P["oplata"]["meta_description"], "/oplata.html", body, body_class="page-oplata")


def render_delivery():
    h1, rest = _split_h1(P["delivery"]["body_html"])
    hero = page_hero(h1, [("Главная", "/"), ("Доставка", None)], eyebrow="Доставка", aside=phone_aside("Заказать звонок"), mark_icon="parts")
    body = f"""{hero}
<section class="wrap page-grid">
  <article class="prose reveal">{rest}</article>
  {_side(f'<a class="card card--link" href="/oplata.html"><div class="card__icon">{icon("ruble")}</div><b class="h4">Оплата запчастей</b><p class="muted" style="margin-top:.4rem;font-size:.9rem">Предоплата от 50 %, наличными в магазине.</p></a>')}
</section>
{request_section("Оставить заявку на запчасти или услуги автосервиса")}"""
    return document(P["delivery"]["title"], P["delivery"]["meta_description"], "/delivery.html", body, body_class="page-delivery")


# ---------- parts ----------
def _brand_tabs(prefix="cat"):
    brands = D.SITE["catalog_brands"]
    cars = [b for b in brands if b["type"] == "car"]
    trucks = [b for b in brands if b["type"] == "truck"]

    def grid(items):
        def tile(b):
            src_file = D.SRC / "assets" / "img" / "brands" / b["img"].rsplit("/", 1)[-1]
            img_tag = (f'<img src="{D.img(b["img"])}" alt="{esc(b["name"])}" width="64" height="64" loading="lazy">'
                       if src_file.exists() else f'<span class="brand__ph" aria-hidden="true">{esc(b["name"][:2])}</span>')
            return f'<a class="brand" href="{b["href"]}">{img_tag}<span>{esc(b["name"])}</span></a>'
        return '<div class="brand-grid">' + "".join(tile(b) for b in items) + "</div>"

    return f"""<div class="tabs" role="tablist" data-tabs>
      <button class="tab" role="tab" id="{prefix}-tab-cars" aria-controls="{prefix}-panel-cars" aria-selected="true">Легковые · {len(cars)}</button>
      <button class="tab" role="tab" id="{prefix}-tab-trucks" aria-controls="{prefix}-panel-trucks" aria-selected="false">Грузовые · {len(trucks)}</button>
    </div>
    <div class="tab-panel" id="{prefix}-panel-cars" role="tabpanel" aria-labelledby="{prefix}-tab-cars">{grid(cars)}</div>
    <div class="tab-panel" id="{prefix}-panel-trucks" role="tabpanel" aria-labelledby="{prefix}-tab-trucks" hidden>{grid(trucks)}</div>"""


def render_avtozapchasti():
    ways = [
        ("Найти запчасти по номеру", "/search/", "search-menu-1.jpg"),
        ("Оставить заявку", "/call/request/", "search-menu-2.jpg"),
        ("Найти запчасти по каталогу", "/cats/", "search-menu-3.jpg"),
        ("Позвонить менеджеру", "/call/manager/", "search-menu-4.jpg"),
        ("Приехать к нам в магазин", "/contacts/", "search-menu-5.jpg"),
    ]
    ways_html = "".join(
        f'<a class="way reveal" href="{h}" style="--d:{i * 50}ms"><img src="{D.img("/img/example/" + im)}" alt="" width="200" height="200" loading="lazy"><span>{esc(n)} {icon("arrow")}</span></a>'
        for i, (n, h, im) in enumerate(ways))
    hero = page_hero(P["avtozapchasti"].get("h1", "Запчасти в Нижнем Новгороде"), [("Главная", "/"), ("Автозапчасти", None)], eyebrow="Автозапчасти", aside=phone_aside("Заказать звонок"), mark_icon="parts",
                     lead="Оптовые и розничные поставки запчастей для любых марок — японских, корейских, европейских, китайских и американских.")
    body = f"""{hero}
<section class="section section--tight">
  <div class="wrap">
    <div class="promo-pair">
      <div class="promo-card reveal">
        <img src="{D.img('/img/money2.jpg')}" alt="" width="120" height="120" loading="lazy">
        <div><b>Гарантия возврата!!!</b><p>Если деталь не подойдёт, мы гарантируем возврат.</p><button class="btn btn--ghost btn--sm" type="button" data-modal="call">{icon('phone')} Заказать звонок</button></div>
      </div>
      <div class="promo-card reveal" style="--d:80ms">
        <img src="{D.img('/img/dostavka2.jpg')}" alt="" width="120" height="120" loading="lazy">
        <div><b>Бесплатная доставка!*</b><p>У вас нет времени приехать в магазин? Доставим сами. <a class="accent" href="/delivery.html">Условия доставки</a></p><button class="btn btn--ghost btn--sm" type="button" data-modal="call">{icon('phone')} Заказать звонок</button><small>* при заказе от 5000 руб.</small></div>
      </div>
    </div>
    <div class="prose reveal">
      <p>Мы специализируемся на оптовых и розничных поставках запчастей для любых марок автомобилей – японских, корейских, европейских, китайских и американских. В нашей базе насчитывается свыше 20 млн наименований запчастей, 2 тысячи торговых марок в наличии и на заказ.</p>
      <p><strong>Сразу ответим на вопрос, который нам зададут не раз – МЫ НЕ ЗАНИМАЕМСЯ КОНТРАКТНЫМИ ЗАПЧАСТЯМИ И ПРОЧИМИ ЗАПЧАСТЯМИ Б/У.</strong></p>
      <p>Как устроены наличие, заказ и подбор деталей, чем оригинал отличается от аналога и что подготовить к заказу, читайте на странице <a class="accent" href="/services/avtozapcasti.html">автозапчасти в наличии и под заказ</a>.</p>
    </div>
    <div class="callout reveal" style="margin-top:1.5rem"><a class="accent" href="#request">Оставьте заявку!</a> или позвоните нам <a href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a></div>
    <div class="ways">{ways_html}</div>
  </div>
</section>
<section class="section section--tight" aria-labelledby="cats-title">
  <div class="wrap">
    <div class="block-title reveal"><span class="tag-num">// каталоги</span><h2 class="h3" id="cats-title">Каталоги запчастей</h2></div>
    <div class="reveal">{_brand_tabs("parts")}</div>
  </div>
</section>
{request_section("Оставить заявку на автозапчасти")}"""
    graph = [schema.shop(), schema.breadcrumbs([("Главная", "/"), ("Автозапчасти", None)], D.SITE_URL + "/avtozapchasti/")]
    return document(P["avtozapchasti"]["title"], P["avtozapchasti"]["meta_description"], "/avtozapchasti/", body, body_class="page-parts",
                    jsonld=schema.dump(graph))


def render_cats():
    hero = page_hero("Каталоги автозапчастей", [("Главная", "/"), ("Каталоги", None)], eyebrow="Электронные каталоги", aside=phone_aside("Заказать звонок"), mark_icon="parts",
                     lead="Выберите марку автомобиля — откроется электронный каталог запчастей.")
    body = f"""{hero}
<section class="section section--tight"><div class="wrap reveal">{_brand_tabs("cats")}</div></section>
{request_section("Оставить заявку на автозапчасти")}"""
    return document(P["cats"]["title"], P["cats"]["meta_description"], "/cats/", body, body_class="page-cats")


def render_search():
    h1, rest = _split_h1(P["search"]["body_html"])
    rest = re.sub(r"<form>.*?</form>", "", rest, flags=re.S)
    rest = re.sub(r"<p><strong>Внимание!.*?</strong></p>", "", rest, flags=re.S)
    hero = page_hero(h1, [("Главная", "/"), ("Поиск по номеру автозапчасти", None)], eyebrow="Поиск запчастей", aside=phone_aside("Заказать звонок"), mark_icon="search")
    body = f"""{hero}
<section class="wrap page-grid">
  <div class="stack" style="--gap:1.5rem">
    <form class="filter reveal" action="/search/" method="get" role="search">
      <div class="filter__input">{icon('search')}<input class="input" type="search" name="num" autocapitalize="characters" autocomplete="off" autocorrect="off" spellcheck="false" enterkeyhint="search" placeholder="Искать по номеру детали..." aria-label="Номер детали"></div>
      <button class="btn btn--primary" type="submit">Поиск</button>
    </form>
    <div class="callout callout--warn reveal">{icon('hazard')} Внимание! Поиск временно не работает. Оставьте заявку или позвоните — подберём деталь вручную.</div>
    <article class="prose reveal">{rest}</article>
  </div>
  {_side()}
</section>
{request_section("Оставить заявку на автозапчасти")}"""
    return document(P["search"]["title"], P["search"]["meta_description"], "/search/", body, body_class="page-search")


# ---------- call ----------
def render_call_request():
    hero = page_hero("Оставить заявку", [("Главная", "/"), ("Оставить заявку", None)], eyebrow="Заявка на подбор запчастей и ремонт",
                     lead="Заполните три коротких шага — менеджер подберёт запчасти или запишет на ремонт и свяжется с вами в рабочие часы.", aside=phone_aside("Заказать звонок"), mark_icon="send")
    body = f"""{hero}
{request_section("Оставить запрос")}
<div class="wrap" style="padding-bottom:var(--section-y)">{green_note()}</div>"""
    return document(P["call_request"]["title"], P["call_request"]["meta_description"], "/call/request/", body, body_class="page-call")


def render_call_manager():
    hero = page_hero("Звонок менеджеру", [("Главная", "/"), ("Звонок менеджеру", None)], eyebrow="Связаться с нами", aside=phone_aside("Заказать звонок"), mark_icon="phone")
    body = f"""{hero}
<section class="wrap page-grid">
  <div class="stack" style="--gap:2rem">
    <p class="lead reveal">Свяжитесь с нами по телефону: <a class="accent" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a>, и один из наших менеджеров быстро и качественно поможет Вам решить проблему или найти ответ на вопрос.</p>
    <p class="h3 reveal">Вы не останетесь без поддержки!</p>
    <div class="cta-inline reveal"><button class="btn btn--primary" type="button" data-modal="call">{icon('phone')} Заказать обратный звонок</button><span class="cta-inline__or">или напишите</span><a class="cta-inline__phone" style="font-size:1.1rem" href="mailto:{D.EMAIL}">{D.EMAIL}</a></div>
  </div>
  {_side()}
</section>
{request_section("Оставить запрос")}"""
    return document("Звонок менеджеру | Гараж - автосервис, поиск и подбор запчастей", "Свяжитесь с менеджером автотехцентра Гараж по телефону (831) 416-16-77.", "/call/manager/", body, body_class="page-call")


# ---------- registration ----------
def render_registration():
    org_types = ["Общество с ограниченной ответственностью", "Закрытое акционерное общество", "Открытое акционерное общество", "Индивидуальный предприниматель", "Некоммерческое партнёрство", "Другое"]
    opts = "".join(f'<option value="{i + 1}">{esc(t)}</option>' for i, t in enumerate(org_types))
    hero = page_hero("Регистрация в личном кабинете", [("Главная", "/"), ("Регистрация", None)], eyebrow="Личный кабинет · скидка 5%",
                     lead="Зарегистрируйтесь на сайте и получите скидку 5% на запчасти и услуги автосервиса.", aside=phone_aside("Заказать звонок"), mark_icon="user")
    body = f"""{hero}
<section class="wrap page-grid">
  <form class="stack reveal" style="--gap:1rem" action="/registration" method="post" novalidate data-registration>
    <div class="reg-section">
      <h2 class="reg-section__title">Регистрационные данные</h2>
      <div class="form-grid form-grid--2">
        <div class="field"><label class="field__label" for="reg-phone">Мобильный телефон <span class="req">*</span></label><div class="input--prefix"><span>+7</span><div class="row" style="--gap:.5rem;flex-wrap:nowrap"><input class="input" id="reg-code" name="RegistrationForm[areaCode]" type="text" inputmode="numeric" autocomplete="tel-area-code" maxlength="3" placeholder="903" style="width:90px" required aria-label="Код оператора"><input class="input" id="reg-phone" name="RegistrationForm[number]" type="text" inputmode="numeric" autocomplete="tel-local" maxlength="7" placeholder="1234567" required></div></div><span class="field__error">Введите номер телефона</span></div>
        <div class="field"><label class="field__label" for="reg-pass">Пароль <span class="req">*</span></label><input class="input" id="reg-pass" name="RegistrationForm[password]" type="password" autocomplete="new-password" required><span class="field__error">Придумайте пароль</span></div>
        <div class="field span-2"><span class="field__label">Укажите, в каком статусе вы будете с нами работать</span><div class="radio-group"><label class="radio"><input type="radio" name="RegistrationForm[type]" value="1" checked><span>Физ. лицо</span></label><label class="radio"><input type="radio" name="RegistrationForm[type]" value="2"><span>Юр. лицо</span></label></div></div>
      </div>
    </div>
    <div class="reg-section">
      <h2 class="reg-section__title">Персональные данные</h2>
      <div class="form-grid form-grid--2">
        <div class="field"><label class="field__label" for="reg-name">Ваше настоящее имя <span class="req">*</span></label><input class="input" id="reg-name" name="RegistrationForm[name]" type="text" placeholder="Например: Иван Иванов" autocomplete="name" autocapitalize="words" required><span class="field__error">Укажите имя</span></div>
        <div class="field" data-org-only hidden><label class="field__label" for="reg-pos">Должность <span class="req">*</span></label><input class="input" id="reg-pos" name="RegistrationForm[orgPosition]" type="text" autocomplete="organization-title" placeholder="Ваша должность..." required><span class="field__error">Укажите должность</span></div>
        <div class="field"><label class="field__label" for="reg-email">E-mail <span class="req">*</span></label><input class="input" id="reg-email" name="RegistrationForm[email]" type="email" placeholder="Адрес E-mail" autocomplete="email" required><span class="field__error">Укажите e-mail</span></div>
        <div class="field"><label class="field__label" for="reg-city">Город <span class="req">*</span></label><input class="input" id="reg-city" name="RegistrationForm[city]" type="text" autocomplete="address-level2" value="Нижний Новгород" required><span class="field__error">Укажите город</span></div>
        <div class="field span-2"><label class="field__label" for="reg-info">Дополнительная информация</label><textarea class="textarea" id="reg-info" name="RegistrationForm[info]" rows="3"></textarea></div>
      </div>
    </div>
    <div class="reg-section" data-org hidden>
      <h2 class="reg-section__title">Данные об организации</h2>
      <div class="form-grid form-grid--2">
        <div class="field"><label class="field__label" for="reg-orgtype">Форма собственности</label><select class="select" id="reg-orgtype" name="RegistrationForm[orgType]">{opts}</select></div>
        <div class="field"><label class="field__label" for="reg-orgname">Наименование организации <span class="req">*</span></label><input class="input" id="reg-orgname" name="RegistrationForm[orgName]" type="text" autocomplete="organization" required><span class="field__error">Укажите наименование</span></div>
        <div class="field"><label class="field__label" for="reg-inn">ИНН <span class="req">*</span></label><input class="input" id="reg-inn" name="RegistrationForm[orgInn]" type="text" inputmode="numeric" autocomplete="off" maxlength="12" required><span class="field__error">Укажите ИНН</span></div>
        <div class="field"><label class="field__label" for="reg-addr">Юридический адрес <span class="req">*</span></label><input class="input" id="reg-addr" name="RegistrationForm[orgAddress]" type="text" autocomplete="street-address" required><span class="field__error">Укажите адрес</span></div>
      </div>
    </div>
    <div class="reg-section">
      <h2 class="reg-section__title">Данные о доставке</h2>
      <div class="form-grid form-grid--2">
        <div class="field"><label class="field__label" for="reg-dost">Способ доставки</label><select class="select" id="reg-dost" name="RegistrationForm[dostavkaType]"><option value="pickup">Самовывоз</option><option value="courier">Доставка курьером</option></select></div>
        <div class="field" data-pickup><label class="field__label" for="reg-punkt">Пункт выдачи <span class="req">*</span></label><select class="select" id="reg-punkt" name="RegistrationForm[dostavkaPunkt]"><option value="1">Красная слобода, 9</option></select></div>
      </div>
      <label class="check"><input type="checkbox" name="RegistrationForm[agreement]" value="1" required><span class="check__box">{icon('check')}</span><span>С <a href="/page/soglashenie/" target="_blank">условиями работы/использования интернет-ресурса</a> согласен</span></label>
    </div>
    <div class="rq__actions"><button class="btn btn--primary btn--lg" type="submit">{icon('user')} Регистрация</button></div>
    <div class="form-success" data-success><div class="form-success__icon">{icon('check')}</div><h3 class="h3">Регистрация отправлена</h3><p class="muted">Мы проверим данные и активируем личный кабинет.</p></div>
  </form>
  {_side()}
</section>"""
    title, desc = D.page_meta("registration", "Регистрация | Гараж - автосервис, поиск и подбор запчастей",
                              "Регистрация в личном кабинете garage.team: скидка 5% на запчасти и услуги автосервиса Гараж, Нижний Новгород.")
    return document(title, desc, "/registration/", body, body_class="page-registration")


# ---------- «Моя машина»: the service book in the browser (build/knizhka.py) ----------
def render_moya_mashina():
    crumbs = [("Главная", "/"), (knizhka.H1, None)]
    hero = page_hero(knizhka.H1, crumbs, eyebrow=knizhka.EYEBROW, lead=esc(knizhka.LEAD), aside=phone_aside("Заказать звонок"),
                     mark_icon="inspection", title_html=knizhka.h1_html())
    title, desc = D.page_meta(knizhka.SEO_KEY, knizhka.TITLE, knizhka.DESCRIPTION)
    body = f"""{hero}
{knizhka.body()}
{request_section("Оставить заявку")}"""
    graph = schema.breadcrumbs(crumbs, D.SITE_URL + knizhka.PATH)
    return document(title, desc, knizhka.PATH, body, body_class="page-knizhka", jsonld=schema.dump(graph))


# ---------- agreement / reviews / 404 ----------
def render_soglashenie():
    pg = P["soglashenie"]
    h1, rest = _split_h1(pg["body_html"])
    hero = page_hero(h1 or "Пользовательское соглашение", [("Главная", "/"), ("Пользовательское соглашение", None)], eyebrow="Документы", mark_icon="inspection")
    body = f"""{hero}
<section class="wrap page-grid page-grid--single"><article class="prose agreement reveal">{rest}</article></section>"""
    return document(pg["title"], pg["meta_description"], "/page/soglashenie/", body, body_class="page-agreement")


def render_otzyvy():
    cards = "".join(review_card(r) for r in D.SITE["reviews"])
    hero = page_hero("Отзывы клиентов", [("Главная", "/"), ("Отзывы", None)], eyebrow="Отзывы", aside=f'<a class="btn btn--primary" href="{D.VK_URL}" target="_blank" rel="noopener">{icon("vk")} Написать отзыв</a>', mark_icon="star",
                     lead="Реальные отзывы из ВКонтакте, Instagram и Facebook. Напишите о своём опыте — мы читаем каждый.")
    body = f"""{hero}
<section class="section section--tight"><div class="wrap reveal"><div class="reviews-grid">{cards}</div></div></section>
{request_section("Оставить запрос")}"""
    title, desc = D.page_meta("otzyvy", "Отзывы клиентов | Автосервис Гараж, Нижний Новгород", "Отзывы клиентов автосервиса Гараж в Нижнем Новгороде.")
    return document(title, desc, "/otzyvy.html", body, body_class="page-reviews")


def render_404():
    body = f"""<section class="wrap notfound">
  <div class="notfound__code" aria-hidden="true">404</div>
  <h1 class="h2" style="margin-top:1rem">Страница не найдена</h1>
  <p class="lead" style="margin:1rem auto 0">Возможно, адрес изменился. Загляните в услуги или позвоните нам — поможем.</p>
  <div class="notfound__actions"><a class="btn btn--primary" href="/">На главную</a><a class="btn btn--ghost is-on-dark" href="/services.html">Все услуги</a><a class="btn btn--ghost is-on-dark" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a></div>
</section>"""
    return document("Страница не найдена | Гараж", "Страница не найдена.", "/404.html", body, body_class="page-404", noindex=True)


PAGES = {
    "/about/": render_about,
    "/contacts/": render_contacts,
    "/oplata.html": render_oplata,
    "/delivery.html": render_delivery,
    "/avtozapchasti/": render_avtozapchasti,
    "/cats/": render_cats,
    "/search/": render_search,
    "/call/request/": render_call_request,
    "/call/manager/": render_call_manager,
    "/registration/": render_registration,
    "/page/soglashenie/": render_soglashenie,
    "/otzyvy.html": render_otzyvy,
    knizhka.PATH: render_moya_mashina,
    "/404.html": render_404,
}
