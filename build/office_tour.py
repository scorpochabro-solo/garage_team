# -*- coding: utf-8 -*-
"""Two connected views of the Garage Team reception and waiting area."""
from .layout import document


def office_tour():
    body = """<section class="office-tour" aria-labelledby="tour-heading">
  <link rel="stylesheet" href="/assets/tour/vendor/pannellum.css">
  <link rel="stylesheet" href="/assets/tour/tour.css">
  <div class="wrap">
    <a class="link-arrow" href="/#inside">← Как у нас</a>
    <h1 id="tour-heading" class="h2">По офису в 360°</h1>
  </div>
  <div id="office-panorama" aria-label="Обзор офиса на 360 градусов">
    <img class="tour-still" src="/assets/tour/reception-view.webp" alt="Приёмка Garage Team. Справа стойка, слева за ней зона ожидания." width="1100" height="619">
  </div>
  <div class="wrap">
    <nav aria-label="Точки экскурсии" class="tour-scenes">
      <a class="btn btn--ghost" href="/assets/tour/reception-view.webp" data-scene="reception" aria-current="true">У стойки</a>
      <a class="btn btn--ghost" href="/assets/tour/lounge-view.webp" data-scene="lounge">У кресел</a>
    </nav>
    <p class="tour-hint" aria-live="polite">Выберите точку, чтобы посмотреть фото.</p>
  </div>
  <script defer src="/assets/tour/vendor/pannellum.js"></script>
  <script defer src="/assets/tour/tour.js"></script>
</section>"""
    return document("Офис Garage Team в 360° | Нижний Новгород",
                    "Осмотритесь у стойки приёмки и в зоне ожидания автосервиса Garage Team.",
                    "/tour/", body, og_image="/assets/tour/reception-view.webp")
