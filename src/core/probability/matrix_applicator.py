"""
Application des matrices fixes aux probabilités (Story 1.4.4.3).

Ordre : intra-type → inter-type → voisin → saisonnalité.
"""

from typing import Any, Dict, List, Tuple

import numpy as np

TYPES = ("agressions", "incendies", "accidents")
GRAVITES = (0, 1, 2)  # benin, moyen, grave
POIDS_VOISIN = (0.2, 0.5, 1.0)  # benin, moyen, grave
SEUIL_VOISINS = 5
EFFET_VOISIN = 0.1


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _vec_clamp(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return tuple(_clamp(x) for x in v)


def _dominant_row(n: Tuple[int, int, int]) -> int:
    """Indice de la gravité dominante (0=benin, 1=moyen, 2=grave). Si tout à 0 → 0."""
    if sum(n) == 0:
        return 0
    return int(np.argmax(n))


def apply_intra_type(
    prob_base: float,
    incidents: Tuple[int, int, int],
    matrice: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Transition gravité : prob_new = prob_base × ligne de la matrice.
    Ligne = gravité dominante dans incidents (bénin, moyen, grave).
    """
    row = _dominant_row(incidents)
    row = min(max(row, 0), 2)
    line = matrice[row, :]
    out = (float(prob_base * line[0]), float(prob_base * line[1]), float(prob_base * line[2]))
    return _vec_clamp(out)


def apply_inter_type(
    prob_intra: Tuple[float, float, float],
    incidents_J: Dict[str, Dict[str, Tuple[int, int, int]]],
    matrices_inter: Dict[str, Dict[str, Dict[str, List[float]]]],
    mz: str,
    type_cible: str,
) -> Tuple[float, float, float]:
    """
    Influence croisée : on ajoute des deltas depuis les autres types.
    influence[type_cible][type_source] = [inf_b, inf_m, inf_g].
    """
    inter = matrices_inter.get(mz, {})
    by_cible = inter.get(type_cible, {})
    delta = [0.0, 0.0, 0.0]
    inc_mz = incidents_J.get(mz, {})
    for type_source in TYPES:
        if type_source == type_cible:
            continue
        coefs = by_cible.get(type_source)
        if not coefs:
            continue
        n = inc_mz.get(type_source, (0, 0, 0))
        total = sum(n)
        cap = min(total, 3)
        for g in range(3):
            delta[g] += (coefs[g] if g < len(coefs) else 0.0) * cap
    out = (
        _clamp(prob_intra[0] + delta[0]),
        _clamp(prob_intra[1] + delta[1]),
        _clamp(prob_intra[2] + delta[2]),
    )
    return out


def apply_voisin(
    prob_inter: Tuple[float, float, float],
    incidents_J: Dict[str, Dict[str, Tuple[int, int, int]]],
    matrices_voisin: Dict[str, Any],
    mz: str,
) -> Tuple[float, float, float]:
    """
    Effet spatial : si >5 incidents (pondérés) dans les 8 voisins → +0.1.
    Pondération : Grave ×1.0, moyen ×0.5, bénin ×0.2.
    """
    voisin_data = matrices_voisin.get(mz, {})
    voisins = voisin_data.get("voisins", [])
    seuil = voisin_data.get("seuil_activation", SEUIL_VOISINS)
    weighted = 0.0
    for v in voisins:
        inc = incidents_J.get(v, {})
        for t in TYPES:
            n = inc.get(t, (0, 0, 0))
            for g in range(3):
                weighted += (n[g] if g < len(n) else 0) * POIDS_VOISIN[g]
    effet = EFFET_VOISIN if weighted > seuil else 0.0
    f = 1.0 + effet
    out = (prob_inter[0] * f, prob_inter[1] * f, prob_inter[2] * f)
    return _vec_clamp(out)


def apply_saisonnalite(
    prob_voisin: Tuple[float, float, float],
    matrices_saison: Dict[str, Dict[str, Dict[str, float]]],
    mz: str,
    type_incident: str,
    saison: str,
) -> Tuple[float, float, float]:
    """Multiplication par le facteur saisonnier (hiver, intersaison, ete)."""
    s = matrices_saison.get(mz, {}).get(type_incident, {}).get(saison, 1.0)
    out = (prob_voisin[0] * s, prob_voisin[1] * s, prob_voisin[2] * s)
    return _vec_clamp(out)
