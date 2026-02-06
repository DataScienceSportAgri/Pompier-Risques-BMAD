"""
Tests de vérification des fréquences simulées (calibration réaliste).
Vérifie que la génération produit approximativement les probabilités cibles
par jour et par microzone moyenne (70 % tout à 0, répartitions type × gravité).
"""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path

import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.generation.calibration import (
    TARGET_P_ALL_ZEROS,
    TARGET_PROBA_ACCIDENT,
    TARGET_PROBA_AGRESSION,
    TARGET_PROBA_INCENDIE,
)

ROOT = Path(__file__).resolve().parents[2]

# Tolérance relative ±50 % sur chaque cible : empirique dans [cible×0.5, cible×1.5]
# (borné à 1.0 pour les probas). Plus strict pour les petites probas (ex. 0,4 % → [0,2 % ; 0,6 %]).
TOL_RELATIVE = 0.5
# Accidents graves : valeur très faible, plus sensible aux modulations → tolérance 90 %
TOL_RELATIVE_ACCIDENT_GRAVE = 0.9
# Agressions graves : idem, tolérance élargie
TOL_RELATIVE_AGRESSION_GRAVE = 0.9

# Nombre de microzones et de jours pour le test de calibration
# Les microzones interagissent entre elles ; on fait 300 jours pour toutes les microzones
# et on calcule les fréquences comme moyenne sur toutes les observations (microzone × jour).
NUM_CALIB_MICROZONES = 10
NUM_CALIB_DAYS = 300
MIN_OBSERVATIONS = 100  # seuil minimum pour calculer les fréquences
# 5 seeds pour tester la variabilité : warning si 1 seed échoue, erreur si 2+ échouent
CALIB_SEEDS = [42, 123, 456, 789, 1024]
MIN_SEEDS_PASS = 4  # au moins 4 seeds sur 5 doivent passer


def _load_state_from_run(run_dir: Path):
    """Charge SimulationState depuis run_XXX/simulation_state.pkl."""
    pkl_path = run_dir / "simulation_state.pkl"
    if not pkl_path.exists():
        raise FileNotFoundError(f"État non trouvé: {pkl_path}")
    with open(pkl_path, "rb") as f:
        return pickle.load(f)


def _compute_empirical_frequencies(state) -> dict:
    """
    Calcule les fréquences empiriques à partir des vecteurs générés.
    Pool toutes les observations (toutes microzones × tous les jours) et retourne
    la moyenne : p_all_zeros, et par type (accident, agression, incendie)
    les probas (p_1_benin, p_1_moyen, p_1_grave).
    """
    vs = state.vectors_state
    microzones = vs.get_all_microzones()
    if not microzones:
        return {}

    count_all_zeros = 0
    n_obs = 0
    counts = {
        INCIDENT_TYPE_ACCIDENT: {"benin": 0, "moyen": 0, "grave": 0},
        INCIDENT_TYPE_AGRESSION: {"benin": 0, "moyen": 0, "grave": 0},
        INCIDENT_TYPE_INCENDIE: {"benin": 0, "moyen": 0, "grave": 0},
    }

    for mz in microzones:
        for jour in vs.get_all_days(mz):
            vecs = vs.get_vectors_for_day(mz, jour)
            acc = vecs.get(INCIDENT_TYPE_ACCIDENT)
            agr = vecs.get(INCIDENT_TYPE_AGRESSION)
            inc = vecs.get(INCIDENT_TYPE_INCENDIE)

            if acc is None or agr is None or inc is None:
                continue
            n_obs += 1

            all_zero = (
                acc.benin == 0 and acc.moyen == 0 and acc.grave == 0
                and agr.benin == 0 and agr.moyen == 0 and agr.grave == 0
                and inc.benin == 0 and inc.moyen == 0 and inc.grave == 0
            )
            if all_zero:
                count_all_zeros += 1

            # Exactement 1 incident de la gravité donnée (reste à 0)
            for type_key, vec in [
                (INCIDENT_TYPE_ACCIDENT, acc),
                (INCIDENT_TYPE_AGRESSION, agr),
                (INCIDENT_TYPE_INCENDIE, inc),
            ]:
                if vec.benin == 1 and vec.moyen == 0 and vec.grave == 0:
                    counts[type_key]["benin"] += 1
                if vec.benin == 0 and vec.moyen == 1 and vec.grave == 0:
                    counts[type_key]["moyen"] += 1
                if vec.benin == 0 and vec.moyen == 0 and vec.grave == 1:
                    counts[type_key]["grave"] += 1

    if n_obs < MIN_OBSERVATIONS:
        return {}
    p_all_zeros = count_all_zeros / n_obs
    freqs = {
        "p_all_zeros": p_all_zeros,
        "n_obs": n_obs,
        INCIDENT_TYPE_ACCIDENT: (
            counts[INCIDENT_TYPE_ACCIDENT]["benin"] / n_obs,
            counts[INCIDENT_TYPE_ACCIDENT]["moyen"] / n_obs,
            counts[INCIDENT_TYPE_ACCIDENT]["grave"] / n_obs,
        ),
        INCIDENT_TYPE_AGRESSION: (
            counts[INCIDENT_TYPE_AGRESSION]["benin"] / n_obs,
            counts[INCIDENT_TYPE_AGRESSION]["moyen"] / n_obs,
            counts[INCIDENT_TYPE_AGRESSION]["grave"] / n_obs,
        ),
        INCIDENT_TYPE_INCENDIE: (
            counts[INCIDENT_TYPE_INCENDIE]["benin"] / n_obs,
            counts[INCIDENT_TYPE_INCENDIE]["moyen"] / n_obs,
            counts[INCIDENT_TYPE_INCENDIE]["grave"] / n_obs,
        ),
    }
    return freqs


