#!/usr/bin/env python3
"""Build isolated hero studies into dist/hero-lab; the main site is unchanged."""
from html import escape
from pathlib import Path
import argparse
import hashlib
import re
import shutil
from PIL import Image
from dark_heroes import DARK_CONCEPTS, dark_heroes
from close_heroes import CLOSE_CONCEPTS, close_heroes, close_header
from page_studies import PAGE_CONCEPTS, page_sections, page_dock, page_gallery

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "dist" / "hero-lab"
BASE = ''
ORIGINAL_CONCEPTS = [
    ("precision", "01", "Свой подход", "Светлый индустриальный", "Скульптурный автомобиль, гигантские буквы и точная журнальная сетка."),
    ("afterhours", "02", "Характер в деталях", "Кинематографичный", "Глубокий чёрный, зелёный универсал Alpina и свет, который собирает форму автомобиля."),
    ("engineering", "03", "Точность в основе", "Инженерный", "Чистый профиль Alpina, диагональная архитектура и техническая графика."),
    ("motion", "04", "Продолжение движения", "Динамичный", "Светлый fashion-постер: красные шлейфы, воздух и огромная типографика."),
    ("atelier", "05", "Место силы", "Параллакс-ателье", "Кирпич, тёплый свет и автомобиль между слоями. Двигается от курсора и прокрутки."),
]
CONCEPTS = ORIGINAL_CONCEPTS + DARK_CONCEPTS + CLOSE_CONCEPTS
DARK_KEYS = {concept[0] for concept in DARK_CONCEPTS}
CLOSE_KEYS = {concept[0] for concept in CLOSE_CONCEPTS}
PAGE_KEYS = {concept[0] for concept in PAGE_CONCEPTS}
ARROW = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="1.5"/></svg>'
DIAG = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 19 19 5M5 5h14v14" stroke="currentColor" stroke-width="1.5"/></svg>'


def cta(label="Записаться в сервис"):
    return f'<a class="cta" href="/call/request/">{label}<span>{ARROW}</span></a>'


def header():
    links = '<a href="/services.html">Услуги</a><a href="/about/">О сервисе</a><a href="/contacts/">Контакты</a>'
    return f'''<a class="skip" href="#main">К содержанию</a>
    <header class="header">
      <a class="brand" href="/" aria-label="Garage Team — главная"><img src="assets/logo.svg" width="124" height="45" alt="Garage Team"></a>
      <nav class="desktop-nav" aria-label="Основное меню">{links}</nav>
      <a class="header-phone" href="tel:+78314161677">(831) 416-16-77</a>
      <a class="header-request" href="/call/request/">Записаться {DIAG}</a>
      <details class="mobile-menu"><summary>Меню <span aria-hidden="true">+</span></summary><nav aria-label="Мобильное меню">{links}<a href="tel:+78314161677">Позвонить</a></nav></details>
    </header>'''


def dock(active):
    series = CLOSE_CONCEPTS if active in CLOSE_KEYS else DARK_CONCEPTS if active in DARK_KEYS else ORIGINAL_CONCEPTS
    links = ''.join(f'<a href="{key}.html" aria-label="Вариант {num}: {title}"'+(' aria-current="page"' if key == active else '')+f'>{num}</a>' for key, num, title, _, _ in series)
    return f'<nav class="lab-dock" aria-label="Варианты первого экрана"><a class="dock-home" href="index.html" aria-label="Все варианты">{ARROW}<span>Все</span></a>{links}</nav>'


def continuation():
    return f'''<section class="continuation" id="approach" aria-labelledby="approach-title">
      <div><p class="eyebrow">GARAGE TEAM / С 2016 ГОДА</p><h2 id="approach-title">У вашей машины<br>есть характер.<br><em>У нас — подход.</em></h2></div>
      <div class="continuation-copy"><p>Диагностика, обслуживание и ремонт премиальных автомобилей в Нижнем Новгороде. Работаем с запчастями от проверенных поставщиков.</p>
        <a href="/services.html">Все услуги {ARROW}</a><a href="/about/">Познакомиться с командой {ARROW}</a><a href="/moya-mashina/">Сервисная книжка автомобиля {ARROW}</a>
        <p class="address">Красная слобода, 9<br>Пн–Пт 09:00–19:00 · Сб–Вс выходные</p>
      </div>
    </section><footer class="study-footer"><span>GARAGE TEAM</span><span>Концепт первого экрана · AI-визуализация автомобиля</span><a href="index.html">К вариантам ↑</a></footer>'''


