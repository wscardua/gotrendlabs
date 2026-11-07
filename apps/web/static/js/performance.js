(() => {
  const controls = document.querySelector('[data-performance-more]');
  if (!controls) return;
  const rows = [...document.querySelectorAll('#performance-history-rows > tr')];
  const button = controls.querySelector('[data-performance-more-button]');
  const count = controls.querySelector('[data-performance-count]');
  const step = 5;
  let visible = Math.min(step, rows.length);
  const update = () => {
    rows.forEach((row, index) => { row.hidden = index >= visible; });
    count.textContent = count.dataset.message
      .replace('{visible}', String(visible)).replace('{total}', String(rows.length));
    button.hidden = visible >= rows.length;
  };
  button.addEventListener('click', () => {
    const firstNewRow = rows[visible];
    visible = Math.min(visible + step, rows.length);
    update();
    firstNewRow?.querySelector('a')?.focus();
  });
  update();
  controls.hidden = false;
})();
