/* ============================================================
   otkryto: «Открыто сейчас» — the live status in Moscow time from the hours in data-oc (build/otkryto.py: 7 days
   from Monday, [opens, closes] in minutes, {note} or null), today in the week; «Как добраться»: copy the address,
   save the contact as a vCard. Without JS the plain hours stay in the markup.
   ============================================================ */
(() => {
  'use strict';
  const G = (window.G = window.G || {});
  const TZ = 'Europe/Moscow';   // Nizhny Novgorod keeps Moscow time: UTC+3 all year, no daylight saving
  const UTC_OFFSET = 180;       // minutes, for a browser without time zone data
  const SOON = 60;              // «Скоро закрываемся»: the last hour
  const NB = '\u00a0';           // no line break after a short preposition: «в 9:00», «до 19:00» stay whole
  const ON_DAY = ['в понедельник', 'во вторник', 'в среду', 'в четверг', 'в пятницу', 'в субботу', 'в воскресенье'].map((d) => d.replace(' ', NB));
  const UNTIL_DAY = ['понедельника', 'вторника', 'среды', 'четверга', 'пятницы', 'субботы', 'воскресенья'];
  const WEEKDAY = { Mon: 0, Tue: 1, Wed: 2, Thu: 3, Fri: 4, Sat: 5, Sun: 6 };

  /* ---------- time: the Moscow wall clock of a Date, { day: 0 (Monday) … 6, min: minutes since midnight } ---------- */
  let clock = null;
  const moscow = (date) => {
    try {
      clock = clock || new Intl.DateTimeFormat('en-US', { timeZone: TZ, weekday: 'short', hour: 'numeric', minute: 'numeric', hour12: false });
      const p = {};
      clock.formatToParts(date).forEach((x) => { p[x.type] = x.value; });
      const day = WEEKDAY[p.weekday];
      const min = (Number(p.hour) % 24) * 60 + Number(p.minute);   // % 24: some engines say «24» at midnight
      if (day !== undefined && !p.dayPeriod && Number.isFinite(min)) return { day, min };
    } catch (_) { /* no time zone data: UTC+3 below */ }
    const t = new Date(date.getTime() + UTC_OFFSET * 60000);
    return { day: (t.getUTCDay() + 6) % 7, min: t.getUTCHours() * 60 + t.getUTCMinutes() };
  };
  const hm = (min) => Math.floor(min / 60) + ':' + String(min % 60).padStart(2, '0');

  /* ---------- status: { state: open | soon | closed | note, word, rest, brief } ----------
     rest goes after the word in the contacts and the menu; brief is the shorter form for the header's top line */
  const status = (week, now) => {
    const today = week[now.day];
    if (Array.isArray(today)) {
      const opens = today[0];
      const closes = today[1];
      if (now.min >= opens && now.min < closes) {
        const soon = closes - now.min <= SOON;
        const until = 'до' + NB + hm(closes);
        return { state: soon ? 'soon' : 'open', word: soon ? 'Скоро закрываемся' : 'Открыто', rest: until, brief: until };
      }
      if (now.min < opens) return { state: 'closed', word: 'Закрыто', rest: 'откроемся сегодня в' + NB + hm(opens), brief: 'до' + NB + hm(opens) };
    } else if (today && today.note) {
      return { state: 'note', word: 'Сегодня', rest: today.note, brief: today.note };
    }
    for (let k = 1; k <= 7; k += 1) {
      const d = (now.day + k) % 7;
      const next = week[d];
      if (Array.isArray(next)) {
        const at = hm(next[0]);
        return k === 1
          ? { state: 'closed', word: 'Закрыто', rest: 'откроемся завтра в' + NB + at, brief: 'до завтра, ' + at }
          : { state: 'closed', word: 'Закрыто', rest: 'откроемся ' + ON_DAY[d] + ' в' + NB + at, brief: 'до ' + UNTIL_DAY[d] + ', ' + at };
      }
      if (next && next.note) {
        const rest = (k === 1 ? 'завтра' : ON_DAY[d]) + ' ' + next.note;
        return { state: 'closed', word: 'Закрыто', rest, brief: rest };
      }
    }
    return { state: 'closed', word: 'Закрыто', rest: '', brief: '' };
  };

  // the vCard lines come escaped and folded from build/otkryto.py; a file wants CRLF line ends
  const vcardFile = (lines) => lines.join('\r\n') + '\r\n';
  G.otkryto = { moscow, status, hm, vcardFile };

  /* ---------- the widgets: header top line, mobile menu, the weeks on the home page and /contacts/ ---------- */
  const widgets = [];
  document.querySelectorAll('[data-oc]').forEach((el) => {
    let week = null;
    try { week = JSON.parse(el.dataset.oc).week; } catch (_) { week = null; }
    if (Array.isArray(week) && week.length === 7) widgets.push({ el, week, brief: el.hasAttribute('data-oc-brief'), key: '' });
  });

  const paint = (w, now) => {
    const s = status(w.week, now);
    const rest = w.brief ? s.brief : s.rest;
    const key = [s.state, s.word, rest, now.day].join('|');
    if (key === w.key) return;   // a minute tick that changes nothing touches nothing
    w.key = key;
    w.el.dataset.ocState = s.state;
    w.el.classList.add('is-live');
    w.el.querySelectorAll('.oc__text').forEach((text) => {
      const word = document.createElement('span');
      word.className = 'oc__word';
      word.textContent = s.word;
      text.textContent = '';
      text.append(word);
      if (rest) {
        const sep = document.createElement('span');
        sep.className = 'oc__sep';
        sep.setAttribute('aria-hidden', 'true');
        sep.textContent = '·';
        text.append(' ', sep, ' ' + rest);
      }
      text.hidden = false;
    });
    w.el.querySelectorAll('.oc[hidden]').forEach((line) => { line.hidden = false; });
    w.el.querySelectorAll('[data-day]').forEach((cell) => {
      const on = Number(cell.dataset.day) === now.day;
      cell.classList.toggle('is-today', on);
      if (on) cell.setAttribute('aria-current', 'date'); else cell.removeAttribute('aria-current');
    });
  };

  if (widgets.length) {
    let timer = 0;
    const tick = () => {
      clearTimeout(timer);
      const now = moscow(new Date());
      widgets.forEach((w) => paint(w, now));
      // next look right after the minute turns, and none while the tab is hidden
      if (document.visibilityState !== 'hidden') timer = setTimeout(tick, 60000 - (Date.now() % 60000) + 200);
    };
    tick();
    document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') clearTimeout(timer); else tick(); });
    addEventListener('pageshow', (e) => { if (e.persisted) tick(); });
    // the dot's pulse stops off screen (base.css: .is-offscreen)
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver((entries) => entries.forEach((en) => en.target.classList.toggle('is-offscreen', !en.isIntersecting)));
      widgets.forEach((w) => io.observe(w.el));
    }
  }

  /* ---------- «Как добраться»: copy the address ---------- */
  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(text); return true; } catch (_) { /* refused: the old way below */ }
    }
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');   // no keyboard on a phone
    ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;font-size:16px';
    document.body.appendChild(ta);
    ta.focus({ preventScroll: true });   // the page must not jump to the hidden field
    ta.select();
    ta.setSelectionRange(0, text.length);   // iOS Safari selects only by range
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (_) { ok = false; }
    ta.remove();
    return ok;
  };
  document.querySelectorAll('[data-oc-copy]').forEach((btn) => {
    let done = 0;
    btn.hidden = false;
    btn.addEventListener('click', async () => {
      const text = btn.dataset.ocCopy;
      if (await copyText(text)) {
        btn.classList.add('is-done');
        clearTimeout(done);
        done = setTimeout(() => btn.classList.remove('is-done'), 2400);
        if (G.toast) G.toast(btn.dataset.ocToast);
      } else if (G.toast) {
        G.toast('Не удалось скопировать. Адрес: ' + text, 'err');
      }
    });
  });

  /* ---------- «Как добраться»: save the contact (a .vcf made here, nothing is fetched) ---------- */
  document.querySelectorAll('[data-oc-vcard]').forEach((btn) => {
    let lines = null;
    try { lines = JSON.parse(btn.dataset.ocVcard); } catch (_) { lines = null; }
    if (!Array.isArray(lines) || !window.Blob || !window.URL || !URL.createObjectURL) return;
    btn.hidden = false;
    btn.addEventListener('click', () => {
      const url = URL.createObjectURL(new Blob([vcardFile(lines)], { type: 'text/vcard;charset=utf-8' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = btn.dataset.ocFile || 'contact.vcf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);   // an iPhone reads the file after its own dialog
      if (G.toast) G.toast(btn.dataset.ocToast);
    });
  });
})();
