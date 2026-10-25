"""Eight page studies, each with the selected hero and three useful sections."""
from html import escape

PAGE_CONCEPTS = [
    ('mint-film', '16', 'Кинолента', 'Кадры во всю ширину', 'Двигатель, тормозной диск и салон. Три крупные сцены с плавной глубиной.'),
    ('mint-grid', '17', 'Точная сборка', 'Сетка / крупные детали', 'Три направления, большой гарантийный блок и спокойная композиция записи.'),
    ('mint-chapters', '18', 'Ночной маршрут', 'Интерактивный выбор', 'Выбор услуги меняет деталь автомобиля. Затем — гарантия и адрес.'),
    ('mint-editorial', '19', 'Чёрный журнал', 'Асимметрия / типографика', 'Широкие строки услуг, узкие фотокадры и выразительный масштаб цифр.'),
    ('mint-workshop', '20', 'Внутри гаража', 'Кирпич / световые окна', 'Фрагменты автомобиля в кирпичной архитектуре и неон в конце маршрута.'),
    ('copper-panorama', '21', 'Тёплая механика', '№12 / панорамные кадры', 'Двигатель во всю ширину, оптика в кирпичной раме и тёплый салон.'),
    ('copper-sequence', '22', 'Линия света', '№12 / смена ракурса', 'Интерактивные детали, крупное колесо и асимметричная композиция записи.'),
    ('copper-collection', '23', 'Частная коллекция', '№12 / галерея деталей', 'Три разных масштаба, свет фары и неоновая вывеска на кирпиче.'),
]

SERVICES = [
    ('Диагностика', '/services/diagnostika.html', 'engine', 'Двигатель, электроника, ходовая.'),
    ('Плановое ТО', '/services/planovoe-to.html', 'wheel', 'Масло, фильтры, регламентные работы.'),
    ('Ремонт', '/services.html', 'brake', 'Двигатель, подвеска, тормоза.'),
]
ALTS = {
    'engine': 'Детали двигателя в мятном свете',
    'brake': 'Тормозной диск и суппорт крупным планом',
    'cockpit': 'Руль и кожаный салон в тёплом свете',
    'mirror': 'Кирпич и неон в отражении зелёного зеркала',
    'tailgate': 'Задний фонарь и зелёное крыло',
    'wheel': 'Многоспицевый диск и переднее крыло',
    'copper-optic': 'Оптика и зелёное крыло в медном свете',
    'copper-engine': 'Детали двигателя и зелёный край крыла',
    'copper-cabin': 'Кожаный салон и зеркало у тёплой кирпичной стены',
}


