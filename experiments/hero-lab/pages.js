/* Purposeful service selection and bounded scroll depth, without a scroll hijack. */
(() => {
  'use strict';
  document.querySelectorAll('.mobile-menu a[href^="#"]').forEach(link => link.addEventListener('click', () => {
    link.closest('details').open = false;
  }));
  const selection = document.querySelector('.service-choices');
  if (selection) {
    const image = document.querySelector('#service-detail img');
    const description = document.querySelector('[data-service-description-output]');
    const link = document.querySelector('[data-service-link]');
    selection.addEventListener('click', event => {
      const button = event.target.closest('.service-choice');
      if (!button) return;
      selection.querySelectorAll('button').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      image.src = button.dataset.serviceImage;
      image.alt = button.dataset.serviceAlt;
      description.textContent = button.dataset.serviceDescription;
      link.href = button.dataset.serviceUrl;
      link.setAttribute('aria-label', `Подробнее: ${button.dataset.serviceName}`);
    });
  }

  const fragments = Array.from(document.querySelectorAll('[data-drift]'));
  if (!fragments.length) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const toggle = document.querySelector('[data-motion-toggle]');
  const visible = new Set();
  let frame = 0;
  const enabled = () => !reduced.matches && toggle.getAttribute('aria-pressed') === 'true';
  function paint() {
    frame = 0;
    if (!enabled() || document.hidden) return;
    // Read all geometry first, then write transforms once per scrolling frame.
    const positions = Array.from(visible, element => {
      const rect = element.getBoundingClientRect();
      return [element, Math.max(-22, Math.min(22, (innerHeight / 2 - rect.top - rect.height / 2) * .055))];
    });
    positions.forEach(([element, y]) => element.style.setProperty('--drift', `${y.toFixed(2)}px`));
  }
  function schedule() {
    if (!frame && enabled() && !document.hidden) frame = requestAnimationFrame(paint);
  }
  function reset() {
    cancelAnimationFrame(frame);
    frame = 0;
    fragments.forEach(element => element.style.removeProperty('--drift'));
    schedule();
  }
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => entry.isIntersecting ? visible.add(entry.target) : visible.delete(entry.target));
    schedule();
  });
  fragments.forEach(element => observer.observe(element));
  window.addEventListener('scroll', schedule, {passive:true});
  window.addEventListener('resize', schedule, {passive:true});
  document.addEventListener('visibilitychange', () => document.hidden ? reset() : schedule());
  reduced.addEventListener('change', reset);
  new MutationObserver(reset).observe(toggle, {attributes:true, attributeFilter:['aria-pressed']});
})();
