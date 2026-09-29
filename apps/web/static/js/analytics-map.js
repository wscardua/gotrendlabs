/* Static IBGE SVG remains visible without JavaScript; this adds counts and filters. */
(() => {
  const host = document.getElementById('analytics-state-map');
  const data = document.getElementById('analytics-region-data');
  if (!host || !data) return;

  const names = {
    AC: 'Acre', AL: 'Alagoas', AP: 'Amapá', AM: 'Amazonas', BA: 'Bahia',
    CE: 'Ceará', DF: 'Distrito Federal', ES: 'Espírito Santo', GO: 'Goiás',
    MA: 'Maranhão', MT: 'Mato Grosso', MS: 'Mato Grosso do Sul', MG: 'Minas Gerais',
    PA: 'Pará', PB: 'Paraíba', PR: 'Paraná', PE: 'Pernambuco', PI: 'Piauí',
    RJ: 'Rio de Janeiro', RN: 'Rio Grande do Norte', RS: 'Rio Grande do Sul',
    RO: 'Rondônia', RR: 'Roraima', SC: 'Santa Catarina', SP: 'São Paulo',
    SE: 'Sergipe', TO: 'Tocantins',
  };
  const rows = JSON.parse(data.textContent);
  const counts = new Map(rows.map(row => [row.region_code, Number(row.sessions) || 0]));
  const peak = Math.max(0, ...counts.values());
  const selected = new URLSearchParams(location.search).get('region');
  const name = document.querySelector('[data-map-name]');
  const count = document.querySelector('[data-map-count]');
  const show = uf => {
    if (!name || !count) return;
    name.textContent = names[uf] || uf;
    const sessions = counts.get(uf) || 0;
    count.textContent = `${sessions} ${sessions === 1 ? 'sessão' : 'sessões'} neste recorte`;
  };

  for (const link of host.querySelectorAll('a[data-uf]')) {
    const uf = link.dataset.uf;
    const sessions = counts.get(uf) || 0;
    const ratio = peak ? sessions / peak : 0;
    const level = ratio === 0 ? 0 : ratio < 0.25 ? 1 : ratio < 0.5 ? 2 : ratio < 0.75 ? 3 : 4;
    const params = new URLSearchParams(location.search);
    params.set('region', uf);
    params.delete('city');
    link.setAttribute('href', `?${params.toString()}`);
    link.setAttribute('data-level', String(level));
    link.setAttribute('aria-label', `${names[uf]}: ${sessions} ${sessions === 1 ? 'sessão' : 'sessões'}`);
    if (selected === uf) link.setAttribute('aria-current', 'true');
    link.addEventListener('mouseenter', () => show(uf));
    link.addEventListener('focus', () => show(uf));
  }
  if (selected && names[selected]) show(selected);
})();