def page_sections(key, asset_url, cta, arrow):
    def photo(name, cls='', drift=True):
        filename = name if name.startswith('copper-') else 'page-' + name
        return f'<div class="fragment {cls}"' + (' data-drift' if drift else '') + f'><img src="{asset_url(filename + ".png")}" alt="{ALTS[name]} — концептуальная визуализация" width="1536" height="1024" loading="lazy" decoding="async"></div>'

    def sign():
        return f'<img class="section-neon" src="{asset_url("close-neon.svg")}" alt="" width="396" height="138" aria-hidden="true" loading="lazy">'

    def service_links(cls='service-lines'):
        links = ''.join(f'<a href="{url}">{label}{arrow}</a>' for label, url, _, _ in SERVICES)
        return f'<div class="{cls}">{links}</div>'

    def guarantee():
        return '<div class="guarantee-copy"><h2 id="approach-title"><strong>1</strong> <span>год</span></h2><p class="guarantee-label">гарантии на все работы</p><div class="parts-note"><p>Работаем с запчастями<br>от наших проверенных поставщиков.</p><a class="text-link" href="/about/#parts">Условия ремонта '+arrow+'</a></div></div>'

    def contact():
        return f'''<div class="visit-copy"><p class="section-kicker">Нижний Новгород</p><h2 id="visit-title">Красная<br>слобода, 9.</h2><div class="visit-hours"><p>Пн–Пт · 09:00–19:00</p><p>Сб–Вс · выходные</p></div><div class="visit-actions">{cta('Записаться')}<a class="visit-phone" href="tel:+78314161677">(831) 416-16-77</a></div><p class="booking-note">Запись подтверждаем по телефону.</p></div>'''

    if key == 'mint-film':
        return f'''<section id="services" class="page-section film-services full-scene" aria-labelledby="services-title">{photo('engine')}<div class="scene-shade"></div><div class="section-content"><h2 id="services-title" class="section-kicker">Услуги</h2>{service_links()}<a class="text-link" href="/services.html">Все направления {arrow}</a></div></section>
        <section id="approach" class="page-section film-guarantee full-scene" aria-labelledby="approach-title">{photo('brake')}<div class="scene-shade"></div>{guarantee()}</section>
        <section id="visit" class="page-section film-visit full-scene" aria-labelledby="visit-title">{photo('cockpit')}<div class="scene-shade"></div>{contact()}</section>'''

    if key == 'mint-grid':
        cards = ''.join(f'<a class="service-tile" href="{url}">{photo(name)}<span>{label}{arrow}</span></a>' for label, url, name, _ in SERVICES)
        return f'''<section id="services" class="page-section grid-services" aria-labelledby="services-title"><div class="section-heading"><h2 id="services-title">Услуги.</h2><a class="text-link" href="/services.html">Все направления {arrow}</a></div><div class="service-triptych">{cards}</div></section>
        <section id="approach" class="page-section grid-guarantee" aria-labelledby="approach-title">{guarantee()}{photo('mirror')}</section>
        <section id="visit" class="page-section grid-visit" aria-labelledby="visit-title">{photo('tailgate')}{contact()}</section>'''

    if key == 'mint-chapters':
        choices = ''.join(f'<button type="button" class="service-choice" aria-pressed="{str(i == 0).lower()}" aria-controls="service-detail" data-service-image="{asset_url("page-" + name + ".png")}" data-service-alt="{ALTS[name]} — концептуальная визуализация" data-service-url="{url}" data-service-description="{escape(description)}" data-service-name="{label}">{label}{arrow}</button>' for i, (label, url, name, description) in enumerate(SERVICES))
        return f'''<section id="services" class="page-section chapter-services" aria-labelledby="services-title"><div class="chapter-selection"><h2 id="services-title" class="section-kicker">Услуги</h2><div class="service-choices">{choices}</div><noscript><a class="text-link" href="/services.html">Все услуги →</a></noscript></div><div class="chapter-detail" id="service-detail">{photo('engine', drift=False)}<div class="chapter-caption" aria-live="polite"><p data-service-description-output>{SERVICES[0][3]}</p><a class="text-link" data-service-link href="{SERVICES[0][1]}" aria-label="Подробнее: Диагностика">Подробнее {arrow}</a></div></div></section>
        <section id="approach" class="page-section chapter-guarantee full-scene" aria-labelledby="approach-title">{photo('wheel')}<div class="scene-shade"></div>{guarantee()}</section>
        <section id="visit" class="page-section chapter-visit" aria-labelledby="visit-title">{contact()}{photo('cockpit')}</section>'''

    if key == 'mint-editorial':
        rows = ''.join(f'<a class="editorial-service" href="{url}"><span>{label}</span>{photo(name, drift=False)}{arrow}</a>' for label, url, name, _ in SERVICES)
        return f'''<section id="services" class="page-section editorial-services" aria-labelledby="services-title"><h2 id="services-title" class="section-kicker">Услуги</h2>{rows}</section>
        <section id="approach" class="page-section editorial-guarantee" aria-labelledby="approach-title">{photo('brake')}{guarantee()}</section>
        <section id="visit" class="page-section editorial-visit" aria-labelledby="visit-title">{photo('mirror')}{contact()}</section>'''

    if key == 'mint-workshop':
        windows = ''.join(f'<a class="workshop-window window-{i}" href="{url}">{photo(name)}<span>{label}{arrow}</span></a>' for i, (label, url, name, _) in enumerate(SERVICES))
        return f'''<section id="services" class="page-section workshop-services brick-surface" aria-labelledby="services-title"><div class="section-heading"><h2 id="services-title">Услуги.</h2><a class="text-link" href="/services.html">Все направления {arrow}</a></div><div class="workshop-windows">{windows}</div></section>
        <section id="approach" class="page-section workshop-guarantee" aria-labelledby="approach-title">{photo('cockpit')}{guarantee()}</section>
        <section id="visit" class="page-section workshop-visit full-scene" aria-labelledby="visit-title">{photo('tailgate')}<div class="scene-shade"></div>{sign()}{contact()}</section>'''
    if key == 'copper-panorama':
        return f'''<section id="services" class="page-section copper-panorama-services full-scene" aria-labelledby="services-title">{photo('copper-engine')}<div class="scene-shade"></div><div class="section-content"><h2 id="services-title" class="section-kicker">Услуги</h2>{service_links()}<a class="text-link" href="/services.html">Все направления {arrow}</a></div></section>
        <section id="approach" class="page-section copper-panel copper-brick" aria-labelledby="approach-title">{guarantee()}{photo('copper-optic')}</section>
        <section id="visit" class="page-section copper-panorama-visit full-scene" aria-labelledby="visit-title">{photo('copper-cabin')}<div class="scene-shade"></div>{contact()}</section>'''

    if key == 'copper-sequence':
        choices = ''.join(f'<button type="button" class="service-choice" aria-pressed="{str(i == 0).lower()}" aria-controls="service-detail" data-service-image="{asset_url(filename)}" data-service-alt="{ALTS[name]} — концептуальная визуализация" data-service-url="{url}" data-service-description="{escape(description)}" data-service-name="{label}">{label}{arrow}</button>' for i, ((label, url, _, description), name, filename) in enumerate(zip(SERVICES, ['copper-engine', 'wheel', 'brake'], ['copper-engine.png', 'page-wheel.png', 'page-brake.png'])))
        return f'''<section id="services" class="page-section copper-sequence-services" aria-labelledby="services-title"><h2 id="services-title">Услуги.</h2><div class="copper-selector"><div class="service-choices">{choices}</div><noscript><a class="text-link" href="/services.html">Все услуги →</a></noscript></div><div class="chapter-detail" id="service-detail">{photo('copper-engine', drift=False)}<div class="chapter-caption" aria-live="polite"><p data-service-description-output>{SERVICES[0][3]}</p><a class="text-link" data-service-link href="{SERVICES[0][1]}" aria-label="Подробнее: Диагностика">Подробнее {arrow}</a></div></div></section>
        <section id="approach" class="page-section copper-sequence-guarantee full-scene" aria-labelledby="approach-title">{photo('wheel')}<div class="scene-shade"></div>{guarantee()}</section>
        <section id="visit" class="page-section copper-sequence-visit copper-brick" aria-labelledby="visit-title"><div class="copper-visit-picture">{photo('copper-cabin')}</div>{contact()}{sign()}</section>'''

    if key == 'copper-collection':
        cards = ''.join(f'<a class="collection-card" href="{url}">{photo(name)}<span>{label}{arrow}</span></a>' for (label, url, _, _), name in zip(SERVICES, ['copper-engine', 'copper-optic', 'brake']))
        return f'''<section id="services" class="page-section copper-collection-services copper-brick" aria-labelledby="services-title"><div class="section-heading"><h2 id="services-title">Услуги.</h2><a class="text-link" href="/services.html">Все направления {arrow}</a></div><div class="collection-cards">{cards}</div></section>
        <section id="approach" class="page-section copper-collection-guarantee full-scene" aria-labelledby="approach-title">{photo('copper-optic')}<div class="scene-shade"></div>{guarantee()}</section>
        <section id="visit" class="page-section copper-collection-visit copper-brick" aria-labelledby="visit-title"><div class="collection-address">{sign()}{contact()}</div>{photo('tailgate')}</section>'''
    raise ValueError(f'Unknown page study: {key}')


