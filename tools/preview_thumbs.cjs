// Thumbnails for the preview index (tools/preview_variants.py): one 1440×900 screenshot of every card, opened at its
// «open» page and anchor, saved as <out>/v/thumbs/<key>.png; preview_variants.py turns them into 960×600 webp.
//
// Playwright is not a dependency of the site; run from the folder where it is installed (see tools/iphone_audit.cjs):
//   node preview_thumbs.cjs <project>/_preview/manifest.json [--only=key,key]
// The preview must be served: PREVIEW=http://localhost:5182 (default), the folder of the manifest is its root.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const manifestPath = process.argv[2];
if (!manifestPath) { console.error('usage: node preview_thumbs.cjs <manifest.json> [--only=a,b]'); process.exit(2); }
const man = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const base = '/' + (man.base || '/v').replace(/^\/+|\/+$/g, '');
const origin = process.env.PREVIEW || 'http://localhost:5182';
const outDir = path.join(path.dirname(path.resolve(manifestPath)), 'v', 'thumbs');
const onlyArg = process.argv.find((a) => a.startsWith('--only='));
const only = onlyArg ? new Set(onlyArg.slice(7).split(',').filter(Boolean)) : null;
const cards = man.groups.flatMap((g) => g.cards).filter((c) => !only || only.has(c.key));

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  let failed = 0;
  for (const c of cards) {
    const open = c.thumb !== undefined ? c.thumb : (c.open || '');
    const [pagePath, anchor] = open.split('#');
    const url = `${origin}${base}/${c.key}/${pagePath}`;
    try {
      const resp = await page.goto(url, { waitUntil: 'networkidle' });
      if (!resp || resp.status() >= 400) throw new Error(`HTTP ${resp ? resp.status() : '—'}`);
      await page.addStyleTag({ content: '.vbadge{display:none!important}' });
      if (anchor) {
        await page.evaluate((id) => {
          document.documentElement.style.scrollBehavior = 'auto';
          const el = document.getElementById(id);
          const header = document.querySelector('.site-header');
          if (el) scrollTo(0, el.getBoundingClientRect().top + scrollY - (header ? header.offsetHeight : 0));
        }, anchor);
      }
      await page.waitForTimeout(2600);   // reveals, lamps, counters, lazy data
      await page.evaluate(() => document.querySelectorAll('.reveal').forEach((e) => e.classList.add('is-in')));
      await page.waitForTimeout(900);
      await page.screenshot({ path: path.join(outDir, `${c.key}.png`) });
      console.log(`${c.key.padStart(10)}  ${url}`);
    } catch (e) {
      failed += 1;
      console.error(`${c.key.padStart(10)}  FAILED ${url}: ${e.message.split('\n')[0]}`);
    }
  }
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
