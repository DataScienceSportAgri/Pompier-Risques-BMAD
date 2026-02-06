"""
Calcul des probabilités d'incidents J+1 (Story 1.4.4.3, 1.4.4.4, 1.4.4.6).

Ordre : matrices fixes → variables d'état (optionnel) → patterns (optionnel).
"""

from typing import Any, Dict, List, Optional, Tuple

from .matrix_applicator import (
    apply_intra_type,
    apply_inter_type,
    apply_voisin,
    apply_saisonnalite,
    _clamp,
)
from .variables_etat_applicator import apply_variables_etat
from .pattern_applicator import apply_patterns

TYPES = ("agressions", "incendies", "accidents")


def calculer_probabilite_incidents_J1(
    prob_base: Dict[str, Dict[str, float]],
    incidents_J: Dict[str, Dict[str, Tuple[int, int, int]]],
    matrices_intra_type: Dict[str, Dict[str, Any]],
    matrices_inter_type: Dict[str, Dict[str, Dict[str, List[float]]]],
    matrices_voisin: Dict[str, Any],
    matrices_saisonnalite: Dict[str, Dict[str, Dict[str, float]]],
    microzone_ids: List[str],
    saison: str,
    *,
    dynamic_state: Optional[Any] = None,
    patterns_actifs: Optional[Dict[str, List[dict]]] = None,
) -> Dict[str, Dict[str, Tuple[float, float, float]]]:
    """
    Probabilités J→J+1 : matrices fixes → variables d'état → patterns.

    - prob_base[mz][type] : probabilité de base (scalaire).
    - incidents_J[mz][type] : (n_benin, n_moyen, n_grave) pour état actuel.
    - saison : "hiver" | "intersaison" | "ete".
    - dynamic_state : optionnel. Trafic, incidents nuit, alcool (Story 1.4.4.4).
    - patterns_actifs : optionnel. Dict[mz, List[Pattern]] (Story 1.4.4.5).
      Application 7j/60j sur agressions uniquement (Story 1.4.4.6).
    - Retour : prob_finales[mz][type] = (p_benin, p_moyen, p_grave) dans [0, 1].
    """
    pat = patterns_actifs if patterns_actifs is not None else {}
    out: Dict[str, Dict[str, Tuple[float, float, float]]] = {}
    for mz in microzone_ids:
        out[mz] = {}
        inc_mz = incidents_J.get(mz, {})
        intra_mz = matrices_intra_type.get(mz, {})
        for t in TYPES:
            pb = prob_base.get(mz, {}).get(t, 0.0)
            inc = inc_mz.get(t, (0, 0, 0))
            mat = intra_mz.get(t)
            if mat is None:
                p = (_clamp(pb), 0.0, 0.0)
            else:
                p = apply_intra_type(pb, inc, mat)
            p = apply_inter_type(p, incidents_J, matrices_inter_type, mz, t)
            p = apply_voisin(p, incidents_J, matrices_voisin, mz)
            p = apply_saisonnalite(p, matrices_saisonnalite, mz, t, saison)
            if dynamic_state is not None:
                p = apply_variables_etat(
                    p, mz, t,
                    dynamic_state.trafic,
                    dynamic_state.incidents_nuit,
                    dynamic_state.incidents_alcool,
                )
            p = apply_patterns(p, mz, t, pat)
            out[mz][t] = p
    return out
