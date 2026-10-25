// Run with the installed Playwright module and the shared browser cache; see README.
const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const http = require('node:http');

const origin = process.env.GARAGE_PREVIEW_ORIGIN || 'http://127.0.0.1:5183';
const here = __dirname;
const reportDir = path.resolve(here, '../../_plans/hero-lab');
const closeKeys = ['mint', 'copper', 'scarlet', 'graphite', 'vault'];
const keys = ['precision', 'afterhours', 'engineering', 'motion', 'atelier', 'ignition', 'nocturne', 'overhead', 'bay', 'closeup', ...closeKeys];
const requestedKeys = process.env.GARAGE_PREVIEW_KEYS?.split(',');
const checkedKeys = requestedKeys || keys;
assert.ok(checkedKeys.every(key => keys.includes(key)), 'Unknown preview variant');
const captureOnly = process.argv.includes('--capture');

async function settle(page) {
  // Offscreen gallery previews need to load before a complete asset audit.
  await page.evaluate(() => document.querySelectorAll('img[loading="lazy"]').forEach(image => { image.loading = 'eager'; }));
  await page.waitForFunction(() => Array.from(document.images).every(image => image.complete && image.naturalWidth > 0));
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all(Array.from(document.images, image => image.decode()));
    await Promise.all(document.getAnimations().map(animation => animation.finished));
  });
}

async function inspect(page) {
  return page.evaluate(() => {
    const title = document.querySelector('h1');
    const cta = document.querySelector('.hero .cta');
    const rect = cta.getBoundingClientRect();
    const center = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
    return {
      overflow: document.documentElement.scrollWidth > window.innerWidth,
      title: title.textContent,
      titleWidth: title.getBoundingClientRect().width,
      ctaUnobstructed: center === cta || cta.contains(center),
      ctaInView: rect.top >= 0 && rect.bottom <= window.innerHeight,
      imageLoaded: Array.from(document.querySelectorAll('.hero img')).every(image => image.naturalWidth > 0),
      mainCount: document.querySelectorAll('main').length,
      h1Count: document.querySelectorAll('h1').length,
      dockItems: document.querySelectorAll('.lab-dock a').length,
    };
  });
}

async function checkDarkControls(page, key) {
  if (key === 'ignition') {
    const control = page.getByRole('button', {name:/Свет фар/});
    await control.click();
    await settle(page);
    assert.equal(await page.locator('.headlamp').first().evaluate(el => getComputedStyle(el).opacity), '0');
    await control.press('Enter');
    await settle(page);
    assert.equal(await page.locator('.headlamp').first().evaluate(el => getComputedStyle(el).opacity), '1');
  } else if (key === 'nocturne') {
    const before = await page.locator('.nocturne-wash').evaluate(el => getComputedStyle(el).backgroundImage);
    await page.getByRole('button', {name:'Холодный',exact:true}).click();
    assert.notEqual(await page.locator('.nocturne-wash').evaluate(el => getComputedStyle(el).backgroundImage), before);
    assert.equal(await page.locator('[data-tone][aria-pressed="true"]').count(), 1);
    await page.getByRole('button', {name:'Тёплый',exact:true}).press('Enter');
  } else if (key === 'overhead') {
    for (const [name, title] of [['Ходовая','Чувствовать дорогу.'],['Обслуживание','Заботиться вовремя.'],['Двигатель','Начать с причины.']]) {
      await page.getByRole('button', {name:new RegExp(name)}).click();
      assert.equal(await page.locator('[data-point-title]').textContent(), title);
      assert.equal(await page.locator('[data-car-point][aria-pressed="true"]').count(), 1);
    }
  } else if (key === 'bay') {
    const button = page.getByRole('button', {name:'Закрыть бокс',exact:true});
    await button.click();
    await settle(page);
    assert.equal(await page.locator('.bay-shutter').evaluate(el => new DOMMatrix(getComputedStyle(el).transform).m42), 0);
    await page.getByRole('button', {name:'Открыть бокс',exact:true}).press('Enter');
    await settle(page);
    assert.ok(await page.locator('.bay-shutter').evaluate(el => new DOMMatrix(getComputedStyle(el).transform).m42 < -100));
  } else if (key === 'closeup') {
    const slider = page.getByRole('slider', {name:'Положение света на автомобиле'});
    const before = await page.locator('.detail-spot').evaluate(el => getComputedStyle(el).backgroundImage);
    await slider.focus();
    await slider.press('Home');
    assert.equal(await slider.inputValue(), '15');
    assert.notEqual(await page.locator('.detail-spot').evaluate(el => getComputedStyle(el).backgroundImage), before);
    await slider.press('End');
    assert.equal(await slider.inputValue(), '95');
  }
}

