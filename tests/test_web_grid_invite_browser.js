/* Run the read-only preview server first. Uses an already installed Playwright. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');
const url = process.env.GTL_INVITE_PREVIEW_URL || 'http://127.0.0.1:8767';
const out = path.resolve('.runtime/grid-invite');
fs.mkdirSync(out, {recursive:true});
const invite = '[data-market-grid-invite]';
const visibleCards = '[data-market-list] > [data-market-card]:visible';
const options = ['suggestion','ranking','badges','results','concepts'];
const destinations = ['/suggestion/','/rankings/','/badges/','/#resolvidos','/concepts/'];
(async () => {
  const browser = await chromium.launch({headless:true, channel:process.env.GTL_BROWSER_CHANNEL || 'chrome'});
  try {
    const context = await browser.newContext({viewport:{width:1366,height:1000}});
    const errors = [];
    const page = await context.newPage();
    page.on('pageerror',error=>errors.push(error.message));
    await page.addInitScript(()=>{
      localStorage.setItem('gtl-analytics-opt-out','1');
      const random = new URL(location.href).searchParams.get('random');
      if (random !== null) {localStorage.removeItem('gotrendlabs-grid-invite-last');Math.random=()=>Number(random);}
    });
    async function open(count, random) {
      await page.goto(`${url}/?count=${count}${random === undefined ? "" : `&random=${random}`}`, {waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>window.gtlMarketGridInvite && document.querySelector('[data-market-grid-invite]').dataset.selection);
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    }
    await page.goto(`${url}/categories/`);
    assert.deepEqual(await page.locator('[data-filter]').evaluateAll(buttons=>buttons.map(b=>b.getAttribute('aria-pressed'))),['true','false','false']);
    await page.locator('[data-filter]').nth(1).click();
    assert.deepEqual(await page.locator('[data-filter]').evaluateAll(buttons=>buttons.map(b=>b.getAttribute('aria-pressed'))),['false','true','false']);
    assert.equal(await page.locator(invite).count(),0);
    console.log('PASS: Categories filter accessibility preserved without a feed target');
    // Actual CSS grid + visible nodes, not a duplicate layout function.
    for (const [width, columns] of [[1366,3],[1000,2],[390,1]]) {
      await page.setViewportSize({width,height:1000});
      for (let count=0; count<=8; count++) {
        await open(count);
        const selection = await page.locator(invite).getAttribute('data-selection');
        for (const theme of ['light','dark']) {
          await page.evaluate(theme=>document.body.dataset.theme=theme,theme);
          const result = await page.evaluate(()=>{
            const grid=document.querySelector('[data-market-list]'), box=grid.querySelector('[data-market-grid-invite]');
            const cards=[...grid.querySelectorAll('[data-market-card]')].filter(c=>!c.hidden);
            return {columns:getComputedStyle(grid).gridTemplateColumns.split(/\s+/).length,
              visible:!box.hidden, span:box.style.gridColumn, count:cards.length,
              last:box===grid.lastElementChild, secondary:document.querySelectorAll('[data-market-pending-list] [data-market-grid-invite]').length,
              overflow:document.documentElement.scrollWidth>innerWidth,
              heights:cards.map(c=>c.getBoundingClientRect().height),
              inviteHeight:box.getBoundingClientRect().height};
          });
          assert.equal(result.columns,columns);
          assert.equal(result.count,count);
          const span=count && columns>1 && count%columns ? columns-count%columns : 0;
          assert.equal(result.visible,!!span, `${width}/${count}/${theme}`);
          assert.equal(result.secondary,0); assert(result.last); assert(!result.overflow);
          if(span) {
            assert.equal(result.span,`span ${span}`);
            assert(Math.abs(result.inviteHeight-result.heights.at(-1))<1);
          }
          assert.equal(await page.locator(invite).getAttribute('data-selection'),selection);
        }
        const before=await page.locator(visibleCards).evaluateAll(cards=>cards.map(c=>({slug:c.dataset.marketSlug,rect:c.getBoundingClientRect().toJSON()})));
        await page.locator(invite).evaluate(e=>e.hidden=true);
        const after=await page.locator(visibleCards).evaluateAll(cards=>cards.map(c=>({slug:c.dataset.marketSlug,rect:c.getBoundingClientRect().toJSON()})));
        assert.deepEqual(after,before,'Invitation must not change market dimensions/order/position');
      }
    }
    console.log('PASS: 0–8 × 3/2/1 columns × light/dark; market dimensions/order; empty/pending; overflow');
    await page.setViewportSize({width:1366,height:1000});
    // A single-column invitation stays vertical even in the widest two-column layout.
    for (const [width, columns] of [[1080,2],[1081,3],[980,1]]) {
      await page.setViewportSize({width,height:1000});
      await open(5);
      assert.equal(await page.locator('[data-market-list]').evaluate(e=>getComputedStyle(e).gridTemplateColumns.split(/\s+/).length),columns);
      if (columns>1) assert.equal(await page.locator(`${invite} .market-grid-invite-inner`).evaluate(e=>getComputedStyle(e).flexDirection),'column');
    }
    await page.setViewportSize({width:1366,height:1000});
    console.log('PASS: responsive breakpoint edges; single-column invitation remains vertical');
    // Force each equally spaced random bucket only in the test browser; product has no override.
    for (let index=0; index<5; index++) {
      for (const count of [4,5]) {
        await open(count, (index+.1)/5);
        assert.equal(await page.locator(invite).getAttribute('data-selection'),options[index]);
        assert.equal(await page.locator(`${invite} a`).getAttribute('href'),destinations[index]);
        for (const theme of ['light','dark']) {
          await page.evaluate(theme=>document.body.dataset.theme=theme,theme);
          await page.evaluate(()=>document.fonts.ready);
          const inner=page.locator(`${invite} .market-grid-invite-inner`);
          assert(await inner.evaluate(e=>e.scrollHeight<=e.clientHeight+1),'Approved copy fits without vertical scroll');
          assert(await inner.evaluate(e=>e.scrollWidth<=e.clientWidth+1),'No horizontal scroll');
          await page.evaluate(()=>{document.documentElement.style.scrollBehavior='auto';scrollTo({top:0,behavior:'instant'});});
          await page.waitForFunction(()=>scrollY===0);
          await page.locator('[data-market-list]').screenshot({path:path.join(out,`${options[index]}-${count}-${theme}.png`)});
        }
        await page.locator(`${invite} a`).focus();
        await page.keyboard.press('Tab');
        await page.keyboard.press('Shift+Tab');
        assert(await page.locator(`${invite} a`).evaluate(e=>e===document.activeElement));
        assert.notEqual(await page.locator(`${invite} a`).evaluate(e=>getComputedStyle(e).outlineStyle),'none');
        if(options[index]==='results') {
          await page.keyboard.press('Enter');
          assert.equal(await page.locator('[data-filter="resolved"]').getAttribute('aria-pressed'),'true');
          assert.equal(await page.locator(visibleCards).count(),1);
          assert.equal(await page.locator(invite).getAttribute('data-selection'),'results');
        }
      }
    }
    console.log('PASS: five options/real named destinations; 20 screenshots; copy fits; keyboard/focus; results action');
    // Each option can be followed by every other option with equal sized random intervals.
    const historyContext=await browser.newContext({viewport:{width:1366,height:1000}});
    const history=await historyContext.newPage();
    history.on('pageerror',error=>errors.push(error.message));
    await history.addInitScript(()=>{localStorage.setItem('gtl-analytics-opt-out','1');Math.random=()=>0;});
    await history.goto(`${url}/?count=4`);
    const first=await history.locator(invite).getAttribute('data-selection');
    await history.reload();
    const second=await history.locator(invite).getAttribute('data-selection');
    assert.notEqual(first,second);
    await history.locator('[data-filter="resolved"]').click();
    await history.locator('[data-filter="ongoing"]').click();
    for(const width of [1000,390,1366]) {
      await history.setViewportSize({width,height:1000});
      assert.equal(await history.locator(invite).getAttribute('data-selection'),second);
    }
    await history.locator('[data-theme-toggle]').click();
    assert.equal(await history.locator(invite).getAttribute('data-selection'),second);
    // Genuine HTMX request and replacement, then repeat lifecycle events to detect duplicate init.
    assert(await history.evaluate(()=>typeof htmx!=='undefined'),'Existing HTMX must be loaded for acceptance');
    await history.evaluate(()=>htmx.ajax('GET','/fragment?count=20',{target:'[data-market-board]',swap:'outerHTML'}));
    await history.waitForFunction(()=>document.querySelectorAll('[data-market-list] [data-market-card]:not([hidden])').length===18);
    assert.equal(await history.locator(invite).getAttribute('data-selection'),second);
    assert(await history.locator(invite).evaluate(e=>e.hidden));
    await history.locator('[data-market-board] > .market-feed-section [data-market-load-more-button]').click();
    await history.locator(`${invite}:visible`).waitFor();
    assert.equal(await history.locator(visibleCards).count(),20);
    assert.equal(await history.locator(invite).getAttribute('data-selection'),second);
    await history.evaluate(()=>{for(let i=0;i<3;i++) document.dispatchEvent(new CustomEvent('htmx:afterSwap'));});
    assert.equal(await history.locator(`${invite} .market-grid-invite-inner`).count(),1);
    await history.locator('[data-filter="resolved"]').click();
    assert.equal(await history.locator(visibleCards).count(),1);
    await history.locator('[data-filter="ongoing"]').click();
    assert.equal(await history.locator(visibleCards).count(),18);
    // Long localized copy may scroll inside the invitation, never stretch market rows or overflow horizontally.
    await history.locator('[data-market-board] > .market-feed-section [data-market-load-more-button]').click();
    const height=await history.locator(visibleCards).last().evaluate(e=>e.getBoundingClientRect().height);
    await history.locator(`${invite} h2`).evaluate(e=>e.textContent='Uma pergunta com palavras muito extensas '.repeat(15));
    assert.equal(await history.locator(visibleCards).last().evaluate(e=>e.getBoundingClientRect().height),height);
    assert(await history.locator(`${invite} .market-grid-invite-inner`).evaluate(e=>e.scrollWidth<=e.clientWidth+1));
    await history.goto(`${url}/?count=5#resolvidos`);
    assert.equal(await history.locator('[data-filter="resolved"]').getAttribute('aria-pressed'),'true');
    console.log('PASS: anti-repeat; filters/resize/theme; actual HTMX replacement + pagination; duplicate events; long copy; results deep link');
    for(const mode of ['unavailable','read-only','corrupt']) {
      const blocked=await browser.newContext({viewport:{width:1366,height:1000}});
      await blocked.addInitScript(mode=>{
        if(mode==='unavailable') Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Denied','SecurityError');}});
        if(mode==='read-only') Storage.prototype.setItem=()=>{throw new DOMException('Full','QuotaExceededError');};
        if(mode==='corrupt') localStorage.setItem('gotrendlabs-grid-invite-last','unknown-option');
      },mode);
      const bp=await blocked.newPage(); const storageErrors=[];
      bp.on('pageerror',e=>storageErrors.push(e.message));
      await bp.goto(`${url}/?count=5`);
      await bp.locator(`${invite}:visible`).waitFor();
      await bp.locator('[data-filter="resolved"]').click();
      await bp.locator('[data-filter="ongoing"]').click();
      await bp.locator('[data-theme-toggle]').click();
      assert.equal(await bp.locator(visibleCards).count(),5);
      assert.deepEqual(storageErrors,[],mode);
      await blocked.close();
    }
    assert.deepEqual(errors,[]);
    console.log('PASS: denied/read-only/corrupt storage; no page errors. Browser acceptance complete.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
