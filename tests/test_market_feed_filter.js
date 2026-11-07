const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../apps/web/static/js/gotrendlabs.js'), 'utf8');
const start = source.indexOf('function parseNumber(');
const end = source.indexOf('// Freshness is independent');
let board;
const context = {
  $$: (selector, scope) => scope === board ? [...board.main.cards, ...board.pendingList.cards] : [...scope.cards],
  $: (selector, scope) => scope ? scope.querySelector(selector) : board.main,
};
vm.runInNewContext(source.slice(start, end), context);
const now = Date.parse('2026-11-07T12:00:00Z');
const card = (status, views, created, order, extras = {}) => ({
  dataset: {marketStatus: status, marketViews: String(views), marketCreatedAt: created,
    marketCloseAt: extras.close || '', originalOrder: String(order),
    marketFavorited: String(!!extras.favorite), marketPredicted: String(!!extras.prediction)},
  badge: {hidden: true},
  querySelector() { return this.badge; },
});
const recent = '2026-11-07T10:00:00Z', older = '2026-11-04T12:00:00Z';
const cards = [
  card('sealed', 9999, recent, 0, {favorite: true, prediction: true}),
  card('resolved', 8000, recent, 1),
  card('locked', 6000, recent, 2, {close: '2026-11-06T10:00:00Z'}),
  card('open', 20, older, 3), card('open', 20, recent, 4), card('open', 20, recent, 5),
  card('draft', 99999, recent, 6, {favorite: true, prediction: true}),
  card('canceled', 99999, recent, 7, {favorite: true, prediction: true}),
];
assert.deepEqual(cards.filter(c => context.marketMatchesMode(c, 'ongoing')), cards.slice(3, 6));
assert.deepEqual(cards.filter(c => context.marketMatchesMode(c, 'resolved')), cards.slice(0, 2));
for (const mode of ['favorited', 'predicted']) {
  assert.deepEqual(cards.filter(c => context.marketMatchesMode(c, mode)), [cards[0]]);
}
assert.deepEqual(cards.slice(3, 6).sort((a,b) => context.compareMarkets('ongoing',a,b)), [cards[4], cards[5], cards[3]]);
const oldPopular = card('open', 100, older, 8), newLessViewed = card('open', 1, recent, 9);
assert.deepEqual([newLessViewed, oldPopular].sort((a,b) => context.compareMarkets('ongoing',a,b)), [oldPopular,newLessViewed]);
const tiedPending = [card('locked',0,older,11,{close:recent}), card('locked',999,older,10,{close:recent})];
assert.equal(tiedPending.sort((a,b)=>context.compareMarkets('closing',a,b))[0].dataset.originalOrder,'10');
for (const [status, created, expected] of [
  ['open', '2026-11-05T12:00:00.001Z', true],
  ['open', '2026-11-05T12:00:00Z', false],
  ['open', '2026-11-05T11:59:59Z', false],
  ['open', '2026-11-07T12:00:00Z', true],
  ['open', '2026-11-07T12:00:00.001Z', false],
  ['locked', recent, false], ['resolved', recent, false], ['sealed', recent, false],
]) assert.equal(context.isNewMarket(card(status,0,created,0), now), expected);

