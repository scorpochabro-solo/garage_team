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
