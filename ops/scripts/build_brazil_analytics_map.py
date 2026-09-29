"""Build a local SVG of the 27 UFs from the official IBGE malhas API.

Run only when refreshing the static map. No browser/runtime request to IBGE is made.
Source: https://servicodados.ibge.gov.br/api/docs/malhas?versao=3
"""

import json
import gzip
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


OUTPUT = Path("apps/web/django/admin_ops/templates/admin_ops/partials/brazil_states_map.svg")
STATES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}


def geometry(uf):
    query = quote("application/vnd.geo+json", safe="")
    url = f"https://servicodados.ibge.gov.br/api/v3/malhas/estados/{uf}?qualidade=minima&formato={query}"
    for attempt in range(4):
        try:
            with urlopen(url, timeout=30) as response:
                body = response.read()
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(attempt + 1)
    if body.startswith(b"\x1f\x8b"):
        body = gzip.decompress(body)
    payload = json.loads(body)
    features = payload["features"]
    if len(features) != 1:
        raise ValueError(f"Malha inesperada: {uf}")
    shape = features[0]["geometry"]
    if shape["type"] == "Polygon":
        return [shape["coordinates"]]
    if shape["type"] == "MultiPolygon":
        return shape["coordinates"]
    raise ValueError(f"Geometria inesperada: {uf}")


def main():
    with ThreadPoolExecutor(max_workers=2) as pool:
        shapes = dict(zip(STATES, pool.map(geometry, STATES)))
    points = [point for polygons in shapes.values() for polygon in polygons
              for ring in polygon for point in ring]
    min_lon = min(point[0] for point in points)
    max_lon = max(point[0] for point in points)
    min_lat = min(point[1] for point in points)
    max_lat = max(point[1] for point in points)
    scale = 15
    padding = 12
    width = round((max_lon - min_lon) * scale + 2 * padding)
    height = round((max_lat - min_lat) * scale + 2 * padding)

    def xy(point):
        return f"{(point[0] - min_lon) * scale + padding:.1f},{(max_lat - point[1]) * scale + padding:.1f}"

    lines = [
        "<!-- Geometria simplificada: IBGE API de Malhas v3, qualidade mínima. "
        "https://servicodados.ibge.gov.br/api/docs/malhas?versao=3 -->",
        f'<svg class="analytics-brazil-map" viewBox="0 0 {width} {height}" '
        'xmlns="http://www.w3.org/2000/svg" role="group" '
        'aria-label="Mapa interativo dos estados do Brasil">',
    ]
    for uf, polygons in sorted(shapes.items()):
        rings = []
        for polygon in polygons:
            for ring in polygon:
                if len(ring) < 3:
                    continue
                rings.append("M" + "L".join(xy(point) for point in ring) + "Z")
        if not rings:
            raise ValueError(f"Estado sem contorno: {uf}")
        lines.append(f'  <a href="?region={uf}" data-uf="{uf}" aria-label="{STATES[uf]}" '
                     f'data-level="0"><path d="{"".join(rings)}" fill-rule="evenodd"/>'
                     f'<title>{STATES[uf]}</title></a>')
    lines.append("</svg>")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{OUTPUT}: {len(shapes)} UFs, viewBox {width}×{height}")


if __name__ == "__main__":
    main()
