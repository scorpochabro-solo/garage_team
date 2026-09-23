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
