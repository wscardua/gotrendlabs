const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

const storedTheme = localStorage.getItem("gotrendlabs-theme");
document.body.dataset.theme = storedTheme || document.body.dataset.theme || "light";

function syncThemeButtons() {
  $$("[data-theme-toggle]").forEach((button) => {
    button.textContent = document.body.dataset.theme === "dark" ? "☀" : "◐";
    button.title = document.body.dataset.theme === "dark" ? "Usar modo claro" : "Usar dark mode";
  });
}

$$("[data-theme-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    document.body.dataset.theme = document.body.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("gotrendlabs-theme", document.body.dataset.theme);
    syncThemeButtons();
  });
});

syncThemeButtons();

$$("[data-context-back]").forEach((link) => {
  let safeReferrer = "";
  try {
    const referrer = document.referrer ? new URL(document.referrer) : null;
    if (referrer && referrer.origin === window.location.origin && referrer.href !== window.location.href) {
      safeReferrer = `${referrer.pathname}${referrer.search}${referrer.hash}`;
    }
  } catch (error) {
    safeReferrer = "";
  }
  if (safeReferrer) {
    link.href = safeReferrer;
    link.addEventListener("click", (event) => {
      if (window.history.length <= 1) return;
      event.preventDefault();
      window.history.back();
    });
  }
});

const integrityDialog = $("[data-integrity-dialog]");
const integrityDialogBody = $("[data-integrity-dialog-body]", integrityDialog || document);
const integrityDialogCache = new Map();
let integrityDialogTrigger = null;

function integrityLoadingMarkup(kind = "integrity") {
  const isReceipt = kind === "receipt";
  const title = isReceipt ? "Abrindo o comprovante" : "Conferindo os registros";
  const detail = isReceipt ? "Validando a assinatura desta ação." : "Isso deve levar apenas um instante.";
  return `<div class="integrity-dialog-loading" role="status"><span aria-hidden="true"></span><strong>${title}</strong><small>${detail}</small></div>`;
}

