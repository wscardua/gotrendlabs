const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../apps/web/static/js/gotrendlabs.js'), 'utf8');
const start = source.indexOf('function parseNumber(');
const end = source.indexOf('$$("[data-market-card]").forEach((card, index)');
const context = {
  $$: (selector, scope) => scope.cards,
  $: () => null,
};
vm.runInNewContext(source.slice(start, end), context);

const card = (status, views, createdAt, originalOrder, extras = {}) => ({
  dataset: {
    marketStatus: status,
    marketViews: String(views),
    marketCreatedAt: createdAt,
    originalOrder: String(originalOrder),
    marketVolume: String(extras.volume || 0),
    marketLikes: String(extras.likes || 0),
    marketFavorited: String(Boolean(extras.favorite)),
    marketPredicted: String(Boolean(extras.prediction)),
  },
});
const newest = '2026-11-06T12:00:00Z';
const older = '2026-11-05T12:00:00Z';
const cards = [
  card('sealed', 1000, newest, 0, {favorite: true, prediction: true}),
  card('resolved', 800, newest, 1),
  card('locked', 600, newest, 2),
  card('open', 20, older, 3),
  card('open', 20, newest, 4),
  card('open', 20, newest, 5),
];
for (const mode of ['trending', 'new', 'volume', 'likes', 'open']) {
  assert.deepEqual(cards.filter(item => context.marketMatchesMode(item, mode)).map(item => item.dataset.marketStatus), ['open', 'open', 'open']);
}
assert.deepEqual(cards.filter(item => context.marketMatchesMode(item, 'closing')).map(item => item.dataset.marketStatus), ['locked']);
assert.deepEqual(cards.filter(item => context.marketMatchesMode(item, 'resolved')).map(item => item.dataset.marketStatus), ['sealed', 'resolved']);
assert.deepEqual(cards.filter(item => context.marketMatchesMode(item, 'favorited')), [cards[0]]);
assert.deepEqual(cards.filter(item => context.marketMatchesMode(item, 'predicted')), [cards[0]]);
assert.deepEqual(cards.filter(item => context.marketMatchesMode(item, 'trending')).sort((a, b) => context.compareMarkets('trending', a, b)), [cards[4], cards[5], cards[3]]);
const paged = {
  dataset: {marketPageSize: '18'},
  cards: [cards[0], ...Array.from({length: 20}, (_, index) => card('open', index, older, index + 6))],
  parentElement: {querySelector: () => null},
};
context.renderMarketChunk(paged, 'trending');
assert.equal(paged.cards.filter(item => !item.hidden).length, 18);
assert.equal(paged.cards[0].hidden, true);
context.renderMarketChunk(paged, 'trending', 36);
assert.equal(paged.cards.filter(item => !item.hidden).length, 20);
context.renderMarketChunk(paged, 'resolved');
assert.deepEqual(paged.cards.filter(item => !item.hidden), [cards[0]]);
console.log('market feed filters: OK');
