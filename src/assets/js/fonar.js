/* ============================================================
   «Фонарь по кирпичу» (fonar): the dark sections of the site are an old brick wall at night, and the mouse carries
   a hand lamp along it — a soft warm pool that trails the cursor and shows brick and mortar inside it, a shade
   warmer under the pendant over «Как у нас». The light goes out when the cursor leaves the wall or rests a while.
   Hook: data-fonar on the sections (build/fonar.py, which also draws the wall tile); styles: fonar.css.
   What keeps it cheap:
     1. nothing at all without a mouse (hover + fine pointer) or with reduced motion: no layers, no listeners;
     2. the lamp travels in legs: the script plans at most GAP-spaced legs from the pointer events, and each leg is
        a pair of compositor animations (Web Animations, one start time) — the pool goes to the cursor and the wall
        inside it goes the other way by exactly as much, so the bricks stay put on the page. The frames in between
        are the compositor's: no script, no restyle, no re-layering. (A transform written every frame re-layers
        the whole page in Chromium: measured, see notes/fishka-fonar.md.) No requestAnimationFrame loop at all;
     3. when the cursor stops, the last leg runs out and nothing runs; over the first screen, a light section or the
        form the script does nothing but store the cursor;
     4. layout is read in one batch when the page changes size (ResizeObserver), never while the light moves;
        the pointer and scroll handlers only store numbers; lights switch with opacity (CSS transitions).
   ============================================================ */