async function openIntegrityDialog(link) {
  if (!integrityDialog?.showModal || !integrityDialogBody) return;
  integrityDialogTrigger = link;
  const sourceUrl = new URL(link.href, window.location.href);
  const cacheKey = sourceUrl.pathname;
  const modalKind = link.dataset.integrityModalKind || "integrity";
  sourceUrl.searchParams.set("modal", "1");
  integrityDialogBody.innerHTML = integrityLoadingMarkup(modalKind);
  integrityDialog.setAttribute("aria-busy", "true");
  integrityDialog.showModal();

  try {
    let markup = integrityDialogCache.get(cacheKey);
    if (!markup) {
      const response = await fetch(sourceUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error("verification_unavailable");
      markup = await response.text();
      integrityDialogCache.set(cacheKey, markup);
    }
    integrityDialogBody.innerHTML = markup;
    integrityDialogBody.scrollTop = 0;
  } catch (_error) {
    integrityDialogBody.innerHTML = '<div class="integrity-dialog-load-error" role="alert"><span aria-hidden="true">!</span><strong>Não foi possível abrir a verificação</strong><p>Confira sua conexão e tente novamente.</p></div>';
  } finally {
    integrityDialog.removeAttribute("aria-busy");
  }
}

document.addEventListener("click", (event) => {
  const link = event.target.closest("[data-integrity-modal-link]");
  if (!link || !integrityDialog?.showModal) return;
  event.preventDefault();
  openIntegrityDialog(link);
});

$("[data-integrity-dialog-close]", integrityDialog || document)?.addEventListener("click", () => {
  integrityDialog?.close();
});

integrityDialog?.addEventListener("click", (event) => {
  if (event.target === integrityDialog) integrityDialog.close();
});

integrityDialog?.addEventListener("close", () => {
  integrityDialogTrigger?.focus();
  integrityDialogTrigger = null;
});

$$("[data-menu-chip]").forEach((chip) => {
  const button = $("[data-menu-button]", chip);
  if (!button) return;
  const setExpanded = (expanded) => button.setAttribute("aria-expanded", expanded ? "true" : "false");
  chip.addEventListener("focusin", () => setExpanded(true));
  chip.addEventListener("focusout", (event) => {
    if (!chip.contains(event.relatedTarget)) setExpanded(false);
  });
  chip.addEventListener("mouseenter", () => setExpanded(true));
  chip.addEventListener("mouseleave", () => setExpanded(false));
});

function parseNumber(value) {
  const normalized = String(value || "0").replace(/\./g, "").replace(",", ".");
  const match = normalized.match(/-?\d+(\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

function parseDateScore(value, fallback = 0) {
  const timestamp = Date.parse(value || "");
  return Number.isNaN(timestamp) ? fallback : timestamp;
}

function marketSortValue(card) {
  return {
    closeAt: parseDateScore(card.dataset.marketCloseAt, Number.POSITIVE_INFINITY),
    createdAt: parseDateScore(card.dataset.marketCreatedAt),
    featured: card.dataset.marketFeatured === "true" ? 1 : 0,
    favorited: card.dataset.marketFavorited === "true" ? 1 : 0,
    likes: parseNumber(card.dataset.marketLikes),
    originalOrder: parseNumber(card.dataset.originalOrder),
    status: card.dataset.marketStatus || "",
    views: parseNumber(card.dataset.marketViews),
    volume: parseNumber(card.dataset.marketVolume),
  };
}

function compareMarkets(mode, a, b) {
  const left = marketSortValue(a);
  const right = marketSortValue(b);
  const tieBreak = right.createdAt - left.createdAt || left.originalOrder - right.originalOrder;
  if (mode === "volume") {
    return right.volume - left.volume || tieBreak;
  }
  if (mode === "likes") {
    return right.likes - left.likes || tieBreak;
  }
  if (mode === "new") {
    return right.createdAt - left.createdAt || left.originalOrder - right.originalOrder;
  }
  if (mode === "featured") {
    return right.featured - left.featured || right.likes - left.likes || tieBreak;
  }
  return right.views - left.views || tieBreak;
}

function marketMatchesMode(card, mode) {
  return !(
    (mode === "resolved" && card.dataset.marketStatus !== "resolved") ||
    (mode === "open" && card.dataset.marketStatus !== "open") ||
    (mode === "closing" && card.dataset.marketStatus !== "locked") ||
    (mode === "favorited" && card.dataset.marketFavorited !== "true") ||
    (mode === "predicted" && card.dataset.marketPredicted !== "true")
  );
}

function renderMarketChunk(list, mode, requestedVisibleCount) {
  const cards = $$("[data-market-card]", list);
  const pageSize = Math.max(1, Number(list.dataset.marketPageSize || 18));
  const matchingCards = cards.filter((card) => marketMatchesMode(card, mode));
  const visibleCount = Math.min(
    Math.max(pageSize, Number(requestedVisibleCount || pageSize)),
    Math.max(pageSize, matchingCards.length),
  );

  cards.forEach((card) => {
    const matchIndex = matchingCards.indexOf(card);
    card.hidden = matchIndex < 0 || matchIndex >= visibleCount;
  });

  const empty = list.parentElement?.querySelector("[data-market-empty]");
  if (empty) {
    const emptyMessages = {
      favorited: "Nenhum mercado favorito ainda.",
      predicted: "Nenhum mercado com previsão sua ainda.",
    };
    empty.textContent = emptyMessages[mode] || "";
    empty.hidden = !(emptyMessages[mode] && matchingCards.length === 0);
  }

  const loadMore = list.parentElement?.querySelector("[data-market-load-more]");
  if (loadMore) {
    const shownCount = Math.min(visibleCount, matchingCards.length);
    const summary = $("[data-market-load-more-summary]", loadMore);
    const button = $("[data-market-load-more-button]", loadMore);
    loadMore.hidden = matchingCards.length <= pageSize || shownCount >= matchingCards.length;
    if (summary) summary.textContent = `Exibindo ${shownCount} de ${matchingCards.length} mercados`;
    if (button) button.disabled = shownCount >= matchingCards.length;
  }

  list.dataset.marketVisibleCount = String(visibleCount);
}

function sortMarketList(group, mode, visibleCount) {
  const target = group.dataset.filterTarget;
  const list = target ? $(target) : null;
  if (!list) return;
  list.dataset.marketFilterMode = mode;
  const cards = $$("[data-market-card]", list);
  cards.sort((a, b) => compareMarkets(mode, a, b));
  cards.forEach((card) => list.appendChild(card));
  renderMarketChunk(list, mode, visibleCount);
}

$$("[data-market-card]").forEach((card, index) => {
  card.dataset.originalOrder = String(index);
});

function clampPercent(value) {
  if (!Number.isFinite(value)) return 100;
  return Math.max(0, Math.min(100, value));
}

function deadlineState(timeLeft, status) {
  if (timeLeft <= 0 || ["locked", "resolved", "canceled"].includes(status)) return "closed";
  if (timeLeft <= 12) return "urgent";
  if (timeLeft <= 32) return "soon";
  return "open";
}

const deadlineAccent = {
  open: "#136f4a",
  soon: "#d89422",
  urgent: "#b7493d",
  closed: "#b7493d",
};

function hydrateDeadlineRail(card) {
  const rail = $("[data-deadline-rail]", card);
  if (!rail) return;
  const createdAt = parseDateScore(card.dataset.marketCreatedAt);
  const closeAt = parseDateScore(card.dataset.marketCloseAt);
  const status = card.dataset.marketStatus || "";
  let timeLeft = 0;
  if (closeAt && !["resolved", "canceled"].includes(status)) {
    const startAt = createdAt && createdAt < closeAt ? createdAt : Date.now();
    const total = Math.max(1, closeAt - startAt);
    const remaining = closeAt - Date.now();
    timeLeft = clampPercent((remaining / total) * 100);
  }
  const state = deadlineState(timeLeft, status);
  ["open", "soon", "urgent", "closed"].forEach((name) => rail.classList.toggle(name, state === name));
  rail.dataset.deadlineState = state;
  rail.style.setProperty("--time-left", `${timeLeft}%`);
  rail.style.setProperty("--deadline-accent", deadlineAccent[state] || deadlineAccent.open);
}

$$("[data-market-card]").forEach(hydrateDeadlineRail);
if ($("[data-deadline-rail]")) {
  window.setInterval(() => $$("[data-market-card]").forEach(hydrateDeadlineRail), 60000);
}

function syncFilterPressedState(group, activeButton) {
  $$("[data-filter]", group).forEach((item) => {
    const isActive = item === activeButton;
    item.classList.toggle("active", isActive);
    item.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
}

$$("[data-filter-group]").forEach((group) => {
  const active = $(".filter.active[data-filter]", group) || $("[data-filter]", group);
  if (active) syncFilterPressedState(group, active);
});

$$("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const group = button.closest("[data-filter-group]");
    syncFilterPressedState(group, button);
    sortMarketList(group, button.dataset.filter || "trending");
  });
});

$$("[data-filter-group][data-filter-target]").forEach((group) => {
  const active = $(".filter.active[data-filter]", group) || $("[data-filter]", group);
  if (active) sortMarketList(group, active.dataset.filter || "trending");
});

$$("[data-market-load-more-button]").forEach((button) => {
  button.addEventListener("click", () => {
    const section = button.closest("section");
    const list = section ? $("[data-market-list]", section) : null;
    const group = section ? $("[data-filter-group][data-filter-target]", section) : null;
    if (!list || !group) return;
    const pageSize = Math.max(1, Number(list.dataset.marketPageSize || 18));
    const nextVisibleCount = Number(list.dataset.marketVisibleCount || pageSize) + pageSize;
    sortMarketList(group, list.dataset.marketFilterMode || "trending", nextVisibleCount);
  });
});

function syncMarketFavorite(slug, favorited) {
  const value = favorited ? "true" : "false";
  $$(`[data-market-slug="${slug}"]`).forEach((element) => {
    if (element.dataset.marketCard !== undefined) element.dataset.marketFavorited = value;
  });
  $$(`[data-market-favorite-form][data-market-slug="${slug}"]`).forEach((form) => {
    const input = $("[data-market-favorite-current]", form);
    const button = $("[data-market-favorite-button]", form);
    if (input) input.value = value;
    if (button) {
      button.classList.toggle("active", favorited);
      const label = favorited ? "Remover dos favoritos" : "Adicionar aos favoritos";
      button.setAttribute("aria-label", label);
      button.title = label;
      button.disabled = false;
    }
  });
  $$("[data-filter-group][data-filter-target]").forEach((group) => {
    const list = $(group.dataset.filterTarget);
    if (list?.dataset.marketFilterMode === "favorited") {
      sortMarketList(group, "favorited", Number(list.dataset.marketVisibleCount || list.dataset.marketPageSize || 18));
    }
  });
}

function marketLikeLabel(count) {
  return `${count} ${count === 1 ? "curtida" : "curtidas"}`;
}

function renderMarketLikeCount(element, count) {
  element.textContent = element.dataset.marketLikeFormat === "short" ? String(count) : marketLikeLabel(count);
}

function syncMarketLike(slug, liked, likeCount) {
  const value = liked ? "true" : "false";
  $$(`[data-market-slug="${slug}"]`).forEach((element) => {
    if (element.dataset.marketCard !== undefined) {
      element.dataset.marketLiked = value;
      element.dataset.marketLikes = String(likeCount);
    }
  });
  $$(`[data-market-like-form][data-market-slug="${slug}"]`).forEach((form) => {
    const input = $("[data-market-like-current]", form);
    const button = $("[data-market-like-button]", form);
    const count = $("[data-market-like-count]", form);
    if (input) input.value = value;
    if (count) renderMarketLikeCount(count, likeCount);
    if (button) {
      button.classList.toggle("active", liked);
      const actionLabel = liked ? "Remover curtida" : "Curtir mercado";
      button.setAttribute("aria-label", actionLabel);
      button.title = actionLabel;
      button.disabled = false;
    }
  });
  $$(`[data-market-card][data-market-slug="${slug}"] [data-market-like-count]`).forEach((count) => {
    renderMarketLikeCount(count, likeCount);
  });
}

$$("[data-market-like-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    if (!window.fetch) return;
    event.preventDefault();
    const button = $("[data-market-like-button]", form);
    if (button) button.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {"X-Requested-With": "XMLHttpRequest"},
        credentials: "same-origin",
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error || "like failed");
      syncMarketLike(payload.slug || form.dataset.marketSlug, Boolean(payload.liked), Number(payload.like_count || 0));
    } catch (error) {
      if (button) button.disabled = false;
      form.submit();
    }
  });
});

let guestAuthNoticeTimeout = null;

function showGuestAuthNotice(message) {
  let notice = $("[data-guest-auth-notice]");
  if (!notice) {
    notice = document.createElement("div");
    notice.className = "market-auth-toast";
    notice.dataset.guestAuthNotice = "true";
    notice.setAttribute("role", "status");
    notice.setAttribute("aria-live", "polite");
    document.body.appendChild(notice);
  }
  notice.textContent = message;
  notice.hidden = false;
  notice.classList.add("visible");
  window.clearTimeout(guestAuthNoticeTimeout);
  guestAuthNoticeTimeout = window.setTimeout(() => {
    notice.classList.remove("visible");
    notice.hidden = true;
  }, 3600);
}

$$("[data-guest-like-button]").forEach((button) => {
  button.addEventListener("click", () => {
    showGuestAuthNotice("Curtir mercados é permitido apenas para usuários logados.");
  });
});

$$("[data-guest-favorite-button]").forEach((button) => {
  button.addEventListener("click", () => {
    showGuestAuthNotice("Favoritar mercados é permitido apenas para usuários logados.");
  });
});

$$("[data-market-favorite-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    if (!window.fetch) return;
    event.preventDefault();
    const button = $("[data-market-favorite-button]", form);
    if (button) button.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {"X-Requested-With": "XMLHttpRequest"},
        credentials: "same-origin",
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.error || "favorite failed");
      syncMarketFavorite(payload.slug || form.dataset.marketSlug, Boolean(payload.favorited));
    } catch (error) {
      if (button) button.disabled = false;
      form.submit();
    }
  });
});