# Microzones factices pour le test de calibration (intensités injectées, pas de fichier).
# Plusieurs microzones pour que les interactions entre elles soient prises en compte ;
# les fréquences sont la moyenne sur toutes les observations (toutes microzones × tous les jours).
_MZ_CALIB_IDS = [f"MZ_CALIB_{i:02d}" for i in range(1, NUM_CALIB_MICROZONES + 1)]

# Matrices vides : pas de modulation, intensité ≈ base (calibration)
_EMPTY_MATRICES = {
    "matrices_intra_type": {},
    "matrices_inter_type": {},
    "matrices_voisin": {},
    "matrices_saisonnalite": {},
}


def _make_calibration_base_intensities():
    """Intensités de base calibration pour toutes les microzones (même valeur, sans fichier)."""
    from src.core.generation.calibration import (
        BASE_INTENSITY_ACCIDENT,
        BASE_INTENSITY_AGRESSION,
        BASE_INTENSITY_INCENDIE,
    )
    return {
        mz_id: {
            INCIDENT_TYPE_ACCIDENT: BASE_INTENSITY_ACCIDENT,
            INCIDENT_TYPE_AGRESSION: BASE_INTENSITY_AGRESSION,
            INCIDENT_TYPE_INCENDIE: BASE_INTENSITY_INCENDIE,
        }
        for mz_id in _MZ_CALIB_IDS
    }


def _accept(target: float, tol: float = TOL_RELATIVE) -> tuple[float, float]:
    """Bornes acceptables : cible × (1 ± tol), plafonnées à 1.0."""
    low = target * (1.0 - tol)
    high = min(1.0, target * (1.0 + tol))
    return (low, high)


def _get_tol(type_key: str, label: str) -> float:
    """Tolérance selon la cible (accident/agression grave = 90 %)."""
    if type_key == INCIDENT_TYPE_ACCIDENT and label == "grave":
        return TOL_RELATIVE_ACCIDENT_GRAVE
    if type_key == INCIDENT_TYPE_AGRESSION and label == "grave":
        return TOL_RELATIVE_AGRESSION_GRAVE
    return TOL_RELATIVE


@pytest.fixture(scope="module")
def calibration_freqs():
    """
    Lance 5 simulations de calibration (une par seed) : 10 microzones × 300 jours,
    matrices vides. Retourne une liste de 5 dicts de fréquences (un par seed).
    """
    from src.core.generation.generation_service import GenerationService
    from src.core.state.simulation_state import SimulationState

    base_intensities = _make_calibration_base_intensities()
    scenario_config = {"facteur_intensite": 1.0, "proba_crise": 0.1}
    all_freqs = []

    for seed in CALIB_SEEDS:
        state = SimulationState(run_id="calib_test", config={})
        state.dynamic_state.ensure_microzones(_MZ_CALIB_IDS)
        gen = GenerationService(
            microzone_ids=_MZ_CALIB_IDS,
            seed=seed,
            base_intensities=base_intensities,
            matrices=_EMPTY_MATRICES,
            scenario_config=scenario_config,
            variabilite_locale=0.5,
            debug_prints=False,
        )
        gen.generate_multiple_days(state, start_day=0, num_days=NUM_CALIB_DAYS)
        freqs = _compute_empirical_frequencies(state)
        all_freqs.append(freqs)

    return all_freqs


def _assert_seeds(calibration_freqs_list: list, check_fn, test_name: str) -> None:
    """
    Pour chaque seed, applique check_fn(freqs) -> (ok: bool, detail: str).
    - Si au moins MIN_SEEDS_PASS seeds passent : test OK.
    - Si exactement 1 seed échoue (4 passent) : warning.
    - Si 2+ seeds échouent : pytest.fail.
    """
    n_pass = 0
    failures = []
    for idx, freqs in enumerate(calibration_freqs_list):
        ok, detail = check_fn(freqs)
        if ok:
            n_pass += 1
        else:
            seed = CALIB_SEEDS[idx] if idx < len(CALIB_SEEDS) else idx
            failures.append((seed, detail))
    if n_pass < MIN_SEEDS_PASS:
        msg = (
            f"{test_name}: seeds passés {n_pass}/{len(CALIB_SEEDS)} "
            f"(attendu >= {MIN_SEEDS_PASS}). Échecs: {failures}"
        )
        pytest.fail(msg)
    if n_pass == MIN_SEEDS_PASS and failures:
        warnings.warn(
            f"{test_name}: une seed a échoué (seed {failures[0][0]}): {failures[0][1]}",
            UserWarning,
            stacklevel=2,
        )


