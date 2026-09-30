# -*- coding: utf-8 -*-
"""Page shell and shared blocks: head, header, footer, modals, request form, reviews, CTA."""
from . import data as D
from . import otkryto
from . import shtorka
from .icons import icon, sprite, icon_for_href

esc = D.esc


# ---------- sliders ----------
def slider_nav(track_id, what):
    """Arrows for a .slider__track; they sit in the section heading, outside the slider, and name their track by aria-controls."""
    return (f'<div class="slider__nav">'
            f'<button class="slider__btn" type="button" data-prev aria-controls="{track_id}" aria-label="Предыдущие {what}">{icon("chevron-left")}</button>'
            f'<button class="slider__btn" type="button" data-next aria-controls="{track_id}" aria-label="Следующие {what}">{icon("chevron-right")}</button>'
            f'</div>')


# ---------- document ----------
def _version(kind):
    """?v=<content hash> for site.css / site.js, so a browser never pairs a new page with a stale cached stylesheet."""
    v = D.ASSET_VERSION.get(kind)
    return f"?v={v}" if v else ""


def document(title, description, path, body, body_class="", og_image=None, jsonld=None, noindex=False):
    canonical = D.SITE_URL + path
    og = og_image or "/assets/img/misc/advantages-bg.webp"
    robots = '<meta name="robots" content="noindex, nofollow">' if noindex else ""
    ld = f'<script type="application/ld+json">{jsonld}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="ru" data-base="{D.BASE}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{robots}
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(D.SITE_URL + og)}">
<meta property="og:locale" content="ru_RU">
<meta name="theme-color" content="#0c0d0c">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/assets/logo/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/logo/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/unbounded-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/manrope-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
{shtorka.head()}
<link rel="stylesheet" href="/assets/css/site.css{_version('css')}">
{ld}
</head>
<body class="{esc(body_class)}">
{sprite()}
<a class="sr-only" href="#main">Перейти к содержимому</a>
{topline()}
{header()}
{mobile_menu()}
{shtorka.markup()}
<main id="main">
{body}
</main>
{footer()}
{mobile_bar()}
{modals()}
<script src="/assets/js/site.js{_version('js')}" defer></script>
</body>
</html>
"""


# ---------- header ----------
def topline():
    return f"""<div class="topline">
  <div class="wrap topline__in">
    <span class="topline__item">{icon('pin')} {esc(D.ADDRESS_SHORT)}</span>
    {otkryto.topline_item()}
    <a class="topline__item topline__item--mail" href="mailto:{D.EMAIL}">{icon('mail')} {D.EMAIL}</a>
    <span class="topline__spacer"></span>
    <a class="topline__item" href="{D.VK_URL}" target="_blank" rel="noopener">{icon('vk')} Подпишитесь на нас</a>
    <button class="topline__item" type="button" data-modal="login">{icon('user')} Вход в личный кабинет</button>
    <a class="topline__item" href="/avtozapchasti/" id="cart-link" data-count="0" title="Корзина запчастей">{icon('cart')} Корзина</a>
  </div>
</div>"""


def header():
    nav = "".join(f'<a class="nav__link" href="{h}">{esc(n)}</a>' for n, h in D.NAV)
    return f"""<header class="site-header" data-header>
  <div class="wrap site-header__in">
    <a class="logo" href="/" aria-label="Гараж — на главную"><img src="/assets/logo/logo.svg" width="133" height="48" alt="Garage Team — автосервис «Гараж» в Нижнем Новгороде"></a>
    <nav class="nav" aria-label="Основное меню">{nav}</nav>
    <div class="site-header__actions">
      <a class="site-header__phone" href="tel:{D.PHONE_TEL}"><span class="mono">{D.PHONE_CODE}</span> {D.PHONE_NUM}</a>
      <button class="btn btn--ghost btn--sm is-on-dark" type="button" data-modal="call">{icon('phone')} Заказать звонок</button>
      <a class="btn btn--primary btn--sm" href="/call/request/">{icon('check')} Оставить заявку</a>
      <button class="burger" type="button" aria-label="Открыть меню" aria-expanded="false" aria-controls="mobile-menu">{icon('menu', 'ic--menu')}{icon('close', 'ic--close')}</button>
    </div>
  </div>
