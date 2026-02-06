"""
Télécharge les quartiers administratifs de Paris (80 quartiers) en GeoJSON.

Source: Open Data Paris – dataset `quartier_paris`
Page dataset: https://opendata.paris.fr/explore/dataset/quartier_paris/

Le fichier est sauvegardé dans `data/source_data/`:
- `quartiers_administratifs.geojson`
- `quartiers_administratifs.pkl` (GeoDataFrame picklé, pratique pour chargements rapides)

Usage (dans l'env conda):
    conda activate paris_risques
    python scripts/download_quartiers_administratifs.py
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd


def main() -> None:
    project_root = Path(__file__).parent.parent
    out_dir = project_root / "data" / "source_data"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Endpoint d'export OpenDataSoft (Open Data Paris) en GeoJSON
    # NB: si l'endpoint change, vous pouvez repartir de la page dataset ci-dessus.
    geojson_url = (
        "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
        "quartier_paris/exports/geojson"
    )

    out_geojson = out_dir / "quartiers_administratifs.geojson"
    out_pkl = out_dir / "quartiers_administratifs.pkl"

    print(f"📥 Téléchargement quartiers administratifs depuis:\n  {geojson_url}\n")
    gdf = gpd.read_file(geojson_url)

    # Normalisation légère des noms de colonnes attendues (sans hypothèse forte)
    # On garde tout tel quel, mais on garantit la présence d'une colonne 'geometry'.
    assert "geometry" in gdf.columns

    print(f"✅ Chargé: {len(gdf)} quartiers / colonnes={len(gdf.columns)}")

    # Sauvegarde GeoJSON + pickle
    gdf.to_file(out_geojson, driver="GeoJSON")
    gdf.to_pickle(out_pkl)

    print(f"\n💾 Sauvegardé:\n  - {out_geojson}\n  - {out_pkl}")


if __name__ == "__main__":
    main()