function makeList() {
  const list = {cards: [], dataset: {marketPageSize: '18'}, closest: () => board,
    appendChild(c) {
      if (c.parent) c.parent.cards.splice(c.parent.cards.indexOf(c), 1);
      this.cards.push(c); c.parent = this;
    }};
  const empty = {hidden: true, dataset: {ongoing: 'Nenhum mercado aberto no momento.', resolved:'Nenhum mercado resolvido ainda.',favorited:'Nenhum mercado favorito ainda.',predicted:'Nenhum mercado com previsão sua ainda.'}}, summary = {}, button = {};
  const more = {hidden: true, querySelector: s => s.includes('summary') ? summary : button};
  list.parentElement = {querySelector: s => s === '[data-market-empty]' ? empty : more};
  list.empty = empty; list.more = more; list.summary = summary;
  return list;
}
const main = makeList(), pendingList = makeList();
const count = {dataset:{singular:'mercado',plural:'mercados'}}, pending = {open: false, querySelector: () => count}, noActive = {};
board = {main, pendingList, querySelector(s) {
  return ({'[data-market-pending]':pending,'[data-market-pending-list]':pendingList,'[data-market-no-active]':noActive})[s];
}};
const group = {dataset: {filterTarget: '[data-market-list]'}};
const opens = Array.from({length: 21},(_,i) => card('open', i, older, i + 20));
const locked = Array.from({length: 20},(_,i) => card('locked', 99999, older, i + 60, {close: `2026-11-${String(i+1).padStart(2,'0')}T00:00:00Z`}));
const noDate = card('locked', 0, older, 100);
[...cards.slice(0,2), ...opens, ...locked, noDate].forEach(c => main.appendChild(c));
const visible = list => list.cards.filter(c => !c.hidden);
context.sortMarketList(group, 'ongoing');
assert.equal(visible(main).length,18);
assert(visible(main).every(c => c.dataset.marketStatus === 'open'));
assert.equal(pending.open,true);
assert.equal(pending.hidden,false);
assert.equal(count.textContent,'21 mercados');
assert.equal(visible(pendingList).length,18);
assert.equal(pendingList.cards.at(-1),noDate);
assert.equal(pendingList.cards[0],locked.at(-1));
pending.open = false;
context.renderMarketChunk(pendingList,'closing',36);
context.sortMarketList(group,'ongoing',36);
assert.equal(visible(main).length,21);
assert.equal(visible(pendingList).length,21);
assert.equal(pending.open,false); // loading opens preserves a manual collapse
context.sortMarketList(group,'resolved');
assert.equal(visible(main).length,2);
assert.equal(pending.hidden,true);
context.sortMarketList(group,'ongoing');
assert.equal(pending.open,true);
// Recortes pessoais do not inherit the discovery filter.
cards[0].dataset.marketFavorited='true';
main.appendChild(cards[0]);
context.sortMarketList(group,'favorited');
assert.deepEqual(visible(main),[cards[0]]);
// No opens: keep locked accessible; no active markets: show route to results.
[...board.main.cards,...board.pendingList.cards].forEach(c => { if(c.dataset.marketStatus==='open') c.dataset.marketStatus='resolved'; });
context.sortMarketList(group,'ongoing');
assert.equal(main.empty.textContent,'Nenhum mercado aberto no momento.');
assert.equal(main.empty.hidden,false);
assert.equal(pending.hidden,false);
[...board.main.cards,...board.pendingList.cards].forEach(c => { if(c.dataset.marketStatus==='locked') c.dataset.marketStatus='sealed'; });
context.sortMarketList(group,'resolved'); context.sortMarketList(group,'ongoing');
assert.equal(pending.hidden,true);
assert.equal(noActive.hidden,false);
console.log('market feed filters: OK');

// Actual freshness startup without any feed/filter board (Categories).
let clock = now, scheduled, visibilityChanged;
const categoryCards = [
  card('open', 0, '2026-11-05T12:00:01Z', 0),
  card('locked', 0, recent, 1),
  card('open', 0, older, 2),
];
const freshnessContext = {
  Date: {now: () => clock},
  parseDateScore: context.parseDateScore,
  isNewMarket: context.isNewMarket,
  $$: () => categoryCards,
  $: (selector, c) => c.badge,
  window: {
    clearTimeout: () => { scheduled = undefined; },
    setTimeout: (callback, delay) => { scheduled = {callback, delay}; return 1; },
  },
  document: {hidden: false, addEventListener: (name, fn) => { visibilityChanged = fn; }},
};
vm.runInNewContext(source.slice(end, source.indexOf('$$("[data-market-card]").forEach((card, index)')), freshnessContext);
assert.equal(categoryCards[0].badge.hidden, false);
assert.equal(categoryCards[1].badge.hidden, true);
assert.equal(categoryCards[2].badge.hidden, true);
assert.equal(scheduled.delay, 1000);
clock += 1000;
scheduled.callback();
assert.equal(categoryCards[0].badge.hidden, true);
assert.equal(scheduled, undefined);
// Returning to a visible tab rechecks the clock even after timer throttling.
clock = now;
visibilityChanged();
assert.equal(categoryCards[0].badge.hidden, false);
clock += 2000;
visibilityChanged();
assert.equal(categoryCards[0].badge.hidden, true);
console.log('market ribbon lifecycle: OK');

// Categories uses the same generic filters without a catalog target.
const genericButtons = [true, false, false].map(active => ({
  active, dataset: {}, attributes: {},
  classList: {toggle(name, value) { this.owner.active = value; }},
  setAttribute(name, value) { this.attributes[name] = value; },
}));
genericButtons.forEach(button => { button.classList.owner = button; });
const genericGroup = {dataset:{}, buttons:genericButtons};
const genericContext = {
  $$: (selector, root) => selector === '[data-filter-group]' ? [genericGroup] : selector === '[data-filter]' ? root.buttons : [],
  $: (selector, root) => selector.startsWith('.filter.active') ? root.buttons.find(button=>button.active) : root.buttons[0],
  window:{location:{hash:''}},
  sortMarketList:()=>{throw Error('A generic filter must not initialize the market board');},
};
vm.runInNewContext(source.slice(source.indexOf('function syncFilterPressedState('), source.indexOf('\nhydrateMarketBoards();')),genericContext);
genericContext.hydrateMarketBoards();
assert.deepEqual(genericButtons.map(button=>button.attributes['aria-pressed']), ['true','false','false']);
console.log('generic filters accessibility: OK');
