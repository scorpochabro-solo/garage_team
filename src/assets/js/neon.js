/* ============================================================
   «Неон» (build/neon.py, neon.css)
   1. The footer sign: dark until the strip comes into view, then it strikes on once and stays lit.
   2. The 404 sign: the broken tube catches after its start-up (CSS); from then on it buzzes briefly every 6–15 s,
      only while the sign is on screen and the tab is visible — between buzzes nothing runs at all.
   Without JavaScript and with reduced motion every tube simply burns (the CSS default).
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};
  if (G.reducedMotion || !('IntersectionObserver' in window)) return;

  /* ---------- 1. the footer sign ---------- */
  // The observer's first report says where the sign is when the page opens: on screen (a short page, a reload at the
  // bottom) it simply stays lit; below the fold it goes dark (unseen) and strikes on once it is well in view.
  const strip = document.querySelector('[data-neon-sign]');
  const stripSign = strip && strip.firstElementChild;
  const ON_AT = 0.6;        // share of the sign that must be on screen
  if (stripSign) {
    let first = true;
    const io = new IntersectionObserver((entries) => {
      const en = entries[entries.length - 1];
      if (first) {
        first = false;
        if (en.isIntersecting) io.disconnect(); else strip.classList.add('is-off');
        return;
      }
      if (!en.isIntersecting || en.intersectionRatio < ON_AT - 0.05) return;
      io.disconnect();
      strip.classList.replace('is-off', 'is-on');
    }, { threshold: ON_AT });
    io.observe(stripSign);
  }

  /* ---------- 2. the broken tube of the 404 ---------- */
  const scene = document.querySelector('[data-neon-404]');
  const tube = scene && scene.querySelector('.neon-404__tube');
  if (!tube) return;
  const BUZZ = ['is-buzz-1', 'is-buzz-2', 'is-buzz-3'];
  const PAUSE_MIN = 6000;   // ms between two buzzes…
  const PAUSE_MAX = 15000;  // …at random, so it never beats like a clock
  let steady = false;
  let onScreen = false;
  let timer = 0;

  const schedule = () => {
    clearTimeout(timer);
    timer = 0;
    if (steady && onScreen && !document.hidden) timer = setTimeout(buzz, PAUSE_MIN + Math.random() * (PAUSE_MAX - PAUSE_MIN));
  };
  function buzz() {
    timer = 0;
    if (!onScreen || document.hidden) return;
    // a buzz whose end was never reported (the tab was hidden at that moment): clear it and wait for the next one
    if (BUZZ.some((c) => scene.classList.contains(c))) { scene.classList.remove(...BUZZ); schedule(); return; }
    scene.classList.add(BUZZ[Math.floor(Math.random() * BUZZ.length)]);
  }
  const settle = () => {
    if (steady) return;
    steady = true;
    scene.classList.add('is-steady');
    schedule();
  };

  // the start-up flicker or a buzz is over (the event of the tube itself, not of its light on the wall)
  tube.addEventListener('animationend', (e) => {
    if (e.target !== tube) return;
    if (!steady) { settle(); return; }
    scene.classList.remove(...BUZZ);
    schedule();
  });
  // in case animationend never comes (the page opened in a background tab): the start-up's own length, from the CSS
  const cs = getComputedStyle(tube);
  setTimeout(settle, (parseFloat(cs.animationDelay) + parseFloat(cs.animationDuration)) * 1000 + 250 || 6000);

  new IntersectionObserver((entries) => {
    onScreen = entries.some((en) => en.isIntersecting);
    schedule();
  }).observe(tube);
  document.addEventListener('visibilitychange', schedule);
})();
