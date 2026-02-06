"""
Tests pour le module precompute_matrices_correlation.py (Story 1.4.4.1).

- Structure des matrices (dimensions, types)
- Valeurs cohérentes (probabilités 0–1, sommes = 1 intra-type, pas de NaN)
- Chargement depuis pickle (IV1)
"""

from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
SOURCE_DATA = ROOT / "data" / "source_data"


def _scripts_path():
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))


def _microzones_gdf(n=12):
    """GeoDataFrame minimal pour les tests (≥9 pour voisin 8)."""
    pytest.importorskip("geopandas")
    import geopandas as gpd
    from shapely.geometry import Polygon
    rows = []
    for i in range(n):
        x, y = 2.35 + i * 0.001, 48.85 + (i % 3) * 0.001
        rows.append({
            "microzone_id": f"MZ{i+1:03d}",
            "arrondissement": (i % 20) + 1,
            "geometry": Polygon([(x, y), (x + 0.01, y), (x + 0.01, y + 0.01), (x, y + 0.01)]),
        })
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


@pytest.fixture(scope="module")
def calculator():
    _scripts_path()
    import yaml
    from precompute_matrices_correlation import MatricesCorrelationCalculator
    cfg = {}
    with open(ROOT / "config" / "config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return MatricesCorrelationCalculator(cfg or {})


@pytest.fixture
def microzones():
    return _microzones_gdf()


class TestMatricesStructure:
    """Validation structure des matrices (Story 1.4.4.1 AC)."""

    def test_intra_type_structure(self, calculator, microzones):
        m = calculator.calculate_matrices_intra_type(microzones)
        assert len(m) == len(microzones)
        for mz_id, by_type in m.items():
            assert by_type.keys() == {"agressions", "incendies", "accidents"}
            for t, mat in by_type.items():
                assert mat.shape == (3, 3)
                assert not np.isnan(mat).any()

    def test_intra_type_sommes_lignes(self, calculator, microzones):
        m = calculator.calculate_matrices_intra_type(microzones)
        for by_type in m.values():
            for mat in by_type.values():
                for i in range(3):
                    assert abs(mat[i, :].sum() - 1.0) < 1e-5

    def test_intra_type_valeurs_0_1(self, calculator, microzones):
        m = calculator.calculate_matrices_intra_type(microzones)
        for by_type in m.values():
            for mat in by_type.values():
                assert (mat >= 0).all() and (mat <= 1).all()

    def test_inter_type_structure(self, calculator, microzones):
        m = calculator.calculate_matrices_inter_type(microzones)
        assert len(m) == len(microzones)
        for mz_id, by_cible in m.items():
            for cible in ["agressions", "incendies", "accidents"]:
                assert cible in by_cible
                for src, vec in by_cible[cible].items():
                    assert src != cible
                    assert len(vec) == 3
                    assert all(0 <= x <= 1 for x in vec)

    def test_voisin_structure(self, calculator, microzones):
        m = calculator.calculate_matrices_voisin(microzones)
        assert len(m) == len(microzones)
        for mz_id, d in m.items():
            assert "voisins" in d and "poids_influence" in d
            assert len(d["voisins"]) == 8
            assert len(d["poids_influence"]) == 8
            assert abs(sum(d["poids_influence"]) - 1.0) < 1e-5
            assert d["seuil_activation"] == 5

    def test_trafic_structure(self, calculator, microzones):
        m = calculator.calculate_matrice_trafic(microzones)
        assert len(m) == len(microzones)
        for mz_id, d in m.items():
            for k in ("prob_engorgement", "prob_desengorgement", "facteur_memoire",
                      "amplitude_engorgement", "amplitude_desengorgement"):
                assert k in d
                assert not np.isnan(d[k])

    def test_alcool_nuit_structure(self, calculator, microzones):
        m = calculator.calculate_matrices_alcool_nuit(microzones)
        assert len(m) == len(microzones)
        for mz_id, by_type in m.items():
            assert by_type.keys() == {"agressions", "incendies", "accidents"}
            for t, d in by_type.items():
                assert "prob_alcool" in d and "prob_nuit" in d
                assert 0 <= d["prob_alcool"] <= 1
                assert 0 <= d["prob_nuit"] <= 1

    def test_saisonnalite_structure(self, calculator, microzones):
        m = calculator.calculate_matrices_saisonnalite(microzones)
        assert len(m) == len(microzones)
        for mz_id, by_type in m.items():
            for t in ["agressions", "incendies", "accidents"]:
                assert t in by_type
                for s in ["hiver", "intersaison", "ete"]:
                    assert s in by_type[t]
                    assert 0.5 <= by_type[t][s] <= 2.0


class TestChargementPickle:
    """IV1: Fichiers pickle lisibles et chargés correctement."""

    def test_precompute_run_produit_pickles(self):
        """Le precompute écrit bien les 6 matrices dans output_dir (IV1)."""
        _scripts_path()
        import pickle
        import shutil
        import yaml
        from precompute_matrices_correlation import precompute_matrices_correlation
        with open(ROOT / "config" / "config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        microzones = _microzones_gdf()
        out = ROOT / "tests" / "tmp_matrices_precompute"
        out.mkdir(parents=True, exist_ok=True)
        try:
            with open(out / "microzones.pkl", "wb") as f:
                pickle.dump(microzones, f)
            ok = precompute_matrices_correlation(cfg, out)
            assert ok
            for name in (
                "matrices_correlation_intra_type.pkl",
                "matrices_correlation_inter_type.pkl",
                "matrices_voisin.pkl",
                "matrices_trafic.pkl",
                "matrices_alcool_nuit.pkl",
                "matrices_saisonnalite.pkl",
            ):
                p = out / name
                assert p.exists(), f"Manquant: {name}"
                with open(p, "rb") as f:
                    data = pickle.load(f)
                assert data is not None
        finally:
            if out.exists():
                shutil.rmtree(out, ignore_errors=True)

    def test_chargement_depuis_source_data_si_presents(self):
        """Charge les matrices depuis data/source_data si pré-calculées."""
        _scripts_path()
        import pickle
        required = (
            "matrices_correlation_intra_type.pkl",
            "matrices_correlation_inter_type.pkl",
            "matrices_voisin.pkl",
            "matrices_trafic.pkl",
            "matrices_alcool_nuit.pkl",
            "matrices_saisonnalite.pkl",
        )
        for name in required:
            p = SOURCE_DATA / name
            if not p.exists():
                pytest.skip(f"Pré-calcul non exécuté: {p} manquant")
            with open(p, "rb") as f:
                data = pickle.load(f)
            assert data is not None
            if "intra_type" in name:
                for by_type in list(data.values())[:1]:
                    for mat in by_type.values():
                        assert mat.shape == (3, 3)
                        assert not np.isnan(mat).any()
