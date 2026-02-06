"""
Tests unitaires pour MLTrainer - Entraînement modèles ML (régression et classification).
Story 2.3.2 - Entraînement modèles ML
"""

import pytest
import numpy as np
import pandas as pd

from src.services.ml_service import (
    MLTrainer,
    _get_ml_feature_columns,
    ML_NON_FEATURE_COLUMNS,
    TOTAL_FEATURES,
)


def _make_df_ml_regression(n_rows: int = 100, n_features: int = 144) -> pd.DataFrame:
    """DataFrame ML minimal pour régression (score continu)."""
    np.random.seed(42)
    feature_cols = [f"f{i}" for i in range(n_features)]
    X = np.random.randn(n_rows, n_features).astype(np.float32)
    y = X[:, 0] * 0.5 + X[:, 1] * 0.3 + np.random.randn(n_rows) * 0.2
    df = pd.DataFrame(X, columns=feature_cols)
    df["run_id"] = "001"
    df["arrondissement"] = 1
    df["mois"] = 1
    df["score"] = y
    return df


def _make_df_ml_classification(n_rows: int = 100, n_features: int = 144) -> pd.DataFrame:
    """DataFrame ML minimal pour classification (classes)."""
    np.random.seed(42)
    feature_cols = [f"f{i}" for i in range(n_features)]
    X = np.random.randn(n_rows, n_features).astype(np.float32)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    classes = ["Normal", "Pre-catastrophique"]
    df = pd.DataFrame(X, columns=feature_cols)
    df["run_id"] = "001"
    df["arrondissement"] = 1
    df["mois"] = 1
    df["classe"] = [classes[i % 2] for i in y]
    return df


class TestGetMLFeatureColumns:
    """Tests extraction des colonnes features du DataFrame ML."""

    def test_exclut_run_id_arrondissement_mois_label(self):
        """_get_ml_feature_columns exclut run_id, arrondissement, mois, label."""
        df = pd.DataFrame({
            "run_id": [1], "arrondissement": [1], "mois": [1],
            "f1": [0.0], "f2": [1.0], "label": [2.5],
        })
        cols = _get_ml_feature_columns(df)
        assert "f1" in cols
        assert "f2" in cols
        assert "run_id" not in cols
        assert "arrondissement" not in cols
        assert "mois" not in cols
        assert "label" not in cols

    def test_retourne_liste_non_vide_si_features_presentes(self):
        """Retourne une liste non vide si des colonnes features existent."""
        df = _make_df_ml_regression(n_rows=10, n_features=5)
        cols = _get_ml_feature_columns(df)
        assert len(cols) == 5


class TestMLTrainerRegression:
    """Tests entraînement régression (Huber Regressor, Ridge)."""

    @pytest.fixture
    def trainer(self):
        return MLTrainer()

    @pytest.fixture
    def df_reg(self):
        return _make_df_ml_regression(n_rows=80, n_features=20)

    def test_train_regression_models_retourne_dict(self, trainer, df_reg):
        """train_regression_models retourne un dict avec huber_regressor et ridge."""
        results = trainer.train_regression_models(
            df_reg, label_column="score", numero_entrainement="001", params_str="default", test_size=0.2
        )
        assert "huber_regressor" in results
        assert "ridge" in results
        assert "metrics" in results["huber_regressor"]
        assert "MAE" in results["huber_regressor"]["metrics"]
        assert "RMSE" in results["huber_regressor"]["metrics"]
        assert "R2" in results["huber_regressor"]["metrics"]
        assert "path" in results["huber_regressor"]
        assert results["huber_regressor"]["path"].exists()

    def test_metrics_regression_format(self, trainer):
        """_metrics_regression retourne MAE, RMSE, R²."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.0, 2.9])
        m = trainer._metrics_regression(y_true, y_pred)
        assert "MAE" in m
        assert "RMSE" in m
        assert "R2" in m
        assert isinstance(m["MAE"], float)
        assert isinstance(m["R2"], float)


class TestMLTrainerClassification:
    """Tests entraînement classification (Logistic Regression, XGBoost)."""

    @pytest.fixture
    def trainer(self):
        return MLTrainer()

    @pytest.fixture
    def df_clf(self):
        return _make_df_ml_classification(n_rows=80, n_features=20)

    def test_train_classification_models_retourne_dict(self, trainer, df_clf):
        """train_classification_models retourne logistic_regression et xgboost (si dispo)."""
        results = trainer.train_classification_models(
            df_clf, label_column="classe", numero_entrainement="001", params_str="default", test_size=0.2
        )
        assert "logistic_regression" in results
        assert "xgboost" in results
        assert results["logistic_regression"] is not None
        assert "metrics" in results["logistic_regression"]
        assert "accuracy" in results["logistic_regression"]["metrics"]
        assert "f1" in results["logistic_regression"]["metrics"]
        assert "path" in results["logistic_regression"]
        assert results["logistic_regression"]["path"].exists()

    def test_metrics_classification_format(self, trainer):
        """_metrics_classification retourne accuracy, precision, recall, f1."""
        y_true = np.array([0, 1, 1, 0])
        y_pred = np.array([0, 1, 0, 0])
        m = trainer._metrics_classification(y_true, y_pred)
        assert "accuracy" in m
        assert "precision" in m
        assert "recall" in m
        assert "f1" in m
        assert isinstance(m["accuracy"], float)
        assert 0 <= m["accuracy"] <= 1


class TestMLTrainerSauvegardeChargement:
    """Tests sauvegarde et rechargement des modèles."""

    def test_save_et_load_model(self, tmp_path):
        """Modèle sauvegardé en joblib peut être rechargé."""
        df = _make_df_ml_regression(n_rows=60, n_features=10)
        trainer = MLTrainer()
        results = trainer.train_regression_models(
            df, label_column="score", numero_entrainement="001", params_str="test", test_size=0.3
        )
        path = results["ridge"]["path"]
        payload = MLTrainer.load_model(path)
        assert "model" in payload
        assert "metadata" in payload
        assert payload["metadata"].get("algo") == "ridge"
        assert "metrics" in payload["metadata"]

    def test_predict_regression_apres_load(self):
        """Prédiction régression après chargement du modèle."""
        df = _make_df_ml_regression(n_rows=50, n_features=10)
        trainer = MLTrainer()
        results = trainer.train_regression_models(df, label_column="score", numero_entrainement="001", params_str="p", test_size=0.2)
        path = results["huber_regressor"]["path"]
        payload = MLTrainer.load_model(path)
        X_new = df[_get_ml_feature_columns(df)].iloc[:5]
        pred = MLTrainer.predict_regression(payload, X_new)
        assert pred.shape == (5,)
        assert np.issubdtype(pred.dtype, np.floating)


class TestMLTrainerTrainAll:
    """Tests train_all (4 modèles)."""

    def test_train_all_retourne_regression_et_classification(self):
        """train_all entraîne régression et classification."""
        df_reg = _make_df_ml_regression(n_rows=60, n_features=15)
        df_clf = _make_df_ml_classification(n_rows=60, n_features=15)
        # DataFrame avec score et classe pour train_all
        df = df_reg.copy()
        df["classe"] = df_clf["classe"]
        trainer = MLTrainer()
        out = trainer.train_all(
            df, numero_entrainement="001", params_str="default",
            label_regression="score", label_classification="classe", test_size=0.2
        )
        assert "regression" in out
        assert "classification" in out
        assert "huber_regressor" in out["regression"]
        assert "ridge" in out["regression"]
        assert "logistic_regression" in out["classification"]
