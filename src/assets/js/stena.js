/* ============================================================
   «Стена направлений» (build/stena.py, stena.css): /services.html
   · the search (pages.js) filters the list of works; the wall mirrors it — a brick stays while its direction is found,
     and the remaining bricks close up into a new running bond (stena.css);
   · the list of works under the wall is open on wide screens and folded on phones; a search opens it and folds it back
     when cleared, and when nothing is found it goes (the phone note under the empty wall says so);
   · the bricks are laid once: the first search (or the end of the entrance) ends the animation, so a brick that
     comes back after a search just appears.
   No animation loop: attribute and class changes only.
   ============================================================ */
(() => {
  'use strict';
  const stena = document.querySelector('[data-stena]');
  if (!stena) return;
  const index = document.querySelector('[data-stena-index]');
  const filter = document.querySelector('[data-filter]');
  const hrefOf = (a) => (a ? a.getAttribute('href') : '');

  /* ---------- the wall follows the list ---------- */
  const slots = new Map(Array.from(stena.querySelectorAll('.stena__slot'), (li) => [hrefOf(li.querySelector('.brick')), li]));
  const cards = index ? Array.from(index.querySelectorAll('.cat-card')) : [];
  const mirror = () => {
    let found = 0;
    cards.forEach((card) => {
      const hidden = card.classList.contains('is-hidden');
      const li = slots.get(hrefOf(card.querySelector('.cat-card__head')));
      if (li) li.hidden = hidden;
      if (!hidden) found += 1;
    });
    index.hidden = found === 0;
  };
  if (cards.length) {
    // pages.js toggles .is-hidden on the cards; whatever changes them, the wall follows in the same frame
    new MutationObserver(mirror).observe(index, { subtree: true, attributes: true, attributeFilter: ['class'] });
    mirror();
  }

  /* ---------- the bricks are laid once ---------- */
  const laid = () => stena.classList.add('is-laid');
  if (filter && filter.value.trim()) laid();   // opened with ?q=: the result is shown at once
  if (filter) filter.addEventListener('input', laid);
  // the entrance lasts bricks × step + delay + duration (stena.css); after it a brick that reappears must not be laid again
  const entrance = () => {
    const css = getComputedStyle(stena);
    const ms = (name, fallback) => parseFloat(css.getPropertyValue(name)) || fallback;
    setTimeout(laid, slots.size * ms('--lay-step', 28) + ms('--lay-delay', 260) + ms('--lay-dur', 600) + 200);
  };
  if (stena.classList.contains('is-in')) entrance();
  else {
    const watch = new MutationObserver(() => {
      if (!stena.classList.contains('is-in')) return;
      watch.disconnect();
      entrance();
    });
    watch.observe(stena, { attributes: true, attributeFilter: ['class'] });
  }

  /* ---------- touch: iOS applies :active (the pressed brick) only with a touch listener ---------- */
  stena.addEventListener('touchstart', () => {}, { passive: true });

  /* ---------- the list of works: open on wide screens, folded on phones ---------- */
  if (!index || !filter) return;
  const wide = matchMedia('(min-width: 1001px)');
  let openedBySearch = false;
  const searching = () => filter.value.trim() !== '';
  const fold = () => {
    if (searching()) {
      if (!index.open) { index.open = true; openedBySearch = true; }
    } else if (openedBySearch) {
      index.open = false;
      openedBySearch = false;
    }
  };
  index.open = searching() || wide.matches;
  openedBySearch = searching() && !wide.matches;
  filter.addEventListener('input', fold);
  const onScreenChange = () => { if (!searching()) index.open = wide.matches; };
  if (wide.addEventListener) wide.addEventListener('change', onScreenChange); else wide.addListener(onScreenChange);
})();
