/* ============================================================
   core: helpers, header, mobile menu, reveal, modals, toast, phone mask
   ============================================================ */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const G = (window.G = window.G || {});
  G.$ = $; G.$$ = $$;
  G.reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  G.canHover = matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---------- header ---------- */
  const header = $('[data-header]');
  const onScroll = () => { if (header) header.classList.toggle('is-scrolled', window.scrollY > 24); };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- mobile menu ---------- */
  const burger = $('.burger');
  const menu = $('#mobile-menu');
  if (burger && menu) {
    const setOpen = (open) => {
      burger.setAttribute('aria-expanded', String(open));
      menu.classList.toggle('is-open', open);
      document.body.classList.toggle('no-scroll', open);
      document.body.classList.toggle('is-menu-open', open);   // hides the fixed mobile bar: the menu has its own call buttons
    };
    burger.addEventListener('click', () => setOpen(burger.getAttribute('aria-expanded') !== 'true'));
    menu.addEventListener('click', (e) => { if (e.target.closest('a, button')) setOpen(false); });
    addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    addEventListener('resize', () => { if (innerWidth > 1100) setOpen(false); }, { passive: true });
  }

  /* ---------- side index: open next to the content on wide screens, collapsed under it on phones ---------- */
  const sideIndex = $('[data-side-index]');
  if (sideIndex) {
    const wide = matchMedia('(min-width: 1001px)');
    const sync = () => { sideIndex.open = wide.matches; };
    sync();
    if (wide.addEventListener) wide.addEventListener('change', sync); else wide.addListener(sync);
    // next to the content the list is always shown: its title is a heading there, not a toggle
    sideIndex.querySelector('summary').addEventListener('click', (e) => { if (wide.matches) e.preventDefault(); });
  }

  /* ---------- active nav ---------- */
  const BASE = (document.documentElement.dataset.base || '').replace(/\/$/, '');
  const path = location.pathname.replace(new RegExp('^' + BASE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), '') || '/';
  $$('.nav__link, .mobile-menu__link').forEach((a) => {
    const href = (a.getAttribute('href') || '').replace(new RegExp('^' + BASE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), '');
    if (href === '/' || href === '') return;
    const base = href.replace(/\/$/, '').replace(/\.html$/, '');
    const cur = path.replace(/\/$/, '').replace(/\.html$/, '');
    if (base && (cur === base || cur.startsWith(base + '/'))) a.classList.add('is-active');
  });

  /* ---------- scroll reveal ---------- */
  const revealEls = $$('.reveal');
  if (revealEls.length) {
    if (G.reducedMotion || !('IntersectionObserver' in window)) {
      revealEls.forEach((el) => el.classList.add('is-in'));
    } else {
      const io = new IntersectionObserver((entries) => {
        entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
      }, { rootMargin: '0px 0px -4% 0px', threshold: 0 });
      revealEls.forEach((el) => io.observe(el));
      // safety net: anything already on screen (or above it) becomes visible even if the observer never fires
      const sweep = () => revealEls.forEach((el) => { if (!el.classList.contains('is-in') && el.getBoundingClientRect().top < innerHeight + 120) el.classList.add('is-in'); });
      setTimeout(sweep, 1200);
      addEventListener('load', () => setTimeout(sweep, 300));
    }
  }

  /* ---------- looping decorations (ticker, scroll hint) tick on every frame even when scrolled away: pause them off screen ---------- */
  const loops = $$('.ticker, .hero__scroll');
  if (loops.length && 'IntersectionObserver' in window) {
    const idle = new IntersectionObserver((entries) => entries.forEach((en) => en.target.classList.toggle('is-offscreen', !en.isIntersecting)));
    loops.forEach((el) => idle.observe(el));
  }

  /* ---------- count-up ---------- */
  const counters = $$('[data-countup]');
  if (counters.length) {
    const run = (el) => {
      const end = Number(el.dataset.countup);
      if (G.reducedMotion || !Number.isFinite(end)) { el.textContent = el.dataset.countup; return; }
      // the markup holds the final number: its width is kept while counting, otherwise a narrow fact card re-wrapped
      // «360 дн.» on every other frame and the whole first screen jumped (layout shift 0.2–0.6 at 1180–1300 px)
      el.style.display = 'inline-block';
      el.style.minWidth = `${el.getBoundingClientRect().width}px`;
      const dur = 1400; const t0 = performance.now();
      const step = (t) => {
        const p = Math.min(1, (t - t0) / dur); const e = 1 - Math.pow(1 - p, 3);
        el.textContent = String(Math.round(end * e));
        if (p < 1) requestAnimationFrame(step);
        else el.style.minWidth = '';   // the final number has that width anyway; a later resize must not keep it
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { run(en.target); io.unobserve(en.target); } });
    }, { threshold: 0.5 });
    // the width is measured in the real font: start once the web fonts are in (a failed font does not block it)
    const fontsIn = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
    fontsIn.catch(() => {}).then(() => counters.forEach((el) => io.observe(el)));
  }

  /* ---------- hero parallax ---------- */
  const heroPhoto = $('.hero__photo');
  if (heroPhoto && G.canHover && !G.reducedMotion) {
    let raf = 0;
    addEventListener('mousemove', (e) => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        const x = (e.clientX / innerWidth - 0.5) * 14; const y = (e.clientY / innerHeight - 0.5) * 10;
        heroPhoto.style.transform = `scale(1.06) translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
        raf = 0;
      });
    }, { passive: true });
  }

  /* ---------- modals ---------- */
  G.openModal = (id, preset) => {
    const dlg = $('#modal-' + id);
    if (!dlg) return;
    if (preset) { Object.entries(preset).forEach(([k, v]) => { const f = dlg.querySelector(`[name="${k}"]`); if (f) f.value = v; }); }
    if (typeof dlg.showModal === 'function') { if (!dlg.open) dlg.showModal(); } else { dlg.setAttribute('open', ''); }
    // with a mouse the cursor goes straight to the first field; on a phone that would throw the keyboard over the form
    // before it is read, so there the dialog keeps its own focus on the close button and the visitor taps a field
    const first = dlg.querySelector('input:not([type=hidden]):not([disabled]), select, textarea');
    if (first && G.canHover) setTimeout(() => first.focus(), 60);
  };
  G.closeModal = (dlg) => { if (!dlg) return; if (typeof dlg.close === 'function') dlg.close(); else dlg.removeAttribute('open'); };
  document.addEventListener('click', (e) => {
    const opener = e.target.closest('[data-modal]');
    if (opener) {
      e.preventDefault();
      let preset = null;
      if (opener.dataset.preset) { try { preset = JSON.parse(opener.dataset.preset); } catch (_) { preset = null; } }
      G.openModal(opener.dataset.modal, preset);
      return;
    }
    const closer = e.target.closest('[data-close]');
    if (closer) { G.closeModal(closer.closest('dialog')); return; }
    if (e.target instanceof HTMLDialogElement) G.closeModal(e.target); // backdrop click
  });

  /* ---------- toast ---------- */
  let toastTimer = 0;
  G.toast = (msg, type = 'ok') => {
    let t = $('.toast');
    if (!t) { t = document.createElement('div'); t.setAttribute('role', 'status'); document.body.appendChild(t); }
    t.className = 'toast toast--' + type;
    t.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#i-${type === 'ok' ? 'check' : 'hazard'}"/></svg><span></span>`;
    t.querySelector('span').textContent = msg;
    requestAnimationFrame(() => t.classList.add('is-visible'));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('is-visible'), 4500);
  };

  /* ---------- phone mask ---------- */
  G.formatPhone = (raw) => {
    let d = String(raw).replace(/\D/g, '');
    if (!d) return '';
    if (d[0] === '8') d = '7' + d.slice(1);
    if (d[0] !== '7') d = '7' + d;
    d = d.slice(0, 11);
    let out = '+7';
    if (d.length > 1) out += ' (' + d.slice(1, 4);
    if (d.length >= 4) out += ') ' + d.slice(4, 7);
    if (d.length >= 7) out += '-' + d.slice(7, 9);
    if (d.length >= 9) out += '-' + d.slice(9, 11);
    return out;
  };
  G.validPhone = (v) => String(v).replace(/\D/g, '').length === 11;
  G.maskPhone = (input) => {
    input.setAttribute('inputmode', 'tel');
    input.addEventListener('input', () => { input.value = G.formatPhone(input.value); });
    input.addEventListener('focus', () => { if (!input.value) input.value = '+7 ('; });
    input.addEventListener('blur', () => { if (input.value === '+7 (' || input.value === '+7') input.value = ''; });
  };
  $$('input[data-phone]').forEach(G.maskPhone);

  /* ---------- field validation helpers ---------- */
  G.setError = (input, on) => {
    const field = input.closest('.field');
    if (field) field.classList.toggle('is-error', !!on);
    input.setAttribute('aria-invalid', on ? 'true' : 'false');
  };
  G.clearErrorsOnInput = (root) => {
    $$('input, select, textarea', root).forEach((el) => {
      el.addEventListener('input', () => G.setError(el, false));
      el.addEventListener('change', () => G.setError(el, false));
    });
  };

  /* ---------- generic POST ---------- */
  G.postForm = async (form) => {
    const body = new FormData(form);
    const action = form.getAttribute('action') || location.pathname;
    const res = await fetch(action, { method: 'POST', body, headers: { 'X-Requested-With': 'XMLHttpRequest', Accept: 'application/json, text/html' }, credentials: 'same-origin' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('json')) {
      const data = await res.json().catch(() => ({}));
      if (data && (data.error || data.success === false)) throw new Error(data.error || 'server');
      return data;
    }
    return {};
  };

  /* ---------- copyright year ---------- */
  $$('[data-year]').forEach((el) => { el.textContent = String(new Date().getFullYear()); });
})();

/* ============================================================
   interactive services map: hotspots, targeting reticle with a spotlight
   veil, HUD lines, readout panel, free-roam scanning, auto-tour.
   What keeps it cheap (the previous loupe stuttered the whole page):
     1. the reticle and the veil move with transform only, each on its own layer;
     2. one requestAnimationFrame loop eases the position and stops when idle;
     3. layout is read in one batch on resize, never inside the frame loop;
     4. idle hotspot rings stop pulsing while the pointer scans the car.
   ============================================================ */
