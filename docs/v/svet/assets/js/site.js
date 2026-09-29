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
      const dur = 1400; const t0 = performance.now();
      const step = (t) => {
        const p = Math.min(1, (t - t0) / dur); const e = 1 - Math.pow(1 - p, 3);
        el.textContent = String(Math.round(end * e));
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { run(en.target); io.unobserve(en.target); } });
    }, { threshold: 0.5 });
    counters.forEach((el) => io.observe(el));
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
