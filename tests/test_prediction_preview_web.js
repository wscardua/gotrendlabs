const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const timers = new Map();
const calls = [];
const analyticsEvents = [];
let timerId = 0;
const targets = new Map();
function form(id, position = false) {
  const handlers = {};
  const target = {html: '', text: '', attrs: {}, setAttribute(k, v) {this.attrs[k] = v;}, replaceChildren(node) {this.text = node.textContent; this.html = '';}, set innerHTML(v) {this.html = v; this.text = '';}, querySelector: selector => selector === '[data-analytics-prediction-preview]' && target.html.includes('data-analytics-prediction-preview') ? {} : null};
  targets.set(id, target);
  const instance = {
    dataset: {previewTarget: id, previewLoading: 'Loading', previewError: 'Try again', [position ? 'positionPreviewUrl' : 'predictionPreviewUrl']: '/preview/' + id},
    fields: {option_id: '', stake_amount: '80', action: position ? 'reinforcement' : '', choice: 'SIM'},
    matches: selector => selector === '[data-prediction-preview-url]' ? !position : true,
    closest: () => ({dataset: {marketSlug: 'market-a'}}), querySelectorAll: () => [],
    querySelector: () => null,
    addEventListener: (name, handler) => {handlers[name] = handler;},
    emit: () => handlers.input(), target,
  };
  return instance;
}
const initial = form('initial');
const position = form('position', true);
class FormData {
  constructor(form) {this.fields = {...form.fields};}
  get(key) {return this.fields[key] || null;}
  set(key, value) {this.fields[key] = value;}
}
const context = {
  window: {}, FormData, WeakMap, JSON,
  document: {querySelectorAll: () => [initial, position], getElementById: id => targets.get(id), createElement: () => ({}), dispatchEvent: event => analyticsEvents.push(event)},
  CustomEvent: class {constructor(type, options) {this.type = type; this.detail = options.detail;}},
  location: {pathname: '/markets/market-a/'},
  setTimeout: callback => {timers.set(++timerId, callback); return timerId;},
  clearTimeout: id => timers.delete(id),
  fetch: (url, options) => new Promise(resolve => calls.push({url, options, resolve})),
};
function tick() {const pending = [...timers.values()]; timers.clear(); pending.forEach(fn => fn());}
async function respond(index, {ok = true, marker = '1', html = '<div>preview</div>', redirected = false} = {}) {
  calls[index].resolve({ok, redirected, headers: {get: () => marker}, text: async () => html});
  await new Promise(resolve => setImmediate(resolve));
}
(async () => {
  vm.runInNewContext(fs.readFileSync('apps/web/static/js/prediction-preview.js', 'utf8'), context);
  tick();
  assert.equal(calls.length, 0, 'no option means no request');
  initial.fields.option_id = '7';
  for (let amount = 1; amount <= 500; amount++) {
    initial.fields.stake_amount = String(amount);
    initial.emit();
  }
  assert.equal(calls.length, 0, 'burst waits for debounce');
  tick();
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.body.get('stake_amount'), '500');
  initial.fields.stake_amount = '300'; initial.emit(); tick();
  initial.fields.stake_amount = '240'; initial.emit(); tick();
  assert.equal(calls.length, 1, 'no overlap while request is running');
  await respond(0, {html: 'OLD 500'});
  assert.equal(initial.target.html, '', 'old response is discarded');
  assert.equal(calls.length, 2);
  assert.equal(calls[1].options.body.get('stake_amount'), '240');
  await respond(1, {html: 'CURRENT 240'});
  assert.equal(initial.target.html, 'CURRENT 240');
  assert.equal(initial.target.attrs['aria-busy'], 'false');
  initial.fields.stake_amount = '250'; initial.emit(); tick();
  await respond(2, {ok: false, html: '<h1>Server Error (500)</h1>'});
  assert.equal(initial.target.html, '');
  assert.equal(initial.target.text, 'Try again');
  initial.emit(); tick(); // retry with same value after failure
  await respond(3, {marker: null, html: '<html>Login</html>'});
  assert.equal(initial.target.text, 'Try again', 'full HTML page must not enter fragment');
  initial.emit(); tick();
  await respond(4, {html: '<div data-analytics-prediction-preview>RECOVERED</div>'});
  assert.equal(initial.target.html, '<div data-analytics-prediction-preview>RECOVERED</div>');
  assert.equal(analyticsEvents.length, 1);
  assert.equal(analyticsEvents[0].detail.marketSlug, 'market-a');
  position.fields.option_id = '8'; position.emit(); tick();
  assert.equal(calls.length, 6);
  assert.equal(calls[5].url, '/preview/position');
  await respond(5, {html: 'POSITION'});
  assert.equal(position.target.html, 'POSITION');
  assert.equal(initial.target.html, '<div data-analytics-prediction-preview>RECOVERED</div>', 'tickets remain independent');
  assert.equal(analyticsEvents.length, 1, 'position preview is not an initial prediction preview');
  console.log('prediction preview: burst, serialization, stale responses, errors and recovery OK');
})().catch(error => {console.error(error); process.exitCode = 1;});
