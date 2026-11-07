/* Start tests/performance_preview.py first; test-only fixtures, no production requests. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({headless:true, channel:'chrome'});
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  fs.mkdirSync('.runtime/performance', {recursive:true});
  await page.addInitScript(() => localStorage.setItem('gtl-analytics-opt-out', '1'));
  try {
    for (const width of [1440, 1024, 768, 390, 320]) {
      await page.setViewportSize({width, height:1000});
      for (const state of ['data', 'empty', 'error']) {
        await page.goto(`http://127.0.0.1:8768/?state=${state}`, {waitUntil:'networkidle'});
        for (const theme of ['light','dark']) {
          await page.evaluate(theme => document.body.dataset.theme = theme, theme);
          await page.waitForTimeout(350); // Allow existing theme transitions to finish before screenshots.
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${width}/${state}/${theme} overflow`);
          if (state === 'data') {
            assert.equal(await page.locator('.performance-table tbody tr').count(), 10);
            assert.equal(await page.locator('.performance-table tbody tr:visible').count(), 5);
            assert.equal(await page.locator('.performance-impact-bar').count(), 10);
            assert.equal(await page.locator('.performance-impact-bar.negative').count(), 5);
            assert.equal(await page.locator('.performance-impact-bar').first().getAttribute('href'), '/markets/mercado-9/');
            assert.equal(await page.locator('.performance-impact-value').first().innerText(), '+4');
            for (const bar of await page.locator('.performance-impact-bar').all()) {
              const box = await bar.boundingBox();
              assert(box.x >= 0 && box.x + box.width <= width, 'Chart bars must fit the viewport');
              assert(await bar.getAttribute('aria-label'), 'Chart links need accessible labels');
            }
            assert.equal(await page.locator('.performance-awards img:visible').count(), 1);
            assert.equal(await page.locator(`.badge-image-${theme}`).isVisible(), true);
            const boxes = await page.locator('.performance-layout > *').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().toJSON()));
            assert(width>850 ? boxes[1].x>boxes[0].x : boxes[1].y>=boxes[0].bottom);
          }
          if ([1440,390].includes(width)) await page.screenshot({path:`.runtime/performance/${width}-${state}-${theme}.png`,fullPage:true});
        }
        if (state === 'data') {
          let requests = 0;
          const trackRequest = () => { requests += 1; };
          page.on('request', trackRequest);
          await page.locator('[data-performance-more-button]').focus();
          await page.keyboard.press('Enter');
          assert.equal(await page.locator('.performance-table tbody tr:visible').count(), 10);
          assert.equal(await page.locator('[data-performance-more-button]').isVisible(), false);
          assert(await page.locator('[data-performance-count]').innerText().then(text => text.includes('10 de 10')));
          assert(await page.locator('.performance-market').nth(5).evaluate(e => e === document.activeElement));
          assert.equal(requests, 0, 'Reveal must not request unsupported API pagination');
          page.off('request', trackRequest);
        } else {
          assert.equal(await page.locator('[data-performance-more-button]').count(), 0);
          assert.equal(await page.locator('.performance-impact-bar').count(), 0);
        }
      }
    }
    const noScriptContext = await browser.newContext({javaScriptEnabled:false});
    const noScriptPage = await noScriptContext.newPage();
    await noScriptPage.goto('http://127.0.0.1:8768/');
    assert.equal(await noScriptPage.locator('.performance-table tbody tr:visible').count(), 10);
    assert.equal(await noScriptPage.locator('[data-performance-more-button]').isVisible(), false);
    await noScriptContext.close();
    await page.goto('http://127.0.0.1:8768/');
    await page.locator('.performance-market').first().focus();
    assert(await page.locator('.performance-market').first().evaluate(e=>e===document.activeElement && getComputedStyle(e).outlineStyle!=='none'));
    await page.keyboard.press('Tab');
    assert(await page.locator('.performance-market').nth(1).evaluate(e=>e===document.activeElement));
    assert.deepEqual(errors, []);
    console.log('PASS: 30 viewport/state/theme combinations; badge themes, layout, keyboard/focus, no horizontal overflow or JS errors. 12 screenshots.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exit(1);});
