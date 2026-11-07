const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('apps/web/static/js/market-grid-invite.js', 'utf8');
const context = {historyKey:'test-history', Math:{random:()=>0,floor:Math.floor}, localStorage:{getItem:()=>null,setItem:()=>{}}};
vm.runInNewContext(source.slice(source.indexOf('  function choose('),source.indexOf('  function update(')),context);
const options=['suggestion','ranking','badges','results','concepts'];
for (const previous of [null, 'invalid', ...options]) {
  let saved;
  context.localStorage={getItem:()=>previous,setItem:(_key,value)=>saved=value};
  const draws=[];
  const eligibleCount=options.includes(previous)?4:5;
  // One midpoint from each equal probability interval, including every previous option.
  for(let index=0; index<eligibleCount; index++) {
    context.Math.random=()=>(index+.5)/eligibleCount;
    const draw=context.choose(options);
    assert.equal(saved,draw);
    assert.notEqual(draw,previous);
    draws.push(draw);
  }
  assert.deepEqual(draws, options.filter(option=>option!==previous));
}
for(const failure of ['read','write']) {
  context.localStorage={getItem(){if(failure==='read')throw Error('Denied');return null;},setItem(){if(failure==='write')throw Error('Full');}};
  context.Math.random=()=>0;
  assert.equal(context.choose(options),'suggestion');
}
console.log('grid invitation selection: equal intervals, all previous choices, corrupt/denied/full history OK');
