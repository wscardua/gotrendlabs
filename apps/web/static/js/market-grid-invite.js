/* One contextual invitation per catalog visit. No domain data or network calls. */
(() => {
  // HTMX may encounter this script again when replacing the full catalog.
  if (window.gtlMarketGridInvite) return;
  const historyKey = 'gotrendlabs-grid-invite-last';
  const grids = new Map();
  let selection;

  function choose(options) {
    let previous;
    try { previous = localStorage.getItem(historyKey); } catch (_) { /* Optional history. */ }
    const eligible = options.filter(option => option !== previous);
    const choice = eligible[Math.floor(Math.random() * eligible.length)];
    try { localStorage.setItem(historyKey, choice); } catch (_) { /* Memory still lasts this visit. */ }
    return choice;
  }

  function update(grid) {
    const invitation = grid.querySelector('[data-market-grid-invite]');
    if (!invitation) return;
    const options = [...invitation.querySelectorAll('template[data-market-invite-option]')];
    if (!selection) selection = choose(options.map(option => option.dataset.marketInviteOption));
    if (!invitation.querySelector('.market-grid-invite-inner')) {
      const template = options.find(option => option.dataset.marketInviteOption === selection);
      if (!template) return;
      invitation.append(template.content.cloneNode(true));
      invitation.dataset.selection = selection;
    }
    // Read the actual CSS grid, so existing responsive breakpoints stay authoritative.
    const columns = getComputedStyle(grid).gridTemplateColumns.split(/\s+/).length;
    const count = [...grid.querySelectorAll('[data-market-card]')].filter(card => !card.hidden).length;
    const remainder = count % columns;
    const span = count && columns > 1 && remainder ? columns - remainder : 0;
    const hidden = !span;
    if (invitation.hidden !== hidden) invitation.hidden = hidden;
    invitation.style.gridColumn = span ? `span ${span}` : '';
    invitation.dataset.span = String(span);
    // Sorting moves the original market nodes. Always follow the last market.
    if (invitation.nextElementSibling) grid.append(invitation);
  }

  function hydrate() {
    for (const [grid, observers] of grids) {
      if (!grid.isConnected) {
        observers.forEach(observer => observer.disconnect());
        grids.delete(grid);
      }
    }
    document.querySelectorAll('[data-market-invite-grid]').forEach(grid => {
      if (!grids.has(grid)) {
        const resize = new ResizeObserver(() => update(grid));
        const mutation = new MutationObserver(records => {
          if (records.some(record => record.target === grid || record.target.matches('[data-market-card]'))) update(grid);
        });
        mutation.observe(grid, {childList: true, subtree: true, attributes: true, attributeFilter: ['hidden']});
        resize.observe(grid);
        grids.set(grid, [resize, mutation]);
      }
      update(grid);
    });
  }

  document.addEventListener('click', event => {
    const link = event.target.closest('[data-market-invite-results]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const filter = link.closest('[data-market-board]')?.querySelector('[data-filter="resolved"]');
    if (!filter) return;
    event.preventDefault();
    filter.click();
    filter.focus();
  });
  window.gtlMarketGridInvite = {hydrate};
  document.addEventListener('htmx:afterSwap', hydrate);
  document.addEventListener('htmx:load', hydrate);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', hydrate, {once: true});
  else hydrate();
})();
