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
    for (const role of ['staff', 'superuser']) {
      for (const width of [1440, 390]) {
        await page.setViewportSize({width, height:1000});
        for (const state of ['data', 'empty', 'error']) {
          await page.goto(`http://127.0.0.1:8768/?state=${state}&role=${role}`, {waitUntil:'networkidle'});
          for (const theme of ['light', 'dark']) {
            await page.evaluate(theme => document.body.dataset.theme = theme, theme);
            await page.waitForTimeout(350);
            assert.equal(await page.locator('#scorecard-title').count(), 0, 'Administrative scorecard stays hidden');
            assert.equal(await page.locator('.performance-impact-bar').count(), state === 'data' ? 10 : 0);
            assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${role}/${width}/${state}/${theme} overflow`);
            if (state === 'data') {
              assert.equal(await page.locator('.performance-impact-chart').isVisible(), true);
              assert.equal(await page.locator('.performance-impact-bar').first().getAttribute('href'), '/markets/mercado-9/');
              assert.equal(await page.locator('.performance-impact-value').first().innerText(), '+4');
              await page.screenshot({path:`.runtime/performance/admin-${role}-${width}-${theme}.png`,fullPage:true});
            }
          }
        }
      }
    }
    const noScriptContext = await browser.newContext({javaScriptEnabled:false});
    const noScriptPage = await noScriptContext.newPage();
    await noScriptPage.goto('http://127.0.0.1:8768/');
    assert.equal(await noScriptPage.locator('.performance-table tbody tr:visible').count(), 10);
    assert.equal(await noScriptPage.locator('[data-performance-more-button]').isVisible(), false);
    await noScriptPage.goto('http://127.0.0.1:8768/?role=staff');
    assert.equal(await noScriptPage.locator('.performance-impact-chart').isVisible(), true);
    assert.equal(await noScriptPage.locator('#scorecard-title').count(), 0);
    await noScriptContext.close();
    await page.goto('http://127.0.0.1:8768/');
    await page.locator('.performance-market').first().focus();
    assert(await page.locator('.performance-market').first().evaluate(e=>e===document.activeElement && getComputedStyle(e).outlineStyle!=='none'));
    await page.keyboard.press('Tab');
    assert(await page.locator('.performance-market').nth(1).evaluate(e=>e===document.activeElement));
    assert.deepEqual(errors, []);
    console.log('PASS: 54 viewport/state/theme/role combinations; admin personal chart with hidden scorecard, empty/error states, badge themes, keyboard/focus, no-JS, no overflow or JS errors. 20 screenshots.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exit(1);});