# --- Mini-tests par cible : une assertion par test, 5 seeds, warning si 1 échoue, erreur si 2+ ---

@pytest.mark.slow
def test_calibration_has_enough_observations(calibration_freqs) -> None:
    """Vérifie qu'on a assez d'observations (microzones × jours) pour chaque seed."""
    def check(freqs):
        if not freqs:
            return False, "aucune observation"
        n_obs = freqs.get("n_obs", 0)
        if n_obs < MIN_OBSERVATIONS:
            return False, f"n_obs={n_obs} < {MIN_OBSERVATIONS}"
        return True, ""
    _assert_seeds(calibration_freqs, check, "test_calibration_has_enough_observations")


@pytest.mark.slow
def test_calibration_p_all_zeros(calibration_freqs) -> None:
    """P(tout à 0) : cible 70 %, tolérance ±50 %."""
    low, high = _accept(TARGET_P_ALL_ZEROS)

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        p = freqs["p_all_zeros"]
        if low <= p <= high:
            return True, ""
        return False, f"obtenu {p:.3f}, attendu [{low:.3f}, {high:.3f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_p_all_zeros")


@pytest.mark.slow
def test_calibration_accident_benin(calibration_freqs) -> None:
    """Accident bénin : cible 14 %, tolérance ±50 %."""
    target = TARGET_PROBA_ACCIDENT[0]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_ACCIDENT, "benin"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_ACCIDENT][0]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_accident_benin")


@pytest.mark.slow
def test_calibration_accident_moyen(calibration_freqs) -> None:
    """Accident moyen : cible 2.4 %, tolérance ±50 %."""
    target = TARGET_PROBA_ACCIDENT[1]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_ACCIDENT, "moyen"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_ACCIDENT][1]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_accident_moyen")


@pytest.mark.slow
def test_calibration_accident_grave(calibration_freqs) -> None:
    """Accident grave : cible 0.4 %, tolérance ±90 %."""
    target = TARGET_PROBA_ACCIDENT[2]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_ACCIDENT, "grave"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_ACCIDENT][2]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_accident_grave")


@pytest.mark.slow
def test_calibration_agression_benin(calibration_freqs) -> None:
    """Agression bénine : cible 9 %, tolérance ±50 %."""
    target = TARGET_PROBA_AGRESSION[0]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_AGRESSION, "benin"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_AGRESSION][0]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_agression_benin")


@pytest.mark.slow
def test_calibration_agression_moyen(calibration_freqs) -> None:
    """Agression moyenne : cible 2 %, tolérance ±50 %."""
    target = TARGET_PROBA_AGRESSION[1]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_AGRESSION, "moyen"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_AGRESSION][1]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_agression_moyen")


@pytest.mark.slow
def test_calibration_agression_grave(calibration_freqs) -> None:
    """Agression grave : cible 0.3 %, tolérance ±90 %."""
    target = TARGET_PROBA_AGRESSION[2]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_AGRESSION, "grave"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_AGRESSION][2]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_agression_grave")


@pytest.mark.slow
def test_calibration_incendie_benin(calibration_freqs) -> None:
    """Incendie bénin : cible 6 %, tolérance ±50 %."""
    target = TARGET_PROBA_INCENDIE[0]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_INCENDIE, "benin"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_INCENDIE][0]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_incendie_benin")


@pytest.mark.slow
def test_calibration_incendie_moyen(calibration_freqs) -> None:
    """Incendie moyen : cible 1.8 %, tolérance ±50 %."""
    target = TARGET_PROBA_INCENDIE[1]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_INCENDIE, "moyen"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_INCENDIE][1]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_incendie_moyen")


@pytest.mark.slow
def test_calibration_incendie_grave(calibration_freqs) -> None:
    """Incendie grave : cible 0.2 %, tolérance ±50 %."""
    target = TARGET_PROBA_INCENDIE[2]
    low, high = _accept(target, tol=_get_tol(INCIDENT_TYPE_INCENDIE, "grave"))

    def check(freqs):
        if not freqs or freqs.get("n_obs", 0) < MIN_OBSERVATIONS:
            return False, "pas assez d'observations"
        emp = freqs[INCIDENT_TYPE_INCENDIE][2]
        if low <= emp <= high:
            return True, ""
        return False, f"obtenu {emp:.4f}, attendu [{low:.4f}, {high:.4f}]"
    _assert_seeds(calibration_freqs, check, "test_calibration_incendie_grave")
