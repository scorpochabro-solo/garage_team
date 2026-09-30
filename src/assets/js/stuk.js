/* ============================================================
   «Что стучит?» (home page, section #stuk, table in build/stuk.py):
   what was noticed → when → (where) → possible causes with links to the
   service pages and a ready request text for the callback modal or the
   request form. The table is fetched only when the section comes near the
   screen; there are no loops or timers, only clicks.
   ============================================================ */
(() => {
  'use strict';
  const root = document.querySelector('[data-stuk]');
  if (!root) return;
  const G = window.G || {};
  const $ = (s, r = root) => r.querySelector(s);
  const $$ = (s, r = root) => Array.from(r.querySelectorAll(s));
  const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ESC[c]);
  // «Стойки стабилизатора» → «стойки стабилизатора», but «ТНВД» and «ABS» stay as they are
  const lower = (s) => (s.length > 1 && s[1] === s[1].toLowerCase() ? s[0].toLowerCase() + s.slice(1) : s);
  const pad2 = (n) => String(n).padStart(2, '0');
  const ic = (name) => `<svg class="ic" aria-hidden="true" focusable="false"><use href="#i-${name}"/></svg>`;

  const steps = [1, 2, 3].map((n) => $(`[data-q="${n}"]`));
  const tiles = $$('.stuk-sym');
  const chipsBox = $('[data-chips]');
  const zoneBtns = $$('.stuk-zone');
  const car = $('.stuk-car__svg');
  const out = $('[data-out]');
  const idle = $('[data-idle]');
  const res = $('[data-res]');
  const resBody = $('[data-res-body]');
  const resLabel = $('[data-res-label]');
  const cta = $('[data-cta]');
  const live = $('[data-live]');
  const narrow = matchMedia('(max-width: 1099px)');   // one column: answered questions fold (stuk.css)
  const ZONE_KEYS = ['front', 'hood', 'under', 'rear'];

  let data = null;
  let loading = null;
  let lastAdded = '';
  const state = { s: null, c: null, z: null };

  /* ---------- data: fetched once, when the section is about to be seen (or on the first tap) ---------- */
  const load = () => {
    if (data) return Promise.resolve(data);
    if (!loading) {
      loading = fetch(root.dataset.src, { credentials: 'same-origin' })
        .then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then((json) => { data = json; return json; })
        .catch((err) => {
          loading = null;
          showError();
          throw err;
        });
    }
    return loading;
  };
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      if (entries.some((en) => en.isIntersecting)) { io.disconnect(); load().catch(() => {}); }
    }, { rootMargin: '600px 0px' });
    io.observe(root);
  } else {
    load().catch(() => {});
  }

  /* ---------- lookups ---------- */
  const sym = () => (data && state.s ? data.s[state.s] : null);
  const ctx = () => { const s = sym(); return s && state.c ? s.c.find((c) => c[0] === state.c) || null : null; };
  const zonesOf = (c) => (c && c[5]) || {};
  const causeKeys = () => { const c = ctx(); const z = zonesOf(c); return state.z && z[state.z] ? z[state.z] : c[4]; };
  const say = () => ctx()[2].replace('{где}', state.z ? data.z[state.z][1] : '');
  const words = (k) => data.c[k][3] || lower(data.c[k][0]);
  const message = () => `${say()}. Возможные причины: ${causeKeys().map(words).join(', ')}.`;

  /* ---------- painting ---------- */
  const announce = (text) => {
    live.textContent = '';
    requestAnimationFrame(() => { live.textContent = text; });
  };

  const setStep = (n, { value = '', done = false, current = false } = {}) => {
    const step = steps[n - 1];
    step.classList.toggle('is-done', done);
    step.classList.toggle('is-current', current);
    step.classList.remove('is-editing');
    $('[data-val]', step).textContent = value;
  };

  const paintTiles = () => {
    tiles.forEach((t) => t.setAttribute('aria-pressed', String(t.dataset.s === state.s)));
    root.classList.toggle('has-s', !!state.s);
  };

  const renderChips = () => {
    const s = sym();
    $('#stuk-q2').textContent = s ? s.q2 : 'Когда?';
    $('[data-wait]').hidden = !!s;
    chipsBox.hidden = !s;
    if (!s) { chipsBox.innerHTML = ''; return; }
    chipsBox.innerHTML = s.c.map((c, i) => {
      const sw = c[6] ? `<span class="stuk-chip__sw" style="--sw:${esc(c[6])}" aria-hidden="true"></span>` : '';
      return `<button class="stuk-chip" type="button" aria-pressed="false" data-c="${esc(c[0])}" style="--i:${i}">${sw}${esc(c[1])}</button>`;
    }).join('');
    // restart the entrance animation of the new set of chips
    chipsBox.classList.remove('is-in');
    void chipsBox.offsetWidth;
    chipsBox.classList.add('is-in');
  };

  const paintChips = () => {
    $$('.stuk-chip', chipsBox).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.c === state.c)));
  };

  const paintZones = () => {
    const c = ctx();
    const zones = zonesOf(c);
    const on = (k) => Object.prototype.hasOwnProperty.call(zones, k);
    const where = steps[2];
    where.hidden = !Object.keys(zones).length;
    if (where.hidden) return;
    $('#stuk-q3').textContent = sym().q3 || 'Где?';
    zoneBtns.forEach((b) => {
      b.hidden = !on(b.dataset.z);
      b.setAttribute('aria-pressed', String(b.dataset.z === state.z));
    });
    ZONE_KEYS.forEach((k) => {
      $$(`.z-${k}, .stuk-car__hit[data-z="${k}"]`, car).forEach((el) => {
        el.classList.toggle('is-on', on(k));
        el.classList.toggle('is-sel', k === state.z);
      });
    });
  };

  // «норма» items get a check instead of a number, so the faults are counted 01, 02… on their own
  const causeHTML = (k, i, keys) => {
    const [title, text, page] = data.c[k];
    const n = keys.slice(0, i + 1).filter((x) => data.c[x][2]).length;
    if (!page) {
      return `<li class="stuk-cause stuk-cause--ok" style="--i:${i}"><span class="stuk-cause__n">${ic('check')}</span>` +
        `<div class="stuk-cause__b"><p class="stuk-cause__t">${esc(title)} <span class="stuk-cause__tag">норма</span></p><p class="stuk-cause__x">${esc(text)}</p></div></li>`;
    }
    const [href, name] = data.p[page];
    return `<li class="stuk-cause" style="--i:${i}"><span class="stuk-cause__n">${pad2(n)}</span>` +
      `<div class="stuk-cause__b"><p class="stuk-cause__t">${esc(title)}</p>` +
      `<a class="stuk-cause__a" href="${esc(href)}">${esc(name)} ${ic('arrow-up-right')}</a>` +
      `<p class="stuk-cause__x">${esc(text)}</p></div></li>`;
  };

  const renderOut = () => {
    const s = sym();
    const c = ctx();
    idle.hidden = !!s;
    res.hidden = !s;
    out.classList.toggle('is-on', !!c);
    cta.hidden = !c;
    if (!s) { resBody.innerHTML = ''; return; }
    if (!c) {
      // a symptom without its context yet: what usually gives it and what to answer next
      resLabel.textContent = '// Подсказка';
      resBody.innerHTML = `<h3 class="stuk-res__title" tabindex="-1">${esc(s.n)}</h3>` +
        `<p class="stuk-res__lead">${esc(s.lead)}</p>` +
        `<p class="stuk-res__next stuk-res__next--ask">${ic('arrow')}<span>${esc(s.q2)}</span></p>`;
      return;
    }
    const keys = causeKeys();
    const [diagHref, diagName] = data.p[c[3]];
    const needWhere = Object.keys(zonesOf(c)).length && !state.z;
    resLabel.textContent = '// Возможные причины';
    resBody.innerHTML = `<h3 class="stuk-res__title" tabindex="-1">${esc(say())}</h3>` +
      (needWhere ? `<p class="stuk-res__next">${ic('arrow')}<span>${esc(s.q3)} Уточните\u00a0— список станет точнее.</span></p>` : '') +
      `<ol class="stuk-causes">${keys.map(causeHTML).join('')}</ol>` +
      `<p class="stuk-res__note">${ic('info')}<span>Это подсказка, а не диагноз: один и тот же признак дают разные узлы. ` +
      `Точную причину покажет <a href="${esc(diagHref)}">${esc(lower(diagName))}</a>.</span></p>` +
      `<div class="stuk-res__msg"><p class="stuk-res__msg-label">Текст для заявки</p><p class="stuk-res__msg-text">${esc(message())}</p></div>`;
  };

  const paint = () => {
    paintTiles();
    paintChips();
    paintZones();
    renderOut();
    const s = sym();
    const c = ctx();
    setStep(1, { value: s ? s.n : '', done: !!s, current: !s });
    setStep(2, { value: c ? c[1] : '', done: !!c, current: !!s && !c });
    setStep(3, { value: state.z ? data.z[state.z][0] : '', done: !!state.z, current: !!c && !state.z });
  };

  /* ---------- phones and tablets: keep the answer in view ---------- */
  const headerH = () => { const h = document.querySelector('[data-header]'); return h ? h.getBoundingClientRect().height : 0; };
  const bringIntoView = () => {
    if (!narrow.matches) return;
    const top = out.getBoundingClientRect().top;
    if (top > headerH() && top < innerHeight * 0.6) return;
    const app = $('[data-app]').getBoundingClientRect().top + scrollY - headerH() - 12;
    scrollTo({ top: app, behavior: G.reducedMotion ? 'auto' : 'smooth' });
  };
  // keyboard users land on the next thing to answer when the question they answered folds away
  const focusNext = (el) => { if (el && narrow.matches) el.focus({ preventScroll: true }); };

  /* ---------- actions ---------- */
  const pickSymptom = (key, byKeyboard) => {
    if (state.s !== key) { state.s = key; state.c = null; state.z = null; renderChips(); }
    paint();
    const s = sym();
    announce(`${s.n}. ${s.q2}`);
    if (byKeyboard) focusNext($('.stuk-chip', chipsBox));
  };

  const pickContext = (key, byKeyboard) => {
    state.c = key;
    state.z = null;
    paint();
    const titles = causeKeys().map((k) => lower(data.c[k][0]));
    announce(`${say()}. Возможные причины: ${titles.join(', ')}. Это подсказка, а не диагноз.`);
    bringIntoView();
    if (byKeyboard) focusNext(steps[2].hidden ? $('.stuk-res__title') : $('.stuk-zone:not([hidden])'));
  };

  const pickZone = (key, byKeyboard) => {
    const c = ctx();
    if (!c || !Object.prototype.hasOwnProperty.call(zonesOf(c), key)) return;
    state.z = state.z === key ? null : key;   // tapping the chosen place again goes back to the general list
    paint();
    const titles = causeKeys().map((k) => lower(data.c[k][0]));
    announce(`${say()}. Возможные причины: ${titles.join(', ')}.`);
    bringIntoView();
    if (byKeyboard) focusNext($('.stuk-res__title'));
  };

  const reset = (byKeyboard) => {
    state.s = null; state.c = null; state.z = null;
    renderChips();
    paint();
    announce('Подсказка очищена. Что заметили?');
    if (narrow.matches) {
      const top = $('[data-app]').getBoundingClientRect().top;
      if (top < headerH()) scrollTo({ top: top + scrollY - headerH() - 12, behavior: G.reducedMotion ? 'auto' : 'smooth' });
    }
    if (byKeyboard) tiles[0].focus({ preventScroll: true });
  };

  const preset = (value) => {
    const [s, c, z] = value.split('|');
    state.s = s; state.c = null; state.z = null;
    renderChips();
    pickContext(c);
    if (z) pickZone(z);
  };

  const edit = (n) => {
    const step = steps[n - 1];
    step.classList.add('is-editing');
    const chosen = $('[aria-pressed="true"]', step) || $('button:not([hidden]):not([data-edit])', $('.stuk-q__body', step));
    if (chosen) chosen.focus({ preventScroll: true });
    step.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'nearest' });
  };

  const callback = () => { if (G.openModal) G.openModal('call', { message: message() }); };

  // the request form keeps the text through its own steps: it only validates and posts request_part[what]
  const toRequest = () => {
    const text = message();
    const form = document.getElementById('request-form');
    const field = document.getElementById('request_what');
    const section = document.getElementById('request');
    const sent = form && form.querySelector('[data-success].is-visible');
    if (!form || !field || !section || sent) { callback(); return; }
    const current = field.value.trim();
    if (lastAdded && current.includes(lastAdded)) field.value = current.replace(lastAdded, text);
    else field.value = current ? `${current}\n${text}` : text;
    lastAdded = text;
    field.dispatchEvent(new Event('input', { bubbles: true }));

    // the form may still be on its first step (the car): a note at the top of that step says where the text went;
    // on the description step the text is in plain sight
    const panel = form.querySelector('.rq__panel.is-active');
    $$('.stuk-rq-note', form).forEach((n) => n.remove());
    if (panel && panel.dataset.panel !== '2') {
      const note = document.createElement('p');
      note.className = 'stuk-rq-note';
      note.innerHTML = `${ic('check')}<span>Описание неисправности уже в заявке, на шаге 2 «Ввод запроса».</span>`;
      panel.insertBefore(note, panel.firstElementChild);
    }
    announce('Описание добавлено в заявку, на шаг 2 «Ввод запроса».');
    // on a phone the section starts with its heading and texts, the form itself is a screen lower
    (narrow.matches ? form : section).scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'start' });
    if (G.canHover) {
      const first = panel && panel.dataset.panel === '2' ? field
        : panel && panel.querySelector('select:not([disabled]), input:not([type=hidden]):not([disabled])');
      if (first) setTimeout(() => first.focus({ preventScroll: true }), 450);
    }
  };

  const showError = () => {
    idle.hidden = true;
    res.hidden = false;
    cta.hidden = true;
    resLabel.textContent = '// Подсказка';
    resBody.innerHTML = '<p class="stuk-res__lead">Подсказка не загрузилась. Обновите страницу или позвоните нам\u00a0— поможем разобраться по телефону.</p>';
  };

  /* ---------- one click listener for the whole section ---------- */
  root.addEventListener('click', (e) => {
    const t = e.target;
    const byKeyboard = e.detail === 0;
    const tile = t.closest('.stuk-sym');
    const chip = t.closest('.stuk-chip:not(.stuk-zone)');
    const zone = t.closest('.stuk-zone') || t.closest('.stuk-car__hit.is-on');
    const pre = t.closest('.stuk-preset');
    const ed = t.closest('[data-edit]');
    const act = t.closest('[data-act]');
    if (!(tile || chip || zone || pre || ed || act)) return;
    load().then(() => {
      if (tile) pickSymptom(tile.dataset.s, byKeyboard);
      else if (chip) pickContext(chip.dataset.c, byKeyboard);
      else if (zone) pickZone(zone.dataset.z, byKeyboard && !!zone.closest('button'));
      else if (pre) preset(pre.dataset.preset);
      else if (ed) edit(Number(ed.dataset.edit));
      else if (act.dataset.act === 'reset') reset(byKeyboard);
      else if (act.dataset.act === 'call') callback();
      else if (act.dataset.act === 'request') toRequest();
    }).catch(() => {});
  });

  /* ---------- the car and the place buttons light up together ---------- */
  const hover = (key, on) => {
    if (!key) return;
    $$(`.z-${key}`, car).forEach((el) => el.classList.toggle('is-hover', on));
    zoneBtns.forEach((b) => { if (b.dataset.z === key) b.classList.toggle('is-hover', on); });
  };
  const hoverKey = (t) => { const el = t.closest('.stuk-car__hit.is-on, .stuk-zone'); return el ? el.dataset.z : null; };
  steps[2].addEventListener('pointerover', (e) => hover(hoverKey(e.target), true), { passive: true });
  steps[2].addEventListener('pointerout', (e) => hover(hoverKey(e.target), false), { passive: true });
})();
