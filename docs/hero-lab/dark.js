/* Optional visual controls never intercept navigation or native scrolling. */
(() => {
  'use strict';
  const scene = document.querySelector('.dark-hero');
  if (!scene) return;

  const headlights = scene.querySelector('[data-headlights]');
  if (headlights) headlights.addEventListener('click', () => {
    const on = headlights.getAttribute('aria-pressed') !== 'true';
    scene.dataset.lights = on ? 'on' : 'off';
    headlights.setAttribute('aria-pressed', String(on));
    headlights.querySelector('[data-headlight-label]').textContent = on ? 'вкл.' : 'выкл.';
  });

  const tones = scene.querySelectorAll('[data-tone]');
  tones.forEach(button => button.addEventListener('click', () => {
    scene.dataset.lightTone = button.dataset.tone;
    tones.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  }));

  const points = {
    engine: {number:'01 / ДВИГАТЕЛЬ', title:'Начать с причины.', copy:'Необычный звук, потеря тяги или индикатор на панели — повод для диагностики.'},
    chassis: {number:'02 / ХОДОВАЯ', title:'Чувствовать дорогу.', copy:'Подвеска, рулевое управление и тормоза. Обратите внимание, если привычные ощущения за рулём изменились.'},
    care: {number:'03 / ОБСЛУЖИВАНИЕ', title:'Заботиться вовремя.', copy:'Масло, фильтры и другие расходные материалы. Плановое обслуживание вашей машины.'},
  };
  const pointButtons = scene.querySelectorAll('[data-car-point]');
  pointButtons.forEach(button => button.addEventListener('click', () => {
    const point = points[button.dataset.carPoint];
    scene.querySelector('[data-point-number]').textContent = point.number;
    scene.querySelector('[data-point-title]').textContent = point.title;
    scene.querySelector('[data-point-copy]').textContent = point.copy;
    pointButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  }));

  const gate = scene.querySelector('[data-gate-toggle]');
  if (gate) gate.addEventListener('click', () => {
    const open = gate.getAttribute('aria-expanded') !== 'true';
    scene.dataset.gate = open ? 'open' : 'closed';
    gate.setAttribute('aria-expanded', String(open));
    gate.querySelector('[data-gate-label]').textContent = open ? 'Закрыть бокс' : 'Открыть бокс';
  });

  const light = scene.querySelector('[data-detail-light]');
  if (light) light.addEventListener('input', () => {
    scene.style.setProperty('--detail-light-x', `${light.value}%`);
  });
})();