(() => {
  'use strict';
  const stage = document.querySelector('[data-svc-stage]');
  if (!stage) return;
  const G = window.G || {};
  const carStage = stage.querySelector('.car-stage');
  const svg = stage.querySelector('.svc-lines');
  const items = Array.from(stage.querySelectorAll('.svc-item'));
  const hotspots = Array.from(stage.querySelectorAll('.hotspot'));
  const readout = stage.querySelector('[data-readout]');
  const itemByKey = new Map(items.map((i) => [i.dataset.key, i]));
  const hotspotByKey = new Map(hotspots.map((h) => [h.dataset.key, h]));
  const dataEl = document.getElementById('svc-data');
  let data = {};
  try { data = JSON.parse(dataEl ? dataEl.textContent : '{}'); } catch (_) { data = {}; }
  const total = Object.keys(data).length || hotspots.length;
  const hintHTML = readout ? readout.innerHTML : '';
  const pad2 = (n) => String(n || 0).padStart(2, '0');
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const NS = 'http://www.w3.org/2000/svg';
  const SNAP = 0.075;          // normalized distance at which the reticle snaps to a hotspot
  const TAU_ROAM = 55;         // ms, easing time constant while following the pointer
  const TAU_JUMP = 170;        // ms, easing time constant for jumps between hotspots (~0.55 s to settle)
  const SETTLED = 0.0004;
  const TOUR_MS = 3200;
  const USER_HOLD_MS = 9000;
  const ITEM_SHIFT = 6;        // px the active list item slides toward the car (see .svc-item.is-active)
  const VEIL = 'rgba(6, 8, 6, 0.74)';
  const VEIL_TEXTURE = 512;    // px: the veil is one small canvas gradient, stretched by CSS and moved by transform

  const spots = hotspots.map((h) => ({
    key: h.dataset.key,
    x: parseFloat(h.style.getPropertyValue('--x')) / 100,
    y: parseFloat(h.style.getPropertyValue('--y')) / 100,
  }));
  const spotByKey = new Map(spots.map((s) => [s.key, s]));
  const desktopMq = matchMedia('(min-width: 901px)');
  const hoverMq = matchMedia('(hover: hover) and (pointer: fine)');

  /* ---------- reticle + spotlight veil: purely decorative, so they are created here and hidden from assistive tech ---------- */
  const div = (cls, parent) => { const n = document.createElement('div'); n.className = cls; parent.appendChild(n); return n; };
  const spot = div('spot', carStage);
  spot.setAttribute('aria-hidden', 'true');
  const veil = document.createElement('canvas');
  veil.className = 'spot__veil';
  veil.width = VEIL_TEXTURE;
  veil.height = VEIL_TEXTURE;
  spot.appendChild(veil);
  const reticle = div('reticle', carStage);
  reticle.setAttribute('aria-hidden', 'true');
  div('reticle__cross', reticle);
  div('reticle__ring', reticle);
  const lock = div('reticle__lock', reticle);
  const tag = div('reticle__tag', reticle);

  /* ---------- geometry: one batched read, refreshed on resize ---------- */
  let geo = { W: 1, H: 1, carLeft: 0, carTop: 0, stageW: 1, stageH: 1, D: 1, spotLeft: 0, spotTop: 0, S: 1, items: new Map() };
  let measured = false;
  function paintVeil() {
    const c = veil.getContext('2d');
    if (!c) return;
    const half = VEIL_TEXTURE / 2;
    const hole = (geo.D * 0.56) / geo.S * VEIL_TEXTURE;   // clear radius, a little wider than the ring
    const soft = (geo.D * 1.15) / geo.S * VEIL_TEXTURE;   // where the veil reaches full strength
    const g = c.createRadialGradient(half, half, hole, half, half, soft);
    g.addColorStop(0, 'rgba(6, 8, 6, 0)');
    g.addColorStop(1, VEIL);
    c.clearRect(0, 0, VEIL_TEXTURE, VEIL_TEXTURE);
    c.fillStyle = g;
    c.fillRect(0, 0, VEIL_TEXTURE, VEIL_TEXTURE);
  }
  function measure() {
    measured = true;
    // offset* ignores transforms, so an item that is mid-slide or a stage that is mid-reveal does not skew the numbers
    const itemBoxes = new Map(items.map((i) => [i.dataset.key, { left: i.offsetLeft, top: i.offsetTop, width: i.offsetWidth, height: i.offsetHeight }]));
    const D = reticle.offsetWidth || 1;
    // the veil must still cover the far corner of its box when the hole sits on the opposite edge
    const S = Math.ceil(2 * Math.max(spot.offsetWidth, spot.offsetHeight) + D);
    geo = { W: carStage.clientWidth || 1, H: carStage.clientHeight || 1, carLeft: carStage.offsetLeft, carTop: carStage.offsetTop,
            stageW: stage.clientWidth || 1, stageH: stage.clientHeight || 1, D, spotLeft: spot.offsetLeft, spotTop: spot.offsetTop, S, items: itemBoxes };
    veil.style.width = `${S}px`;
    veil.style.height = `${S}px`;
    paintVeil();
  }

  /* ---------- reticle position: eased in one rAF loop ---------- */
  let curX = 0.5; let curY = 0.5; let tgtX = 0.5; let tgtY = 0.5;
  let placed = false; let visible = false; let free = false;
  let raf = 0; let lastT = 0;
  let edgeKey = '';
  let tagText = '';

  // the ring may protrude ~30% beyond the stage, never more; the target itself stays where the hotspot is
  function clampRing(fx, fy) {
    const m = geo.D * 0.35;
    return [geo.W > 2 * m ? clamp(fx, m / geo.W, 1 - m / geo.W) : fx, geo.H > 2 * m ? clamp(fy, m / geo.H, 1 - m / geo.H) : fy];
  }
  function placeReticle(gx, gy) {
    const x = gx * geo.W; const y = gy * geo.H;
    reticle.style.transform = `translate3d(${(x - geo.D / 2).toFixed(2)}px, ${(y - geo.D / 2).toFixed(2)}px, 0)`;
    veil.style.transform = `translate3d(${(x - geo.spotLeft - geo.S / 2).toFixed(2)}px, ${(y - geo.spotTop - geo.S / 2).toFixed(2)}px, 0)`;
  }
  function setTag(text) { if (text !== tagText) { tagText = text; tag.textContent = text; } }
  function lockPulse() {
    lock.classList.remove('is-locking');
    void lock.offsetWidth; // restart the animation
    lock.classList.add('is-locking');
  }
  function moveTo(fx, fy, isFree) {
    if (!measured) measure();   // asked for before the section came on screen (keyboard focus, a fast hover)
    tgtX = fx; tgtY = fy; free = isFree;
    if (!placed || G.reducedMotion) { curX = fx; curY = fy; placed = true; }
    const [px, py] = clampRing(fx, fy);
    const nextEdge = `${py > 0.62 ? 't' : ''}${px < 0.22 ? 'l' : ''}${px > 0.78 ? 'r' : ''}`;
    if (nextEdge !== edgeKey) {
      edgeKey = nextEdge;
      reticle.classList.toggle('reticle--top', py > 0.62);
      reticle.classList.toggle('reticle--edge-left', px < 0.22);
      reticle.classList.toggle('reticle--edge-right', px > 0.78);
    }
    if (!visible) {
      visible = true;
      carStage.classList.add('is-aiming');
      reticle.classList.add('is-visible');
      spot.classList.add('is-visible');
    }
    reticle.classList.toggle('is-free', isFree);
    schedule();
  }
  function hide() {
    if (!visible) return;
    visible = false; placed = false;
    reticle.classList.remove('is-visible', 'is-free');
    spot.classList.remove('is-visible');
    carStage.classList.remove('is-aiming');
  }
  function schedule() { if (!raf) raf = requestAnimationFrame(frame); }
  function frame(t) {
    raf = 0;
    const dt = lastT ? Math.min(64, t - lastT) : 16.7;
    lastT = t;
    if (pointerDirty) handlePointer();
    if (!visible) { lastT = 0; return; }
    const k = 1 - Math.exp(-dt / (free ? TAU_ROAM : TAU_JUMP));
    curX += (tgtX - curX) * k;
    curY += (tgtY - curY) * k;
    const settled = Math.abs(tgtX - curX) < SETTLED && Math.abs(tgtY - curY) < SETTLED;
    if (settled) { curX = tgtX; curY = tgtY; }
    const [px, py] = clampRing(curX, curY);
    placeReticle(px, py);
    if (!settled || pointerDirty) schedule(); else lastT = 0;
  }

  /* ---------- HUD connector line (drawn from cached geometry, no layout reads) ---------- */
  const el = (tagName, attrs) => { const n = document.createElementNS(NS, tagName); Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, String(v))); return n; };
  const clearLines = () => { while (svg.firstChild) svg.removeChild(svg.firstChild); };

  function drawLine(key) {
    clearLines();
    if (!desktopMq.matches) return;
    const box = geo.items.get(key);
    const s = spotByKey.get(key);
    const item = itemByKey.get(key);
    if (!box || !s || !item) return;
    svg.setAttribute('viewBox', `0 0 ${geo.stageW} ${geo.stageH}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    const [px, py] = clampRing(s.x, s.y);
    const tx = geo.carLeft + px * geo.W;
    const ty = geo.carTop + py * geo.H;
    const side = item.dataset.side;
    let sx; let sy; let ex; let ey;
    if (side === 'left') { sx = box.left + box.width + ITEM_SHIFT; sy = box.top + box.height / 2; ex = sx + 26; ey = sy; }
    else if (side === 'right') { sx = box.left - ITEM_SHIFT; sy = box.top + box.height / 2; ex = sx - 26; ey = sy; }
    else { sx = box.left + box.width / 2; sy = box.top; ex = sx; ey = sy - Math.max(24, (sy - ty) * 0.35); }
    // stop at the ring instead of its centre
    const dx = tx - ex; const dy = ty - ey; const len = Math.hypot(dx, dy) || 1;
    const r = Math.min(geo.D / 2 + 6, len - 4);
    const fx = tx - (dx / len) * r; const fy = ty - (dy / len) * r;
    const d = `M${sx.toFixed(1)},${sy.toFixed(1)} L${ex.toFixed(1)},${ey.toFixed(1)} L${fx.toFixed(1)},${fy.toFixed(1)}`;
    const L = (Math.hypot(ex - sx, ey - sy) + Math.hypot(fx - ex, fy - ey)).toFixed(1);
    const g = el('g', {});
    const halo = el('path', { d, class: 'halo' });
    const line = el('path', { d, class: 'line' });
    [halo, line].forEach((p) => { p.style.setProperty('--len', L); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; });
    g.append(halo, line, el('circle', { cx: sx, cy: sy, r: 3.5, class: 'knot' }), el('circle', { cx: fx, cy: fy, r: 3, class: 'end' }));
    svg.appendChild(g);
    requestAnimationFrame(() => g.classList.add('is-visible'));
  }

  /* ---------- readout ---------- */
  function readoutHTML(d) {
    const price = d.price
      ? `<b>${d.price}</b><span>${d.price_note || ''}</span>`
      : '<span>Стоимость уточняйте по\u00a0телефону</span>';
    return `
      <div class="svc-readout__icon"><svg class="ic" aria-hidden="true"><use href="#i-${d.icon}"/></svg></div>
      <div class="svc-readout__body">
        <div class="svc-readout__cat">${d.cat}</div>
        <div class="svc-readout__title">${d.name}</div>
        <div class="svc-readout__blurb">${d.blurb}</div>
        <div class="svc-readout__status"><i></i>Зона ${pad2(d.n)} / ${pad2(total)} · узел найден</div>
      </div>
      <div class="svc-readout__price">${price}
        <a class="link-arrow link-arrow--inline svc-readout__link" href="${d.href}">Подробнее <svg class="ic" aria-hidden="true"><use href="#i-arrow"/></svg></a>
      </div>`;
  }
  const roamHTML = '<div class="svc-readout__icon"><svg class="ic" aria-hidden="true"><use href="#i-search"/></svg></div><div class="svc-readout__hint">Ведите прицел по автомобилю. Рядом с точкой он «прилипнет» к узлу и покажет услугу.</div>';
  let swapTimer = 0;

  /* the panel keeps one size for every service: the tallest of all its possible contents at the current width */
  let readoutW = 0;
  function lockReadout(force) {
    if (!readout) return;
    const w = readout.offsetWidth;
    if (!w || (w === readoutW && !force)) return;
    readoutW = w;
    const probe = readout.cloneNode(false);
    probe.removeAttribute('data-readout');
    probe.removeAttribute('aria-live');
    probe.setAttribute('aria-hidden', 'true');
    probe.style.cssText = `position:absolute;left:0;top:0;width:${w}px;height:auto;visibility:hidden;pointer-events:none`;
    readout.parentNode.appendChild(probe);
    let max = 0;
    [hintHTML, roamHTML, ...Object.values(data).map(readoutHTML)].forEach((html) => {
      probe.innerHTML = html;
      max = Math.max(max, probe.offsetHeight);
    });
    probe.remove();
    readout.style.setProperty('--readout-h', `${Math.ceil(max)}px`);
  }
  lockReadout(true);
  if (document.fonts) {
    // web fonts change line wrapping: measure again once they are in
    document.fonts.ready.then(() => lockReadout(true));
    document.fonts.addEventListener('loadingdone', () => lockReadout(true));
  }

  function updateReadout(key, roam) {
    if (!readout) return;
    const d = key ? data[key] : null;
    clearTimeout(swapTimer);
    readout.classList.add('is-swapping');
    swapTimer = setTimeout(() => {
      readout.classList.toggle('is-on', !!d);
      readout.innerHTML = d ? readoutHTML(d) : (roam ? roamHTML : hintHTML);
      readout.classList.remove('is-swapping');
    }, 160);
  }

  /* ---------- activation: only the previous and the next element are touched ---------- */
  let active = null; let roaming = false; let userBusyUntil = 0; let listDimmed = false;

  /**
   * @param {string|null} key
   * @param {boolean} fromUser pauses the auto-tour for a while
   * @param {boolean} [viaRoam] activation by snapping while the pointer scans the car: the list is not dimmed then,
   *   because fading 21 items in and out on every snap was the largest single hitch of the scan (a 100 ms frame)
   */
  function setActive(key, fromUser, viaRoam) {
    if (fromUser) userBusyUntil = Date.now() + USER_HOLD_MS;
    if (active === key && key) return;
    [itemByKey.get(active), hotspotByKey.get(active)].forEach((n) => n && n.classList.remove('is-active'));
    [itemByKey.get(key), hotspotByKey.get(key)].forEach((n) => n && n.classList.add('is-active'));
    const dim = !!key && !viaRoam;
    if (dim !== listDimmed) { listDimmed = dim; stage.classList.toggle('has-active', dim); }
    active = key;
    const s = spotByKey.get(key);
    if (s) {
      moveTo(s.x, s.y, false);
      lockPulse();
      if (data[key]) setTag(`${pad2(data[key].n)} · ${data[key].name}`);
      drawLine(key);
    } else {
      clearLines();
      if (!roaming) hide();
    }
    updateReadout(key, roaming);
  }

  items.forEach((it) => {
    it.addEventListener('pointerenter', () => { if (hoverMq.matches) { roaming = false; setActive(it.dataset.key, true); } });
    it.addEventListener('focus', () => { roaming = false; setActive(it.dataset.key, true); });
  });
  hotspots.forEach((h) => {
    h.addEventListener('click', (e) => {
      e.preventDefault();
      const key = h.dataset.key;
      if (active === key && !hoverMq.matches) { const d = data[key]; if (d && d.href) location.href = d.href; return; }
      roaming = false;
      setActive(key, true);
      if (!desktopMq.matches && readout) readout.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
    });
    h.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); h.click(); } });
  });

  /* ---------- free-roam scanning (mouse only): events only store coordinates, the frame loop does the work ---------- */
  // .is-roaming calms the idle hotspot rings: 21 looping CSS animations were about 70% of the style work of every scanned frame
  function setRoaming(on) {
    roaming = on;
    carStage.classList.toggle('is-roaming', on);
  }
  let pointerDirty = false; let pointerX = 0; let pointerY = 0;
  let viewRect = null;   // viewport rect of the car stage, re-read at most once per frame and only after scroll / resize
  const dropViewRect = () => { viewRect = null; };

  function handlePointer() {
    pointerDirty = false;
    if (!viewRect) viewRect = carStage.getBoundingClientRect();
    if (!viewRect.width || !viewRect.height) return;
    const fx = clamp((pointerX - viewRect.left) / viewRect.width, 0, 1);
    const fy = clamp((pointerY - viewRect.top) / viewRect.height, 0, 1);
    userBusyUntil = Date.now() + USER_HOLD_MS;
    const aspect = viewRect.height / viewRect.width;
    let best = null; let bestD = 1;
    spots.forEach((s) => { const d = Math.hypot(s.x - fx, (s.y - fy) * aspect); if (d < bestD) { bestD = d; best = s; } });
    if (best && bestD < SNAP) {
      roaming = false;   // snapped: locked on a hotspot, but the pointer is still scanning (rings stay calm)
      if (active !== best.key) setActive(best.key, true, true);
      return;
    }
    const wasRoaming = roaming;
    setRoaming(true);
    if (active) setActive(null, true, true);
    moveTo(fx, fy, true);
    setTag('сканирование…');
    if (!wasRoaming) updateReadout(null, true);
  }

  if (hoverMq.matches) {
    carStage.addEventListener('pointerenter', dropViewRect);
    carStage.addEventListener('pointermove', (e) => { pointerX = e.clientX; pointerY = e.clientY; pointerDirty = true; schedule(); });
    carStage.addEventListener('pointerleave', () => {
      pointerDirty = false;
      setRoaming(false);
      const s = spotByKey.get(active);
      if (s) { moveTo(s.x, s.y, false); } else { hide(); updateReadout(null, false); }
    });
    addEventListener('scroll', dropViewRect, { passive: true });
  }

  /* ---------- keyboard cycling ---------- */
  stage.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    const idx = items.findIndex((i) => i.dataset.key === active);
    const next = e.key === 'ArrowDown' ? (idx + 1) % items.length : (idx - 1 + items.length) % items.length;
    e.preventDefault();
    items[next].focus();
  });

  /* ---------- auto tour; every looping CSS animation of the section pauses while it is off screen ---------- */
  let tourTimer = 0; let tourIdx = -1; let started = false;
  function tourTick() {
    if (Date.now() < userBusyUntil || document.hidden || roaming) return;
    tourIdx = (tourIdx + 1) % items.length;
    setActive(items[tourIdx].dataset.key, false);
  }
  function tourStop() { if (tourTimer) clearInterval(tourTimer); tourTimer = 0; }
  function tourStart() {
    tourStop();
    if (G.reducedMotion || !desktopMq.matches) return;
    tourTimer = setInterval(tourTick, TOUR_MS);
  }
  function onScreen(isIn) {
    stage.classList.toggle('is-paused', !isIn);
    if (!isIn) { tourStop(); return; }
    if (!started) {
      started = true;
      measure();
      carStage.classList.add('is-scanning');
      setTimeout(() => carStage.classList.add('is-ready'), 450);
      setTimeout(() => { if (!active && !roaming && Date.now() > userBusyUntil) tourTick(); }, 1700);
    }
    tourStart();
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((entries) => entries.forEach((en) => onScreen(en.isIntersecting)), { threshold: 0.3 }).observe(stage);
  } else { onScreen(true); }
  document.addEventListener('visibilitychange', () => { if (document.hidden) tourStop(); else if (started) tourStart(); });

  /* ---------- resize: re-measure once, re-place the reticle, redraw the line ---------- */
  let resizeRaf = 0;
  const onResize = () => {
    dropViewRect();
    if (resizeRaf) return;
    resizeRaf = requestAnimationFrame(() => {
      resizeRaf = 0;
      lockReadout();
      if (!measured) return;
      measure();
      const s = spotByKey.get(active);
      if (s) { moveTo(s.x, s.y, false); drawLine(active); } else if (visible) { schedule(); }
    });
  };
  if ('ResizeObserver' in window) new ResizeObserver(onResize).observe(stage); else addEventListener('resize', onResize, { passive: true });
})();

/* ============================================================
   «Что горит на приборной панели» (#pribory): warning-light cluster.
   The cards are rendered by build/pribory.py; without this script they
   stay a readable list. Here: one card at a time, the lamps as toggle
   buttons, the ignition bulb check once when the panel first comes
   into view. No animation loop: every effect is a class switch that
   fades opacity (css/pribory.css).
   ============================================================ */
(() => {
  'use strict';
  const root = document.querySelector('[data-pribory]');
  if (!root) return;
  const G = window.G || {};
  const cluster = root.querySelector('[data-cluster]');
  const lamps = Array.from(root.querySelectorAll('[data-lamp]'));
  const cards = new Map(Array.from(root.querySelectorAll('[data-lamp-card]'), (c) => [c.dataset.lampCard, c]));
  const screen = root.querySelector('.cluster__screen');
  const screenText = root.querySelector('[data-cluster-screen]');
  const live = root.querySelector('[data-pribory-live]');
  if (!cluster || !lamps.length) return;
  const CHECK_MS = 1100;       // how long every lamp stays lit at «ignition»; each then goes out after its own --off delay
  const SEEN = 96;             // px of the card that must show above the bottom edge for the page to stay where it is

  root.classList.add('is-live');   // one card at a time (the section's inline first line normally set this already)

  let current = '';
  let checking = false;
  let checkTimer = 0;

  /* ---------- the trip-computer line ---------- */
  function showOnScreen(key) {
    if (!screen || !screenText) return;
    const card = key ? cards.get(key) : null;
    screenText.textContent = card ? card.dataset.short : screen.dataset[checking ? 'check' : 'idle'];
    if (card) screen.dataset.tone = card.dataset.tone; else screen.removeAttribute('data-tone');
  }

  /* ---------- bring the card into view when it opened below the fold (phones: the card is under the panel) ---------- */
  // page position from offsetTop: unlike getBoundingClientRect it ignores a scroll-reveal that is still sliding in
  const pageTop = (el) => { let y = 0; for (let n = el; n; n = n.offsetParent) y += n.offsetTop; return y; };
  function reveal(card, force) {
    const header = document.querySelector('[data-header]');
    const bar = document.querySelector('.mobile-bar');
    const top = header ? header.getBoundingClientRect().height : 0;
    const bottom = innerHeight - (bar ? bar.getBoundingClientRect().height : 0);
    const y = pageTop(card) - scrollY;
    if (!force && y >= top && y <= bottom - SEEN) return;
    // a link to one lamp shows the panel together with its card when both fit on the screen
    const stage = card.closest('.pribory__stage');
    const target = force && stage && stage.offsetHeight <= bottom - top - 24 ? stage : card;
    scrollTo({ top: Math.max(0, pageTop(target) - top - 12), behavior: G.reducedMotion ? 'auto' : 'smooth' });
  }

  function stopCheck() {
    if (!checking) return;
    checking = false;
    clearTimeout(checkTimer);
    cluster.classList.remove('is-check');
  }

  /* ---------- select a lamp: '' shows the colour legend again ---------- */
  function select(key, opts = {}) {
    if (!cards.has(key)) key = '';
    stopCheck();
    current = key;
    lamps.forEach((b) => {
      const on = b.dataset.lamp === key;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    cards.forEach((c, k) => c.classList.toggle('is-active', k === key));
    cluster.classList.toggle('has-active', !!key);
    showOnScreen(key);
    const card = cards.get(key);
    if (live) {
      const title = key && card.querySelector('.lamp-card__title');
      const urgency = key && card.querySelector('.lamp-card__urgency');
      live.textContent = key ? `${title.textContent}. ${urgency.textContent}` : '';
    }
    if (key && opts.scroll !== false) reveal(card);
  }

  cluster.addEventListener('click', (e) => {
    const b = e.target.closest('[data-lamp]');
    if (!b) return;
    // a second press on the lit lamp switches it off: back to the colour legend (toggle-button semantics)
    select(b.dataset.lamp === current ? '' : b.dataset.lamp);
  });

  /* ---------- the screen previews the lamp under the mouse or the keyboard focus ---------- */
  // keyboard focus only: a mouse click also focuses the button and would leave a stale name on the screen
  const byKeyboard = (el) => { try { return el.matches(':focus-visible'); } catch (_) { return false; } };
  lamps.forEach((b) => {
    b.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') showOnScreen(b.dataset.lamp); });
    b.addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse') showOnScreen(current); });
    b.addEventListener('focus', () => { if (byKeyboard(b)) showOnScreen(b.dataset.lamp); });
    b.addEventListener('blur', () => showOnScreen(current));
  });

  /* ---------- arrows move between lamps as on the grid; Tab still visits every lamp ---------- */
  const columns = () => {
    const top = lamps[0].offsetTop;
    const n = lamps.findIndex((b) => b.offsetTop !== top);
    return n > 0 ? n : lamps.length;
  };
  cluster.addEventListener('keydown', (e) => {
    const i = lamps.indexOf(document.activeElement);
    if (i < 0) return;
    const step = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns(), ArrowUp: -columns() }[e.key];
    let j = step === undefined ? { Home: 0, End: lamps.length - 1 }[e.key] : i + step;
    if (j === undefined) return;
    e.preventDefault();
    j = Math.min(lamps.length - 1, Math.max(0, j));
    lamps[j].focus();
  });

  /* ---------- ignition: all lamps light up for a moment and go out, as when the key is turned ---------- */
  function ignition() {
    cluster.classList.add('is-awake');
    if (current) return;   // a lamp was already chosen (a quick tap or a link to #pribory-…): no light show over it
    checking = true;
    cluster.classList.add('is-check');
    showOnScreen('');
    checkTimer = setTimeout(() => { stopCheck(); showOnScreen(current); }, CHECK_MS);
  }
  if (G.reducedMotion || !('IntersectionObserver' in window)) {
    cluster.classList.add('is-awake');
  } else {
    // most of the panel on screen (or half the screen filled by it, on a short landscape phone)
    const onScreen = (r) => {
      const seen = Math.min(r.bottom, innerHeight) - Math.max(r.top, 0);
      return seen >= r.height * 0.75 || seen >= innerHeight * 0.5;
    };
    const io = new IntersectionObserver((entries) => {
      if (!entries.some((en) => onScreen(en.boundingClientRect))) return;
      io.disconnect();
      // let the scroll-reveal fade the panel in first; if it was only scrolled past, wait for the next time it shows
      setTimeout(() => { if (onScreen(cluster.getBoundingClientRect())) ignition(); else io.observe(cluster); }, 450);
    }, { threshold: [0.25, 0.5, 0.75, 1] });
    io.observe(cluster);
  }

  /* ---------- a link to one lamp: /#pribory-oil opens its card ---------- */
  const fromHash = () => {
    const key = decodeURIComponent(location.hash.replace(/^#pribory-/, ''));
    if (!key || key === location.hash || !cards.has(key)) return;
    select(key, { scroll: false });
    // scroll once the web fonts are in: until then the text above is set in a fallback font and every offset is off
    const go = () => reveal(cards.get(key), true);
    if (document.fonts && document.fonts.status !== 'loaded') document.fonts.ready.then(go); else go();
  };
  fromHash();
  addEventListener('hashchange', fromHash);
})();

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
    // the arrows sit in the section heading, outside the slider, and name their track with aria-controls
    const control = (sel) => (track.id && document.querySelector(`${sel}[aria-controls="${track.id}"]`)) || slider.querySelector(sel);
    const prev = control('[data-prev]');
    const next = control('[data-next]');
    const behavior = G.reducedMotion ? 'auto' : 'smooth';
    const EDGE = 2;   // px of rounding slack at both ends
    // a page is the set of fully visible cards: "next" brings the first cut-off card to the left edge,
    // "prev" goes back until the current first card becomes the last visible one
    const starts = () => {
      const left = track.getBoundingClientRect().left - track.scrollLeft;
      return Array.from(track.children, (el) => {
        const r = el.getBoundingClientRect();
        return { start: r.left - left, end: r.right - left };
      });
    };
    const maxLeft = () => track.scrollWidth - track.clientWidth;
    const go = (dir) => {
      const x = track.scrollLeft;
      const cards = starts();
      let target;
      if (dir > 0) {
        const cut = cards.find((c) => c.end > x + track.clientWidth + EDGE);
        target = cut ? cut.start : maxLeft();
      } else {
        const back = cards.find((c) => c.start >= x - track.clientWidth - EDGE);
        target = back && back.start < x - EDGE ? back.start : 0;
      }
      track.scrollTo({ left: Math.max(0, Math.min(target, maxLeft())), behavior });
    };
    if (prev) prev.addEventListener('click', () => go(-1));
    if (next) next.addEventListener('click', () => go(1));
    const update = () => {
      const noScroll = maxLeft() <= EDGE;
      if (prev) prev.disabled = noScroll || track.scrollLeft <= EDGE;
      if (next) next.disabled = noScroll || track.scrollLeft >= maxLeft() - EDGE;
    };
    track.addEventListener('scroll', update, { passive: true });
    if ('ResizeObserver' in window) new ResizeObserver(update).observe(track); else addEventListener('resize', update, { passive: true });
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

/* ============================================================
   request form (3 steps), callback modal, login modal
   Backend endpoints are the same as on the current garage.team:
   POST /call/request, POST /call, POST /findcar/requestmodels/id/<brand>,
   POST /findcar/requestsizes/, POST /login/popup, /email/lostpass, /sms/lostpass
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  const required = (fields) => {
    let ok = true;
    fields.forEach((f) => {
      if (!f || f.closest('[hidden]') || f.disabled) return;
      let bad;
      if (f.type === 'checkbox') bad = !f.checked;
      else if (f.tagName === 'SELECT') bad = !f.value || f.value === '-1';
      else if (f.dataset.phone !== undefined) bad = !G.validPhone(f.value);
      else bad = !f.value.trim();
      if (bad) ok = false;
      G.setError(f, bad);
    });
    return ok;
  };

  const fill = (select, placeholder, rows) => {
    select.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '-1'; opt.textContent = placeholder;
    select.appendChild(opt);
    rows.forEach((r) => { const o = document.createElement('option'); o.value = String(r.id); o.textContent = r.name; select.appendChild(o); });
    select.disabled = false;
  };

  const postJSON = async (url, params) => {
    const res = await fetch(url, { method: 'POST', body: params ? new URLSearchParams(params) : undefined, headers: { 'X-Requested-With': 'XMLHttpRequest', Accept: 'application/json' }, credentials: 'same-origin' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  };

  /* ---------- request form ---------- */
  $$('[data-rq]').forEach((form) => {
    const steps = $$('.step', form);
    const panels = $$('.rq__panel', form);
    const modeInput = $('input[name="request_part[select_car_type]"]', form);
    const selectMode = $('[data-mode="select"]', form);
    const textMode = $('[data-mode="text"]', form);
    const brand = $('#tecdoc_car_brand', form);
    const model = $('#tecdoc_car_model', form);
    const year = $('#tecdoc_car_year', form);
    const type = $('#tecdoc_car_type', form);
    const alertBox = $('[data-alert]', form);
    const success = $('[data-success]', form);
    let models = {};
    let current = 1;

    G.clearErrorsOnInput(form);

    const show = (n) => {
      current = n;
      panels.forEach((p) => p.classList.toggle('is-active', Number(p.dataset.panel) === n));
      steps.forEach((s) => {
        const i = Number(s.dataset.step);
        s.classList.toggle('is-active', i === n);
        s.classList.toggle('is-done', i < n);
      });
      if (n > 1) form.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'start' });
      const first = $(`.rq__panel[data-panel="${n}"] input:not([type=hidden]):not([disabled]), .rq__panel[data-panel="${n}"] select:not([disabled])`, form);
      // phones: no automatic focus, it would open the keyboard or a select wheel on its own (see G.openModal)
      if (first && n > 1 && G.canHover) setTimeout(() => first.focus(), 350);
    };

    /* car selection mode toggle */
    const setMode = (mode, note) => {
      const isSelect = mode === 'select';
      if (modeInput) modeInput.value = isSelect ? '1' : '0';
      if (selectMode) selectMode.hidden = !isSelect;
      if (textMode) textMode.hidden = isSelect;
      $$('[data-mode-toggle]', form).forEach((b) => { b.textContent = isSelect ? 'Не нашли свой автомобиль?' : 'Выбрать из списка'; });
      if (note) G.toast(note, 'err');
    };
    $$('[data-mode-toggle]', form).forEach((b) => b.addEventListener('click', () => setMode(modeInput && modeInput.value === '1' ? 'text' : 'select')));

    /* dependent selects (backend of garage.team) */
    if (brand && model && year && type) {
      brand.addEventListener('change', async () => {
        fill(model, 'Выберите модель', []); model.disabled = true;
        fill(year, 'Выберите год', []); year.disabled = true;
        fill(type, 'Выберите модификацию', []); type.disabled = true;
        if (brand.value === '-1') return;
        try {
          const json = await postJSON('/findcar/requestmodels/id/' + encodeURIComponent(brand.value));
          const rows = (json && json.data) || [];
          models = {};
          rows.forEach((r) => { models[r.id] = r; });
          fill(model, 'Выберите модель', rows);
          model.focus();
        } catch (_) {
          setMode('text', 'Список моделей сейчас недоступен — укажите автомобиль вручную');
        }
      });
      model.addEventListener('change', () => {
        fill(year, 'Выберите год', []); year.disabled = true;
        fill(type, 'Выберите модификацию', []); type.disabled = true;
        const m = models[model.value];
        if (!m) return;
        const now = new Date().getFullYear();
        const start = Number(m.year_start) || now - 30;
        const end = Number(m.year_end) || now;
        const rows = [];
        for (let y = end; y >= start; y -= 1) rows.push({ id: y, name: String(y) });
        fill(year, 'Выберите год', rows);
        year.focus();
      });
      year.addEventListener('change', async () => {
        fill(type, 'Выберите модификацию', []); type.disabled = true;
        if (year.value === '-1') return;
        try {
          const json = await postJSON('/findcar/requestsizes/', { id: model.value, year: year.value });
          fill(type, 'Выберите модификацию', (json && json.data) || []);
        } catch (_) { type.disabled = true; }
      });
    }

    /* VIN helper */
    $$('[data-vin-help]', form).forEach((b) => b.addEventListener('click', () => {
      const box = $('[data-vin-help-text]', form);
      if (box) box.hidden = !box.hidden;
    }));

    /* parts list */
    const partsBox = $('[data-parts]', form);
    const addPart = () => {
      const n = $$('.part', partsBox).length + 1;
      const row = document.createElement('div');
      row.className = 'part';
      row.innerHTML = `
        <div class="field"><label class="field__label" for="part_name_${n}">Запчасть №${n}</label><input class="input" id="part_name_${n}" name="request_part[parts][${n}][name]" type="text" placeholder="Например: противотуманные фары"></div>
        <div class="field"><label class="field__label" for="part_count_${n}">Кол-во, шт.</label><input class="input" id="part_count_${n}" name="request_part[parts][${n}][count]" type="number" min="1" value="1"></div>
        <button type="button" class="part__remove" aria-label="Удалить запчасть"><svg class="ic" aria-hidden="true"><use href="#i-close"/></svg></button>`;
      partsBox.appendChild(row);
      $('input', row).focus();
    };
    if (partsBox) {
      $$('[data-add-part]', form).forEach((b) => b.addEventListener('click', addPart));
      partsBox.addEventListener('click', (e) => {
        const btn = e.target.closest('.part__remove');
        if (!btn) return;
        if ($$('.part', partsBox).length <= 1) return;
        btn.closest('.part').remove();
        $$('.part', partsBox).forEach((row, i) => {
          const n = i + 1;
          row.querySelector('label').textContent = `Запчасть №${n}`;
          row.querySelector('input[type=text]').name = `request_part[parts][${n}][name]`;
          row.querySelector('input[type=number]').name = `request_part[parts][${n}][count]`;
        });
      });
    }

    /* step validation */
    const validateStep = (n) => {
      if (n === 1) {
        const isSelect = !modeInput || modeInput.value === '1';
        return isSelect
          ? required([brand, model, year])
          : required([$('#text_car_brand', form), $('#text_car_model', form), $('#text_car_year', form), $('#text_car_type', form)]);
      }
      if (n === 2) {
        const first = $('.part input[type=text]', form);
        const filled = $$('.part input[type=text]', form).some((i) => i.value.trim());
        const comment = $('[name="request_part[what]"]', form);
        const ok = filled || (comment && comment.value.trim());
        if (first) G.setError(first, !ok);
        return !!ok;
      }
      if (n === 3) {
        return required([$('[name="request_part[contact_name]"]', form), $('[name="request_part[city]"]', form), $('[name="request_part[contact_phone]"]', form), $('[name="agree"]', form)]);
      }
      return true;
    };

    $$('[data-next]', form).forEach((b) => b.addEventListener('click', () => {
      if (!validateStep(current)) { G.toast('Заполните обязательные поля', 'err'); return; }
      show(Math.min(3, current + 1));
    }));
    $$('[data-prev]', form).forEach((b) => b.addEventListener('click', () => show(Math.max(1, current - 1))));
    steps.forEach((s) => s.addEventListener('click', () => { const n = Number(s.dataset.step); if (n < current) show(n); }));

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!validateStep(3)) { G.toast('Заполните обязательные поля', 'err'); return; }
      const btn = $('[type=submit]', form);
      btn.disabled = true; btn.classList.add('is-loading');
      if (alertBox) alertBox.classList.remove('is-visible');
      try {
        await G.postForm(form);
        panels.forEach((p) => p.classList.remove('is-active'));
        $('.steps', form).hidden = true;
        if (success) success.classList.add('is-visible');
        form.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'center' });
      } catch (err) {
        if (alertBox) {
          alertBox.textContent = 'Не удалось отправить заявку. Позвоните нам: (831) 416-16-77 — менеджер примет запрос по телефону.';
          alertBox.classList.add('is-visible');
        }
        G.toast('Ошибка отправки. Позвоните: (831) 416-16-77', 'err');
      } finally { btn.disabled = false; btn.classList.remove('is-loading'); }
    });
    show(1);
  });

  /* ---------- simple modal forms (callback, login, lost password) ---------- */
  $$('form[data-simple-form]').forEach((form) => {
    G.clearErrorsOnInput(form);
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fields = $$('[required]', form);
      if (!required(fields)) { G.toast('Заполните обязательные поля', 'err'); return; }
      const btn = $('[type=submit]', form);
      if (btn) btn.disabled = true;
      try {
        const data = await G.postForm(form);
        const succ = $('[data-success]', form);
        if (form.dataset.redirect && data && data.redirect) { location.href = data.redirect; return; }
        if (succ) { $$('[data-body]', form).forEach((b) => { b.hidden = true; }); succ.classList.add('is-visible'); }
        else { G.toast(form.dataset.successText || 'Отправлено', 'ok'); const dlg = form.closest('dialog'); if (dlg) G.closeModal(dlg); }
      } catch (err) {
        G.toast(form.dataset.errorText || 'Не удалось отправить. Позвоните: (831) 416-16-77', 'err');
      } finally { if (btn) btn.disabled = false; }
    });
  });

  /* login modal: forgot password toggle */
  const login = $('#modal-login');
  if (login) {
    const lost = $('[data-lost]', login);
    $$('[data-lost-toggle]', login).forEach((b) => b.addEventListener('click', () => { if (lost) lost.hidden = !lost.hidden; }));
    const sms = $('[data-sms]', login);
    if (sms) sms.addEventListener('click', async () => {
      const area = $('input[name="UserLoginForm[areaCode]"]', login);
      const num = $('input[name="UserLoginForm[number]"]', login);
      const phone = ((area && area.value) || '') + ((num && num.value) || '');
      if (!/^9\d{9}$/.test(phone)) { G.setError(num, true); G.toast('Введите номер телефона в формате 9XXXXXXXXX', 'err'); return; }
      try { await postJSON('/sms/lostpass', { phone }); G.toast('Пароль отправлен по СМС', 'ok'); }
      catch (_) { G.toast('Не удалось отправить СМС. Позвоните: (831) 416-16-77', 'err'); }
    });
    const emailBtn = $('[data-email-lost]', login);
    if (emailBtn) emailBtn.addEventListener('click', async () => {
      const email = $('input[name="lost-email"]', login);
      if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value)) { if (email) G.setError(email, true); G.toast('Введите корректный e-mail', 'err'); return; }
      try { await postJSON('/email/lostpass', { email: email.value }); G.toast('Пароль отправлен на e-mail', 'ok'); }
      catch (_) { G.toast('Не удалось отправить письмо. Позвоните: (831) 416-16-77', 'err'); }
    });
  }

  /* dialogs: reset simple forms on close */
  $$('dialog').forEach((d) => d.addEventListener('close', () => {
    $$('form[data-simple-form]', d).forEach((f) => { f.reset(); $$('[data-body]', f).forEach((b) => { b.hidden = false; }); const s = $('[data-success]', f); if (s) s.classList.remove('is-visible'); $$('.field', f).forEach((x) => x.classList.remove('is-error')); });
  }));
})();

/* ============================================================
   winter checklist on the home page (#zima, build/zima.py):
   ticks → instrument gauge, unticked items → message for the call modal or the request form.
   What keeps it cheap:
     1. nothing runs until the section is ~600px away (IntersectionObserver);
     2. the needle turns and the segments fade in by CSS transitions (transform / opacity only);
     3. the only requestAnimationFrame loop counts the percentage for 0.7–1.2 s after a change, then stops.
   Ticks and the engine type are kept in localStorage (wrapped in try/catch: private mode, blocked storage).
   ============================================================ */
(() => {
  'use strict';
  const root = document.querySelector('[data-zima]');
  if (!root) return;
  const G = window.G || {};
  const $ = (s, r = root) => r.querySelector(s);
  const $$ = (s, r = root) => Array.from(r.querySelectorAll(s));
  const KEY = 'garage.zima.v1';
  const START = -120;           // needle angle at 0 %, degrees (build/zima.py: START, SWEEP)
  const SWEEP = 240;
  const TICK_MS = 700;           // the count after a tick (the needle: 0.85 s with a small overshoot, zima.css)
  const WAKE_MS = 1200;          // first sweep to the saved value: .zima.is-awake in zima.css has the same duration
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  const easeInOut = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(2 - 2 * p, 3) / 2);
  const easeInOutInv = (q) => (q < 0.5 ? Math.cbrt(q / 4) : 1 - Math.cbrt(2 * (1 - q)) / 2);

  const plural = (n, one, few, many) => {
    const m10 = n % 10; const m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
    return many;
  };
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

  const load = () => {
    try {
      const s = JSON.parse(localStorage.getItem(KEY) || 'null');
      return s && typeof s === 'object' ? s : null;
    } catch (_) { return null; }
  };

  function init() {
    const items = $$('.zima-item');
    const inputs = new Map(items.map((li) => [li, $('.zima-item__input', li)]));
    const radios = $$('input[name="zima-engine"]');
    const dial = $('.zima-dial');
    const needle = $('.zima-dial__needle');
    const segs = $$('.zima-dial__seg');
    const glow = $('.zima-dial__glow');
    const pctEl = $('[data-zima-pct]');
    const countEl = $('[data-zima-count]');
    const titleEl = $('[data-zima-title]');
    const textEl = $('[data-zima-text]');
    const live = $('[data-zima-live]');
    const reset = $('[data-zima-reset]');
    const mini = $('[data-zima-mini]');
    const cells = $$('.zima-mini__bar i');
    const book = $('[data-zima-book]');
    const add = $('[data-zima-add]');
    const hintTitle = titleEl ? titleEl.textContent : '';
    const hintText = textEl ? textEl.textContent : '';

    let engine = (radios.find((r) => r.checked) || {}).value || 'petrol';
    let awake = false;          // the dial shows the real value once it has been on screen
    let shown = 0;              // percentage currently printed in the dial
    let raf = 0;

    const visible = () => items.filter((li) => !li.hidden);
    const done = (li) => inputs.get(li).checked;

    /* ---------- state: restore, save ---------- */
    const saved = load();
    if (saved) {
      if (saved.engine === 'diesel' || saved.engine === 'petrol') engine = saved.engine;
      const set = new Set(Array.isArray(saved.done) ? saved.done : []);
      items.forEach((li) => { inputs.get(li).checked = set.has(li.dataset.key); });
    }
    const save = () => {
      try {
        localStorage.setItem(KEY, JSON.stringify({ engine, done: items.filter(done).map((li) => li.dataset.key) }));
      } catch (_) { /* storage unavailable: the checklist still works for this visit */ }
    };
    const applyEngine = (animate) => {
      radios.forEach((r) => { r.checked = r.value === engine; });
      items.forEach((li) => {
        if (!li.dataset.engine) return;
        const was = li.hidden;
        li.hidden = li.dataset.engine !== engine;
        if (animate && was && !li.hidden) {   // the item that comes in for the other engine fades in once
          li.classList.remove('is-swap');
          void li.offsetWidth;
          li.classList.add('is-swap');
        }
      });
    };

    /* ---------- the message: unticked items in plain words ---------- */
    const message = () => {
      const left = visible().filter((li) => !done(li)).map((li) => li.dataset.acc);
      const head = `Подготовка к зиме (${engine === 'diesel' ? 'дизель' : 'бензин'})`;
      return left.length
        ? `${head}: проверить ${left.join(', ')}.`   // commas only: the items have «и» inside («свет и фары»)
        : `${head}: по чек-листу на сайте всё отмечено, хочу записаться на общую проверку перед зимой.`;
    };

    /* ---------- gauge ---------- */
    const countTo = (to, animate, ms = TICK_MS, ease = easeOut) => {
      cancelAnimationFrame(raf);
      if (!animate || G.reducedMotion) { shown = to; pctEl.textContent = String(to); return; }
      const from = shown; const t0 = performance.now();
      const step = (t) => {
        const p = Math.min(1, (t - t0) / ms);
        shown = Math.round(from + (to - from) * ease(p));
        pctEl.textContent = String(shown);
        raf = p < 1 ? requestAnimationFrame(step) : 0;
      };
      raf = requestAnimationFrame(step);
    };

    const render = (opts = {}) => {
      const list = visible();
      const total = list.length || 1;
      const left = list.filter((li) => !done(li));
      const n = total - left.length;
      const ready = n === total;
      const pct = Math.round((n / total) * 100);
      const lit = Math.round((n / total) * segs.length);

      items.forEach((li) => li.classList.toggle('is-done', done(li)));
      root.classList.toggle('is-ready', ready);
      root.classList.toggle('is-empty', n === 0);
      if (reset) reset.disabled = n === 0;
      if (dial) {
        dial.setAttribute('aria-valuemax', String(total));
        dial.setAttribute('aria-valuenow', String(n));
        dial.setAttribute('aria-valuetext', ready ? `Отмечено ${n} из ${total}: машина готова к зиме` : `Отмечено ${n} из ${total}`);
      }

      // status: what is left, three names at most so the card keeps its height
      if (titleEl && textEl) {
        if (ready) {
          titleEl.textContent = 'Машина готова к зиме';
          textEl.textContent = 'Все пункты отмечены — можно встречать зиму спокойно.';
        } else if (n === 0) {
          titleEl.textContent = hintTitle;
          textEl.textContent = hintText;
        } else {
          titleEl.textContent = `Осталось ${left.length} ${plural(left.length, 'пункт', 'пункта', 'пунктов')}`;
          const names = left.map((li) => $('.zima-item__name', li).textContent.toLowerCase());
          const shownNames = names.length > 3 ? `${names.slice(0, 3).join(', ')} и ещё ${names.length - 3}` : names.join(', ');
          textEl.textContent = `${cap(shownNames)}.`;
        }
      }

      // mini bar (phones): no counting, it just follows
      if (mini) mini.textContent = String(pct);
      cells.forEach((c, i) => c.classList.toggle('is-on', i < lit));

      // the dial stays at zero until it has been seen, then wakes up to the saved value
      if (awake) {
        if (needle) needle.style.transform = `rotate(${START + SWEEP * (n / total)}deg)`;
        segs.forEach((s, i) => s.classList.toggle('is-on', i < lit));
        if (countEl) countEl.textContent = String(n);
        if (glow) glow.style.opacity = ready ? '1' : String(0.12 + 0.38 * (n / total));
        if (opts.wake && !G.reducedMotion) {
          // each segment lights up as the sweeping needle passes its middle
          segs.forEach((sg, i) => { sg.style.transitionDelay = i < lit ? `${Math.round(easeInOutInv((i + 0.5) / lit) * WAKE_MS)}ms` : ''; });
          countTo(pct, true, WAKE_MS, easeInOut);
        } else countTo(pct, opts.animate !== false);
      }

      if (opts.announce && live) {
        live.textContent = ready ? `Отмечено ${n} из ${total}. Машина готова к зиме.` : `Отмечено ${n} из ${total}. Осталось ${left.length} ${plural(left.length, 'пункт', 'пункта', 'пунктов')}.`;
      }
      if (book) book.dataset.preset = JSON.stringify({ message: message() });
    };

    /* ---------- events ---------- */
    root.addEventListener('change', (e) => {
      const t = e.target;
      if (t.name === 'zima-engine') {
        engine = t.value;
        applyEngine(true);
        render({ announce: true });
        save();
        return;
      }
      if (t.classList.contains('zima-item__input')) {
        render({ announce: true });
        save();
      }
    });

    if (reset) reset.addEventListener('click', () => {
      items.forEach((li) => { inputs.get(li).checked = false; });
      render();
      save();
      if (live) live.textContent = 'Отметки сброшены.';
      // the button disables itself: keep the keyboard focus inside the card
      const first = visible()[0];
      if (first && document.activeElement === reset) inputs.get(first).focus();
    });

    // «Записаться…» is a data-modal="call" button: its preset is refreshed here, core.js opens the modal
    if (book) book.addEventListener('click', () => { book.dataset.preset = JSON.stringify({ message: message() }); });

    // «Добавить в заявку»: the text goes to the request form (step 2, «Или опишите задачу»), the link scrolls to it
    const what = document.getElementById('request_what');
    let inserted = '';
    if (add && !what) add.hidden = true;
    if (add && what) add.addEventListener('click', (e) => {
      const text = message();
      const cur = what.value;
      if (inserted && cur.includes(inserted)) what.value = cur.replace(inserted, () => text);
      else what.value = cur.trim() ? `${cur.replace(/\s+$/, '')}\n${text}` : text;
      inserted = text;
      what.dispatchEvent(new Event('input', { bubbles: true }));   // clears a «fill in the field» error of the form
      const panel = what.closest('.rq__panel');
      if (panel && panel.classList.contains('is-active')) {
        // the visitor is already on step 2: go straight to the field
        e.preventDefault();
        what.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'center' });
        if (G.canHover) setTimeout(() => what.focus({ preventScroll: true }), 400);
        if (G.toast) G.toast('Список добавлен в заявку');
      } else if (G.toast) {
        G.toast('Список добавлен в заявку — он будет на шаге 2 «Ввод запроса»');
      }
    });

    /* ---------- start ---------- */
    applyEngine();
    render({ animate: false });

    const wake = () => {
      if (awake) return;
      awake = true;
      root.classList.add('is-awake');
      render({ wake: true });
      // after the first sweep the needle answers each tick with a shorter, livelier move
      setTimeout(() => { root.classList.remove('is-awake'); segs.forEach((sg) => { sg.style.transitionDelay = ''; }); }, WAKE_MS + 300);
    };
    if (G.reducedMotion || !('IntersectionObserver' in window) || !dial) wake();
    else {
      const io = new IntersectionObserver((entries) => {
        // a short pause lets the card finish most of its scroll-reveal fade before the needle starts
        if (entries.some((en) => en.isIntersecting)) { io.disconnect(); setTimeout(wake, 220); }
      }, { threshold: 0.35 });
      io.observe(dial);
    }

    // phones: while the dial is off screen, a slim progress bar follows the list (see .zima-mini)
    const gauge = $('.zima-gauge');
    if (gauge && 'IntersectionObserver' in window) {
      new IntersectionObserver((entries) => {
        entries.forEach((en) => root.classList.toggle('is-away', !en.isIntersecting));
      }, { threshold: 0 }).observe(gauge);
    }
  }

  if (!('IntersectionObserver' in window)) { init(); return; }
  const io = new IntersectionObserver((entries) => {
    if (entries.some((en) => en.isIntersecting)) { io.disconnect(); init(); }
  }, { rootMargin: '600px 0px' });
  io.observe(root);
})();

/* ============================================================
   «Что стучит?» (home page, section #stuk, table in build/stuk.py):
   what was noticed → when → (where) → possible causes with links to the
   service pages and a ready request text for the callback modal or the
   request form. The table is fetched only when the section comes near the
   screen; there are no loops or timers, only clicks.
   ============================================================ */
(() => {
  'use strict';
  const root = document.querySelector('[data-stuk]');
  if (!root) return;
  const G = window.G || {};
  const $ = (s, r = root) => r.querySelector(s);
  const $$ = (s, r = root) => Array.from(r.querySelectorAll(s));
  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ESC[c]);
  // «Стойки стабилизатора» → «стойки стабилизатора», but «ТНВД» and «ABS» stay as they are
  const lower = (s) => (s.length > 1 && s[1] === s[1].toLowerCase() ? s[0].toLowerCase() + s.slice(1) : s);
  const pad2 = (n) => String(n).padStart(2, '0');
  const ic = (name) => `<svg class="ic" aria-hidden="true" focusable="false"><use href="#i-${name}"/></svg>`;

  const steps = [1, 2, 3].map((n) => $(`[data-q="${n}"]`));
  const tiles = $$('.stuk-sym');
  const chipsBox = $('[data-chips]');
  const zoneBtns = $$('.stuk-zone');
  const car = $('.stuk-car__svg');
  const out = $('[data-out]');
  const idle = $('[data-idle]');
  const res = $('[data-res]');
  const resBody = $('[data-res-body]');
  const resLabel = $('[data-res-label]');
  const cta = $('[data-cta]');
  const live = $('[data-live]');
  const narrow = matchMedia('(max-width: 1099px)');   // one column: answered questions fold (stuk.css)
  const ZONE_KEYS = ['front', 'hood', 'under', 'rear'];

  let data = null;
  let loading = null;
  let lastAdded = '';
  const state = { s: null, c: null, z: null };

  /* ---------- data: fetched once, when the section is about to be seen (or on the first tap) ---------- */
  const load = () => {
    if (data) return Promise.resolve(data);
    if (!loading) {
      loading = fetch(root.dataset.src, { credentials: 'same-origin' })
        .then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then((json) => { data = json; return json; })
        .catch((err) => {
          loading = null;
          showError();
          throw err;
        });
    }
    return loading;
  };
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      if (entries.some((en) => en.isIntersecting)) { io.disconnect(); load().catch(() => {}); }
    }, { rootMargin: '600px 0px' });
    io.observe(root);
  } else {
    load().catch(() => {});
  }

  /* ---------- lookups ---------- */
  const sym = () => (data && state.s ? data.s[state.s] : null);
  const ctx = () => { const s = sym(); return s && state.c ? s.c.find((c) => c[0] === state.c) || null : null; };
  const zonesOf = (c) => (c && c[5]) || {};
  const causeKeys = () => { const c = ctx(); const z = zonesOf(c); return state.z && z[state.z] ? z[state.z] : c[4]; };
  const say = () => ctx()[2].replace('{где}', state.z ? data.z[state.z][1] : '');
  const words = (k) => data.c[k][3] || lower(data.c[k][0]);
  const message = () => `${say()}. Возможные причины: ${causeKeys().map(words).join(', ')}.`;

  /* ---------- painting ---------- */
  const announce = (text) => {
    live.textContent = '';
    requestAnimationFrame(() => { live.textContent = text; });
  };

  const setStep = (n, { value = '', done = false, current = false } = {}) => {
    const step = steps[n - 1];
    step.classList.toggle('is-done', done);
    step.classList.toggle('is-current', current);
    step.classList.remove('is-editing');
    $('[data-val]', step).textContent = value;
  };

  const paintTiles = () => {
    tiles.forEach((t) => t.setAttribute('aria-pressed', String(t.dataset.s === state.s)));
    root.classList.toggle('has-s', !!state.s);
  };

  const renderChips = () => {
    const s = sym();
    $('#stuk-q2').textContent = s ? s.q2 : 'Когда?';
    $('[data-wait]').hidden = !!s;
    chipsBox.hidden = !s;
    if (!s) { chipsBox.innerHTML = ''; return; }
    chipsBox.innerHTML = s.c.map((c, i) => {
      const sw = c[6] ? `<span class="stuk-chip__sw" style="--sw:${esc(c[6])}" aria-hidden="true"></span>` : '';
      return `<button class="stuk-chip" type="button" aria-pressed="false" data-c="${esc(c[0])}" style="--i:${i}">${sw}${esc(c[1])}</button>`;
    }).join('');
    // restart the entrance animation of the new set of chips
    chipsBox.classList.remove('is-in');
    void chipsBox.offsetWidth;
    chipsBox.classList.add('is-in');
  };

  const paintChips = () => {
    $$('.stuk-chip', chipsBox).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.c === state.c)));
  };

  const paintZones = () => {
    const c = ctx();
    const zones = zonesOf(c);
    const on = (k) => Object.prototype.hasOwnProperty.call(zones, k);
    const where = steps[2];
    where.hidden = !Object.keys(zones).length;
    if (where.hidden) return;
    $('#stuk-q3').textContent = sym().q3 || 'Где?';
    zoneBtns.forEach((b) => {
      b.hidden = !on(b.dataset.z);
      b.setAttribute('aria-pressed', String(b.dataset.z === state.z));
    });
    ZONE_KEYS.forEach((k) => {
      $$(`.z-${k}, .stuk-car__hit[data-z="${k}"]`, car).forEach((el) => {
        el.classList.toggle('is-on', on(k));
        el.classList.toggle('is-sel', k === state.z);
      });
    });
  };

  // «норма» items get a check instead of a number, so the faults are counted 01, 02… on their own
  const causeHTML = (k, i, keys) => {
    const [title, text, page] = data.c[k];
    const n = keys.slice(0, i + 1).filter((x) => data.c[x][2]).length;
    if (!page) {
      return `<li class="stuk-cause stuk-cause--ok" style="--i:${i}"><span class="stuk-cause__n">${ic('check')}</span>` +
        `<div class="stuk-cause__b"><p class="stuk-cause__t">${esc(title)} <span class="stuk-cause__tag">норма</span></p><p class="stuk-cause__x">${esc(text)}</p></div></li>`;
    }
    const [href, name] = data.p[page];
    return `<li class="stuk-cause" style="--i:${i}"><span class="stuk-cause__n">${pad2(n)}</span>` +
      `<div class="stuk-cause__b"><p class="stuk-cause__t">${esc(title)}</p>` +
      `<a class="stuk-cause__a" href="${esc(href)}">${esc(name)} ${ic('arrow-up-right')}</a>` +
      `<p class="stuk-cause__x">${esc(text)}</p></div></li>`;
  };

  const renderOut = () => {
    const s = sym();
    const c = ctx();
    idle.hidden = !!s;
    res.hidden = !s;
    out.classList.toggle('is-on', !!c);
    cta.hidden = !c;
    if (!s) { resBody.innerHTML = ''; return; }
    if (!c) {
      // a symptom without its context yet: what usually gives it and what to answer next
      resLabel.textContent = '// Подсказка';
      resBody.innerHTML = `<h3 class="stuk-res__title" tabindex="-1">${esc(s.n)}</h3>` +
        `<p class="stuk-res__lead">${esc(s.lead)}</p>` +
        `<p class="stuk-res__next stuk-res__next--ask">${ic('arrow')}<span>${esc(s.q2)}</span></p>`;
      return;
    }
    const keys = causeKeys();
    const [diagHref, diagName] = data.p[c[3]];
    const needWhere = Object.keys(zonesOf(c)).length && !state.z;
    resLabel.textContent = '// Возможные причины';
    resBody.innerHTML = `<h3 class="stuk-res__title" tabindex="-1">${esc(say())}</h3>` +
      (needWhere ? `<p class="stuk-res__next">${ic('arrow')}<span>${esc(s.q3)} Уточните\u00a0— список станет точнее.</span></p>` : '') +
      `<ol class="stuk-causes">${keys.map(causeHTML).join('')}</ol>` +
      `<p class="stuk-res__note">${ic('info')}<span>Это подсказка, а не диагноз: один и тот же признак дают разные узлы. ` +
      `Точную причину покажет <a href="${esc(diagHref)}">${esc(lower(diagName))}</a>.</span></p>` +
      `<div class="stuk-res__msg"><p class="stuk-res__msg-label">Текст для заявки</p><p class="stuk-res__msg-text">${esc(message())}</p></div>`;
  };

  const paint = () => {
    paintTiles();
    paintChips();
    paintZones();
    renderOut();
    const s = sym();
    const c = ctx();
    setStep(1, { value: s ? s.n : '', done: !!s, current: !s });
    setStep(2, { value: c ? c[1] : '', done: !!c, current: !!s && !c });
    setStep(3, { value: state.z ? data.z[state.z][0] : '', done: !!state.z, current: !!c && !state.z });
  };

  /* ---------- phones and tablets: keep the answer in view ---------- */
  const headerH = () => { const h = document.querySelector('[data-header]'); return h ? h.getBoundingClientRect().height : 0; };
  const bringIntoView = () => {
    if (!narrow.matches) return;
    const top = out.getBoundingClientRect().top;
    if (top > headerH() && top < innerHeight * 0.6) return;
    const app = $('[data-app]').getBoundingClientRect().top + scrollY - headerH() - 12;
    scrollTo({ top: app, behavior: G.reducedMotion ? 'auto' : 'smooth' });
  };
  // keyboard users land on the next thing to answer when the question they answered folds away
  const focusNext = (el) => { if (el && narrow.matches) el.focus({ preventScroll: true }); };

  /* ---------- actions ---------- */
  const pickSymptom = (key, byKeyboard) => {
    if (state.s !== key) { state.s = key; state.c = null; state.z = null; renderChips(); }
    paint();
    const s = sym();
    announce(`${s.n}. ${s.q2}`);
    if (byKeyboard) focusNext($('.stuk-chip', chipsBox));
  };

  const pickContext = (key, byKeyboard) => {
    state.c = key;
    state.z = null;
    paint();
    const titles = causeKeys().map((k) => lower(data.c[k][0]));
    announce(`${say()}. Возможные причины: ${titles.join(', ')}. Это подсказка, а не диагноз.`);
    bringIntoView();
    if (byKeyboard) focusNext(steps[2].hidden ? $('.stuk-res__title') : $('.stuk-zone:not([hidden])'));
  };

  const pickZone = (key, byKeyboard) => {
    const c = ctx();
    if (!c || !Object.prototype.hasOwnProperty.call(zonesOf(c), key)) return;
    state.z = state.z === key ? null : key;   // tapping the chosen place again goes back to the general list
    paint();
    const titles = causeKeys().map((k) => lower(data.c[k][0]));
    announce(`${say()}. Возможные причины: ${titles.join(', ')}.`);
    bringIntoView();
    if (byKeyboard) focusNext($('.stuk-res__title'));
  };

  const reset = (byKeyboard) => {
    state.s = null; state.c = null; state.z = null;
    renderChips();
    paint();
    announce('Подсказка очищена. Что заметили?');
    if (narrow.matches) {
      const top = $('[data-app]').getBoundingClientRect().top;
      if (top < headerH()) scrollTo({ top: top + scrollY - headerH() - 12, behavior: G.reducedMotion ? 'auto' : 'smooth' });
    }
    if (byKeyboard) tiles[0].focus({ preventScroll: true });
  };

  const preset = (value) => {
    const [s, c, z] = value.split('|');
    state.s = s; state.c = null; state.z = null;
    renderChips();
    pickContext(c);
    if (z) pickZone(z);
  };

  const edit = (n) => {
    const step = steps[n - 1];
    step.classList.add('is-editing');
    const chosen = $('[aria-pressed="true"]', step) || $('button:not([hidden]):not([data-edit])', $('.stuk-q__body', step));
    if (chosen) chosen.focus({ preventScroll: true });
    step.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
  };

  const callback = () => { if (G.openModal) G.openModal('call', { message: message() }); };

  // the request form keeps the text through its own steps: it only validates and posts request_part[what]
  const toRequest = () => {
    const text = message();
    const form = document.getElementById('request-form');
    const field = document.getElementById('request_what');
    const section = document.getElementById('request');
    const sent = form && form.querySelector('[data-success].is-visible');
    if (!form || !field || !section || sent) { callback(); return; }
    const current = field.value.trim();
    if (lastAdded && current.includes(lastAdded)) field.value = current.replace(lastAdded, text);
    else field.value = current ? `${current}\n${text}` : text;
    lastAdded = text;
    field.dispatchEvent(new Event('input', { bubbles: true }));

    // the form may still be on its first step (the car): a note at the top of that step says where the text went;
    // on the description step the text is in plain sight
    const panel = form.querySelector('.rq__panel.is-active');
    $$('.stuk-rq-note', form).forEach((n) => n.remove());
    if (panel && panel.dataset.panel !== '2') {
      const note = document.createElement('p');
      note.className = 'stuk-rq-note';
      note.innerHTML = `${ic('check')}<span>Описание неисправности уже в заявке, на шаге 2 «Ввод запроса».</span>`;
      panel.insertBefore(note, panel.firstElementChild);
    }
    announce('Описание добавлено в заявку, на шаг 2 «Ввод запроса».');
    // on a phone the section starts with its heading and texts, the form itself is a screen lower
    (narrow.matches ? form : section).scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'start' });
    if (G.canHover) {
      const first = panel && panel.dataset.panel === '2' ? field
        : panel && panel.querySelector('select:not([disabled]), input:not([type=hidden]):not([disabled])');
      if (first) setTimeout(() => first.focus({ preventScroll: true }), 450);
    }
  };

  const showError = () => {
    idle.hidden = true;
    res.hidden = false;
    cta.hidden = true;
    resLabel.textContent = '// Подсказка';
    resBody.innerHTML = '<p class="stuk-res__lead">Подсказка не загрузилась. Обновите страницу или позвоните нам\u00a0— поможем разобраться по телефону.</p>';
  };

  /* ---------- one click listener for the whole section ---------- */
  root.addEventListener('click', (e) => {
    const t = e.target;
    const byKeyboard = e.detail === 0;
    const tile = t.closest('.stuk-sym');
    const chip = t.closest('.stuk-chip:not(.stuk-zone)');
    const zone = t.closest('.stuk-zone') || t.closest('.stuk-car__hit.is-on');
    const pre = t.closest('.stuk-preset');
    const ed = t.closest('[data-edit]');
    const act = t.closest('[data-act]');
    if (!(tile || chip || zone || pre || ed || act)) return;
    load().then(() => {
      if (tile) pickSymptom(tile.dataset.s, byKeyboard);
      else if (chip) pickContext(chip.dataset.c, byKeyboard);
      else if (zone) pickZone(zone.dataset.z, byKeyboard && !!zone.closest('button'));
      else if (pre) preset(pre.dataset.preset);
      else if (ed) edit(Number(ed.dataset.edit));
      else if (act.dataset.act === 'reset') reset(byKeyboard);
      else if (act.dataset.act === 'call') callback();
      else if (act.dataset.act === 'request') toRequest();
    }).catch(() => {});
  });

  /* ---------- the car and the place buttons light up together ---------- */
  const hover = (key, on) => {
    if (!key) return;
    $$(`.z-${key}`, car).forEach((el) => el.classList.toggle('is-hover', on));
    zoneBtns.forEach((b) => { if (b.dataset.z === key) b.classList.toggle('is-hover', on); });
  };
  const hoverKey = (t) => { const el = t.closest('.stuk-car__hit.is-on, .stuk-zone'); return el ? el.dataset.z : null; };
  steps[2].addEventListener('pointerover', (e) => hover(hoverKey(e.target), true), { passive: true });
  steps[2].addEventListener('pointerout', (e) => hover(hoverKey(e.target), false), { passive: true });
})();

/* ============================================================
   inner pages: services filter, tabs, registration form logic
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};

  /* ---------- services index filter ---------- */
  const filter = document.querySelector('[data-filter]');
  if (filter) {
    const cards = Array.from(document.querySelectorAll('.cat-card'));
    const countEl = document.querySelector('[data-filter-count]');
    const empty = document.querySelector('.empty-state');
    const norm = (s) => s.toLowerCase().replace(/ё/g, 'е').trim();
    const apply = () => {
      const q = norm(filter.value);
      let shown = 0;
      cards.forEach((card) => {
        const title = norm(card.dataset.title || '');
        const subs = Array.from(card.querySelectorAll('.cat-card__subs a'));
        let visibleSubs = 0;
        subs.forEach((a) => {
          const hit = !q || norm(a.textContent).includes(q) || title.includes(q);
          a.classList.toggle('is-hidden', !hit);
          if (hit) visibleSubs += 1;
        });
        const show = !q || title.includes(q) || visibleSubs > 0;
        card.classList.toggle('is-hidden', !show);
        if (show) shown += 1;
      });
      if (countEl) countEl.textContent = q ? `Найдено: ${shown}` : `${cards.length} направлений`;
      if (empty) empty.classList.toggle('is-visible', shown === 0);
    };
    filter.addEventListener('input', apply);
    const params = new URLSearchParams(location.search);
    if (params.get('q')) { filter.value = params.get('q'); }
    apply();
  }

  /* ---------- tabs ---------- */
  document.querySelectorAll('[data-tabs]').forEach((tabs) => {
    const btns = Array.from(tabs.querySelectorAll('[role=tab]'));
    const panels = btns.map((b) => document.getElementById(b.getAttribute('aria-controls')));
    const select = (i) => {
      btns.forEach((b, j) => { b.setAttribute('aria-selected', String(i === j)); b.tabIndex = i === j ? 0 : -1; });
      panels.forEach((p, j) => { if (p) p.hidden = i !== j; });
    };
    btns.forEach((b, i) => {
      b.addEventListener('click', () => select(i));
      b.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') { select((i + 1) % btns.length); btns[(i + 1) % btns.length].focus(); }
        if (e.key === 'ArrowLeft') { select((i - 1 + btns.length) % btns.length); btns[(i - 1 + btns.length) % btns.length].focus(); }
      });
    });
    select(0);
  });

  /* ---------- registration form ---------- */
  const reg = document.querySelector('[data-registration]');
  if (reg) {
    const typeInputs = Array.from(reg.querySelectorAll('input[name="RegistrationForm[type]"]'));
    const orgSection = reg.querySelector('[data-org]');
    const orgOnly = Array.from(reg.querySelectorAll('[data-org-only]'));
    const syncType = () => {
      const legal = typeInputs.some((r) => r.checked && r.value === '2');
      if (orgSection) orgSection.hidden = !legal;
      orgOnly.forEach((el) => { el.hidden = !legal; });
    };
    typeInputs.forEach((r) => r.addEventListener('change', syncType));
    syncType();
    const delivery = reg.querySelector('select[name="RegistrationForm[dostavkaType]"]');
    const point = reg.querySelector('[data-pickup]');
    const syncDelivery = () => { if (point && delivery) point.hidden = delivery.value !== 'pickup'; };
    if (delivery) { delivery.addEventListener('change', syncDelivery); syncDelivery(); }

    G.clearErrorsOnInput && G.clearErrorsOnInput(reg);
    reg.addEventListener('submit', async (e) => {
      e.preventDefault();
      let ok = true;
      Array.from(reg.querySelectorAll('[required]')).forEach((f) => {
        if (f.closest('[hidden]')) return;
        const bad = f.type === 'checkbox' ? !f.checked : !f.value.trim() || (f.dataset.phone !== undefined && !G.validPhone(f.value));
        if (bad) ok = false;
        G.setError(f, bad);
      });
      if (!ok) { G.toast('Заполните обязательные поля', 'err'); return; }
      const btn = reg.querySelector('[type=submit]');
      btn.disabled = true;
      try {
        await G.postForm(reg);
        reg.querySelector('[data-success]').classList.add('is-visible');
        Array.from(reg.children).forEach((c) => { if (!c.matches('[data-success]')) c.hidden = true; });
      } catch (err) {
        G.toast('Не удалось отправить форму. Позвоните нам: (831) 416-16-77', 'err');
      } finally { btn.disabled = false; }
    });
  }
})();

/* ============================================================
   «Шинный калькулятор» (build/shiny.py): two tyre sizes -> diameter, sidewall, clearance, speedometer.
   The page arrives with the default pair already counted and drawn; the script starts when the block comes near
   the screen. Drawing: one short tween of SVG transforms per change, no loop; the meter and the marking bar are
   CSS transitions. localStorage only remembers the last pair (in try/catch).
   ============================================================ */
(() => {
  'use strict';
  const root = document.querySelector('[data-shiny]');
  if (!root) return;
  const G = window.G || {};
  const NB = '\u00a0';
  const MINUS = '\u2212';
  const STORE = 'garage.shiny';
  const conf = root.dataset;           // speeds, the 3 % limit, the meter range and every phrase: build/shiny.py
  const SPEEDS = conf.speeds.split(' ').map(Number);
  const LIMIT = +conf.limit;
  const METER = +conf.meter;

  /* ---------- maths: the same formulas as build/shiny.py, lengths in hundredths of a millimetre ---------- */
  const sidewall = (s) => s.w * s.p;
  const rim = (s) => s.d * 2540;
  const outer = (s) => rim(s) + 2 * sidewall(s);
  const tenths = (h) => (h >= 0 ? 1 : -1) * Math.floor((Math.abs(h) + 5) / 10);
  const round1 = (x) => (x ? Math.sign(x) * Math.floor(Math.abs(x) * 10 + 0.5) / 10 : 0);

  const compare = (a, b) => {
    const odA = outer(a); const odB = outer(b); const diff = odB - odA;
    return {
      odA: tenths(odA), odB: tenths(odB), odD: tenths(odB) - tenths(odA),
      sA: tenths(sidewall(a)), sB: tenths(sidewall(b)), sD: tenths(sidewall(b)) - tenths(sidewall(a)),
      wD: b.w - a.w,
      clearance: tenths(diff / 2),                     // outer() is always even
      pct: round1(diff / odA * 100),
      speeds: SPEEDS.map((v) => round1(v * odB / odA)),
      same: a.w === b.w && a.p === b.p && a.d === b.d,
    };
  };

  /* ---------- formatting: decimal comma, real minus, no-break space before the unit ---------- */
  const dec = (t) => { t = Math.abs(t); return Math.floor(t / 10) + ',' + (t % 10); };
  const signedT = (t) => (t === 0 ? '0' : (t > 0 ? '+' : MINUS) + dec(t));
  const signedF = (x) => signedT(Math.round(x * 10));
  const signedI = (n) => (n === 0 ? '0' : (n > 0 ? '+' : MINUS) + Math.abs(n));
  const label = (s) => `${s.w}/${s.p} R${s.d}`;

  /* ---------- elements ---------- */
  const $ = (sel, el = root) => el.querySelector(sel);
  const $$ = (sel, el = root) => Array.from(el.querySelectorAll(sel));
  const out = {};
  $$('[data-o]').forEach((el) => { out[el.dataset.o] = el; });
  const sizes = {};
  $$('[data-size]').forEach((fs) => {
    sizes[fs.dataset.size] = {
      text: $('[data-text]', fs), err: $('[data-err]', fs),
      w: $('[data-part="w"]', fs), p: $('[data-part="p"]', fs), d: $('[data-part="d"]', fs),
    };
  });
  const texts = conf;
  const cta = $('[data-cta]');
  const live = $('[data-live]');
  const svg = $('.shiny-svg');

  const read = (k) => ({ w: +sizes[k].w.value, p: +sizes[k].p.value, d: +sizes[k].d.value });
  // a size is allowed when every part is one of the options of the selects
  const has = (sel, v) => Array.from(sel.options).some((o) => +o.value === v);
  const valid = (s) => !!s && has(sizes.a.w, s.w) && has(sizes.a.p, s.p) && has(sizes.a.d, s.d);
  const write = (k, s) => {
    const f = sizes[k];
    f.w.value = String(s.w); f.p.value = String(s.p); f.d.value = String(s.d);
    f.text.value = label(s);
    showError(k, '');
  };

  /* «205/55 R16», «205/55R16», «205 55 16», «205-55-r16», «225/45 ZR17 94W», Cyrillic «Р» — width, profile, rim */
  const parse = (raw) => {
    const m = String(raw).toUpperCase().match(/(\d{3})\s*[/\\\-.,\s]\s*(\d{2})\s*[/\\\-.,]?\s*[A-ZА-ЯЁ]{0,3}\s*[/\\\-.,]?\s*(\d{2})(?!\d)/);
    return m ? { w: +m[1], p: +m[2], d: +m[3] } : null;
  };
  function showError(k, which) {
    const f = sizes[k];
    f.err.hidden = !which;
    if (which) f.err.textContent = which === 'range' ? texts.errRange : texts.errParse;
    f.text.setAttribute('aria-invalid', which ? 'true' : 'false');
  }

  /* ---------- drawing: SVG transforms by data-t, the same strings as transforms() in build/shiny.py ---------- */
  const view = {
    ground: +svg.dataset.ground, top: +svg.dataset.top, side: +svg.dataset.side, front: +svg.dataset.front,
    min: +svg.dataset.min, bar: svg.dataset.bar.split(' ').map(Number),
  };
  const parts = {};
  $$('[data-t]', svg).forEach((el) => { parts[el.dataset.t] = el; });
  const f3 = (x) => String(+x.toFixed(3));
  // what the drawing depends on, in millimetres and viewBox units per millimetre; a tween interpolates these numbers
  const shape = (a, b) => {
    const odA = outer(a) / 100; const odB = outer(b) / 100;
    const topMm = Math.max(view.min, Math.ceil(Math.max(odA, odB) / 100) * 100);
    return { s: (view.ground - view.top) / topMm, odA, odB, rimA: a.d * 25.4, rimB: b.d * 25.4, wA: a.w, wB: b.w };
  };
  const draw = (g) => {
    const ra = g.odA / 2 * g.s; const rb = g.odB / 2 * g.s;
    const put = (name, value) => { if (parts[name]) parts[name].setAttribute('transform', value); };
    put('tyre-b', `translate(${view.side} ${f3(view.ground - rb)}) scale(${f3(rb / 100)})`);
    put('rim-b', `translate(${view.side} ${f3(view.ground - rb)}) scale(${f3(g.rimB / 2 * g.s / 100)})`);
    put('tyre-a', `translate(${view.side} ${f3(view.ground - ra)}) scale(${f3(ra / 100)})`);
    put('rim-a', `translate(${view.side} ${f3(view.ground - ra)}) scale(${f3(g.rimA / 2 * g.s / 100)})`);
    put('front-b', `translate(${view.front} ${view.ground}) scale(${f3(g.wB * g.s)} ${f3(g.odB * g.s)})`);
    put('front-a', `translate(${view.front} ${view.ground}) scale(${f3(g.wA * g.s)} ${f3(g.odA * g.s)})`);
    put('top-b', `translate(0 ${f3(view.ground - 2 * rb)})`);
    put('top-a', `translate(0 ${f3(view.ground - 2 * ra)})`);
    put('bar', `translate(${view.bar[0]} ${view.bar[1]}) scale(${f3(100 * g.s)} 1)`);
  };
  let shown = null; let raf = 0;
  const morph = (to, animate) => {
    cancelAnimationFrame(raf); raf = 0;
    if (!animate || !shown || G.reducedMotion) { shown = to; draw(to); return; }
    const from = shown; const t0 = performance.now(); const dur = 560;
    const step = (now) => {
      const p = Math.min(1, (now - t0) / dur); const e = 1 - Math.pow(1 - p, 4);
      const g = {};
      Object.keys(to).forEach((k) => { g[k] = from[k] + (to[k] - from[k]) * e; });
      shown = g; draw(g);
      raf = p < 1 ? requestAnimationFrame(step) : 0;
    };
    raf = requestAnimationFrame(step);
  };

  /* ---------- render ---------- */
  const set = (key, text) => { if (out[key] && out[key].textContent !== text) out[key].textContent = text; };
  let liveTimer = 0;
  const render = (animate) => {
    const a = read('a'); const b = read('b'); const r = compare(a, b);
    set('head', r.odD === 0 ? texts.headSame : `${r.odD > 0 ? texts.headMore : texts.headLess} ${dec(r.odD)}${NB}мм`);
    set('pct', `${signedF(r.pct)}${NB}%`);
    set('odA', dec(r.odA)); set('odB', dec(r.odB)); set('odD', `${signedT(r.odD)}${NB}мм`);
    set('sA', dec(r.sA)); set('sB', dec(r.sB)); set('sD', `${signedT(r.sD)}${NB}мм`);
    set('wA', String(a.w)); set('wB', String(b.w)); set('wD', `${signedI(r.wD)}${NB}мм`);
    set('cD', `${signedT(r.clearance)}${NB}мм`);
    r.speeds.forEach((v, i) => set('v' + i, dec(Math.round(v * 10))));
    set('labelA', label(a)); set('labelB', label(b));

    const state = r.same ? 'same' : Math.abs(r.pct) <= LIMIT ? 'ok' : 'over';
    const lead = texts[state];
    const more = state === 'over' ? (r.pct > 0 ? texts.overMore : texts.overLess) : '';
    out.verdict.dataset.state = state;
    set('verdict-text', lead);
    set('verdict-more', more);
    const verdict = more ? `${lead} ${more}` : lead;
    const pos = (Math.max(-METER, Math.min(METER, r.pct)) + METER) / (2 * METER) * 100;
    out.meter.style.transform = `translateX(${pos.toFixed(2)}%)`;

    const fill = (tpl, extra) => Object.entries({ now: label(a), new: label(b), ...extra }).reduce((t, [k, v]) => t.split(`{${k}}`).join(v), tpl);
    cta.dataset.preset = JSON.stringify({ message: fill(r.same ? texts.msgSame : texts.msg) });
    morph(shape(a, b), animate);

    try { localStorage.setItem(STORE, JSON.stringify({ a, b })); } catch (_) { /* private mode */ }
    // screen readers: one short summary after the last change, not a word per select
    clearTimeout(liveTimer);
    if (animate) {
      liveTimer = setTimeout(() => {
        const diff = r.odD === 0 ? texts.headSame : `${r.odD > 0 ? texts.headMore : texts.headLess} ${dec(r.odD)} мм, ${signedF(r.pct)} %`;
        live.textContent = r.same ? verdict : fill(texts.live, { diff, v90: dec(Math.round(r.speeds[1] * 10)), verdict });
      }, 700);
    }
  };

  /* ---------- marking strip ---------- */
  const markLine = $('.shiny-mark__line');
  const markBar = $('.shiny-mark__bar');
  const markParts = $$('[data-mark]');
  const placeBar = () => {
    const btn = markParts.find((x) => x.classList.contains('is-active')) || markParts[0];
    if (!btn || !markBar) return;
    // over the part's own underline (::after, 2px in from each side)
    markBar.style.transform = `translate(${btn.offsetLeft + 2}px, ${btn.offsetTop + btn.offsetHeight - 2}px) scaleX(${(btn.offsetWidth - 4) / 100})`;
  };
  const pick = (btn) => {
    markParts.forEach((x) => {
      const on = x === btn;
      x.classList.toggle('is-active', on);
      x.setAttribute('aria-pressed', on ? 'true' : 'false');
      const about = root.querySelector(`[data-about="${x.dataset.mark}"]`);
      if (about) about.hidden = !on;
    });
    placeBar();
  };

  /* ---------- start: when the block comes near the screen ---------- */
  const start = () => {
    let saved = null;
    try { saved = JSON.parse(localStorage.getItem(STORE) || 'null'); } catch (_) { saved = null; }
    ['a', 'b'].forEach((k) => write(k, saved && valid(saved[k]) ? saved[k] : read(k)));
    render(false);

    Object.keys(sizes).forEach((k) => {
      const f = sizes[k];
      [f.w, f.p, f.d].forEach((sel) => sel.addEventListener('change', () => { f.text.value = label(read(k)); showError(k, ''); render(true); }));
      f.text.addEventListener('input', () => {
        const s = parse(f.text.value);
        if (s && valid(s)) {
          showError(k, '');
          const cur = read(k);
          if (cur.w !== s.w || cur.p !== s.p || cur.d !== s.d) { f.w.value = String(s.w); f.p.value = String(s.p); f.d.value = String(s.d); render(true); }
        }
      });
      const settle = () => {
        const v = f.text.value.trim();
        const s = parse(v);
        if (!v) { f.text.value = label(read(k)); showError(k, ''); return; }
        if (!s) { showError(k, 'parse'); return; }
        if (!valid(s)) { showError(k, 'range'); return; }
        f.text.value = label(s); showError(k, '');
      };
      f.text.addEventListener('change', settle);
      f.text.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); settle(); f.text.blur(); } });
    });

    const swap = $('[data-swap]');
    let turns = 0;
    swap.addEventListener('click', () => {
      const a = read('a'); const b = read('b');
      write('a', b); write('b', a);
      turns += 1; swap.style.setProperty('--turn', String(turns));
      render(true);
    });

    markParts.forEach((btn) => btn.addEventListener('click', () => pick(btn)));
    placeBar();
    if ('ResizeObserver' in window) new ResizeObserver(placeBar).observe(markLine);
    else addEventListener('resize', placeBar, { passive: true });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(placeBar);
  };

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      if (entries.some((en) => en.isIntersecting)) { io.disconnect(); start(); }
    }, { rootMargin: '300px 0px' });
    io.observe(root);
  } else {
    start();
  }
})();

/* ============================================================
   otkryto: «Открыто сейчас» — the live status in Moscow time from the hours in data-oc (build/otkryto.py: 7 days
   from Monday, [opens, closes] in minutes, {note} or null), today in the week; «Как добраться»: copy the address,
   save the contact as a vCard. Without JS the plain hours stay in the markup.
   ============================================================ */
(() => {
  'use strict';
  const G = (window.G = window.G || {});
  const TZ = 'Europe/Moscow';   // Nizhny Novgorod keeps Moscow time: UTC+3 all year, no daylight saving
  const UTC_OFFSET = 180;       // minutes, for a browser without time zone data
  const SOON = 60;              // «Скоро закрываемся»: the last hour
  const NB = '\u00a0';           // no line break after a short preposition: «в 9:00», «до 19:00» stay whole
  const ON_DAY = ['в понедельник', 'во вторник', 'в среду', 'в четверг', 'в пятницу', 'в субботу', 'в воскресенье'].map((d) => d.replace(' ', NB));
  const UNTIL_DAY = ['понедельника', 'вторника', 'среды', 'четверга', 'пятницы', 'субботы', 'воскресенья'];
  const WEEKDAY = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 };

  /* ---------- time: the Moscow wall clock of a Date, { day: 0 (Monday) … 6, min: minutes since midnight } ---------- */
  let clock = null;
  const moscow = (date) => {
    try {
      clock = clock || new Intl.DateTimeFormat('en-US', { timeZone: TZ, weekday: 'short', hour: 'numeric', minute: 'numeric', hour12: false });
      const p = {};
      clock.formatToParts(date).forEach((x) => { p[x.type] = x.value; });
      const day = WEEKDAY[p.weekday];
      const min = (Number(p.hour) % 24) * 60 + Number(p.minute);   // % 24: some engines say «24» at midnight
      if (day !== undefined && !p.dayPeriod && Number.isFinite(min)) return { day, min };
    } catch (_) { /* no time zone data: UTC+3 below */ }
    const t = new Date(date.getTime() + UTC_OFFSET * 60000);
    return { day: (t.getUTCDay() + 6) % 7, min: t.getUTCHours() * 60 + t.getUTCMinutes() };
  };
  const hm = (min) => Math.floor(min / 60) + ':' + String(min % 60).padStart(2, '0');

  /* ---------- status: { state: open | soon | closed | note, word, rest, brief } ----------
     rest goes after the word in the contacts and the menu; brief is the shorter form for the header's top line */
  const status = (week, now) => {
    const today = week[now.day];
    if (Array.isArray(today)) {
      const opens = today[0];
      const closes = today[1];
      if (now.min >= opens && now.min < closes) {
        const soon = closes - now.min <= SOON;
        const until = 'до' + NB + hm(closes);
        return { state: soon ? 'soon' : 'open', word: soon ? 'Скоро закрываемся' : 'Открыто', rest: until, brief: until };
      }
      if (now.min < opens) return { state: 'closed', word: 'Закрыто', rest: 'откроемся сегодня в' + NB + hm(opens), brief: 'до' + NB + hm(opens) };
    } else if (today && today.note) {
      return { state: 'note', word: 'Сегодня', rest: today.note, brief: today.note };
    }
    for (let k = 1; k <= 7; k += 1) {
      const d = (now.day + k) % 7;
      const next = week[d];
      if (Array.isArray(next)) {
        const at = hm(next[0]);
        return k === 1
          ? { state: 'closed', word: 'Закрыто', rest: 'откроемся завтра в' + NB + at, brief: 'до завтра, ' + at }
          : { state: 'closed', word: 'Закрыто', rest: 'откроемся ' + ON_DAY[d] + ' в' + NB + at, brief: 'до ' + UNTIL_DAY[d] + ', ' + at };
      }
      if (next && next.note) {
        const rest = (k === 1 ? 'завтра' : ON_DAY[d]) + ' ' + next.note;
        return { state: 'closed', word: 'Закрыто', rest, brief: rest };
      }
    }
    return { state: 'closed', word: 'Закрыто', rest: '', brief: '' };
  };

  // the vCard lines come escaped and folded from build/otkryto.py; a file wants CRLF line ends
  const vcardFile = (lines) => lines.join('\r\n') + '\r\n';
  G.otkryto = { moscow, status, hm, vcardFile };

  /* ---------- the widgets: header top line, mobile menu, the weeks on the home page and /contacts/ ---------- */
  const widgets = [];
  document.querySelectorAll('[data-oc]').forEach((el) => {
    let week = null;
    try { week = JSON.parse(el.dataset.oc).week; } catch (_) { week = null; }
    if (Array.isArray(week) && week.length === 7) widgets.push({ el, week, brief: el.hasAttribute('data-oc-brief'), key: '' });
  });

  const paint = (w, now) => {
    const s = status(w.week, now);
    const rest = w.brief ? s.brief : s.rest;
    const key = [s.state, s.word, rest, now.day].join('|');
    if (key === w.key) return;   // a minute tick that changes nothing touches nothing
    w.key = key;
    w.el.dataset.ocState = s.state;
    w.el.classList.add('is-live');
    w.el.querySelectorAll('.oc__text').forEach((text) => {
      const word = document.createElement('span');
      word.className = 'oc__word';
      word.textContent = s.word;
      text.textContent = '';
      text.append(word);
      if (rest) {
        const sep = document.createElement('span');
        sep.className = 'oc__sep';
        sep.setAttribute('aria-hidden', 'true');
        sep.textContent = '·';
        text.append(' ', sep, ' ' + rest);
      }
      text.hidden = false;
    });
    w.el.querySelectorAll('.oc[hidden]').forEach((line) => { line.hidden = false; });
    w.el.querySelectorAll('[data-day]').forEach((cell) => {
      const on = Number(cell.dataset.day) === now.day;
      cell.classList.toggle('is-today', on);
      if (on) cell.setAttribute('aria-current', 'date'); else cell.removeAttribute('aria-current');
    });
  };

  if (widgets.length) {
    let timer = 0;
    const tick = () => {
      clearTimeout(timer);
      const now = moscow(new Date());
      widgets.forEach((w) => paint(w, now));
      // next look right after the minute turns, and none while the tab is hidden
      if (document.visibilityState !== 'hidden') timer = setTimeout(tick, 60000 - (Date.now() % 60000) + 200);
    };
    tick();
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') clearTimeout(timer); else tick(); });
    addEventListener('pageshow', (e) => { if (e.persisted) tick(); });
    // the dot's pulse stops off screen (base.css: .is-offscreen)
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver((entries) => entries.forEach((en) => en.target.classList.toggle('is-offscreen', !en.isIntersecting)));
      widgets.forEach((w) => io.observe(w.el));
    }
  }

  /* ---------- «Как добраться»: copy the address ---------- */
  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(text); return true; } catch (_) { /* refused: the old way below */ }
    }
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');   // no keyboard on a phone
    ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;font-size:16px';
    document.body.appendChild(ta);
    ta.focus({ preventScroll: true });   // the page must not jump to the hidden field
    ta.select();
    ta.setSelectionRange(0, text.length);   // iOS Safari selects only by range
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
    ta.remove();
    return ok;
  };
  document.querySelectorAll('[data-oc-copy]').forEach((btn) => {
    let done = 0;
    btn.hidden = false;
    btn.addEventListener('click', async () => {
      const text = btn.dataset.ocCopy;
      if (await copyText(text)) {
        btn.classList.add('is-done');
        clearTimeout(done);
        done = setTimeout(() => btn.classList.remove('is-done'), 2400);
        if (G.toast) G.toast(btn.dataset.ocToast);
      } else if (G.toast) {
        G.toast('Не удалось скопировать. Адрес: ' + text, 'err');
      }
    });
  });

  /* ---------- «Как добраться»: save the contact (a .vcf made here, nothing is fetched) ---------- */
  document.querySelectorAll('[data-oc-vcard]').forEach((btn) => {
    let lines = null;
    try { lines = JSON.parse(btn.dataset.ocVcard); } catch (_) { lines = null; }
    if (!Array.isArray(lines) || !window.Blob || !window.URL || !URL.createObjectURL) return;
    btn.hidden = false;
    btn.addEventListener('click', () => {
      const url = URL.createObjectURL(new Blob([vcardFile(lines)], { type: 'text/vcard;charset=utf-8' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = btn.dataset.ocFile || 'contact.vcf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);   // an iPhone reads the file after its own dialog
      if (G.toast) G.toast(btn.dataset.ocToast);
    });
  });
})();

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