def page_dock(active, arrow):
    series = [concept for concept in PAGE_CONCEPTS if concept[0].startswith(active.split('-')[0] + '-')]
    links = ''.join(f'<a href="{key}.html" aria-label="Вариант {num}: {title}"' + (' aria-current="page"' if key == active else '') + f'>{num}</a>' for key, num, title, _, _ in series)
    return f'<nav class="lab-dock page-dock" aria-label="Варианты страницы"><a class="dock-home" href="pages.html">{arrow}<span>Все</span></a>{links}</nav>'


def page_gallery(asset_url, arrow, available_assets):
    cards = ''
    for key, num, title, _, description in PAGE_CONCEPTS[5:] + PAGE_CONCEPTS[:5]:
        thumb = 'thumb-' + key + '.jpg'
        cover = thumb if thumb in available_assets else 'page-engine.png'
        cards += f'''<a class="page-study-card" href="{key}.html"><div class="page-study-cover"><img src="{asset_url(cover)}" width="1440" height="1000" alt="Продолжение №{num}: {title}" loading="lazy"></div><div class="page-study-caption"><span>{num}</span><div><h2>{title}</h2><p>{description}</p></div>{arrow}</div></a>'''
    return f'''<header class="gallery-header"><a href="index.html" aria-label="Все первые экраны"><img src="assets/logo.svg" width="124" height="45" alt="Garage Team"></a><a href="index.html">Все 23 варианта {arrow}</a></header><main class="page-gallery"><div class="page-gallery-heading"><p>№11 И №12 + ТРИ БЛОКА</p><h1>Восемь способов<br>продолжить.</h1><p>Услуги. Гарантия. Запись.</p><nav class="page-origins" aria-label="Исходные первые экраны"><a class="text-link" href="copper.html">№12 · Тёплый металл {arrow}</a><a class="text-link" href="mint.html">№11 · Мятный свет {arrow}</a></nav></div><div class="page-studies">{cards}</div></main>'''