</header>"""


def mobile_menu():
    links = "".join(f'<a class="mobile-menu__link" href="{h}">{esc(n)} {icon("arrow-up-right")}</a>' for n, h in D.NAV)
    return f"""<div class="mobile-menu" id="mobile-menu">
  <nav class="mobile-menu__nav" aria-label="Мобильное меню">{links}</nav>
  <div class="mobile-menu__meta">
    <a class="mobile-menu__phone" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a>
    {otkryto.menu_item()}
    <span>{icon('pin')} {esc(D.ADDRESS_SHORT)}</span>
    <a href="mailto:{D.EMAIL}">{icon('mail')} {D.EMAIL}</a>
    <a href="{D.VK_URL}" target="_blank" rel="noopener">{icon('vk')} Мы ВКонтакте</a>
    <button type="button" data-modal="login">{icon('user')} Вход в личный кабинет</button>
    <a href="/avtozapchasti/">{icon('cart')} Корзина</a>
  </div>
  <div class="mobile-menu__cta">
    <a class="btn btn--primary" href="/call/request/">{icon('check')} Оставить заявку</a>
    <button class="btn btn--ghost is-on-dark" type="button" data-modal="call">{icon('phone')} Заказать звонок</button>
  </div>
</div>"""


def mobile_bar():
    return f"""<div class="mobile-bar">
  <a class="btn btn--ghost is-on-dark" href="tel:{D.PHONE_TEL}">{icon('phone')} Позвонить</a>
  <a class="btn btn--primary" href="/call/request/">{icon('check')} Заявка</a>
</div>"""


# ---------- footer ----------
def footer():
    links = "".join(f'<a href="{h}">{esc(n)}</a>' for n, h in D.FOOTER_LINKS)
    cats = "".join(f'<a href="{c["href"]}">{esc(c["name"])}</a>' for c in D.CATEGORIES[:10])
    hours = "".join(f"<span>{icon('clock')}<span>{esc(d)}: {esc(h)}</span></span>" for d, h in D.HOURS)
    return f"""<footer class="site-footer">
  <div class="footer__watermark" aria-hidden="true">ГАРАЖ</div>
  <div class="wrap site-footer__in">
    <div class="footer__grid">
      <div class="footer__brand">
        <a class="logo logo--footer" href="/"><img src="/assets/logo/logo.svg" width="221" height="80" alt="Garage Team — автосервис «Гараж»" loading="lazy"></a>
        <p class="footer__slogan mono" lang="en">{esc(D.SLOGAN_EN)}</p>
        <p>{esc(D.COMPANY)}<br>{esc(D.COMPANY_LINE_2)}<br>Автосервис и магазин запчастей в Нижнем Новгороде с {D.FOUNDED} года.</p>
        <div class="footer__social">
          <a href="{D.VK_URL}" target="_blank" rel="noopener" aria-label="ВКонтакте">{icon('vk')}</a>
          <a href="{D.FB_URL}" target="_blank" rel="noopener" aria-label="Facebook">{icon('facebook')}</a>
        </div>
      </div>
      <div>
        <div class="footer__title">Разделы</div>
        <div class="footer__links">{links}</div>
      </div>
      <div>
        <div class="footer__title">Услуги</div>
        <div class="footer__links">{cats}<a href="/services.html"><b>Все {len(D.CATEGORIES)} направлений →</b></a></div>
      </div>
      <div>
        <div class="footer__title">Звоните по телефонам горячей линии</div>
        <div class="footer__contact">
          <a class="footer__phone" href="tel:{D.PHONE_TEL}">{esc(D.PHONE)}</a>
          <a href="mailto:{D.EMAIL}">{icon('mail')}<span>{D.EMAIL}</span></a>
          <span>{icon('pin')}<span>{esc(D.ADDRESS_FULL)}</span></span>
          {hours}
        </div>
      </div>
    </div>
    <div class="footer__bottom">
      <span>© {D.COPYRIGHT_FROM}–<span data-year>{D.year_now()}</span> {esc(D.COMPANY)}. Все права защищены.</span>
      <span><a href="/page/soglashenie/">Пользовательское соглашение</a> · <a href="/contacts/">Схема проезда</a></span>
    </div>
  </div>
