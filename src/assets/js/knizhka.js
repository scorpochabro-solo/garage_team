/* ============================================================
   knizhka: «Моя машина» — the car's service book in this browser (/moya-mashina/, build/knizhka.py).
   This file is the model, on every page: calendar dates, the VIN check, the next service from the owner's own
   interval (km or months, whichever comes first, counted from the last entry marked «ТО»), the calendar file (.ics,
   RFC 5545), the check of a saved or loaded book and the merge of two books; the storage (one localStorage key,
   every access in try/catch); the request form's «Заполнить из «Моей машины»», shown once a car is saved.
   The page itself is js/knizhka-ui.js. The pure part is G.knizhka: tests/knizhka_logic.cjs runs it in node.
   Nothing leaves the browser.
   ============================================================ */
(() => {
  'use strict';
  const G = (window.G = window.G || {});
  const KEY = 'garage.knizhka.v1';
  const FORMAT = 'garage-knizhka';
  const VERSION = 1;
  const MAX_KM = 2000000;              // a bigger mileage is a typo
  const MAX_ENTRIES = 2000;            // far beyond a car's life; keeps a copy under MAX_FILE
  const MAX_FILE = 1024 * 1024;
  const RATE_DAYS = 14;                // a daily average needs at least two weeks of driving after the service
  const SOON = 0.9;                    // 90 % of an interval used: the gauge turns amber
  const INTERVAL_KM = [100, 200000];
  const INTERVAL_MONTHS = [1, 120];
  const LEN = { brand: 40, model: 40, engine: 24, text: 600, note: 300 };
  const ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$/;   // safe in a CSS selector and in the calendar UID
  const DAY = 86400000;
  const NB = '\u00a0';

  /* ---------- calendar dates as 'YYYY-MM-DD', counted in whole UTC days: no time zone or DST drift ---------- */
  const pad = (n) => String(n).padStart(2, '0');
  const daysIn = (y, m) => new Date(Date.UTC(y, m, 0)).getUTCDate();          // m: 1…12
  const iso = (y, m, d) => `${String(y).padStart(4, '0')}-${pad(m)}-${pad(d)}`;
  const parseDate = (s) => {
    const m = typeof s === 'string' ? /^(\d{4})-(\d{2})-(\d{2})$/.exec(s) : null;
    if (!m) return null;
    const y = Number(m[1]); const mo = Number(m[2]); const d = Number(m[3]);
    if (y < 1900 || y > 2199 || mo < 1 || mo > 12 || d < 1 || d > daysIn(y, mo)) return null;
    return { y, m: mo, d };
  };
  const dayNum = (s) => { const p = parseDate(s); return p ? Date.UTC(p.y, p.m - 1, p.d) / DAY : NaN; };
  const fromDayNum = (n) => { const t = new Date(n * DAY); return iso(t.getUTCFullYear(), t.getUTCMonth() + 1, t.getUTCDate()); };
  const addDays = (s, n) => fromDayNum(dayNum(s) + n);
  const daysBetween = (a, b) => dayNum(b) - dayNum(a);
  // Jan 31 + 1 month = Feb 28 (29 in a leap year): the day is clamped to the end of the month, as in a service book
  const addMonths = (s, n) => {
    const p = parseDate(s);
    if (!p) return null;
    const total = p.y * 12 + (p.m - 1) + n;
    const y = Math.floor(total / 12);
    const m = total - y * 12 + 1;
    return iso(y, m, Math.min(p.d, daysIn(y, m)));
  };
  const localToday = (now = new Date()) => iso(now.getFullYear(), now.getMonth() + 1, now.getDate());

  /* ---------- VIN: 17 Latin letters and digits without I, O, Q; spaces go, Cyrillic look-alikes become Latin ---------- */
  const LOOKALIKE = { 'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X' };
  const normalizeVin = (raw) => String(raw == null ? '' : raw).toUpperCase()
    .replace(/[\s\u00a0\u2000-\u200b\u202f\u2060\u2010-\u2015-]/g, '')
    .replace(/[АВЕКМНОРСТУХ]/g, (c) => LOOKALIKE[c]);
  const checkVin = (raw) => {
    const value = normalizeVin(raw);
    let error = null;
    if (value) {
      if (/[IOQ]/.test(value)) error = 'ioq';
      else if (!/^[A-Z0-9]+$/.test(value)) error = 'chars';
      else if (value.length !== 17) error = 'length';
    }
    return { value, error, length: value.length, fixed: /[АВЕКМНОРСТУХавекмнорстух]/.test(String(raw == null ? '' : raw)) };
  };

  /* ---------- numbers ---------- */
  const fmtNum = (n) => String(Math.round(Math.abs(n))).replace(/\B(?=(\d{3})+(?!\d))/g, NB);
  // an optional whole number typed by a person: null when empty, NaN when it is not a number in [lo, hi]
  const parseWhole = (raw, lo, hi) => {
    const s = String(raw == null ? '' : raw).replace(/[\s\u00a0\u202f]/g, '').replace(/(км|мес)\.?$/i, '');
    if (!s) return null;
    if (!/^\d{1,9}$/.test(s)) return NaN;
    const n = Number(s);
    return n >= lo && n <= hi ? n : NaN;
  };
  const parseKm = (raw) => parseWhole(raw, 0, MAX_KM);

  /* ---------- the book ---------- */
  const newId = () => {
    let r = '';
    try {
      const a = new Uint32Array(2);
      window.crypto.getRandomValues(a);
      r = a[0].toString(36) + a[1].toString(36);
    } catch (_) { r = Math.random().toString(36).slice(2, 12); }
    return `${Date.now().toString(36)}-${r}`.slice(0, 40);
  };
  const emptyBook = () => ({ format: FORMAT, version: VERSION, id: '', car: null, reminder: { km: null, months: null }, entries: [] });
  const hasData = (b) => !!(b.car || b.entries.length || b.reminder.km || b.reminder.months);
  const isTo = (e) => e.works.indexOf('to') >= 0;
  const newestFirst = (a, b) => dayNum(b.date) - dayNum(a.date)
    || (b.km === null ? -1 : b.km) - (a.km === null ? -1 : a.km) || b.created - a.created;
  const lastService = (entries) => entries.filter(isTo).sort(newestFirst)[0] || null;
  // the highest mileage known (the passport or any entry) and the day it was read
  const reading = (book) => {
    const all = [];
    if (book.car && book.car.km !== null) all.push({ km: book.car.km, date: book.car.kmDate });
    book.entries.forEach((e) => { if (e.km !== null) all.push({ km: e.km, date: e.date }); });
    all.sort((a, b) => b.km - a.km || (dayNum(b.date) || 0) - (dayNum(a.date) || 0));
    return all[0] || null;
  };

  /* ---------- the next service: the owner's interval from the last «ТО», whichever limit comes first ----------
     state: setup (no interval) | need-to (no entry marked «ТО») | no-km (only a km interval, the «ТО» has no km)
            | ok | soon (≥ 90 % of a limit) | over (a limit reached) */
  const forecast = (book, today) => {
    const r = book.reminder || {};
    const f = { state: 'setup', base: null, km: null, time: null, rate: null, date: null, by: null, noBaseKm: false, guess: false };
    if (!r.km && !r.months) return f;
    const base = lastService(book.entries);
    if (!base) { f.state = 'need-to'; return f; }
    f.base = { id: base.id, date: base.date, km: base.km };
    if (r.km && base.km === null) f.noBaseKm = true;
    if (r.km && base.km !== null) {
      const now = reading(book);
      const current = Math.max(now ? now.km : base.km, base.km);
      const used = current - base.km;
      f.km = { interval: r.km, from: base.km, due: base.km + r.km, current, used, left: base.km + r.km - current, frac: used / r.km, date: null };
      const span = now && now.date ? daysBetween(base.date, now.date) : 0;
      if (span >= RATE_DAYS && used > 0) {
        f.rate = used / span;
        if (f.km.left > 0) {
          f.km.date = addDays(now.date, Math.ceil(f.km.left / f.rate));
          // an old reading can put the estimate in the past: then it is «about now» and worth a fresh reading
          if (daysBetween(today, f.km.date) < 0) { f.km.date = today; f.guess = true; }
        }
      }
    }
    if (r.months) {
      const due = addMonths(base.date, r.months);
      const total = daysBetween(base.date, due);
      f.time = { months: r.months, from: base.date, due, left: daysBetween(today, due), passed: Math.max(0, daysBetween(base.date, today)), total, frac: 0 };
      f.time.frac = total > 0 ? f.time.passed / total : 1;
    }
    const ends = [];
    if (f.time) ends.push({ date: f.time.due, by: 'time' });
    if (f.km && f.km.date) ends.push({ date: f.km.date, by: 'km' });
    ends.sort((a, b) => dayNum(a.date) - dayNum(b.date));
    if (ends.length) { f.date = ends[0].date; f.by = ends[0].by; }
    const over = (f.km && f.km.left <= 0) || (f.time && f.time.left <= 0);
    const worst = Math.max(f.km ? f.km.frac : 0, f.time ? f.time.frac : 0);
    if (over) f.state = 'over';
    else if (worst >= SOON || f.guess) f.state = 'soon';
    else f.state = f.km || f.time ? 'ok' : 'no-km';
    return f;
  };

  /* ---------- .ics (RFC 5545): CRLF, TEXT escaping, lines folded at 75 octets without cutting a letter ---------- */
  const icsText = (s) => String(s).replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r\n|\r|\n/g, '\\n');
  const octets = (ch) => { const c = ch.codePointAt(0); return c < 0x80 ? 1 : c < 0x800 ? 2 : c < 0x10000 ? 3 : 4; };
  const tokenOctets = (tok) => { let n = 0; for (const ch of tok) n += octets(ch); return n; };
  const icsFold = (line) => {
    const out = [];
    let cur = []; let size = 0;
    (String(line).match(/\\[\s\S]|[\s\S]/gu) || []).forEach((tok) => {   // an escape («\,») is one token
      const n = tokenOctets(tok);
      if (size + n > 75) {
        // a continuation line starts with one space; were the text's own space next, a careless reader would trim
        // both and glue two words: the last letter moves down with it
        const carry = /^\s/.test(tok) && cur.length > 1 ? [cur.pop()] : [];
        out.push(cur.join(''));
        cur = [' ', ...carry];
        size = 1 + carry.reduce((s, x) => s + tokenOctets(x), 0);
      }
      cur.push(tok);
      size += n;
    });
    out.push(cur.join(''));
    return out;
  };
  const icsStamp = (d) => new Date(d).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  // an all-day event on the date; the alarm at 9:00 the day before (-PT15H from the day's midnight, as Apple Calendar
  // writes «1 day before» for all-day events)
  const buildIcs = (ev) => {
    const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//garage.team//Moya mashina//RU', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'BEGIN:VEVENT', `UID:${ev.uid}`, `DTSTAMP:${icsStamp(ev.stamp)}`,
      `DTSTART;VALUE=DATE:${ev.date.replace(/-/g, '')}`, `DTEND;VALUE=DATE:${addDays(ev.date, 1).replace(/-/g, '')}`,
      `SUMMARY:${icsText(ev.summary)}`];
    if (ev.description) lines.push(`DESCRIPTION:${icsText(ev.description)}`);
    if (ev.url) lines.push(`URL:${ev.url}`);
    lines.push('TRANSP:TRANSPARENT', 'BEGIN:VALARM', 'ACTION:DISPLAY', `DESCRIPTION:${icsText(ev.alarm || ev.summary)}`,
      'TRIGGER:-PT15H', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR');
    return lines.reduce((all, l) => all.concat(icsFold(l)), []).join('\r\n') + '\r\n';
  };

  /* ---------- a book from a file or the storage: every field checked, the broken ones dropped ---------- */
  const isObj = (v) => !!v && typeof v === 'object' && !Array.isArray(v);
  const oneLine = (v, max) => (typeof v === 'string' ? v.replace(/\s+/g, ' ').trim().slice(0, max) : '');
  const para = (v, max) => (typeof v === 'string'
    ? v.replace(/\r\n?/g, '\n').replace(/[^\S\n]+/g, ' ').replace(/ *\n */g, '\n').replace(/\n{3,}/g, '\n\n').trim().slice(0, max) : '');
  const whole = (v, lo, hi) => (typeof v === 'number' && Number.isInteger(v) && v >= lo && v <= hi ? v : null);
  const moment = (v) => (typeof v === 'number' && Number.isFinite(v) && v >= 0 ? Math.round(v) : 0);
  const sanitizeCar = (c) => {
    if (!isObj(c)) return null;
    const brand = oneLine(c.brand, LEN.brand);
    const model = oneLine(c.model, LEN.model);
    if (!brand && !model) return null;
    const vin = checkVin(typeof c.vin === 'string' ? c.vin : '');
    const km = whole(c.km, 0, MAX_KM);
    return { brand, model, year: whole(c.year, 1900, 2199), engine: oneLine(c.engine, LEN.engine), vin: vin.error ? '' : vin.value,
      km, kmDate: km !== null && parseDate(c.kmDate) ? c.kmDate : null };
  };
  const sanitizeEntry = (e, keys) => {
    if (!isObj(e) || !parseDate(e.date)) return null;
    const works = keys.filter((k) => Array.isArray(e.works) && e.works.indexOf(k) >= 0);   // known marks, fixed order
    const text = para(e.text, LEN.text);
    if (!works.length && !text) return null;
    return { id: typeof e.id === 'string' && ID.test(e.id) ? e.id : newId(), date: e.date, km: whole(e.km, 0, MAX_KM), works, text,
      note: oneLine(e.note, LEN.note), created: moment(e.created), updated: moment(e.updated) };
  };
  // → { ok: true, book, dropped } | { ok: false, error: 'format' | 'newer' | 'big' }
  const sanitizeBook = (obj, keys) => {
    if (!isObj(obj) || obj.format !== FORMAT || !Number.isInteger(obj.version) || obj.version < 1) return { ok: false, error: 'format' };
    if (obj.version > VERSION) return { ok: false, error: 'newer' };
    if (obj.entries !== undefined && !Array.isArray(obj.entries)) return { ok: false, error: 'format' };
    const list = obj.entries || [];
    if (list.length > MAX_ENTRIES) return { ok: false, error: 'big' };
    const seen = new Set();
    const entries = [];
    let dropped = 0;
    list.forEach((e) => {
      const s = sanitizeEntry(e, keys || []);
      if (!s) { dropped += 1; return; }
      while (seen.has(s.id)) s.id = newId();
      seen.add(s.id);
      entries.push(s);
    });
    const r = isObj(obj.reminder) ? obj.reminder : {};
    return { ok: true, dropped, book: { format: FORMAT, version: VERSION, id: typeof obj.id === 'string' && ID.test(obj.id) ? obj.id : newId(),
      car: sanitizeCar(obj.car), reminder: { km: whole(r.km, INTERVAL_KM[0], INTERVAL_KM[1]), months: whole(r.months, INTERVAL_MONTHS[0], INTERVAL_MONTHS[1]) },
      entries } };
  };
  const serial = (book, now) => ({ format: FORMAT, version: VERSION, saved: new Date(now).toISOString(), id: book.id, car: book.car,
    reminder: book.reminder, entries: book.entries });

  /* ---------- merging a copy into the book: the same entry (id or content) once, the newer edit wins ---------- */
  const sameCar = (a, b) => a.brand.toLowerCase() === b.brand.toLowerCase() && a.model.toLowerCase() === b.model.toLowerCase()
    && (!a.vin || !b.vin || a.vin === b.vin);
  const mergeCar = (a, b) => {
    if (!a || !b) return a || b || null;
    if (!sameCar(a, b)) return a;
    const later = b.km !== null && (a.km === null || b.km > a.km);
    return { ...a, year: a.year || b.year, engine: a.engine || b.engine, vin: a.vin || b.vin, km: later ? b.km : a.km, kmDate: later ? b.kmDate : a.kmDate };
  };
  const signature = (e) => [e.date, e.km === null ? '' : e.km, e.works.join('+'), e.text, e.note].join('|');
  const mergeBooks = (cur, inc) => {
    const entries = cur.entries.slice();
    const at = new Map(entries.map((e, i) => [e.id, i]));
    const sigs = new Set(entries.map(signature));
    let added = 0; let updated = 0; let skipped = 0;
    inc.entries.forEach((e) => {
      if (at.has(e.id)) {
        const i = at.get(e.id);
        if (e.updated > entries[i].updated && signature(e) !== signature(entries[i])) {
          sigs.delete(signature(entries[i]));
          entries[i] = e;
          sigs.add(signature(e));
          updated += 1;
        }
        return;
      }
      if (sigs.has(signature(e))) return;                  // the same work entered on another device
      if (entries.length >= MAX_ENTRIES) { skipped += 1; return; }
      at.set(e.id, entries.length);
      entries.push(e);
      sigs.add(signature(e));
      added += 1;
    });
    const reminder = cur.reminder.km || cur.reminder.months ? cur.reminder : inc.reminder;
    return { book: { ...cur, id: cur.id || inc.id, car: mergeCar(cur.car, inc.car), reminder: { ...reminder }, entries }, added, updated, skipped };
  };

  /* ---------- storage: this browser only; the calls throw when storage is blocked (private modes, settings) ---------- */
  const ls = () => window.localStorage;
  const store = {
    probe() {
      try { ls().setItem(`${KEY}.probe`, '1'); ls().removeItem(`${KEY}.probe`); return true; } catch (_) { return false; }
    },
    read() {
      let raw = null;
      try { raw = ls().getItem(KEY); } catch (_) { return { status: 'off' }; }
      if (raw === null) return { status: 'empty' };
      try { return { status: 'ok', obj: JSON.parse(raw), raw }; } catch (_) { return { status: 'broken', raw }; }
    },
    write(obj) {
      try { ls().setItem(KEY, JSON.stringify(obj)); return 'ok'; } catch (e) {
        const full = e && (e.name === 'QuotaExceededError' || e.name === 'NS_ERROR_DOM_QUOTA_REACHED' || e.code === 22 || e.code === 1014);
        return full ? 'full' : 'off';
      }
    },
    // an unreadable saved book is set aside once before the first save over it
    keep(raw) { try { ls().setItem(`${KEY}.broken`, raw); } catch (_) { /* no room for the copy: the save goes on */ } },
    clear() {
      try { ls().removeItem(KEY); ls().removeItem(`${KEY}.broken`); return 'ok'; } catch (_) { return 'off'; }
    },
  };

  /* ---------- the car in words ---------- */
  const carTitle = (c) => [c.brand, c.model].filter(Boolean).join(' ');
  const engineText = (e) => (/^\d{1,2}([.,]\d{1,2})?$/.test(e) ? `${e.replace('.', ',')}${NB}л` : e);

  /* ---------- the request form on any page: «Заполнить из «Моей машины»» (build/knizhka.py fill_button) ---------- */
  const fillButtons = Array.from(document.querySelectorAll('[data-kn-fill]'));
  const savedCar = () => {
    const r = store.read();
    if (r.status !== 'ok') return null;
    const s = sanitizeBook(r.obj, []);
    return s.ok ? s.book.car : null;
  };
  const syncFill = (car) => fillButtons.forEach((btn) => {
    btn.hidden = !car;
    const name = btn.querySelector('[data-kn-fill-car]');
    if (name) name.textContent = car ? [carTitle(car), car.year].filter(Boolean).join(' · ') : '';
  });
  const fillRequest = (btn, car) => {
    const form = btn.closest('form');
    if (!form) return;
    // form.js keeps the mode in a hidden field: '1' lists to choose from, '0' the car typed in; its toggle switches it
    const mode = form.querySelector('input[name="request_part[select_car_type]"]');
    const toggle = form.querySelector('[data-mode-toggle]');
    if (mode && mode.value !== '0' && toggle) toggle.click();
    const fields = [['#text_car_brand', car.brand], ['#text_car_model', car.model], ['#text_car_year', car.year ? String(car.year) : ''],
      ['#text_car_type', car.engine ? engineText(car.engine) : ''], ['#car_vin', car.vin]];
    fields.forEach(([sel, value]) => {
      const f = form.querySelector(sel);
      if (!f || !value) return;
      f.value = value;
      f.dispatchEvent(new Event('input', { bubbles: true }));   // clears a «fill in the field» mark of form.js
    });
    if (G.toast) G.toast(btn.dataset.knFill);
    // with a mouse, straight to what is still empty (on a phone that would throw the keyboard up)
    const empty = fields.slice(0, 4).map(([sel]) => form.querySelector(sel)).find((f) => f && !f.value.trim());
    if (empty && G.canHover) empty.focus();
  };
  if (fillButtons.length) {
    fillButtons.forEach((btn) => btn.addEventListener('click', () => {
      const car = savedCar();
      syncFill(car);
      if (car) fillRequest(btn, car);
    }));
    syncFill(savedCar());
    addEventListener('storage', (e) => { if (e.key === KEY || e.key === null) syncFill(savedCar()); });
    addEventListener('pageshow', (e) => { if (e.persisted) syncFill(savedCar()); });
  }

  G.knizhka = {
    KEY, FORMAT, VERSION, NB, LIMITS: { LEN, INTERVAL_KM, INTERVAL_MONTHS, MAX_ENTRIES, MAX_FILE, SOON },
    parseDate, pad, addDays, addMonths, daysBetween, localToday, fmtNum, parseWhole, parseKm, oneLine, para,
    normalizeVin, checkVin, newId, emptyBook, hasData, isTo, newestFirst, forecast, sanitizeBook, mergeBooks, serial,
    icsText, icsFold, buildIcs, store, carTitle, engineText, syncFill,
  };
})();
