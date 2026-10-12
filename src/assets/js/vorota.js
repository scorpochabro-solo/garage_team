/* ============================================================
   vorota: «Ворота» — the contacts scene (build/vorota.py, css/vorota.css)
   the sign over the gate lights up when the facade comes into view; while the stage is pinned the scroll
   rolls the shutter up and then walks the camera through the gate into the workshop.
   One rAF loop, only while the scene is on screen and only until it catches up with the scroll.
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};
  const gate = document.querySelector('[data-gate]');
  // without an observer or with reduced motion the scene stays static: gate open, sign lit (the CSS default)
  if (!gate || !('IntersectionObserver' in window) || G.reducedMotion) return;
  const stage = gate.querySelector('.gate__stage');
  gate.classList.add('gate--scroll');

  /* ---------- the sign: lights up once, when the sign itself is well inside the screen (above the phone call bar);
     watched through its halo, one per framing — the hidden framing never intersects ---------- */
  const lit = new IntersectionObserver((entries) => {
    if (entries.some((en) => en.isIntersecting)) { gate.classList.add('is-lit'); lit.disconnect(); }
  }, { threshold: 0.5, rootMargin: '0px 0px -12% 0px' });
  gate.querySelectorAll('.gate__glow').forEach((el) => lit.observe(el));
  new IntersectionObserver((entries) => entries.forEach((en) => gate.classList.toggle('is-offscreen', !en.isIntersecting))).observe(stage);

  const world = gate.querySelector('.gate__world');
  const inside = gate.querySelector('.gate__inside');
  const insideImg = inside.querySelector('img');
  const remote = gate.querySelector('[data-gate-remote]');
  const btn = remote.querySelector('[data-gate-toggle]');
  const meter = remote.querySelector('[data-gate-meter]');
  const value = remote.querySelector('[data-gate-value]');
  remote.hidden = false;

  const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
  const smooth = (t) => t * t * (3 - 2 * t);
  const phase = (p, a, b) => smooth(clamp01((p - a) / (b - a)));
  // progress 0…1 over the pinned run: the shutter rolls up on 0.04–0.46, the scene rests at OPEN
  // (the remote's «open» stop), the walk-in takes 0.5–0.94 and the workshop fades in on the way
  const OPEN = 0.5;

  let run = 1, pin = 0, shutter = null, spill = null, tx = 0, ty = 0, zoom = 2;
  let cur = -1, raf = 0, shownPct = -1, isOpen = null;

  const measure = () => {
    pin = parseFloat(getComputedStyle(stage).top) || 0;
    run = Math.max(1, gate.offsetHeight - stage.offsetHeight);
    const art = Array.from(gate.querySelectorAll('.gate__art')).find((el) => el.offsetWidth);   // the framing on screen
    if (!art) return;
    shutter = art.querySelector('[data-gate-shutter]');
    spill = art.querySelector('.gate__spill');
    const op = art.querySelector('.gate__opening');
    // layout values (transforms ignored): the middle of the opening is the zoom origin and travels to the middle of the stage
    const ox = op.offsetLeft + op.offsetWidth / 2;
    const oy = op.offsetTop + op.offsetHeight / 2;
    world.style.transformOrigin = `${ox}px ${oy}px`;
    tx = stage.clientWidth / 2 - (world.offsetLeft + ox);
    ty = stage.clientHeight / 2 - (world.offsetTop + oy);
    zoom = Math.min(2.4, 0.9 * Math.max(stage.clientWidth / op.offsetWidth, stage.clientHeight / op.offsetHeight));
    cur = -1;   // redraw at once, without easing
  };

  const render = (p) => {
    const open = phase(p, 0.04, 0.46);
    const walk = phase(p, 0.5, 0.94);
    const fade = phase(p, 0.66, 0.9);
    if (shutter) shutter.style.transform = `translate3d(0, ${(-100 * open).toFixed(2)}%, 0)`;
    if (spill) spill.style.opacity = clamp01(open * 1.6).toFixed(3);
    world.style.transform = walk
      ? `translate3d(${(tx * walk).toFixed(1)}px, ${(ty * walk).toFixed(1)}px, 0) scale(${(1 + (zoom - 1) * walk).toFixed(4)})`
      : '';
    inside.style.opacity = fade.toFixed(3);
    insideImg.style.transform = `scale(${(1.12 - 0.12 * fade).toFixed(4)})`;
    meter.style.transform = `scaleY(${open.toFixed(3)})`;
    const pct = Math.round(open * 100);
    if (pct !== shownPct) { shownPct = pct; value.textContent = pct + '%'; }
    const o = p >= OPEN - 0.02;
    if (o !== isOpen) {
      isOpen = o;
      remote.classList.toggle('is-open', o);
      btn.setAttribute('aria-label', o ? 'Закрыть ворота' : 'Открыть ворота');
    }
  };

  const progress = () => clamp01((pin - gate.getBoundingClientRect().top) / run);
  // the remote drives the page like a gate motor: slow and steady, soft start and stop (inside the same loop)
  let drive = null;
  const html = document.documentElement;
  const endDrive = () => { if (drive) { drive = null; html.style.scrollBehavior = ''; } };
  const tick = (now) => {
    raf = 0;
    if (drive) {
      const t = clamp01((now - drive.t0) / drive.dur);
      const e = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      scrollTo(0, Math.round(drive.from + (drive.to - drive.from) * e));
      if (t >= 1) endDrive();
    }
    const target = progress();
    // a little inertia: the shutter follows the scroll like a motor, not like a sheet of paper
    const next = cur < 0 ? target : cur + (target - cur) * 0.2;
    cur = Math.abs(target - next) < 0.0005 ? target : next;
    render(cur);
    if (cur !== target || drive) raf = requestAnimationFrame(tick);
  };
  const kick = () => { if (!raf) raf = requestAnimationFrame(tick); };

  /* ---------- the loop runs only while the scene is near the screen ---------- */
  let active = false;
  new IntersectionObserver((entries) => {
    const on = entries[entries.length - 1].isIntersecting;
    if (on === active) return;
    active = on;
    gate.classList.toggle('is-active', on);   // will-change only while it matters
    if (on) {
      addEventListener('scroll', kick, { passive: true });
      kick();
    } else {
      removeEventListener('scroll', kick);
      if (raf) { cancelAnimationFrame(raf); raf = 0; }
      cur = progress();   // leave it in its end state (0 above the scene, 1 below)
      render(cur);
    }
  }, { rootMargin: '15% 0px' }).observe(gate);

  /* ---------- the remote: ▲ rolls the page to the open gate, ▼ back to the closed one; any scroll input takes over ---------- */
  btn.addEventListener('click', () => {
    const from = scrollY;
    const to = Math.round(gate.getBoundingClientRect().top + scrollY - pin + (isOpen ? 0 : OPEN * run));
    html.style.scrollBehavior = 'auto';   // steps of the drive must not be smoothed by the page's scroll-behavior
    drive = { from, to, t0: performance.now(), dur: Math.min(2600, Math.max(900, (Math.abs(to - from) / run) * 3400)) };
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(tick);
  });
  ['wheel', 'touchstart', 'keydown'].forEach((type) => addEventListener(type, (e) => { if (!btn.contains(e.target)) endDrive(); }, { passive: true }));

  measure();
  render(progress());
  addEventListener('resize', () => { measure(); kick(); }, { passive: true });
  addEventListener('load', () => { measure(); kick(); });
})();