function syncRankingSubcategories(form) {
  const categorySelect = $("[data-ranking-category]", form);
  const subcategorySelect = $("[data-ranking-subcategory]", form);
  const eventSelect = $("[data-ranking-event]", form);
  if (!categorySelect || !subcategorySelect) return;
  const category = categorySelect.value;
  let selectedStillVisible = false;
  $$("option", subcategorySelect).forEach((option) => {
    const isPlaceholder = !option.value;
    const matches = isPlaceholder || (category && option.dataset.category === category);
    option.hidden = !matches;
    option.disabled = !matches;
    if (matches && option.selected && !isPlaceholder) selectedStillVisible = true;
  });
  subcategorySelect.disabled = !category;
  if (!selectedStillVisible) {
    subcategorySelect.value = "";
  }
  syncRankingEvents(form);
}

function syncRankingEvents(form) {
  const categorySelect = $("[data-ranking-category]", form);
  const subcategorySelect = $("[data-ranking-subcategory]", form);
  const eventSelect = $("[data-ranking-event]", form);
  if (!categorySelect || !subcategorySelect || !eventSelect) return;
  const category = categorySelect.value;
  const subcategory = subcategorySelect.value;
  let selectedStillVisible = false;
  $$("option", eventSelect).forEach((option) => {
    const isPlaceholder = !option.value;
    const matches = isPlaceholder || (category && subcategory && option.dataset.category === category && option.dataset.subcategory === subcategory);
    option.hidden = !matches;
    option.disabled = !matches;
    if (matches && option.selected && !isPlaceholder) selectedStillVisible = true;
  });
  eventSelect.disabled = !category || !subcategory;
  if (!selectedStillVisible) {
    eventSelect.value = "";
  }
}

$$("[data-ranking-filters]").forEach((form) => {
  $("[data-ranking-category]", form)?.addEventListener("change", () => syncRankingSubcategories(form));
  $("[data-ranking-subcategory]", form)?.addEventListener("change", () => syncRankingEvents(form));
  syncRankingSubcategories(form);
});

function initTaxonomyBrowser(browser) {
  const triggers = $$("[data-taxonomy-category-trigger]", browser);
  const panels = $$("[data-taxonomy-panel]", browser);
  const empty = $("[data-taxonomy-empty]", browser);
  const search = $("[data-taxonomy-search]", browser);
  const filters = $$("[data-taxonomy-filter]", browser);
  let activeSlug = triggers.find((trigger) => trigger.classList.contains("active"))?.dataset.taxonomyCategoryTrigger || triggers[0]?.dataset.taxonomyCategoryTrigger || "";
  let mode = filters.find((filter) => filter.classList.contains("active"))?.dataset.taxonomyFilter || "all";

  function showPanel(slug) {
    activeSlug = slug;
    triggers.forEach((trigger) => {
      const isActive = trigger.dataset.taxonomyCategoryTrigger === slug;
      trigger.classList.toggle("active", isActive);
      trigger.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.taxonomyPanel !== slug;
    });
  }

  function matchesFilter(trigger) {
    const markets = Number(trigger.dataset.marketsCount || 0);
    const blocked = trigger.dataset.blocked === "true";
    const query = (search?.value || "").trim().toLowerCase();
    const text = trigger.dataset.taxonomyName || "";
    const matchesQuery = !query || text.includes(query);
    const matchesMode =
      mode === "all" ||
      (mode === "with-markets" && markets > 0) ||
      (mode === "without-markets" && markets === 0) ||
      (mode === "blocked" && blocked);
    return matchesQuery && matchesMode;
  }

  function applyFilters() {
    let firstVisible = "";
    triggers.forEach((trigger) => {
      const visible = matchesFilter(trigger);
      trigger.hidden = !visible;
      if (visible && !firstVisible) firstVisible = trigger.dataset.taxonomyCategoryTrigger;
    });
    if (empty) empty.hidden = Boolean(firstVisible);
    if (!firstVisible) {
      panels.forEach((panel) => {
        panel.hidden = true;
      });
      return;
    }
    const activeStillVisible = triggers.some((trigger) => trigger.dataset.taxonomyCategoryTrigger === activeSlug && !trigger.hidden);
    showPanel(activeStillVisible ? activeSlug : firstVisible);
  }

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", () => showPanel(trigger.dataset.taxonomyCategoryTrigger));
  });
  filters.forEach((filter) => {
    filter.addEventListener("click", () => {
      mode = filter.dataset.taxonomyFilter || "all";
      filters.forEach((item) => item.classList.remove("active"));
      filter.classList.add("active");
      applyFilters();
    });
  });
  search?.addEventListener("input", applyFilters);
  applyFilters();
}

$$("[data-taxonomy-browser]").forEach(initTaxonomyBrowser);

document.addEventListener("click", (event) => {
  const choice = event.target.closest("[data-choice]");
  if (!choice) return;
  const group = choice.closest(".option-grid");
  const form = choice.closest("form");
  if (group) {
    $$(".choice", group).forEach((item) => item.classList.remove("active"));
  }
  choice.classList.add("active");
  const radio = $("input[name='option_id']", choice);
  if (radio) radio.checked = true;
  const target = form ? $("[data-selected-choice]", form) : $("[data-selected-choice]");
  if (target) target.textContent = choice.dataset.choice;
  const optionInput = form ? $("[data-selected-option-id]:checked", form) || $("[data-selected-option-id]", form) : $("[data-selected-option-id]:checked") || $("[data-selected-option-id]");
  if (optionInput && choice.dataset.optionId && optionInput.type === "hidden") optionInput.value = choice.dataset.optionId;
  const submit = form ? $("[data-requires-choice]", form) : null;
  if (submit) {
    submit.disabled = false;
    submit.removeAttribute("disabled");
  }
  updatePredictionPreview();
});

function updatePredictionPreview() {
  $$("[data-amount]").forEach((range) => {
    const amount = Number(range.value || 0);
    const output = $(`[data-amount-output="${range.dataset.amount}"]`);
    if (output) output.textContent = `${range.value} GT₵`;
    const lockedBox = $(`[data-locked-output="${range.dataset.amount}"]`);
    if (lockedBox) lockedBox.textContent = `${range.value} GT₵`;
  });
  const form = $("[data-prediction-preview-url]");
  const preview = $("#prediction-preview");
  if (!form || !preview) return;
  const optionInput = $("[data-selected-option-id]:checked", form) || $("[data-selected-option-id][type='hidden']", form);
  if (!optionInput?.value) return;
  const body = new FormData(form);
  fetch(form.dataset.predictionPreviewUrl, {
    method: "POST",
    body,
    credentials: "same-origin",
    headers: {"X-Requested-With": "XMLHttpRequest"},
  })
    .then((response) => response.text())
    .then((html) => {
      preview.innerHTML = html;
    })
    .catch(() => {});
}

function updatePositionActionPreview(form) {
  const targetId = form.dataset.previewTarget;
  const preview = targetId ? document.getElementById(targetId) : null;
  if (!preview) return;
  const optionInput = $("[data-selected-option-id]:checked", form) || $("[name='option_id'][type='hidden']", form);
  if (!optionInput?.value) return;
  const body = new FormData(form);
  fetch(form.dataset.positionPreviewUrl, {
    method: "POST",
    body,
    credentials: "same-origin",
    headers: {"X-Requested-With": "XMLHttpRequest"},
  })
    .then((response) => response.text())
    .then((html) => {
      preview.innerHTML = html;
    })
    .catch(() => {});
}

$$("[data-amount]").forEach((range) => {
  range.addEventListener("input", updatePredictionPreview);
  range.addEventListener("input", () => {
    const form = range.closest("[data-position-preview-url]");
    if (form) updatePositionActionPreview(form);
  });
  updatePredictionPreview();
});

$$("[data-position-preview-url]").forEach((form) => {
  form.addEventListener("change", () => updatePositionActionPreview(form));
  updatePositionActionPreview(form);
});

let pendingConfirmTrigger = null;

function runConfirmedAction(trigger) {
  if (!trigger) return;
  const form = trigger.closest("form");
  if (form && trigger.type === "submit") {
    form.requestSubmit(trigger);
    return;
  }
  const href = trigger.getAttribute("href");
  if (href && href !== "#") {
    window.location.href = href;
  }
}