</footer>"""


# ---------- modals ----------
def modals():
    return call_modal() + login_modal() + lightbox()


def call_modal():
    return f"""<dialog class="modal" id="modal-call" aria-labelledby="modal-call-title">
  <div class="modal__panel">
    <button class="modal__close" type="button" data-close aria-label="Закрыть">{icon('close')}</button>
    <form data-simple-form action="/call" method="post" novalidate data-error-text="Не удалось отправить. Позвоните: {esc(D.PHONE)}">
      <div data-body>
        <h2 class="modal__title" id="modal-call-title">Заказать звонок / консультацию</h2>
        <p class="modal__lead">Заполните, пожалуйста, поля ниже, чтобы мы могли связаться с вами.</p>
        <div class="form-grid form-grid--2">
          <div class="field"><label class="field__label" for="call-name">Имя <span class="req">*</span></label><input class="input" id="call-name" name="contact_name" type="text" autocomplete="name" autocapitalize="words" enterkeyhint="next" required><span class="field__error">Укажите, как к вам обращаться</span></div>
          <div class="field"><label class="field__label" for="call-phone">Телефон <span class="req">*</span></label><input class="input" id="call-phone" name="contact_phone" type="tel" autocomplete="tel" enterkeyhint="next" data-phone required><span class="field__error">Укажите корректный телефон</span></div>
          <div class="field"><label class="field__label" for="call-car">Для автомобиля</label><input class="input" id="call-car" name="car" type="text" placeholder="Марка, модель, год"></div>
          <div class="field"><label class="field__label" for="call-vin">VIN</label><input class="input" id="call-vin" name="vin_code" type="text" autocapitalize="characters" autocomplete="off" autocorrect="off" spellcheck="false" maxlength="17" placeholder="Например: 2C4GJ453XYR693697"></div>
          <div class="field span-2"><label class="field__label" for="call-msg">Комментарий</label><textarea class="textarea" id="call-msg" name="message" rows="3"></textarea></div>
          <div class="field span-2"><label class="check"><input type="checkbox" name="agree" value="1" required><span class="check__box">{icon('check')}</span><span>Соглашаюсь с <a href="/page/soglashenie/" target="_blank">пользовательским соглашением</a> и обработкой персональных данных</span></label></div>
        </div>
        <input type="hidden" name="send" value="1">
        <div class="rq__actions"><button class="btn btn--ghost" type="button" data-close>Отмена</button><button class="btn btn--primary" type="submit">{icon('phone')} Позвоните мне</button></div>
      </div>
      <div class="form-success" data-success>
        <div class="form-success__icon">{icon('check')}</div>
        <h3 class="h4">{esc(D.SITE.get('sent_message', 'Ваше сообщение отправлено!'))}</h3>
        <button class="btn btn--primary btn--sm" type="button" data-close>OK</button>
      </div>
    </form>
  </div>
</dialog>"""


def login_modal():
    return f"""<dialog class="modal" id="modal-login" aria-labelledby="modal-login-title">
  <div class="modal__panel">
    <button class="modal__close" type="button" data-close aria-label="Закрыть">{icon('close')}</button>
    <form data-simple-form data-redirect="1" action="/login/popup" method="post" novalidate data-success-text="Вы вошли в личный кабинет" data-error-text="Не удалось войти. Проверьте телефон и пароль">
      <div data-body>
        <h2 class="modal__title" id="modal-login-title">Вход в личный кабинет</h2>
        <p class="modal__lead">Для входа введите мобильный и пароль. Или <a href="/registration/">зарегистрируйтесь</a>, если у вас ещё нет учётной записи.</p>
        <div class="form-grid">
          <div class="field">
            <label class="field__label" for="login-phone">Мобильный телефон <span class="req">*</span></label>
            <div class="input--prefix"><span>+7</span><div class="row" style="--gap:.5rem;flex-wrap:nowrap"><input class="input" id="login-code" name="UserLoginForm[areaCode]" type="text" inputmode="numeric" autocomplete="tel-area-code" maxlength="3" placeholder="903" style="width:90px" required aria-label="Код оператора"><input class="input" id="login-phone" name="UserLoginForm[number]" type="text" inputmode="numeric" autocomplete="tel-local" maxlength="7" placeholder="1234567" required></div></div>
            <span class="field__error">Введите номер телефона</span>
          </div>
          <div class="field"><label class="field__label" for="login-pass">Пароль <span class="req">*</span></label><input class="input" id="login-pass" name="UserLoginForm[password]" type="password" autocomplete="current-password" required><span class="field__error">Введите пароль</span></div>
          <div class="row between" style="--gap:.75rem">
            <button class="btn btn--text" type="button" data-lost-toggle>Забыли пароль?</button>
            <button class="btn btn--text" type="button" data-sms>Получить пароль по СМС</button>
          </div>
          <div data-lost hidden>
            <div class="field"><label class="field__label" for="lost-email">Эл. почта <span class="req">*</span></label><div class="row" style="--gap:.5rem;flex-wrap:nowrap"><input class="input" id="lost-email" name="lost-email" type="email" autocomplete="email" placeholder="you@mail.ru"><button class="btn btn--ghost btn--sm" type="button" data-email-lost>Отправить</button></div><span class="field__hint">Пришлём пароль на указанный e-mail.</span></div>
          </div>
          <label class="check"><input type="checkbox" name="agree" value="1" required checked><span class="check__box">{icon('check')}</span><span>Подтверждаю, что с <a href="/page/soglashenie/" target="_blank">Пользовательским соглашением</a> ознакомлен и согласен</span></label>
        </div>
        <input type="hidden" name="send" value="1">
        <div class="rq__actions"><a class="btn btn--ghost" href="/registration/">Регистрация</a><button class="btn btn--primary" type="submit">{icon('user')} Войти</button></div>
      </div>
      <div class="form-success" data-success>
        <div class="form-success__icon">{icon('check')}</div>
        <h3 class="h4">{esc(D.SITE.get('sent_message', 'Ваше сообщение отправлено!'))}</h3>
        <button class="btn btn--primary btn--sm" type="button" data-close>OK</button>
      </div>
    </form>
  </div>
