// iPhone audit of the built site in WebKit (Safari engine) with Playwright's iPhone 16 Pro / 17 Pro Max profiles.
//
// Playwright is not a dependency of the site; install it once in any scratch folder and run from there:
//   mkdir -p /tmp/pw && cd /tmp/pw && npm i playwright && npx playwright install webkit
//   cp <project>/tools/iphone_audit.cjs . && DIST=<project>/dist node iphone_audit.cjs --all
// The site must be served on BASE (default http://localhost:5181, the «garage-2027» preview in .claude/launch.json).
//   node iphone_audit.cjs                 20 key pages, both phones, plus finger interactions (sliders, menu, modal…)
//   node iphone_audit.cjs --all           every page of dist/sitemap.xml, checks only
//   DEVICES="iPhone 16 Pro landscape,iPhone 17 Pro Max landscape" node iphone_audit.cjs --all
//   node iphone_audit.cjs --only=/,/services.html --shots     full-page screenshots
// Output: a report on stdout, JSON and screenshots in ../iphone/ next to the script.
const { webkit, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE || 'http://localhost:5181';
const OUT = path.join(__dirname, '..', 'iphone');
const SHOTS = process.argv.includes('--shots');
const onlyArg = process.argv.find((a) => a.startsWith('--only='));
const DEVICES = (process.env.DEVICES || 'iPhone 16 Pro,iPhone 17 Pro Max').split(',');
let PAGES = ['/', '/services.html', '/services/remont-dvigatela.html', '/services/remont-dvigatela/zamena-remna-grm.html',
  '/services/remont-tnvd.html', '/services/avtozapcasti.html', '/services/diagnostika/diagnostika-podveski.html',
  '/avtozapchasti/', '/cats/', '/search/', '/contacts/', '/call/request/', '/call/manager/', '/registration/',
  '/otzyvy.html', '/about/', '/oplata.html', '/delivery.html', '/page/soglashenie/', '/404.html'];
if (onlyArg) PAGES = onlyArg.slice(7).split(',');
const ALL = process.argv.includes('--all');
if (ALL) {
  const sm = fs.readFileSync(path.join(process.env.DIST || '/Users/scorpocha/рабочее/garage-2027/dist', 'sitemap.xml'), 'utf8');
  PAGES = Array.from(sm.matchAll(/<loc>https?:\/\/[^/]+([^<]*)<\/loc>/g), (m) => m[1] || '/').concat(['/404.html']);
}
fs.mkdirSync(OUT, { recursive: true });

// runs in the page: static checks
function pageChecks() {
  document.querySelectorAll('.reveal').forEach((e) => e.classList.add('is-in'));
  const vw = document.documentElement.clientWidth;
  const res = { vw, sw: document.documentElement.scrollWidth, overflow: [], small: [], tinyText: [], inputs: [], imgs: [], fixed: [] };
  const label = (el) => {
    const id = el.id ? '#' + el.id : '';
    const cls = typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
    const txt = (el.getAttribute('aria-label') || el.textContent || el.value || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    return `${el.tagName.toLowerCase()}${id}${cls} «${txt}»`;
  };
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return false;
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return false;
      if (n.tagName === 'DIALOG' && !n.open) return false;
      if (n.hidden) return false;
    }
    return true;
  };
  const clippedByAncestor = (el) => {
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      const ox = getComputedStyle(n).overflowX;
      if (ox !== 'visible') return true;
      if (getComputedStyle(n).position === 'fixed') return true;
    }
    return false;
  };
  document.querySelectorAll('body *').forEach((el) => {
    if (!visible(el)) return;
    const r = el.getBoundingClientRect();
    if ((r.right > vw + 1 || r.left < -1) && !clippedByAncestor(el) && getComputedStyle(el).position !== 'fixed') {
      res.overflow.push(`${label(el)} left=${Math.round(r.left)} right=${Math.round(r.right)}`);
    }
  });
  const ctrls = document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=tab]');
  ctrls.forEach((el) => {
    if (!visible(el)) return;
    let target = el;
    if (el.matches('input[type=checkbox], input[type=radio]')) target = el.closest('label') || el;
    if (!visible(target)) return;
    let r = target.getBoundingClientRect();
    // an invisible ::after that extends the tap area (the scheme markers) counts as part of the target
    const after = getComputedStyle(target, '::after');
    if (after.content !== 'none' && after.position === 'absolute') {
      const px = (v) => (v.endsWith('px') ? parseFloat(v) : 0);
      const w = r.width - px(after.left) - px(after.right), h = r.height - px(after.top) - px(after.bottom);
      if (w > r.width && h > r.height) r = { width: w, height: h };
    }
    const parent = el.parentElement;
    // a link that is part of a sentence: its text block holds more text than the link itself (WCAG 2.5.8 exception)
    const block = el.tagName === 'A' ? el.closest('p, li, td, dd, figcaption, blockquote, .faq__a, .svc-block__note, .field__hint, .check, .modal__lead, .intro__text, .price-block__foot span') : null;
    const squash = (t) => t.replace(/\s+/g, ' ').trim();
    const inline = !!block && block !== el && squash(block.textContent).length > squash(el.textContent).length + 3;
    // markers on the car picture: 36px by design, they can sit 29px apart (see car.css); everything else 44pt
    const min = inline ? 24 : (el.classList.contains('hotspot') ? 36 : 44);
    // WCAG 2.5.8 exempts links inside a sentence; everything else should be 44pt (Apple HIG)
    if (!inline && !el.classList.contains('sr-only') && (r.height < min - 0.5 || r.width < min - 0.5)) res.small.push(`${label(el)} ${Math.round(r.width)}×${Math.round(r.height)}`);
  });
  document.querySelectorAll('input, select, textarea').forEach((el) => {
    if (el.type === 'hidden' || el.type === 'checkbox' || el.type === 'radio') return;
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 16) res.inputs.push(`${label(el)} ${fs}px`);
  });
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  for (let t = walker.nextNode(); t; t = walker.nextNode()) {
    if (!t.textContent.trim()) continue;
    const el = t.parentElement;
    if (!el || seen.has(el) || !visible(el)) continue;
    seen.add(el);
    const fs = parseFloat(getComputedStyle(el).fontSize);
    if (fs < 11) res.tinyText.push(`${label(el)} ${fs}px`);
  }
  document.querySelectorAll('img').forEach((img) => {
    if (img.getAttribute('src') && (!img.getAttribute('width') || !img.getAttribute('height'))) res.imgs.push(`no size: ${img.getAttribute('src')}`);
  });
  document.querySelectorAll('body *').forEach((el) => {
    const cs = getComputedStyle(el);
    if ((cs.position === 'fixed' || cs.position === 'sticky') && visible(el)) {
      const r = el.getBoundingClientRect();
      res.fixed.push(`${label(el).slice(0, 50)} ${cs.position} top=${Math.round(r.top)} h=${Math.round(r.height)}`);
    }
  });
  return res;
}

