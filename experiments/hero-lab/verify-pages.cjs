const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const origin = process.env.GARAGE_PREVIEW_ORIGIN || 'http://127.0.0.1:5183';
const keys = ['mint-film','mint-grid','mint-chapters','mint-editorial','mint-workshop','copper-panorama','copper-sequence','copper-collection'];
const selected = process.env.GARAGE_PREVIEW_KEYS?.split(',') || keys;
assert.ok(selected.every(key => keys.includes(key)));
const capture = process.argv.includes('--capture');
const report = path.resolve(__dirname,'../../_plans/hero-lab/pages');

async function ready(page) {
  await page.evaluate(() => document.querySelectorAll('img').forEach(img => {img.loading='eager';}));
  await page.waitForFunction(() => [...document.images].every(img => img.complete && img.naturalWidth));
  await page.evaluate(() => document.fonts.ready);
}

(async () => {
  await fs.mkdir(report,{recursive:true});
  const browser = await chromium.launch({headless:true});
  const errors = [], results = [];
  try {
    for (const viewport of [{width:1440,height:1000},{width:1280,height:720},{width:1024,height:900},{width:768,height:1024},{width:393,height:852},{width:375,height:812},{width:844,height:390}]) {
      if(capture && ![1440,393].includes(viewport.width)) continue;
      const page = await browser.newPage({viewport,isMobile:viewport.width<700,hasTouch:viewport.width<700});
      page.on('pageerror',error => errors.push(error.message));
      for (const key of selected) {
        await page.goto(`${origin}/hero-lab/${key}.html`,{waitUntil:'networkidle'});
        await ready(page);
        assert.equal(await page.locator('main>section').count(),4,`${key}: hero and exactly three sections`);
        assert.equal(await page.locator('h1').count(),1);
        assert.equal(await page.locator(key.startsWith('copper-')?'.close-copper':'.close-mint').count(),1,`${key}: chosen hero`);
        const layout = await page.evaluate(() => ({
          overflow:document.documentElement.scrollWidth>innerWidth,
          sections:[...document.querySelectorAll('.page-section')].map(section => ({
            id:section.id,
            image:[...section.querySelectorAll('.fragment img')].some(img=>img.complete && img.naturalWidth>0),
            textFits:[...section.querySelectorAll('h2,p,.service-lines>a,.service-choice,.editorial-service>span,.service-tile>span,.workshop-window>span,.collection-card>span')].every(el=>{
              const r=el.getBoundingClientRect();
              return r.left>=-1 && r.right<=innerWidth+1 && el.scrollWidth<=el.clientWidth+2;
            })
          }))
        }));
        assert.equal(layout.overflow,false,`${key}/${viewport.width}: overflow`);
        for(const section of layout.sections){
          assert.equal(section.image,true,`${key}/${section.id}: generated fragment`);
          assert.equal(section.textFits,true,`${key}/${viewport.width}/${section.id}: clipped text`);
          await page.locator('#'+section.id).scrollIntoViewIfNeeded();
          const links=page.locator('#'+section.id+' a');
          for(let i=0;i<await links.count();i++){
            const link=links.nth(i);
            await link.scrollIntoViewIfNeeded();
            assert.ok(await link.evaluate(el=>{
              const r=el.getBoundingClientRect();
              const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
              return hit===el || el.contains(hit);
            }),`${key}/${section.id}: blocked link`);
          }
        }
        if([1440,393].includes(viewport.width)){
          await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
          await page.screenshot({path:path.join(report,`${key}-${viewport.width}-full.jpg`),type:'jpeg',quality:85,fullPage:true});
          for(const id of ['services','approach','visit']){
            await page.locator('#'+id).screenshot({path:path.join(report,`${key}-${viewport.width}-${id}.jpg`),type:'jpeg',quality:85});
          }
          if(viewport.width===1440){
            await page.evaluate(()=>scrollTo({top:document.querySelector('#services').offsetTop,behavior:'instant'}));
            await page.screenshot({path:path.join(__dirname,'assets',`thumb-${key}.jpg`),type:'jpeg',quality:78});
          }
        }
        if(!capture && viewport.width===393){
          await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));
          await page.locator('.mobile-menu summary').click();
          await page.locator('.mobile-menu a[href="#services"]').click();
          assert.equal(await page.locator('.mobile-menu').getAttribute('open'),null);
          assert.equal(new URL(page.url()).hash,'#services');
        }
        if(key==='mint-chapters' || key==='copper-sequence'){
          const choice=page.getByRole('button',{name:'Плановое ТО',exact:true});
          await choice.focus(); await choice.press('Enter');
          assert.equal(await choice.getAttribute('aria-pressed'),'true');
          assert.match(await page.locator('#service-detail img').getAttribute('src'),/page-wheel/);
          assert.ok((await page.locator('[data-service-link]').getAttribute('href')).endsWith('/services/planovoe-to.html'));
          assert.equal(await page.locator('.service-choice[aria-pressed=true]').count(),1);
        }
        results.push({key,viewport,layout:'passed'});
      }
      await page.close();
    }
    if(!capture){
      const page=await browser.newPage({viewport:{width:1440,height:1000}});
      page.on('pageerror',error=>errors.push(error.message));
      for(const key of selected){
        await page.emulateMedia({reducedMotion:'no-preference'});
        await page.goto(`${origin}/hero-lab/${key}.html`);
        await ready(page);
        await page.mouse.move(1250,400);
        await page.waitForFunction(()=>Math.abs(new DOMMatrix(getComputedStyle(document.querySelector('.close-media')).transform).m41)>4);
        await page.evaluate(()=>scrollTo({top:document.querySelector('#services').offsetTop+180,behavior:'instant'}));
        await page.waitForFunction(()=>[...document.querySelectorAll('[data-drift]')].some(el=>Math.abs(parseFloat(el.style.getPropertyValue('--drift')))>1));
        await page.locator('[data-motion-toggle]').click();
        await page.waitForFunction(()=>[...document.querySelectorAll('[data-drift]')].every(el=>!el.style.getPropertyValue('--drift')));
        await page.locator('[data-motion-toggle]').click();
        await page.emulateMedia({reducedMotion:'reduce'});
        await page.screenshot({path:path.join(report,`${key}-reduced.jpg`),type:'jpeg'});
        await page.waitForFunction(()=>document.querySelector('[data-motion-toggle]').disabled);
        assert.ok(await page.locator('[data-drift] img').evaluateAll(images=>images.every(img=>getComputedStyle(img).transform==='none')));
        await page.locator('#visit .cta').click();
        await page.waitForURL('**/call/request/');
        results.push({key,interaction:'parallax, reduced motion and booking passed'});
      }
      await page.goto(`${origin}/hero-lab/pages.html`);
      await ready(page);
      assert.equal(await page.locator('.page-study-card').count(),8);
      await page.locator('.page-study-card[href="mint-film.html"]').click();
      await page.waitForURL('**/mint-film.html');
      await page.locator('.page-dock a[href="mint-workshop.html"]').click();
      await page.waitForURL('**/mint-workshop.html');
      await page.getByRole('link',{name:'Все варианты страницы',exact:true}).click();
      await page.waitForURL('**/pages.html');
      await page.close();
    }
    assert.deepEqual(errors,[]);
    await fs.writeFile(path.join(report,capture?'capture.json':'verification.json'),JSON.stringify({results,errors},null,2));
    console.log(`PASS: ${results.length} page checks; screenshots: ${report}`);
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
