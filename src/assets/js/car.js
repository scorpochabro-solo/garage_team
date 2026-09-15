/* ============================================================
   interactive services map: diagnostic loupe, hotspots, HUD lines,
   readout panel, free-roam scanning, auto-tour
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
  const lens = carStage.querySelector('.lens');
  const lensLayers = lens ? Array.from(lens.querySelectorAll('.lens__img, .lens__xray')) : [];
  const lensTag = lens ? lens.querySelector('.lens__tag') : null;
  const lensLock = lens ? lens.querySelector('.lens__lock') : null;
  const dataEl = document.getElementById('svc-data');
  let data = {};
  try { data = JSON.parse(dataEl ? dataEl.textContent : '{}'); } catch (_) { data = {}; }
  const total = Object.keys(data).length || hotspots.length;
  const hintHTML = readout ? readout.innerHTML : '';
  const NS = 'http://www.w3.org/2000/svg';
  const ZOOM = 2.1;          // magnification inside the loupe
  const SNAP = 0.075;        // normalized distance at which the loupe snaps to a hotspot

  const spots = hotspots.map((h) => ({
    key: h.dataset.key,
    x: parseFloat(h.style.getPropertyValue('--x')) / 100,
    y: parseFloat(h.style.getPropertyValue('--y')) / 100,
  }));

  const isDesktop = () => matchMedia('(min-width: 901px)').matches;
  const canHover = () => matchMedia('(hover: hover) and (pointer: fine)').matches;

  let active = null;
  let roaming = false;
  let userBusyUntil = 0;
  let tourTimer = 0;
  let tourIdx = -1;
  let started = false;
  let swapTimer = 0;

  /* ---------- loupe ---------- */
  let lensPos = null; // where the loupe actually sits (fractions of the stage), after clamping
  function placeLens(fx, fy, free) {
    if (!lens) return;
    const W = carStage.clientWidth;
    const H = carStage.clientHeight;
    const R = lens.offsetWidth / 2;
    // the glass may protrude ~30% beyond the stage, never more; the magnified content stays centred on the target
    const m = R * 0.7;
    const px = W > 2 * m ? Math.min(1 - m / W, Math.max(m / W, fx)) : fx;
    const py = H > 2 * m ? Math.min(1 - m / H, Math.max(m / H, fy)) : fy;
    lensPos = { fx: px, fy: py };
    lens.classList.toggle('lens--top', py > 0.62);
    lens.classList.toggle('lens--edge-left', px < 0.22);
    lens.classList.toggle('lens--edge-right', px > 0.78);
    lens.style.setProperty('--lx', (px * 100).toFixed(2) + '%');
    lens.style.setProperty('--ly', (py * 100).toFixed(2) + '%');
    const size = `${(W * ZOOM).toFixed(1)}px ${(H * ZOOM).toFixed(1)}px`;
    const pos = `${(R - fx * W * ZOOM).toFixed(1)}px ${(R - fy * H * ZOOM).toFixed(1)}px`;
    lensLayers.forEach((l) => { l.style.backgroundSize = size; l.style.backgroundPosition = pos; });
    lens.classList.toggle('is-free', !!free);
    lens.classList.add('is-visible');
    carStage.classList.add('is-lens');
  }
  function hideLens() {
    if (!lens) return;
    lens.classList.remove('is-visible', 'is-free');
    carStage.classList.remove('is-lens');
  }
  function lockLens() {
    if (!lensLock) return;
    lensLock.classList.remove('is-locking');
    void lensLock.offsetWidth; // restart the animation
    lensLock.classList.add('is-locking');
  }
  const lensRadius = () => (lens && lens.classList.contains('is-visible') ? lens.offsetWidth / 2 + 6 : 8);

  /* ---------- HUD connector line ---------- */
  const el = (tag, attrs) => { const n = document.createElementNS(NS, tag); Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, String(v))); return n; };
  const clearLines = () => { while (svg.firstChild) svg.removeChild(svg.firstChild); };

  function drawLine(key) {
    clearLines();
    if (!isDesktop()) return;
    const item = items.find((i) => i.dataset.key === key);
    const hs = hotspots.find((h) => h.dataset.key === key);
    if (!item || !hs) return;
    const sr = stage.getBoundingClientRect();
    const ir = item.getBoundingClientRect();
    const hr = hs.getBoundingClientRect();
    svg.setAttribute('viewBox', `0 0 ${sr.width} ${sr.height}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    let tx = hr.left + hr.width / 2 - sr.left;
    let ty = hr.top + hr.height / 2 - sr.top;
    if (lens && lens.classList.contains('is-visible') && lensPos) {
      const cr = carStage.getBoundingClientRect();
      tx = cr.left - sr.left + lensPos.fx * cr.width;
      ty = cr.top - sr.top + lensPos.fy * cr.height;
    }
    const side = item.dataset.side;
    let sx, sy, ex, ey;
    if (side === 'left') { sx = ir.right - sr.left; sy = ir.top + ir.height / 2 - sr.top; ex = sx + 26; ey = sy; }
    else if (side === 'right') { sx = ir.left - sr.left; sy = ir.top + ir.height / 2 - sr.top; ex = sx - 26; ey = sy; }
    else { sx = ir.left + ir.width / 2 - sr.left; sy = ir.top - sr.top; ex = sx; ey = sy - Math.max(24, (sy - ty) * 0.35); }
    // stop at the loupe ring instead of the centre
    const dx = tx - ex; const dy = ty - ey; const len = Math.hypot(dx, dy) || 1;
    const r = Math.min(lensRadius(), len - 4);
    const fx = tx - (dx / len) * r; const fy = ty - (dy / len) * r;
    const d = `M${sx},${sy} L${ex},${ey} L${fx},${fy}`;
    const g = el('g', {});
    const halo = el('path', { d, class: 'halo' });
    const line = el('path', { d, class: 'line' });
    g.append(halo, line, el('circle', { cx: sx, cy: sy, r: 3.5, class: 'knot' }), el('circle', { cx: fx, cy: fy, r: 3, class: 'end' }));
    svg.appendChild(g);
    const L = line.getTotalLength();
    [halo, line].forEach((p) => { p.style.setProperty('--len', String(L)); p.style.strokeDasharray = String(L); p.style.strokeDashoffset = String(L); });
    requestAnimationFrame(() => g.classList.add('is-visible'));
  }

  /* ---------- readout ---------- */
  function readoutHTML(d) {
    const price = d.price
      ? `<b>${d.price}</b><span>${d.price_note || ''}</span>`
      : `<span>Стоимость уточняйте по телефону</span>`;
    return `
      <div class="svc-readout__icon"><svg class="ic" aria-hidden="true"><use href="#i-${d.icon}"/></svg></div>
      <div class="svc-readout__body">
        <div class="svc-readout__cat">${d.cat}</div>
        <div class="svc-readout__title">${d.name}</div>
        <div class="svc-readout__blurb">${d.blurb}</div>
        <div class="svc-readout__status"><i></i>Зона ${String(d.n || 0).padStart(2, '0')} / ${String(total).padStart(2, '0')} · узел найден</div>
      </div>
      <div class="svc-readout__price">${price}
        <a class="link-arrow link-arrow--inline svc-readout__link" href="${d.href}">Подробнее <svg class="ic" aria-hidden="true"><use href="#i-arrow"/></svg></a>
      </div>`;
  }
  const roamHTML = `<div class="svc-readout__icon"><svg class="ic" aria-hidden="true"><use href="#i-search"/></svg></div><div class="svc-readout__hint">Ведите лупу по автомобилю. Рядом с точкой она «прилипнет» к узлу и покажет услугу.</div>`;
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

  /* ---------- activation ---------- */
  function setActive(key, fromUser) {
    if (fromUser) userBusyUntil = Date.now() + 9000;
    if (active === key && key) return;
    active = key;
    items.forEach((i) => i.classList.toggle('is-active', i.dataset.key === key));
    hotspots.forEach((h) => h.classList.toggle('is-active', h.dataset.key === key));
    stage.classList.toggle('has-active', !!key);
    const spot = spots.find((s) => s.key === key);
    if (spot) {
      placeLens(spot.x, spot.y, false);
      lockLens();
      if (lensTag && data[key]) lensTag.textContent = `${String(data[key].n || 0).padStart(2, '0')} · ${data[key].name}`;
      drawLine(key);
    } else {
      clearLines();
      if (!roaming) hideLens();
    }
    updateReadout(key, roaming);
  }

  items.forEach((it) => {
    it.addEventListener('pointerenter', () => { if (canHover()) { roaming = false; setActive(it.dataset.key, true); } });
    it.addEventListener('focus', () => { roaming = false; setActive(it.dataset.key, true); });
  });
  hotspots.forEach((h) => {
    h.addEventListener('click', (e) => {
      e.preventDefault();
      const key = h.dataset.key;
      if (active === key && !canHover()) { const d = data[key]; if (d && d.href) location.href = d.href; return; }
      roaming = false;
      setActive(key, true);
      if (!isDesktop() && readout) readout.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
    });
    h.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); h.click(); } });
  });

  /* ---------- free-roam scanning with the loupe (mouse only) ---------- */
  if (lens && canHover()) {
    let raf = 0;
    let last = null;
    carStage.addEventListener('pointermove', (e) => {
      last = e;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        const r = carStage.getBoundingClientRect();
        if (!r.width || !r.height) return;
        const fx = Math.min(1, Math.max(0, (last.clientX - r.left) / r.width));
        const fy = Math.min(1, Math.max(0, (last.clientY - r.top) / r.height));
        userBusyUntil = Date.now() + 9000;
        const aspect = r.height / r.width;
        let best = null; let bestD = 1;
        spots.forEach((s) => { const d = Math.hypot(s.x - fx, (s.y - fy) * aspect); if (d < bestD) { bestD = d; best = s; } });
        if (best && bestD < SNAP) {
          roaming = false;
          if (active !== best.key) setActive(best.key, true);
        } else {
          const wasRoaming = roaming;
          roaming = true;
          if (active) setActive(null, true);
          placeLens(fx, fy, true);
          if (lensTag) lensTag.textContent = 'сканирование…';
          if (!wasRoaming) updateReadout(null, true);
        }
      });
    });
    carStage.addEventListener('pointerleave', () => {
      roaming = false;
      if (active) {
        const s = spots.find((x) => x.key === active);
        if (s) placeLens(s.x, s.y, false);
      } else {
        hideLens();
        updateReadout(null, false);
      }
    });
  }

  /* ---------- keyboard cycling ---------- */
  stage.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    const idx = items.findIndex((i) => i.dataset.key === active);
    const next = e.key === 'ArrowDown' ? (idx + 1) % items.length : (idx - 1 + items.length) % items.length;
    e.preventDefault();
    items[next].focus();
  });

  /* ---------- auto tour ---------- */
  function tourTick() {
    if (Date.now() < userBusyUntil || document.hidden || roaming) return;
    tourIdx = (tourIdx + 1) % items.length;
    setActive(items[tourIdx].dataset.key, false);
  }
  function tourStart() {
    tourStop();
    if (G.reducedMotion || !isDesktop()) return;
    tourTimer = setInterval(tourTick, 3200);
  }
  function tourStop() { if (tourTimer) clearInterval(tourTimer); tourTimer = 0; }

  function start() {
    if (!started) {
      started = true;
      carStage.classList.add('is-scanning');
      setTimeout(() => carStage.classList.add('is-ready'), 450);
      setTimeout(() => { if (!active && !roaming && Date.now() > userBusyUntil) tourTick(); }, 1700);
    }
    tourStart();
  }
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) start(); else tourStop(); });
    }, { threshold: 0.3 });
    io.observe(stage);
  } else { start(); }

  document.addEventListener('visibilitychange', () => { if (document.hidden) tourStop(); else if (started) tourStart(); });
  let rz = 0;
  addEventListener('resize', () => {
    clearTimeout(rz);
    rz = setTimeout(() => {
      if (!active) return;
      const s = spots.find((x) => x.key === active);
      if (s) placeLens(s.x, s.y, false);
      drawLine(active);
    }, 120);
  }, { passive: true });
})();
