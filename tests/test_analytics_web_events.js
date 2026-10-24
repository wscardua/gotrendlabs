const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../apps/web/static/js/analytics.js'), 'utf8');
const listeners = new Map();
const observers = [];
const timers = [];
const batches = [];
const stored = new Map();
let nextId = 0;

const predictionForm = {
  dataset: { marketSlug: 'market-a' },
  matches: selector => selector === 'form[data-prediction-preview-url]',
  closest: selector => selector === '[data-market-slug]' ? predictionForm : null,
};
const positionForm = {
  dataset: { marketSlug: 'market-a' },
  closest: selector => selector === '[data-market-slug]' ? positionForm : null,
};
const choice = form => ({
  matches: selector => selector === '[data-choice]',
  closest: selector => {
    if (selector === 'a, button, [data-choice]') return choiceNodes.get(form);
    if (selector === 'form[data-prediction-preview-url]') return form === predictionForm ? form : null;
    if (selector === '[data-market-slug]') return form;
    return null;
  },
});
const choiceNodes = new Map();
choiceNodes.set(predictionForm, choice(predictionForm));
choiceNodes.set(positionForm, choice(positionForm));

class IntersectionObserver {
  constructor(callback) {
    this.callback = callback;
    this.targets = new Set();
    observers.push(this);
  }
  observe(target) { this.targets.add(target); }
  unobserve(target) { this.targets.delete(target); }
  show(target) { this.callback([{ target, isIntersecting: true }]); }
}

const document = {
  referrer: '',
  querySelector: selector => selector === 'meta[name="csrf-token"]' ? { content: 'csrf' } : null,
  querySelectorAll: selector => selector === 'form[data-prediction-preview-url]' ? [predictionForm] : [],
  addEventListener: (name, callback) => listeners.set(name, callback),
};
const context = {
  URL,
  URLSearchParams,
  Date,
  WeakSet,
  crypto: { randomUUID: () => `00000000-0000-4000-8000-${String(++nextId).padStart(12, '0')}` },
  document,
  location: { pathname: '/markets/market-a/', search: '' },
  navigator: { doNotTrack: '0' },
  localStorage: {
    getItem: key => stored.get(key) || null,
    setItem: (key, value) => stored.set(key, value),
    removeItem: key => stored.delete(key),
  },
  window: { IntersectionObserver, addEventListener: () => {} },
  IntersectionObserver,
  setInterval: callback => timers.push(callback),
  fetch: async (url, options) => {
    batches.push(JSON.parse(options.body));
    return { ok: true, status: 200 };
  },
};

(async () => {
  vm.runInNewContext(source, context);
  const ticketObserver = observers[1];
  assert(ticketObserver.targets.has(predictionForm));

  await timers[0]();
  assert.equal(batches[0].events.some(event => event.name === 'prediction_started'), false);

  ticketObserver.show(predictionForm);
  listeners.get('click')({ target: choiceNodes.get(predictionForm) });
  listeners.get('click')({ target: choiceNodes.get(positionForm) });
  await timers[0]();

  const names = batches[1].events.map(event => event.name);
  assert.deepEqual(names, ['prediction_started', 'prediction_option_selected']);
  assert.equal(batches[1].events[0].properties.market_slug, 'market-a');

  listeners.get('htmx:pushedIntoHistory')();
  listeners.get('click')({ target: choiceNodes.get(predictionForm) });
  ticketObserver.show(predictionForm);
  await timers[0]();
  assert.deepEqual(batches[2].events.map(event => event.name), [
    'page_viewed', 'market_detail_viewed', 'prediction_started', 'prediction_option_selected',
  ]);
  listeners.get('gtl:prediction-preview-viewed')({detail: {marketSlug: 'market-a'}});
  await timers[0]();
  assert.deepEqual(batches[3].events.map(event => event.name), ['prediction_preview_viewed']);
  console.log('analytics web ticket lifecycle: OK');
})().catch(error => { console.error(error); process.exitCode = 1; });