</dialog>"""


def lightbox():
    return f"""<dialog class="lightbox" id="lightbox" aria-label="Просмотр фото">
  <div class="lightbox__stage"><img class="lightbox__img" alt=""></div>
  <span class="lightbox__count">01 / 01</span>
  <button class="lightbox__btn lightbox__btn--prev" type="button" data-prev aria-label="Предыдущее фото">{icon('chevron-left')}</button>
  <button class="lightbox__btn lightbox__btn--next" type="button" data-next aria-label="Следующее фото">{icon('chevron-right')}</button>
  <button class="lightbox__close" type="button" data-close aria-label="Закрыть">{icon('close')}</button>
</dialog>"""


# ---------- shared blocks ----------
def crumbs(items):
    lis = []
    for name, href in items:
        lis.append(f'<li><a href="{href}">{esc(name)}</a></li>' if href else f'<li><span aria-current="page">{esc(name)}</span></li>')
    return f'<nav aria-label="Хлебные крошки"><ol class="crumbs">{"".join(lis)}</ol></nav>'


def page_hero(title, crumb_items, eyebrow=None, lead=None, aside=None, mark_icon=None, title_html=None):
    eb = f'<p class="eyebrow">{esc(eyebrow)}</p>' if eyebrow else ""
    ld = f'<p class="lead page-hero__lead">{lead}</p>' if lead else ""
    aside_html = f'<div class="page-hero__aside">{aside}</div>' if aside else ""
    mark = f'<div class="page-hero__mark" aria-hidden="true">{icon(mark_icon)}</div>' if mark_icon else ""
    return f"""<section class="page-hero">
  {mark}
  <div class="wrap page-hero__in">
    <div>
      {crumbs(crumb_items)}
      {eb}
      <h1 class="h1 page-hero__title">{title_html or esc(title)}</h1>
      {ld}
    </div>
    {aside_html}
  </div>
</section>"""


def phone_aside(cta_label="Записаться на приём", preset=None):
    preset_attr = f" data-preset='{preset}'" if preset else ""
    return f"""<button class="btn btn--primary" type="button" data-modal="call"{preset_attr}>{icon('phone')} {esc(cta_label)}</button>
    <a class="page-hero__phone" href="tel:{D.PHONE_TEL}"><b>{esc(D.PHONE)}</b><span>или позвоните нам</span></a>"""


def contact_card(shop=False):
    """Side card with the phone and opening hours: the workshop's by default, the parts shop's when shop=True."""
    label, hours = ("Магазин запчастей", D.SHOP_HOURS) if shop else ("Записаться на приём", D.HOURS)
    return f"""<div class="contact-card">
  <div class="contact-card__label">{label}</div>
  <a class="contact-card__phone" href="tel:{D.PHONE_TEL}"><small>звоните</small>{esc(D.PHONE)}</a>
  <div class="contact-card__hours">Пн–Пт {esc(hours[0][1])} · Сб {esc(hours[1][1])}<br>{esc(D.ADDRESS_SHORT)}</div>
  <button class="btn btn--white btn--sm" type="button" data-modal="call">{icon('phone')} Заказать звонок</button>
