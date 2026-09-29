/* ============================================================
   «Арки» (build/arki.py, arki.css): the arched windows of «Как у нас»
   stay dark until the row comes into view, then light up one after another;
   in the strip (phones, tablets) the window at the start of the strip is lit and the light follows the swipe.
   No animation loop: class changes only, the transitions are opacity/transform in CSS.
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};
  const row = document.querySelector('[data-arcade]');
  if (!row || !('IntersectionObserver' in window)) return;
  const arches = Array.from(row.querySelectorAll('.arch'));

  /* ---------- lightbox on a phone: the 800px copies of the full photos (build/images.py, RESPONSIVE_WIDTHS) ---------- */
  if (matchMedia('(max-width: 640px)').matches) {
    row.querySelectorAll('a[data-lightbox]').forEach((a) => a.setAttribute('href', a.getAttribute('href').replace(/\.webp$/, '-800.webp')));
  }

  /* ---------- lights on (without JS or with reduced motion the windows are simply lit) ---------- */
  if (!G.reducedMotion) {
    row.classList.add('is-dark');
    const wake = new IntersectionObserver((entries) => {
      if (!entries.some((en) => en.isIntersecting)) return;
      wake.disconnect();
      row.classList.add('is-waking');
      row.classList.remove('is-dark');
      // the stagger delay is only for this first sequence: hover must answer at once afterwards
      const step = parseFloat(getComputedStyle(row).getPropertyValue('--arch-step')) || 330;
      setTimeout(() => row.classList.remove('is-waking'), arches.length * step + 1400);
    }, { threshold: 0.3 });
    wake.observe(row);
  }

  /* ---------- strip: the window crossing the band 15–55% from the left edge of the strip is lit ---------- */
  const strip = matchMedia('(max-width: 999px)');
  let lit = null;
  const sync = () => {
    if (lit) { lit.disconnect(); lit = null; }
    arches.forEach((a) => a.classList.remove('is-lit'));
    if (!strip.matches) return;
    lit = new IntersectionObserver((entries) => entries.forEach((en) => en.target.closest('.arch').classList.toggle('is-lit', en.isIntersecting)),
      { root: row, rootMargin: '0px -45% 0px -15%', threshold: 0 });
    arches.forEach((a) => lit.observe(a.querySelector('.arch__win')));
  };
  sync();
  if (strip.addEventListener) strip.addEventListener('change', sync); else strip.addListener(sync);
})();
