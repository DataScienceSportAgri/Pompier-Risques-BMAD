"""
Extraction des features et labels ML depuis SimulationState.
Story 2.4.4 - Interface ML modèles

Logique :
- Stack des features à J+7, J+14, J+21, J+28... : pour chaque semaine k (1 à nb_semaines),
  on calcule les 18 features de la semaine k (jours (k-1)*7 à k*7-1) et on les empile.
- À J+28 (et J+56, J+84...), on concatène les 4 semaines empilées pour construire les 90 features
  (central_sem_m1..m4 + voisins_moy_sem_m1) et le label du mois (voir ml_service.construire_ligne_90_features).

Grille : 4*4 semaines min, incréments 8 semaines, max 100*4 semaines.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from src.core.state.simulation_state import SimulationState
from src.core.utils.path_resolver import PathResolver
from src.services.casualty_calculator import CasualtyCalculator
from src.services.feature_calculator import StateCalculator
from src.services.label_calculator import LabelCalculator

# Constantes de comptage (Story 2.4.4)
# Grille : 4*4 semaines à 100*4 semaines par pallier de 8 semaines
SEMAINES_PAR_MOIS = 4
SEMAINES_MIN = 16   # 4*4
SEMAINES_MAX = 400  # 100*4
PALIER_SEMAINES = 8

# Valeurs autorisées : 16, 24, 32, ..., 400
SEMAINES_GRID = list(range(SEMAINES_MIN, SEMAINES_MAX + 1, PALIER_SEMAINES))


def get_allowed_durations_days() -> List[int]:
    """Retourne les durées autorisées en jours : 112, 168, 224, ..., 2800."""
    return [s * 7 for s in SEMAINES_GRID]


def _run_id_numeric(run_id: str) -> str:
    """Extrait la partie numérique du run_id (ex: run_000 -> 000)."""
    if run_id.startswith("run_"):
        return run_id[4:]
    return run_id


def compute_nb_semaines_from_days(total_days: int) -> int:
    """
    Calcule le nombre de semaines exploitables selon la grille 16, 24, 32, ..., 400.

    Args:
        total_days: Nombre total de jours de simulation

    Returns:
        Nombre de semaines (0 si insuffisant)
    """
    semaines_dispo = total_days // 7
    if semaines_dispo < SEMAINES_MIN:
        return 0
    for s in reversed(SEMAINES_GRID):
        if s <= semaines_dispo:
            return s
    return SEMAINES_MIN


def compute_nb_mois_from_days(total_days: int) -> int:
    """
    Calcule le nombre de mois (4 semaines chacun) exploitables selon la grille.

    Returns:
        Nombre de mois (= nb_semaines // 4)
    """
    nb_sem = compute_nb_semaines_from_days(total_days)
    return nb_sem // SEMAINES_PAR_MOIS if nb_sem > 0 else 0


def extract_features_and_labels(
    state: SimulationState,
    run_id: Optional[str] = None,
    nb_mois: Optional[int] = None,
    prediction_min: bool = False,
) -> Tuple[Optional[object], Optional[object]]:
    """
    Extrait features (DataFrame) et labels (DataFrame) depuis un SimulationState.

    Stack des semaines à J+7, J+14, J+21, J+28... : pour chaque semaine k, on calcule
    les 18 features de la semaine k (jours (k-1)*7 à k*7-1) et on les empile.
    À J+28 (chaque fin de mois), preparer_run / construire_ligne_90_features concatène
    les 4 semaines empilées pour construire les 90 features et le label.

    Args:
        state: État de simulation chargé
        run_id: Identifiant du run (ex: "000"). Si None, extrait de state.run_id.
        nb_mois: Nombre de mois à extraire. Si None, calcule depuis state.current_day.
        prediction_min: Si True, autorise 1 mois minimum (4 semaines) pour la prédiction.

    Returns:
        (df_features, df_labels) ou (None, None) en cas d'erreur
    """
    run_id = run_id or _run_id_numeric(state.run_id)
    total_days = state.current_day

    if nb_mois is None:
        if prediction_min and total_days >= 28:
            # Mode prédiction : extraire tous les mois complets (4 semaines chacun)
            nb_mois = total_days // (SEMAINES_PAR_MOIS * 7)
        else:
            nb_mois = compute_nb_mois_from_days(total_days)

    if prediction_min and total_days >= 28 and (nb_mois is None or nb_mois < 1):
        nb_mois = 1

    nb_semaines = nb_mois * SEMAINES_PAR_MOIS
    min_sem = 4 if prediction_min else SEMAINES_MIN
    if nb_semaines < min_sem:
        return None, None

    try:
        limites = CasualtyCalculator.load_limites_microzone_arrondissement()
    except FileNotFoundError:
        return None, None

    # StateCalculator sans CasualtyCalculator pour MVP (morts/blessés = 0)
    fc = StateCalculator(limites, casualty_calculator=None)
    lc = LabelCalculator()

    semaines = list(range(1, nb_semaines + 1))
    mois = list(range(1, nb_mois + 1))

    # Stack des features à J+7, J+14, J+21, J+28... : une semaine = 18 features (arrondissement, semaine, f1..f18)
    dfs_semaines: List[object] = []
    for semaine in semaines:
        df_week = fc.calculer_features_semaine(
            semaine,
            state.vectors_state,
            state.dynamic_state,
            events_state=state.events_state,
        )
        dfs_semaines.append(df_week)
    df_features = (
        pd.concat(dfs_semaines, ignore_index=True)
        if dfs_semaines
        else pd.DataFrame()
    )

    # Labels mensuels : à J+28, J+56... on construira les lignes ML en concaténant les 4 semaines (ml_service)
    df_labels = lc.calculer_labels_multiple_mois(mois, state.events_state)

    return df_features, df_labels


def extract_and_save_ml_data(
    state_path: Optional[Path] = None,
    state: Optional[SimulationState] = None,
    run_id: Optional[str] = None,
    prediction_min: bool = False,
) -> bool:
    """
    Charge un SimulationState, extrait features et labels, sauvegarde dans run_XXX/ml/.

    Args:
        state_path: Chemin vers simulation_state.pkl (si state est None)
        state: SimulationState déjà chargé (alternative à state_path)
        run_id: Identifiant du run (ex: "000")

    Returns:
        True si succès, False sinon
    """
    if state is None and state_path is None:
        return False

    if state is None:
        state_path = Path(state_path)
        if not state_path.exists():
            return False
        state = SimulationState.load(str(state_path))

    run_id = run_id or _run_id_numeric(state.run_id)
    df_features, df_labels = extract_features_and_labels(
        state, run_id=run_id, prediction_min=prediction_min
    )

    if df_features is None or df_labels is None:
        return False

    try:
        limites = CasualtyCalculator.load_limites_microzone_arrondissement()
    except FileNotFoundError:
        return False

    fc = StateCalculator(limites, casualty_calculator=None)
    lc = LabelCalculator()

    fc.save_features(df_features, run_id)
    lc.save_labels(df_labels, run_id)

    return True
