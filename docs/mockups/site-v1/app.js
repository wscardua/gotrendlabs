const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

const currentPage = location.pathname.split("/").pop() || "index.html";
const isAdmin = currentPage.startsWith("admin-");
const storedTheme = localStorage.getItem("gotrendlabs-theme");
const initialTheme = currentPage === "dark-mode.html" ? "dark" : (storedTheme || document.body.dataset.theme || "light");
document.body.dataset.theme = initialTheme;

function publicHeader() {
  return `
    <header class="topbar">
      <nav class="shell nav">
        <a class="brand" href="index.html"><span class="brand-mark">O</span><span>GoTrendLabs</span></a>
        <div class="nav-links">
          <a class="nav-link ${currentPage === "index.html" ? "active" : ""}" href="index.html">Mercados</a>
          <a class="nav-link ${currentPage === "rankings.html" ? "active" : ""}" href="rankings.html">Ranking</a>
        </div>
        <div class="nav-actions">
          <button class="theme-toggle" type="button" data-theme-toggle aria-label="Alternar dark mode">◐</button>
          <span class="language">PT-BR</span>
          <div class="user-chip">
            <button class="user-button" type="button"><span class="avatar">WL</span><span class="chip-meta"><strong>Will Costa</strong><span>2.480 GTL · Rep 82</span></span></button>
            <div class="user-menu">
              <a href="profile.html">Perfil e badges</a>
              <a href="wallet.html">Carteira e extrato</a>
              <a href="suggestion.html">Sugerir mercado</a>
              <a href="feedback.html">Enviar feedback</a>
              <a href="login.html">Sair desta sessão</a>
            </div>
          </div>
        </div>
      </nav>
    </header>`;
}

function adminHeader() {
  return `
    <header class="topbar">
      <nav class="shell nav">
        <a class="brand" href="admin-dashboard.html"><span class="brand-mark">A</span><span>GoTrendLabs Admin</span></a>
        <div class="nav-links"></div>
        <div class="nav-actions"><button class="theme-toggle" type="button" data-theme-toggle aria-label="Alternar dark mode">◐</button><a class="btn ghost" href="index.html">Ver site público</a></div>
      </nav>
    </header>`;
}

function footer() {
  const adminLink = isAdmin ? '<a href="index.html">Site público</a>' : '<a href="admin-dashboard.html">Admin</a>';
  return `
    <footer class="footer">
      <div class="shell footer-grid">
        <div><strong>GoTrendLabs</strong><p>Rede social de previsões com moeda educativa, reputação e resolução auditável.</p></div>
        <div><strong>Produto</strong><a href="index.html">Mercados</a><a href="rankings.html">Ranking</a><a href="suggestion.html">Sugerir mercado</a></div>
        <div><strong>Confiança</strong><a href="concepts.html">Conceitos</a><a href="security.html">Segurança</a><a href="feedback.html">Feedback</a></div>
        <div><strong>Comunidade</strong><a href="rankings.html">Ranking</a><a href="share-result.html">Compartilhar resultado</a><a href="suggestion.html">Sugerir mercado</a></div>
        <div><strong>Conta</strong><a href="profile.html">Perfil público</a><a href="wallet.html">Carteira</a><a href="login.html">Login</a></div>
      </div>
    </footer>`;
}

if (!$(".topbar")) {
  document.body.insertAdjacentHTML("afterbegin", isAdmin ? adminHeader() : publicHeader());
}

if (!$(".footer")) {
  document.body.insertAdjacentHTML("beforeend", footer());
}

if (!isAdmin) {

  // Public navigation is normalized here so static HTML cannot leak stale/internal links.
  $$('.topbar .nav-links a[href="categories.html"], .topbar .nav-links a[href="wallet.html"]').forEach((link) => link.remove());
  $$('.footer a[href="categories.html"], .footer a[href="admin-dashboard.html"], .footer a[href="admin-moderation.html"], .footer a[href="dark-mode.html"]').forEach((link) => link.remove());

  const menu = $(".user-menu");
  if (menu) {
    menu.innerHTML = `
      <a href="profile.html">Perfil e badges</a>
      <a href="wallet.html">Carteira e extrato</a>
      <a href="suggestion.html">Sugerir mercado</a>
      <a href="feedback.html">Enviar feedback</a>
      <a href="login.html">Sair desta sessão</a>`;
  }
}

if (!isAdmin && currentPage !== "index.html" && !$("a.inline-back")) {
  const firstPanel = $("main .panel");
  if (firstPanel) {
    firstPanel.insertAdjacentHTML("afterbegin", '<div class="section-kicker"><a class="inline-back" href="index.html">← Voltar ao feed</a></div>');
  }
}

if (!$("[data-theme-toggle]")) {
  const actions = $(".nav-actions");
  if (actions) actions.insertAdjacentHTML("afterbegin", '<button class="theme-toggle" type="button" data-theme-toggle aria-label="Alternar dark mode">◐</button>');
}

if (isAdmin) {
  $$(".admin-menu").forEach((menu) => {
    menu.innerHTML = `
      <a href="admin-dashboard.html">Visão geral</a>
      <a href="admin-markets.html">Mercados</a>
      <a href="admin-moderation.html">Filas operacionais</a>
      <a href="admin-taxonomy.html">Categorias</a>`;
    const activeHref =
      currentPage === "admin-dashboard.html" ? "admin-dashboard.html" :
      currentPage.includes("market") || currentPage.includes("resolution") ? "admin-markets.html" :
      currentPage === "admin-moderation.html" ? "admin-moderation.html" :
      currentPage === "admin-taxonomy.html" ? "admin-taxonomy.html" : "";
    const active = menu.querySelector(`[href="${activeHref}"]`);
    if (active) active.classList.add("active");
  });
  $$('.topbar .nav-links a:not(:first-child)').forEach((link) => link.remove());
}

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

$$("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const group = button.closest("[data-filter-group]");
    $$("[data-filter]", group).forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
  });
});

$$("[data-choice]").forEach((choice) => {
  choice.addEventListener("click", () => {
    const group = choice.closest(".option-grid");
    $$(".choice", group).forEach((item) => item.classList.remove("active"));
    choice.classList.add("active");
    const target = $("[data-selected-choice]");
    if (target) target.textContent = choice.dataset.choice;
  });
});

$$("[data-amount]").forEach((range) => {
  const output = $(`[data-amount-output="${range.dataset.amount}"]`);
  const update = () => {
    if (output) output.textContent = `${range.value} GTL`;
    const returnBox = $(`[data-return-output="${range.dataset.amount}"]`);
    if (returnBox) returnBox.textContent = `${Math.round(Number(range.value) * 1.62)} GTL`;
  };
  range.addEventListener("input", update);
  update();
});

$$("[data-confirm]").forEach((trigger) => {
  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    const modal = $("#confirm-modal");
    if (!modal) return;
    $("[data-confirm-title]", modal).textContent = trigger.dataset.confirm;
    $("[data-confirm-desc]", modal).textContent = trigger.dataset.confirmDesc || "Esta ação fica registrada na trilha de auditoria.";
    modal.classList.add("show");
  });
});

$$("[data-close-modal]").forEach((button) => {
  button.addEventListener("click", () => {
    const modal = button.closest(".modal");
    if (modal) modal.classList.remove("show");
  });
});
