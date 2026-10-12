/* ============================================================
   «Свет ламп»: the pendant lamps on the first screen (markup build/svet.py, styles svet.css).
   A lamp is a toggle button: it switches off and on with a short flicker. With every lamp off the room goes dark,
   the neon sign of the workshop lights up and, with a mouse, the cursor becomes a hand lamp over the brick.
   Switching any lamp back on brings the light back.
   The lamps sway a little when the page scrolls, when the cursor brushes them and when they are switched.
   What keeps it cheap:
     1. lamps and the hand lamp move with transform only, lights switch with opacity (CSS keyframes);
     2. one requestAnimationFrame loop, running only while the hero is on screen and something still moves;
     3. layout is read in one batch on resize, never inside the frame loop.
   ============================================================ */
(() => {
  'use strict';
  const room = document.querySelector('[data-svet]');
  if (!room) return;
  const G = window.G || {};
  const hero = room.closest('.hero') || room.parentElement;
  const pools = Array.from(hero.querySelectorAll('[data-svet-pool]'));
  const lamps = Array.from(room.querySelectorAll('[data-svet-lamp]')).map((el, i) => ({
    el, btn: el.querySelector('button'), pool: pools[i] || null, on: true,
    a: 0, v: 0,                            // angle (deg) and angular velocity (deg/s)
    f: 0.85 + (i % 3) * 0.12,              // each lamp takes a push a little differently, so they never swing in step
    x: 0, y: 0, shown: true,               // dome centre in hero coordinates; a lamp hidden by CSS is skipped
  }));
  const status = room.querySelector('[data-svet-status]');
  const torch = hero.querySelector('.svet-wall__torch');
  const reduced = !!G.reducedMotion;
  const hoverMq = matchMedia('(hover: hover) and (pointer: fine)');
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  const K = 30;          // 1/s², stiffness: about 0.9 swings a second, a lamp on a short cord
  const DAMP = 1.9;      // 1/s, a push dies out in 4–5 s
  const MAX = 6;         // deg
  const REST_A = 0.03;   // deg
  const REST_V = 0.2;    // deg/s
  const TORCH = 190;     // px, radius of the hand lamp's light
  const TORCH_TAU = 70;  // ms, easing of the hand lamp towards the cursor

  /* ---------- geometry: one batched read, refreshed on resize ---------- */
  let W = 1; let H = 1; let heroTop = 0; let heroLeft = 0; let S = 1;
  function paintTorch() {
    const c = torch && torch.getContext('2d');
    if (!c) return;
    const n = torch.width; const half = n / 2;
    const r = (TORCH * 1.35) / S * n;
    const g = c.createRadialGradient(half, half, 0, half, half, r);
    g.addColorStop(0, 'rgba(255, 196, 128, 0.1)');    // a warm hint in the middle of the beam
    g.addColorStop(0.36, 'rgba(255, 190, 120, 0.02)');
    g.addColorStop(0.6, 'rgba(6, 4, 3, 0.4)');
    g.addColorStop(0.84, 'rgba(5, 4, 3, 0.84)');
    g.addColorStop(1, 'rgba(5, 4, 3, 0.93)');
    c.clearRect(0, 0, n, n);
    c.fillStyle = g;
    c.fillRect(0, 0, n, n);
  }
  function measure() {
    const hr = hero.getBoundingClientRect();
    W = hr.width || 1; H = hr.height || 1;
    heroTop = hr.top + scrollY; heroLeft = hr.left + scrollX;
    lamps.forEach((l) => {
      const b = l.btn.getBoundingClientRect();
      l.shown = b.width > 0;
      l.x = b.left - hr.left + b.width / 2; l.y = b.top - hr.top + b.height / 2;
      l.r = b.width * 0.75;
    });
    // the veil must still cover the far corner of the hero when the beam sits on the opposite edge
    S = Math.ceil(2 * Math.max(W, H) + TORCH * 2);
    if (torch) { torch.style.width = `${S}px`; torch.style.height = `${S}px`; paintTorch(); placeTorch(); }
  }

  /* ---------- the hand lamp (dark room, mouse only) ---------- */
  const useTorch = !!torch && hoverMq.matches;
  hero.classList.toggle('has-torch', useTorch);
  let tx = 0; let ty = 0; let gx = -1; let gy = -1;
  function placeTorch() {
    if (!torch) return;
    if (gx < 0) { gx = W * 0.5; gy = H * 0.3; tx = gx; ty = gy; }
    torch.style.transform = `translate3d(${(tx - S / 2).toFixed(1)}px, ${(ty - S / 2).toFixed(1)}px, 0)`;
  }

  /* ---------- the swing: one rAF loop, only while something moves and the hero is on screen ---------- */
  let raf = 0; let last = 0; let visible = true; let dark = false;
  function frame(t) {
    raf = 0;
    const dt = Math.min(0.032, Math.max(0.001, (t - last) / 1000));
    last = t;
    let moving = false;
    lamps.forEach((l) => {
      if (!l.a && !l.v) return;
      l.v += (-K * l.a - DAMP * l.v) * dt;
      l.a = clamp(l.a + l.v * dt, -MAX, MAX);
      if (Math.abs(l.a) < REST_A && Math.abs(l.v) < REST_V) { l.a = 0; l.v = 0; l.el.style.transform = ''; return; }
      moving = true;
      l.el.style.transform = `rotate(${l.a.toFixed(2)}deg)`;
    });
    if (dark && useTorch && (Math.abs(gx - tx) > 0.3 || Math.abs(gy - ty) > 0.3)) {
      const k = reduced ? 1 : 1 - Math.exp(-(dt * 1000) / TORCH_TAU);
      tx += (gx - tx) * k; ty += (gy - ty) * k;
      placeTorch();
      moving = true;
    }
    if (moving && visible) raf = requestAnimationFrame(frame);
  }
  function wake() {
    if (raf || !visible) return;
    last = performance.now();
    raf = requestAnimationFrame(frame);
  }
  function push(l, dv) {
    if (reduced || !l.shown) return;
    l.v = clamp(l.v + dv, -60, 60);
    wake();
  }

  /* ---------- switching ---------- */
  let darkTimer = 0;
  function setDark(on) {
    if (on === dark) return;
    dark = on;
    hero.classList.toggle('is-dark', on);
    if (status) status.textContent = on ? 'Свет в офисе выключен' : '';
    if (on && useTorch) { tx = gx; ty = gy; placeTorch(); }
  }
  function sync() {
    clearTimeout(darkTimer);
    const shown = lamps.filter((l) => l.shown);
    if (shown.length && shown.every((l) => !l.on)) darkTimer = setTimeout(() => setDark(true), reduced ? 0 : 420);  // after the last flicker
    else setDark(false);
  }
  function setLamp(l, on) {
    if (l.on === on) return;
    l.on = on;
    [l.el, l.pool].forEach((n) => { if (n) { n.classList.toggle('is-off', !on); n.classList.toggle('is-relit', on); } });
    l.btn.setAttribute('aria-pressed', String(on));
  }
  lamps.forEach((l) => {
    l.btn.addEventListener('click', () => {
      setLamp(l, !l.on);
      push(l, (Math.random() < 0.5 ? -1 : 1) * 28);   // the hand that reaches for the switch nudges the lamp
      sync();
    });
  });

  /* ---------- the cursor brushes the lamps; in the dark it carries the hand lamp ---------- */
  let px = -1; let py = -1;
  hero.addEventListener('pointermove', (e) => {
    if (e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;
    const x = e.pageX - heroLeft; const y = e.pageY - heroTop;
    if (px >= 0) {
      const dx = x - px;
      lamps.forEach((l) => { if (Math.abs(x - l.x) < l.r && Math.abs(y - l.y) < l.r) push(l, clamp(dx, -24, 24) * 1.1 * l.f); });
    }
    px = x; py = y;
    if (useTorch) { gx = x; gy = y; if (dark) wake(); }
  }, { passive: true });

  /* ---------- scrolling sways the row a little ---------- */
  let lastY = scrollY;
  addEventListener('scroll', () => {
    const dy = scrollY - lastY;
    lastY = scrollY;
    if (!visible || reduced) return;
    const kick = clamp(dy * 0.12, -4, 4);
    if (Math.abs(kick) > 0.2) lamps.forEach((l) => { if (Math.abs(l.v) < 28) push(l, kick * l.f); });
  }, { passive: true });

  /* ---------- start / stop with the hero on screen ---------- */
  measure();
  let resizeRaf = 0;
  addEventListener('resize', () => {
    if (resizeRaf) return;
    resizeRaf = requestAnimationFrame(() => { resizeRaf = 0; measure(); sync(); });
  }, { passive: true });
  addEventListener('load', measure);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((entries) => entries.forEach((en) => {
      visible = en.isIntersecting;
      if (visible) wake(); else if (raf) { cancelAnimationFrame(raf); raf = 0; }
    })).observe(hero);
  }
})();
