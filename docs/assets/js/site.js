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
    };
    burger.addEventListener('click', () => setOpen(burger.getAttribute('aria-expanded') !== 'true'));
    menu.addEventListener('click', (e) => { if (e.target.closest('a, button')) setOpen(false); });
    addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    addEventListener('resize', () => { if (innerWidth > 1100) setOpen(false); }, { passive: true });
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
    const first = dlg.querySelector('input:not([type=hidden]):not([disabled]), select, textarea');
    if (first) setTimeout(() => first.focus(), 60);
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
      if (first && n > 1) setTimeout(() => first.focus(), 350);
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