async function interactions(page, device) {
  const log = [];
  const ok = (name, cond, extra = '') => log.push(`${cond ? 'OK  ' : 'FAIL'} ${name}${extra ? ' — ' + extra : ''}`);
  // sliders on the home page
  await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  for (const id of ['gallery-track', 'reviews-track']) {
    const next = page.locator(`[data-next][aria-controls="${id}"]`);
    const prev = page.locator(`[data-prev][aria-controls="${id}"]`);
    if (!(await next.count())) { ok(`slider ${id}`, false, 'no arrows with aria-controls'); continue; }
    await next.scrollIntoViewIfNeeded();
    const before = await page.$eval('#' + id, (t) => t.scrollLeft);
    const prevDisabled0 = await prev.isDisabled();
    await next.tap();
    await page.waitForTimeout(900);
    const after = await page.$eval('#' + id, (t) => t.scrollLeft);
    const prevDisabled1 = await prev.isDisabled();
    const bg = await next.evaluate((b) => getComputedStyle(b).backgroundColor);
    ok(`slider ${id}: arrow scrolls`, after > before + 10, `scrollLeft ${Math.round(before)} → ${Math.round(after)}`);
    ok(`slider ${id}: prev enabled after next`, prevDisabled0 && !prevDisabled1);
    ok(`slider ${id}: no sticky hover after tap`, !/0, 150, 61|31, 196, 99/.test(bg), `bg ${bg}`);
    await prev.tap();
    await page.waitForTimeout(900);
    const back = await page.$eval('#' + id, (t) => t.scrollLeft);
    ok(`slider ${id}: back arrow returns`, back < 5, `scrollLeft ${Math.round(back)}`);
  }
  // car scheme: tap a hotspot
  const hs = page.locator('.hotspot').first();
  if (await hs.count()) {
    await hs.scrollIntoViewIfNeeded();
    await page.waitForTimeout(600);
    const key = await hs.getAttribute('data-key');
    await hs.tap();
    await page.waitForTimeout(700);
    const readout = await page.$eval('.svc-readout', (r) => r.innerText.replace(/\s+/g, ' ').slice(0, 80)).catch(() => '');
    ok('scheme: tap on a hotspot fills the readout', readout && !/проведите|сканир/i.test(readout), readout);
    ok('scheme: first tap does not navigate', new URL(page.url()).pathname === '/', `key ${key}`);
  }
  // burger menu
  const burger = page.locator('.burger');
  if (await burger.isVisible()) {
    await page.evaluate(() => scrollTo(0, 0));
    await burger.tap();
    await page.waitForTimeout(500);
    const st = await page.evaluate(() => {
      const m = document.querySelector('#mobile-menu');
      const r = m.getBoundingClientRect();
      m.scrollTop = m.scrollHeight;
      const last = m.querySelector('.mobile-menu__cta') || m.lastElementChild;
      const lr = last.getBoundingClientRect();
      const bar = document.querySelector('.mobile-bar');
      const barTop = bar && getComputedStyle(bar).display !== 'none' ? bar.getBoundingClientRect().top : innerHeight;
      return { open: m.classList.contains('is-open'), top: r.top, h: r.height, vh: innerHeight, bodyOverflow: getComputedStyle(document.body).overflow,
               lastBottom: lr.bottom, barTop, barVisible: bar && getComputedStyle(bar).display !== 'none' && getComputedStyle(bar).visibility !== 'hidden' };
    });
    ok('menu opens', st.open);
    ok('menu locks page scroll', st.bodyOverflow === 'hidden', st.bodyOverflow);
    ok('menu end is not under the bottom bar', st.lastBottom <= st.barTop + 1, `last bottom ${Math.round(st.lastBottom)}, bar top ${Math.round(st.barTop)}, bar visible ${st.barVisible}`);
    await burger.tap();
    // the menu rolls back up like a shutter (vorota.css, 0.55 s): wait until it is gone before looking for buttons
    await page.waitForFunction(() => !document.querySelector('#mobile-menu').classList.contains('is-open')
      && getComputedStyle(document.querySelector('#mobile-menu')).display === 'none', null, { timeout: 3000 }).catch(() => {});
    await page.waitForTimeout(100);
  }
  // call-back modal
  const opener = page.locator('[data-modal="call"]:visible').first();
  if (await opener.count()) {
    await opener.tap();
    await page.waitForTimeout(600);
    const m = await page.evaluate(() => {
      const d = document.querySelector('dialog[open]');
      if (!d) return null;
      const r = d.getBoundingClientRect();
      const close = d.querySelector('[data-close], .modal__close');
      const cr = close ? close.getBoundingClientRect() : { width: 0, height: 0 };
      const html = getComputedStyle(document.documentElement).overflow;
      return { top: r.top, bottom: r.bottom, vh: innerHeight, closeW: cr.width, closeH: cr.height, htmlOverflow: html,
               inputs: Array.from(d.querySelectorAll('input:not([type=hidden]):not([type=checkbox]), textarea, select')).map((i) => parseFloat(getComputedStyle(i).fontSize)) };
    });
    ok('call modal opens', !!m);
    if (m) {
      ok('call modal fits the screen', m.top >= 0 && m.bottom <= m.vh + 1, `top ${Math.round(m.top)}, bottom ${Math.round(m.bottom)}, vh ${m.vh}`);
      ok('call modal inputs ≥ 16px (no zoom on focus)', m.inputs.every((f) => f >= 16), m.inputs.join(','));
      ok('call modal close ≥ 44px', m.closeW >= 44 && m.closeH >= 44, `${m.closeW}×${m.closeH}`);
      ok('page behind the modal does not scroll', m.htmlOverflow === 'hidden', `html overflow ${m.htmlOverflow}`);
    }
    await page.keyboard.press('Escape');
  }
  // lightbox from the gallery
  const photo = page.locator('#gallery a[data-lightbox]').first();
  if (await photo.count()) {
    await photo.scrollIntoViewIfNeeded();
    await photo.tap();
    await page.waitForTimeout(600);
    const lb = await page.evaluate(() => {
      const d = document.getElementById('lightbox');
      const btn = d.querySelector('.lightbox__btn--next').getBoundingClientRect();
      return { open: d.open, btnBottom: btn.bottom, vh: innerHeight, count: d.querySelector('.lightbox__count').textContent };
    });
    ok('lightbox opens', lb.open, lb.count);
    ok('lightbox arrows inside the screen', lb.btnBottom <= lb.vh, `bottom ${Math.round(lb.btnBottom)} / ${lb.vh}`);
    await page.locator('.lightbox__btn--next').tap();
    await page.waitForTimeout(300);
    const c2 = await page.$eval('.lightbox__count', (e) => e.textContent);
    ok('lightbox next', c2 !== lb.count, `${lb.count} → ${c2}`);
    await page.keyboard.press('Escape');
  }
  // FAQ on a service page
  await page.goto(BASE + '/services/remont-dvigatela/zamena-remna-grm.html', { waitUntil: 'networkidle' });
  const sum = page.locator('.faq summary').first();
  if (await sum.count()) {
    await sum.scrollIntoViewIfNeeded();
    await sum.tap();
    await page.waitForTimeout(300);
    ok('FAQ opens on tap', await page.$eval('.faq details', (d) => d.open));
  }
  // catalog tabs
  await page.goto(BASE + '/cats/', { waitUntil: 'networkidle' });
  const tab = page.locator('[role=tab]').nth(1);
  if (await tab.count()) {
    await tab.tap();
    await page.waitForTimeout(200);
    ok('catalog tabs switch on tap', (await tab.getAttribute('aria-selected')) === 'true');
  }
  return log;
}

