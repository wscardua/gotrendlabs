const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

const storedTheme = localStorage.getItem("orynth-theme");
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
    localStorage.setItem("orynth-theme", document.body.dataset.theme);
    syncThemeButtons();
  });
});

syncThemeButtons();

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

$$("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const group = button.closest("[data-filter-group]");
    $$("[data-filter]", group).forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
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
}

$$("[data-ranking-filters]").forEach((form) => {
  $("[data-ranking-category]", form)?.addEventListener("change", () => syncRankingSubcategories(form));
  syncRankingSubcategories(form);
});

$$("[data-taxonomy-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const mode = button.dataset.taxonomyFilter;
    let visibleCount = 0;
    $$("[data-taxonomy-category]").forEach((row) => {
      const markets = Number(row.dataset.marketsCount || 0);
      const subcategories = Number(row.dataset.subcategoriesCount || 0);
      const blocked = row.dataset.blocked === "true";
      const subRow = row.nextElementSibling?.matches("[data-taxonomy-subcategory-row]") ? row.nextElementSibling : null;
      const visible =
        mode === "all" ||
        (mode === "with-markets" && markets > 0) ||
        (mode === "without-markets" && markets === 0) ||
        (mode === "without-subcategories" && subcategories === 0) ||
        (mode === "blocked" && blocked);
      row.hidden = !visible;
      if (subRow) subRow.hidden = !visible;
      if (visible) visibleCount += 1;
    });
    const empty = $("[data-taxonomy-empty]");
    if (empty) empty.hidden = visibleCount !== 0;
  });
});

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
    if (output) output.textContent = `${range.value} O₵`;
    const lockedBox = $(`[data-locked-output="${range.dataset.amount}"]`);
    if (lockedBox) lockedBox.textContent = `${range.value} O₵`;
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

$$("[data-amount]").forEach((range) => {
  range.addEventListener("input", updatePredictionPreview);
  updatePredictionPreview();
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
      title: button.dataset.shareTitle || "Orynth Trends",
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
  const summary = fieldValue(form, "summary", "Resumo do mercado aparece aqui conforme você preenche.");

  const thumbBox = $("[data-preview-thumb]", preview);
  const thumbText = $("[data-preview-thumb-text]", preview);
  if (thumbBox) thumbBox.style.setProperty("--thumb", color);
  if (thumbText) thumbText.textContent = thumb;
  $("[data-preview-title]", preview).textContent = title;
  $("[data-preview-category]", preview).textContent = category;
  $("[data-preview-subcategory]", preview).textContent = subcategory;
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
  const lightUrl = fieldValue(form, "image_url", "");
  const darkUrl = fieldValue(form, "image_dark_url", "");
  const lightImage = $("[data-preview-badge-image-light]", preview);
  const darkImage = $("[data-preview-badge-image-dark]", preview);
  const icon = $("[data-preview-badge-icon]", preview);

  $("[data-preview-badge-name]", preview).textContent = name;
  $("[data-preview-badge-description]", preview).textContent = description;
  $("[data-preview-badge-rule]", preview).textContent = rule;
  $("[data-preview-badge-status]", preview).textContent = isActive ? "Ativa para concessão" : "Inativa";
  preview.classList.toggle("locked", !isActive);

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
  if (!selectedStillVisible) {
    subcategorySelect.value = "";
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
    if (event.target.matches('input[type="file"][name="thumbnail_file"]')) {
      const file = event.target.files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.addEventListener("load", () => {
          const thumbBox = $("[data-preview-thumb]");
          if (!thumbBox) return;
          thumbBox.innerHTML = `<img src="${reader.result}" alt="">`;
        });
        reader.readAsDataURL(file);
      }
    }
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
});

$$("[data-badge-form]").forEach((form) => {
  form.addEventListener("input", () => updateBadgePreview(form));
  form.addEventListener("change", (event) => {
    if (event.target.matches('input[type="file"][name="badge_image"], input[type="file"][name="badge_dark_image"]')) {
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
    updateBadgePreview(form);
  });
  updateBadgePreview(form);
});
