// Checks that the variants and perks merged into the site work together: presence on the pages and one real
// interaction each, in Chromium and WebKit (Safari engine), on a desktop and on an iPhone profile.
//
// Playwright is not a dependency of the site; install it once in any scratch folder and run from there
// (the same folder as tools/iphone_audit.cjs):
//   mkdir -p /tmp/pw && cd /tmp/pw && npm i playwright && npx playwright install webkit chromium
//   cp <project>/tools/features_check.cjs . && node features_check.cjs
// Chromium: Playwright's headless shell, or the installed Google Chrome when that is missing (channel «chrome»).
// The site must be served on BASE (default http://localhost:5181, the «garage-2027» preview in .claude/launch.json).
// Exit code 1 when any check fails.
const { chromium, webkit, devices } = require('playwright');

const BASE = process.env.BASE || 'http://localhost:5181';
const RUNS = [
  { name: 'Chromium desktop 1440', engine: 'chromium', ctx: { viewport: { width: 1440, height: 900 } } },
  { name: 'WebKit desktop 1440', engine: 'webkit', ctx: { viewport: { width: 1440, height: 900 } } },
  { name: 'WebKit iPhone 16 Pro', engine: 'webkit', ctx: { ...devices['iPhone 16 Pro'] } },
];

let failed = 0;
const line = (ok, what, detail = '') => {
  if (!ok) failed += 1;
  console.log(`  ${ok ? 'OK  ' : 'FAIL'} ${what}${detail ? ' — ' + detail : ''}`);
};

async function launch(engine) {
  if (engine === 'webkit') return webkit.launch();
  try {
    return await chromium.launch();   // headless: Playwright's «chromium-headless-shell»
  } catch (e) {
    return chromium.launch({ channel: 'chrome' });
  }
}

// scroll an element to the upper part of the screen and give its observers and transitions time
async function show(page, sel, wait = 900) {
  await page.evaluate((s) => {
    document.documentElement.style.scrollBehavior = 'auto';
    const el = document.querySelector(s);
    scrollTo(0, el.getBoundingClientRect().top + scrollY - 90);
  }, sel);
  await page.waitForTimeout(wait);
}

