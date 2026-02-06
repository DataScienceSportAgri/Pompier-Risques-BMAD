"""
Script de diagnostic des microzones (data/source_data/microzones.pkl).

Affiche : nombre, liste des IDs, couverture (bounds), géométries invalides.
Utile pour vérifier que tout Paris est bien découpé en microzones.
"""

import pickle
import sys
from pathlib import Path

# Racine du projet
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import geopandas as gpd
except ImportError:
    print("❌ geopandas requis : pip install geopandas")
    sys.exit(1)


def main():
    data_dir = ROOT / "data" / "source_data"
    microzones_file = data_dir / "microzones.pkl"

    if not microzones_file.exists():
        print(f"❌ Fichier introuvable : {microzones_file}")
        print("   Exécutez le pré-calcul : python scripts/run_precompute.py --only-distances")
        sys.exit(1)

    print("=" * 60)
    print("DIAGNOSTIC MICROZONES")
    print("=" * 60)
    print(f"Fichier : {microzones_file}\n")

    with open(microzones_file, "rb") as f:
        data = pickle.load(f)

    if isinstance(data, dict) and "data" in data:
        gdf = data["data"]
    else:
        gdf = data

    if not isinstance(gdf, gpd.GeoDataFrame):
        print(f"❌ Type inattendu : {type(gdf)}")
        sys.exit(1)

    n = len(gdf)
    print(f"Nombre de microzones : {n}")
    if n < 100:
        print(f"   ⚠️  Attendu ~100 (Epic 1). Pour régénérer : python scripts/run_precompute.py --only-distances")
    print()

    # Colonnes
    print("Colonnes :", list(gdf.columns))
    print()

    # IDs
    if "microzone_id" in gdf.columns:
        ids = gdf["microzone_id"].tolist()
        print(f"IDs (microzone_id) : {len(ids)} valeurs")
        print("   Premiers :", ids[:5])
        print("   Derniers :", ids[-5:])
        if len(set(ids)) != len(ids):
            print("   ⚠️  Doublons détectés dans microzone_id")
    else:
        print("   Pas de colonne 'microzone_id'")
    print()

    # Bounds (couverture Paris)
    try:
        bounds = gdf.total_bounds  # minx, miny, maxx, maxy
        print("Couverture (bounds) :")
        print(f"   minx={bounds[0]:.6f}, miny={bounds[1]:.6f}, maxx={bounds[2]:.6f}, maxy={bounds[3]:.6f}")
        # Paris approximatif : lon ~2.2-2.4, lat ~48.81-48.90
        if bounds[0] > 2.5 or bounds[2] < 2.2 or bounds[1] > 48.95 or bounds[3] < 48.80:
            print("   ⚠️  Les bounds ne couvrent pas entièrement Paris (lon ~2.2-2.4, lat ~48.81-48.90)")
    except Exception as e:
        print(f"   Erreur bounds : {e}")
    print()

    # Géométries invalides
    if hasattr(gdf.geometry, "is_valid"):
        invalid = ~gdf.geometry.is_valid
        n_invalid = invalid.sum()
        if n_invalid > 0:
            print(f"⚠️  Géométries invalides : {n_invalid}/{n}")
            idx_invalid = gdf.index[invalid].tolist()[:10]
            print("   Indices (10 premiers) :", idx_invalid)
            print("   Correction possible : make_valid() ou buffer(0) avant affichage.")
        else:
            print("Géométries : toutes valides.")
    else:
        print("Géométries : is_valid non disponible (vérifier shapely/geopandas).")
    print()

    # Arrondissements
    if "arrondissement" in gdf.columns:
        arr_unique = sorted(gdf["arrondissement"].dropna().unique())
        print(f"Arrondissements couverts : {len(arr_unique)} — {arr_unique[:5]} ... {arr_unique[-3:]}")
        if len(arr_unique) < 20:
            print("   ⚠️  Paris a 20 arrondissements (1-20). Certains peuvent être absents.")
    print()

    print("=" * 60)
    print("Pour régénérer les 100 microzones (découpage Paris) :")
    print("  python scripts/run_precompute.py --only-distances")
    print("=" * 60)


if __name__ == "__main__":
    main()