def asset_url(name):
    version = hashlib.sha256((HERE / 'assets' / name).read_bytes()).hexdigest()[:10]
    output_name = str(Path(name).with_suffix('.webp')) if name.endswith('.png') else name
    return f'assets/{output_name}?v={version}'


def rebase_html(html):
    """Prefix site links, including URLs used by the service selector."""
    return re.sub(r'(\b(?:href|src|data-service-url)=[\"\'])/(?!/)', lambda match: match[1] + BASE + '/', html)


def picture(key, cls="car-image", extra=""):
    model = 'Alpina B3 Touring, универсал' if key == 'afterhours' or key in DARK_KEYS else 'Alpina B3'
    if key == 'closeup':
        model = 'Фара и переднее крыло Alpina B3 Touring крупным планом'
    if key in CLOSE_KEYS:
        model = {'mint':'Фара Alpina в мятном свете', 'copper':'Диск и крыло Alpina у кирпичной стены', 'scarlet':'Задний фонарь Alpina крупным планом', 'graphite':'Чёрная решётка Alpina анфас', 'vault':'Фара и капот Alpina у кирпичного простенка'}[key]
    return f'<img class="{cls}" src="{asset_url(key + ".png")}" alt="{model} — концептуальная визуализация" fetchpriority="high" decoding="async" {extra}>'


def motion_controls(below_hero=False):
    cls = 'parallax-controls parallax-settings' if below_hero else 'parallax-controls'
    return f'''<div class="{cls}"><button type="button" data-motion-toggle aria-controls="hero-scene" aria-pressed="true">Параллакс <span data-motion-label>вкл.</span><i aria-hidden="true"></i></button><span class="mono" data-motion-hint>ДВИГАЙТЕ КУРСОРОМ / ЛИСТАЙТЕ</span></div>'''