</div>"""


def side_index(active_href=None):
    items = []
    for c in D.CATEGORIES:
        cls = ' class="is-active"' if c["href"] == active_href else ""
        items.append(f'<li><a href="{c["href"]}"{cls}>{icon(icon_for_href(c["href"]))}<span>{esc(c["name"])}</span></a></li>')
    # a disclosure: open next to the content on wide screens, collapsed under it on phones (core.js syncs `open`)
    return f"""<details class="side-index" data-side-index open>
  <summary class="side-index__title"><span>Направления</span><span class="side-index__n">{len(D.CATEGORIES)}{icon('plus', 'side-index__ic')}</span></summary>
  <nav aria-label="Все направления услуг"><ul>{"".join(items)}</ul></nav>
</details>"""


def green_note():
    return f"""<div class="note-green reveal">
  <p>Позвоните менеджеру нашего сервисного центра, готовому предоставить бесплатную консультацию и оформить заявку на посещение ремонтного бокса.</p>
  <a class="note-green__phone" href="tel:{D.PHONE_TEL}"><small>бесплатная консультация</small>{esc(D.PHONE)}</a>
</div>"""


def review_card(r):
    photo = f'<img class="avatar" src="{D.img(r["photo"])}" alt="" loading="lazy" width="56" height="56">' if r.get("photo") else '<span class="avatar"></span>'
    link = ""
    src_icon = ""
    if r.get("link"):
        host = r["link"].split("/")[2]
        label = "ВКонтакте" if "vk.com" in host else ("Instagram" if "instagram" in host else ("Facebook" if "facebook" in host else host))
        ic = "vk" if "vk.com" in host else ("instagram" if "instagram" in host else ("facebook" if "facebook" in host else "external"))
        link = f'<a href="{esc(r["link"])}" target="_blank" rel="noopener nofollow">{icon("external", "ic--sm")} Отзыв в {esc(label)}</a>'
        src_icon = f'<span class="review__src" aria-hidden="true">{icon(ic)}</span>'
    return f"""<article class="review">
  <p class="review__text">{esc(r["text"])}</p>
  <div class="review__who">{photo}<div><b>{esc(r["name"])}</b>{link}</div>{src_icon}</div>
</article>"""


def reviews_section(compact=False, paper=True):
    cards = "".join(review_card(r) for r in D.SITE["reviews"])
    theme = " theme-paper section--paper" if paper else ""
    n = len(D.SITE["reviews"])
    return f"""<section class="section{theme}" id="reviews" aria-labelledby="reviews-title">
  <div class="wrap">
    <div class="sec-head reveal">
      <div><p class="eyebrow">// Отзывы клиентов</p><h2 class="h2 sec-head__title" id="reviews-title">Что говорят<br>наши клиенты</h2></div>
      <div class="row between" style="--gap:1rem"><p class="sec-head__aside">{n} реальных отзывов из ВКонтакте, Instagram и Facebook. Ещё больше — на нашей странице <a class="accent" href="{D.VK_URL}" target="_blank" rel="noopener">ВКонтакте</a>.</p>
      {slider_nav("reviews-track", "отзывы")}</div>
    </div>
    <div class="slider reveal" data-slider>
      <div class="slider__track" id="reviews-track">{cards}</div>
    </div>
  </div>
