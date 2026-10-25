"""Close editorial studies: fixed copy, five photographic compositions."""

CLOSE_CONCEPTS = [
    ('mint', '11', 'Мятный свет', 'Оптика / неон', 'Крупная фара, зелёный металл и настоящие контуры вывески.'),
    ('copper', '12', 'Тёплый металл', 'Колесо / кирпич', 'Многоспицевый диск крупным планом и тёплая кирпичная стена.'),
    ('scarlet', '13', 'Красная линия', 'Задний фонарь / контраст', 'Красный свет фонаря, чёрный кузов и мятная вывеска.'),
    ('graphite', '14', 'Чёрный хром', 'Решётка / фронтальный ракурс', 'Весь экран — фактура металла. Кирпич и вывеска над автомобилем.'),
    ('vault', '15', 'Своя территория', 'Макро / типографика', 'Оптика в упор, кирпичный простенок и крупная типографика.'),
]


def close_header():
    links = '<a href="/services.html">Услуги</a><a href="/contacts/">Контакты</a>'
    return f'''<a class="skip" href="#main">К содержанию</a><header class="header">
      <a class="brand" href="/" aria-label="Garage Team — главная"><img src="assets/logo.svg" width="124" height="45" alt="Garage Team"></a>
      <nav class="desktop-nav" aria-label="Основное меню">{links}</nav>
      <a class="header-phone" href="tel:+78314161677">(831) 416-16-77</a>
      <details class="mobile-menu"><summary>Меню <span aria-hidden="true">+</span></summary><nav aria-label="Мобильное меню">{links}<a href="tel:+78314161677">Позвонить</a></nav></details>
    </header>'''


def close_heroes(picture, cta, asset_url):
    result = {}
    for key, *_ in CLOSE_CONCEPTS:
        result[key] = f'''<section class="hero close-scene close-{key}" id="hero-scene" data-parallax aria-labelledby="hero-title">
          <div class="close-media" data-depth="1.1">{picture(key, 'scene-image')}</div>
          <div class="close-wall" aria-hidden="true"></div><div class="close-shade" aria-hidden="true"></div>
          <div class="close-sign" data-depth="0.3" aria-hidden="true"><img src="{asset_url('close-neon.svg')}" alt="" width="396" height="138"></div>
          <div class="close-copy"><h1 id="hero-title"><span>Сервис</span> <span>премиальных</span> <span>автомобилей.</span></h1></div>
          <div class="close-action">{cta('Записаться')}<a class="close-address" href="/contacts/">Нижний Новгород<br><span>Красная слобода, 9 ↗</span></a></div>
        </section>'''
    return result
