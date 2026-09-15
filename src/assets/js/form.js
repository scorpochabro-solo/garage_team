/* ============================================================
   request form (3 steps), callback modal, login modal
   Backend endpoints are the same as on the current garage.team:
   POST /call/request, POST /call, POST /findcar/requestmodels/id/<brand>,
   POST /findcar/requestsizes/, POST /login/popup, /email/lostpass, /sms/lostpass
   ============================================================ */
(() => {
  'use strict';
  const G = window.G || {};
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  const required = (fields) => {
    let ok = true;
    fields.forEach((f) => {
      if (!f || f.closest('[hidden]') || f.disabled) return;
      let bad;
      if (f.type === 'checkbox') bad = !f.checked;
      else if (f.tagName === 'SELECT') bad = !f.value || f.value === '-1';
      else if (f.dataset.phone !== undefined) bad = !G.validPhone(f.value);
      else bad = !f.value.trim();
      if (bad) ok = false;
      G.setError(f, bad);
    });
    return ok;
  };

  const fill = (select, placeholder, rows) => {
    select.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '-1'; opt.textContent = placeholder;
    select.appendChild(opt);
    rows.forEach((r) => { const o = document.createElement('option'); o.value = String(r.id); o.textContent = r.name; select.appendChild(o); });
    select.disabled = false;
  };

  const postJSON = async (url, params) => {
    const res = await fetch(url, { method: 'POST', body: params ? new URLSearchParams(params) : undefined, headers: { 'X-Requested-With': 'XMLHttpRequest', Accept: 'application/json' }, credentials: 'same-origin' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    return res.json();
  };

  /* ---------- request form ---------- */
  $$('[data-rq]').forEach((form) => {
    const steps = $$('.step', form);
    const panels = $$('.rq__panel', form);
    const modeInput = $('input[name="request_part[select_car_type]"]', form);
    const selectMode = $('[data-mode="select"]', form);
    const textMode = $('[data-mode="text"]', form);
    const brand = $('#tecdoc_car_brand', form);
    const model = $('#tecdoc_car_model', form);
    const year = $('#tecdoc_car_year', form);
    const type = $('#tecdoc_car_type', form);
    const alertBox = $('[data-alert]', form);
    const success = $('[data-success]', form);
    let models = {};
    let current = 1;

    G.clearErrorsOnInput(form);

    const show = (n) => {
      current = n;
      panels.forEach((p) => p.classList.toggle('is-active', Number(p.dataset.panel) === n));
      steps.forEach((s) => {
        const i = Number(s.dataset.step);
        s.classList.toggle('is-active', i === n);
        s.classList.toggle('is-done', i < n);
      });
      if (n > 1) form.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'start' });
      const first = $(`.rq__panel[data-panel="${n}"] input:not([type=hidden]):not([disabled]), .rq__panel[data-panel="${n}"] select:not([disabled])`, form);
      if (first && n > 1) setTimeout(() => first.focus(), 350);
    };

    /* car selection mode toggle */
    const setMode = (mode, note) => {
      const isSelect = mode === 'select';
      if (modeInput) modeInput.value = isSelect ? '1' : '0';
      if (selectMode) selectMode.hidden = !isSelect;
      if (textMode) textMode.hidden = isSelect;
      $$('[data-mode-toggle]', form).forEach((b) => { b.textContent = isSelect ? 'Не нашли свой автомобиль?' : 'Выбрать из списка'; });
      if (note) G.toast(note, 'err');
    };
    $$('[data-mode-toggle]', form).forEach((b) => b.addEventListener('click', () => setMode(modeInput && modeInput.value === '1' ? 'text' : 'select')));

    /* dependent selects (backend of garage.team) */
    if (brand && model && year && type) {
      brand.addEventListener('change', async () => {
        fill(model, 'Выберите модель', []); model.disabled = true;
        fill(year, 'Выберите год', []); year.disabled = true;
        fill(type, 'Выберите модификацию', []); type.disabled = true;
        if (brand.value === '-1') return;
        try {
          const json = await postJSON('/findcar/requestmodels/id/' + encodeURIComponent(brand.value));
          const rows = (json && json.data) || [];
          models = {};
          rows.forEach((r) => { models[r.id] = r; });
          fill(model, 'Выберите модель', rows);
          model.focus();
        } catch (_) {
          setMode('text', 'Список моделей сейчас недоступен — укажите автомобиль вручную');
        }
      });
      model.addEventListener('change', () => {
        fill(year, 'Выберите год', []); year.disabled = true;
        fill(type, 'Выберите модификацию', []); type.disabled = true;
        const m = models[model.value];
        if (!m) return;
        const now = new Date().getFullYear();
        const start = Number(m.year_start) || now - 30;
        const end = Number(m.year_end) || now;
        const rows = [];
        for (let y = end; y >= start; y -= 1) rows.push({ id: y, name: String(y) });
        fill(year, 'Выберите год', rows);
        year.focus();
      });
      year.addEventListener('change', async () => {
        fill(type, 'Выберите модификацию', []); type.disabled = true;
        if (year.value === '-1') return;
        try {
          const json = await postJSON('/findcar/requestsizes/', { id: model.value, year: year.value });
          fill(type, 'Выберите модификацию', (json && json.data) || []);
        } catch (_) { type.disabled = true; }
      });
    }

    /* VIN helper */
    $$('[data-vin-help]', form).forEach((b) => b.addEventListener('click', () => {
      const box = $('[data-vin-help-text]', form);
      if (box) box.hidden = !box.hidden;
    }));

    /* parts list */
    const partsBox = $('[data-parts]', form);
    const addPart = () => {
      const n = $$('.part', partsBox).length + 1;
      const row = document.createElement('div');
      row.className = 'part';
      row.innerHTML = `
        <div class="field"><label class="field__label" for="part_name_${n}">Запчасть №${n}</label><input class="input" id="part_name_${n}" name="request_part[parts][${n}][name]" type="text" placeholder="Например: противотуманные фары"></div>
        <div class="field"><label class="field__label" for="part_count_${n}">Кол-во, шт.</label><input class="input" id="part_count_${n}" name="request_part[parts][${n}][count]" type="number" min="1" value="1"></div>
        <button type="button" class="part__remove" aria-label="Удалить запчасть"><svg class="ic" aria-hidden="true"><use href="#i-close"/></svg></button>`;
      partsBox.appendChild(row);
      $('input', row).focus();
    };
    if (partsBox) {
      $$('[data-add-part]', form).forEach((b) => b.addEventListener('click', addPart));
      partsBox.addEventListener('click', (e) => {
        const btn = e.target.closest('.part__remove');
        if (!btn) return;
        if ($$('.part', partsBox).length <= 1) return;
        btn.closest('.part').remove();
        $$('.part', partsBox).forEach((row, i) => {
          const n = i + 1;
          row.querySelector('label').textContent = `Запчасть №${n}`;
          row.querySelector('input[type=text]').name = `request_part[parts][${n}][name]`;
          row.querySelector('input[type=number]').name = `request_part[parts][${n}][count]`;
        });
      });
    }

    /* step validation */
    const validateStep = (n) => {
      if (n === 1) {
        const isSelect = !modeInput || modeInput.value === '1';
        return isSelect
          ? required([brand, model, year])
          : required([$('#text_car_brand', form), $('#text_car_model', form), $('#text_car_year', form), $('#text_car_type', form)]);
      }
      if (n === 2) {
        const first = $('.part input[type=text]', form);
        const filled = $$('.part input[type=text]', form).some((i) => i.value.trim());
        const comment = $('[name="request_part[what]"]', form);
        const ok = filled || (comment && comment.value.trim());
        if (first) G.setError(first, !ok);
        return !!ok;
      }
      if (n === 3) {
        return required([$('[name="request_part[contact_name]"]', form), $('[name="request_part[city]"]', form), $('[name="request_part[contact_phone]"]', form), $('[name="agree"]', form)]);
      }
      return true;
    };

    $$('[data-next]', form).forEach((b) => b.addEventListener('click', () => {
      if (!validateStep(current)) { G.toast('Заполните обязательные поля', 'err'); return; }
      show(Math.min(3, current + 1));
    }));
    $$('[data-prev]', form).forEach((b) => b.addEventListener('click', () => show(Math.max(1, current - 1))));
    steps.forEach((s) => s.addEventListener('click', () => { const n = Number(s.dataset.step); if (n < current) show(n); }));

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!validateStep(3)) { G.toast('Заполните обязательные поля', 'err'); return; }
      const btn = $('[type=submit]', form);
      btn.disabled = true; btn.classList.add('is-loading');
      if (alertBox) alertBox.classList.remove('is-visible');
      try {
        await G.postForm(form);
        panels.forEach((p) => p.classList.remove('is-active'));
        $('.steps', form).hidden = true;
        if (success) success.classList.add('is-visible');
        form.scrollIntoView({ behavior: G.reducedMotion ? 'auto' : 'smooth', block: 'center' });
      } catch (err) {
        if (alertBox) {
          alertBox.textContent = 'Не удалось отправить заявку. Позвоните нам: (831) 416-16-77 — менеджер примет запрос по телефону.';
          alertBox.classList.add('is-visible');
        }
        G.toast('Ошибка отправки. Позвоните: (831) 416-16-77', 'err');
      } finally { btn.disabled = false; btn.classList.remove('is-loading'); }
    });
    show(1);
  });

  /* ---------- simple modal forms (callback, login, lost password) ---------- */
  $$('form[data-simple-form]').forEach((form) => {
    G.clearErrorsOnInput(form);
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fields = $$('[required]', form);
      if (!required(fields)) { G.toast('Заполните обязательные поля', 'err'); return; }
      const btn = $('[type=submit]', form);
      if (btn) btn.disabled = true;
      try {
        const data = await G.postForm(form);
        const succ = $('[data-success]', form);
        if (form.dataset.redirect && data && data.redirect) { location.href = data.redirect; return; }
        if (succ) { $$('[data-body]', form).forEach((b) => { b.hidden = true; }); succ.classList.add('is-visible'); }
        else { G.toast(form.dataset.successText || 'Отправлено', 'ok'); const dlg = form.closest('dialog'); if (dlg) G.closeModal(dlg); }
      } catch (err) {
        G.toast(form.dataset.errorText || 'Не удалось отправить. Позвоните: (831) 416-16-77', 'err');
      } finally { if (btn) btn.disabled = false; }
    });
  });

  /* login modal: forgot password toggle */
  const login = $('#modal-login');
  if (login) {
    const lost = $('[data-lost]', login);
    $$('[data-lost-toggle]', login).forEach((b) => b.addEventListener('click', () => { if (lost) lost.hidden = !lost.hidden; }));
    const sms = $('[data-sms]', login);
    if (sms) sms.addEventListener('click', async () => {
      const area = $('input[name="UserLoginForm[areaCode]"]', login);
      const num = $('input[name="UserLoginForm[number]"]', login);
      const phone = ((area && area.value) || '') + ((num && num.value) || '');
      if (!/^9\d{9}$/.test(phone)) { G.setError(num, true); G.toast('Введите номер телефона в формате 9XXXXXXXXX', 'err'); return; }
      try { await postJSON('/sms/lostpass', { phone }); G.toast('Пароль отправлен по СМС', 'ok'); }
      catch (_) { G.toast('Не удалось отправить СМС. Позвоните: (831) 416-16-77', 'err'); }
    });
    const emailBtn = $('[data-email-lost]', login);
    if (emailBtn) emailBtn.addEventListener('click', async () => {
      const email = $('input[name="lost-email"]', login);
      if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value)) { if (email) G.setError(email, true); G.toast('Введите корректный e-mail', 'err'); return; }
      try { await postJSON('/email/lostpass', { email: email.value }); G.toast('Пароль отправлен на e-mail', 'ok'); }
      catch (_) { G.toast('Не удалось отправить письмо. Позвоните: (831) 416-16-77', 'err'); }
    });
  }

  /* dialogs: reset simple forms on close */
  $$('dialog').forEach((d) => d.addEventListener('close', () => {
    $$('form[data-simple-form]', d).forEach((f) => { f.reset(); $$('[data-body]', f).forEach((b) => { b.hidden = false; }); const s = $('[data-success]', f); if (s) s.classList.remove('is-visible'); $$('.field', f).forEach((x) => x.classList.remove('is-error')); });
  }));
})();
