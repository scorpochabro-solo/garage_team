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
