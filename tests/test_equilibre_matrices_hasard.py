"""
Story 2.4.3.2 : Test équilibre matrices/hasard et équité spatiale.

Vérifie que sur 200 jours de simulation, pour toutes les combinaisons
Scénario (Pessimiste, Standard, Optimiste) × Variabilité Locale (Faible, Moyenne, Forte) :
- Toutes les microzones ont au moins 1 jour avec incident (bénin, moyen ou grave).
- Toutes les microzones ont au moins 10 jours vides (aucun incident).

Métrique d'équilibre : coefficient de Gini sur le nombre total d'incidents par microzone.
- Formule : Gini = 1 - 2 * (AUC de la courbe de Lorenz) ; 0 = égalité parfaite, 1 = inégalité max.
- Seuil suggéré : Gini < 0.35 (dispersion modérée ; au-delà, risque d'effet de surenchère).
- Variance du nombre d'incidents par microzone est aussi calculée et loguée.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

# Racine projet
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

# Seed fixe pour reproductibilité (Story 2.4.3.2)
EQUILIBRE_TEST_SEED = 42
NUM_DAYS = 200
MIN_DAYS_WITH_INCIDENT = 1
MIN_DAYS_EMPTY = 10

# Combinaisons Scénario × Variabilité (9 au total)
SCENARIOS_UI = ["Pessimiste", "Standard", "Optimiste"]
VARIABILITES_UI = ["Faible", "Moyenne", "Forte"]

# Seuil métrique équilibre : Gini au-delà = alerte (dispersion élevée)
GINI_SEUIL_ALERTE = 0.35

logger = logging.getLogger(__name__)


def _stats_par_microzone(
    state: Any,
    microzone_ids: List[str],
    num_days: int,
) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int]]:
    """
    Calcule par microzone : jours avec incident, jours vides, total incidents.

    Returns:
        (days_with_incident, days_empty, total_incidents) chacun Dict[microzone_id, int]
    """
    days_with_incident: Dict[str, int] = {mz: 0 for mz in microzone_ids}
    total_incidents: Dict[str, int] = {mz: 0 for mz in microzone_ids}

    for mz_id in microzone_ids:
        for day in range(num_days):
            vectors = state.vectors_state.get_vectors_for_day(mz_id, day)
            day_total = sum(v.total() for v in vectors.values()) if vectors else 0
            if day_total >= 1:
                days_with_incident[mz_id] += 1
            total_incidents[mz_id] += day_total

    days_empty = {
        mz: num_days - days_with_incident[mz]
        for mz in microzone_ids
    }
    return days_with_incident, days_empty, total_incidents


def _gini_coefficient(values: List[float]) -> float:
    """
    Coefficient de Gini (0 = égalité, 1 = inégalité max).
    values : liste des valeurs (ex. nombre d'incidents par microzone).
    """
    if not values:
        return 0.0
    arr = sorted([float(v) for v in values if v is not None])
    n = len(arr)
    if n == 0:
        return 0.0
    cumsum = 0.0
    for i, x in enumerate(arr):
        cumsum += (2 * (i + 1) - n - 1) * x
    total = sum(arr)
    if total == 0:
        return 0.0
    return cumsum / (n * total)


def _variance_values(values: List[float]) -> float:
    """Variance des valeurs (population)."""
    if not values:
        return 0.0
    arr = [float(v) for v in values]
    n = len(arr)
    mean = sum(arr) / n
    return sum((x - mean) ** 2 for x in arr) / n


def _run_200_jours(
    scenario_ui: str,
    variabilite_ui: str,
    seed: int = EQUILIBRE_TEST_SEED,
) -> Tuple[Any, List[str], Dict[str, Any]]:
    """
    Exécute une simulation de 200 jours avec scénario et variabilité donnés.

    Returns:
        (state, microzone_ids, config_dict)
    """
    from src.core.config.config_validator import load_and_validate_config
    from src.core.utils.path_resolver import PathResolver
    from src.services.simulation_service import SimulationService, _get_microzone_ids

    path = PathResolver.config_file("config.yaml")
    config = load_and_validate_config(str(path))
    microzone_ids = _get_microzone_ids(config)
    svc = SimulationService(config=config, seed=seed)
    state = svc.run_one(
        days=NUM_DAYS,
        run_id="equilibre_test",
        scenario_ui=scenario_ui,
        variabilite_ui=variabilite_ui,
        output_dir=None,
        save_pickles=False,
        save_trace=False,
        debug_prints=False,
    )
    return state, microzone_ids, config.model_dump()


@pytest.mark.slow
@pytest.mark.parametrize("scenario_ui", SCENARIOS_UI)
@pytest.mark.parametrize("variabilite_ui", VARIABILITES_UI)
def test_equilibre_200_jours_equite_spatiale(
    scenario_ui: str,
    variabilite_ui: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Pour chaque combinaison (Scénario, Variabilité), sur 200 jours :
    - Toutes les microzones ont ≥ 1 jour avec incident.
    - Toutes les microzones ont ≥ 10 jours vides.
    - Métrique d'équilibre (Gini) calculée et loguée.
    """
    with caplog.at_level(logging.INFO):
        state, microzone_ids, _ = _run_200_jours(scenario_ui, variabilite_ui)
    days_with, days_empty, total_inc = _stats_par_microzone(
        state, microzone_ids, NUM_DAYS
    )

    # Critère 1 : au moins 1 jour avec incident par microzone
    microzones_sans_incident = [
        mz for mz in microzone_ids
        if days_with[mz] < MIN_DAYS_WITH_INCIDENT
    ]
    assert not microzones_sans_incident, (
        f"[{scenario_ui} / {variabilite_ui}] Microzones sans aucun jour avec incident "
        f"(attendu ≥ {MIN_DAYS_WITH_INCIDENT}) : {microzones_sans_incident}"
    )

    # Critère 2 : au moins 10 jours vides par microzone
    microzones_surchargees = [
        mz for mz in microzone_ids
        if days_empty[mz] < MIN_DAYS_EMPTY
    ]
    assert not microzones_surchargees, (
        f"[{scenario_ui} / {variabilite_ui}] Microzones avec moins de {MIN_DAYS_EMPTY} jours vides "
        f"(surcharge) : {microzones_surchargees} — jours vides : "
        f"{[(mz, days_empty[mz]) for mz in microzones_surchargees]}"
    )

    # Métrique d'équilibre
    totals = [total_inc[mz] for mz in microzone_ids]
    gini = _gini_coefficient(totals)
    variance = _variance_values(totals)
    ratio_max_min = (
        max(totals) / min(totals) if totals and min(totals) > 0
        else float("inf")
    )

    # Log rapport (reproductible)
    logger.info(
        "[%s / %s] 200 j — Gini=%.4f, Var=%.2f, max/min=%.2f, total_incidents=%d",
        scenario_ui, variabilite_ui, gini, variance, ratio_max_min, sum(totals),
    )
    if gini > GINI_SEUIL_ALERTE:
        logger.warning(
            "[%s / %s] Gini (%.4f) > seuil alerte (%.2f) — dispersion élevée, "
            "envisager ajustements (plancher λ, caps matrices, poids hasard).",
            scenario_ui, variabilite_ui, gini, GINI_SEUIL_ALERTE,
        )


def test_equilibre_rapport_metriques(caplog: pytest.LogCaptureFixture) -> None:
    """
    Exécute un run (Standard / Moyenne) et produit un rapport avec métriques
    par microzone et métrique d'équilibre globale (reproductible, seed fixe).
    """
    with caplog.at_level(logging.INFO):
        state, microzone_ids, _ = _run_200_jours("Standard", "Moyenne")
    days_with, days_empty, total_inc = _stats_par_microzone(
        state, microzone_ids, NUM_DAYS
    )

    totals = [total_inc[mz] for mz in microzone_ids]
    gini = _gini_coefficient(totals)
    variance = _variance_values(totals)

    logger.info(
        "Rapport équilibre (Standard / Moyenne, 200 j, seed=%s) : Gini=%.4f, Var=%.2f",
        EQUILIBRE_TEST_SEED, gini, variance,
    )
    # Résumé par microzone (échantillon : premières et extrêmes)
    sorted_by_total = sorted(microzone_ids, key=lambda mz: total_inc[mz])
    for mz in sorted_by_total[:3]:
        logger.info(
            "  mz %s : jours_avec_incident=%d, jours_vides=%d, total_incidents=%d",
            mz, days_with[mz], days_empty[mz], total_inc[mz],
        )
    for mz in sorted_by_total[-3:]:
        logger.info(
            "  mz %s : jours_avec_incident=%d, jours_vides=%d, total_incidents=%d",
            mz, days_with[mz], days_empty[mz], total_inc[mz],
        )

    # Assertions équité pour ce run
    assert all(days_with[mz] >= MIN_DAYS_WITH_INCIDENT for mz in microzone_ids), (
        "Au moins une microzone sans jour avec incident"
    )
    assert all(days_empty[mz] >= MIN_DAYS_EMPTY for mz in microzone_ids), (
        "Au moins une microzone avec moins de 10 jours vides"
    )
