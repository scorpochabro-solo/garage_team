/* ============================================================
   knizhka-ui: the page «Моя машина» (/moya-mashina/, build/knizhka.py; the model is js/knizhka.js):
   · the first visit: the garage bay, «Завести книжку» rolls its shutter up and opens the passport;
   · the passport as a steel plate with a mechanical odometer, a quick «Обновить пробег»;
   · the next service: the owner's interval, two gauges (km, days), the estimated date, the calendar file,
     «Записаться на ТО»;
   · the log: add, edit, delete after a question, newest first by year; «Записаться» with the chosen works;
   · the copy: save (.json), load (merge or replace), print, delete everything.
   Every phrase comes from build/knizhka.py (data-kn-conf). Motion: transform and opacity only (knizhka.css).
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};
  const K = G.knizhka;
  if (!K) return;
  const { KEY, NB, LIMITS: { LEN, INTERVAL_KM, INTERVAL_MONTHS, MAX_ENTRIES, MAX_FILE, SOON }, parseDate, pad, daysBetween, localToday,
    fmtNum, parseWhole, parseKm, oneLine, para, checkVin, newId, emptyBook, hasData, isTo, newestFirst, forecast, sanitizeBook,
    mergeBooks, serial, buildIcs, store, carTitle, engineText, syncFill } = K;

  const root = document.querySelector('[data-knizhka]');
  if (!root) return;
  let conf = null;
  try { conf = JSON.parse(root.dataset.knConf || ''); } catch (_) { conf = null; }
  if (!conf || !conf.texts || !Array.isArray(conf.works)) return;
  const T = conf.texts;
  const KEYS = conf.works.map((w) => w.key);
  const LABEL = {};
  const PHRASE = {};
  conf.works.forEach((w) => { LABEL[w.key] = w.label; PHRASE[w.key] = w.phrase; });
  const t = (key, vars) => String(T[key] == null ? '' : T[key]).replace(/\{(\w+)\}/g, (m, k) => (vars && k in vars ? String(vars[k]) : m));
  const plural = (n, forms) => {
    const a = Math.abs(n) % 100; const b = a % 10;
    return forms[a > 10 && a < 20 ? 2 : b === 1 ? 0 : b >= 2 && b <= 4 ? 1 : 2];
  };
  const count = (n, key) => `${fmtNum(n)}${NB}${plural(n, T[key])}`;
  const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
  const fmtDate = (s) => { const p = parseDate(s); return p ? `${pad(p.d)}.${pad(p.m)}.${p.y}` : ''; };
  const fmtLong = (s) => { const p = parseDate(s); return p ? `${p.d}${NB}${MONTHS[p.m - 1]}${NB}${p.y}` : ''; };   // one piece
  const toast = (msg, type) => { if (G.toast && msg) G.toast(msg, type); };
  const $ = (sel, r = root) => r.querySelector(sel);
  const $$ = (sel, r = root) => Array.from(r.querySelectorAll(sel));
  // an element with a class and a text (textContent: whatever the visitor typed never becomes markup)
  const node = (tag, cls, text) => Object.assign(document.createElement(tag), cls ? { className: cls } : {}, text !== undefined ? { textContent: text } : {});
  const smooth = () => (G.reducedMotion ? 'auto' : 'smooth');
  // «Kia Rio, 2017 г., 1,6 л» (+ «пробег 84 500 км»): the car line of a message
  const carLine = (c, km) => {
    if (!c) return '';
    const parts = [carTitle(c)];
    if (c.year) parts.push(`${c.year}${NB}г.`);
    if (c.engine) parts.push(engineText(c.engine));
    if (km && c.km !== null) parts.push(t('carKm', { km: fmtNum(c.km) }));
    return parts.join(', ');
  };
  const pageUrl = () => { const c = document.querySelector('link[rel="canonical"]'); return c ? c.href : location.href.split('#')[0]; };

  const el = {
    alert: $('[data-kn-alert]'), start: $('[data-kn-start]'), intro: $('[data-kn-intro]'), desk: $('[data-kn-desk]'),
    slotStart: $('[data-kn-slot="start"]'), slotBook: $('[data-kn-slot="book"]'), carForm: $('[data-kn-car-form]'),
    plate: $('[data-kn-plate]'), name: $('[data-kn-name]'), nameHint: $('[data-kn-name-hint]'), year: $('[data-kn-year]'),
    engine: $('[data-kn-engine]'), vin: $('[data-kn-vin]'), drums: $('[data-kn-drums]'), odoSr: $('[data-kn-odo-sr]'),
    odoCap: $('[data-kn-odo-cap]'), odoOpen: $('[data-kn-odo-open]'), odoForm: $('[data-kn-odo-form]'),
    next: $('[data-kn-next]'), rule: $('[data-kn-rule]'), ruleText: $('[data-kn-rule-text]'), main: $('[data-kn-main]'),
    need: $('[data-kn-need]'), head: $('[data-kn-head]'), sub: $('[data-kn-sub]'), note: $('[data-kn-note]'), ics: $('[data-kn-ics]'),
    icsNote: $('[data-kn-ics-note]'), interval: $('[data-kn-interval]'), intervalHead: $('[data-kn-interval-head]'),
    intervalErr: $('[data-kn-interval-err]'), intervalCancel: $('[data-kn-interval-cancel]'),
    list: $('[data-kn-list]'), empty: $('[data-kn-empty]'), count: $('[data-kn-count]'), add: $('[data-kn-add]'),
    entryForm: $('[data-kn-entry-form]'), entryTitle: $('[data-kn-entry-title]'), sheet: $('[data-kn-sheet]'),
  };
  const cf = { brand: $('#kn-c-brand'), model: $('#kn-c-model'), year: $('#kn-c-year'), engine: $('#kn-c-engine'), vin: $('#kn-c-vin'),
    km: $('#kn-c-km'), kmHint: $('[data-kn-km-hint]'), vinNote: $('[data-kn-vin-note]') };
  const ef = { date: $('#kn-e-date'), km: $('#kn-e-km'), text: $('#kn-e-text'), note: $('#kn-e-note'), works: $$('input[name="works"]') };
  const iKm = $('#kn-i-km');
  const iMonths = $('#kn-i-months');
  const oKm = $('#kn-o-km');
  const bookWorks = $$('input[name="book-works"]');

  let book = emptyBook();
  let problem = '';        // '' | 'off' | 'full' | 'broken': the message over the book
  let brokenRaw = null;    // an unreadable saved book, set aside before the first save over it
  let carOpen = false;     // the passport form is open
  let intervalOpen = false;
  let editing = null;      // the id of the entry in the form, '' for a new one, null when the form is closed

  /* ---------- errors next to the fields (components.css .field.is-error) ---------- */
  const setErr = (input, msg) => {
    const field = input.closest('.field');
    const err = field ? field.querySelector('.field__error') : null;
    if (err && msg) err.textContent = msg;
    if (field) field.classList.toggle('is-error', !!msg);
    if (input.matches('input, textarea, select, fieldset')) input.setAttribute('aria-invalid', msg ? 'true' : 'false');
  };
  const clearErrs = (form) => form.querySelectorAll('.field').forEach((f) => {
    f.classList.remove('is-error');
    f.querySelectorAll('[aria-invalid]').forEach((x) => x.setAttribute('aria-invalid', 'false'));
  });
  // [[input, message]] → marks them, focuses the first; true when there was something to show
  const showErrs = (bad) => {
    bad.forEach(([input, msg]) => setErr(input, msg));
    if (!bad.length) return false;
    const first = bad[0][0];
    const target = first.matches('fieldset') ? first.querySelector('input') : first;
    if (target) { target.focus({ preventScroll: true }); target.scrollIntoView({ block: 'center', behavior: smooth() }); }
    return true;
  };
  [el.carForm, el.odoForm, el.entryForm].forEach((f) => { if (f && G.clearErrorsOnInput) G.clearErrorsOnInput(f); });
  ef.works.forEach((c) => c.addEventListener('change', () => setErr(c.closest('fieldset'), '')));

  /* ---------- load, save ---------- */
  const load = () => {
    const r = store.read();
    if (r.status === 'off') return { book: emptyBook(), problem: 'off' };
    if (r.status === 'empty') return { book: emptyBook(), problem: '' };
    const s = r.status === 'ok' ? sanitizeBook(r.obj, KEYS) : { ok: false };
    if (!s.ok) { brokenRaw = r.raw; return { book: emptyBook(), problem: 'broken' }; }
    return { book: s.book, problem: '' };
  };
  const commit = (next, message, after) => {
    book = next;
    if (brokenRaw !== null) { store.keep(brokenRaw); brokenRaw = null; }
    const res = store.write(serial(book, Date.now()));
    problem = res === 'ok' ? '' : res;
    render();
    syncFill(book.car);
    toast(message);
    if (after) after();
  };

  /* ---------- rendering ---------- */
  const renderAlert = () => {
    const msg = { off: T.storeOff, full: T.storeFull, broken: T.storeBroken }[problem] || '';
    if (el.alert.textContent !== msg) el.alert.textContent = msg;
    el.alert.hidden = !msg;
  };

  const makeDrum = () => {
    const d = node('span', 'kn-odo__d');
    const s = node('span', 'kn-odo__s');
    for (let k = 0; k < 10; k += 1) s.appendChild(node('span', '', String(k)));
    d.appendChild(s);
    return d;
  };
  // the mechanical odometer: one drum per digit (at least six), each rolls to its digit with transform
  const setOdo = (km) => {
    const digits = km === null ? '' : String(km);
    const n = Math.max(6, digits.length);
    let grew = false;
    while (el.drums.children.length < n) { el.drums.insertBefore(makeDrum(), el.drums.firstChild); grew = true; }
    while (el.drums.children.length > n) el.drums.removeChild(el.drums.firstChild);
    if (grew) void el.drums.offsetWidth;   // new drums start at 0 and roll to their digit
    const padded = digits.padStart(n, '0');
    Array.from(el.drums.children).forEach((d, i) => {
      d.style.setProperty('--n', km === null ? '0' : padded[i]);
      d.style.setProperty('--i', String(n - 1 - i));
      d.classList.toggle('is-lead', km === null || i < n - digits.length);
    });
  };
  const renderVin = (vin) => {
    el.vin.textContent = '';
    el.vin.classList.toggle('is-empty', !vin);
    if (!vin) { el.vin.textContent = T.none; return; }
    // the three parts of a VIN (maker, description, serial) with gaps that do not get copied
    [vin.slice(0, 3), vin.slice(3, 9), vin.slice(9)].forEach((part) => el.vin.appendChild(node('span', '', part)));
  };
  const renderPlate = () => {
    const c = book.car;
    el.plate.hidden = carOpen;
    el.name.textContent = c ? carTitle(c) : T.noCar;
    el.name.classList.toggle('is-empty', !c);
    el.nameHint.hidden = !!c;
    el.year.textContent = c && c.year ? String(c.year) : '—';
    el.engine.textContent = c && c.engine ? engineText(c.engine) : '—';
    renderVin(c ? c.vin : '');
    const km = c ? c.km : null;
    setOdo(km);
    el.odoCap.textContent = km === null ? T.kmNone : t('kmAt', { date: fmtDate(c.kmDate) || '—' });
    el.odoSr.textContent = km === null ? T.kmNone : t('kmSr', { km: fmtNum(km), date: fmtDate(c.kmDate) || '—' });
    el.odoOpen.hidden = !c || !el.odoForm.hidden;
  };

  const ruleText = (r) => {
    if (r.km && r.months) return t('rule', { km: fmtNum(r.km), months: count(r.months, 'pMonths') });
    if (r.km) return t('ruleKm', { km: fmtNum(r.km) });
    return r.months ? t('ruleMonths', { months: count(r.months, 'pMonths') }) : '';
  };
  const lastLine = (base) => [fmtDate(base.date), base.km === null ? '' : `${fmtNum(base.km)}${NB}км`].filter(Boolean).join(', ');
  const setMeter = (kind, m) => {
    const box = $(`[data-kn-meter="${kind}"]`);
    const body = box.querySelector('[data-body]');
    const none = box.querySelector('[data-none]');
    body.hidden = !m.show;
    none.hidden = m.show || !m.none;
    none.textContent = m.none || '';
    box.dataset.state = m.show ? m.state : 'none';
    if (!m.show) return;
    const frac = Math.min(1, Math.max(0, m.frac));
    const track = box.querySelector('[data-track]');
    box.querySelector('[data-pre]').textContent = m.pre;
    box.querySelector('[data-val]').textContent = m.value;
    box.querySelector('[data-a]').textContent = m.a;
    box.querySelector('[data-b]').textContent = m.b;
    track.style.setProperty('--f', frac.toFixed(4));
    track.setAttribute('aria-valuenow', String(Math.round(frac * 100)));
    track.setAttribute('aria-valuetext', m.text);
  };
  const meterState = (left, frac) => (left <= 0 ? 'over' : frac >= SOON ? 'soon' : 'ok');
  // the big line of the card and the line under it
  const headline = (f) => {
    if (f.state === 'over') {
      const why = [];
      if (f.km && f.km.left < 0) why.push(t('subOverKm', { km: fmtNum(-f.km.left) }));
      if (f.km && f.km.left === 0) why.push(T.subKmReached);
      if (f.time && f.time.left < 0) why.push(t('subOverTime', { days: count(-f.time.left, 'pDays') }));
      if (f.time && f.time.left === 0) why.push(T.subToday);
      return { head: T.headOver, sub: why.join(' ') };
    }
    if (f.guess) return { head: T.headGuess, sub: '' };
    if (f.date) {
      return { head: t(f.state === 'soon' ? 'headSoon' : 'headOk', { date: fmtLong(f.date) }),
        sub: t(f.time && f.km && f.km.date ? 'subBoth' : 'subOne', { by: f.by === 'km' ? T.byKm : T.byTime }) };
    }
    if (f.km) return { head: t('headKm', { km: fmtNum(f.km.left) }), sub: T.subNoDate };
    return { head: T.headNoKm, sub: T.noBaseKm };
  };
  const renderNext = () => {
    const today = localToday();
    const f = forecast(book, today);
    const r = book.reminder;
    const setup = f.state === 'setup' || intervalOpen;
    el.next.dataset.state = setup ? 'setup' : f.state;
    el.rule.hidden = !(r.km || r.months) || intervalOpen;
    el.ruleText.textContent = ruleText(r);
    el.interval.hidden = !setup;
    el.intervalCancel.hidden = !intervalOpen;
    el.intervalHead.hidden = intervalOpen;
    el.need.hidden = setup || f.state !== 'need-to';
    el.main.hidden = setup || f.state === 'need-to';
    if (el.main.hidden) return;

    const { head, sub } = headline(f);
    el.head.textContent = head;
    el.sub.textContent = sub;
    el.sub.hidden = !sub;

    if (f.km) {
      const k = f.km;
      setMeter('km', { show: true, state: meterState(k.left, k.frac), frac: k.frac, pre: k.left > 0 ? T.left : k.left < 0 ? T.overKm : '',
        value: k.left === 0 ? T.today : `${fmtNum(k.left)}${NB}км`, a: `${fmtNum(k.from)}${NB}км`, b: `${fmtNum(k.due)}${NB}км`,
        text: t('meterKm', { used: fmtNum(Math.max(0, k.used)), all: fmtNum(k.interval) }) });
    } else {
      setMeter('km', { show: false, none: r.km ? (f.noBaseKm ? T.noBaseKm : '') : T.noKmInterval });
    }
    if (f.time) {
      const d = f.time;
      setMeter('time', { show: true, state: meterState(d.left, d.frac), frac: d.frac, pre: d.left > 0 ? T.left : d.left < 0 ? T.overTime : '',
        value: d.left === 0 ? T.today : count(Math.abs(d.left), 'pDays'), a: fmtDate(d.from), b: fmtDate(d.due),
        text: t('meterTime', { used: count(Math.min(d.passed, d.total), 'pDays'), all: count(d.total, 'pDays') }) });
    } else {
      setMeter('time', { show: false, none: T.noTimeInterval });
    }

    let note = '';
    if (f.guess) note = T.noteGuess;
    else if (f.rate && f.km && f.km.left > 0) note = t('noteRate', { km: fmtNum(Math.max(1, Math.round(f.rate))) });
    else if (f.km && f.km.left > 0) note = T.noteNoRate;
    el.note.textContent = note;
    el.note.hidden = !note;

    const canIcs = f.state !== 'over' && !!f.date && daysBetween(today, f.date) > 0;
    el.ics.hidden = f.state === 'over';
    el.ics.disabled = !canIcs;
    el.icsNote.hidden = canIcs || f.state === 'over';
    el.icsNote.textContent = T.icsNoDate;
  };

  const SVG = 'http://www.w3.org/2000/svg';
  const svgUse = (name) => {   // an icon of the page's own sprite (build/knizhka.py _sprite)
    const svg = document.createElementNS(SVG, 'svg');
    const use = document.createElementNS(SVG, 'use');
    [['class', 'ic'], ['aria-hidden', 'true'], ['focusable', 'false']].forEach(([k, v]) => svg.setAttribute(k, v));
    use.setAttribute('href', `#kn-i-${name}`);
    svg.appendChild(use);
    return svg;
  };
  const toolButton = (act, icon, label, aria) => {   // «Изменить» / «Удалить» of an entry; the name says which entry
    const b = Object.assign(node('button', 'kn-link'), { type: 'button' });
    b.dataset.act = act;
    b.setAttribute('aria-label', aria);
    b.append(svgUse(icon), node('span', '', label));
    return b;
  };
  const entryNode = (e) => {
    const li = node('li', `kn-entry${isTo(e) ? ' is-to' : ''}${editing === e.id ? ' is-editing' : ''}`);
    li.dataset.id = e.id;
    li.tabIndex = -1;
    const date = fmtDate(e.date);
    const when = node('div', 'kn-entry__when');
    const time = node('time', 'kn-entry__date', date);
    time.dateTime = e.date;
    when.append(time, node('span', 'kn-entry__km', e.km === null ? T.entryKmNone : `${fmtNum(e.km)}${NB}км`));
    if (isTo(e)) {
      const stamp = node('span', 'kn-stamp', T.stamp);
      stamp.setAttribute('aria-hidden', 'true');
      when.appendChild(stamp);
    }
    const body = node('div', 'kn-entry__body');
    if (e.works.length) {
      const tags = node('ul', 'kn-tags');
      tags.setAttribute('aria-label', T.tagsAria);
      e.works.forEach((k) => tags.appendChild(node('li', `kn-tag${k === 'to' ? ' kn-tag--to' : ''}`, LABEL[k] || k)));
      body.appendChild(tags);
    }
    if (e.text) body.appendChild(node('p', 'kn-entry__text', e.text));
    if (e.note) body.appendChild(node('p', 'kn-entry__note', e.note));
    const tools = node('div', 'kn-entry__tools');
    tools.append(toolButton('edit', 'pencil', T.edit, t('editAria', { date })), toolButton('remove', 'trash', T.remove, t('removeAria', { date })));
    li.append(when, body, tools);
    return li;
  };
  const renderLog = () => {
    const sorted = book.entries.slice().sort(newestFirst);
    el.list.textContent = '';
    el.count.textContent = sorted.length ? count(sorted.length, 'pEntries') : '';
    el.empty.hidden = sorted.length > 0 || editing !== null;
    let year = ''; let ol = null;
    sorted.forEach((e) => {
      if (e.date.slice(0, 4) !== year) {
        year = e.date.slice(0, 4);
        const group = node('div', 'kn-year');
        ol = node('ol', 'kn-entries');
        group.append(node('h3', 'kn-year__y', year), ol);
        el.list.appendChild(group);
      }
      ol.appendChild(entryNode(e));
    });
  };

  const render = () => {
    const has = hasData(book);
    root.dataset.state = has ? 'book' : 'start';
    el.start.hidden = has;
    el.desk.hidden = !has;
    const slot = has ? el.slotBook : el.slotStart;
    if (el.carForm.parentNode !== slot) slot.appendChild(el.carForm);
    el.carForm.hidden = !carOpen;
    renderAlert();
    if (!has) {
      el.intro.hidden = carOpen;
      el.start.classList.toggle('is-open', carOpen);
      return;
    }
    renderPlate();
    renderNext();
    renderLog();
  };

  /* ---------- the passport ---------- */
  const maxYear = () => new Date().getFullYear() + 1;
  const kmHint = () => {
    const c = book.car;
    cf.kmHint.textContent = c && c.km !== null && c.kmDate ? t('kmHintAt', { date: fmtDate(c.kmDate) }) : T.kmHintNew;
  };
  const openCar = () => {
    const c = book.car || { brand: '', model: '', year: null, engine: '', vin: '', km: null };
    cf.brand.value = c.brand; cf.model.value = c.model; cf.year.value = c.year ? String(c.year) : '';
    cf.engine.value = c.engine; cf.vin.value = c.vin; cf.km.value = c.km === null ? '' : String(c.km);
    cf.vinNote.hidden = true;
    kmHint();
    clearErrs(el.carForm);
    carOpen = true;
    render();
    (G.canHover ? cf.brand : $('#kn-c-title')).focus({ preventScroll: true });
    el.carForm.scrollIntoView({ block: 'nearest', behavior: smooth() });
  };
  const closeCar = () => {
    carOpen = false;
    render();
    const back = hasData(book) ? $('[data-kn-car-edit]') : $('[data-kn-go]');
    if (back) back.focus({ preventScroll: true });
  };
  const vinMessage = (v) => (v.error === 'length' ? t('vinLength', { n: v.length }) : v.error === 'ioq' ? T.vinIoq : T.vinChars);
  cf.vin.addEventListener('blur', () => {
    const v = checkVin(cf.vin.value);
    if (!cf.vin.value.trim()) { cf.vinNote.hidden = true; return; }
    cf.vin.value = v.value;
    cf.vinNote.hidden = !v.fixed;
    setErr(cf.vin, v.error ? vinMessage(v) : '');
  });
  el.carForm.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const brand = oneLine(cf.brand.value, LEN.brand);
    const model = oneLine(cf.model.value, LEN.model);
    const yearRaw = cf.year.value.trim();
    const year = yearRaw ? parseWhole(yearRaw, 1900, maxYear()) : null;
    const vin = checkVin(cf.vin.value);
    const km = parseKm(cf.km.value);
    const bad = [];
    if (!brand) bad.push([cf.brand, T.errBrand]);
    if (!model) bad.push([cf.model, T.errModel]);
    if (Number.isNaN(year) || (yearRaw && !/^\d{4}$/.test(yearRaw))) bad.push([cf.year, t('errYear', { max: maxYear() })]);
    if (vin.error) bad.push([cf.vin, vinMessage(vin)]);
    if (Number.isNaN(km)) bad.push([cf.km, T.errKm]);
    if (showErrs(bad)) return;
    const prev = book.car;
    const today = localToday();
    const kmDate = km === null ? null : (prev && prev.km === km && prev.kmDate ? prev.kmDate : today);
    const car = { brand, model, year, engine: oneLine(cf.engine.value, LEN.engine), vin: vin.value, km, kmDate };
    carOpen = false;
    commit({ ...book, id: book.id || newId(), car }, T.carSaved, () => {
      el.plate.focus({ preventScroll: true });
      el.plate.scrollIntoView({ block: 'nearest', behavior: smooth() });
    });
  });
  $('[data-kn-car-cancel]').addEventListener('click', closeCar);
  $('[data-kn-car-edit]').addEventListener('click', openCar);
  $('[data-kn-go]').addEventListener('click', openCar);

  /* the mileage, quickly: never less than what is already written (a correction goes through the passport) */
  const closeOdo = (focus) => {
    el.odoForm.hidden = true;
    el.odoOpen.hidden = !book.car;
    clearErrs(el.odoForm);
    if (focus) el.odoOpen.focus({ preventScroll: true });
  };
  el.odoOpen.addEventListener('click', () => {
    el.odoForm.hidden = false;
    el.odoOpen.hidden = true;
    oKm.value = '';
    oKm.focus();
  });
  $('[data-kn-odo-cancel]').addEventListener('click', () => closeOdo(true));
  el.odoForm.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const c = book.car;
    if (!c) { closeOdo(false); return; }
    const km = parseKm(oKm.value);
    if (km === null || Number.isNaN(km)) { showErrs([[oKm, T.errKm]]); return; }
    if (c.km !== null && km < c.km) { showErrs([[oKm, t('errKmLess', { km: fmtNum(c.km) })]]); return; }
    closeOdo(false);
    commit({ ...book, car: { ...c, km, kmDate: localToday() } }, T.kmSaved, () => el.odoOpen.focus({ preventScroll: true }));
  });

  /* ---------- the interval ---------- */
  const intervalError = (msg, input) => {
    el.intervalErr.textContent = msg;
    el.intervalErr.hidden = !msg;
    [iKm, iMonths].forEach((i) => i.setAttribute('aria-invalid', msg && (!input || i === input) ? 'true' : 'false'));
    if (msg && input) input.focus();
  };
  [iKm, iMonths].forEach((i) => i.addEventListener('input', () => intervalError('')));
  $('[data-kn-interval-edit]').addEventListener('click', () => {
    iKm.value = book.reminder.km ? String(book.reminder.km) : '';
    iMonths.value = book.reminder.months ? String(book.reminder.months) : '';
    intervalError('');
    intervalOpen = true;
    renderNext();
    if (G.canHover) iKm.focus({ preventScroll: true });
    el.interval.scrollIntoView({ block: 'nearest', behavior: smooth() });
  });
  el.intervalCancel.addEventListener('click', () => {
    intervalOpen = false;
    intervalError('');
    renderNext();
    $('[data-kn-interval-edit]').focus({ preventScroll: true });
  });
  el.interval.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const km = parseWhole(iKm.value, INTERVAL_KM[0], INTERVAL_KM[1]);
    const months = parseWhole(iMonths.value, INTERVAL_MONTHS[0], INTERVAL_MONTHS[1]);
    if (km === null && months === null) { intervalError(T.errInterval, iKm); return; }
    if (Number.isNaN(km)) { intervalError(T.errIntervalKm, iKm); return; }
    if (Number.isNaN(months)) { intervalError(T.errIntervalMonths, iMonths); return; }
    intervalOpen = false;
    commit({ ...book, id: book.id || newId(), reminder: { km, months } }, T.intervalSaved, () => {
      // the form is gone: the focus goes to what it produced — the count, or the next step («Добавить запись о ТО»)
      const target = el.main.hidden ? el.need : el.main;
      (el.main.hidden ? el.need.querySelector('[data-kn-add-to]') : el.head).focus({ preventScroll: true });
      target.scrollIntoView({ block: 'nearest', behavior: smooth() });
    });
  });

  /* ---------- the log ---------- */
  const markEditing = () => $$('.kn-entry', el.list).forEach((li) => li.classList.toggle('is-editing', li.dataset.id === editing));
  const closeEntry = (focus) => {
    editing = null;
    el.entryForm.hidden = true;
    el.add.setAttribute('aria-expanded', 'false');
    el.empty.hidden = book.entries.length > 0;
    markEditing();
    if (focus) el.add.focus({ preventScroll: true });
  };
  const openEntry = (entry, preset) => {
    if (!entry && book.entries.length >= MAX_ENTRIES) { toast(T.errFull, 'err'); return; }
    editing = entry ? entry.id : '';
    const today = localToday();
    el.entryTitle.textContent = entry ? T.entryEdit : T.entryNew;
    ef.date.max = today;
    ef.date.value = entry ? entry.date : today;
    const km = entry ? entry.km : (book.car ? book.car.km : null);
    ef.km.value = km === null ? '' : String(km);
    const works = entry ? entry.works : preset || [];
    ef.works.forEach((c) => { c.checked = works.indexOf(c.value) >= 0; });
    ef.text.value = entry ? entry.text : '';
    ef.note.value = entry ? entry.note : '';
    clearErrs(el.entryForm);
    el.entryForm.hidden = false;
    el.add.setAttribute('aria-expanded', 'true');
    el.empty.hidden = true;
    markEditing();
    el.entryForm.scrollIntoView({ block: 'start', behavior: smooth() });
    // with a mouse the cursor goes to the date; on a touch screen the title takes the focus (a screen reader starts
    // there) and no keyboard jumps up over the form
    (G.canHover ? ef.date : el.entryTitle).focus({ preventScroll: true });
  };
  // flash: the entry lights up once; move: the focus and the view go to it
  const focusEntry = (id, flash, move = true) => {
    const li = el.list.querySelector(`[data-id="${id}"]`);
    if (!li) return;
    if (flash) {
      li.classList.add('is-new');
      setTimeout(() => li.classList.remove('is-new'), 1800);
    }
    if (!move) return;
    li.focus({ preventScroll: true });
    li.scrollIntoView({ block: 'nearest', behavior: smooth() });
  };
  el.add.addEventListener('click', () => { if (editing !== null) closeEntry(true); else openEntry(null); });
  $$('[data-kn-add-to]').forEach((b) => b.addEventListener('click', () => openEntry(null, ['to'])));
  $('[data-kn-entry-cancel]').addEventListener('click', () => closeEntry(true));
  el.entryForm.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const today = localToday();
    const date = ef.date.value;
    const km = parseKm(ef.km.value);
    const works = ef.works.filter((c) => c.checked).map((c) => c.value);
    const text = para(ef.text.value, LEN.text);
    const bad = [];
    if (!parseDate(date)) bad.push([ef.date, T.errDate]);
    else if (date > today) bad.push([ef.date, T.errFuture]);
    if (Number.isNaN(km)) bad.push([ef.km, T.errKm]);
    if (!works.length && !text) bad.push([ef.works[0].closest('fieldset'), T.errWhat]);
    if (showErrs(bad)) return;
    const old = editing ? book.entries.find((e) => e.id === editing) : null;
    const stamp = Date.now();
    const entry = { id: old ? old.id : newId(), date, km, works, text, note: oneLine(ef.note.value, LEN.note),
      created: old ? old.created : stamp, updated: stamp };
    const entries = old ? book.entries.map((e) => (e.id === old.id ? entry : e)) : book.entries.concat(entry);
    let car = book.car;
    let message = old ? T.saved : T.added;
    // a higher mileage in the log is the latest known one: the passport follows it
    if (km !== null && car && (car.km === null || km > car.km)) {
      car = { ...car, km, kmDate: date };
      if (!old) message = T.addedKm;
    }
    const counting = (state) => ['setup', 'need-to'].indexOf(state) < 0;
    const before = forecast(book, today).state;
    closeEntry(false);
    commit({ ...book, id: book.id || newId(), car, entries }, message, () => {
      // the first «ТО» starts the count: that is what the visitor waits for, so the focus and the view go to the card
      const first = !counting(before) && counting(forecast(book, today).state);
      focusEntry(entry.id, true, !first);
      if (first) {
        el.head.focus({ preventScroll: true });
        el.next.scrollIntoView({ block: 'start', behavior: smooth() });
      }
    });
  });

  /* ---------- the one confirm window (delete, delete everything, import) ---------- */
  const dlg = document.getElementById('kn-dialog');
  const ask = (o) => new Promise((resolve) => {
    if (!dlg || typeof dlg.showModal !== 'function') {
      resolve(window.confirm(`${o.title}\n\n${o.text}`) ? o.actions[0].value : null);
      return;
    }
    if (dlg.open) { resolve(null); return; }
    const opener = document.activeElement;
    dlg.querySelector('#kn-dialog-title').textContent = o.title;
    dlg.querySelector('#kn-dialog-text').textContent = o.text;
    const box = dlg.querySelector('[data-kn-dialog-actions]');
    box.textContent = '';
    const cancel = Object.assign(node('button', 'btn btn--ghost', T.cancel), { type: 'button' });
    cancel.setAttribute('data-close', '');   // core.js closes the dialog
    box.appendChild(cancel);
    o.actions.forEach((a) => {
      const b = node('button', `btn ${a.kind === 'ghost' ? 'btn--ghost' : 'btn--primary'}${a.kind === 'danger' ? ' kn-btn-danger' : ''}`, a.label);
      Object.assign(b, { type: 'button' }).dataset.knChoice = a.value;
      box.appendChild(b);
    });
    let result = null;
    const pick = (ev) => {
      const b = ev.target.closest('[data-kn-choice]');
      if (!b) return;
      result = b.dataset.knChoice;
      dlg.close();
    };
    dlg.addEventListener('click', pick);
    dlg.addEventListener('close', () => {
      dlg.removeEventListener('click', pick);
      if (opener && typeof opener.focus === 'function' && document.contains(opener)) opener.focus({ preventScroll: true });
      resolve(result);
    }, { once: true });
    dlg.showModal();
    cancel.focus();
  });

  el.list.addEventListener('click', async (ev) => {
    const b = ev.target.closest('[data-act]');
    if (!b) return;
    const li = b.closest('.kn-entry');
    const e = li ? book.entries.find((x) => x.id === li.dataset.id) : null;
    if (!e) return;
    if (b.dataset.act === 'edit') { openEntry(e); return; }
    const date = fmtDate(e.date);
    if (await ask({ title: T.delTitle, text: t('delText', { date }), actions: [{ value: 'yes', label: T.delOk, kind: 'danger' }] }) !== 'yes') return;
    const sorted = book.entries.slice().sort(newestFirst);
    const i = sorted.findIndex((x) => x.id === e.id);
    const next = sorted[i + 1] || sorted[i - 1] || null;
    if (editing === e.id) closeEntry(false);
    commit({ ...book, entries: book.entries.filter((x) => x.id !== e.id) }, T.deleted, () => {
      if (next) focusEntry(next.id, false);
      else if (!el.desk.hidden) el.add.focus({ preventScroll: true });
    });
  });

  /* ---------- the next service: calendar, «Записаться» ---------- */
  const download = (text, type, name) => {   // a file made here: nothing is fetched or sent
    if (!window.Blob || !window.URL || !URL.createObjectURL) return false;
    const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(new Blob([text], { type })), download: name });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 60000);   // a phone reads the file after its own dialog
    return true;
  };
  el.ics.addEventListener('click', () => {
    const today = localToday();
    const f = forecast(book, today);
    if (f.state === 'over' || !f.date || daysBetween(today, f.date) <= 0) { renderNext(); return; }
    const car = book.car ? carTitle(book.car) : '';
    const text = buildIcs({
      // one reminder per service cycle: a new export after the same «ТО» replaces the event in the calendar
      uid: `knizhka-${book.id || 'book'}-${f.base.id}@garage.team`,
      stamp: new Date(),
      date: f.date,
      summary: car ? t('icsSummary', { car }) : T.icsSummaryNoCar,
      description: t('icsDesc', { rule: ruleText(book.reminder), last: lastLine(f.base), phone: conf.phone }),
      url: pageUrl(),
      alarm: car ? t('icsAlarm', { car }) : T.icsSummaryNoCar,
    });
    if (download(text, 'text/calendar;charset=utf-8', T.icsFile)) toast(t('icsDone', { file: T.icsFile }));
    else toast(T.noDownload, 'err');
  });
  const openCall = (works, withLast) => {
    const c = book.car;
    const parts = [works.length ? t('bookWorks', { works: works.map((k) => PHRASE[k] || k).join(', ') }) : T.bookNone];
    if (c) parts.push(t('bookCar', { car: carLine(c, true) }));
    const f = withLast ? forecast(book, localToday()) : null;
    if (f && f.base) parts.push(t('bookLast', { last: lastLine(f.base) }));
    if (G.openModal) G.openModal('call', { message: parts.join(' '), car: c ? carLine(c, false) : '', vin_code: c ? c.vin : '' });
  };
  $('[data-kn-book]').addEventListener('click', () => openCall(bookWorks.filter((c) => c.checked).map((c) => c.value), false));
  $('[data-kn-book-to]').addEventListener('click', () => openCall(['to'], true));

  /* ---------- the copy: save, load (merge or replace), delete everything, print ---------- */
  $('[data-kn-export]').addEventListener('click', () => {
    const name = t('jsonFile', { date: localToday() });
    if (download(JSON.stringify(serial(book, Date.now()), null, 2), 'application/json;charset=utf-8', name)) toast(t('jsonDone', { file: name }));
    else toast(T.noDownload, 'err');
  });
  const picker = $('[data-kn-file]');   // a hidden file field; the two «Загрузить из файла» buttons open it
  $$('[data-kn-import]').forEach((b) => b.addEventListener('click', () => { picker.value = ''; picker.click(); }));
  const readText = (file) => new Promise((resolve, reject) => {
    const r = new FileReader();
    Object.assign(r, { onload: () => resolve(String(r.result)), onerror: () => reject(r.error) });
    r.readAsText(file);
  });
  const settle = (next, message) => {
    carOpen = false;
    intervalOpen = false;
    if (editing !== null) closeEntry(false);
    commit(next, message, () => { if (!el.desk.hidden) el.plate.focus({ preventScroll: true }); root.scrollIntoView({ block: 'start', behavior: smooth() }); });
  };
  picker.addEventListener('change', async () => {
    const file = picker.files && picker.files[0];
    if (!file) return;
    if (file.size > MAX_FILE) { toast(T.importLarge, 'err'); return; }
    let raw = '';
    try { raw = await readText(file); } catch (_) { toast(T.importRead, 'err'); return; }
    let obj = null;
    try { obj = JSON.parse(raw); } catch (_) { toast(T.importBroken, 'err'); return; }
    const s = sanitizeBook(obj, KEYS);
    if (!s.ok) { toast(T[`import_${s.error}`] || T.import_format, 'err'); return; }
    const skipped = s.dropped ? ` ${t('importSkipped', { n: s.dropped })}` : '';
    const loaded = t('importDone', { n: count(s.book.entries.length, 'pEntries') }) + skipped;
    if (!hasData(book)) { settle(s.book, loaded); return; }
    const what = `${s.book.car ? carTitle(s.book.car) : T.importNoCar}, ${count(s.book.entries.length, 'pEntries')}`;
    const choice = await ask({ title: T.importTitle, text: t('importAsk', { what }),
      actions: [{ value: 'replace', label: T.importReplace, kind: 'ghost' }, { value: 'merge', label: T.importMerge, kind: 'primary' }] });
    if (choice === 'replace') settle(s.book, loaded);
    else if (choice === 'merge') {
      const m = mergeBooks(book, s.book);
      settle(m.book, (m.added ? t('importMerged', { n: count(m.added, 'pEntries') }) : T.importNothing) + skipped);
    }
  });
  $('[data-kn-wipe]').addEventListener('click', async () => {
    if (await ask({ title: T.wipeTitle, text: T.wipeText, actions: [{ value: 'wipe', label: T.wipeOk, kind: 'danger' }] }) !== 'wipe') return;
    const res = store.clear();
    brokenRaw = null;
    book = emptyBook();
    carOpen = false;
    intervalOpen = false;
    closeEntry(false);
    closeOdo(false);
    bookWorks.forEach((c) => { c.checked = false; });
    iKm.value = '';
    iMonths.value = '';
    problem = res === 'ok' ? '' : 'off';
    render();
    syncFill(null);
    toast(T.wipeDone);
    root.scrollIntoView({ block: 'start', behavior: smooth() });
    $('[data-kn-go]').focus({ preventScroll: true });
  });

  // the print version: a plain sheet with the passport, the interval and the log in order of dates (knizhka.css @media print)
  const buildPrint = () => {
    const p = el.sheet;
    p.textContent = '';
    const c = book.car;
    const today = localToday();
    p.appendChild(node('p', 'kn-print__kicker', `${T.printTitle}`));
    p.appendChild(node('h2', 'kn-print__car', c ? carTitle(c) : T.noCar));
    const facts = [];
    if (c && c.year) facts.push(`${c.year}${NB}г.`);
    if (c && c.engine) facts.push(engineText(c.engine));
    if (c && c.vin) facts.push(`VIN ${c.vin}`);
    if (c && c.km !== null) facts.push(`${fmtNum(c.km)}${NB}км (${t('kmAt', { date: fmtDate(c.kmDate) || '—' })})`);
    if (facts.length) p.appendChild(node('p', 'kn-print__facts', facts.join(' · ')));
    const f = forecast(book, today);
    if (book.reminder.km || book.reminder.months) p.appendChild(node('p', 'kn-print__line', t('printRule', { rule: ruleText(book.reminder) })));
    if (['setup', 'need-to'].indexOf(f.state) < 0) {
      // «Следующее ТО: Примерно 5 октября 2026, осталось 500 км / 224 дня» — the card's line and what is left
      const left = [f.km && f.km.left > 0 ? `${fmtNum(f.km.left)}${NB}км` : '', f.time && f.time.left > 0 ? count(f.time.left, 'pDays') : '']
        .filter(Boolean).join(' / ');
      const text = [headline(f).head, f.state !== 'over' && left ? t('printLeft', { what: left }) : ''].filter(Boolean).join(', ');
      p.appendChild(node('p', 'kn-print__line', t('printNext', { text })));
    }
    p.appendChild(node('h3', 'kn-print__h', T.printLog));
    const rows = book.entries.slice().sort(newestFirst).reverse();
    if (!rows.length) p.appendChild(node('p', 'kn-print__line', T.printEmpty));
    else {
      const table = node('table', 'kn-print__table');
      const head = node('tr');
      T.printCols.forEach((h) => head.appendChild(node('th', '', h)));
      const thead = node('thead');
      thead.appendChild(head);
      const tbody = node('tbody');
      rows.forEach((e) => {
        const tr = node('tr');
        const what = [e.works.map((k) => LABEL[k] || k).join(', '), e.text].filter(Boolean).join('. ');
        [fmtDate(e.date), e.km === null ? '—' : fmtNum(e.km), what, e.note, ''].forEach((v) => tr.appendChild(node('td', '', v)));
        tbody.appendChild(tr);
      });
      table.append(thead, tbody);
      p.appendChild(table);
    }
    p.appendChild(node('p', 'kn-print__foot', t('printFoot', { date: fmtDate(today), url: pageUrl().replace(/^https?:\/\//, ''), phone: conf.phone })));
  };
  $('[data-kn-print]').addEventListener('click', () => { buildPrint(); window.print(); });
  addEventListener('beforeprint', buildPrint);

  // Escape in an open form works as its «Отмена» (the confirm window closes itself)
  root.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Escape' || !ev.target.closest) return;
    const form = ev.target.closest('form');
    const cancel = form ? form.querySelector('[data-kn-car-cancel], [data-kn-entry-cancel], [data-kn-interval-cancel], [data-kn-odo-cancel]') : null;
    if (cancel && !cancel.hidden) { ev.preventDefault(); cancel.click(); }
  });

  /* ---------- start ---------- */
  const first = load();
  book = first.book;
  problem = first.problem || (store.probe() ? '' : 'off');
  // another tab of this site changed the book
  addEventListener('storage', (e) => {
    if (e.key !== KEY && e.key !== null) return;
    const next = load();
    book = next.book;
    problem = next.problem;
    if (editing && !book.entries.some((x) => x.id === editing)) closeEntry(false);
    render();
    syncFill(book.car);
  });
  root.hidden = false;
  render();
})();
