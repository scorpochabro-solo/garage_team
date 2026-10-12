/* ============================================================
   «Что сказал мастер?» — the glossary page /slovar/ (markup and texts in build/slovar.py).
   Instant search over the names, other names and texts: ё = е, hyphens and spaces do not matter, Russian
   endings are forgiven («сайлентблоки»), a typo or a wrong keyboard layout still finds the word; filters by
   system and by letter; deep links #<term> reveal the term and light it up; the call-back modal gets the term
   (or the word that was not found) in its message. Only events: no loops, just two short debounces — the
   screen-reader announcement and the ?q= in the address bar.
   ============================================================ */
(() => {
  'use strict';
  const root = document.querySelector('[data-gl]');
  if (!root) return;
  const G = window.G || {};
  const $ = (s, r = root) => r.querySelector(s);
  const $$ = (s, r = root) => Array.from(r.querySelectorAll(s));

  const input = $('[data-gl-q]');
  const form = $('[data-gl-form]');
  const clearBtn = $('[data-gl-clear]');
  const status = $('[data-gl-status]');
  const live = $('[data-gl-live]');
  const catBar = $('[data-gl-cats]');
  const abcBar = $('[data-gl-abc]');
  const empty = $('[data-gl-empty]');
  const more = $('[data-gl-more]');
  const list = $('.gl__list');
  const bar = $('.gl-bar');
  const header = document.querySelector('[data-header]');
  const sections = $$('[data-gl-section]');
  const chips = $$('[data-cat]', catBar);
  const letterBtns = $$('[data-letter]', abcBar);
  const ctas = $$('[data-gl-cta]', document);
  const notes = $$('[data-gl-cta-note]', document);
  if (!input || !form || !status || !list || !sections.length) return;
  const narrow = matchMedia('(max-width: 1099px)');   // the search bar sticks on its own (slovar.css)
  const MAX_Q = 80;
  const MSG = 'Хочу записаться на диагностику';

  /* ---------- text: lower case, ё = е, only letters and digits (and where each of them stood) ---------- */
  const ALNUM = /[0-9a-zа-я]/;
  const lower = (s) => {
    let out = '';
    for (let i = 0; i < s.length; i += 1) {
      const c = s[i].toLowerCase();
      out += c.length === 1 ? c : s[i];   // one character in, one out: positions stay comparable
    }
    return out.replace(/ё/g, 'е');
  };
  const squeeze = (s) => {
    const low = lower(s);
    let text = '';
    const at = [];
    for (let i = 0; i < low.length; i += 1) if (ALNUM.test(low[i])) { text += low[i]; at.push(i); }
    return { text, at };
  };
  const words = (s) => lower(s).replace(/[^0-9a-zа-я]+/g, ' ').trim().split(' ').filter(Boolean);
  // «что такое гур в автомобиле» → «гур»
  const STOP = new Set(['что', 'такое', 'это', 'значит', 'означает', 'как', 'где', 'зачем', 'почему', 'какой', 'какая', 'какие',
    'в', 'во', 'на', 'и', 'или', 'по', 'для', 'с', 'со', 'у', 'а', 'ли', 'же', 'не', 'мне', 'мастер', 'сказал', 'сказали', 'говорит',
    'машина', 'машины', 'машине', 'автомобиль', 'автомобиля', 'автомобиле', 'авто', 'расшифровка']);
  const tokens = (q) => { const all = words(q); const kept = all.filter((w) => !STOP.has(w)); return kept.length ? kept : all; };
  // Russian endings: «сайлентблоки» finds «сайлентблок», «шаровые» — «шаровая», «колодок» — «колодки»
  const variants = (w) => (w.length >= 6 ? [w, w.slice(0, -1), w.slice(0, -2)] : w.length === 5 ? [w, w.slice(0, -1)] : [w]);

  /* ---------- a wrong keyboard layout: «cfqktyn» is «сайлент» ---------- */
  const EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,.`";
  const RU = 'йцукенгшщзхъфывапролджэячсмитьбюё';
  const SWAP = new Map([...EN].map((c, i) => [c, RU[i]]).concat([...RU].map((c, i) => [c, EN[i]])));
  const swapLayout = (q) => Array.from(q.toLowerCase(), (c) => SWAP.get(c) || c).join('');

  /* ---------- typos: optimal string alignment distance, stops as soon as it exceeds the limit ---------- */
  const distance = (a, b, limit) => {
    if (Math.abs(a.length - b.length) > limit) return limit + 1;
    let before = null;
    let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
    for (let i = 1; i <= a.length; i += 1) {
      const cur = [i];
      let best = i;
      for (let j = 1; j <= b.length; j += 1) {
        let v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (before && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, before[j - 2] + 1);
        cur.push(v);
        if (v < best) best = v;
      }
      if (best > limit) return limit + 1;
      before = prev;
      prev = cur;
    }
    return prev[b.length];
  };
  // the typed word against the start of a name word: «салентбл» still meets «сайлентблок»
  const near = (w, word) => {
    if (w.length < 4) return false;
    const k = w.length <= 5 ? 1 : 2;
    for (let n = Math.max(1, w.length - 1); n <= Math.min(word.length, w.length + 1); n += 1) {
      if (distance(w, word.slice(0, n), k) <= k) return true;
    }
    return false;
  };

  /* ---------- the terms, read once from the page ---------- */
  const catName = {};
  sections.forEach((s) => { catName[s.dataset.glSection] = s.querySelector('.gl-cat__h').textContent.trim(); });
  const terms = $$('.gl-term').map((el) => {
    let refs = [];
    try { refs = el.dataset.refs ? JSON.parse(el.dataset.refs) : []; } catch (_) { refs = []; }
    const fields = $$('[data-f]', el).map((f) => {
      const text = f.textContent;
      return { el: f, name: f.dataset.f === 'n', text, sq: squeeze(text), marked: false };
    });
    const names = [...fields.filter((f) => f.name).map((f) => f.text), ...refs];
    const nameWords = names.flatMap(words);
    return {
      el,
      id: el.id,
      cat: el.dataset.cat,
      name: el.querySelector('.gl-term__name').textContent.trim(),
      section: el.closest('[data-gl-section]'),
      fields,
      hay: squeeze([...fields.map((f) => f.text), ...refs, catName[el.dataset.cat] || ''].join(' ')).text,
      namesHay: squeeze(names.join(' ')).text,
      nameWords,
      letters: (el.dataset.l || '').split(' ').filter(Boolean),
    };
  });
  const byId = new Map(terms.map((t) => [t.id, t]));
  const sectionIds = new Set(sections.map((s) => s.id));

  /* ---------- matching ---------- */
  // one or two letters are the start of a name («то» → «ТО», «ша» → «Шаровая опора»); longer words match anywhere in a
  // name, another name or a cross-reference (inName), or anywhere in the entry (hitWord)
  const inName = (t, w) => (w.length <= 2 ? t.nameWords.some((x) => x.startsWith(w)) : variants(w).some((v) => t.namesHay.includes(v)));
  const hitWord = (t, w) => (w.length <= 2 ? inName(t, w) : variants(w).some((v) => t.hay.includes(v)));
  const strict = (toks) => terms.filter((t) => toks.every((w) => hitWord(t, w)));
  const named = (t, toks) => toks.every((w) => inName(t, w));
  const fuzzy = (toks) => terms.filter((t) => toks.every((w) => hitWord(t, w) || t.nameWords.some((x) => near(w, x))));
  const find = (q) => {
    const toks = tokens(q);
    if (!toks.length) return null;
    let hits = strict(toks);
    if (hits.length) {
      // precision first: «ремень» shows the two terms called so; the thirteen that only mention it wait behind «ещё»
      const best = hits.filter((t) => named(t, toks));
      const rest = best.length ? hits.filter((t) => !best.includes(t)) : [];
      return { hits: best.length ? best : hits, rest, toks, mode: 'exact' };
    }
    const alt = swapLayout(q);
    const altToks = lower(alt) !== lower(q) ? tokens(alt) : [];
    if (altToks.length) {
      hits = strict(altToks);
      if (hits.length) return { hits, toks: altToks, mode: 'layout', shown: alt.trim() };
    }
    hits = fuzzy(toks);
    if (hits.length) return { hits, toks, mode: 'fuzzy' };
    if (altToks.length) {
      hits = fuzzy(altToks);
      if (hits.length) return { hits, toks: altToks, mode: 'layout', shown: alt.trim() };
    }
    return { hits: [], toks, mode: 'none' };
  };

  /* ---------- highlight what was found ---------- */
  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ESC[c]);
  const ranges = (f, toks) => {
    const out = [];
    toks.forEach((w) => {
      if (w.length <= 2) {
        if (!f.name) return;   // short words: only at the start of a word of a name
        const low = lower(f.text);
        for (let i = low.indexOf(w); i !== -1; i = low.indexOf(w, i + 1)) {
          if (i === 0 || !ALNUM.test(low[i - 1])) out.push([i, i + w.length]);
        }
        return;
      }
      const v = variants(w).find((x) => f.sq.text.includes(x));
      if (!v) return;
      for (let i = f.sq.text.indexOf(v); i !== -1; i = f.sq.text.indexOf(v, i + v.length)) {
        out.push([f.sq.at[i], f.sq.at[i + v.length - 1] + 1]);   // hyphens and spaces inside a match are marked too
      }
    });
    return out.sort((a, b) => a[0] - b[0]);
  };
  const paint = (f, toks) => {
    const found = toks ? ranges(f, toks) : [];
    if (!found.length) {
      if (f.marked) { f.el.textContent = f.text; f.marked = false; }
      return;
    }
    let html = '';
    let pos = 0;
    found.forEach(([s, e]) => {
      if (e <= pos) return;
      const from = Math.max(s, pos);
      html += `${esc(f.text.slice(pos, from))}<mark>${esc(f.text.slice(from, e))}</mark>`;
      pos = e;
    });
    f.el.innerHTML = html + esc(f.text.slice(pos));
    f.marked = true;
  };

  /* ---------- state and painting ---------- */
  const state = { q: '', cat: '', letter: '', more: false };
  let shown = terms;
  let current = null;   // the term the call-back message is about
  let lit = null;
  const plural = (n, one, few, many) => {
    const a = Math.abs(n) % 100;
    const b = a % 10;
    if (a > 10 && a < 20) return many;
    if (b === 1) return one;
    return b >= 2 && b <= 4 ? few : many;
  };
  const termsWord = (n) => `${n} ${plural(n, 'термин', 'термина', 'терминов')}`;
  const letterLabel = (L) => (L === 'latin' ? 'латиницей' : `на «${L.toUpperCase()}»`);
  const setText = (el, text) => { if (el && el.textContent !== text) el.textContent = text; };
  const letterFits = (L, cat) => terms.some((t) => t.letters.includes(L) && (!cat || t.cat === cat));

  let liveTimer = 0;
  const announce = (text) => {
    clearTimeout(liveTimer);
    liveTimer = setTimeout(() => { if (live) live.textContent = text; }, 450);
  };

  const syncTabStops = (buttons) => {
    const usable = buttons.filter((b) => !b.disabled);
    const stop = usable.find((b) => b.getAttribute('aria-pressed') === 'true') || usable[0];
    buttons.forEach((b) => { b.tabIndex = b === stop ? 0 : -1; });
  };

  const defaults = new Map(ctas.map((a) => {
    let message = MSG + '.';
    try { message = JSON.parse(a.dataset.preset || '{}').message || message; } catch (_) { /* the default above */ }
    return [a, message];
  }));
  const updateCta = () => {
    const q = state.q.trim();
    const single = shown.length === 1 && (q || state.letter) ? shown[0] : null;
    const t = single || (current && !current.el.hidden ? current : null);
    ctas.forEach((a) => {
      let message = defaults.get(a);
      if (a.dataset.glCta === 'query' && q) message = `${MSG}. Не нашлось в словаре на сайте: «${q}».`;
      else if (t) message = `${MSG}. Интересует: «${t.name}» (из словаря автомеханика на сайте).`;
      a.dataset.preset = JSON.stringify({ message });
    });
    notes.forEach((n) => {
      n.hidden = !t;
      if (t) setText(n, `В комментарий к звонку добавим: «${t.name}»`);
    });
  };

  // the status line: what is on the screen and why
  const statusFor = (result, hiddenRest) => {
    if (!shown.length) return 'Ничего не нашлось';
    if (result) {
      let text = `Найдено: ${shown.length}`;
      if (state.cat) text += ` в разделе «${catName[state.cat]}»`;
      if (hiddenRest) text += ` · ещё ${hiddenRest} в текстах`;
      if (result.mode === 'fuzzy') text += ' · похожие по написанию';
      if (result.mode === 'layout') text += ` · раскладка: «${result.shown}»`;
      return text;
    }
    if (state.letter) return `${termsWord(shown.length)} ${letterLabel(state.letter)}`;
    if (state.cat) return `${catName[state.cat]}: ${termsWord(shown.length)}`;
    return termsWord(terms.length);
  };

  const apply = () => {
    const q = state.q.trim();
    const result = q ? find(q) : null;
    const inCat = (t) => !state.cat || t.cat === state.cat;
    // what matches: every term for the word (named and mentioned), or the letter, or everything
    const matches = result ? result.hits.concat(result.rest || [])
      : state.letter ? terms.filter((t) => t.letters.includes(state.letter)) : terms;
    // what is shown: the named ones first; the mentions too after «ещё», or when the system has no named one
    const expand = !result || state.more || !result.hits.some(inCat);
    const pick = new Set((expand ? matches : result.hits).map((t) => t.id));
    shown = terms.filter((t) => pick.has(t.id) && inCat(t));
    const hiddenRest = expand ? 0 : (result.rest || []).filter(inCat).length;
    const marks = result && matches.length ? result.toks : null;
    const on = new Set(shown.map((t) => t.id));
    terms.forEach((t) => {
      const visible = on.has(t.id);
      if (t.el.hidden === visible) t.el.hidden = !visible;
      if (visible) t.fields.forEach((f) => paint(f, marks));
    });
    const filtered = !!(result || state.letter || state.cat);
    sections.forEach((s) => {
      const key = s.dataset.glSection;
      const n = shown.filter((t) => t.cat === key).length;
      if (s.hidden !== (n === 0)) s.hidden = n === 0;
      const count = s.querySelector('[data-gl-count]');
      const total = Number(count.dataset.total);
      setText(count, filtered && n !== total ? `${n} из ${total}` : termsWord(total));
    });
    // a system's count is every match in it, so a system with only mentions is not shown as empty
    const perCat = new Map();
    matches.forEach((t) => perCat.set(t.cat, (perCat.get(t.cat) || 0) + 1));
    chips.forEach((b) => {
      const key = b.dataset.cat;
      const n = key ? perCat.get(key) || 0 : matches.length;
      b.setAttribute('aria-pressed', String(key === state.cat));
      b.classList.toggle('is-empty', n === 0);
      setText(b.querySelector('[data-n]'), String(n));
    });
    letterBtns.forEach((b) => {
      const L = b.dataset.letter;
      b.setAttribute('aria-pressed', String(L === state.letter));
      b.disabled = L !== state.letter && !letterFits(L, state.cat);
    });
    syncTabStops(chips);
    syncTabStops(letterBtns);

    const text = statusFor(result, hiddenRest);
    setText(status, text);
    if (more) {
      more.hidden = !hiddenRest;
      const label = hiddenRest ? `Ещё ${termsWord(hiddenRest)}, где упоминается «${q}»` : '';
      if (more.dataset.label !== label) {
        more.dataset.label = label;
        more.innerHTML = label ? `<svg class="ic" aria-hidden="true" focusable="false"><use href="#i-plus"/></svg><span>${esc(label)}</span>` : '';
      }
    }
    root.classList.toggle('is-query', !!result);
    root.classList.toggle('is-searching', !!(result || state.letter));
    root.classList.toggle('is-empty', !shown.length);
    if (empty) empty.hidden = shown.length > 0;
    if (clearBtn) clearBtn.hidden = !input.value;
    updateCta();
    return text;
  };

  /* ---------- keep the list in sight after a filter changes ---------- */
  // the bar sticks under the header on phones in portrait (slovar.css); elsewhere only the header covers the page.
  // Heights, not positions: right after the list shrinks and the scroll is clamped, WebKit reports a sticky
  // element's position from before the clamp (the header's bottom came back as −2046 px).
  const barSticks = () => !!bar && getComputedStyle(bar).position === 'sticky';
  const coverBottom = () => (header ? header.offsetHeight : 0) + (barSticks() ? bar.offsetHeight : 0);
  const toListTop = (evenIfBelow) => {
    requestAnimationFrame(() => {
      const top = list.getBoundingClientRect().top;
      const limit = coverBottom() + 12;
      if (top < limit - 1 || (evenIfBelow && top > innerHeight * 0.75)) {
        scrollTo({ top: Math.max(0, scrollY + top - limit), behavior: 'instant' });
      }
    });
  };

  /* ---------- the search in the address bar: /slovar/?q=граната ---------- */
  let urlTimer = 0;
  const syncUrl = () => {
    clearTimeout(urlTimer);
    urlTimer = setTimeout(() => {
      try {
        const u = new URL(location.href);
        const q = state.q.trim();
        if (q) u.searchParams.set('q', q); else u.searchParams.delete('q');
        if (u.href !== location.href) history.replaceState(history.state, '', u.href);
      } catch (_) { /* a sandboxed frame or too many updates: the address stays as it was */ }
    }, 700);
  };

  /* ---------- deep links: /slovar/#grm, the index, «См. также» ---------- */
  const targetOf = (id) => {
    const t = byId.get(id);
    if (t) return { el: t.el, term: t, hidden: t.el.hidden || t.section.hidden };
    if (!sectionIds.has(id)) return null;
    const el = document.getElementById(id);
    return { el, term: null, hidden: el.hidden };
  };
  const clearFilters = () => {
    state.q = '';
    state.cat = '';
    state.letter = '';
    input.value = '';
    syncUrl();
    return apply();
  };
  // a filtered-out term must be visible before the browser (or this script) scrolls to it
  const reveal = (id) => {
    const target = targetOf(id);
    if (target && target.hidden) clearFilters();
    return target;
  };
  // the lamp flickers on when the term arrives on screen, not while a long smooth scroll is still carrying it there
  let arrival = null;
  const switchOn = (el) => {
    el.classList.remove('is-lit');
    void el.offsetWidth;   // restart the lamp when the same term is opened again
    el.classList.add('is-lit');
  };
  const light = (t) => {
    if (lit && lit !== t.el) lit.classList.remove('is-lit');
    lit = t.el;
    if (arrival) { arrival.disconnect(); arrival = null; }
    if (!('IntersectionObserver' in window)) { switchOn(t.el); return; }
    t.el.classList.remove('is-lit');
    arrival = new IntersectionObserver((entries) => {
      if (!entries.some((en) => en.isIntersecting)) return;
      arrival.disconnect();
      arrival = null;
      switchOn(t.el);
    }, { threshold: Math.min(0.9, (innerHeight * 0.5) / Math.max(1, t.el.offsetHeight)) });   // a tall term: half a screen of it
    arrival.observe(t.el);
  };
  // scroll: 'smooth' after a click, 'instant' on load; without it only a term that was filtered out is scrolled to
  const openHash = (scroll) => {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = id ? reveal(id) : null;
    if (!target) return;
    if (scroll || target.hidden) {
      target.el.scrollIntoView({ block: 'start', behavior: scroll === 'instant' || G.reducedMotion ? 'instant' : 'smooth' });
    }
    if (target.term) {
      current = target.term;
      light(target.term);
      updateCta();
      announce(`${target.term.name}.`);
    }
  };
  addEventListener('hashchange', () => openHash(false));
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;
    let id = '';
    try { id = decodeURIComponent(a.getAttribute('href').slice(1)); } catch (_) { return; }
    if (!byId.has(id) && !sectionIds.has(id)) return;
    reveal(id);
    // the same hash again: the browser scrolls, but there is no hashchange to light the term
    if (location.hash === `#${a.getAttribute('href').slice(1)}`) requestAnimationFrame(() => openHash(false));
  });

  /* ---------- search ---------- */
  input.addEventListener('input', () => {
    state.q = input.value.slice(0, MAX_Q);
    state.more = false;
    if (state.q.trim()) state.letter = '';
    announce(apply());
    toListTop(false);
    syncUrl();
  });
  input.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || !input.value) return;
    e.preventDefault();
    input.value = '';
    state.q = '';
    announce(apply());
    syncUrl();
  });
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (shown.length === 1 && state.q.trim()) {   // Enter with one answer opens it
      const id = shown[0].id;
      if (location.hash === `#${id}`) openHash('smooth'); else location.hash = id;
      return;
    }
    if (!G.canHover) input.blur();   // a phone: put the keyboard away and show the answers
    toListTop(true);
  });
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      input.value = '';
      state.q = '';
      announce(apply());
      syncUrl();
      input.focus();
    });
  }

  const reset = empty && empty.querySelector('[data-gl-reset]');
  if (reset) {
    reset.addEventListener('click', () => {
      announce(clearFilters());
      input.focus({ preventScroll: true });
      toListTop(false);
    });
  }

  if (more) {
    more.addEventListener('click', () => {
      const before = new Set(shown.map((t) => t.id));
      state.more = true;
      announce(apply());
      // the mentions come in among the named terms: bring the first of them into view and give it the focus
      const added = shown.find((t) => !before.has(t.id));
      if (added) {
        added.el.scrollIntoView({ block: 'start', behavior: 'instant' });
        added.el.focus({ preventScroll: true });
      }
    });
  }

  /* ---------- systems and letters ---------- */
  catBar.addEventListener('click', (e) => {
    const b = e.target.closest('[data-cat]');
    if (!b) return;
    const key = b.dataset.cat;
    state.cat = key && state.cat !== key ? key : '';   // the pressed system again shows every system
    if (state.letter && !letterFits(state.letter, state.cat)) state.letter = '';
    announce(apply());
    toListTop(true);
  });
  abcBar.addEventListener('click', (e) => {
    const b = e.target.closest('[data-letter]');
    if (!b || b.disabled) return;
    const L = b.dataset.letter;
    state.letter = state.letter === L ? '' : L;
    if (state.letter && input.value) {
      input.value = '';
      state.q = '';
      syncUrl();
    }
    announce(apply());
    toListTop(true);
  });
  // a toolbar is one Tab stop; the arrows, Home and End move inside it
  const rove = (group, buttons) => {
    group.addEventListener('keydown', (e) => {
      const usable = buttons.filter((b) => !b.disabled);
      const i = usable.indexOf(document.activeElement);
      if (i === -1) return;
      const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      const j = step ? (i + step + usable.length) % usable.length : e.key === 'Home' ? 0 : e.key === 'End' ? usable.length - 1 : -1;
      if (j < 0) return;
      e.preventDefault();
      buttons.forEach((b) => { b.tabIndex = b === usable[j] ? 0 : -1; });
      usable[j].focus();
    });
  };
  rove(catBar, chips);
  rove(abcBar, letterBtns);

  /* ---------- how far the sticky search bar covers the list (anchors land below it) ---------- */
  if (bar) {
    const measure = () => root.style.setProperty('--gl-bar-h', `${barSticks() ? Math.round(bar.getBoundingClientRect().height) : 0}px`);
    measure();
    if ('ResizeObserver' in window) new ResizeObserver(measure).observe(bar);
    const short = matchMedia('(max-height: 500px)');
    [narrow, short].forEach((mq) => { if (mq.addEventListener) mq.addEventListener('change', measure); else if (mq.addListener) mq.addListener(measure); });
  }

  /* ---------- start: ?q= from the address, then the term of the link ---------- */
  const q0 = new URLSearchParams(location.search).get('q');
  if (!input.value && q0) input.value = q0;
  state.q = input.value.slice(0, MAX_Q);
  apply();
  if (location.hash) openHash('instant');
  // back to the page from the history: the browser may have restored the field without an input event
  addEventListener('pageshow', (e) => {
    if (e.persisted && input.value.slice(0, MAX_Q) !== state.q) { state.q = input.value.slice(0, MAX_Q); apply(); }
  });
})();