$$("[data-confirm]").forEach((trigger) => {
  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    const form = trigger.closest("form");
    if (form && trigger.type === "submit" && !form.reportValidity()) return;
    const modal = $("#confirm-modal");
    if (!modal) return;
    pendingConfirmTrigger = trigger;
    $("[data-confirm-title]", modal).textContent = trigger.dataset.confirm;
    $("[data-confirm-desc]", modal).textContent = trigger.dataset.confirmDesc || "Esta ação fica registrada na trilha de auditoria.";
    modal.classList.add("show");
  });
});

document.addEventListener("click", (event) => {
  const modalTrigger = event.target.closest("[data-open-modal]");
  if (modalTrigger) {
    const modal = $(modalTrigger.dataset.openModal);
    if (!modal) return;
    event.preventDefault();
    pendingConfirmTrigger = null;
    modal.classList.add("show");
    const focusTarget = $("[data-close-modal], a, button, input, select, textarea", modal);
    if (focusTarget) focusTarget.focus();
    return;
  }

  const closeButton = event.target.closest("[data-close-modal]");
  if (!closeButton) return;
  const modal = closeButton.closest(".modal");
  const shouldRun = closeButton.classList.contains("primary") && pendingConfirmTrigger;
  if (modal) modal.classList.remove("show");
  if (shouldRun) {
    const trigger = pendingConfirmTrigger;
    pendingConfirmTrigger = null;
    runConfirmedAction(trigger);
    return;
  }
  pendingConfirmTrigger = null;
});

function showFeedbackModal(title, desc) {
  const modal = $("#confirm-modal");
  if (!modal) return;
  pendingConfirmTrigger = null;
  $("[data-confirm-title]", modal).textContent = title;
  $("[data-confirm-desc]", modal).textContent = desc;
  modal.classList.add("show");
}

async function copyShareText(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (error) {
    return false;
  }
  return false;
}

function trackShareAction(url) {
  if (!url) return;
  try {
    if (navigator.sendBeacon) {
      const body = new Blob(["{}"], { type: "application/json" });
      if (navigator.sendBeacon(url, body)) return;
    }
  } catch (error) {
    // Tracking must never block the share action.
  }
  try {
    fetch(url, {
      method: "POST",
      credentials: "same-origin",
      keepalive: true,
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }).catch(() => {});
  } catch (error) {
    // Ignore unsupported keepalive/fetch combinations.
  }
}

$$("[data-share-track]:not([data-share-native]):not([data-share-badge])").forEach((trigger) => {
  trigger.addEventListener("click", () => {
    trackShareAction(trigger.dataset.shareTrack);
  });
});

$$("[data-share-native], [data-share-badge]").forEach((button) => {
  button.addEventListener("click", async () => {
    trackShareAction(button.dataset.shareTrack);
    const shareData = {
      title: button.dataset.shareTitle || "GoTrendLabs",
      text: button.dataset.shareText || "",
      url: button.dataset.shareUrl || window.location.href,
    };
    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        if (error?.name !== "AbortError") showFeedbackModal("Compartilhamento indisponível", "Tente copiar o link da conquista.");
      }
      return;
    }
    const copied = await copyShareText(`${shareData.text} ${shareData.url}`.trim());
    showFeedbackModal(copied ? "Compartilhamento copiado" : "Compartilhamento indisponível", copied ? "Texto e link prontos para colar onde preferir." : "Não foi possível acessar a área de transferência neste navegador.");
  });
});

$$("[data-copy-share]").forEach((button) => {
  button.addEventListener("click", async () => {
    const copied = await copyShareText(button.dataset.shareText || window.location.href);
    showFeedbackModal(copied ? "Link copiado" : "Cópia indisponível", copied ? "O conteúdo está pronto para colar e compartilhar." : "Não foi possível acessar a área de transferência neste navegador.");
  });
});

function setVisibility(element, visible) {
  if (!element) return;
  element.hidden = !visible;
  element.classList.toggle("is-hidden", !visible);
}

function updateAdminMarketOptions(form) {
  const kind = $('[name="kind"]', form)?.value || "binary";
  const binaryBox = $("[data-binary-options]", form);
  const multipleBox = $("[data-multiple-options]", form);
  const addButton = $("[data-add-option]", form);
  const help = $("[data-option-help]", form);
  const isBinary = kind === "binary";

  setVisibility(binaryBox, isBinary);
  setVisibility(multipleBox, !isBinary);
  setVisibility(addButton, !isBinary);
  if (help) {
    help.textContent = isBinary
      ? "Sim/Não usa duas opções fixas com probabilidade inicial balanceada."
      : "Múltipla escolha distribui o percentual decimal igualmente entre todas as opções preenchidas.";
  }
  $$('input[name="option_label"], input[name="option_hint"]', form).forEach((input) => {
    input.disabled = isBinary;
  });

  const rows = $$("[data-multiple-options] .dynamic-option", form);
  const activeRows = rows.filter((row) => $('input[name="option_label"]', row)?.value.trim());
  const count = Math.max(activeRows.length || rows.length, 1);
  const display = Math.floor(100 / count);
  rows.forEach((row) => {
    const label = $('input[name="option_label"]', row);
    const output = $("[data-option-percent]", row);
    if (!output) return;
    if (label && !label.value.trim() && activeRows.length) {
      output.textContent = "0%";
      return;
    }
    output.textContent = `${display}%`;
  });
}

function fieldValue(form, name, fallback = "") {
  return $(`[name="${name}"]`, form)?.value.trim() || fallback;
}

function updateMarketPreview(form) {
  const preview = $("[data-market-preview]");
  if (!preview) return;
  const color = fieldValue(form, "thumb_color", "#d8ece2");
  const thumb = fieldValue(form, "thumb", "MK").slice(0, 4).toUpperCase();
  const kind = fieldValue(form, "kind", "binary");
  const title = fieldValue(form, "title", "Novo mercado");
  const category = fieldValue(form, "category", "Categoria");
  const subcategory = fieldValue(form, "subcategory", "Subcategoria");
  const eventName = fieldValue(form, "event", "Evento");
  const summary = fieldValue(form, "summary", "Resumo do mercado aparece aqui conforme você preenche.");

  const thumbBox = $("[data-preview-thumb]", preview);
  const thumbText = $("[data-preview-thumb-text]", preview);
  if (thumbBox) thumbBox.style.setProperty("--thumb", color);
  if (thumbText) thumbText.textContent = thumb;
  $("[data-preview-title]", preview).textContent = title;
  $("[data-preview-category]", preview).textContent = category;
  $("[data-preview-subcategory]", preview).textContent = subcategory;
  const eventPreview = $("[data-preview-event]", preview);
  if (eventPreview) eventPreview.textContent = eventName;
  $("[data-preview-kind]", preview).textContent = kind === "multiple" ? "Múltipla escolha" : "Sim/Não";
  $("[data-preview-summary]", preview).textContent = summary;
  const bar = $("[data-preview-bar]", preview);
  if (bar) {
    const filledOptions = $$("[data-multiple-options] .dynamic-option", form)
      .filter((row) => $('input[name="option_label"]', row)?.value.trim());
    const optionCount = Math.max(filledOptions.length || 2, 1);
    bar.style.width = kind === "multiple" ? `${100 / optionCount}%` : "50%";
  }
}

