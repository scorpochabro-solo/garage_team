/* ============================================================
   shtorka: «Рольворота между страницами» — marks the incoming cross-document view transition
   NOT part of site.js: build/shtorka.py inlines this file into <head>. `pagereveal` fires right before the new page's
   first frame, and that frame is when the new state is captured, so the listener must exist before the body is
   parsed; a deferred script would come too late on long pages.
   The look and the timing are CSS (css/shtorka.css). This script only decides whether the shutter runs, in which
   direction, and where the content area of the new page starts and ends.
   ============================================================ */
(() => {
  'use strict';
  // without cross-document view transitions the navigation is a plain one and nothing here is needed
  if (!('onpagereveal' in window)) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const nav = window.navigation;
  // formNav: the navigation under way comes from a form, it gets no shutter;
  // restored: this document has just come back from the back/forward cache
  let formNav = false;
  let restored = false;
  // skipping rejects `ready` with an AbortError by design; unhandled, a page kept in the back/forward cache reports it
  // as an uncaught error when it is restored. Any other reason still surfaces.
  const skip = (vt) => {
    vt.ready.catch((err) => { if (!err || err.name !== 'AbortError') throw err; });
    vt.skipTransition();
  };

  /* ---------- leaving the page ---------- */
  // a submitted form is not a move between pages (and a POST fails on a static host anyway); any click starts over
  addEventListener('click', () => { formNav = false; }, true);
  addEventListener('submit', (e) => { formNav = !e.defaultPrevented; });
  // form.submit() fires no submit event, but the Navigation API still sees its POST data
  if (nav) nav.addEventListener('navigate', (e) => { if (e.formData) formNav = true; });
  // the page left through a form and restored from the cache must not keep the flag for its next link
  addEventListener('pageshow', (e) => { restored = e.persisted; if (e.persisted) formNav = false; });

  const samePage = (url) => {
    const u = new URL(url, location.href);
    return u.pathname === location.pathname && u.search === location.search;
  };
  addEventListener('pageswap', (e) => {
    const vt = e.viewTransition;
    if (!vt) return;
    // a link to the page itself would only roll the shutter over the same page
    const to = e.activation && e.activation.entry ? e.activation.entry.url : '';
    if (formNav || (to && samePage(to))) skip(vt);
  });

  /* ---------- arriving ---------- */
  // back = a traversal to an earlier history entry; Safari before 26.2 has no Navigation API, there a page restored
  // from the cache or loaded by Back/Forward counts as «back»
  const goingBack = () => {
    const act = nav && nav.activation;
    if (act && act.entry && act.from) return act.navigationType === 'traverse' && act.entry.index < act.from.index;
    if (restored) return true;
    const entry = performance.getEntriesByType('navigation')[0];
    return !!entry && entry.type === 'back_forward';
  };
  // the shutter runs in the content area: from the bottom edge of the header (the top line above it on a desktop
  // page at its top) down to the phone call bar (0 when the bar is hidden). One layout read, right before the first
  // frame lays the page out anyway; the writes go to the shutter alone, which is still display: none.
  // Rounded down, so the shutter tucks under the header and the bar (they are painted over it): a fractional edge on a
  // 3x screen must not leave a hairline of the page flickering between them.
  const place = (shutter) => {
    const header = document.querySelector('.site-header');
    const bar = document.querySelector('.mobile-bar');
    if (header) shutter.style.top = Math.max(0, Math.floor(header.getBoundingClientRect().bottom)) + 'px';
    if (bar) shutter.style.bottom = Math.floor(bar.getBoundingClientRect().height) + 'px';
  };
  addEventListener('pagereveal', (e) => {
    const vt = e.viewTransition;
    if (!vt) return;
    const shutter = document.getElementById('shtorka');
    // without transition types the CSS could not tell the shutter from the browser's default cross-fade
    if (reduce.matches || !vt.types || !shutter) { skip(vt); return; }
    try {
      place(shutter);
      vt.types.add('shtorka');
      if (goingBack()) vt.types.add('shtorka-back');
    } catch (err) {
      // a plain navigation then, and the error still reaches the console
      skip(vt);
      throw err;
    }
    // the new page may still scroll while the shutter runs: to the #anchor of the link, to the place restored by
    // Back. The sticky header moves with it and the snapshots are live, so the shutter follows. Such a scroll comes
    // a frame after the start at the earliest, when the shutter is still out of sight, so the move is never seen.
    const follow = () => place(shutter);
    const stop = () => { removeEventListener('scroll', follow); removeEventListener('resize', follow); };
    addEventListener('scroll', follow, { passive: true });
    addEventListener('resize', follow, { passive: true });
    vt.finished.then(stop, stop);
  });
})();
