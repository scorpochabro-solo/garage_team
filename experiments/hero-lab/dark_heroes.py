"""Five dark editorial studies, sharing the existing site's navigation and assets."""

DARK_CONCEPTS = [
    ('ignition', '06', 'Первый взгляд', 'Анфас / свет фар', 'Симметрия, автомобиль в центре и свет фар, который можно включить.'),
    ('nocturne', '07', 'Другой ракурс', 'Вид сзади / атмосфера', 'Автомобиль слева, типографика справа. Два настроения света в одном боксе.'),
    ('overhead', '08', 'Внимание к деталям', 'Вид сверху / точки внимания', 'Необычный ракурс и три интерактивные точки: двигатель, ходовая и обслуживание.'),
    ('bay', '09', 'Свой гараж', 'Профиль / рольворота', 'Длинный силуэт универсала внутри светового портала. Откройте и закройте бокс.'),
    ('closeup', '10', 'Ближе к машине', 'Макро / управляемый свет', 'Крупный план оптики и металла. Проведите светом по деталям автомобиля.'),
]


def dark_heroes(picture, cta, motion_controls, arrow):
    return {
        'ignition': f'''<section class="hero ignition dark-hero" id="hero-scene" data-parallax data-lights="on" aria-labelledby="hero-title">
          <div class="dark-meta"><span>Нижний Новгород</span><span>Ваш автомобиль. Наше внимание.</span><span>С 2016 года</span></div>
          <div class="ignition-halo" data-depth="0.25" aria-hidden="true"></div>
          <div class="ignition-heading"><p class="dark-kicker">GARAGE TEAM / CAR SERVICE</p><h1 id="hero-title">С ПЕРВОГО <br><em>ВЗГЛЯДА.</em></h1></div>
          <div class="ignition-car" data-depth="1.3">{picture('ignition')}
            <span class="headlamp headlamp--left" aria-hidden="true"></span><span class="headlamp headlamp--right" aria-hidden="true"></span>
          </div>
          <div class="ignition-copy"><span class="section-mark">01 — ВНИМАНИЕ</span><p>Вы чувствуете свою машину.<br>Мы понимаем, что ей нужно.</p></div>
          <button class="effect-button light-switch" type="button" data-headlights aria-pressed="true"><span class="light-icon" aria-hidden="true">{arrow}</span>Свет фар <span data-headlight-label>вкл.</span></button>
          <div class="ignition-bottom"><span class="dark-note">Диагностика / обслуживание / ремонт</span>{cta()}<span class="dark-note">Красная слобода, 9</span></div>
        </section>{motion_controls(True)}''',

        'nocturne': f'''<section class="hero nocturne dark-hero" id="hero-scene" data-parallax data-light-tone="warm" aria-labelledby="hero-title">
          <div class="nocturne-wash" aria-hidden="true"></div><div class="nocturne-line" data-depth="0.3" aria-hidden="true"></div>
          <div class="dark-meta"><span>GARAGE TEAM</span><span>Сервис с вашим характером</span><span>Нижний Новгород</span></div>
          <span class="nocturne-word" aria-hidden="true">garage.</span>
          <div class="nocturne-car" data-depth="1.3">{picture('nocturne')}</div>
          <div class="nocturne-copy"><p class="dark-kicker">СВОИ ЛЮДИ. СВОЁ МЕСТО.</p><h1 id="hero-title">СВОЙ СЕРВИС.<br><em>СВОЙ <br>ХАРАКТЕР.</em></h1><p class="dark-description">Заботу о машине оставьте нам.<br>Всё остальное — впереди.</p>{cta()}</div>
          <div class="tone-control"><span class="control-caption">Свет в боксе</span><div class="tone-buttons" role="group" aria-label="Свет в боксе"><button type="button" data-tone="warm" aria-pressed="true">Тёплый</button><button type="button" data-tone="cool" aria-pressed="false">Холодный</button></div></div>
          <div class="nocturne-footer"><span>Премиальные автомобили</span><span>С 2016 года</span></div>
        </section>{motion_controls(True)}''',

        'overhead': f'''<section class="hero overhead dark-hero" id="hero-scene" data-parallax aria-labelledby="hero-title">
          <div class="overhead-lines" data-depth="0.2" aria-hidden="true"></div>
          <div class="overhead-copy"><p class="dark-kicker">GARAGE TEAM / ВНИМАНИЕ К ДЕТАЛЯМ</p><h1 id="hero-title">ВИДИМ<br><em>БОЛЬШЕ.</em></h1><p class="dark-description">За каждой деталью — целая машина.<br>За вашей машиной — наша команда.</p>{cta()}</div>
          <div class="overhead-stage" data-depth="0.7"><span class="overhead-ring" aria-hidden="true"></span>{picture('overhead')}
            <div class="car-points" role="group" aria-label="Выберите направление сервиса">
              <button class="car-point car-point--engine" type="button" data-car-point="engine" aria-label="Двигатель" aria-pressed="true" aria-controls="point-panel"><span>01</span><span class="point-label">Двигатель</span></button>
              <button class="car-point car-point--chassis" type="button" data-car-point="chassis" aria-label="Ходовая" aria-pressed="false" aria-controls="point-panel"><span>02</span><span class="point-label">Ходовая</span></button>
              <button class="car-point car-point--care" type="button" data-car-point="care" aria-label="Обслуживание" aria-pressed="false" aria-controls="point-panel"><span>03</span><span class="point-label">Обслуживание</span></button>
            </div>
          </div>
          <div class="point-panel" id="point-panel" aria-live="polite"><span class="section-mark" data-point-number>01 / ДВИГАТЕЛЬ</span><h2 data-point-title>Начать с причины.</h2><p data-point-copy>Необычный звук, потеря тяги или индикатор на панели — повод для диагностики.</p><a href="/services.html">Посмотреть услуги {arrow}</a></div>
          <span class="overhead-caption dark-note">Нажмите на точку — узнайте больше</span>
        </section>{motion_controls(True)}''',

        'bay': f'''<section class="hero bay dark-hero" id="hero-scene" data-parallax data-gate="open" aria-labelledby="hero-title">
          <div class="bay-top"><p class="dark-kicker">НИЖНИЙ НОВГОРОД / КРАСНАЯ СЛОБОДА, 9</p><span>С 2016 года</span></div>
          <div class="bay-heading"><h1 id="hero-title">СВОЙ <em>ГАРАЖ.</em></h1><p>Место, где вашу машину<br>понимают с полуслова.</p></div>
          <div class="bay-portal"><div class="bay-backwall" aria-hidden="true"></div><div class="bay-toplight" aria-hidden="true"></div>
            <div class="bay-car" data-depth="1.2">{picture('bay')}</div>
            <div class="bay-shutter" id="bay-door" aria-hidden="true"><span>GARAGE TEAM</span></div>
          </div>
          <div class="bay-bottom"><div class="bay-guarantee"><strong>1 <small>год</small></strong><span>гарантия на все<br>выполненные работы</span></div>{cta()}<button class="effect-button gate-switch" type="button" data-gate-toggle aria-expanded="true" aria-controls="bay-door"><span class="gate-symbol" aria-hidden="true"></span><span data-gate-label>Закрыть бокс</span></button></div>
        </section>{motion_controls(True)}''',

        'closeup': f'''<section class="hero closeup dark-hero" id="hero-scene" data-parallax aria-labelledby="hero-title">
          <div class="detail-stage" data-depth="1.1">{picture('closeup', 'scene-image')}<div class="detail-spot" aria-hidden="true"></div></div>
          <div class="detail-shade" aria-hidden="true"></div>
          <div class="detail-top"><p class="dark-kicker">GARAGE TEAM / CAR SERVICE</p><span>Внимание — в каждой детали.</span></div>
          <div class="detail-heading"><h1 id="hero-title">СМОТРИМ<br><em>ГЛУБЖЕ.</em></h1></div>
          <div class="detail-bottom"><div><p>Ваша машина заслуживает<br>внимания к мелочам.</p>{cta()}</div><label class="detail-control"><span>Проведите светом по кузову</span><input type="range" min="15" max="95" value="68" data-detail-light aria-label="Положение света на автомобиле"><span class="detail-scale" aria-hidden="true"><span>СВЕТ</span><span>← →</span></span></label></div>
          <span class="detail-side dark-note">ДИАГНОСТИКА / ОБСЛУЖИВАНИЕ / РЕМОНТ</span>
        </section>{motion_controls(True)}''',
    }
