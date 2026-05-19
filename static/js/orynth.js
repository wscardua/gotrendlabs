const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

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
    if (output) output.textContent = `${range.value} OC`;
    const returnBox = $(`[data-return-output="${range.dataset.amount}"]`);
    if (returnBox) returnBox.textContent = `${Math.round(Number(range.value) * 1.62)} OC`;
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