(async () => {
  const browser = await webkit.launch();
  const report = {};
  for (const name of DEVICES) {
    const ctx = await browser.newContext({ ...devices[name] });
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    page.on('requestfailed', (r) => { if (r.url().startsWith(BASE)) errors.push('failed: ' + r.url()); });
    report[name] = { pages: {}, errors };
    for (const p of PAGES) {
      const resp = await page.goto(BASE + p, { waitUntil: 'networkidle' });
      // settle every entrance animation (scroll reveal, the scheme's markers) before measuring
      await page.evaluate(() => { document.querySelectorAll('.reveal').forEach((e) => e.classList.add('is-in')); document.querySelectorAll('.car-stage').forEach((e) => e.classList.add('is-ready')); });
      // the scheme's markers scale in one after another (staggered delays): give them time to reach full size
      await page.waitForTimeout((await page.$('.car-stage')) ? 3000 : 1000);
      const res = await page.evaluate(pageChecks);
      res.status = resp ? resp.status() : 0;
      report[name].pages[p] = res;
      if (SHOTS) {
        const file = path.join(OUT, `${name.replace(/\s+/g, '-')}${p.replace(/[/.]+/g, '_')}.png`);
        await page.screenshot({ path: file, fullPage: true, scale: 'css' });
      }
    }
    if (!onlyArg && !ALL && !/landscape/.test(name)) report[name].interactions = await interactions(page, name);
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 1));
  for (const [name, r] of Object.entries(report)) {
    console.log(`\n=== ${name}`);
    for (const [p, res] of Object.entries(r.pages)) {
      const issues = [...res.overflow.map((x) => 'OVERFLOW ' + x), ...res.small.map((x) => 'SMALL ' + x), ...res.inputs.map((x) => 'INPUT<16 ' + x),
        ...res.tinyText.map((x) => 'TINY ' + x), ...res.imgs.map((x) => 'IMG ' + x)];
      console.log(`${p} [${res.status}] vw=${res.vw} sw=${res.sw}${res.sw > res.vw ? ' ← HORIZONTAL SCROLL' : ''} issues=${issues.length}`);
      issues.slice(0, 40).forEach((x) => console.log('   ' + x));
      if (issues.length > 40) console.log(`   … +${issues.length - 40}`);
    }
    if (r.errors.length) { console.log('errors:'); [...new Set(r.errors)].forEach((e) => console.log('   ' + e)); }
    if (r.interactions) { console.log('interactions:'); r.interactions.forEach((x) => console.log('   ' + x)); }
  }
})().catch((e) => { console.error(e); process.exit(1); });
