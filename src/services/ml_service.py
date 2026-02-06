"""
MLService - Préparation données ML en fenêtres glissantes de 4 semaines.
MLTrainer - Entraînement et prédiction modèles ML (régression + classification).
Story 2.3.1 - Préparation données ML
Story 2.3.2 - Entraînement modèles ML
Story 2.3.3 - SHAP values

90 features = central sem_m1 (18) + central sem_m2,m3,m4 (54) + voisins_moy sem_m1 (18).
Nomenclature : sem_m1 = dernière semaine (week -1), sem_m2..m4 = 3 semaines précédentes ;
voisins_moy = moyenne des 4 arrondissements adjacents (commune à tous les arrondissements).
DataFrame final : 90 colonnes features + 1 colonne label (score ou classe).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import HuberRegressor, Ridge
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    r2_score,
)

from ..data.adjacents import get_voisins
from ..core.utils.path_resolver import PathResolver
from ..core.utils.pickle_utils import load_pickle, save_pickle
from .feature_calculator import StateCalculator
from .label_calculator import LabelCalculator
from .ml_data_extractor import extract_and_save_ml_data, compute_nb_mois_from_days

# XGBoost optionnel (dépendance optionnelle)
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

# 18 features hebdomadaires (colonnes du DataFrame features, sans arrondissement/semaine)
FEATURE_COLUMNS_18: List[str] = [
    "agressions_moyen_grave",
    "agressions_benin",
    "incendies_moyen_grave",
    "incendies_benin",
    "accidents_moyen_grave",
    "accidents_benin",
    "agressions_alcool",
    "agressions_nuit",
    "incendies_alcool",
    "incendies_nuit",
    "accidents_alcool",
    "accidents_nuit",
    "morts_accidents",
    "morts_incendies",
    "morts_agressions",
    "blesses_graves_accidents",
    "blesses_graves_incendies",
    "blesses_graves_agressions",
]

SEMAINES_PAR_MOIS = 4
NB_VOISINS = 4
NB_FEATURES_CENTRAL_SEM_M1 = 18
NB_FEATURES_CENTRAL_SEM_M2_M4 = 54
NB_FEATURES_VOISINS_MOY_SEM_M1 = 18
TOTAL_FEATURES = 90


class MLService:
    """
    Service de préparation des données ML en fenêtre glissante de 4 semaines.

    - Central sem_m1 (dernière semaine, week -1) : 18 features
    - Central sem_m2, sem_m3, sem_m4 (3 semaines précédentes) : 54 features
    - Voisins_moy sem_m1 (moyenne des 4 arrondissements adjacents, dernière semaine) : 18 features
    - Total : 90 features + 1 label (score ou classe)
    - Nomenclature commune : sem_m1..m4, voisins_moy (pas de numéro d'arrondissement dans les noms)
    """

    def __init__(self) -> None:
        pass

    def _get_features_semaine_arrondissement(
        self,
        df_features: pd.DataFrame,
        arrondissement: int,
        semaine: int,
    ) -> pd.Series:
        """
        Récupère les 18 features pour un (arrondissement, semaine).
        Retourne une Series avec les noms de colonnes ; valeurs à 0 si absent.
        """
        mask = (df_features["arrondissement"] == arrondissement) & (
            df_features["semaine"] == semaine
        )
        row = df_features.loc[mask]
        if row.empty:
            return pd.Series({c: 0 for c in FEATURE_COLUMNS_18})
        return row[FEATURE_COLUMNS_18].iloc[0]

    def construire_ligne_90_features(
        self,
        df_features: pd.DataFrame,
        df_labels: pd.DataFrame,
        arrondissement: int,
        mois: int,
        label_column: str = "score",
    ) -> Optional[dict]:
        """
        Construit une ligne ML (90 features + label) pour un (arrondissement, mois).

        À J+28 (chaque fin de mois) : concatène les 4 semaines empilées (stack à J+7, J+14, J+21, J+28)
        pour former les 90 features (central_sem_m1..m4 + voisins_moy_sem_m1) et attache le label du mois.

        Nomenclature : sem_m1 = dernière semaine du mois (week -1), sem_m2..m4 = 3 semaines précédentes ;
        voisins_moy_sem_m1 = moyenne des 4 arrondissements adjacents (dernière semaine).
        Commune à tous les arrondissements (pas de numéro d'arrondissement dans les noms).

        Returns:
            Dictionnaire avec clés central_sem_m*_, voisins_moy_sem_m1_*, label, ou None si données manquantes.
        """
        semaine_debut = (mois - 1) * SEMAINES_PAR_MOIS + 1
        semaines_mois = list(
            range(semaine_debut, semaine_debut + SEMAINES_PAR_MOIS)
        )
        derniere_semaine = semaines_mois[-1]
        trois_semaines_avant = semaines_mois[:-1]

        # Label
        mask_label = (df_labels["arrondissement"] == arrondissement) & (
            df_labels["mois"] == mois
        )
        labels_row = df_labels.loc[mask_label]
        if labels_row.empty:
            return None
        label_val = labels_row[label_column].iloc[0]

        out = {"run_id": None, "arrondissement": arrondissement, "mois": mois}

        # Central sem_m1 (dernière semaine, week -1) : 18
        central_sem_m1 = self._get_features_semaine_arrondissement(
            df_features, arrondissement, derniere_semaine
        )
        for col in FEATURE_COLUMNS_18:
            out[f"central_sem_m1_{col}"] = central_sem_m1.get(col, 0)

        # Central sem_m2, sem_m3, sem_m4 (3 semaines précédentes) : 54
        for i, sem in enumerate(trois_semaines_avant, 2):
            ser = self._get_features_semaine_arrondissement(
                df_features, arrondissement, sem
            )
            for col in FEATURE_COLUMNS_18:
                out[f"central_sem_m{i}_{col}"] = ser.get(col, 0)

        # Voisins_moy sem_m1 (moyenne des 4 adjacents, dernière semaine) : 18
        voisins = get_voisins(arrondissement)
        sommes_voisins = {c: 0.0 for c in FEATURE_COLUMNS_18}
        for voisin in voisins[:NB_VOISINS]:
            ser = self._get_features_semaine_arrondissement(
                df_features, voisin, derniere_semaine
            )
            for col in FEATURE_COLUMNS_18:
                sommes_voisins[col] = sommes_voisins.get(col, 0) + float(ser.get(col, 0))
        n_voisins = min(len(voisins), NB_VOISINS)
        for col in FEATURE_COLUMNS_18:
            out[f"voisins_moy_sem_m1_{col}"] = sommes_voisins[col] / n_voisins if n_voisins else 0.0

        out["label"] = label_val
        if "score" in labels_row.columns:
            out["score"] = labels_row["score"].iloc[0]
        if "classe" in labels_row.columns:
            out["classe"] = labels_row["classe"].iloc[0]
        return out

    def preparer_run(
        self,
        run_id: str,
        label_column: str = "score",
    ) -> pd.DataFrame:
        """
        Prépare le DataFrame ML (90 features + label) pour un run.

        Charge le stack des features (18 par semaine, empilées à J+7, J+14, J+21, J+28...)
        et les labels depuis data/intermediate/run_{run_id}/ml/.
        À J+28 pour chaque mois : concatène les 4 semaines empilées pour construire
        les 90 features et le label (construire_ligne_90_features).

        Args:
            run_id: Identifiant du run (ex: "001")
            label_column: Colonne label à utiliser ("score" ou "classe")

        Returns:
            DataFrame avec 90 colonnes features + 1 colonne label
        """
        df_features = StateCalculator.load_features(run_id)
        df_labels = LabelCalculator.load_labels(run_id)

        rows = []
        for _, label_row in df_labels.iterrows():
            arr = int(label_row["arrondissement"])
            mois = int(label_row["mois"])
            ligne = self.construire_ligne_90_features(
                df_features, df_labels, arr, mois, label_column=label_column
            )
            if ligne is not None:
                ligne["run_id"] = run_id
                rows.append(ligne)

        if not rows:
            return self._empty_dataframe()

        df = pd.DataFrame(rows)
        # Ordre des colonnes : run_id, arrondissement, mois, 90 features, score?, classe?, label
        meta_cols = ["run_id", "arrondissement", "mois"]
        extra_cols = [c for c in ("score", "classe") if c in df.columns]
        feature_cols = [c for c in df.columns if c not in meta_cols + extra_cols + ["label"]]
        feature_cols.sort()
        df = df[meta_cols + feature_cols + extra_cols + ["label"]]
        df = df.fillna(0)
        for col in feature_cols + ["label"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df

    def _empty_dataframe(self) -> pd.DataFrame:
        """Retourne un DataFrame vide avec la structure attendue (90 features + label)."""
        feature_cols = (
            [f"central_sem_m1_{c}" for c in FEATURE_COLUMNS_18]
            + [f"central_sem_m{i}_{c}" for i in (2, 3, 4) for c in FEATURE_COLUMNS_18]
            + [f"voisins_moy_sem_m1_{c}" for c in FEATURE_COLUMNS_18]
        )
        return pd.DataFrame(columns=["run_id", "arrondissement", "mois"] + feature_cols + ["label"])

    def extract_ml_data_from_run(
        self,
        run_id: str,
        state_path: Optional[Union[str, Path]] = None,
    ) -> bool:
        """
        Extrait features et labels depuis simulation_state.pkl et sauvegarde dans run_XXX/ml/.

        Args:
            run_id: Identifiant du run (ex: "000")
            state_path: Chemin vers simulation_state.pkl. Si None, utilise data/intermediate/run_{run_id}/simulation_state.pkl

        Returns:
            True si succès
        """
        if state_path is None:
            state_path = PathResolver.data_intermediate(f"run_{run_id}", "simulation_state.pkl")
        return extract_and_save_ml_data(state_path=Path(state_path), run_id=run_id)

    def workflow_extract_then_prepare(
        self,
        run_ids: Optional[List[str]] = None,
        nb_runs: Optional[int] = None,
        label_column: str = "score",
        verbose: bool = True,
        calibrate_classification: bool = True,
        progress_callback: Optional[Any] = None,
    ) -> pd.DataFrame:
        """
        Extrait features/labels depuis simulation_state.pkl pour chaque run, puis prépare le DataFrame ML.

        Story 2.4.4 : logique 4*4 semaines min, +2*4 jusqu'à 100*4.
        Si label_column=classe et calibrate_classification=True, recalibre pour ~85/10/5.
        """
        return self.workflow_50_runs(
            run_ids=run_ids,
            nb_runs=nb_runs,
            label_column=label_column,
            verbose=verbose,
            calibrate_classification=calibrate_classification,
            extract_first=True,
            progress_callback=progress_callback,
        )

    def workflow_50_runs(
        self,
        run_ids: Optional[List[str]] = None,
        nb_runs: Optional[int] = None,
        label_column: str = "score",
        verbose: bool = True,
        calibrate_classification: bool = False,
        extract_first: bool = False,
        progress_callback: Optional[Any] = None,
    ) -> pd.DataFrame:
        """
        Agrège les données ML sur N runs (1 affiché + N-1 calcul seul).

        Par défaut run_ids = run_000 à run_049 (ou run_ids déduit de nb_runs).

        Args:
            run_ids: Liste des run_id à traiter (ex: ["000","001",...])
            nb_runs: Si run_ids est None, génère run_ids pour 0..nb_runs-1 (défaut 50)
            label_column: Colonne label ("score" ou "classe")
            verbose: Afficher la progression
            calibrate_classification: Si True et label_column=classe, recalibre pour ~85/10/5
            extract_first: Si True, extrait features/labels depuis simulation_state avant
            progress_callback: Callback(current, total, phase) avec phase="extract"|"prepare"

        Returns:
            DataFrame géant : 90 colonnes features + 1 colonne label
        """
        n = nb_runs if nb_runs is not None else 50
        if run_ids is None:
            run_ids = [f"{i:03d}" for i in range(n)]
        total = len(run_ids)

        if extract_first:
            for i, run_id in enumerate(run_ids):
                if verbose and (i == 0 or i % 10 == 0):
                    print(f"Extraction run {run_id}...")
                try:
                    self.extract_ml_data_from_run(run_id)
                    if progress_callback is not None:
                        progress_callback(i + 1, total, "extract")
                except Exception as e:
                    if verbose and i == 0:
                        print(f"  Skip {run_id}: {e}")

        dfs = []
        for i, run_id in enumerate(run_ids):
            show = verbose and (i == 0)
            try:
                df_run = self.preparer_run(run_id, label_column=label_column)
                if not df_run.empty:
                    dfs.append(df_run)
                if show:
                    print(f"Run {run_id}: {len(df_run)} lignes")
                if progress_callback is not None:
                    progress_callback(i + 1, total, "prepare")
            except FileNotFoundError as e:
                if show:
                    print(f"Run {run_id}: skip ({e})")
                continue

        if not dfs:
            return self._empty_dataframe()

        df = pd.concat(dfs, ignore_index=True)

        if calibrate_classification and label_column == "classe" and "score" in df.columns:
            df = calibrate_labels_classification(df, score_column="score", classe_column="classe")
            if "label" in df.columns:
                df["label"] = df["classe"]

        return df

    def save_features_labels(
        self,
        df_ml: pd.DataFrame,
        output_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Sauvegarde le DataFrame ML (features + label) au format pickle standardisé.

        Args:
            df_ml: DataFrame 90 features + label
            output_path: Chemin de sortie (défaut: data/intermediate/ml/features_labels.pkl)
        """
        if output_path is None:
            output_path = PathResolver.data_intermediate("ml", "features_labels.pkl")
        else:
            output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data_dict = {
            "data": df_ml.to_dict("records"),
            "columns": list(df_ml.columns),
            "index": df_ml.index.tolist(),
        }
        save_pickle(
            data=data_dict,
            path=output_path,
            data_type="features_labels",
            description=f"ML 90 features + label, {len(df_ml)} lignes",
            schema_version="1.0",
        )

    @classmethod
    def load_features_labels(
        cls,
        path: Optional[Union[str, Path]] = None,
    ) -> pd.DataFrame:
        """
        Charge le DataFrame ML depuis un fichier pickle.

        Args:
            path: Chemin (défaut: data/intermediate/ml/features_labels.pkl)

        Returns:
            DataFrame 90 features + label
        """
        if path is None:
            path = PathResolver.data_intermediate("ml", "features_labels.pkl")
        else:
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier features_labels introuvable: {path}")
        data = load_pickle(path, expected_type="features_labels")
        if isinstance(data, dict) and "data" in data:
            df = pd.DataFrame(data["data"])
            if "columns" in data:
                df = df.reindex(columns=data["columns"])
            return df
        return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Story 2.3.2 - Entraînement modèles ML
# ---------------------------------------------------------------------------

# Colonnes non-features du DataFrame ML (label peut être "score" ou "classe")
ML_NON_FEATURE_COLUMNS = {"run_id", "arrondissement", "mois", "label", "score", "classe"}

# Cibles calibration Story 2.4.4
CALIBRATION_PCT_NORMAL = 0.85
CALIBRATION_PCT_PRE_CATA = 0.10
CALIBRATION_PCT_CATA = 0.05


def calibrate_labels_classification(
    df: pd.DataFrame,
    score_column: str = "score",
    classe_column: str = "classe",
    pct_normal: float = CALIBRATION_PCT_NORMAL,
    pct_pre_cata: float = CALIBRATION_PCT_PRE_CATA,
) -> pd.DataFrame:
    """
    Recalibre la colonne classe pour viser ~85% Normal, ~10% Pre-cata, ~5% Cata.

    Utilise les percentiles du score pour définir les seuils.

    Args:
        df: DataFrame avec colonnes score et classe
        score_column: Nom de la colonne score
        classe_column: Nom de la colonne classe à écrire
        pct_normal: Cible % Normal
        pct_pre_cata: Cible % Pre-catastrophique

    Returns:
        DataFrame avec colonne classe mise à jour
    """
    from .label_calculator import CLASSE_NORMAL, CLASSE_PRE_CATASTROPHE, CLASSE_CATASTROPHE

    df = df.copy()
    if score_column not in df.columns or len(df) == 0:
        return df

    scores = df[score_column].values
    p85 = float(np.percentile(scores, (pct_normal) * 100))
    p95 = float(np.percentile(scores, (pct_normal + pct_pre_cata) * 100))

    def _classe(s: float) -> str:
        if s <= p85:
            return CLASSE_NORMAL
        if s <= p95:
            return CLASSE_PRE_CATASTROPHE
        return CLASSE_CATASTROPHE

    df[classe_column] = df[score_column].apply(_classe)
    return df


def _get_ml_feature_columns(df: pd.DataFrame) -> List[str]:
    """Retourne la liste des colonnes features (exclut run_id, arrondissement, mois, label/score/classe)."""
    return [c for c in df.columns if c not in ML_NON_FEATURE_COLUMNS]


class MLTrainer:
    """
    Entraînement et prédiction des modèles ML.

    - 2 régression : Huber Regressor, Ridge (MAE, RMSE, R²)
    - 2 classification : Logistic Regression, XGBoost (Accuracy, Precision, Recall, F1)
    - Sauvegarde : {algo}_{numero}_{params}.joblib dans data/models/regression/ ou classification/
    """

    def __init__(self) -> None:
        pass

    def _get_X_y(
        self,
        df: pd.DataFrame,
        label_column: str,
    ) -> tuple:
        """Extrait X (features) et y (label) du DataFrame ML."""
        feature_cols = _get_ml_feature_columns(df)
        if not feature_cols:
            raise ValueError("Aucune colonne feature trouvée dans le DataFrame")
        X = df[feature_cols].copy()
        X = X.fillna(0)
        if label_column not in df.columns:
            raise ValueError(f"Colonne label '{label_column}' absente du DataFrame")
        y = df[label_column]
        return X, y, feature_cols

    def _metrics_regression(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calcule MAE, RMSE, R² pour la régression."""
        return {
            "MAE": float(mean_absolute_error(y_true, y_pred)),
            "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "R2": float(r2_score(y_true, y_pred)),
        }

    def _metrics_classification(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        average: str = "macro",
    ) -> Dict[str, float]:
        """Calcule Accuracy, Precision, Recall, F1 pour la classification."""
        return {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, average=average, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, average=average, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, average=average, zero_division=0)),
        }

    def _path_model(self, subdir: str, algo: str, numero: str, params: str) -> Path:
        """Chemin de sauvegarde : data/models/{subdir}/{algo}_{numero}_{params}.joblib."""
        root = PathResolver.get_project_root()
        dir_path = root / "data" / "models" / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        safe_params = params.replace("/", "_").replace(" ", "_")[:30]
        return dir_path / f"{algo}_{numero}_{safe_params}.joblib"

    def _save_model(
        self,
        model: Any,
        metadata: Dict[str, Any],
        subdir: str,
        algo: str,
        numero: str,
        params: str,
    ) -> Path:
        """Sauvegarde le modèle et ses métadonnées en joblib."""
        path = self._path_model(subdir, algo, numero, params)
        payload = {"model": model, "metadata": metadata}
        joblib.dump(payload, path)
        return path

    def train_regression_models(
        self,
        df_ml: pd.DataFrame,
        label_column: str = "score",
        numero_entrainement: str = "001",
        params_str: str = "default",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Entraîne Huber Regressor et Ridge sur le label (régression).

        Returns:
            Dict algo -> { "model", "metrics", "path", "feature_columns" } (huber_regressor, ridge)
        """
        from sklearn.model_selection import train_test_split

        X, y, feature_cols = self._get_X_y(df_ml, label_column)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        y_train = np.asarray(y_train, dtype=float)
        y_test = np.asarray(y_test, dtype=float)

        results: Dict[str, Dict[str, Any]] = {}

        # Huber Regressor (pas de random_state en sklearn)
        huber = HuberRegressor(epsilon=1.35, max_iter=200)
        huber.fit(X_train, y_train)
        y_pred_huber = huber.predict(X_test)
        metrics_huber = self._metrics_regression(y_test, y_pred_huber)
        meta_huber = {
            "algo": "huber_regressor",
            "numero_entrainement": numero_entrainement,
            "params": params_str,
            "metrics": metrics_huber,
            "feature_columns": feature_cols,
        }
        path_huber = self._save_model(huber, meta_huber, "regression", "huber_regressor", numero_entrainement, params_str)
        results["huber_regressor"] = {"model": huber, "metrics": metrics_huber, "path": path_huber, "feature_columns": feature_cols}

        # Ridge
        ridge = Ridge(alpha=1.0, random_state=random_state)
        ridge.fit(X_train, y_train)
        y_pred_ridge = ridge.predict(X_test)
        metrics_ridge = self._metrics_regression(y_test, y_pred_ridge)
        meta_ridge = {
            "algo": "ridge",
            "numero_entrainement": numero_entrainement,
            "params": params_str,
            "metrics": metrics_ridge,
            "feature_columns": feature_cols,
        }
        path_ridge = self._save_model(ridge, meta_ridge, "regression", "ridge", numero_entrainement, params_str)
        results["ridge"] = {"model": ridge, "metrics": metrics_ridge, "path": path_ridge, "feature_columns": feature_cols}

        return results

    def train_classification_models(
        self,
        df_ml: pd.DataFrame,
        label_column: str = "classe",
        numero_entrainement: str = "001",
        params_str: str = "default",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Entraîne Logistic Regression et XGBoost sur le label (classification).

        Returns:
            Dict algo -> { "model", "metrics", "path", "feature_columns" }
        """
        from sklearn.model_selection import train_test_split

        X, y, feature_cols = self._get_X_y(df_ml, label_column)
        # Encoder les classes en entiers si besoin
        if y.dtype == object or y.dtype.name == "category" or not np.issubdtype(y.dtype, np.number):
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            y_enc = le.fit_transform(y.astype(str))
            self._label_encoder = le
        else:
            y_enc = np.asarray(y, dtype=int)
            self._label_encoder = None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_enc, test_size=test_size, random_state=random_state
        )

        results = {}

        # Logistic Regression
        logreg = LogisticRegression(max_iter=500, random_state=random_state)
        logreg.fit(X_train, y_train)
        y_pred_lr = logreg.predict(X_test)
        metrics_lr = self._metrics_classification(y_test, y_pred_lr)
        meta_lr = {
            "algo": "logistic_regression",
            "numero_entrainement": numero_entrainement,
            "params": params_str,
            "metrics": metrics_lr,
            "feature_columns": feature_cols,
        }
        path_lr = self._save_model(
            logreg, meta_lr, "classification", "logistic_regression", numero_entrainement, params_str
        )
        results["logistic_regression"] = {"model": logreg, "metrics": metrics_lr, "path": path_lr, "feature_columns": feature_cols}

        # XGBoost (optionnel)
        if HAS_XGBOOST:
            xgb_clf = xgb.XGBClassifier(n_estimators=100, max_depth=6, random_state=random_state)
            xgb_clf.fit(X_train, y_train)
            y_pred_xgb = xgb_clf.predict(X_test)
            metrics_xgb = self._metrics_classification(y_test, y_pred_xgb)
            meta_xgb = {
                "algo": "xgboost",
                "numero_entrainement": numero_entrainement,
                "params": params_str,
                "metrics": metrics_xgb,
                "feature_columns": feature_cols,
            }
            path_xgb = self._save_model(xgb_clf, meta_xgb, "classification", "xgboost", numero_entrainement, params_str)
            results["xgboost"] = {"model": xgb_clf, "metrics": metrics_xgb, "path": path_xgb, "feature_columns": feature_cols}
        else:
            results["xgboost"] = None  # non disponible

        return results

    def train_all(
        self,
        df_ml: pd.DataFrame,
        numero_entrainement: str = "001",
        params_str: str = "default",
        label_regression: str = "score",
        label_classification: str = "classe",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Entraîne les 4 modèles (2 régression + 2 classification).

        Returns:
            Dict "regression" -> results Huber/Ridge, "classification" -> results LogReg/XGBoost
        """
        out = {}
        out["regression"] = self.train_regression_models(
            df_ml, label_column=label_regression, numero_entrainement=numero_entrainement,
            params_str=params_str, test_size=test_size, random_state=random_state,
        )
        out["classification"] = self.train_classification_models(
            df_ml, label_column=label_classification, numero_entrainement=numero_entrainement,
            params_str=params_str, test_size=test_size, random_state=random_state,
        )
        return out

    @staticmethod
    def load_model(path: Union[str, Path]) -> Dict[str, Any]:
        """
        Charge un modèle sauvegardé (joblib).

        Returns:
            Dict avec "model" et "metadata"
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Modèle introuvable: {path}")
        return joblib.load(path)

    @staticmethod
    def _prepare_X_for_prediction(
        row_or_df: pd.DataFrame,
        model_payload: Dict[str, Any],
        df_ml: Optional[pd.DataFrame] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Prépare X pour prédiction en alignant les colonnes du modèle.
        Gère les modèles avec noms réels (central_sem_m1_*) ou génériques (f0, f1, ...).
        Retourne None si impossible de construire X valide.
        """
        feat_cols = model_payload.get("metadata", {}).get("feature_columns", [])
        if not feat_cols:
            return None
        df_cols = _get_ml_feature_columns(df_ml) if df_ml is not None else _get_ml_feature_columns(row_or_df)
        if not df_cols:
            return None

        # Cas 1 : les colonnes du modèle existent dans la row
        common = [c for c in feat_cols if c in row_or_df.columns]
        if len(common) == len(feat_cols):
            X = row_or_df[feat_cols].fillna(0)
            if len(X) == 0:
                return None
            return X.astype(float)

        # Cas 2 : modèle avec f0, f1... — mapper par position depuis df_cols (triées)
        if all(c.startswith("f") and c[1:].isdigit() for c in feat_cols):
            src_cols = [c for c in sorted(df_cols) if c in row_or_df.columns]
            n = min(len(feat_cols), len(src_cols))
            if n == 0:
                return None
            data = row_or_df[src_cols[:n]].fillna(0).values
            if data.size == 0:
                return None
            mapping = {feat_cols[i]: float(data[0, i]) for i in range(n)}
            for i in range(n, len(feat_cols)):
                mapping[feat_cols[i]] = 0.0
            return pd.DataFrame([mapping])[feat_cols]

        # Cas 3 : fallback — compléter les colonnes manquantes par 0
        use_cols = [c for c in feat_cols if c in row_or_df.columns]
        if not use_cols:
            return None
        X = row_or_df[use_cols].fillna(0).copy()
        for c in feat_cols:
            if c not in X.columns:
                X[c] = 0.0
        X = X[feat_cols]
        return X.astype(float) if len(X) > 0 else None

    @staticmethod
    def predict_regression(model_payload: Dict[str, Any], X: pd.DataFrame) -> np.ndarray:
        """Prédiction régression. X doit avoir les mêmes colonnes que feature_columns."""
        model = model_payload["model"]
        return model.predict(X)

    @staticmethod
    def predict_classification(model_payload: Dict[str, Any], X: pd.DataFrame) -> np.ndarray:
        """Prédiction classification."""
        model = model_payload["model"]
        return model.predict(X)


# ---------------------------------------------------------------------------
# Story 2.3.3 - SHAP values pour interprétabilité
# ---------------------------------------------------------------------------

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


def compute_shap_values(
    model: Any,
    X: Union[pd.DataFrame, np.ndarray],
    feature_names: Optional[List[str]] = None,
    model_type: str = "linear",
    max_samples: Optional[int] = 100,
) -> Dict[str, Any]:
    """
    Calcule les SHAP values pour un modèle (régression ou classification).

    Nomenclature des features : central_sem_m1_*, central_sem_m2_*, ... voisins_moy_sem_m1_*
    (sem_m1 = dernière semaine / week -1, voisins_moy = moyenne des 4 arrondissements adjacents).

    Args:
        model: Modèle sklearn (Huber, Ridge, LogReg) ou XGBoost
        X: DataFrame ou array des features (90 colonnes)
        feature_names: Noms des colonnes (déduits de X si DataFrame)
        model_type: "linear" (Huber, Ridge, LogReg) ou "tree" (XGBoost)
        max_samples: Limiter le nombre d'échantillons pour accélérer (None = tous)

    Returns:
        Dict avec "shap_values", "base_values", "feature_names", "explainer"
    """
    if not HAS_SHAP:
        raise ImportError("SHAP non installé : pip install shap")
    if isinstance(X, pd.DataFrame):
        X_arr = np.asarray(X, dtype=float)
        if feature_names is None:
            feature_names = list(X.columns)
    else:
        X_arr = np.asarray(X, dtype=float)
        if feature_names is None:
            feature_names = [f"f{i}" for i in range(X_arr.shape[1])]
    if max_samples is not None and len(X_arr) > max_samples:
        rng = np.random.RandomState(42)
        idx = rng.choice(len(X_arr), max_samples, replace=False)
        X_arr = X_arr[idx]
    if model_type == "tree":
        explainer = shap.TreeExplainer(model, X_arr)
    else:
        masker = shap.maskers.Independent(X_arr)
        explainer = shap.LinearExplainer(model, masker)
    shap_values = explainer.shap_values(X_arr)
    if isinstance(shap_values, list):
        shap_values = shap_values[0] if len(shap_values) > 0 else shap_values
    return {
        "shap_values": shap_values,
        "base_values": getattr(explainer, "expected_value", None),
        "feature_names": feature_names,
        "explainer": explainer,
    }


def save_shap_values(
    shap_result: Dict[str, Any],
    path: Union[str, Path],
    algo_name: str = "model",
) -> None:
    """Sauvegarde les SHAP values (sans l'explainer) en joblib pour réutilisation."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    to_save = {
        "shap_values": shap_result["shap_values"],
        "base_values": shap_result.get("base_values"),
        "feature_names": shap_result["feature_names"],
        "algo": algo_name,
    }
    joblib.dump(to_save, path)
