(() => {
  const states = new WeakMap();
  const selector = '[data-prediction-preview-url], [data-position-preview-url]';

  function message(state, text) {
    const notice = document.createElement('div');
    notice.className = 'notice';
    notice.textContent = text;
    state.target.replaceChildren(notice);
  }

  async function send(form, state) {
    if (state.running || !state.ready || !state.pending) return;
    const request = state.pending;
    state.running = true;
    state.ready = false;
    try {
      const response = await fetch(form.dataset.predictionPreviewUrl || form.dataset.positionPreviewUrl, {
        method: 'POST', body: request.body, credentials: 'same-origin',
        headers: {'X-Requested-With': 'XMLHttpRequest'},
      });
      if (!response.ok || response.redirected || response.headers.get('X-GTL-Preview') !== '1') {
        throw new Error('Invalid preview response');
      }
      const html = await response.text();
      if (state.pending === request) state.target.innerHTML = html;
    } catch (_) {
      if (state.pending === request) message(state, form.dataset.previewError);
    } finally {
      state.running = false;
      if (state.pending === request) {
        state.pending = null;
        state.target.setAttribute('aria-busy', 'false');
      }
      // Never abort and replace an in-flight request: the server may still be working.
      // Wait for it to settle, then send only the latest value once debounce elapsed.
      send(form, state);
    }
  }

  function update(form) {
    if (!form?.matches(selector)) return;
    const state = states.get(form);
    if (!state) return;
    form.querySelectorAll('[data-amount]').forEach(range => {
      const output = form.querySelector(`[data-amount-output="${range.dataset.amount}"]`);
      if (output) output.textContent = `${range.value} GT₵`;
    });
    const body = new FormData(form);
    if (!body.get('option_id')) return;
    const radio = form.querySelector('[name="option_id"]:checked');
    if (radio) body.set('choice', radio.closest('[data-choice]')?.dataset.choice || '');
    const key = JSON.stringify(['option_id', 'stake_amount', 'action', 'choice'].map(name => body.get(name)));
    // Click/change for the same interaction must not queue an extra request.
    if (state.pending?.key === key) return;
    clearTimeout(state.timer);
    state.pending = {body, key};
    state.ready = false;
    state.target.setAttribute('aria-busy', 'true');
    message(state, form.dataset.previewLoading);
    state.timer = setTimeout(() => {
      state.ready = true;
      send(form, state);
    }, 300);
  }

  document.querySelectorAll(selector).forEach(form => {
    const target = document.getElementById(form.dataset.previewTarget || 'prediction-preview');
    if (!target) return;
    states.set(form, {target, running: false, ready: false, pending: null});
    target.setAttribute('aria-live', 'polite');
    form.addEventListener('input', () => update(form));
    form.addEventListener('change', () => update(form));
    update(form);
  });
  window.gtlUpdatePredictionPreview = update;
})();