async function home(page, phone) {
  await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  const has = await page.evaluate(() => ({
    svet: !!document.querySelector('.hero--svet [data-svet]'),
    lamps: document.querySelectorAll('#pribory .lamp').length,
    arches: document.querySelectorAll('#inside .arch').length,
    insideLamp: !!document.querySelector('#inside .svet-lit .svet-mini'),
    director: !!document.querySelector('.director__photo--arch'),
    stuk: !!document.querySelector('#stuk[data-stuk]'),
    zima: document.querySelectorAll('#zima .zima-item').length,
    gate: !!document.querySelector('#contacts .gate'),
    order: Array.from(document.querySelectorAll('main section[id], body > section[id], section[id]')).map((s) => s.id).join(' '),
  }));
  line(has.svet && has.lamps === 16 && has.arches === 4 && has.insideLamp && has.director && has.stuk && has.zima >= 10 && has.gate,
    'home: every block is on the page', `lamps ${has.lamps}, arches ${has.arches}, zima ${has.zima}`);
  line(/pribory advantages inside gallery team reviews stuk zima request contacts/.test(has.order), 'home: section order', has.order);

  // «Свет ламп»: every lamp off -> the dark room with the neon; any lamp brings the light back
  const lampBtns = page.locator('[data-svet-lamp] button:visible');
  const n = await lampBtns.count();
  for (let i = 0; i < n; i += 1) await lampBtns.nth(i).click();
  await page.waitForTimeout(900);
  const dark = await page.evaluate(() => document.querySelector('.hero--svet').classList.contains('is-dark'));
  await lampBtns.first().click();
  await page.waitForTimeout(400);
  const lit = await page.evaluate(() => !document.querySelector('.hero--svet').classList.contains('is-dark'));
  line(n >= 2 && dark && lit, '«Свет ламп»: lamps off -> dark room, one lamp -> light', `${n} lamps`);

  // «Что горит на панели?»: a lamp opens its card
  await show(page, '#pribory', 2200);
  await page.locator('#pribory .lamp').first().click();
  await page.waitForTimeout(500);
  const card = await page.evaluate(() => {
    const c = document.querySelector('#pribory .lamp-card.is-active');
    return c && c.dataset.lampCard ? c.querySelector('.lamp-card__title').textContent.trim() : '';
  });
  line(!!card, '«Что горит на панели?»: a lamp opens its card', card);

  // «Как у нас»: the pendant over the heading lights up, a window opens the photo
  await show(page, '#inside', 1600);
  const pendant = await page.evaluate(() => document.querySelector('#inside .svet-lit').classList.contains('is-in'));
  line(pendant, '«Арки» + «Свет ламп»: the pendant over «Как у нас» is on');
  await page.locator('#inside .arch__win').first().click();
  await page.waitForTimeout(700);
  const lb = await page.evaluate(() => { const d = document.getElementById('lightbox'); return d && d.open ? d.querySelector('img').getAttribute('src') : ''; });
  line(/\/real\/workshop(-800)?\.webp$/.test(lb), '«Арки»: a window opens the full photo', lb);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);

  // «Что стучит?»: symptom -> when -> where -> causes with links, never to the «удаление» pages
  await show(page, '#stuk', 1500);
  await page.locator('#stuk .stuk-sym').first().click();
  await page.waitForTimeout(400);
  await page.locator('#stuk [data-chips] button:visible').first().click();
  await page.waitForTimeout(400);
  const zone = page.locator('#stuk .stuk-zone:visible');
  if (await zone.count()) { await zone.first().click(); await page.waitForTimeout(400); }
  const res = await page.evaluate(() => {
    const r = document.querySelector('#stuk [data-res]');
    const links = Array.from(document.querySelectorAll('#stuk [data-res-body] a')).map((a) => a.getAttribute('href'));
    return { shown: r && !r.hidden, links };
  });
  line(res.shown && res.links.length > 0 && !res.links.some((h) => /udalen/.test(h)), '«Что стучит?»: causes with service links', `${res.links.length} links`);

  // «Готова ли машина к зиме?»: two ticks move the dial (the ticks are real checkboxes)
  await show(page, '#zima', 1500);
  await page.evaluate(() => localStorage.removeItem('garage.zima.v1'));
  const boxes = page.locator('#zima .zima-item:not([hidden]) .zima-item__input');
  await boxes.nth(0).check({ force: true });
  await boxes.nth(1).check({ force: true });
  await page.waitForTimeout(900);
  const count = await page.$eval('#zima [data-zima-count]', (e) => e.textContent);
  const miniPct = await page.$eval('#zima [data-zima-mini]', (e) => e.textContent);
  line(count === '2' || miniPct === '20', '«Зима»: ticks move the dial', `count ${count}, mini ${miniPct}%`);
  await page.locator('#zima [data-zima-reset]').click();

  // «Ворота» + «Открыто сейчас»: the live status under the address, the remote opens the gate
  await show(page, '#contacts', 1200);
  const status = await page.evaluate(() => {
    const el = document.querySelector('.gate__oc');
    return el ? { state: el.dataset.ocState || '', text: el.textContent.trim() } : null;
  });
  line(!!status && /^(open|soon|closed|note)$/.test(status.state), '«Ворота» + «Открыто сейчас»: live status in the scene', status && status.text);
  const remote = page.locator('[data-gate-toggle]');
  if (await remote.isVisible()) {
    await remote.click();
    await page.waitForTimeout(3600);
    const pct = await page.$eval('[data-gate-value]', (e) => e.textContent);
    line(pct === '100%', '«Ворота»: the remote rolls the shutter up', pct);
  } else {
    line(false, '«Ворота»: the remote is visible');
  }

  if (phone) {
    // the menu rolls down like a shutter and back up
    await page.evaluate(() => scrollTo(0, 0));
    await page.locator('.burger').tap();
    await page.waitForTimeout(700);
    const open = await page.evaluate(() => document.querySelector('#mobile-menu').classList.contains('is-open'));
    const oc = await page.evaluate(() => { const m = document.querySelector('#mobile-menu .oc-menu'); return m && m.classList.contains('is-live'); });
    await page.locator('.burger').tap();
    await page.waitForTimeout(900);
    const closed = await page.evaluate(() => getComputedStyle(document.querySelector('#mobile-menu')).display === 'none');
    line(open && oc && closed, 'menu: opens with the live status, closes', `open ${open}, status ${oc}, closed ${closed}`);
  } else {
    const top = await page.evaluate(() => { const el = document.querySelector('.topline .oc'); return el && el.classList.contains('is-live') ? el.textContent.trim() : ''; });
    line(!!top, '«Открыто сейчас»: the status in the top line', top);
  }
}

