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
      : '<span>Стоимость уточняйте по телефону</span>';
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
      if (!measured) return;
      measure();
      const s = spotByKey.get(active);
      if (s) { moveTo(s.x, s.y, false); drawLine(active); } else if (visible) { schedule(); }
    });
  };
  if ('ResizeObserver' in window) new ResizeObserver(onResize).observe(stage); else addEventListener('resize', onResize, { passive: true });
})();
