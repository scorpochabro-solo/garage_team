/* ============================================================
   horizontal sliders (scroll-snap + drag) and lightbox
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};

  /* ---------- sliders ---------- */
  document.querySelectorAll('[data-slider]').forEach((slider) => {
    const track = slider.querySelector('.slider__track');
    if (!track) return;
    const prev = slider.querySelector('[data-prev]');
    const next = slider.querySelector('[data-next]');
    const step = () => Math.max(track.clientWidth * 0.72, 280);
    const behavior = G.reducedMotion ? 'auto' : 'smooth';
    if (prev) prev.addEventListener('click', () => track.scrollBy({ left: -step(), behavior }));
    if (next) next.addEventListener('click', () => track.scrollBy({ left: step(), behavior }));
    const update = () => {
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
    };
    track.addEventListener('scroll', update, { passive: true });
    addEventListener('resize', update, { passive: true });
    update();

    let down = false, startX = 0, startLeft = 0, moved = false;
    track.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse') return;
      down = true; moved = false; startX = e.clientX; startLeft = track.scrollLeft;
      track.classList.add('is-dragging');
    });
    addEventListener('pointermove', (e) => {
      if (!down) return;
      const dx = e.clientX - startX;
      if (Math.abs(dx) > 4) moved = true;
      track.scrollLeft = startLeft - dx;
    });
    addEventListener('pointerup', () => { if (!down) return; down = false; track.classList.remove('is-dragging'); });
    track.addEventListener('click', (e) => { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);
  });

  /* ---------- lightbox ---------- */
  const links = Array.from(document.querySelectorAll('a[data-lightbox]'));
  const dlg = document.getElementById('lightbox');
  if (!links.length || !dlg || typeof dlg.showModal !== 'function') return;
  const img = dlg.querySelector('.lightbox__img');
  const counter = dlg.querySelector('.lightbox__count');
  const groups = {};
  links.forEach((l) => { (groups[l.dataset.lightbox] = groups[l.dataset.lightbox] || []).push(l); });
  let group = [];
  let idx = 0;
  const show = (i) => {
    if (!group.length) return;
    idx = (i + group.length) % group.length;
    const l = group[idx];
    img.src = l.getAttribute('href');
    const thumb = l.querySelector('img');
    img.alt = thumb && thumb.alt ? thumb.alt : 'Фото работ автотехцентра Гараж';
    counter.textContent = `${String(idx + 1).padStart(2, '0')} / ${String(group.length).padStart(2, '0')}`;
  };
  links.forEach((l) => l.addEventListener('click', (e) => {
    e.preventDefault();
    group = groups[l.dataset.lightbox];
    show(group.indexOf(l));
    if (!dlg.open) dlg.showModal();
  }));
  dlg.querySelector('[data-prev]').addEventListener('click', () => show(idx - 1));
  dlg.querySelector('[data-next]').addEventListener('click', () => show(idx + 1));
  dlg.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') show(idx - 1);
    if (e.key === 'ArrowRight') show(idx + 1);
  });
  dlg.addEventListener('click', (e) => { if (e.target === dlg || e.target.classList.contains('lightbox__stage')) dlg.close(); });
  let tx = 0;
  dlg.addEventListener('touchstart', (e) => { tx = e.touches[0].clientX; }, { passive: true });
  dlg.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 40) show(dx < 0 ? idx + 1 : idx - 1);
  }, { passive: true });
  dlg.addEventListener('close', () => { img.removeAttribute('src'); });
})();
