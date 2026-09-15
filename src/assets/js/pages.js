/* ============================================================
   inner pages: services filter, tabs, registration form logic
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};

  /* ---------- services index filter ---------- */
  const filter = document.querySelector('[data-filter]');
  if (filter) {
    const cards = Array.from(document.querySelectorAll('.cat-card'));
    const countEl = document.querySelector('[data-filter-count]');
    const empty = document.querySelector('.empty-state');
    const norm = (s) => s.toLowerCase().replace(/ё/g, 'е').trim();
    const apply = () => {
      const q = norm(filter.value);
      let shown = 0;
      cards.forEach((card) => {
        const title = norm(card.dataset.title || '');
        const subs = Array.from(card.querySelectorAll('.cat-card__subs a'));
        let visibleSubs = 0;
        subs.forEach((a) => {
          const hit = !q || norm(a.textContent).includes(q) || title.includes(q);
          a.classList.toggle('is-hidden', !hit);
          if (hit) visibleSubs += 1;
        });
        const show = !q || title.includes(q) || visibleSubs > 0;
        card.classList.toggle('is-hidden', !show);
        if (show) shown += 1;
      });
      if (countEl) countEl.textContent = q ? `Найдено: ${shown}` : `${cards.length} направлений`;
      if (empty) empty.classList.toggle('is-visible', shown === 0);
    };
    filter.addEventListener('input', apply);
    const params = new URLSearchParams(location.search);
    if (params.get('q')) { filter.value = params.get('q'); }
    apply();
  }

  /* ---------- tabs ---------- */
  document.querySelectorAll('[data-tabs]').forEach((tabs) => {
    const btns = Array.from(tabs.querySelectorAll('[role=tab]'));
    const panels = btns.map((b) => document.getElementById(b.getAttribute('aria-controls')));
    const select = (i) => {
      btns.forEach((b, j) => { b.setAttribute('aria-selected', String(i === j)); b.tabIndex = i === j ? 0 : -1; });
      panels.forEach((p, j) => { if (p) p.hidden = i !== j; });
    };
    btns.forEach((b, i) => {
      b.addEventListener('click', () => select(i));
      b.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') { select((i + 1) % btns.length); btns[(i + 1) % btns.length].focus(); }
        if (e.key === 'ArrowLeft') { select((i - 1 + btns.length) % btns.length); btns[(i - 1 + btns.length) % btns.length].focus(); }
      });
    });
    select(0);
  });

  /* ---------- registration form ---------- */
  const reg = document.querySelector('[data-registration]');
  if (reg) {
    const typeInputs = Array.from(reg.querySelectorAll('input[name="RegistrationForm[type]"]'));
    const orgSection = reg.querySelector('[data-org]');
    const orgOnly = Array.from(reg.querySelectorAll('[data-org-only]'));
    const syncType = () => {
      const legal = typeInputs.some((r) => r.checked && r.value === '2');
      if (orgSection) orgSection.hidden = !legal;
      orgOnly.forEach((el) => { el.hidden = !legal; });
    };
    typeInputs.forEach((r) => r.addEventListener('change', syncType));
    syncType();
    const delivery = reg.querySelector('select[name="RegistrationForm[dostavkaType]"]');
    const point = reg.querySelector('[data-pickup]');
    const syncDelivery = () => { if (point && delivery) point.hidden = delivery.value !== 'pickup'; };
    if (delivery) { delivery.addEventListener('change', syncDelivery); syncDelivery(); }

    G.clearErrorsOnInput && G.clearErrorsOnInput(reg);
    reg.addEventListener('submit', async (e) => {
      e.preventDefault();
      let ok = true;
      Array.from(reg.querySelectorAll('[required]')).forEach((f) => {
        if (f.closest('[hidden]')) return;
        const bad = f.type === 'checkbox' ? !f.checked : !f.value.trim() || (f.dataset.phone !== undefined && !G.validPhone(f.value));
        if (bad) ok = false;
        G.setError(f, bad);
      });
      if (!ok) { G.toast('Заполните обязательные поля', 'err'); return; }
      const btn = reg.querySelector('[type=submit]');
      btn.disabled = true;
      try {
        await G.postForm(reg);
        reg.querySelector('[data-success]').classList.add('is-visible');
        Array.from(reg.children).forEach((c) => { if (!c.matches('[data-success]')) c.hidden = true; });
      } catch (err) {
        G.toast('Не удалось отправить форму. Позвоните нам: (831) 416-16-77', 'err');
      } finally { btn.disabled = false; }
    });
  }
})();
