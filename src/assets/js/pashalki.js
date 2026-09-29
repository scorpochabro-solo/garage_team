/* ============================================================
   пасхалки: the V8 table x-ray switch, the niche in the brick wall,
   the V8 back-to-top gauge. No frame loop at all: the crank is turned
   by CSS scroll-driven animations, everything else is CSS transitions
   on transform / opacity; the script only flips classes and attributes.
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};
  const reduced = !!G.reducedMotion;
  const pad2 = (n) => String(n).padStart(2, '0');

  /* ---------- V8 table: hover and keyboard focus show the pistons by CSS; a tap (or Enter) pins them ---------- */
  document.querySelectorAll('[data-xray]').forEach((btn) => {
    btn.addEventListener('click', () => btn.setAttribute('aria-pressed', String(btn.getAttribute('aria-pressed') !== 'true')));
  });

  /* ---------- niche: every press lights the lamp, swings it a little and puts the next object in ---------- */
  const niche = document.querySelector('[data-niche]');
  if (niche) {
    const spot = niche.closest('.niche-spot');
    const items = Array.from(niche.querySelectorAll('.niche__item'));
    const names = (niche.dataset.names || '').split('|');
    const numEl = spot.querySelector('[data-niche-n]');
    const nameEl = spot.querySelector('[data-niche-name]');
    const lamp = spot.querySelector('.lamp');
    let cur = 0;
    niche.addEventListener('click', () => {
      spot.classList.add('is-lit');
      const prev = items[cur];
      cur = (cur + 1) % items.length;
      prev.classList.replace('is-active', 'is-out');
      items[cur].classList.remove('is-out');
      items[cur].classList.add('is-active');
      if (numEl) numEl.textContent = pad2(cur + 1);
      if (nameEl) nameEl.textContent = names[cur] || '';
      if (lamp && !reduced) {
        lamp.classList.remove('is-swinging');
        requestAnimationFrame(() => requestAnimationFrame(() => lamp.classList.add('is-swinging')));   // restart the swing mid-way
      }
    });
    // an object that has left goes back to its place on the right, unseen, ready for the next round
    items.forEach((it) => it.addEventListener('transitionend', (e) => { if (e.propertyName === 'opacity' && it.classList.contains('is-out')) it.classList.remove('is-out'); }));
    if (lamp) lamp.addEventListener('animationend', () => lamp.classList.remove('is-swinging'));
  }

  /* ---------- for those who open the developer console ---------- */
  try {
    console.info('%cГАРАЖ%c Заглянули под капот? Мы тоже так делаем. Ул. Красная слобода, 9 · (831) 416-16-77',
      'background:#00963d;color:#fff;font-weight:700;padding:2px 6px', 'color:inherit');
  } catch (_) { /* no console */ }

  /* ---------- V8 gauge: shown past the first screen; the crank and the progress bar follow the scroll by CSS ---------- */
  const v8 = document.querySelector('[data-v8]');
  if (!v8) return;
  const wide = matchMedia('(min-width: 901px)');
  // without scroll-driven animations the bar is set from here (the engine then stays at rest)
  const sda = !!(window.CSS && CSS.supports && CSS.supports('animation-timeline: scroll()'));
  let viewH = innerHeight, shown = false, on = false;
  const onScroll = () => {
    const y = scrollY;
    const show = y > viewH * 0.9;
    if (show !== shown) { shown = show; v8.classList.toggle('is-shown', show); }
    if (!sda) v8.style.setProperty('--progress', Math.min(1, y / Math.max(1, document.documentElement.scrollHeight - viewH)).toFixed(3));
  };
  const measure = () => { viewH = innerHeight; };
  const sync = () => {
    if (wide.matches === on) return;
    on = wide.matches;
    v8.hidden = !on;
    if (on) {
      measure();
      addEventListener('scroll', onScroll, { passive: true });
      addEventListener('resize', measure, { passive: true });
      onScroll();
    } else {
      removeEventListener('scroll', onScroll);
      removeEventListener('resize', measure);
      shown = false;
      v8.classList.remove('is-shown');
    }
  };
  // at the very end of the page the button would cover the footer's last links: it steps up over them
  const foot = document.querySelector('.footer__bottom');
  if (foot && 'IntersectionObserver' in window) {
    new IntersectionObserver((entries) => entries.forEach((en) => v8.classList.toggle('is-lifted', en.isIntersecting))).observe(foot);
  }
  v8.addEventListener('click', () => {
    scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });   // on the way up the crank runs in reverse
    const logo = document.querySelector('.site-header .logo');
    if (logo) logo.focus({ preventScroll: true });
  });
  if (wide.addEventListener) wide.addEventListener('change', sync); else wide.addListener(sync);
  sync();
})();
