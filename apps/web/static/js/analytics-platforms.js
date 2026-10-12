(() => {
  'use strict';
  const chart = document.querySelector('[data-platform-chart]');
  if (!chart) return;
  const platforms = JSON.parse(document.getElementById('analytics-platform-totals').textContent);
  const daily = JSON.parse(document.getElementById('analytics-platform-daily').textContent);
  if (!daily.length) return;
  const svg = chart.querySelector('svg');
  const control = chart.querySelector('input[type="range"]');
  const output = chart.querySelector('output');
  const locale = document.documentElement.lang || 'pt-BR';
  const dateFormat = new Intl.DateTimeFormat(locale, {day: '2-digit', month: '2-digit', timeZone: 'UTC'});
  const fullDateFormat = new Intl.DateTimeFormat(locale, {dateStyle: 'short', timeZone: 'UTC'});
  const numbers = new Intl.NumberFormat(locale);
  const labels = Object.fromEntries([...document.querySelectorAll('[data-series-label]')]
    .map(label => [label.dataset.seriesLabel, label.textContent.trim()]));
  const dayDate = day => new Date(`${day}T00:00:00Z`);
  const ns = 'http://www.w3.org/2000/svg';
  const max = Math.max(1, ...daily.flatMap(day => platforms.map(row => day[`${row.platform}_sessions`])));
  let selected = 0;
  let width;
  const x = index => 42 + index * (width - 58) / Math.max(1, daily.length - 1);
  const y = value => 174 - value * 150 / max;
  const add = (tag, attributes, text) => {
    const element = document.createElementNS(ns, tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    element.setAttribute('data-chart-mark', '');
    svg.appendChild(element);
    return element;
  };
  const selectionLine = document.createElementNS(ns, 'line');
  selectionLine.setAttribute('class', 'chart-selection');
  const markers = platforms.map(row => {
    const marker = document.createElementNS(ns, 'circle');
    marker.setAttribute('class', `chart-series is-${row.platform}`);
    marker.setAttribute('r', row.platform === 'web' ? 5 : 3);
    return marker;
  });
  const select = index => {
    selected = Math.max(0, Math.min(daily.length - 1, index));
    control.value = selected;
    const day = daily[selected];
    const values = platforms.map(row => `${labels[row.platform]}: ${numbers.format(day[`${row.platform}_sessions`])}`);
    const text = `${fullDateFormat.format(dayDate(day.day))} UTC · ${values.join(' · ')}`;
    if (output.textContent !== text) output.textContent = text;
    control.setAttribute('aria-valuetext', text);
    selectionLine.setAttribute('x1', x(selected));
    selectionLine.setAttribute('x2', x(selected));
    selectionLine.setAttribute('y1', 20);
    selectionLine.setAttribute('y2', 174);
    markers.forEach((marker, index) => {
      marker.setAttribute('cx', x(selected));
      marker.setAttribute('cy', y(day[`${platforms[index].platform}_sessions`]));
    });
  };
  const render = () => {
    svg.querySelectorAll('[data-chart-mark]').forEach(element => element.remove());
    width = Math.max(280, chart.clientWidth);
    svg.setAttribute('viewBox', `0 0 ${width} 220`);
    const ticks = [...new Set([0, Math.round(max / 2), max])];
    ticks.forEach(value => {
      add('line', {x1: 42, x2: width - 16, y1: y(value), y2: y(value), class: 'chart-grid'});
      add('text', {x: 34, y: y(value) + 4, 'text-anchor': 'end'}, numbers.format(value));
    });
    platforms.forEach(row => {
      const points = daily.map((day, index) => `${x(index)},${y(day[`${row.platform}_sessions`])}`).join(' ');
      add('polyline', {points, class: `chart-series is-${row.platform}`});
      [0, daily.length - 1].forEach(index => {
        add('circle', {cx: x(index), cy: y(daily[index][`${row.platform}_sessions`]),
          r: row.platform === 'web' ? 4 : 2, class: `chart-series is-${row.platform}`});
      });
    });
    const tickCount = Math.min(daily.length, Math.max(2, Math.floor((width - 58) / 80)), 8);
    const dates = [...new Set(Array.from({length: tickCount}, (_, index) =>
      Math.round(index * (daily.length - 1) / Math.max(1, tickCount - 1))))];
    dates.forEach(index => {
      add('text', {x: x(index), y: 201,
        'text-anchor': index === 0 ? 'start' : index === daily.length - 1 ? 'end' : 'middle'},
      dateFormat.format(dayDate(daily[index].day)));
    });
    svg.appendChild(selectionLine);
    markers.forEach(marker => svg.appendChild(marker));
    select(selected);
  };
  control.max = daily.length - 1;
  control.disabled = daily.length === 1;
  control.addEventListener('input', () => select(Number(control.value)));
  const selectPointer = event => {
    const bounds = svg.getBoundingClientRect();
    const chartX = (event.clientX - bounds.left) * width / bounds.width;
    select(Math.round((chartX - 42) * (daily.length - 1) / (width - 58)));
  };
  svg.addEventListener('pointermove', event => {
    if (event.pointerType === 'mouse' || event.buttons) selectPointer(event);
  });
  svg.addEventListener('pointerdown', selectPointer);
  chart.hidden = false;
  render();
  window.addEventListener('resize', render);
  document.querySelector('.analytics-platform-daily').open = false;
})();