(async () => {
  await fs.mkdir(reportDir, {recursive: true});
  const browser = await chromium.launch({headless: true});
  const results = [];
  const errors = [];
  try {
    for (const viewport of [{width:1440,height:1000}, {width:1280,height:720}, {width:1366,height:768}, {width:393,height:852}, {width:375,height:812}, {width:844,height:390}, {width:1024,height:900}]) {
      if (captureOnly && viewport.width !== 1440 && viewport.width !== 393) continue;
      const context = await browser.newContext({viewport, deviceScaleFactor:1, reducedMotion:'no-preference', isMobile:viewport.width < 700, hasTouch:viewport.width < 700});
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      for (const key of checkedKeys) {
        await page.goto(`${origin}/hero-lab/${key}.html`, {waitUntil:'networkidle'});
        await settle(page);
        const state = await inspect(page);
        assert.equal(state.overflow, false, `${key}/${viewport.width}: horizontal overflow`);
        assert.equal(state.imageLoaded, true, `${key}: image missing`);
        assert.equal(state.mainCount, 1);
        assert.equal(state.h1Count, 1);
        assert.equal(state.dockItems, 6);
        if (closeKeys.includes(key)) {
          const text = await page.locator('.close-scene').innerText();
          assert.equal(text.replace(/\s+/g,' ').trim(), 'Сервис премиальных автомобилей. Записаться Нижний Новгород Красная слобода, 9 ↗', `${key}: hero copy budget`);
          assert.equal(await page.locator('.header .header-request').count(), 0, 'No duplicated booking action');
          const dock = await page.locator('.lab-dock').boundingBox();
          assert.ok(dock.y >= viewport.height, 'Variant navigation stays outside the hero');
          const headingFits = await page.locator('.close-copy h1 span').evaluateAll(spans => spans.every(span => {
            const rect = span.getBoundingClientRect();
            return rect.left >= 0 && rect.right <= innerWidth && span.scrollWidth <= span.clientWidth + 1;
          }));
          assert.equal(headingFits, true, `${key}/${viewport.width}: clipped headline`);
        }
        if (viewport.height > 700) {
          assert.equal(state.ctaUnobstructed, true, `${key}/${viewport.width}: blocked primary CTA`);
          assert.equal(state.ctaInView, true, `${key}/${viewport.width}: primary CTA below the fold`);
        }
        results.push({key,viewport,...state});
        if (viewport.width === 1440 || viewport.width === 393 || viewport.width === 1280) {
          await page.screenshot({path:path.join(reportDir, `${key}-${viewport.width}.jpg`),type:'jpeg',quality:88});
          if (viewport.width === 1440) await page.screenshot({path:path.join(here, 'assets', `thumb-${key}.jpg`),type:'jpeg',quality:75});
        }
        if (viewport.width === 393 && !captureOnly) {
          await checkDarkControls(page, key);
          await page.locator('.mobile-menu summary').click();
          assert.equal(await page.locator('.mobile-menu').getAttribute('open'), '');
          await page.keyboard.press('Escape');
          assert.equal(await page.locator('.mobile-menu').getAttribute('open'), null);
        }
      }
      await context.close();
    }

    if (!captureOnly) {
      const context = await browser.newContext({viewport:{width:1440,height:1000}});
      const page = await context.newPage();
      page.on('pageerror', error => errors.push(error.message));
      const movingImages = {
        precision:'.precision-car', afterhours:'.cinema-image',
        engineering:'.profile-car', motion:'.motion-image', atelier:'.atelier-car',
        ignition:'.ignition-car', nocturne:'.nocturne-car', overhead:'.overhead-stage', bay:'.bay-car', closeup:'.detail-stage',
        ...Object.fromEntries(closeKeys.map(key => [key, '.close-media'])),
      };
      for (const key of checkedKeys) {
        await page.emulateMedia({reducedMotion:'no-preference'});
        await page.goto(`${origin}/hero-lab/${key}.html`);
        await settle(page);
        const selector = movingImages[key];
        const ctaBefore = await page.locator('.hero .cta').boundingBox();
        await page.mouse.move(1200,400);
        await page.waitForFunction(selector => Math.abs(new DOMMatrix(getComputedStyle(document.querySelector(selector)).transform).m41) > 4, selector);
        const depth = await page.locator('[data-depth]').evaluateAll(elements => elements.map(element => ({
          factor:Number(element.dataset.depth),
          x:Math.abs(new DOMMatrix(getComputedStyle(element).transform).m41),
        })).sort((a,b) => a.factor - b.factor));
        for (let i=1; i<depth.length; i++) assert.ok(depth[i].x > depth[i-1].x, `${key}: layers must move at different depths`);
        if (key !== 'atelier') assert.deepEqual(await page.locator('.hero .cta').boundingBox(), ctaBefore, `${key}: primary action should remain still`);
        if (key === 'precision') assert.equal(await page.locator('.hero').innerText().then(text => /01 \/ ALPINA|ХАРАКТЕР В КАЖДОЙ ЛИНИИ/.test(text)), false);
        if (key === 'engineering') assert.equal(await page.locator('.hero').innerText().then(text => /ALPINA B3|ФОРМА \/ ФУНКЦИЯ/.test(text)), false);
        if (key === 'afterhours') {
          assert.equal(await page.locator('.hero .status-dot').count(), 0);
          const fonts = await page.locator('.cinema-coordinate, .hero .eyebrow, .cinema-bottom>p').evaluateAll(elements => elements.map(element => getComputedStyle(element).fontFamily));
          assert.ok(fonts.length === 3 && fonts.every(font => font.includes('Manrope') && !font.includes('Mono')), 'After Hours labels must use the new sans serif');
          assert.match(await page.locator('.cinema-image img').getAttribute('alt'), /Touring/);
        }
        await checkDarkControls(page, key);
        await page.getByRole('button', {name:/Параллакс/}).click();
        await page.mouse.move(900,300);
        assert.equal(await page.locator('[data-motion-toggle]').getAttribute('aria-pressed'), 'false');
        assert.equal(await page.locator(selector).evaluate(element=>getComputedStyle(element).transform),'none');
        await page.getByRole('button', {name:/Параллакс/}).click();
        await page.mouse.move(0,0);
        await page.evaluate(() => window.scrollTo({top:350,behavior:'instant'}));
        await page.waitForFunction(selector => {
          const layer = document.querySelector(selector);
          return new DOMMatrix(getComputedStyle(layer).transform).m42 > 12 * Number(layer.dataset.depth);
        }, selector);
        await page.emulateMedia({reducedMotion:'reduce'});
        // A screenshot flushes Chromium's emulated media change into a rendered frame.
        await page.screenshot({path:path.join(reportDir,`reduced-motion-${key}.jpg`),type:'jpeg',quality:75});
        await page.waitForFunction(() => document.querySelector('[data-motion-toggle]').disabled);
        assert.equal(await page.locator(selector).evaluate(element=>getComputedStyle(element).transform),'none');
        assert.equal(await page.evaluate(()=>document.getAnimations().length),0);
        results.push({key,parallax:'pointer + scroll + layer depths + off switch + reduced motion passed'});
      }
      await page.goto(`${origin}/hero-lab/`);
      await settle(page);
      assert.equal(await page.locator('.study-card').count(),23);
      await page.locator('.study-card--mint').click();
      await page.waitForURL('**/mint.html');
      await page.locator('.lab-dock a[href="vault.html"]').click();
      await page.waitForURL('**/vault.html');
      await page.getByRole('link', {name:'Все варианты',exact:true}).click();
      await page.waitForURL('**/index.html');
      await page.locator('.study-card--ignition').click();
      await page.waitForURL('**/ignition.html');
      await page.locator('.lab-dock a[href="closeup.html"]').click();
      await page.waitForURL('**/closeup.html');
      await page.getByRole('link', {name:'Все варианты',exact:true}).click();
      await page.waitForURL('**/index.html');
      await page.locator('.study-card--precision').click();
      await page.waitForURL('**/precision.html');
      await page.locator('.lab-dock a[href="motion.html"]').click();
      await page.waitForURL('**/motion.html');
      await page.locator('.hero .cta').click();
      await page.waitForURL('**/call/request/');
      assert.ok((await page.title()).length > 0);
      await context.close();
      for (const route of ['/','/about/','/contacts/','/services.html','/call/request/','/moya-mashina/']) {
        const status = await new Promise((resolve, reject) => {
          const request = http.get(origin + route, response => {
            response.resume();
            response.on('end', () => resolve(response.statusCode));
            response.on('error', reject);
          });
          request.setTimeout(5000, () => request.destroy(new Error(`Timed out: ${route}`)));
          request.on('error', reject);
        });
        assert.equal(status,200,`Broken destination ${route}`);
      }
    }
    assert.deepEqual(errors,[],'Browser errors');
    await fs.writeFile(path.join(reportDir,'verification.json'),JSON.stringify({results,errors},null,2));
    console.log(`PASS: ${results.length} checks; screenshots in ${reportDir}`);
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode=1;});
