/* ============================================================
   «Что горит на приборной панели» (#pribory): warning-light cluster.
   The cards are rendered by build/pribory.py; without this script they
   stay a readable list. Here: one card at a time, the lamps as toggle
   buttons, the ignition bulb check once when the panel first comes
   into view. No animation loop: every effect is a class switch that
   fades opacity (css/pribory.css).
   ============================================================ */
(() => {
  'use strict';
  const root = document.querySelector('[data-pribory]');
  if (!root) return;
  const G = window.G || {};
  const cluster = root.querySelector('[data-cluster]');
  const lamps = Array.from(root.querySelectorAll('[data-lamp]'));
  const cards = new Map(Array.from(root.querySelectorAll('[data-lamp-card]'), (c) => [c.dataset.lampCard, c]));
  const screen = root.querySelector('.cluster__screen');
  const screenText = root.querySelector('[data-cluster-screen]');
  const live = root.querySelector('[data-pribory-live]');
  if (!cluster || !lamps.length) return;
  const CHECK_MS = 1100;       // how long every lamp stays lit at «ignition»; each then goes out after its own --off delay
  const SEEN = 96;             // px of the card that must show above the bottom edge for the page to stay where it is

  root.classList.add('is-live');   // one card at a time (the section's inline first line normally set this already)

  let current = '';
  let checking = false;
  let checkTimer = 0;

  /* ---------- the trip-computer line ---------- */
  function showOnScreen(key) {
    if (!screen || !screenText) return;
    const card = key ? cards.get(key) : null;
    screenText.textContent = card ? card.dataset.short : screen.dataset[checking ? 'check' : 'idle'];
    if (card) screen.dataset.tone = card.dataset.tone; else screen.removeAttribute('data-tone');
  }

  /* ---------- bring the card into view when it opened below the fold (phones: the card is under the panel) ---------- */
  // page position from offsetTop: unlike getBoundingClientRect it ignores a scroll-reveal that is still sliding in
  const pageTop = (el) => { let y = 0; for (let n = el; n; n = n.offsetParent) y += n.offsetTop; return y; };
  function reveal(card, force) {
    const header = document.querySelector('[data-header]');
    const bar = document.querySelector('.mobile-bar');
    const top = header ? header.getBoundingClientRect().height : 0;
    const bottom = innerHeight - (bar ? bar.getBoundingClientRect().height : 0);
    const y = pageTop(card) - scrollY;
    if (!force && y >= top && y <= bottom - SEEN) return;
    // a link to one lamp shows the panel together with its card when both fit on the screen
    const stage = card.closest('.pribory__stage');
    const target = force && stage && stage.offsetHeight <= bottom - top - 24 ? stage : card;
    scrollTo({ top: Math.max(0, pageTop(target) - top - 12), behavior: G.reducedMotion ? 'auto' : 'smooth' });
  }

  function stopCheck() {
    if (!checking) return;
    checking = false;
    clearTimeout(checkTimer);
    cluster.classList.remove('is-check');
  }

  /* ---------- select a lamp: '' shows the colour legend again ---------- */
  function select(key, opts = {}) {
    if (!cards.has(key)) key = '';
    stopCheck();
    current = key;
    lamps.forEach((b) => {
      const on = b.dataset.lamp === key;
      b.classList.toggle('is-on', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    cards.forEach((c, k) => c.classList.toggle('is-active', k === key));
    cluster.classList.toggle('has-active', !!key);
    showOnScreen(key);
    const card = cards.get(key);
    if (live) {
      const title = key && card.querySelector('.lamp-card__title');
      const urgency = key && card.querySelector('.lamp-card__urgency');
      live.textContent = key ? `${title.textContent}. ${urgency.textContent}` : '';
    }
    if (key && opts.scroll !== false) reveal(card);
  }

  cluster.addEventListener('click', (e) => {
    const b = e.target.closest('[data-lamp]');
    if (!b) return;
    // a second press on the lit lamp switches it off: back to the colour legend (toggle-button semantics)
    select(b.dataset.lamp === current ? '' : b.dataset.lamp);
  });

  /* ---------- the screen previews the lamp under the mouse or the keyboard focus ---------- */
  // keyboard focus only: a mouse click also focuses the button and would leave a stale name on the screen
  const byKeyboard = (el) => { try { return el.matches(':focus-visible'); } catch (_) { return false; } };
  lamps.forEach((b) => {
    b.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') showOnScreen(b.dataset.lamp); });
    b.addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse') showOnScreen(current); });
    b.addEventListener('focus', () => { if (byKeyboard(b)) showOnScreen(b.dataset.lamp); });
    b.addEventListener('blur', () => showOnScreen(current));
  });

  /* ---------- arrows move between lamps as on the grid; Tab still visits every lamp ---------- */
  const columns = () => {
    const top = lamps[0].offsetTop;
    const n = lamps.findIndex((b) => b.offsetTop !== top);
    return n > 0 ? n : lamps.length;
  };
  cluster.addEventListener('keydown', (e) => {
    const i = lamps.indexOf(document.activeElement);
    if (i < 0) return;
    const step = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns(), ArrowUp: -columns() }[e.key];
    let j = step === undefined ? { Home: 0, End: lamps.length - 1 }[e.key] : i + step;
    if (j === undefined) return;
    e.preventDefault();
    j = Math.min(lamps.length - 1, Math.max(0, j));
    lamps[j].focus();
  });

  /* ---------- ignition: all lamps light up for a moment and go out, as when the key is turned ---------- */
  function ignition() {
    cluster.classList.add('is-awake');
    if (current) return;   // a lamp was already chosen (a quick tap or a link to #pribory-…): no light show over it
    checking = true;
    cluster.classList.add('is-check');
    showOnScreen('');
    checkTimer = setTimeout(() => { stopCheck(); showOnScreen(current); }, CHECK_MS);
  }
  if (G.reducedMotion || !('IntersectionObserver' in window)) {
    cluster.classList.add('is-awake');
  } else {
    // most of the panel on screen (or half the screen filled by it, on a short landscape phone)
    const onScreen = (r) => {
      const seen = Math.min(r.bottom, innerHeight) - Math.max(r.top, 0);
      return seen >= r.height * 0.75 || seen >= innerHeight * 0.5;
    };
    const io = new IntersectionObserver((entries) => {
      if (!entries.some((en) => onScreen(en.boundingClientRect))) return;
      io.disconnect();
      // let the scroll-reveal fade the panel in first; if it was only scrolled past, wait for the next time it shows
      setTimeout(() => { if (onScreen(cluster.getBoundingClientRect())) ignition(); else io.observe(cluster); }, 450);
    }, { threshold: [0.25, 0.5, 0.75, 1] });
    io.observe(cluster);
  }

  /* ---------- a link to one lamp: /#pribory-oil opens its card ---------- */
  const fromHash = () => {
    const key = decodeURIComponent(location.hash.replace(/^#pribory-/, ''));
    if (!key || key === location.hash || !cards.has(key)) return;
    select(key, { scroll: false });
    // scroll once the web fonts are in: until then the text above is set in a fallback font and every offset is off
    const go = () => reveal(cards.get(key), true);
    if (document.fonts && document.fonts.status !== 'loaded') document.fonts.ready.then(go); else go();
  };
  fromHash();
  addEventListener('hashchange', fromHash);
})();