</section>"""


# ---------- request form ----------
def request_section(title="Оставить запрос", section_id="request", paper=False):
    brands = "".join(f'<option value="{b["id"]}">{esc(b["name"])}</option>' for b in D.SITE["brand_options"])
    steps = "".join(f'<div class="step{" is-active" if i == 1 else ""}" data-step="{i}"><span class="step__n">{i}</span><span>{n}</span></div>'
                    for i, n in [(1, "Выбор автомобиля"), (2, "Ввод запроса"), (3, "Контактная информация")])
    theme = " theme-paper section--paper" if paper else ""
    return f"""<section class="section request{theme}" id="{section_id}" aria-labelledby="{section_id}-title">
  <div class="wrap request__in">
    <div class="request__side reveal">
      <p class="eyebrow">// Заявка онлайн</p>
      <h2 class="h2 sec-head__title" id="{section_id}-title">{esc(title)}</h2>
      <p class="lead">Подберём запчасти и запишем на ремонт. Три коротких шага — и менеджер свяжется с вами в рабочие часы.</p>
      <p class="muted" style="margin-top:1.2rem;max-width:44ch">{esc(D.SITE.get('request_fallback', ''))}</p>
      <a class="request__phone" href="tel:{D.PHONE_TEL}"><small>звоните</small>{esc(D.PHONE)}</a>
      <div class="request__social"><span>Подпишитесь на нас</span><a href="{D.VK_URL}" target="_blank" rel="noopener" aria-label="ВКонтакте">{icon('vk')}</a><a href="{D.FB_URL}" target="_blank" rel="noopener" aria-label="Facebook">{icon('facebook')}</a></div>
    </div>
    <form class="rq reveal" id="request-form" action="/call/request" method="post" novalidate data-rq>
      <input type="hidden" name="request_part[select_car_type]" value="1">
      <div class="steps" role="list">{steps}</div>

      <div class="rq__panel is-active" data-panel="1">
        <div class="rq__title"><span>Ваш автомобиль</span><button class="rq__switch" type="button" data-mode-toggle>Не нашли свой автомобиль?</button></div>
        <div data-mode="select">
          <div class="form-grid form-grid--2">
            <div class="field"><label class="field__label" for="tecdoc_car_brand">Марка автомобиля <span class="req">*</span></label><select class="select" id="tecdoc_car_brand" name="request_part[tecdoc_car_brand]"><option value="-1">Выберите марку</option>{brands}</select><span class="field__error">Укажите марку автомобиля</span></div>
            <div class="field"><label class="field__label" for="tecdoc_car_model">Модель <span class="req">*</span></label><select class="select" id="tecdoc_car_model" name="request_part[tecdoc_car_model]" disabled><option value="-1">Выберите модель</option></select><span class="field__error">Укажите модель автомобиля</span></div>
            <div class="field"><label class="field__label" for="tecdoc_car_year">Год выпуска <span class="req">*</span></label><select class="select" id="tecdoc_car_year" name="request_part[tecdoc_car_year]" disabled><option value="-1">Выберите год</option></select><span class="field__error">Укажите год выпуска</span></div>
            <div class="field"><label class="field__label" for="tecdoc_car_type">Модификация</label><select class="select" id="tecdoc_car_type" name="request_part[tecdoc_car_type]" disabled><option value="-1">Выберите модификацию</option></select><span class="field__error">Укажите модификацию автомобиля</span></div>
          </div>
        </div>
        <div data-mode="text" hidden>
          <div class="form-grid form-grid--2">
            <div class="field"><label class="field__label" for="text_car_brand">Марка автомобиля <span class="req">*</span></label><input class="input" id="text_car_brand" name="request_part[text_car_brand]" type="text" placeholder="Введите марку"><span class="field__error">Укажите марку автомобиля</span></div>
            <div class="field"><label class="field__label" for="text_car_model">Модель <span class="req">*</span></label><input class="input" id="text_car_model" name="request_part[text_car_model]" type="text" placeholder="Введите модель"><span class="field__error">Укажите модель автомобиля</span></div>
            <div class="field"><label class="field__label" for="text_car_year">Год выпуска <span class="req">*</span></label><input class="input" id="text_car_year" name="request_part[text_car_year]" type="text" inputmode="numeric" maxlength="4" placeholder="Введите год выпуска"><span class="field__error">Укажите год выпуска</span></div>
            <div class="field"><label class="field__label" for="text_car_type">Объём двигателя <span class="req">*</span></label><input class="input" id="text_car_type" name="request_part[text_car_type]" type="text" placeholder="Введите объём двигателя"><span class="field__error">Укажите объём двигателя автомобиля</span></div>
          </div>
        </div>
        <div class="form-grid" style="margin-top:1.1rem">
          <div class="field"><label class="field__label" for="car_vin">VIN-код</label><input class="input" id="car_vin" name="request_part[car_vin]" type="text" autocomplete="off" autocorrect="off" spellcheck="false" maxlength="17" placeholder="Например: 2C4GJ453XYR693697" autocapitalize="characters"><span class="field__hint">17 символов с таблички в проёме двери или в СТС. <button class="btn btn--text" type="button" data-vin-help style="font-size:.8rem">Я не знаю, что такое VIN-код</button></span>
          <p class="form-note" data-vin-help-text hidden>VIN — уникальный идентификационный номер автомобиля из 17 знаков. По нему мы подбираем запчасти точно под вашу комплектацию. Найти его можно в свидетельстве о регистрации (СТС), ПТС или на табличке под лобовым стеклом. Если VIN под рукой нет — просто пропустите это поле.</p></div>
        </div>
        <div class="rq__actions"><button class="btn btn--primary" type="button" data-next>Вперёд {icon('arrow')}</button></div>
      </div>

      <div class="rq__panel" data-panel="2">
        <div class="rq__title"><span>Что нужно сделать?</span></div>
        <div data-parts>
          <div class="part">
            <div class="field"><label class="field__label" for="part_name_1">Запчасть №1</label><input class="input" id="part_name_1" name="request_part[parts][1][name]" type="text" placeholder="Например: противотуманные фары"><span class="field__error">Введите запрос</span></div>
            <div class="field"><label class="field__label" for="part_count_1">Кол-во, шт.</label><input class="input" id="part_count_1" name="request_part[parts][1][count]" type="number" inputmode="numeric" min="1" value="1"></div>
            <button type="button" class="part__remove" aria-label="Удалить запчасть" disabled>{icon('close')}</button>
          </div>
        </div>
        <button class="btn btn--ghost btn--sm" type="button" data-add-part>{icon('plus')} Добавить запчасть</button>
        <div class="field" style="margin-top:1.1rem"><label class="field__label" for="request_what">Или опишите задачу для автосервиса</label><textarea class="textarea" id="request_what" name="request_part[what]" rows="3" placeholder="Например: стук в передней подвеске, нужна диагностика и замена"></textarea></div>
        <div class="rq__actions"><button class="btn btn--ghost" type="button" data-prev>{icon('arrow-left')} Назад</button><button class="btn btn--primary" type="button" data-next>Вперёд {icon('arrow')}</button></div>
      </div>

      <div class="rq__panel" data-panel="3">
        <div class="rq__title"><span>Контактная информация</span></div>
        <div class="form-grid form-grid--2">
          <div class="field"><label class="field__label" for="contact_name">Ваше имя <span class="req">*</span></label><input class="input" id="contact_name" name="request_part[contact_name]" type="text" autocomplete="name" autocapitalize="words"><span class="field__error">Укажите, как к вам следует обращаться</span></div>
          <div class="field"><label class="field__label" for="contact_city">Ваш город <span class="req">*</span></label><input class="input" id="contact_city" name="request_part[city]" type="text" value="Нижний Новгород" autocomplete="address-level2"><span class="field__error">Выберите город, в котором вы находитесь</span></div>
          <div class="field"><label class="field__label" for="contact_phone">Контактный телефон <span class="req">*</span></label><input class="input" id="contact_phone" name="request_part[contact_phone]" type="tel" autocomplete="tel" data-phone><span class="field__error">Укажите контактный телефон для связи с вами</span></div>
          <div class="field"><label class="field__label" for="contact_comment">Комментарий</label><input class="input" id="contact_comment" name="request_part[comment]" type="text" placeholder="Удобное время звонка, пожелания"></div>
          <div class="field span-2"><label class="check"><input type="checkbox" name="agree" value="1"><span class="check__box">{icon('check')}</span><span>Соглашаюсь с <a href="/page/soglashenie/" target="_blank">пользовательским соглашением</a> и обработкой персональных данных</span></label><span class="field__error">Необходимо согласие</span></div>
        </div>
        <div class="form-alert" data-alert role="alert"></div>
        <div class="rq__actions"><button class="btn btn--ghost" type="button" data-prev>{icon('arrow-left')} Назад</button><button class="btn btn--primary" type="submit">{icon('send')} Отправить заявку</button></div>
      </div>

      <div class="form-success" data-success>
        <div class="form-success__icon">{icon('check')}</div>
        <h3 class="h3">Ваша заявка отправлена!</h3>
        <p class="muted">Наши менеджеры рассмотрят её в рабочие часы и свяжутся с вами.</p>
        <a class="btn btn--ghost btn--sm" href="/">На главную</a>
      </div>
    </form>
  </div>
</section>"""
