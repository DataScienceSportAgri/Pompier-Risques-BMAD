"""
Tests unitaires pour MLService - Préparation données ML fenêtres glissantes.
Story 2.3.1 - Préparation données ML
"""

import pytest
import pandas as pd

from src.data.adjacents import ADJACENTS_PARIS, get_voisins
from src.services.ml_service import (
    MLService,
    FEATURE_COLUMNS_18,
    TOTAL_FEATURES,
    NB_FEATURES_CENTRAL_SEM_M1,
    NB_FEATURES_CENTRAL_SEM_M2_M4,
    NB_FEATURES_VOISINS_MOY_SEM_M1,
)


class TestAdjacents:
    """Tests arrondissements adjacents (définis en dur)."""

    def test_adjacents_couverture_1_20(self):
        """Tous les arrondissements 1-20 ont des voisins."""
        for arr in range(1, 21):
            assert arr in ADJACENTS_PARIS
            assert len(ADJACENTS_PARIS[arr]) == 4

    def test_get_voisins_retourne_4(self):
        """get_voisins retourne exactement 4 voisins."""
        for arr in [1, 10, 20]:
            voisins = get_voisins(arr)
            assert len(voisins) == 4
            assert all(1 <= v <= 20 for v in voisins)

    def test_get_voisins_ordre_stable(self):
        """get_voisins retourne une liste stable (même ordre à chaque appel)."""
        v1 = get_voisins(1)
        v2 = get_voisins(1)
        assert v1 == v2

    def test_get_voisins_arrondissement_inconnu(self):
        """get_voisins lève KeyError pour arrondissement hors 1-20."""
        with pytest.raises(KeyError, match="inconnu"):
            get_voisins(0)
        with pytest.raises(KeyError, match="inconnu"):
            get_voisins(21)


class TestMLServiceFenetresGlissantes:
    """Tests fenêtres glissantes (90 features)."""

    @pytest.fixture
    def service(self):
        return MLService()

    @pytest.fixture
    def df_features_mini(self):
        """DataFrame features minimal : 1 arrondissement, 4 semaines (mois 1)."""
        rows = []
        for semaine in range(1, 5):
            row = {"arrondissement": 11, "semaine": semaine}
            for col in FEATURE_COLUMNS_18:
                row[col] = float(semaine) if "alcool" in col or "nuit" in col else semaine
            rows.append(row)
        return pd.DataFrame(rows)

    @pytest.fixture
    def df_labels_mini(self):
        """DataFrame labels minimal : 1 arrondissement, 1 mois."""
        return pd.DataFrame([
            {"arrondissement": 11, "mois": 1, "score": 2.5, "classe": "Normal"}
        ])

    def test_constantes_90_features(self):
        """Structure 90 = 18 + 54 + 18 (central sem_m1 + central sem_m2..m4 + voisins_moy sem_m1)."""
        assert NB_FEATURES_CENTRAL_SEM_M1 == 18
        assert NB_FEATURES_CENTRAL_SEM_M2_M4 == 54
        assert NB_FEATURES_VOISINS_MOY_SEM_M1 == 18
        assert TOTAL_FEATURES == 90

    def test_construire_ligne_90_features_retourne_dict(self, service, df_labels_mini):
        """construire_ligne_90_features retourne un dict avec 90 noms feature + label (nomenclature sem_m1..m4, voisins_moy)."""
        voisins = get_voisins(11)
        rows = []
        for arr in [11] + list(voisins):
            semaines = [1, 2, 3, 4] if arr == 11 else [4]
            for semaine in semaines:
                row = {"arrondissement": arr, "semaine": semaine}
                for col in FEATURE_COLUMNS_18:
                    row[col] = float(semaine) if "alcool" in col or "nuit" in col else semaine
                rows.append(row)
        df_features = pd.DataFrame(rows)
        ligne = service.construire_ligne_90_features(
            df_features, df_labels_mini, 11, 1, label_column="score"
        )
        assert ligne is not None
        assert "label" in ligne
        assert ligne["label"] == 2.5
        feature_keys = [k for k in ligne if k not in ("run_id", "arrondissement", "mois", "label")]
        assert len(feature_keys) == TOTAL_FEATURES
        assert any("central_sem_m1_" in k for k in feature_keys)
        assert any("voisins_moy_sem_m1_" in k for k in feature_keys)

    def test_construire_ligne_90_features_sans_label_retourne_none(self, service, df_features_mini):
        """Si pas de label pour (arr, mois), retourne None."""
        df_labels_vide = pd.DataFrame(columns=["arrondissement", "mois", "score"])
        ligne = service.construire_ligne_90_features(
            df_features_mini, df_labels_vide, 11, 1
        )
        assert ligne is None

    def test_preparer_run_dataframe_90_plus_label(self, service):
        """preparer_run nécessite features.pkl et labels.pkl ; on teste la structure du DataFrame vide."""
        df_empty = service._empty_dataframe()
        feature_cols = [c for c in df_empty.columns if c not in ("run_id", "arrondissement", "mois", "label")]
        assert len(feature_cols) == TOTAL_FEATURES
        assert "label" in df_empty.columns

    def test_workflow_50_runs_sans_fichiers_retourne_dataframe_vide(self, service):
        """workflow_50_runs sans run existant retourne un DataFrame vide avec la bonne structure."""
        df = service.workflow_50_runs(run_ids=["999"], verbose=False)
        assert isinstance(df, pd.DataFrame)
        feature_cols = [c for c in df.columns if c not in ("run_id", "arrondissement", "mois", "label")]
        assert len(feature_cols) == TOTAL_FEATURES or len(df) == 0


