/* First-party, best-effort web observations. The API validates every event. */
(() => {
  if (location.pathname.startsWith('/admin-ops/') || localStorage.getItem('gtl-analytics-opt-out') === '1' || navigator.doNotTrack === '1') return;
  const cookie = document.querySelector('meta[name="csrf-token"]')?.content;
  if (!cookie) return;
  const id = () => crypto.randomUUID();
  const now = Date.now();
  let visitor = localStorage.getItem('gtl-analytics-visitor');
  if (!visitor) {
    visitor = id();
    localStorage.setItem('gtl-analytics-visitor', visitor);
  }
  let session = localStorage.getItem('gtl-analytics-session');
  const last = Number(localStorage.getItem('gtl-analytics-last') || 0);
  if (!session || now - last > 30 * 60 * 1000) {
    session = id();
    localStorage.setItem('gtl-analytics-session', session);
  }
  localStorage.setItem('gtl-analytics-last', String(now));
  let view = id();
  let queue = [];
  let sending = false;
  const utm = key => (new URLSearchParams(location.search).get(key) || '').replace(/[^a-zA-Z0-9_.-]/g, '').slice(0, 120);
  const route = () => {
    const path = location.pathname;
    if (/^\/markets\/[^/]+\//.test(path)) return 'market_detail';
    if (path.startsWith('/password-reset/')) return 'password_reset';
    if (path.startsWith('/email-confirm/')) return 'email_confirm';
    if (path.startsWith('/share/')) return 'shared_content';
    return path === '/' ? 'home' : path.replace(/^\/+|\/+$/g, '').replaceAll('/', '_')
      .replace(/[^a-zA-Z0-9_:/{}.-]/g, '_').slice(0, 80);
  };
  const market = (node) => node?.closest('[data-market-slug]')?.dataset.marketSlug ||
    location.pathname.match(/^\/markets\/([^/]+)\//)?.[1] || '';
  const event = (name, target_key = '', properties = {}) => {
    queue.push({ event_id: id(), view_id: view, name, occurred_at: new Date().toISOString(),
      screen_key: route(), target_key, properties });
    if (queue.length >= 10) flush();
  };
  async function flush() {
    if (sending || !queue.length) return;
    sending = true;
    const batch = queue.splice(0, 20);
    const payload = { visitor_id: visitor, session_id: session, entry_screen: route(),
      referrer_host: (() => { try { return new URL(document.referrer).hostname; } catch { return ''; } })(),
      utm_source: utm('utm_source'),
      utm_medium: utm('utm_medium'),
      utm_campaign: utm('utm_campaign'),
      events: batch };
    try {
      const response = await fetch('/analytics/events/', { method: 'POST', credentials: 'same-origin',
        keepalive: true, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': cookie },
        body: JSON.stringify(payload) });
      if (!response.ok && response.status >= 500) queue = batch.concat(queue).slice(0, 40);
    } catch { queue = batch.concat(queue).slice(0, 40); }
    sending = false;
  }
  const observer = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const card = entry.target;
      observer.unobserve(card);
      event('market_card_viewed', 'market_card', { market_slug: card.dataset.marketSlug, placement: route() });
    }
  }, { threshold: 0.5 }) : null;
  const watchCards = (root = document) => root.querySelectorAll('[data-market-card]').forEach(card => {
    if (card.dataset.analyticsObserved) return;
    card.dataset.analyticsObserved = '1';
    observer?.observe(card);
  });
  const pageView = () => {
    view = id();
    event('page_viewed');
    if (route() === 'market_detail') event('market_detail_viewed', '', { market_slug: market(null) });
    watchCards();
  };
  document.addEventListener('click', e => {
    const target = e.target.closest('a, button, [data-choice]');
    if (!target) return;
    const card = target.closest('[data-market-card]');
    if (target.matches('[data-filter]')) event('market_filter_applied', 'market_filter', { filter: target.dataset.filter });
    if (card && target.closest('a')) event('market_card_clicked', 'market_card', { market_slug: card.dataset.marketSlug, placement: route() });
    else if (target.matches('[data-choice]')) {
      if (!window.gtlAnalyticsPredictionStarted) {
        event('prediction_started', 'prediction_ticket', { market_slug: market(target) });
        window.gtlAnalyticsPredictionStarted = true;
      }
      event('prediction_option_selected', 'prediction_option', { market_slug: market(target) });
    }
    else if (target.closest('[data-share-native], [data-share-track], [data-share-badge]')) event('share_started', 'share', { kind: 'web' });
    else if (target.closest('.badge-share-link')) event('badge_share_clicked', 'badge_share');
    else if (target.closest('.notification-item')) event('notification_opened', 'notification', { kind: 'web' });
    else if (target.closest('[data-copy-share]')) event('link_copied', 'share_link', { kind: 'web' });
    else if (target.closest('[data-integrity-modal-link]')) event('integrity_opened', 'integrity', { market_slug: market(target) });
    else if (target.matches('a[href]')) event('navigation_clicked', 'link');
    if (target.matches('a[href="/logout/"]')) {
      localStorage.removeItem('gtl-analytics-visitor');
      localStorage.removeItem('gtl-analytics-session');
    }
  });
  document.addEventListener('submit', e => {
    const form = e.target;
    if (form.matches('[data-prediction-preview-url]')) event('prediction_submit_clicked', 'prediction_form', { market_slug: market(form) });
    else if (form.matches('[data-position-preview-url]')) event('position_submit_clicked', 'position_form', { market_slug: market(form), action: form.querySelector('[name="action"]')?.value || 'position' });
    else if (form.matches('[data-market-like-form]')) event('market_like_clicked', 'like', { market_slug: market(form) });
    else if (form.matches('[data-market-favorite-form]')) event('market_favorite_clicked', 'favorite', { market_slug: market(form) });
    else if (form.action.includes('/comments/') && form.action.includes('/reaction/')) event('comment_reaction_clicked', 'reaction', { market_slug: market(form) });
    else if (form.action.includes('/comments/')) event('comment_submit_clicked', 'comment_form', { market_slug: market(form) });
    else if (form.action.includes('/wallet/recharge-request/')) event('recharge_submit_clicked', 'recharge_form');
    else if (location.pathname === '/suggestion/') event('suggestion_submit_clicked', 'suggestion_form');
    else if (location.pathname === '/feedback/') event('feedback_submit_clicked', 'feedback_form');
    else if (location.pathname === '/profile/') event('profile_update_clicked', 'profile_form');
    else if (location.pathname === '/register/') event('signup_started', 'register_form');
    else if (location.pathname === '/login/') event('login_started', 'login_form');
  });
  document.addEventListener('change', e => {
    if (e.target.closest('[data-filter-group], [data-ranking-filters]')) event('market_filter_applied', 'filter', { filter: 'selected' });
  });
  const milestones = new Set();
  window.addEventListener('scroll', () => {
    const full = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const pct = Math.round((scrollY / full) * 100);
    for (const mark of [25, 50, 75, 100]) {
      if (pct >= mark && !milestones.has(mark)) {
        milestones.add(mark);
        event('scroll_reached', 'page', { percent: mark });
      }
    }
  }, { passive: true });
  document.addEventListener('htmx:afterSwap', e => watchCards(e.target));
  document.addEventListener('htmx:pushedIntoHistory', pageView);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') flush(); });
  setInterval(flush, 5000);
  pageView();
})();