function updateBadgePreview(form) {
  const preview = $("[data-badge-preview]");
  if (!preview) return;
  const name = fieldValue(form, "name", "Nome da badge");
  const description = fieldValue(form, "description", "Descrição curta da conquista aparece aqui.");
  const rule = fieldValue(form, "rule_description", "Descrição da regra aparece aqui.");
  const isActive = $('[name="is_active"]', form)?.checked ?? true;
  const ruleActive = $('[name="rule_active"]', form)?.checked ?? true;
  const lightUrl = fieldValue(form, "image_url", "");
  const darkUrl = fieldValue(form, "image_dark_url", "");
  const lightImage = $("[data-preview-badge-image-light]", preview);
  const darkImage = $("[data-preview-badge-image-dark]", preview);
  const icon = $("[data-preview-badge-icon]", preview);

  $("[data-preview-badge-name]", preview).textContent = name;
  $("[data-preview-badge-description]", preview).textContent = description;
  $("[data-preview-badge-rule]", preview).textContent = rule;
  $("[data-preview-badge-status]", preview).textContent = !isActive ? "Oculta" : ruleActive ? "Ativa para concessão" : "Concessão pausada";
  preview.classList.toggle("locked", !isActive);

  if (form.matches("[data-ai-badge-editor]")) return;

  if (lightUrl && lightImage && lightImage.dataset.localPreview !== "1") {
    lightImage.src = lightUrl;
    lightImage.classList.remove("is-hidden");
  } else if (!lightUrl && lightImage && lightImage.dataset.localPreview !== "1") {
    lightImage.classList.add("is-hidden");
  }

  if (darkUrl && darkImage && darkImage.dataset.localPreview !== "1") {
    darkImage.src = darkUrl;
    darkImage.classList.remove("is-hidden");
  } else if (!darkUrl && darkImage && darkImage.dataset.localPreview !== "1") {
    darkImage.classList.add("is-hidden");
  }

  const hasLightImage = Boolean(lightUrl || lightImage?.dataset.localPreview === "1");
  const hasDarkImage = Boolean(darkUrl || darkImage?.dataset.localPreview === "1");
  lightImage?.classList.toggle("has-dark", hasDarkImage);
  if (hasLightImage || hasDarkImage) {
    icon?.classList.add("is-hidden");
  } else {
    icon?.classList.remove("is-hidden");
  }
}

function syncBadgeRequirementTaxonomy(row) {
  const category = $('[data-requirement-category-select]', row)?.value || "";
  const subcategorySelect = $('[data-requirement-subcategory-select]', row);
  const eventSelect = $('[data-requirement-event-select]', row);
  if (subcategorySelect) {
    $$("option", subcategorySelect).forEach((option) => {
      const optionCategory = option.dataset.category || "";
      option.hidden = Boolean(option.value && category && optionCategory !== category);
      if (option.hidden && option.selected) subcategorySelect.value = "";
    });
  }
  const subcategory = subcategorySelect?.value || "";
  if (eventSelect) {
    $$("option", eventSelect).forEach((option) => {
      const optionCategory = option.dataset.category || "";
      const optionSubcategory = option.dataset.subcategory || "";
      option.hidden = Boolean(
        option.value &&
          ((category && optionCategory !== category) || (subcategory && optionSubcategory !== subcategory))
      );
      if (option.hidden && option.selected) eventSelect.value = "";
    });
  }
}

function reindexBadgeRequirements(form) {
  const rows = $$("[data-badge-requirement-row]", form);
  rows.forEach((row, index) => {
    $$("[name]", row).forEach((field) => {
      field.name = field.name.replace(/requirements_\d+_/, `requirements_${index}_`);
    });
    syncBadgeRequirementTaxonomy(row);
  });
  const count = $("[data-badge-requirement-count]", form);
  if (count) count.value = rows.length;
}

function badgeRequirementRow(form, index) {
  const metricOptions = $('[name="rule_type"]', form)?.innerHTML || "";
  const categoryOptions = $('[data-category-select]', form)?.innerHTML || "";
  const subcategoryOptions = $('[data-subcategory-select]', form)?.innerHTML || "";
  const eventOptions = $('[data-event-select]', form)?.innerHTML || "";
  const row = document.createElement("div");
  row.className = "dynamic-option";
  row.dataset.badgeRequirementRow = "1";
  row.innerHTML = `
    <div class="field">
      <label>Métrica</label>
      <select name="requirements_${index}_metric_type"><option value="">Escolha uma métrica</option>${metricOptions}</select>
    </div>
    <div class="field">
      <label>Valor mínimo/posição</label>
      <input type="number" step="0.0001" min="0" name="requirements_${index}_threshold_value" value="1">
    </div>
    <div class="field">
      <label>Categoria</label>
      <select name="requirements_${index}_category" data-requirement-category-select>${categoryOptions}</select>
    </div>
    <div class="field">
      <label>Subcategoria</label>
      <select name="requirements_${index}_subcategory" data-requirement-subcategory-select>${subcategoryOptions}</select>
    </div>
    <div class="field">
      <label>Evento</label>
      <select name="requirements_${index}_event" data-requirement-event-select>${eventOptions}</select>
    </div>
    <label class="toggle-row"><input type="checkbox" name="requirements_${index}_is_active" checked> <span>Ativo</span></label>
    <button class="btn small ghost" type="button" data-remove-badge-requirement>Remover</button>
  `;
  return row;
}

function updateAutoCloseHelp(form) {
  const autoClose = $('[name="auto_close_enabled"]', form);
  const help = $("[data-auto-close-help]", form);
  const disabledAction = $("[data-manual-close-disabled]", form);
  if (!autoClose || !help) return;
  if (autoClose.checked) {
    help.textContent = "Marcado: o daemon fechará o mercado automaticamente quando a data/hora vencer.";
    if (disabledAction) disabledAction.textContent = "Fechamento automático ativo";
    return;
  }
  help.textContent = "Desmarcado: depois de publicado, use o botão Fechar manualmente no rodapé do editor.";
  if (disabledAction) disabledAction.textContent = "Fechar manualmente após publicar";
}

function syncMarketTaxonomy(form) {
  const categorySelect = $("[data-category-select]", form);
  const subcategorySelect = $("[data-subcategory-select]", form);
  const eventSelect = $("[data-event-select]", form);
  if (!categorySelect || !subcategorySelect) return;
  const category = categorySelect.value;
  const subcategory = subcategorySelect.value;
  let selectedStillVisible = false;
  $$("option", subcategorySelect).forEach((option) => {
    const isPlaceholder = !option.value;
    const matches = isPlaceholder || (category && option.dataset.category === category);
    option.hidden = !matches;
    option.disabled = !matches;
    if (matches && option.selected && !isPlaceholder) selectedStillVisible = true;
  });
  if (!selectedStillVisible) {
    subcategorySelect.value = "";
  }
  if (!eventSelect) return;
  const previousEvent = eventSelect.value;
  let selectedEventStillVisible = false;
  $$("option", eventSelect).forEach((option) => {
    const isPlaceholder = !option.value;
    const matches = isPlaceholder || (category && subcategorySelect.value && option.dataset.category === category && option.dataset.subcategory === subcategorySelect.value);
    option.hidden = !matches;
    option.disabled = !matches;
    if (matches && option.selected && !isPlaceholder) selectedEventStillVisible = true;
  });
  if (!selectedEventStillVisible) {
    const matchingEvent = Array.from(eventSelect.options).find((option) => !option.disabled && option.value === previousEvent && option.value);
    eventSelect.selectedIndex = matchingEvent ? matchingEvent.index : 0;
  }
}

$$("[data-market-form]").forEach((form) => {
  const kind = $('[name="kind"]', form);
  const optionsBox = $("[data-multiple-options]", form);
  const addButton = $("[data-add-option]", form);
  const template = () => {
    const row = document.createElement("div");
    row.className = "option-line dynamic-option";
    row.innerHTML = `
      <input type="text" name="option_label" placeholder="Opção">
      <span class="option-percent" data-option-percent>0%</span>
      <input type="text" name="option_hint" placeholder="Hint opcional">
      <button class="icon-action danger" type="button" data-remove-option aria-label="Remover opção">×</button>
    `;
    return row;
  };

  kind?.addEventListener("change", () => updateAdminMarketOptions(form));
  $("[data-category-select]", form)?.addEventListener("change", () => {
    syncMarketTaxonomy(form);
    updateMarketPreview(form);
  });
  $("[data-subcategory-select]", form)?.addEventListener("change", () => {
    syncMarketTaxonomy(form);
    updateMarketPreview(form);
  });
  addButton?.addEventListener("click", () => {
    optionsBox?.appendChild(template());
    updateAdminMarketOptions(form);
    updateMarketPreview(form);
  });
  form.addEventListener("click", (event) => {
    if (!event.target.matches("[data-remove-option]")) return;
    const rows = $$("[data-multiple-options] .dynamic-option", form);
    if (rows.length <= 2) return;
    event.target.closest(".dynamic-option")?.remove();
    updateAdminMarketOptions(form);
    updateMarketPreview(form);
  });
  form.addEventListener("input", (event) => {
    if (event.target.matches('input[name="option_label"]')) updateAdminMarketOptions(form);
    updateMarketPreview(form);
  });
  form.addEventListener("change", (event) => {
    updateMarketPreview(form);
    updateAutoCloseHelp(form);
  });
  $$("[data-color]", form).forEach((button) => {
    button.addEventListener("click", () => {
      const input = $('[name="thumb_color"]', form);
      if (input) input.value = button.dataset.color;
      updateMarketPreview(form);
    });
  });
  updateAdminMarketOptions(form);
  syncMarketTaxonomy(form);
  updateMarketPreview(form);
  updateAutoCloseHelp(form);
});