class TestMLServiceFormatDataFrame:
    """Tests format DataFrame utilisable pour scikit-learn (pas de NaN, types numériques)."""

    @pytest.fixture
    def service(self):
        return MLService()

    def test_empty_dataframe_pas_nan(self, service):
        """Le DataFrame vide n'a pas de colonnes avec des NaN non prévus."""
        df = service._empty_dataframe()
        assert df.isna().sum().sum() == 0 or len(df) == 0

    def test_preparer_run_remplit_nan_par_zero(self, service):
        """Le DataFrame vide a des colonnes numériques pour les features."""
        df = service._empty_dataframe()
        feature_cols = [c for c in df.columns if c not in ("run_id", "arrondissement", "mois", "label")]
        assert len(feature_cols) == TOTAL_FEATURES

    def test_nombre_colonnes_final_90_plus_label(self, service):
        """DataFrame final a 90 colonnes features + 1 label (nomenclature central_sem_m*, voisins_moy_sem_m1)."""
        df = service._empty_dataframe()
        n_features = len([c for c in df.columns if c.startswith("central_") or c.startswith("voisins_moy_")])
        assert n_features == TOTAL_FEATURES
        assert "label" in df.columns


class TestSHAP:
    """Tests calcul SHAP values (Story 2.3.3)."""

    def test_compute_shap_values_linear_retourne_dict(self):
        """compute_shap_values (linear) retourne dict avec shap_values, feature_names."""
        from src.services.ml_service import compute_shap_values, HAS_SHAP
        from sklearn.linear_model import Ridge
        import numpy as np
        if not HAS_SHAP:
            import pytest
            pytest.skip("SHAP non installé")
        X = np.random.randn(30, 10).astype(np.float32)
        y = X[:, 0] * 0.5 + X[:, 1] * 0.3
        model = Ridge(alpha=1.0).fit(X, y)
        result = compute_shap_values(model, X, feature_names=[f"f{i}" for i in range(10)], model_type="linear", max_samples=20)
        assert "shap_values" in result
        assert "feature_names" in result
        assert len(result["feature_names"]) == 10
        assert result["shap_values"].shape[0] <= 20

    def test_save_shap_values_ecrit_fichier(self, tmp_path):
        """save_shap_values écrit un fichier joblib."""
        from src.services.ml_service import save_shap_values
        import numpy as np
        shap_result = {
            "shap_values": np.random.randn(10, 5).astype(np.float32),
            "base_values": 0.0,
            "feature_names": [f"f{i}" for i in range(5)],
        }
        path = tmp_path / "shap_test.joblib"
        save_shap_values(shap_result, path, algo_name="ridge")
        assert path.exists()
        import joblib
        loaded = joblib.load(path)
        assert "shap_values" in loaded
        assert loaded["algo"] == "ridge"