def heroes():
    return {
        "precision": f'''<section class="hero precision" id="hero-scene" data-parallax aria-labelledby="hero-title">
        <div class="precision-top"><p class="eyebrow">АВТОСЕРВИС / НИЖНИЙ НОВГОРОД</p><span class="mono">ОТНОШЕНИЕ РЕШАЕТ.</span></div>
        <div class="giant-word" data-depth="0.3" aria-hidden="true">GARAGE</div>
        <div class="precision-circle" aria-hidden="true">G<span>®</span></div>
        <div class="precision-car" data-depth="1.3">{picture('precision')}</div>
        <div class="hero-copy"><h1 id="hero-title">СВОЙ<br>ПОДХОД<span class="green-dot">.</span></h1><p>К вашей машине.<br>К каждой детали. К вам.</p>{cta()}</div>
        <div class="hero-baseline"><span>ПРЕМИАЛЬНЫЕ АВТОМОБИЛИ</span><span>С 2016 ГОДА</span><a href="#approach">НАШ ПОДХОД ↓</a></div>
        </section>{motion_controls(True)}''',
        "afterhours": f'''<section class="hero afterhours" id="hero-scene" data-parallax aria-labelledby="hero-title">
        <div class="cinema-image" data-depth="1.25">{picture('afterhours', 'scene-image')}</div><div class="cinema-shade" aria-hidden="true"></div>
        <div class="cinema-coordinate">С 2016 ГОДА / GARAGE TEAM<span>НИЖНИЙ НОВГОРОД</span></div>
        <div class="hero-copy"><p class="eyebrow">GARAGE TEAM / CAR SERVICE</p><h1 id="hero-title">ХАРАКТЕР<br>В <em>ДЕТАЛЯХ.</em></h1><p>Вы чувствуете свою машину.<br>Мы понимаем, что ей нужно.</p>{cta()}</div>
        <div class="cinema-side mono" aria-hidden="true">CRAFTED TO CARE / EST. 2016</div>
        <div class="cinema-bottom"><div><strong>1 <small>год</small></strong><span>гарантия на все<br>выполненные работы</span></div><p>ДИАГНОСТИКА<br>ОБСЛУЖИВАНИЕ<br>РЕМОНТ</p><a class="round-link" href="#approach" aria-label="Узнать о нашем подходе">{ARROW}</a></div>
        </section>{motion_controls(True)}''',
        "engineering": f'''<section class="hero engineering" id="hero-scene" data-parallax aria-labelledby="hero-title">
        <div class="engineering-stripe" aria-hidden="true"></div><div class="technical-grid" data-depth="0.2" aria-hidden="true"></div>
        <div class="engineering-heading"><p class="eyebrow">СИСТЕМНЫЙ ПОДХОД К ВАШЕМУ АВТОМОБИЛЮ</p><h1 id="hero-title">ТОЧНОСТЬ.<br><em>В ОСНОВЕ ВСЕГО.</em></h1></div>
        <span class="engineering-index" data-depth="0.35" aria-hidden="true">B3</span>
        <div class="profile-car" data-depth="1.2">{picture('engineering')}<div class="measurement" aria-hidden="true"><span>ТОЧНОСТЬ В КАЖДОЙ ДЕТАЛИ</span></div></div>
        <div class="engineering-bottom"><p>Диагностика, обслуживание и ремонт<br>премиальных автомобилей.<br><span>Нижний Новгород · с 2016 года</span></p>{cta('Доверить автомобиль')}<a class="engineering-scroll mono" href="#approach">ИЗУЧИТЬ ПОДХОД ↓</a></div>
        </section>{motion_controls(True)}''',
        "motion": f'''<section class="hero motion" id="hero-scene" data-parallax aria-labelledby="hero-title">
        <div class="motion-image" data-depth="1.25">{picture('motion', 'scene-image')}</div>
        <div class="hero-copy"><p class="eyebrow">GARAGE TEAM / НА ВАШЕЙ СТОРОНЕ</p><h1 id="hero-title">Чтобы<br>движение<br><em>продолжалось.</em></h1><p>Заботу о машине оставьте нам.<br>Всё остальное — впереди.</p>{cta()}</div>
        <div class="motion-caption mono"><svg class="motion-star" viewBox="0 0 40 40" aria-hidden="true"><path d="M20 2v36M2 20h36M7 7l26 26M7 33 33 7" fill="none" stroke="currentColor" stroke-width="1.5"/></svg> ЗАБОТА О МАШИНЕ.<br>СВОБОДА ДЛЯ ВАС.</div>
        <div class="motion-word" data-depth="0.3" aria-hidden="true">garage<span>®</span></div>
        <div class="hero-baseline"><span>CAR SERVICE / НИЖНИЙ НОВГОРОД</span><a href="#approach">ДАЛЬШЕ — БОЛЬШЕ ↓</a></div>
        </section>{motion_controls(True)}''',
        "atelier": f'''<section class="hero atelier" id="hero-scene" data-parallax aria-labelledby="hero-title">
        <div class="atelier-brick" data-depth="0.3" aria-hidden="true"></div>
        <div class="atelier-portal" data-depth="0.55" aria-hidden="true"><div class="portal-light"></div><span class="mono">GARAGE / 2016</span></div>
        <div class="atelier-orbit" data-depth="0.8" aria-hidden="true"></div>
        <div class="atelier-heading" data-depth="0.4"><p class="eyebrow">ВАШ АВТОМОБИЛЬ. В СВОЁМ МЕСТЕ.</p><h1 id="hero-title">МЕСТО<br><em>СИЛЫ.</em></h1></div>
        <div class="atelier-car" data-depth="1.5">{picture('atelier')}</div>
        <div class="atelier-plaque" data-depth="2"><span class="mono">ЗНАК КАЧЕСТВА / GARAGE TEAM</span><strong>1 <i>год</i></strong><p>гарантия на все<br>выполненные работы</p></div>
        <div class="atelier-bottom"><p>Сервис для тех, кто любит свою машину.<br>Нижний Новгород. Красная слобода, 9.</p>{cta()}</div>
        {motion_controls()}
        </section>''',
    }