(() => {
  'use strict';
  const hosts = Array.from(document.querySelectorAll('[data-fonar]'));
  if (!hosts.length || !('ResizeObserver' in window) || !Element.prototype.animate) return;
  const fineMq = matchMedia('(hover: hover) and (pointer: fine)');    // the same queries as G.canHover / G.reducedMotion,
  const calmMq = matchMedia('(prefers-reduced-motion: reduce)');      // but followed live (a mouse plugged in, a setting)

  const DUR = 280;        // ms, one leg; a new leg starts from wherever the light is, so the lamp trails the hand
  const EASE = 'cubic-bezier(0.22, 0.7, 0.35, 1)';   // quick start, long soft arrival
  const GAP = 70;         // ms: legs are planned at most this often, the compositor draws every frame in between
  const LEG = 320;        // px: the longest leg; a flick is chased in several legs (the wall is this much larger)
  const IDLE = 2600;      // ms of stillness before the light goes out
  const FADE = 1000;      // ms: the fade-out of .fonar__beam in fonar.css; its layers are kept that long
  const PENDANT = '.svet-mini .svet-lamp__bulb';   // the lamp over «Как у нас» (build/svet.py) and its heading
  const PENDANT_ON = '.svet-lit';                  // (.is-in once the heading has scrolled in and the lamp is on)

  let zones = [];
  let D = 0; let R = 0; let TW = 0; let TH = 0;       // diameter and radius of the light, size of the wall tile
  let px = 0; let py = 0; let sx = 0; let sy = 0;     // the cursor (viewport px) and the scroll of the page
  let pointer = false; let awake = false; let shining = false;
  let lastMove = 0; let lastLeg = -1e9; let legTimer = 0; let idleTimer = 0; let running = false; let ro = null;
  let leg = null;                                     // { p, q, clock }: the light's top-left on the page, from p to q

  const div = (cls, parent) => { const n = document.createElement('div'); n.className = cls; parent.appendChild(n); return n; };
  const find = (host, sel) => { try { return sel ? host.querySelector(sel) : null; } catch (_) { return null; } };
  const T = (x, y) => `translate(${x}px, ${y}px)`;
  // the colour the section is painted with («r, g, b»): its own background, or the page's where it has none
  function ground(el) {
    for (let n = el; n; n = n.parentElement) {
      const m = getComputedStyle(n).backgroundColor.match(/[\d.]+/g);
      if (m && (m.length < 4 || Number(m[3]) === 1)) return m.slice(0, 3).join(', ');
    }
    return '7, 8, 7';   // --black (the page always has a ground; this is only a fallback)
  }

  /* ---------- layers: created on the first run, removed when the mouse or the motion setting goes ---------- */
  function build() {
    zones = hosts.map((host) => {
      const layer = div('fonar', host);            // absolutely placed, painted under everything (z-index −1): its
      layer.setAttribute('aria-hidden', 'true');   // place in the markup does not matter, the end keeps :first-child
      layer.style.setProperty('--fonar-ground', ground(host));   // rules of the section intact
      const beam = div('fonar__beam', layer);
      div('fonar__glow', beam);                    // the light and its ground, and the fall-off (the veil, last):
      const wall = div('fonar__wall', beam);       // never restyled (fonar.css)
      const bulb = host.querySelector(PENDANT);
      const pool = bulb ? div('fonar__pool', beam) : null;
      div('fonar__veil', beam);
      host.classList.add('is-fonar');
      // the layer is placed on its section: a section that is not positioned (the 404 block) is made the anchor,
      // or the layer would stretch over the first screen from the top of the page
      if (getComputedStyle(host).position === 'static') host.classList.add('is-fonar-anchor');
      return { host, layer, beam, wall, pool, bulb, lamp: bulb && bulb.closest(PENDANT_ON), after: find(host, host.getAttribute('data-fonar-after')),
        x: 0, y: 0, w: 0, h: 0, from: 0, wx: 0, wy: 0, pw: 0, ph: 0, lit: false, fading: 0, anims: [] };
    });
  }
  function unbuild() {
    zones.forEach((z) => { clearTimeout(z.fading); z.anims.forEach((a) => a.cancel()); z.layer.remove(); z.host.classList.remove('is-fonar', 'is-fonar-anchor'); });
    zones = [];
    leg = null;
  }

  /* ---------- geometry: one batched read (ResizeObserver runs it right after layout), then one write per wall ---------- */
  function measure() {
    if (!zones.length) return;
    sx = scrollX; sy = scrollY;
    D = zones[0].beam.offsetWidth; R = D / 2;
    if (!TW) {   // the tile's size, as build/fonar.py wrote it into the wall's rule («408px 160px»)
      const [w, h] = getComputedStyle(zones[0].wall).backgroundSize.split(' ').map(parseFloat);
      TW = w > 0 ? w : 0; TH = h > 0 ? h : 0;
    }
    zones.forEach((z) => {
      const r = z.layer.getBoundingClientRect();
      z.x = r.left + sx; z.y = r.top + sy; z.w = r.width; z.h = r.height;
      z.from = z.after ? Math.max(z.y, z.after.getBoundingClientRect().bottom + sy) : z.y;
      if (z.bulb) {
        const b = z.bulb.getBoundingClientRect();
        z.wx = b.left + b.width / 2 + sx; z.wy = b.top + b.height / 2 + sy;
        z.pw = z.pool.offsetWidth; z.ph = z.pool.offsetHeight;
      }
    });
    // the wall covers the pool, one tile to lay it on the page grid and one leg of travel (see move())
    const ww = `${Math.ceil(D + TW + LEG)}px`; const wh = `${Math.ceil(D + TH + LEG)}px`;
    zones.forEach((z) => { if (z.wall.style.width !== ww || z.wall.style.height !== wh) { z.wall.style.width = ww; z.wall.style.height = wh; } });
    if (shining) { lastLeg = -1e9; plan(); }   // the page moved under the lamp: a new leg from the new places
  }

  /* ---------- a leg: the pool goes from p to q, the wall inside it the other way, the warm patch with the wall ---------- */
  function move(z, p, q, t0) {
    // the wall's corner on the page grid of the tile, fixed for the whole leg: at both ends it is at or left of / above
    // the pool's corner, and never more than a tile plus a leg away, which is what the wall's size allows for
    const gx = Math.floor(Math.min(p[0], q[0]) / TW) * TW; const gy = Math.floor(Math.min(p[1], q[1]) / TH) * TH;
    const opts = { duration: DUR, easing: EASE, fill: 'forwards' };
    const next = [
      z.beam.animate([{ transform: T(p[0] - z.x, p[1] - z.y) }, { transform: T(q[0] - z.x, q[1] - z.y) }], opts),
      z.wall.animate([{ transform: T(gx - p[0], gy - p[1]) }, { transform: T(gx - q[0], gy - q[1]) }], opts),
    ];
    if (z.pool) {
      const ox = Math.round(z.wx - z.pw / 2); const oy = Math.round(z.wy - z.ph * 0.2);
      next.push(z.pool.animate([{ transform: T(ox - p[0], oy - p[1]) }, { transform: T(ox - q[0], oy - q[1]) }], opts));
    }
    // one start time for all of them: the pool and the wall move in step, frame by frame, on the compositor
    if (t0 != null) next.forEach((a) => { a.startTime = t0; });
    z.anims.forEach((a) => a.cancel());
    z.anims = next;
    return next[0];
  }
  function light(z, on) {
    z.lit = on;
    clearTimeout(z.fading);
    z.fading = on ? 0 : setTimeout(() => { z.fading = 0; z.beam.classList.remove('is-live'); }, FADE);
    if (on && z.pool) z.pool.hidden = !(z.lamp && z.lamp.classList.contains('is-in'));   // the pendant must be on
    z.beam.classList.toggle('is-on', on);
    if (on) z.beam.classList.add('is-live');
  }
  // where the light is now (its top-left on the page): the running leg's progress, no layout involved
  function here() {
    if (!leg) return null;
    const k = leg.clock ? leg.clock.effect.getComputedTiming().progress : null;
    const f = k == null ? 1 : k;
    return [Math.round(leg.p[0] + (leg.q[0] - leg.p[0]) * f), Math.round(leg.p[1] + (leg.q[1] - leg.p[1]) * f)];
  }
  // is the cursor (viewport px) on the wall of some zone? Cached numbers only, no layout
  const onWall = (x, y) => zones.some((z) => x + sx >= z.x && x + sx < z.x + z.w && y + sy >= z.from && y + sy < z.y + z.h);
  const touches = (z, b) => b[1] + D > z.y && b[1] < z.y + z.h && b[0] + D > z.x && b[0] < z.x + z.w;

  function step() {
    legTimer = 0;
    lastLeg = performance.now();
    const on = pointer && awake && onWall(px, py);
    const target = [Math.round(px + sx - R), Math.round(py + sy - R)];
    const p = (shining && here()) || target;         // a dark lamp is switched on in the hand, it does not fly in
    const dx = target[0] - p[0]; const dy = target[1] - p[1]; const dist = Math.hypot(dx, dy);
    const q = dist > LEG ? [Math.round(p[0] + (dx * LEG) / dist), Math.round(p[1] + (dy * LEG) / dist)] : target;
    const t0 = document.timeline ? document.timeline.currentTime : null;
    let clock = null;
    shining = false;
    zones.forEach((z) => {
      const want = on && (touches(z, p) || touches(z, q));
      if (want || z.lit || z.fading) { const a = move(z, p, q, t0); clock = clock || a; }   // a fading light follows too
      if (want !== z.lit) light(z, want);
      if (want) shining = true;
    });
    leg = { p, q, clock };
    if (shining && dist > LEG) plan();   // still far behind the hand: the next leg
    else armIdle();
  }
  // plan a leg now, or as soon as GAP has passed since the last one (one timer at most)
  function plan() {
    if (legTimer || !running || !D || !TW || !TH) return;
    const wait = GAP - (performance.now() - lastLeg);
    if (wait <= 0) step(); else legTimer = setTimeout(step, wait);
  }

  /* the light goes out after IDLE ms of stillness; one timer, re-armed only after the last leg */
  function armIdle() {
    if (idleTimer || !shining) return;
    idleTimer = setTimeout(checkIdle, Math.max(40, IDLE - (performance.now() - lastMove)));
  }
  function checkIdle() {
    idleTimer = 0;
    const rest = IDLE - (performance.now() - lastMove);
    if (rest > 40) { idleTimer = setTimeout(checkIdle, rest); return; }
    awake = false;
    plan();
  }

  /* ---------- input: the handlers only store numbers, and plan a leg only when the wall is concerned ---------- */
  const fading = () => zones.some((z) => z.fading);
  function stir() {
    lastMove = performance.now();
    awake = true;
    // over the first screen, the paper sections or the form nothing is lit and nothing fades: nothing to do
    if (shining || onWall(px, py) || fading()) plan();
  }
  function onMove(e) {
    if (e.pointerType === 'touch') return;
    // browsers send a move at the same spot when the page scrolls under a still cursor: that is not the hand moving
    // (the scroll handler takes care of it), and it must not keep the light awake
    if (pointer && e.clientX === px && e.clientY === py) return;
    px = e.clientX; py = e.clientY;
    pointer = true;
    stir();
  }
  function onScroll() {
    sx = scrollX; sy = scrollY;
    if (pointer) stir();                      // the wall slides past the lamp: that is movement too
  }
  function onLeave() { pointer = false; if (shining) plan(); }
  function onOut(e) { if (!e.relatedTarget) onLeave(); }                            // out of the window
  function onOver(e) { if (e.target && e.target.tagName === 'IFRAME') onLeave(); }  // into the map: no more moves here
  function onHide() { if (document.hidden) onLeave(); }

  function start() {
    if (running) return;
    running = true;
    if (!zones.length) build();
    document.addEventListener('pointermove', onMove, { passive: true });
    document.addEventListener('pointerout', onOut, { passive: true });
    document.addEventListener('pointerover', onOver, { passive: true });
    document.addEventListener('visibilitychange', onHide);
    addEventListener('scroll', onScroll, { passive: true });
    ro = new ResizeObserver(measure);           // fires once right away, then whenever the page or a zone changes size
    ro.observe(document.body);
    zones.forEach((z) => ro.observe(z.host));
  }
  function stop() {
    if (!running) return;
    running = false;
    document.removeEventListener('pointermove', onMove);
    document.removeEventListener('pointerout', onOut);
    document.removeEventListener('pointerover', onOver);
    document.removeEventListener('visibilitychange', onHide);
    removeEventListener('scroll', onScroll);
    if (ro) { ro.disconnect(); ro = null; }
    clearTimeout(legTimer); legTimer = 0;
    clearTimeout(idleTimer); idleTimer = 0;
    pointer = false; awake = false; shining = false;
    unbuild();
  }
  const sync = () => (fineMq.matches && !calmMq.matches ? start() : stop());
  [fineMq, calmMq].forEach((mq) => { if (mq.addEventListener) mq.addEventListener('change', sync); else mq.addListener(sync); });
  sync();
})();