$$("[data-taxonomy-form]").forEach((form) => {
  syncMarketTaxonomy(form);
  $("[data-category-select]", form)?.addEventListener("change", () => syncMarketTaxonomy(form));
  $("[data-subcategory-select]", form)?.addEventListener("change", () => syncMarketTaxonomy(form));
});

$$("[data-badge-form]").forEach((form) => {
  form.addEventListener("input", () => updateBadgePreview(form));
  form.addEventListener("change", (event) => {
    if (!form.matches("[data-ai-badge-editor]") && event.target.matches('input[type="file"][name="badge_image"], input[type="file"][name="badge_dark_image"]')) {
      const file = event.target.files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.addEventListener("load", () => {
          const preview = $("[data-badge-preview]");
          const isDarkImage = event.target.name === "badge_dark_image";
          const image = isDarkImage ? $("[data-preview-badge-image-dark]", preview) : $("[data-preview-badge-image-light]", preview);
          const lightImage = $("[data-preview-badge-image-light]", preview);
          const icon = $("[data-preview-badge-icon]", preview);
          if (!image) return;
          image.src = reader.result;
          image.dataset.localPreview = "1";
          image.classList.remove("is-hidden");
          if (isDarkImage) lightImage?.classList.add("has-dark");
          icon?.classList.add("is-hidden");
        });
        reader.readAsDataURL(file);
      }
    }
    if (event.target.matches("[data-requirement-category-select], [data-requirement-subcategory-select]")) {
      syncBadgeRequirementTaxonomy(event.target.closest("[data-badge-requirement-row]"));
    }
    updateBadgePreview(form);
  });
  form.addEventListener("click", (event) => {
    if (event.target.matches("[data-add-badge-requirement]")) {
      const list = $("[data-badge-requirement-list]", form);
      const index = $$("[data-badge-requirement-row]", form).length;
      if (list) {
        list.appendChild(badgeRequirementRow(form, index));
        reindexBadgeRequirements(form);
      }
    }
    if (event.target.matches("[data-remove-badge-requirement]")) {
      event.target.closest("[data-badge-requirement-row]")?.remove();
      reindexBadgeRequirements(form);
    }
  });
  $$("[data-badge-requirement-row]", form).forEach(syncBadgeRequirementTaxonomy);
  reindexBadgeRequirements(form);
  updateBadgePreview(form);
});

$$("[data-thumb-image]").forEach((image) => {
  image.addEventListener("error", () => {
    image.hidden = true;
    image.nextElementSibling?.removeAttribute("hidden");
  });
});

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderEmailTemplatePreview(source, samples) {
  return String(source || "").replace(/{{\s*([a-zA-Z0-9_]+)\s*}}/g, (_match, name) => {
    return samples[name] ?? "";
  });
}

function sanitizePreviewHtml(html) {
  const template = document.createElement("template");
  template.innerHTML = String(html || "");
  $$("script", template.content).forEach((node) => node.remove());
  $$("*", template.content).forEach((node) => {
    Array.from(node.attributes).forEach((attribute) => {
      const name = attribute.name.toLowerCase();
      const value = attribute.value.trim().toLowerCase();
      if (name.startsWith("on") || value.startsWith("javascript:")) {
        node.removeAttribute(attribute.name);
      }
    });
  });
  return template.innerHTML;
}

function insertAtCursor(field, value) {
  if (!field || !("value" in field)) return false;
  const start = field.selectionStart ?? field.value.length;
  const end = field.selectionEnd ?? field.value.length;
  field.value = `${field.value.slice(0, start)}${value}${field.value.slice(end)}`;
  const next = start + value.length;
  field.focus();
  if (field.setSelectionRange) field.setSelectionRange(next, next);
  field.dispatchEvent(new Event("input", { bubbles: true }));
  return true;
}

$$("[data-email-template-editor]").forEach((form) => {
  let activeField = null;
  const sampleNode = $("#email-template-samples");
  const footerNode = $("#email-template-footer");
  const samples = sampleNode ? JSON.parse(sampleNode.textContent || "{}") : {};
  const previewFooter = footerNode ? JSON.parse(footerNode.textContent || "{}") : {};
  const subjectField = $('[name="subject"]', form);
  const textField = $('[name="body_text"]', form);
  const htmlField = $('[name="body_html"]', form);
  const templateKey = form.dataset.emailTemplateKey || "";
  const isFooterTemplate = templateKey === "system.transactional_footer";
  const previewDialog = $("[data-email-preview-dialog]");
  const previewBody = $("[data-email-preview-body]");
  const previewMode = $("[data-email-preview-mode]");
  const previewSubject = $("[data-email-preview-subject]");
  const hasPreviewFooter = (value) => (
    (value || "").includes("Este é um email transacional") ||
    (value || "").includes("This transactional email was sent")
  );
  const appendHtmlPreviewFooter = (value) => {
    const htmlFooter = previewFooter.body_html || "";
    if (!value || !htmlFooter || isFooterTemplate || hasPreviewFooter(value)) return value;
    const trimmed = value.trimEnd();
    if (trimmed.endsWith("</div>")) {
      return `${trimmed.slice(0, -6)}${htmlFooter}</div>`;
    }
    return `${trimmed}${htmlFooter}`;
  };
  const appendTextPreviewFooter = (value) => {
    const textFooter = previewFooter.body_text || "";
    if (!value || !textFooter || isFooterTemplate || hasPreviewFooter(value)) return value;
    return `${value.trimEnd()}${textFooter}`;
  };

  [subjectField, textField, htmlField].forEach((field) => {
    field?.addEventListener("focus", () => {
      activeField = field;
    });
  });

  $$("[data-email-var-token]").forEach((button) => {
    button.addEventListener("click", async () => {
      const token = button.dataset.emailVarToken || "";
      const target = activeField || textField || subjectField;
      if (!insertAtCursor(target, token)) {
        try {
          await navigator.clipboard.writeText(token);
        } catch (_error) {
        }
      }
    });
  });

  $("[data-email-preview-open]")?.addEventListener("click", () => {
    const renderedSubject = renderEmailTemplatePreview(subjectField?.value || "", samples);
    const htmlSource = (htmlField?.value || "").trim();
    const textSource = textField?.value || "";
    if (previewSubject) previewSubject.textContent = renderedSubject || "Sem assunto";
    if (previewBody) {
      previewBody.replaceChildren();
      if (htmlSource) {
        const renderedHtml = renderEmailTemplatePreview(htmlSource, samples);
        previewBody.innerHTML = sanitizePreviewHtml(appendHtmlPreviewFooter(renderedHtml));
        if (previewMode) previewMode.textContent = "Renderizando Corpo HTML com valores de exemplo e rodapé transacional.";
      } else {
        const fallback = document.createElement("pre");
        const renderedText = renderEmailTemplatePreview(textSource, samples);
        fallback.textContent = appendTextPreviewFooter(renderedText);
        previewBody.appendChild(fallback);
        if (previewMode) previewMode.textContent = "Corpo HTML vazio; prévia usando Corpo texto com rodapé transacional.";
      }
    }
    if (previewDialog?.showModal) {
      previewDialog.showModal();
    } else {
      previewDialog?.setAttribute("open", "open");
    }
  });

  $("[data-email-preview-close]")?.addEventListener("click", () => {
    previewDialog?.close?.();
    previewDialog?.removeAttribute("open");
  });

  previewDialog?.addEventListener("click", (event) => {
    if (event.target === previewDialog) {
      previewDialog.close?.();
      previewDialog.removeAttribute("open");
    }
  });
});