async function contacts(page) {
  await page.goto(BASE + '/contacts/', { waitUntil: 'networkidle' });
  await page.evaluate(() => document.querySelectorAll('.reveal').forEach((e) => e.classList.add('is-in')));
  const c = await page.evaluate(() => {
    const door = document.querySelector('.find .arch--door .arch__opening');
    const map = document.querySelector('.find .map');
    const r = door ? door.getBoundingClientRect() : { width: 0, height: 0 };
    return { door: [Math.round(r.width), Math.round(r.height)], map: !!map, live: document.querySelectorAll('.oc-sched.is-live').length,
             sw: document.documentElement.scrollWidth, vw: innerWidth };
  });
  line(c.door[0] > 100 && c.door[1] > 100 && c.map, '/contacts/: the arched facade beside the map', `door ${c.door.join('×')}`);
  line(c.live === 2, '/contacts/: both weeks live', `${c.live}`);
  line(c.sw <= c.vw, '/contacts/: no sideways scroll', `${c.sw} / ${c.vw}`);
}

async function neon(page) {
  // «Неон»: the 404 is the neon wall and its broken tube catches; the footer sign is dark below the fold, lit in view
  await page.goto(BASE + '/404.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(6000);   // the start-up of the broken tube (neon.css): 5 s after a 0.35 s delay
  const nf = await page.evaluate(() => {
    const s = document.querySelector('[data-neon-404]');
    return s ? { steady: s.classList.contains('is-steady'), layers: s.querySelectorAll('.neon-404__sign svg').length } : null;
  });
  line(!!nf && nf.layers === 3 && nf.steady, '«Неон»: the 404 sign burns, the broken tube has caught', nf ? `${nf.layers} layers` : 'no sign');
  await page.goto(BASE + '/oplata.html', { waitUntil: 'networkidle' });
  const before = await page.evaluate(() => { const s = document.querySelector('[data-neon-sign]'); return s ? s.className : ''; });
  await show(page, '.neon-strip', 1600);
  const after = await page.evaluate(() => {
    const s = document.querySelector('[data-neon-sign]');
    return s ? `${s.className} ${getComputedStyle(s.querySelector('.neon-sign__lit')).opacity}` : '';
  });
  line(before === 'neon-strip is-off' && after === 'neon-strip is-on 1', '«Неон»: the footer sign strikes on in view', `${before} -> ${after}`);
}

async function shiny(page) {
  await page.goto(BASE + '/services/sinomontaz.html', { waitUntil: 'networkidle' });
  const text = page.locator('[data-shiny] [data-size="b"] [data-text]');
  await text.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1200);   // shiny.js starts when the block comes near (IntersectionObserver)
  await text.fill('225/45 R17');
  await text.press('Enter');
  await page.waitForTimeout(900);
  const d = await page.evaluate(() => {
    const o = document.querySelector('[data-shiny] [data-o]');
    return { sel: ['w', 'p', 'd'].map((k) => document.querySelector(`[data-shiny] [data-size="b"] [data-part="${k}"]`).value).join('/'), out: o ? o.textContent.trim() : '' };
  });
  line(d.sel === '225/45/17' && !!d.out, '«Шинный калькулятор»: a typed size is read', `${d.sel}, ${d.out}`);
}

(async () => {
  for (const run of RUNS) {
    console.log(`=== ${run.name}`);
    const browser = await launch(run.engine);
    const ctx = await browser.newContext(run.ctx);
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    // third-party frames (the Yandex map) log their own network errors: only this site's errors count
    page.on('console', (m) => { if (m.type() === 'error' && (m.location().url || BASE).startsWith(BASE)) errors.push('console: ' + m.text() + ' ' + (m.location().url || '')); });
    page.on('requestfailed', (r) => { if (r.url().startsWith(BASE)) errors.push('failed: ' + r.url()); });
    const phone = !!run.ctx.isMobile;
    for (const step of [() => home(page, phone), () => contacts(page), () => shiny(page), () => neon(page)]) {
      try { await step(); } catch (e) { line(false, 'step crashed', e.message.split('\n')[0]); }
    }
    line(errors.length === 0, 'no errors in the console', errors.slice(0, 5).join(' | '));
    await browser.close();
  }
  console.log(failed ? `\n${failed} check(s) failed` : '\nall checks passed');
  process.exit(failed ? 1 : 0);
})();
