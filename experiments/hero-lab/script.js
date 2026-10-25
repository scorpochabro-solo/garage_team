/* Motion is transform-only, bounded and idle when nothing changes. */
(() => {
  'use strict';
  const menu = document.querySelector('.mobile-menu');
  if (menu) {
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.open) {
        menu.open = false;
        menu.querySelector('summary').focus();
      }
    });
    document.addEventListener('click', event => {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
  }

  const scene = document.querySelector('[data-parallax]');
  if (!scene) return;

  const layers = Array.from(scene.querySelectorAll('[data-depth]'), element => ({
    element,
    depth: Number(element.dataset.depth),
  }));
  const toggle = document.querySelector('[data-motion-toggle]');
  const label = document.querySelector('[data-motion-label]');
  const hint = document.querySelector('[data-motion-hint]');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)');
  let userEnabled = true;
  let visible = true;
  let frame = 0;
  let bounds = scene.getBoundingClientRect();
  let top = bounds.top + window.scrollY;
  let currentX = 0;
  let currentY = 0;
  let currentScroll = 0;
  let targetX = 0;
  let targetY = 0;
  let targetScroll = 0;
  let previousTime = 0;

  const enabled = () => userEnabled && !reduced.matches;

  function stop() {
    cancelAnimationFrame(frame);
    frame = 0;
    previousTime = 0;
  }

  function reset() {
    stop();
    currentX = currentY = currentScroll = targetX = targetY = targetScroll = 0;
    layers.forEach(({element}) => { element.style.transform = ''; });
  }

  function paint(time) {
    frame = 0;
    if (!enabled() || !visible || document.hidden) return;
    const delta = previousTime ? Math.min(time - previousTime, 50) : 16;
    previousTime = time;
    const blend = 1 - Math.exp(-delta / 110);
    currentX += (targetX - currentX) * blend;
    currentY += (targetY - currentY) * blend;
    currentScroll += (targetScroll - currentScroll) * blend;
    layers.forEach(({element, depth}) => {
      const x = currentX * depth;
      const y = (currentY + currentScroll) * depth;
      element.style.transform = `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0)`;
    });
    if (Math.abs(targetX - currentX) + Math.abs(targetY - currentY) + Math.abs(targetScroll - currentScroll) > 0.06) {
      frame = requestAnimationFrame(paint);
    } else {
      previousTime = 0;
    }
  }

  function schedule() {
    if (!frame && enabled() && visible && !document.hidden) frame = requestAnimationFrame(paint);
  }

  function onScroll() {
    if (!enabled() || !visible) return;
    targetScroll = Math.max(0, Math.min(window.scrollY - top, bounds.height)) * 0.075;
    schedule();
  }

  function measure() {
    bounds = scene.getBoundingClientRect();
    top = bounds.top + window.scrollY;
    onScroll();
  }

  function updateControls() {
    toggle.disabled = reduced.matches;
    toggle.setAttribute('aria-pressed', String(enabled()));
    label.textContent = enabled() ? 'вкл.' : 'выкл.';
    hint.textContent = reduced.matches ? 'ДВИЖЕНИЕ ОТКЛЮЧЕНО В НАСТРОЙКАХ УСТРОЙСТВА' : fine.matches ? 'ДВИГАЙТЕ КУРСОРОМ / ЛИСТАЙТЕ' : 'ЛИСТАЙТЕ — СЛОИ ДВИГАЮТСЯ';
    if (!enabled()) reset();
    else { measure(); schedule(); }
  }

  scene.addEventListener('pointermove', event => {
    if (!enabled() || !fine.matches || event.pointerType === 'touch') return;
    targetX = ((event.clientX - bounds.left) / bounds.width - 0.5) * 25;
    targetY = ((event.clientY + window.scrollY - top) / bounds.height - 0.5) * 17;
    schedule();
  }, {passive: true});
  scene.addEventListener('pointerleave', () => {
    targetX = targetY = 0;
    schedule();
  });
  toggle.addEventListener('click', () => {
    userEnabled = !userEnabled;
    updateControls();
  });
  window.addEventListener('scroll', onScroll, {passive: true});
  window.addEventListener('resize', measure, {passive: true});
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else { measure(); schedule(); }
  });
  reduced.addEventListener('change', updateControls);
  fine.addEventListener('change', updateControls);
  const observer = new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    if (visible) { measure(); schedule(); }
    else stop();
  });
  observer.observe(scene);
  updateControls();
})();