$$("[data-push-template-editor]").forEach((form) => {
  let activeField = null;
  const sampleNode = $("#push-template-samples");
  const samples = sampleNode ? JSON.parse(sampleNode.textContent || "{}") : {};
  const titleField = $('[name="title"]', form);
  const bodyField = $('[name="body"]', form);
  const previewDialog = $("[data-push-preview-dialog]");
  const previewTitle = $("[data-push-preview-title]");
  const cardTitle = $("[data-push-preview-card-title]");
  const cardBody = $("[data-push-preview-card-body]");

  [titleField, bodyField].forEach((field) => {
    field?.addEventListener("focus", () => {
      activeField = field;
    });
  });

  $$("[data-push-var-token]").forEach((button) => {
    button.addEventListener("click", async () => {
      const token = button.dataset.pushVarToken || "";
      const target = activeField || bodyField || titleField;
      if (!insertAtCursor(target, token)) {
        try {
          await navigator.clipboard.writeText(token);
        } catch (_error) {
        }
      }
    });
  });

  $("[data-push-preview-open]")?.addEventListener("click", () => {
    const renderedTitle = renderEmailTemplatePreview(titleField?.value || "", samples) || "GoTrendLabs";
    const renderedBody = renderEmailTemplatePreview(bodyField?.value || "", samples);
    if (previewTitle) previewTitle.textContent = renderedTitle;
    if (cardTitle) cardTitle.textContent = renderedTitle;
    if (cardBody) cardBody.textContent = renderedBody;
    if (previewDialog?.showModal) {
      previewDialog.showModal();
    } else {
      previewDialog?.setAttribute("open", "open");
    }
  });

  $("[data-push-preview-close]")?.addEventListener("click", () => {
    previewDialog?.close?.();
    previewDialog?.removeAttribute("open");
  });

  previewDialog?.addEventListener("click", (event) => {
    if (event.target === previewDialog) {
      previewDialog.close?.();
      previewDialog.removeAttribute("open");
    }
  });
});

// Feedback for API-backed MCP operations without storing form content.
document.querySelectorAll('.integration-panel form[method="post"], .integration-page form[method="post"]').forEach((form) => {
  form.addEventListener('submit', () => { form.setAttribute('aria-busy', 'true'); });
});

// Keep credential issuance on a GET document: reloading cannot resubmit issuance.
document.querySelectorAll('form[data-once-credential]').forEach((form) => {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const body = new FormData(form);
    body.set('action', 'credentials');
    const button = form.querySelector('button');
    button.disabled = true;
    const output = document.querySelector('[data-credential-result]');
    try {
      const response = await fetch(form.getAttribute('action') || window.location.href, {
        method: 'POST', body, credentials: 'same-origin', cache: 'no-store',
        headers: {'X-Requested-With': 'XMLHttpRequest'}
      });
      if (!response.ok) throw new Error('api_unavailable');
      // This fragment is rendered and escaped by Django, never by the executor.
      output.innerHTML = await response.text();
    } catch (_) {
      output.textContent = document.documentElement.lang.startsWith('en')
        ? 'Unable to issue credential. Check API availability.'
        : 'Não foi possível emitir a credencial. Confira a disponibilidade da API.';
    } finally { button.disabled = false; form.setAttribute('aria-busy', 'false'); }
  });
});

