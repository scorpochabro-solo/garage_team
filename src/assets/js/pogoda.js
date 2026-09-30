/* ============================================================
   «Пора переобуваться?» (#pogoda, build/pogoda.py): the Open-Meteo forecast for Nizhny Novgorod -> the verdict
   «пора ли менять резину» and a chart of the days.
   What keeps it cheap and safe:
     1. nothing runs until the section is ~600px away (IntersectionObserver); then one request, or none: a forecast
        younger than two hours, of the same Moscow day, comes from localStorage (wrapped in try/catch);
     2. the answer is checked strictly — dates in a row, units, lengths, number ranges — before anything is drawn;
     3. the bars grow in once by CSS transitions (transform and opacity only); no requestAnimationFrame loop;
     4. any failure (offline, timeout, HTTP, a broken answer) leaves the rule of thumb and the booking button, with
        «Попробовать ещё раз»; the reason goes to data-pg-error for debugging, nothing to the console.
   The rule, the words and the address come from #pogoda-data. The pure part (parse, verdict, describe…) is also
   G.pogoda: tests/pogoda_verdict.cjs runs it in node on test forecasts.
   ============================================================ */
(() => {
  'use strict';
  const G = (window.G = window.G || {});
  const NB = '\u00a0';
  const MINUS = '\u2212';
  const DAY_MS = 86400000;
  const MSK_OFFSET = 180;       // minutes: Moscow keeps UTC+3 all year — the fallback for a browser without time zones
  const MIN_BAR = 0.04;         // share of the plot height: the shortest bar drawn
  const ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

  /* ---------- dates: «YYYY-MM-DD» strings, arithmetic in UTC, so the machine's own time zone plays no part ---------- */
  const utc = (iso) => {
    const m = typeof iso === 'string' ? ISO.exec(iso) : null;
    if (!m) return NaN;
    const t = Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return new Date(t).toISOString().slice(0, 10) === iso ? t : NaN;   // 2026-02-30 rolls over to March: not a date
  };
  const addDays = (iso, n) => new Date(utc(iso) + n * DAY_MS).toISOString().slice(0, 10);
  const weekday = (iso) => (new Date(utc(iso)).getUTCDay() + 6) % 7;   // Monday = 0
  const monthOf = (iso) => Number(iso.slice(5, 7));

  // the wall clock of a moment in the forecast's time zone: { date: 'YYYY-MM-DD', time: 'H:MM' }
  const clocks = {};
  const zoned = (moment, tz) => {
    try {
      clocks[tz] = clocks[tz] || new Intl.DateTimeFormat('en-US', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: 'numeric', minute: '2-digit', hour12: false });
      const p = {};
      clocks[tz].formatToParts(moment).forEach((x) => { p[x.type] = x.value; });
      const date = `${p.year}-${p.month}-${p.day}`;
      const hour = Number(p.hour) % 24;   // some engines say «24» at midnight
      const minute = String(p.minute || '').padStart(2, '0');
      if (Number.isFinite(utc(date)) && Number.isFinite(hour) && /^\d{2}$/.test(minute)) return { date, time: `${hour}:${minute}` };
    } catch (_) { /* no time zone data: UTC+3 below */ }
    const t = new Date(moment.getTime() + MSK_OFFSET * 60000);
    return { date: t.toISOString().slice(0, 10), time: `${t.getUTCHours()}:${String(t.getUTCMinutes()).padStart(2, '0')}` };
  };

  /* ---------- words ---------- */
  const fill = (text, map) => String(text).replace(/\{(\w+)\}/g, (all, k) => (Object.prototype.hasOwnProperty.call(map, k) ? String(map[k]) : all));
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  const plural = (n, forms) => {
    const a = Math.abs(n) % 100;
    const b = a % 10;
    if (a > 10 && a < 20) return forms[2];
    if (b === 1) return forms[0];
    return b >= 2 && b <= 4 ? forms[1] : forms[2];
  };
  const count = (n, cfg) => `${n}${NB}${plural(n, cfg.dayForms)}`;                                // «4 дня»
  const deg = (v) => { const n = Math.round(v); return n > 0 ? `+${n}` : n < 0 ? `${MINUS}${-n}` : '0'; };   // −0.4 -> «0»
  const temp = (v) => `${deg(v)}${NB}°C`;
  const dateText = (iso, cfg) => `${Number(iso.slice(8, 10))}${NB}${cfg.months[monthOf(iso) - 1]}`;   // «2 октября»
  const dateWd = (iso, cfg) => `${dateText(iso, cfg)}, ${cfg.weekdays[weekday(iso)]}`;             // «2 октября, пт»

  /* ---------- parse: the Open-Meteo answer -> [{ date, min, max, mean, precip, snow }], or an Error with the reason ---------- */
  const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
  const parse = (json, cfg) => {
    const fail = (why) => { throw new Error(why); };
    if (!json || typeof json !== 'object' || Array.isArray(json)) fail('answer: not an object');
    if (json.error) fail('answer: error');
    if (json.timezone !== cfg.tz) fail('answer: time zone');
    if (!isNum(json.latitude) || !isNum(json.longitude) || Math.abs(json.latitude - cfg.at[0]) > 0.5 || Math.abs(json.longitude - cfg.at[1]) > 0.5) fail('answer: place');
    const daily = json.daily;
    const units = json.daily_units;
    if (!daily || typeof daily !== 'object' || !units || typeof units !== 'object') fail('answer: no daily data');
    const time = daily.time;
    const least = cfg.past + cfg.minDays;
    if (!Array.isArray(time) || time.length < least || time.length > cfg.past + cfg.forecast) fail('dates: count');
    if (units.time !== 'iso8601') fail('dates: format');
    time.forEach((d, i) => {
      if (!Number.isFinite(utc(d))) fail(`dates: ${i}`);
      if (i && d !== addDays(time[i - 1], 1)) fail('dates: not in a row');
    });
    const col = {};
    Object.keys(cfg.vars).forEach((k) => {
      const name = cfg.vars[k];
      if (units[name] !== cfg.units[name]) fail(`${name}: unit`);
      const values = daily[name];
      if (!Array.isArray(values) || values.length !== time.length) fail(`${name}: length`);
      values.forEach((v) => { if (v !== null && !isNum(v)) fail(`${name}: value`); });
      col[k] = values;
    });
    // a day without a temperature ends the series: the last forecast days may come empty, a gap inside may not
    const known = (i) => col.min[i] !== null && col.max[i] !== null && col.mean[i] !== null;
    let n = time.length;
    while (n > 0 && !known(n - 1)) n -= 1;
    if (n < least) fail('days: too few with data');
    const [tLo, tHi] = cfg.limits.t;
    const inside = (v, [lo, hi]) => v === null || (v >= lo && v <= hi);
    const days = [];
    for (let i = 0; i < n; i += 1) {
      if (!known(i)) fail(`day ${i}: no temperature`);
      const d = { date: time[i], min: col.min[i], max: col.max[i], mean: col.mean[i], precip: col.precip[i], snow: col.snow[i] };
      if ([d.min, d.max, d.mean].some((t) => t < tLo || t > tHi)) fail(`day ${i}: temperature out of range`);
      if (d.min > d.max || d.mean < d.min - 0.1 || d.mean > d.max + 0.1) fail(`day ${i}: min, mean, max`);
      if (!inside(d.precip, cfg.limits.precip) || !inside(d.snow, cfg.limits.snow)) fail(`day ${i}: precipitation`);
      days.push(d);
    }
    return days;
  };

  /* ---------- verdict: the rule of thumb over the days; t = the index of today ----------
     { season, state: now | soon | early | summer | winter, from: the day it changes (index) or -1,
       cause: cold | frost | warm | short, run: [first, last] cold spell or null, frost: first frost day or -1,
       rebound: the first day of the warm end of the forecast (autumn) or -1 } */
  const verdict = (days, t, cfg) => {
    const n = days.length;
    if (!(t >= 0 && t < n)) throw new Error('today is not in the forecast');
    const season = cfg.seasons[String(monthOf(days[t].date))];
    const cold = (d) => d.mean <= cfg.threshold;
    const frosty = (d) => d.min <= cfg.frost;
    const good = (d) => !cold(d) && !frosty(d);
    const v = { season, state: season, from: -1, cause: '', run: null, frost: -1, rebound: -1 };
    if (season === 'autumn') {
      // the first spell of STREAK or more cold days that reaches today or later (it may have begun before today)
      for (let i = 0; i < n && !v.run;) {
        if (!cold(days[i])) { i += 1; continue; }
        let j = i;
        while (j + 1 < n && cold(days[j + 1])) j += 1;
        if (j >= t && j - i + 1 >= cfg.streak) v.run = [i, j];
        i = j + 1;
      }
      for (let i = t; i < n && v.frost < 0; i += 1) if (frosty(days[i])) v.frost = i;
      const coldAt = v.run ? Math.max(v.run[0], t) : -1;
      const at = [coldAt, v.frost].filter((i) => i >= 0);
      if (!at.length) {
        v.state = 'early';
        v.cause = days.slice(t).some(cold) ? 'short' : 'warm';
        return v;
      }
      v.from = Math.min(...at);
      v.cause = v.from === coldAt ? 'cold' : 'frost';
      v.state = v.from - t <= cfg.nowDays ? 'now' : 'soon';
      // the forecast ends warm again: its last days, STREAK or more, above the threshold and frost-free
      let r = n;
      while (r > v.from + 1 && good(days[r - 1])) r -= 1;
      if (n - r >= cfg.streak) v.rebound = r;
      return v;
    }
    if (season === 'spring') {
      // summer tyres from the day after the last cold or frosty day of the forecast, if STREAK good days follow it
      let last = -1;
      for (let i = t; i < n; i += 1) if (!good(days[i])) last = i;
      const from = Math.max(t, last + 1);
      if (n - from >= cfg.streak) {
        v.from = from;
        v.state = from - t <= cfg.nowDays ? 'now' : 'soon';
        v.cause = 'warm';
      } else {
        v.state = 'early';
        v.cause = days.slice(t).some(frosty) ? 'frost' : 'cold';
      }
    }
    return v;
  };

  /* ---------- describe: the verdict in words — title, kicker, countdown chip, why, note, live text, message ---------- */
  const describe = (v, days, t, cfg) => {
    const T = cfg.texts;
    const n = days.length;
    const date = (i) => dateText(days[i].date, cfg);
    const fromWord = (i) => (i === t ? T['from-today'] : i === t + 1 ? T['from-tomorrow'] : fill(T['from-date'], { date: date(i) }));
    const onWord = (i) => (i === t ? T['on-today'] : i === t + 1 ? T['on-tomorrow'] : date(i));
    const dayWord = (i) => (i === t ? T['day-today'] : i === t + 1 ? T['day-tomorrow'] : date(i));
    const lowest = (key, from) => Math.min(...days.slice(from).map((d) => d[key]));
    const highest = (key, from) => Math.max(...days.slice(from).map((d) => d[key]));
    const neutral = v.season !== 'autumn' && v.season !== 'spring';
    const winterish = (v.season === 'autumn' && v.state !== 'early') || (v.season === 'spring' && v.state === 'early') || v.season === 'winter';
    const out = {
      tone: winterish ? 'winter' : 'summer',
      title: T[neutral ? v.season : `${v.season}-${v.state}`],
      kick: '', chip: '', why: '', note: '',
      message: cfg.messages[v.season === 'autumn' || v.season === 'spring' ? v.season : 'any'],
    };
    if (v.state === 'now') out.kick = v.from === t ? T['kick-today'] : T['kick-tomorrow'];
    if (v.state === 'soon') {
      out.kick = fill(T[`kick-${v.season}-soon`], { date: dateWd(days[v.from].date, cfg) });
      out.chip = fill(T['in-days'], { n: count(v.from - t, cfg) });
    }
    if (v.state === 'early') out.kick = T[`kick-${v.season}-early`];

    const why = [];
    const coldText = () => {
      const [a, b] = v.run;
      if (a < t) return fill(T['why-cold-since'], { n: count(t - a + 1, cfg) });
      const span = b === n - 1 ? T['till-end'] : fill(T['in-a-row'], { n: count(b - a + 1, cfg) });
      return fill(T['why-cold-from'], { from: fromWord(a), span });
    };
    const frostText = (first) => fill(T[first ? 'why-frost' : 'why-frost-also'], { on: onWord(v.frost), day: dayWord(v.frost), min: temp(days[v.frost].min) });
    if (neutral) why.push(T[`why-${v.season}`]);
    else if (v.season === 'autumn' && v.state === 'early') why.push(v.cause === 'warm' ? fill(T['why-warm'], { n: count(n - t, cfg) }) : T['why-short']);
    else if (v.season === 'autumn') {
      if (v.cause === 'cold') { why.push(coldText()); if (v.frost >= 0) why.push(frostText(false)); }
      else { why.push(frostText(true)); if (v.run) why.push(coldText()); }
      if (v.rebound >= 0) out.note = fill(T['note-rebound'], { date: date(v.rebound), max: temp(highest('max', v.rebound)) });
    } else if (v.state === 'early') {
      why.push(v.cause === 'frost' ? fill(T['why-spring-frost'], { min: temp(lowest('min', t)) }) : fill(T['why-spring-cold'], { low: temp(lowest('mean', t)) }));
    } else {
      why.push(v.from === t ? fill(T['why-warm'], { n: count(n - t, cfg) }) : fill(T['why-warm-from'], { from: fromWord(v.from) }));
    }
    out.why = why.join(' ');
    out.live = `${out.title}${out.kick ? ` ${out.kick}` : ''}${out.chip ? `, ${out.chip}` : ''}. ${out.why}`;
    return out;
  };

  // the chart's scale: whole degrees with a degree of air, always holding the 0 °C line and the threshold
  const scale = (days, cfg) => {
    const lo = Math.floor(Math.min(cfg.frost, ...days.map((d) => d.min)) - 1);
    const hi = Math.ceil(Math.max(cfg.threshold, ...days.map((d) => d.max)) + 1);
    return { lo, hi, at: (x) => Math.round(((x - lo) / (hi - lo)) * 10000) / 10000 };
  };

  G.pogoda = { parse, verdict, describe, scale, zoned, temp, deg, dateText, dateWd, plural, addDays, fill };

  /* ============================================================ the section ============================================================ */
  const root = document.querySelector('[data-pogoda]');
  if (!root) return;
  let cfg = null;
  try { cfg = JSON.parse(document.getElementById('pogoda-data').textContent); } catch (_) { cfg = null; }
  if (!cfg || typeof cfg !== 'object' || !cfg.texts || !cfg.url) { root.dataset.pgError = 'config'; return; }   // the rule of thumb stays
  const T = cfg.texts;
  const $ = (s) => root.querySelector(s);
  const el = {
    status: $('[data-pg-status]'), rule: $('[data-pg-rule]'), face: $('[data-pg-face]'), verdict: $('[data-pg-verdict]'), title: $('[data-pg-title]'),
    kick: $('[data-pg-kick]'), chip: $('[data-pg-chip]'), chipText: $('[data-pg-chip-text]'), why: $('[data-pg-why]'),
    note: $('[data-pg-note]'), book: $('[data-pg-book]'), plot: $('[data-pg-plot]'), list: $('[data-pg-days]'),
    msg: $('[data-pg-msg]'), msgText: $('[data-pg-msg-text]'), retry: $('[data-pg-retry]'), updated: $('[data-pg-updated]'),
    live: $('[data-pg-live]'), snow: $('.pogoda-key--snow svg'),
  };
  if (Object.keys(el).some((k) => !el[k])) { root.dataset.pgError = 'markup'; return; }

  const reduced = () => !!G.reducedMotion;
  let shownAt = 0;              // when the forecast on screen was fetched (ms), 0 = nothing shown
  let shownDay = '';            // the Moscow day it was shown for
  let busy = false;
  let said = '';
  let asked = false;            // the visitor started this load («Попробовать ещё раз», the network came back)
  let refocus = false;          // «Попробовать ещё раз» was pressed: the keyboard focus follows the result

  const make = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  // the live region speaks when the visitor asked for the result or is looking at the section — not when the
  // forecast quietly arrives while the section is still 600px away
  const inView = () => { const r = root.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; };
  const announce = (text) => {
    if (!text || text === said || !(asked || inView())) return;
    said = text;
    el.live.textContent = text;
  };
  // after «Попробовать ещё раз» the focus follows the result — unless the visitor has moved it somewhere else meanwhile
  const follow = (target) => {
    if (!refocus) return;
    refocus = false;
    if ([el.retry, el.msgText, document.body, null].includes(document.activeElement)) target.focus({ preventScroll: true });
  };
  // the status line breaks only between its parts («Нижний Новгород · прогноз на 10 дней»), never inside one
  const setStatus = (text) => {
    el.status.textContent = '';
    text.split(' · ').forEach((part, i) => {
      if (i) el.status.append(' · ');
      el.status.append(make('span', 'pogoda-card__part', part));
    });
  };
  const seasonNow = () => cfg.seasons[String(monthOf(zoned(new Date(), cfg.tz).date))];
  const setMessage = (season) => { el.book.dataset.preset = JSON.stringify({ message: cfg.messages[season === 'autumn' || season === 'spring' ? season : 'any'] }); };

  /* ---------- storage ---------- */
  const readCache = () => {
    try {
      const c = JSON.parse(localStorage.getItem(cfg.cacheKey) || 'null');
      return c && typeof c === 'object' && isNum(c.t) && typeof c.day === 'string' && c.json && typeof c.json === 'object' ? c : null;
    } catch (_) { return null; }
  };
  const writeCache = (entry) => {
    try { localStorage.setItem(cfg.cacheKey, JSON.stringify(entry)); } catch (_) { /* full or blocked: the next visit asks again */ }
  };

  /* ---------- the request: a timeout, no cookies, no referrer ---------- */
  const request = async () => {
    const ctl = typeof AbortController === 'function' ? new AbortController() : null;
    let timer = 0;
    const late = new Promise((_, reject) => { timer = setTimeout(() => { if (ctl) ctl.abort(); reject(new Error('timeout')); }, cfg.timeout); });
    try {
      const res = await Promise.race([fetch(cfg.url, { signal: ctl ? ctl.signal : undefined, credentials: 'omit', referrerPolicy: 'no-referrer' }), late]);
      if (!res.ok) throw new Error(`http ${res.status}`);
      const json = await Promise.race([res.json(), late]);
      // only what the section reads is kept (and stored)
      return json && typeof json === 'object'
        ? { timezone: json.timezone, latitude: json.latitude, longitude: json.longitude, daily_units: json.daily_units, daily: json.daily, error: json.error }
        : json;
    } catch (e) {
      if (e && e.name === 'AbortError') throw new Error('timeout');
      if (e && e.name === 'SyntaxError') throw new Error('answer: not JSON');   // WebKit: a DOMException of that name
      throw e instanceof Error && /^(timeout|http |answer)/.test(e.message) ? e : new Error('network');
    } finally {
      clearTimeout(timer);
    }
  };

  /* ---------- drawing ---------- */
  const label = (value) => {
    const s = make('span');
    s.append(deg(value), make('span', 'pogoda-day__deg', '°'));
    return s;
  };

  const drawDays = (days, t, v) => {
    const first = Math.max(0, t - cfg.past);
    const list = days.slice(first, t + cfg.forecast);
    const sc = scale(list, cfg);
    el.plot.style.setProperty('--p0', String(sc.at(cfg.frost)));
    el.plot.style.setProperty('--pb', String(sc.at(cfg.band)));
    el.plot.style.setProperty('--pt', String(sc.at(cfg.threshold)));
    const run = v.season === 'autumn' && v.run ? [Math.max(v.run[0], first), v.run[1]] : (v.season === 'spring' && v.from >= 0 ? [v.from, days.length - 1] : null);
    const frag = document.createDocumentFragment();
    list.forEach((d, k) => {
      const i = first + k;
      const snow = d.snow !== null && d.snow >= cfg.snowMin;
      const frost = d.min <= cfg.frost;
      const li = make('li', ['pogoda-day', i < t ? 'is-past' : '', i === t ? 'is-today' : '', d.mean <= cfg.threshold ? 'is-cold' : '',
        frost ? 'is-frost' : '', snow ? 'is-snow' : '', run && i >= run[0] && i <= run[1] ? 'is-run' : '', i === v.from ? 'is-from' : ''].filter(Boolean).join(' '));
      const lo = sc.at(d.min);
      const hi = sc.at(d.max);
      const mid = (lo + hi) / 2;
      const half = Math.max(hi - lo, MIN_BAR) / 2;   // a day with min ≈ max still shows a short capsule
      li.style.setProperty('--lo', String(lo));
      li.style.setProperty('--hi', String(hi));
      li.style.setProperty('--blo', String(Math.round((mid - half) * 10000) / 10000));
      li.style.setProperty('--bhi', String(Math.round((mid + half) * 10000) / 10000));
      li.style.setProperty('--mean', String(sc.at(d.mean)));
      li.style.setProperty('--i', String(k));
      // the plot part of the day: bar, mean, labels; the date row under it
      const box = make('span', 'pogoda-day__plot');
      const max = make('span', 'pogoda-day__max');
      max.append(label(d.max));
      const min = make('span', 'pogoda-day__min');
      min.append(label(d.min));
      box.append(make('span', 'pogoda-day__bar'), make('span', 'pogoda-day__dot'), max, min);
      if (snow) { const flake = el.snow.cloneNode(true); flake.setAttribute('class', 'ic pogoda-snow pogoda-day__snow'); box.append(flake); }
      const when = make('span', 'pogoda-day__date');
      when.append(make('span', 'pogoda-day__wd', cfg.weekdays[weekday(d.date)]));
      if (i === t) when.append(make('span', 'pogoda-day__now', T.today));   // in the weekday's place where there is room
      when.append(make('span', 'pogoda-day__dn', String(Number(d.date.slice(8, 10)))));
      box.setAttribute('aria-hidden', 'true');
      when.setAttribute('aria-hidden', 'true');
      li.append(box, when);
      if (i < t) li.setAttribute('aria-hidden', 'true');   // the past days are the trend for the eye; the words say it
      else {
        let marks = frost ? T['sr-frost'] : '';
        if (snow) marks += T['sr-snow'];
        else if (d.precip !== null && d.precip >= cfg.precipMin) marks += fill(T['sr-precip'], { mm: Math.round(d.precip) });
        const day = i === t ? fill(T['sr-today'], { date: dateText(d.date, cfg) }) : `${cap(cfg.weekdaysFull[weekday(d.date)])}, ${dateText(d.date, cfg)}`;
        li.append(make('span', 'sr-only', fill(T['sr-day'], { day, min: temp(d.min), max: temp(d.max), mean: temp(d.mean), marks })));
      }
      frag.append(li);
    });
    el.plot.classList.remove('is-drawn');
    el.list.textContent = '';
    el.list.append(frag);
    el.list.hidden = false;
    // the bars grow in from the next frame (CSS transitions); with reduced motion they are simply there
    if (reduced()) el.plot.classList.add('is-drawn');
    else requestAnimationFrame(() => requestAnimationFrame(() => el.plot.classList.add('is-drawn')));
  };

  /* ---------- states ---------- */
  const setLoading = () => {
    root.dataset.state = 'loading';
    setStatus(T['status-loading']);
    el.msgText.textContent = T['msg-loading'];
    el.msg.hidden = false;
    // the retry button goes away while loading: the keyboard focus waits on the message instead of falling to the page
    if (document.activeElement === el.retry) el.msgText.focus({ preventScroll: true });
    el.retry.hidden = true;
  };

  const setError = (reason) => {
    root.dataset.state = 'error';
    root.dataset.tone = 'neutral';
    delete root.dataset.verdict;
    shownAt = 0;
    setStatus(T['status-error']);
    el.rule.hidden = false;
    el.face.hidden = true;
    el.list.hidden = true;
    el.list.textContent = '';
    el.updated.textContent = '';
    el.msgText.textContent = reason === 'offline' ? T['msg-offline'] : T['msg-error'];
    el.msg.hidden = false;
    el.retry.hidden = false;
    setMessage(seasonNow());
    announce(`${T['status-error']}.`);
    follow(el.retry);
  };

  // entry: { t: fetched at (ms), day: the Moscow day of fetching, json }; stale: an older forecast after a failure
  const show = (entry, stale) => {
    let days;
    try { days = parse(entry.json, cfg); } catch (e) { root.dataset.pgError = e.message; return false; }
    const today = zoned(new Date(), cfg.tz).date;
    // a fresh answer: Open-Meteo's own «today» follows the past days; an old one: find today in it
    const t = stale ? days.findIndex((d) => d.date === today) : cfg.past;
    if (t < 0 || days.length - t < cfg.minDays) { root.dataset.pgError = 'days: today is missing'; return false; }
    const v = verdict(days, t, cfg);
    const words = describe(v, days, t, cfg);
    root.dataset.state = stale ? 'stale' : 'ready';
    root.dataset.tone = words.tone;
    root.dataset.verdict = `${v.season}-${v.state}`;
    const fetched = zoned(new Date(entry.t), cfg.tz);
    setStatus(stale
      ? fill(T['status-stale'], { when: `${dateText(fetched.date, cfg)}, ${fetched.time}` })
      : fill(T['status-ready'], { n: count(days.length - t, cfg) }));
    el.rule.hidden = true;
    el.face.hidden = false;
    el.title.textContent = words.title;
    el.kick.textContent = words.kick;
    el.kick.hidden = !words.kick;
    el.chipText.textContent = words.chip;
    el.chip.hidden = !words.chip;
    el.why.textContent = words.why;
    el.note.textContent = words.note;
    el.note.hidden = !words.note;
    el.book.dataset.preset = JSON.stringify({ message: words.message });
    el.msg.hidden = true;
    el.retry.hidden = true;
    el.updated.textContent = stale
      ? fill(T['updated-stale'], { when: `${dateText(fetched.date, cfg)}, ${fetched.time}` })
      : fill(T.updated, { time: fetched.time });
    drawDays(days, t, v);
    shownAt = entry.t;
    shownDay = today;
    announce(words.live);
    follow(el.verdict);
    return true;
  };

  // quiet: a refresh of what is already on screen — no «loading», and a failure keeps the old forecast
  const load = async ({ force = false, quiet = false } = {}) => {
    if (busy) return;
    busy = true;
    const now = Date.now();
    const day = zoned(new Date(now), cfg.tz).date;
    const cached = readCache();
    const age = cached ? now - cached.t : Infinity;
    try {
      if (!force && cached && cached.day === day && age >= 0 && age < cfg.cacheMinutes * 60000 && show(cached, false)) return;
      if (typeof fetch !== 'function') throw new Error('no fetch');
      if (navigator.onLine === false) throw new Error('offline');
      if (!quiet) setLoading();
      const json = await request();
      parse(json, cfg);   // a broken answer is neither shown nor stored
      const entry = { t: Date.now(), day, json };
      if (!show(entry, false)) throw new Error(root.dataset.pgError || 'draw');
      writeCache(entry);
      delete root.dataset.pgError;
    } catch (e) {
      const reason = e && e.message ? e.message : 'network';
      root.dataset.pgError = reason;
      if (quiet && shownAt) return;   // keep the forecast on screen, try again at the next look
      // an earlier forecast (up to STALE_HOURS old) is better than none: shown with its time
      if (cached && age >= 0 && age < cfg.staleHours * 3600000 && show(cached, true)) return;
      setError(reason);
    } finally {
      busy = false;
      asked = false;
    }
  };

  el.retry.addEventListener('click', () => {
    asked = true;
    refocus = document.activeElement === el.retry || document.activeElement === document.body;   // Safari: a clicked button takes no focus
    load({ force: true });
  });
  addEventListener('online', () => { if (root.dataset.state === 'error') { asked = true; load({ force: true }); } });
  // a tab left open: at the next look a forecast older than the cache time, or of yesterday, is refreshed quietly
  const revisit = () => {
    if (document.visibilityState === 'hidden' || !shownAt) return;
    if (Date.now() - shownAt > cfg.cacheMinutes * 60000 || zoned(new Date(), cfg.tz).date !== shownDay) load({ quiet: true });
  };
  document.addEventListener('visibilitychange', revisit);
  addEventListener('pageshow', (e) => { if (e.persisted) revisit(); });

  const start = () => {
    setMessage(seasonNow());
    load();
  };
  if (!('IntersectionObserver' in window)) { start(); return; }
  const io = new IntersectionObserver((entries) => {
    if (entries.some((en) => en.isIntersecting)) { io.disconnect(); start(); }
  }, { rootMargin: '600px 0px' });
  io.observe(root);
})();
