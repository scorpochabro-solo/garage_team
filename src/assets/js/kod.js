/* ============================================================
   «Расшифровка кода ошибки» (build/kod.py): an OBD-II code split into its parts after SAE J2012, the standard
   meaning of the common generic codes, the codes in the call-back message.
   The table is read from the reference rows of the block, the phrases from its JSON; parse() and explain() are
   pure and exported as G.kod (tests/kod_decode.cjs runs them in node). explain() repeats build/kod.py rule for rule.
   Nothing runs at rest: no loop, no timer until the visitor types; a new result fades in by opacity/transform.
   ============================================================ */
(() => {
  'use strict';
  const G = (window.G = window.G || {});

  /* ---------- parsing: «P0301», «p0301», «P0 301», «Р0301», «PO301», several codes in one text ---------- */
  // Cyrillic letters that look like Latin ones, the Russian keys under P, B and U (the keyboard was left in Russian)
  // and the letter O typed for a zero
  const LOOK = { 'Р': 'P', 'З': 'P', 'В': 'B', 'И': 'B', 'С': 'C', 'Г': 'U', 'У': 'U', 'А': 'A', 'Ф': 'A', 'Е': 'E', 'О': '0', 'O': '0' };
  const CODE = /^[PBCU][0-3][0-9A-F]{3}$/;
  const PART = /^[PBCU][0-9A-F]{0,3}$/;     // the start of a code typed in pieces: «P», «P0», «P03», «P030»
  const HEX = /^[0-9A-F]+$/;
  const MAX = 10;

  // words and numbers of the text, upper case, each with the letters mapped (t) and as typed (raw)
  const tokens = (raw) => String(raw == null ? '' : raw).normalize('NFKC').toUpperCase()
    .split(/[^0-9A-ZА-ЯЁ]+/).filter(Boolean)
    .map((w) => ({ raw: w, t: Array.from(w, (c) => LOOK[c] || c).join('') }));

  // why a piece with digits is not a code: the key of the phrase in texts.err
  const classify = (t) => {
    if (/^[0-3][0-9A-F]{3}$/.test(t)) return 'noletter';
    if (/^[PBCU][0-9A-F]+$/.test(t)) {
      if (t.length !== 5) return 'length';
      return /^[PBCU][0-3]/.test(t) ? 'chars' : 'second';
    }
    if (/^[PBCU][0-3][0-9A-Z]{3}$/.test(t)) return 'chars';
    if (/^[A-ZА-ЯЁ][0-9A-F]{4}$/.test(t)) return 'letter';
    return 'other';                                   // a year, a mileage, «B1S1» from a scanner's description
  };
  // next to real codes, a number without a letter is most likely a year or a mileage, not a mistyped code
  const STRAY = ['noletter', 'other'];

  // -> { codes: unique codes in the order typed (at most max), errors: [{ key, token, fix, pending }], more }
  // pending: the last piece is still being typed (shorter than a code, nothing after it) — not an error yet
  const parse = (raw, max = MAX) => {
    const list = tokens(raw);
    const open = !/[^0-9A-Za-zА-ЯЁа-яё]$/.test(String(raw == null ? '' : raw).normalize('NFKC'));
    const codes = [];
    const errors = [];
    let more = false;
    const add = (c) => {
      if (codes.includes(c)) return;
      if (codes.length >= max) { more = true; return; }
      codes.push(c);
    };
    for (let i = 0; i < list.length; i += 1) {
      let t = list[i].t;
      let shown = list[i].raw;
      // a code typed in pieces («P0 301», «P 0301», «P0-3-01»): join while the pieces add up to five characters.
      // A lone Cyrillic letter is a word («и», «в», «с», «у»), never the start of a code.
      const lone = shown.length === 1 && /[А-ЯЁ]/.test(shown);
      if (!lone && PART.test(t) && t.length < 5) {
        let j = i;
        let joined = t;
        let text = shown;
        while (joined.length < 5 && j + 1 < list.length && HEX.test(list[j + 1].t) && joined.length + list[j + 1].t.length <= 5) {
          j += 1;
          joined += list[j].t;
          text += ' ' + list[j].raw;
        }
        if (joined.length === 5) { i = j; t = joined; shown = text; }
      }
      if (CODE.test(t)) { add(t); continue; }
      // codes typed without a space: «P0301P0171»
      if (t.length > 5 && t.length % 5 === 0) {
        const chunks = t.match(/.{5}/g);
        if (chunks.every((c) => CODE.test(c))) { chunks.forEach(add); continue; }
      }
      // a word («код», «ошибка») is skipped; a piece with a digit was meant as a code
      if (/\d/.test(shown)) {
        const e = {
          key: classify(t),
          token: shown.length > 16 ? shown.slice(0, 15) + '…' : shown,
          fix: 'P' + t,
          pending: open && i === list.length - 1 && t.length < 5,
        };
        if (!errors.some((x) => x.key === e.key && x.token === e.token)) errors.push(e);
      }
    }
    return { codes, errors: codes.length ? errors.filter((e) => !STRAY.includes(e.key)) : errors, more };
  };

  /* ---------- decoding: the same rules as kind() and explain() in build/kod.py ---------- */
  // generic | maker | reserved, by the second character (P3: by the third as well: P3000–P33FF maker, P3400– generic)
  const kind = (code) => {
    const letter = code[0];
    const second = code[1];
    if (letter === 'P') {
      if (second === '0' || second === '2') return 'generic';
      if (second === '1') return 'maker';
      return parseInt(code[2], 16) <= 3 ? 'maker' : 'generic';
    }
    if (second === '0') return 'generic';
    return second === '3' ? 'reserved' : 'maker';
  };

  const explain = (code, model) => {
    const T = model.texts;
    const k = kind(code);
    const typeText = code.startsWith('P3') ? T.type['p3-' + k] : T.type[k];
    const table = T.sub[code.slice(0, 2)];
    const sub = (table && table[code[2]]) || '';
    const parts = [['sys', code[0], T.letters[code[0]]], ['type', code[1], typeText]];
    if (sub) parts.push(['sub', code[2], sub], ['num', code.slice(3), T.num.sub]);
    else parts.push(['num', code.slice(2), T.num.all]);
    const entry = model.codes[code] || null;
    const note = entry ? T.note.known : T.note[k === 'generic' ? 'unknown' : k];
    return { code, kind: k, parts, entry, note };
  };

  const fill = (tpl, vars) => String(tpl).replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  const message = (codes, T) => (codes.length ? fill(T.msg.codes, { codes: codes.join(', ') }) : T.msg.none);
  const errorText = (e, T) => fill(T.err[e.key], { t: e.token || '', fix: e.fix || '' });

  G.kod = { parse, explain, kind, message, errorText, tokens };

  /* ---------- the page ---------- */
  const root = document.querySelector('[data-kod]');
  if (!root) return;
  let T = null;
  try { T = JSON.parse(root.querySelector('[data-kod-texts]').textContent); } catch (_) { return; }
  const $ = (sel) => root.querySelector(sel);
  const scan = $('.kod-scan');
  const form = $('[data-kod-form]');
  const input = $('[data-kod-input]');
  const errorsBox = $('[data-kod-errors]');
  const out = $('[data-kod-out]');
  const cta = $('[data-kod-cta]');
  const ctaNote = $('[data-kod-cta-note]');
  const live = $('[data-kod-live]');
  if (!form || !input || !errorsBox || !out || !cta) return;
  const coarse = matchMedia('(pointer: coarse)').matches;

  // the table: every row of the reference list, as build/kod.py rendered it (no-break spaces stay: «банк 1»)
  const text = (n) => (n ? n.textContent.replace(/[ \t\n\r\f]+/g, ' ').trim() : '');
  const codes = {};
  root.querySelectorAll('[data-code]').forEach((row) => {
    const f = (k) => row.querySelector(`[data-f="${k}"]`);
    const link = f('link');
    codes[row.dataset.code] = {
      name: text(f('name')), check: text(f('check')), urge: !!f('urge'),
      href: link ? link.getAttribute('href') : null, label: link ? text(link) : null,
    };
  });
  const model = { texts: T, codes };

  /* ---------- markup: the same as card() in build/kod.py ---------- */
  const NS = 'http://www.w3.org/2000/svg';
  const el = (tag, cls, content) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (content != null) n.textContent = content;
    return n;
  };
  const svgIcon = (name, cls) => {
    const s = document.createElementNS(NS, 'svg');
    s.setAttribute('class', cls ? 'ic ' + cls : 'ic');
    s.setAttribute('aria-hidden', 'true');
    s.setAttribute('focusable', 'false');
    const u = document.createElementNS(NS, 'use');
    u.setAttribute('href', '#i-' + name);
    s.appendChild(u);
    return s;
  };

  function card(x) {
    const box = el('div', 'kod-card');
    box.dataset.kind = x.kind;
    box.dataset.known = x.entry ? '1' : '0';
    const id = el('div', 'kod-card__id');
    const lcd = el('div', 'kod-lcd');
    lcd.setAttribute('role', 'img');
    lcd.setAttribute('aria-label', fill(T.labels.code, { code: x.code }));
    const cells = el('div', 'kod-lcd__cells');
    const keys = el('div', 'kod-lcd__keys');
    keys.setAttribute('aria-hidden', 'true');
    const dl = el('dl', 'kod-parts');
    x.parts.forEach(([role, chars, about]) => {
      Array.from(chars).forEach((ch) => {
        const c = el('span', 'kod-lcd__cell', ch);
        c.dataset.role = role;
        cells.appendChild(c);
      });
      const key = el('span', 'kod-lcd__key', T.keys[role]);
      key.dataset.role = role;
      key.style.setProperty('--n', String(chars.length));
      keys.appendChild(key);
      const row = el('div', 'kod-part');
      row.dataset.role = role;
      const dd = el('dd');
      dd.append(el('b', 'kod-part__ch', chars), el('span', null, about));
      row.append(el('dt', null, T.roles[role]), dd);
      dl.appendChild(row);
    });
    lcd.append(cells, keys);
    id.append(lcd, dl);
    const body = el('div', 'kod-card__text');
    const e = x.entry;
    body.appendChild(el('p', 'kod-card__label', T.labels.mean));
    if (e) {
      body.append(el('p', 'kod-card__name', e.name), el('p', 'kod-card__label', T.labels.check), el('p', 'kod-card__check', e.check));
      if (e.urge) {
        const u = el('p', 'kod-card__urge');
        u.append(svgIcon('hazard', 'ic--sm'), el('span', null, T.urge));
        body.appendChild(u);
      }
      if (e.href) {
        const a = el('a', 'link-arrow link-arrow--inline kod-card__link', e.label + ' ');
        a.setAttribute('href', e.href);
        a.appendChild(svgIcon('arrow'));
        body.appendChild(a);
      }
      const n = el('p', 'kod-card__note');
      n.append(svgIcon('info', 'ic--sm'), el('span', null, x.note));
      body.appendChild(n);
    } else {
      body.appendChild(el('p', 'kod-card__none', x.note));
    }
    box.append(id, body);
    return box;
  }

  const brief = (x) => (x.entry ? x.entry.name : T.status[x.kind === 'generic' ? 'unknown' : x.kind]);

  function codeList(xs, current, more) {
    const box = el('div', 'kod-codes');
    box.setAttribute('role', 'group');
    box.setAttribute('aria-labelledby', 'kod-codes-head');
    const head = el('p', 'kod-codes__head', fill(T.labels.list, { n: xs.length }));
    head.id = 'kod-codes-head';
    box.appendChild(head);
    const ul = el('ul', 'kod-codes__list');
    xs.forEach((x) => {
      const b = el('button', 'kod-codes__btn');
      b.type = 'button';
      b.dataset.kodPick = x.code;
      b.dataset.kind = x.kind;
      b.dataset.known = x.entry ? '1' : '0';
      b.setAttribute('aria-pressed', x.code === current ? 'true' : 'false');
      b.append(el('span', 'kod-codes__code', x.code), el('span', 'kod-codes__name', brief(x)));
      const li = el('li');
      li.appendChild(b);
      ul.appendChild(li);
    });
    box.appendChild(ul);
    if (more) box.appendChild(el('p', 'kod-codes__more', fill(T.labels.more, { max: T.max })));
    return box;
  }

  /* ---------- state and rendering ---------- */
  const example = out.innerHTML;      // the worked example P0301, rendered by build/kod.py
  let shown = { codes: [], more: false };   // the codes on the screen …
  let current = '';                          // … and the one that is opened
  let liveTimer = 0;

  const say = (msg, later) => {
    clearTimeout(liveTimer);
    if (!live) return;
    if (later) liveTimer = setTimeout(() => { live.textContent = msg; }, 900);
    else live.textContent = msg;
  };
  const summary = (x) => fill(T.live.one, { code: x.code, text: brief(x) });
  const report = () => {
    const x = explain(current, model);
    return shown.codes.length > 1 ? fill(T.live.many, { n: shown.codes.length, code: x.code, text: brief(x) }) : summary(x);
  };

  function setCta(list) {
    cta.dataset.preset = JSON.stringify({ message: message(list, T) });
    if (!ctaNote) return;
    ctaNote.hidden = !list.length;
    ctaNote.textContent = list.length ? fill(T.ctaNote, { codes: list.join(', ') }) : '';
  }

  function showErrors(errors) {
    errorsBox.textContent = '';
    errors.forEach((e) => {
      const li = el('li', 'kod-form__error');
      li.append(svgIcon('hazard', 'ic--sm'), el('span', null, errorText(e, T)));
      errorsBox.appendChild(li);
    });
    errorsBox.hidden = !errors.length;
    input.setAttribute('aria-invalid', errors.length ? 'true' : 'false');
    if (scan) scan.dataset.state = errors.length ? 'error' : shown.codes.length ? 'ok' : 'idle';
  }

  function showExample() {
    out.classList.remove('is-stale');
    if (out.dataset.view === 'example') return;
    shown = { codes: [], more: false };
    current = '';
    out.classList.remove('is-live');
    out.innerHTML = example;          // the page's own markup, kept at start: no visitor text in it
    out.dataset.view = 'example';
    setCta([]);
  }

  // -> true when the screen changed (a new set of codes or another code opened)
  function showCodes(r, pick) {
    out.classList.remove('is-stale');
    const onScreen = out.dataset.view === 'codes';
    const same = onScreen && r.codes.length === shown.codes.length && r.codes.every((c, i) => c === shown.codes[i]);
    const next = pick || (r.codes.includes(current) ? current : r.codes[0]);
    if (same && next === current && r.more === shown.more) return false;
    const xs = r.codes.map((c) => explain(c, model));
    // the opened code stays in place when only the list changes (a second code typed after it): no second drop-in
    const keep = onScreen && next === current ? out.querySelector('.kod-card') : null;
    shown = { codes: r.codes.slice(), more: r.more };
    current = next;
    const list = xs.length > 1 ? codeList(xs, current, r.more) : null;
    if (keep) {
      const old = out.querySelector('.kod-codes');
      if (old) old.remove();
      if (list) out.insertBefore(list, keep);
    } else {
      out.textContent = '';
      if (list) out.appendChild(list);
      out.appendChild(card(xs.find((x) => x.code === current)));
    }
    out.classList.add('is-live');
    out.dataset.view = 'codes';
    setCta(shown.codes);
    return true;
  }

  // typing: a finished code is decoded at once; a piece that is still being typed is not an error yet
  function onInput() {
    const r = parse(input.value, T.max);
    const errors = r.errors.filter((e) => !e.pending);
    if (!input.value.trim()) {
      showExample();
      showErrors([]);
      say('');
      return;
    }
    if (r.codes.length) {
      if (showCodes(r)) say(report(), true);
    } else if (errors.length) {
      showExample();                                  // a finished piece that is not a code: the errors explain it
    } else if (out.dataset.view === 'codes') {
      out.classList.add('is-stale');                  // a code is being retyped: the old answer steps back
    }
    showErrors(errors);
  }

  // «Расшифровать» or Enter: every error, including an empty field or a text without a code
  function commit() {
    const value = input.value;
    const r = parse(value, T.max);
    let errors = r.errors;
    if (!value.trim()) errors = [{ key: 'empty' }];
    else if (!r.codes.length && !errors.length) errors = [{ key: 'none' }];
    if (r.codes.length) showCodes(r); else showExample();
    showErrors(errors);
    const words = errors.map((e) => errorText(e, T));
    say((r.codes.length ? [report(), ...words] : words).join(' '));
  }

  function decode(code, focus) {
    input.value = code;
    commit();
    if (focus) out.focus({ preventScroll: true });
  }

  input.addEventListener('input', onInput);
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    commit();
    // on a phone the keyboard would cover the answer
    if (coarse) input.blur();
  });

  // «Например»: one tap decodes the example
  form.addEventListener('click', (e) => {
    const b = e.target.closest('[data-kod-example]');
    if (b) decode(b.dataset.kodExample, false);
  });

  // several codes: the list chooses which one is opened (the list is drawn anew: focus goes to the same button)
  out.addEventListener('click', (e) => {
    const b = e.target.closest('[data-kod-pick]');
    if (!b || b.dataset.kodPick === current) return;
    showCodes(shown, b.dataset.kodPick);
    const again = out.querySelector(`[data-kod-pick="${current}"]`);
    if (again) again.focus();
    say(summary(explain(current, model)));
  });

  /* ---------- the reference list: a code becomes a button that decodes it on the screen above ---------- */
  root.querySelectorAll('.kod-row__code').forEach((dt) => {
    const code = dt.parentElement.dataset.code;
    const b = el('button', 'kod-row__pick', code);
    b.type = 'button';
    b.dataset.kodRef = code;
    b.setAttribute('aria-label', fill(T.labels.pick, { code }));
    dt.textContent = '';
    dt.appendChild(b);
  });
  const toScreen = () => {
    const target = scan || out;
    target.scrollIntoView({ block: 'start', behavior: G.reducedMotion ? 'auto' : 'smooth' });
  };
  root.addEventListener('click', (e) => {
    const b = e.target.closest('[data-kod-ref]');
    if (!b) return;
    decode(b.dataset.kodRef, true);
    toScreen();
  });

  /* ---------- a link to the block: #kod lands on the title, #kod-p0301 opens that code ---------- */
  const fromHash = () => {
    let hash = location.hash || '';
    try { hash = decodeURIComponent(hash); } catch (_) { return; }
    const m = /^#kod-([0-9a-z]{5})$/i.exec(hash);
    if (m && CODE.test(m[1].toUpperCase())) {
      decode(m[1].toUpperCase(), false);
    } else if (hash !== '#kod') {
      return;
    }
    // once the web fonts are in: until then the text above is set in a fallback font and the offset is off
    const go = () => (m ? toScreen() : root.scrollIntoView({ block: 'start' }));
    if (document.fonts && document.fonts.status !== 'loaded') document.fonts.ready.then(go); else go();
  };
  out.dataset.view = 'example';
  fromHash();
  addEventListener('hashchange', fromHash);
})();