// The admin menu filters destinations only; every page retains server authorization.
(() => {
  const sidebar = document.querySelector('[data-admin-sidebar]');
  if (!sidebar) return;
  const toggle = document.querySelector('[data-admin-menu-toggle]');
  const backdrop = document.querySelector('.admin-navigation-backdrop');
  const content = document.querySelector('#admin-content');
  const search = sidebar.querySelector('[data-admin-navigation-search]');
  const mobile = window.matchMedia('(max-width: 980px)');
  let open = false;
  document.body.classList.add('admin-navigation-ready');
  sidebar.querySelector('[data-admin-search-container]').hidden = false;
  const focusable = () => Array.from(sidebar.querySelectorAll('a,button,input')).filter(el => !el.closest('[hidden]') && el.getClientRects().length);
  function setOpen(value, returnFocus = true) {
    open = mobile.matches && value;
    sidebar.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    sidebar.toggleAttribute('inert', mobile.matches && !open);
    if (mobile.matches && !open) sidebar.setAttribute('aria-hidden', 'true');
    else sidebar.removeAttribute('aria-hidden');
    backdrop.hidden = !open;
    content.toggleAttribute('inert', open);
    document.body.classList.toggle('admin-navigation-open', open);
    if (open) search.focus();
    else if (returnFocus && mobile.matches) toggle.focus();
  }
  toggle.addEventListener('click', () => setOpen(!open));
  document.querySelectorAll('[data-admin-menu-close]').forEach(el => el.addEventListener('click', () => setOpen(false)));
  mobile.addEventListener('change', () => setOpen(false, false));
  document.addEventListener('keydown', event => {
    if (!open) return;
    if (event.key === 'Escape') { event.preventDefault(); setOpen(false); }
    if (event.key === 'Tab') {
      const items = focusable();
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
  });
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  search.addEventListener('input', () => {
    const query = normalize(search.value);
    let visible = 0;
    sidebar.querySelectorAll('[data-admin-navigation-group]').forEach(group => {
      let count = 0;
      group.querySelectorAll('a').forEach(link => {
        link.hidden = !normalize(link.textContent).includes(query);
        if (!link.hidden) { count++; visible++; }
      });
      group.hidden = count === 0;
    });
    sidebar.querySelector('[data-admin-navigation-empty]').hidden = visible !== 0;
  });
  setOpen(false, false);
})();
// One selected source; a late response cannot replace a later manual choice or submission.
function initThumbnailEditor(form) {
  const controls = form.querySelector('[data-thumbnail-controls]');
  const isBadge = form.matches('[data-ai-badge-editor]');
  const fileInput = isBadge ? form.elements.badge_image : form.elements.thumbnail_file;
  const darkInput = isBadge ? form.elements.badge_dark_image : null;
  if (!fileInput) return;
  const aliases = isBadge ? {thumbnail_origin:'badge_image_origin',thumbnail_candidate_id:'badge_image_candidate_id'} : {};
  const field = (name) => form.elements[aliases[name] || name];
  const thumb = document.querySelector('[data-preview-thumb]');
  const initialUrl = field('image_url').value;
  const initialDarkUrl = isBadge ? field('image_dark_url').value : '';
  let selected = {origin: field('thumbnail_origin')?.value || 'current', url: initialUrl, file: null,
    candidate: field('thumbnail_candidate_id')?.value || '', snapshot: null, darkUrl:initialDarkUrl, darkFile:null};
  if (selected.origin === 'generated' && controls && selected.candidate) {
    selected.url = `${controls.dataset.url}${selected.candidate}/preview/`;
    if(isBadge) selected.darkUrl = selected.url + "?theme=dark";
  }
  let previous = null, revision = 0, active = false, submitted = false, waitSubmit = null;
  let pendingSubmit = null, timer = null, alive = true, inFlightId = null, inFlightSnapshot = null;
  let continueSubmit = false;
  const button = controls?.querySelector('[data-thumbnail-generate]');
  const progress = controls?.querySelector('[data-thumbnail-progress]');
  let idleLabel = button?.textContent || '';
  const undo = controls?.querySelector('[data-thumbnail-undo]');
  const status = controls?.querySelector('[data-thumbnail-status]');
  const stale = controls?.querySelector('[data-thumbnail-stale]');
  const decision = controls?.querySelector('[data-thumbnail-submit]');
  const contextNames = isBadge ? ['name','description','rule_description','badge_type','category','subcategory','event'] : ['title','summary','category','subcategory','event'];
  const context = () => Object.fromEntries(contextNames.map(name => [name, field(name).value.trim()]));
  const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
  const say = (text,error=false) => { if(status) {status.textContent=text; status.setAttribute('role',error?'alert':'status');} };
  function render() {
    if (field('thumbnail_origin')) field('thumbnail_origin').value = selected.origin;
    if (field('thumbnail_candidate_id')) field('thumbnail_candidate_id').value = selected.candidate || '';
    // image_url never accepts the protected preview URL; backend derives the public URL by candidate ID.
    field('image_url').value = selected.origin === 'current' ? selected.url : initialUrl;
    if(isBadge) {
      const light = document.querySelector('[data-preview-badge-image-light]');
      const dark = document.querySelector('[data-preview-badge-image-dark]');
      const darkUrl = selected.darkUrl || '';
      if(light) { light.src=selected.url || ''; light.classList.toggle('is-hidden',!selected.url); light.classList.toggle('has-dark',Boolean(darkUrl)); }
      if(dark) { dark.src=darkUrl; dark.classList.toggle('is-hidden',!darkUrl); }
      document.querySelector('[data-preview-badge-icon]')?.classList.toggle('is-hidden',Boolean(selected.url || darkUrl));
      field('image_dark_url').value = initialDarkUrl;
    } else if (thumb) {
      thumb.replaceChildren();
      if (selected.url) { const img=document.createElement('img'); img.src=selected.url; img.alt=''; thumb.append(img); }
      else { const span=document.createElement('span'); span.dataset.previewThumbText=''; span.textContent=field('thumb')?.value || 'MK'; thumb.append(span); }
    }
    if(undo) undo.hidden=!previous;
    if(stale) stale.hidden=!selected.snapshot || same(selected.snapshot,context());
  }
  function choose(next) { previous=selected; selected=next; revision++; render(); }
  fileInput.addEventListener('change', () => {
    const file=fileInput.files?.[0];
    if (!file) return;
    const url=URL.createObjectURL(file);
    choose({origin:'upload',url,file,candidate:'',snapshot:null,darkUrl:selected.origin==='generated'?initialDarkUrl:selected.darkUrl,darkFile:selected.darkFile || null});
    say('');
  });
  darkInput?.addEventListener('change', () => {
    const file=darkInput.files?.[0]; if(!file) return;
    choose({origin:'upload',url:selected.origin==='generated'?initialUrl:selected.url,file:selected.file || null,candidate:'',snapshot:null,darkUrl:URL.createObjectURL(file),darkFile:file}); say('');
  });
  undo?.addEventListener('click', () => {
    if(!previous) return;
    selected=previous; previous=null; revision++;
    const files=new DataTransfer(); if(selected.file) files.items.add(selected.file);
    fileInput.files=files.files;
    if(darkInput) {const darkFiles=new DataTransfer(); if(selected.darkFile) darkFiles.items.add(selected.darkFile); darkInput.files=darkFiles.files;}
    render(); say('');
  });
  form.addEventListener('input', () => { if(stale) stale.hidden=!selected.snapshot || same(selected.snapshot,context()); });
  form.addEventListener('change', () => { if(stale) stale.hidden=!selected.snapshot || same(selected.snapshot,context()); });
  if(!controls) { render(); return; }
  async function fetchJob(url,options={}) {
    const response=await fetch(url,{credentials:'same-origin',...options});
    if(!response.ok) { let message=controls.dataset.failed; try { message=(await response.json()).message || message; } catch {} const error=new Error(message); error.status=response.status; throw error; }
    return response.json();
  }
  function busy(value) {
    active=value; button.disabled=value; controls.dataset.busy=String(value);
    button.setAttribute('aria-busy',String(value));
    button.textContent=value ? controls.dataset.loadingShort : idleLabel;
    if(progress) progress.hidden=!value;
    if(value) say('');
  }
  function finishManualSelection() {
    const cancelled=Boolean(waitSubmit || pendingSubmit);
    waitSubmit=null; pendingSubmit=null;
    if(decision) decision.hidden=true;
    busy(false);
    say(controls.dataset.manual + (cancelled ? ' ' + controls.dataset.waitCancelled : ''));
  }
  async function accept(job,selectionRevision,allowSelection=true) {
    if(!alive || submitted) return;
    if(['queued','running'].includes(job.state)) {
      busy(true); inFlightId=job.request_id; inFlightSnapshot=job.snapshot;
      timer=setTimeout(() => poll(job.request_id,selectionRevision),1500); return;
    }
    inFlightId=null; inFlightSnapshot=null;
    if(job.state==='succeeded') {
      idleLabel=controls.dataset.again;
      if(allowSelection && revision===selectionRevision) {
        // Load first, preserving the old image if the protected file/session is unavailable.
        const urls = isBadge ? [job.preview_url, job.preview_dark_url] : [job.preview_url];
        if(urls.some(url => !url)) throw new Error(controls.dataset.failed);
        await Promise.all(urls.map(url => {const image=new Image(); image.src=url; return image.decode();}));
        if(!alive || submitted) { waitSubmit=null; pendingSubmit=null; busy(false); return; }
        if(revision!==selectionRevision) { finishManualSelection(); return; }
        busy(false);
        choose({origin:'generated',url:job.preview_url,candidate:job.candidate_id,file:null,snapshot:job.snapshot,darkUrl:isBadge?job.preview_dark_url:'',darkFile:null});
        // Keep previous File in undo memory, but exclude it from form submission now.
        fileInput.value=''; if(darkInput) darkInput.value='';
        say(controls.dataset.ready);
      } else if(allowSelection) { finishManualSelection(); return; }
      else { busy(false); say(''); }
      if(waitSubmit) { const submitter=waitSubmit; waitSubmit=null; submitter.form.requestSubmit(submitter.button); }
    } else { busy(false); say(job.message || controls.dataset.failed,true); waitSubmit=null; }
    if(decision) decision.hidden=true;
  }
  async function poll(id,selectionRevision) {
    try { await accept(await fetchJob(`${controls.dataset.url}${id}/`),selectionRevision); }
    catch(error) { busy(false); say(error.message,true); waitSubmit=null; }
  }
  button.addEventListener('click', async () => {
    if(active) return;
    const snapshot=context();
    if((isBadge ? ['name','description'] : ['title','summary','category','subcategory']).some(key => !snapshot[key])) { say(controls.dataset.required,true); return; }
    const selectionRevision=revision;
    // Retrying an adapter timeout reuses identity and original snapshot, avoiding duplicate paid calls.
    const id=inFlightId || crypto.randomUUID();
    inFlightSnapshot=inFlightId ? inFlightSnapshot : snapshot; inFlightId=id;
    busy(true);
    try { const job=await fetchJob(controls.dataset.url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':field('csrfmiddlewaretoken').value},
      body:JSON.stringify({...inFlightSnapshot,request_id:id,...(isBadge ? {badge_code:form.dataset.badgeCode || ''} : {})})}); await accept(job,selectionRevision); }
    catch(error) { busy(false); if(error.status && error.status<500) {inFlightId=null; inFlightSnapshot=null;} say(error.message,true); }
  });
  function onSubmit(event) {
    if(event.submitter?.value==='publish-reviewed' && selected.origin!=='current') {
      event.preventDefault(); say(controls.dataset.review,true); status.focus(); return;
    }
    if(active && !submitted && !continueSubmit) {
      event.preventDefault(); pendingSubmit={form:event.target,button:event.submitter}; decision.hidden=false; decision.focus(); return;
    }
    submitted=true; clearTimeout(timer);
    if(selected.origin!=='upload') {fileInput.value=''; if(darkInput) darkInput.value='';}
  }
  form.addEventListener('submit',onSubmit);
  document.querySelectorAll('[data-editorial-publish]').forEach(publishForm => publishForm.addEventListener('submit',onSubmit));
  controls.querySelector('[data-thumbnail-continue]').addEventListener('click', () => {
    const submitter=pendingSubmit;
    if(!submitter) return;
    if(!submitter.form.noValidate && !submitter.button?.formNoValidate && !submitter.form.reportValidity()) return;
    continueSubmit=true;
    try { submitter.form.requestSubmit(submitter.button); }
    finally { continueSubmit=false; }
    if(submitted) { pendingSubmit=null; decision.hidden=true; }
  });
  controls.querySelector('[data-thumbnail-wait]').addEventListener('click', () => {
    waitSubmit=pendingSubmit; pendingSubmit=null; decision.hidden=true; button.focus();
  });
  window.addEventListener('pagehide', () => {alive=false; clearTimeout(timer);});
  render();
  // Recover an active request after navigation. A completed historical job isn't auto-selected.
  fetchJob(controls.dataset.url).then(job => {if(job && !active) accept(job,revision,['queued','running'].includes(job.state));}).catch(() => {});
}
$$('[data-market-form], [data-ai-badge-editor]').forEach(initThumbnailEditor);
