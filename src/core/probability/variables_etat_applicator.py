"""
Intégration des variables d'état dynamiques aux probabilités (Story 1.4.4.4).

- Trafic > 0.7 → +15% accidents et agressions.
- Incidents nuit > seuil (2/jour/microzone) → +10%.
- Incidents alcool > seuil (2/jour/microzone) → +8%.
"""

from typing import Dict, Tuple

from .matrix_applicator import _vec_clamp

TYPES = ("agressions", "incendies", "accidents")

SEUIL_TRAFIC_HAUT = 0.7
EFFET_TRAFIC = 0.15
SEUIL_INCIDENTS_NUIT = 2   # 2 événements/jour/microzone
SEUIL_INCIDENTS_ALCOOL = 2 # 2 événements/jour/microzone (seuil défini story 1.4.4.4)
EFFET_NUIT = 0.10
EFFET_ALCOOL = 0.08


def _total_incidents_mz(incidents_par_type: Dict[str, int]) -> int:
    return sum(incidents_par_type.get(t, 0) for t in TYPES)


def apply_variables_etat(
    prob: Tuple[float, float, float],
    mz: str,
    type_incident: str,
    trafic: Dict[str, float],
    incidents_nuit: Dict[str, Dict[str, int]],
    incidents_alcool: Dict[str, Dict[str, int]],
) -> Tuple[float, float, float]:
    """
    Applique trafic, incidents nuit et alcool aux probabilités modulées.

    - Trafic > 0.7 : +15% pour agressions et accidents.
    - Incidents nuit > 2 (total mz) : +10% pour tous les types.
    - Incidents alcool > 2 (total mz) : +8% pour tous les types.
    """
    f = 1.0
    t = trafic.get(mz, 0.0)
    if type_incident in ("agressions", "accidents") and t > SEUIL_TRAFIC_HAUT:
        f *= 1.0 + EFFET_TRAFIC
    nuit_mz = incidents_nuit.get(mz, {})
    if _total_incidents_mz(nuit_mz) > SEUIL_INCIDENTS_NUIT:
        f *= 1.0 + EFFET_NUIT
    alcool_mz = incidents_alcool.get(mz, {})
    if _total_incidents_mz(alcool_mz) > SEUIL_INCIDENTS_ALCOOL:
        f *= 1.0 + EFFET_ALCOOL
    out = (prob[0] * f, prob[1] * f, prob[2] * f)
    return _vec_clamp(out)