def document(title, body, theme, hero_image=None):
    version = hashlib.sha256((HERE / 'style.css').read_bytes() + (HERE / 'script.js').read_bytes()).hexdigest()[:10]
    preload = f'<link rel="preload" as="image" href="{asset_url(hero_image + ".png")}">' if hero_image else ''
    extra_styles = extra_script = extra_class = ''
    if theme in DARK_KEYS:
        dark_version = hashlib.sha256((HERE / 'dark.css').read_bytes() + (HERE / 'dark.js').read_bytes()).hexdigest()[:10]
        extra_styles = f'<link rel="stylesheet" href="dark.css?v={dark_version}">'
        extra_script = f'<script src="dark.js?v={dark_version}" defer></script>'
        extra_class = ' dark-edition'
    if theme in CLOSE_KEYS or theme in PAGE_KEYS or theme == 'pages':
        close_version = hashlib.sha256((HERE / 'close.css').read_bytes()).hexdigest()[:10]
        extra_styles = f'<link rel="stylesheet" href="close.css?v={close_version}">'
        extra_class = ' close-edition'
    if theme in PAGE_KEYS or theme == 'pages':
        page_version = hashlib.sha256((HERE / 'pages.css').read_bytes() + (HERE / 'pages.js').read_bytes()).hexdigest()[:10]
        extra_styles += f'<link rel="stylesheet" href="pages.css?v={page_version}">'
        extra_script = f'<script src="pages.js?v={page_version}" defer></script>'
        extra_class += ' page-edition'
    if theme.startswith('copper-'):
        copper_version = hashlib.sha256((HERE / 'copper-pages.css').read_bytes()).hexdigest()[:10]
        extra_styles += f'<link rel="stylesheet" href="copper-pages.css?v={copper_version}">'
        extra_class += ' copper-page'
    return rebase_html(f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#101310"><title>{escape(title)} — Garage Team</title>
<link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="fonts.css"><link rel="stylesheet" href="style.css?v={version}">{extra_styles}{preload}
<script src="script.js?v={version}" defer></script>{extra_script}</head><body class="theme-{theme}{extra_class}">{body}</body></html>''')


def gallery_cards(concepts):
    cards = ''
    for key, num, title, subtitle, desc in concepts:
        thumb = f'thumb-{key}.jpg'
        fallback = ('copper' if key.startswith('copper-') else 'mint') if key in PAGE_KEYS else key
        cover = thumb if (HERE / 'assets' / thumb).exists() else f'{fallback}.png'
        cards += f'''<a class="study-card study-card--{key}" href="{key}.html"><div class="study-cover"><img src="{asset_url(cover)}" width="1440" height="1000" alt="Первый экран: {title}" loading="lazy"><span class="study-open">Открыть {DIAG}</span></div><div class="study-info"><span class="study-number">{num}</span><div><p class="eyebrow">{subtitle}</p><h3>{title}</h3><p>{desc}</p></div>{DIAG}</div></a>'''
    return cards


def gallery():
    return f'''<header class="gallery-header"><a href="/" aria-label="Главная Garage Team"><img src="assets/logo.svg" width="124" height="45" alt="Garage Team"></a><span class="mono">CREATIVE DIRECTION / 2026</span><a href="/">Текущий сайт {DIAG}</a></header>
    <main id="main" class="gallery-main"><section class="gallery-intro"><p class="eyebrow">GARAGE TEAM / 23 ВАРИАНТА</p><h1>ВЫБЕРИТЕ<br><span>СВОЙ ГАРАЖ.</span></h1><nav class="series-nav" aria-label="Серии концепций"><a href="pages.html">16–23 / Первый экран + три блока →</a><a href="#close-series">11–15 / Крупным планом ↓</a><a href="#dark-series">06–10 / Тёмная серия ↓</a><a href="#original-series">01–05 / Первая серия ↓</a></nav></section>
    <section id="full-pages" class="gallery-series" aria-labelledby="full-pages-title"><div class="series-heading"><h2 id="full-pages-title">За первым экраном.</h2><p>Восемь страниц: первый экран, услуги, гарантия и запись.<br><a href="pages.html">Сравнить продолжения →</a></p></div><div class="studies">{gallery_cards(PAGE_CONCEPTS[5:] + PAGE_CONCEPTS[:5])}</div></section>
    <section id="close-series" class="gallery-series" aria-labelledby="close-series-title"><div class="series-heading"><h2 id="close-series-title">Крупным планом.</h2><p>Кирпич, неон и минимум слов.<br><a href="pages.html">Восемь страниц с продолжением →</a></p></div><div class="studies">{gallery_cards(CLOSE_CONCEPTS)}</div></section>
    <section id="dark-series" class="gallery-series" aria-labelledby="dark-series-title"><div class="series-heading"><h2 id="dark-series-title">После заката.</h2><p>Пять новых ракурсов. Пять способов взаимодействовать.</p></div><div class="studies">{gallery_cards(DARK_CONCEPTS)}</div></section>
    <section id="original-series" class="gallery-series" aria-labelledby="original-series-title"><div class="series-heading"><h2 id="original-series-title">Первая коллекция.</h2><p>Светлый индустриальный, кинематографичный и три других характера.</p></div><div class="studies">{gallery_cards(ORIGINAL_CONCEPTS)}</div></section></main>
    <footer class="gallery-footer"><p>Автомобили — сгенерированные концептуальные иллюстрации.</p><p>Параллакс есть во всех вариантах. Попробуйте движение мыши и прокрутку.</p><a href="/">Открыть текущий сайт {ARROW}</a></footer>'''


def main():
    global OUT, BASE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='', help='Site URL prefix, e.g. /garage_team')
    parser.add_argument('--out', type=Path, default=OUT, help='Output directory for the lab only')
    parser.add_argument('--site-root', type=Path, default=ROOT / 'dist', help='Built main site providing font rules')
    args = parser.parse_args()
    BASE = args.base.rstrip('/')
    if BASE and (not BASE.startswith('/') or not re.fullmatch(r'/[A-Za-z0-9_/-]+', BASE)):
        parser.error('--base must be a path prefix such as /garage_team')
    OUT = args.out.resolve()
    site_css = args.site_root / 'assets/css/site.css'
    if not site_css.exists():
        raise SystemExit(f'Built site CSS not found: {site_css}')
    missing = [key for key, *_ in CONCEPTS if not (HERE / f'assets/{key}.png').exists()]
    if missing:
        raise SystemExit('Missing generated assets: ' + ', '.join(missing))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    for source in (HERE / 'assets').iterdir():
        if not source.is_file():
            continue
        if source.suffix == '.png':
            target = OUT / 'assets' / source.with_suffix('.webp').name
            # A fresh Git checkout can make an old WebP newer than its edited PNG.
            with Image.open(source) as image:
                image.save(target, 'WEBP', quality=90, method=6)
        else:
            shutil.copy(source, OUT / 'assets' / source.name)
    shutil.copy(ROOT / 'src/assets/logo/logo.svg', OUT / 'assets/logo.svg')
    for name in ('style.css', 'script.js', 'dark.css', 'dark.js', 'close.css', 'pages.css', 'pages.js', 'copper-pages.css'):
        shutil.copy(HERE / name, OUT / name)
    font_rules = '\n'.join(line for line in site_css.read_text().splitlines() if line.startswith('@font-face'))
    # Font URLs can already carry the main build's base path.
    font_rules = re.sub(r'url\(([\"\']?)/[^)\"\']*?/assets/', lambda match: 'url(' + match[1] + '/assets/', font_rules)
    font_rules = re.sub(r'url\(([\"\']?)/assets/', lambda match: 'url(' + match[1] + BASE + '/assets/', font_rules)
    (OUT / 'fonts.css').write_text(font_rules + '\n')
    all_heroes = heroes()
    all_heroes.update(dark_heroes(picture, cta, motion_controls, ARROW))
    all_heroes.update(close_heroes(picture, cta, asset_url))
    for key, _, title, _, _ in CONCEPTS:
        if key in CLOSE_KEYS:
            body = close_header() + '<main id="main">' + all_heroes[key] + dock(key) + motion_controls(True) + continuation() + '</main>'
        else:
            body = header() + '<main id="main">' + all_heroes[key] + continuation() + '</main>' + dock(key)
        (OUT / f'{key}.html').write_text(document(title, body, key, key))
    for key, _, title, _, _ in PAGE_CONCEPTS:
        hero = 'copper' if key.startswith('copper-') else 'mint'
        number = '12' if hero == 'copper' else '11'
        navigation = close_header().replace('href="/services.html"', 'href="#services"').replace('href="/contacts/"', 'href="#visit"')
        body = navigation + '<main id="main">' + all_heroes[hero] + page_sections(key, asset_url, cta, ARROW) + '</main>'
        body += page_dock(key, ARROW) + motion_controls(True)
        body += f'<footer class="study-footer"><a href="pages.html">Все варианты страницы</a><span>Концепт · AI-визуализации автомобиля</span><a href="{hero}.html">Исходный №{number}</a></footer>'
        (OUT / f'{key}.html').write_text(document(title, body, key, hero))
    available_assets = {path.name for path in (HERE / 'assets').iterdir()}
    (OUT / 'pages.html').write_text(document('Восемь страниц с продолжением', page_gallery(asset_url, ARROW, available_assets), 'pages'))
    (OUT / 'index.html').write_text(document('Первые экраны', gallery(), 'gallery'))
    print(f'Built {len(CONCEPTS)} heroes, {len(PAGE_CONCEPTS)} page studies + two galleries: {OUT}')


if __name__ == '__main__':
    main()
