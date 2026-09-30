/* ============================================================
   vremya: «Когда удобно приехать?» — a wish for the day and the part of the day in the request form (step 2) and in
   the call-back modal. data-vremya (build/vremya.py) holds the week of D.HOURS in minutes, the parts of the day and
   the texts; the 14 days are counted here in Moscow time, and today's parts that are over are left out.
   The choice is one line at the top of the text the backend already receives («Удобно приехать: пт, 2 октября,
   утром (9–12)»): replaced when the choice changes, removed when it is cleared. Everything else in the text stays as
   the visitor (or «Что стучит?», «Зима») wrote it, and a line edited by hand is the visitor's own text from then on.
   Without JS the picker stays hidden and the form is as it was.
   ============================================================ */
(() => {
  'use strict';
  const G = (window.G = window.G || {});
  const TZ = 'Europe/Moscow';   // Nizhny Novgorod keeps Moscow time: UTC+3 all year, no daylight saving
  const UTC_OFFSET = 180;       // minutes, for a browser without time zone data
  const LIVE_DELAY = 450;       // arrow keys run through the days: the screen reader hears the line once they stop
  const WEEKDAY = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 };
  const WD = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];
  const WD_FULL = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'];
  const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
  const MONTHS_SHORT = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
  const STEP = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };

  /* ---------- the Moscow calendar of a Date: { y, m (1–12), d, wd (0 = Monday), min (since midnight) } ----------
     the approach of otkryto.js: Intl with the Moscow zone, UTC+3 arithmetic when the browser has no zone data */
  let clock = null;
  const moscow = (date) => {
    try {
      clock = clock || new Intl.DateTimeFormat('en-US', { timeZone: TZ, year: 'numeric', month: 'numeric', day: 'numeric', weekday: 'short', hour: 'numeric', minute: 'numeric', hour12: false });
      const p = {};
      clock.formatToParts(date).forEach((x) => { p[x.type] = x.value; });
      // % 24: some engines say «24» at midnight
      const now = { y: Number(p.year), m: Number(p.month), d: Number(p.day), wd: WEEKDAY[p.weekday], min: (Number(p.hour) % 24) * 60 + Number(p.minute) };
      if (now.wd !== undefined && !p.dayPeriod && [now.y, now.m, now.d, now.min].every(Number.isFinite)) return now;
    } catch (_) { /* no time zone data: UTC+3 below */ }
    const t = new Date(date.getTime() + UTC_OFFSET * 60000);
    return { y: t.getUTCFullYear(), m: t.getUTCMonth() + 1, d: t.getUTCDate(), wd: (t.getUTCDay() + 6) % 7, min: t.getUTCHours() * 60 + t.getUTCMinutes() };
  };

  const pad = (n) => String(n).padStart(2, '0');
  const hm = (min) => (min % 60 ? Math.floor(min / 60) + ':' + pad(min % 60) : String(min / 60));   // 540 «9», 570 «9:30»
  const escRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const fill = (tpl, vars) => tpl.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m));

  /* ---------- the logic of one picker, without the page (tests/vremya_cases.cjs runs it in node) ---------- */
  const create = (conf) => {
    const { week, parts, lead, t } = conf;
    const TIME = '\\d{1,2}(?::\\d{2})?';
    // exactly the line this script writes; anything else in the text belongs to the visitor
    const shape = new RegExp(`^\\s*${escRe(t.prefix)} (${WD.join('|')}), (\\d{1,2}) (${MONTHS.join('|')})`
      + `(?:, (?:(${parts.map((p) => escRe(p.word)).join('|')}) \\((${TIME})–(${TIME})\\)|(${escRe(t.any_line)})))?\\s*$`);

    // the window of conf.days days from today: each day open / closed / late (today, every part over) with its parts
    const days = (now) => {
      const list = [];
      for (let i = 0; i < conf.days; i += 1) {
        const c = new Date(Date.UTC(now.y, now.m - 1, now.d + i));   // calendar arithmetic: months and years roll over
        const day = { key: `${c.getUTCFullYear()}-${pad(c.getUTCMonth() + 1)}-${pad(c.getUTCDate())}`, y: c.getUTCFullYear(),
          m: c.getUTCMonth() + 1, d: c.getUTCDate(), wd: (c.getUTCDay() + 6) % 7, offset: i, state: 'open', note: '', slots: [] };
        const spec = week[day.wd];
        if (Array.isArray(spec)) {
          // a part of the day is its window cut by the day's hours; today it is offered while `lead` minutes of it are left
          day.slots = parts.map((p) => ({ key: p.key, word: p.word, title: p.title, from: Math.max(p.from, spec[0]), to: Math.min(p.to, spec[1]) }))
            .filter((s) => s.to > s.from && (i > 0 || now.min <= s.to - lead));
          if (i === 0 && !day.slots.length) day.state = 'late';
        } else if (spec && spec.note) {
          day.note = spec.note;   // a day with a note instead of hours («по предварительной записи»): only «Любое время»
        } else {
          day.state = 'closed';   // null: not in D.HOURS
        }
        list.push(day);
      }
      return list;
    };

    // what a day's chip shows and what a screen reader hears: «пятница, 2 октября, сегодня», «воскресенье, 4 октября, выходной»
    const dayLabel = (day) => {
      const when = day.offset === 0 ? t.today : day.offset === 1 ? t.tomorrow : '';
      const why = day.state === 'closed' ? t.closed : day.state === 'late' ? t.late : day.note;
      return { wd: WD[day.wd], num: pad(day.d), tag: day.state === 'closed' ? t.closed : when || MONTHS_SHORT[day.m - 1],
        sr: [`${WD_FULL[day.wd]}, ${day.d} ${MONTHS[day.m - 1]}`, when, why].filter(Boolean).join(', ') };
    };
    // a part's chip: «Утром» over «9–12»; a screen reader hears «утром, с 9 до 12»
    const partLabel = (slot) => {
      const from = hm(slot.from);
      const to = hm(slot.to);
      return { title: slot.title, hours: `${from}–${to}`, sr: fill(t.part_sr, { word: slot.word, from, to }) };
    };

    const lineFor = (day, part) => {
      const slot = day.slots.find((s) => s.key === part);
      let line = `${t.prefix} ${WD[day.wd]}, ${day.d} ${MONTHS[day.m - 1]}`;
      if (part === 'any') line += `, ${t.any_line}`;
      else if (slot) line += `, ${slot.word} (${hm(slot.from)}–${hm(slot.to)})`;
      return line;
    };

    const isLine = (l) => shape.test(l);
    // the text with `line` at the top (or without any line of ours when `line` is empty); the rest stays as it was
    const withLine = (text, line) => {
      const rest = String(text == null ? '' : text).split('\n').filter((l) => !isLine(l)).join('\n');
      // with a line and nothing else the text ends in a line break: a tap under it starts a new line, not our line
      return line ? `${line}\n${rest}` : rest;
    };

    // the choice a line of ours in the text stands for: { date, part } | { invalid } | null when there is no such line
    const parse = (text, list) => {
      const lines = String(text == null ? '' : text).split('\n');
      for (let i = 0; i < lines.length; i += 1) {
        const m = shape.exec(lines[i]);
        if (!m) continue;
        const day = list.find((x) => WD[x.wd] === m[1] && x.d === Number(m[2]) && MONTHS[x.m - 1] === m[3]);
        if (!day || day.state !== 'open') return { invalid: true };
        if (m[7]) return { date: day.key, part: 'any' };
        if (!m[4]) return { date: day.key, part: null };
        const slot = day.slots.find((s) => s.word === m[4]);
        if (!slot || hm(slot.from) !== m[5] || hm(slot.to) !== m[6]) return { invalid: true };
        return { date: day.key, part: slot.key };
      }
      return null;
    };

    return { days, dayLabel, partLabel, lineFor, withLine, isLine, parse };
  };

  /* ---------- the picker on the page ---------- */
  const valid = (c) => !!c && Array.isArray(c.week) && c.week.length === 7 && Array.isArray(c.parts) && c.parts.length > 0
    && c.parts.every((p) => p && typeof p.key === 'string' && typeof p.word === 'string' && typeof p.title === 'string' && p.from < p.to)
    && Number.isFinite(c.lead) && Number.isInteger(c.days) && c.days > 0 && !!c.t
    && ['prefix', 'any', 'any_line', 'today', 'tomorrow', 'closed', 'late', 'part_sr', 'expired', 'cleared', 'where'].every((k) => typeof c.t[k] === 'string');
  const same = (a, b) => (!a && !b) || (!!a && !!b && a.date === b.date && a.part === b.part);

  const mount = (root, conf, field) => {
    const api = create(conf);
    const t = conf.t;
    const $ = (s) => root.querySelector(s);
    const daysBox = $('[data-vr-days]');
    const partsBox = $('[data-vr-parts]');
    const clearBtn = $('[data-vr-clear]');
    const status = $('[data-vr-status]');
    const lineOut = $('[data-vr-line]');
    const live = $('[data-vr-live]');
    const body = $('[data-vr-body]');
    const toggle = $('[data-vr-toggle]');   // the modal's picker is folded: its question opens the days
    if (!daysBox || !partsBox || !clearBtn || !status || !lineOut || !live || !body) return null;

    let open = !toggle;
    let list = [];
    let key = '';
    let sel = null;        // { date: 'YYYY-MM-DD', part: key | 'any' | null }
    let writing = false;   // our own input event: nothing to read back
    let liveTimer = 0;

    const selDay = () => (sel ? list.find((d) => d.key === sel.date) : null);
    const currentLine = () => { const day = selDay(); return day ? api.lineFor(day, sel.part) : ''; };

    /* chips: buttons with the radio role (a named input would add a field to what the form posts) */
    const radio = (cls, label) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = cls;
      b.tabIndex = -1;
      b.setAttribute('role', 'radio');
      b.setAttribute('aria-checked', 'false');
      b.setAttribute('aria-label', label);
      return b;
    };
    const span = (cls, text) => {
      const s = document.createElement('span');
      s.className = cls;
      s.textContent = text;
      s.setAttribute('aria-hidden', 'true');
      return s;
    };
    const dayChip = (day) => {
      const l = api.dayLabel(day);
      const b = radio('vr-day', l.sr);
      b.dataset.date = day.key;
      if (day.offset === 0) b.classList.add('is-today');
      if (day.state !== 'open') { b.disabled = true; b.classList.add('is-' + day.state); }
      b.append(span('vr-day__wd', l.wd), ' ', span('vr-day__d', l.num), ' ', span('vr-day__tag', l.tag));   // spaces: copied text reads «пт 02 окт»
      return b;
    };
    const partChip = (slot) => {
      const l = api.partLabel(slot);
      const b = radio('vr-part', l.sr);
      b.dataset.part = slot.key;
      b.append(span('vr-part__t', l.title), ' ', span('vr-part__h', l.hours));
      return b;
    };
    const anyChip = () => {
      const b = radio('vr-part vr-part--any', t.any);
      b.dataset.part = 'any';
      b.append(span('vr-part__t', t.any));
      return b;
    };

    /* roving tabindex: one tab stop per group, on the checked chip or the first one that can be chosen */
    const radios = (box) => Array.from(box.querySelectorAll('[role="radio"]'));
    const paint = (box, attr, value) => {
      const all = radios(box);
      const on = all.find((b) => !b.disabled && b.dataset[attr] === value);
      const stop = on || all.find((b) => !b.disabled);
      all.forEach((b) => { b.setAttribute('aria-checked', String(b === on)); b.tabIndex = b === stop ? 0 : -1; });
    };
    const buildDays = () => { daysBox.textContent = ''; list.forEach((d) => daysBox.append(dayChip(d))); };
    const buildParts = () => {
      const day = selDay();
      partsBox.textContent = '';
      partsBox.hidden = !day;
      if (!day) return;
      [...day.slots.map(partChip), anyChip()].forEach((b, i) => {
        b.style.setProperty('--i', String(i));   // the chips come in one after another (vremya.css)
        partsBox.append(b);
      });
    };
    const render = (dayChanged) => {
      paint(daysBox, 'date', sel && sel.date);
      if (dayChanged) buildParts();
      paint(partsBox, 'part', sel && sel.part);
    };
    const showStatus = (expired) => {
      const line = currentLine();
      status.hidden = !line && !expired;
      status.classList.toggle('is-warn', !line && !!expired);
      lineOut.textContent = line || (expired ? t.expired : '');
      clearBtn.hidden = !sel;
      root.classList.toggle('is-set', !!sel);
    };
    const announce = (text, soon) => {
      clearTimeout(liveTimer);
      liveTimer = setTimeout(() => { live.textContent = text; }, soon ? 60 : LIVE_DELAY);
    };

    /* the text field: the line goes in, is replaced or comes out; an input event tells the form's own listeners.
       A visitor typing in it (a choice taken back by the clock) keeps the caret: the change is above it, so the
       caret keeps its distance from the end */
    const write = () => {
      const before = field.value;
      const next = api.withLine(before, currentLine());
      if (next === before) return;
      const typing = document.activeElement === field;
      const fromEnd = typing ? [before.length - field.selectionStart, before.length - field.selectionEnd] : null;
      field.value = next;
      if (fromEnd) field.setSelectionRange(Math.max(0, next.length - fromEnd[0]), Math.max(0, next.length - fromEnd[1]));
      writing = true;
      try { field.dispatchEvent(new Event('input', { bubbles: true })); } finally { writing = false; }
    };

    const choose = (next) => {
      const dayChanged = (sel && sel.date) !== (next && next.date);
      sel = next;
      render(dayChanged);
      write();
      showStatus(false);
      announce(sel ? `${t.where} ${currentLine()}` : t.cleared, !sel);
    };
    const focusChip = (box, attr, value) => {
      const b = radios(box).find((x) => x.dataset[attr] === value);
      if (!b) return;
      b.focus({ preventScroll: true });
      b.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: G.reducedMotion ? 'auto' : 'smooth' });
    };
    const pickDay = (b, byKey) => {
      const day = list.find((d) => d.key === b.dataset.date);
      if (!day || day.state !== 'open') return;
      // the part stays when the new day has it too: Saturday's evening is shorter, it is still the evening
      const part = sel && (sel.part === 'any' || day.slots.some((s) => s.key === sel.part)) ? sel.part : null;
      if (!same(sel, { date: day.key, part })) choose({ date: day.key, part });
      if (byKey) focusChip(daysBox, 'date', day.key);
    };
    const pickPart = (b, byKey) => {
      if (!sel) return;
      if (sel.part !== b.dataset.part) choose({ date: sel.date, part: b.dataset.part });
      if (byKey) focusChip(partsBox, 'part', b.dataset.part);
    };

    // arrows move and choose, as in a group of radio buttons; the closed days are stepped over
    const onKey = (box, pick) => (e) => {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      const items = radios(box).filter((b) => !b.disabled);
      const i = items.indexOf(e.target);
      if (i < 0) return;
      let j;
      if (e.key in STEP) j = (i + STEP[e.key] + items.length) % items.length;
      else if (e.key === 'Home') j = 0;
      else if (e.key === 'End') j = items.length - 1;
      else return;
      e.preventDefault();
      pick(items[j], true);
    };
    daysBox.addEventListener('keydown', onKey(daysBox, pickDay));
    partsBox.addEventListener('keydown', onKey(partsBox, pickPart));
    daysBox.addEventListener('click', (e) => { const b = e.target.closest('.vr-day'); if (b && !b.disabled) pickDay(b, false); });
    partsBox.addEventListener('click', (e) => { const b = e.target.closest('.vr-part'); if (b) pickPart(b, false); });
    clearBtn.addEventListener('click', () => {
      choose(null);
      // the button hides itself: the keyboard focus goes to the days (to the question when they are folded)
      const stop = open ? daysBox.querySelector('[tabindex="0"]') : toggle;
      if (stop) stop.focus({ preventScroll: true });
    });

    const setOpen = (v) => {
      open = v;
      body.hidden = !v;
      if (toggle) toggle.setAttribute('aria-expanded', String(v));
      root.classList.toggle('is-open', v);
    };
    if (toggle) toggle.addEventListener('click', () => setOpen(!open));

    // the text is the truth: a line removed or changed by hand clears the chips; a line of ours sets them
    // (a form the browser restored after a reload); repair: a restored line for a day already gone is taken out
    const sync = (repair) => {
      const found = api.parse(field.value, list);
      if (found && found.invalid && repair) field.value = api.withLine(field.value, '');
      const next = found && !found.invalid ? found : null;
      if (same(next, sel)) return;
      const dayChanged = (sel && sel.date) !== (next && next.date);
      sel = next;
      render(dayChanged);
      showStatus(false);
    };
    field.addEventListener('input', () => { if (!writing) sync(false); });

    // the modal's form is reset when the dialog closes (form.js): the field empties itself, the chips follow
    if (field.form) {
      field.form.addEventListener('reset', () => {
        clearTimeout(liveTimer);
        live.textContent = '';
        const dayChanged = !!sel;
        sel = null;
        render(dayChanged);
        showStatus(false);
        if (toggle) setOpen(false);
      });
    }

    // a new day (midnight) or today's part that is over: the days are built again; a choice that is gone is taken back
    const refresh = (now) => {
      const next = api.days(now);
      const k = next.map((d) => `${d.key}:${d.state}:${d.slots.map((s) => s.key).join('.')}`).join('|');
      if (k === key) return;
      key = k;
      list = next;
      const had = root.contains(document.activeElement) ? document.activeElement : null;
      buildDays();
      let expired = false;
      const day = selDay();
      if (sel && !(day && day.state === 'open' && (!sel.part || sel.part === 'any' || day.slots.some((s) => s.key === sel.part)))) {
        sel = null;
        expired = true;
      }
      render(true);
      if (expired) { write(); announce(t.expired, true); }
      showStatus(expired);
      if (had && !root.contains(document.activeElement)) {
        const stop = (had.dataset.part && partsBox.querySelector('[tabindex="0"]')) || daysBox.querySelector('[tabindex="0"]');
        if (stop) stop.focus({ preventScroll: true });
      }
    };

    return {
      field,
      ownText: () => api.withLine(field.value, ''),
      start(now) {
        refresh(now);
        sync(true);
        setOpen(open || !!sel);   // a choice restored with the form is shown open
        root.hidden = false;
      },
      refresh,
    };
  };

  /* ---------- start: every [data-vremya] with its text field; one minute clock for all ---------- */
  const pickers = [];
  G.vremya = {
    create,
    moscow,
    // form.js, step 2: the text of the field without the picker's line (the line alone does not describe the task)
    ownText: (el) => {
      const p = pickers.find((x) => x.field === el);
      return p ? p.ownText() : (el ? el.value : '');
    },
  };

  // whatever goes wrong with one picker, it stays hidden and the form works as before; site.js goes on
  const now = moscow(new Date());
  document.querySelectorAll('[data-vremya]').forEach((root) => {
    let conf = null;
    try { conf = JSON.parse(root.dataset.vremya); } catch (_) { conf = null; }
    const field = document.getElementById(root.dataset.vrFor || '');
    if (!valid(conf) || !field || !('value' in field)) return;
    try {
      const p = mount(root, conf, field);
      if (!p) return;
      p.start(now);
      pickers.push(p);
    } catch (_) {
      root.hidden = true;
    }
  });

  if (pickers.length) {
    let timer = 0;
    const tick = () => {
      clearTimeout(timer);
      // next look right after the minute turns, and none while the tab is hidden
      if (document.visibilityState !== 'hidden') timer = setTimeout(tick, 60000 - (Date.now() % 60000) + 200);
      const at = moscow(new Date());
      pickers.forEach((p) => { try { p.refresh(at); } catch (_) { /* this picker keeps its days; the next minute tries again */ } });
    };
    timer = setTimeout(tick, 60000 - (Date.now() % 60000) + 200);
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') clearTimeout(timer); else tick(); });
    addEventListener('pageshow', (e) => { if (e.persisted) tick(); });
  }
})();
