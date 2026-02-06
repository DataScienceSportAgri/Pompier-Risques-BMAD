"""
Évolution des incidents alcool J→J+1 (Story 1.4.4.2).

- Mémoire 60–70 %, corrélations inter-type, saisonnalité (+50 % accidents été).
- Calibration par probabilité de base : raw (matrices + temporalités) modulé en %
  pour atteindre ~45 % accidents, ~65 % incendies, ~70 % agressions.
- Valeur toujours ≤ total, la plupart du temps strictement inférieure.
"""

from typing import Any, Dict, List, Optional

import numpy as np

from .nuit_evolution import (
    TYPES,
    _calibrer_vers_proportion,
    _count_by_type,
    _inter_influence,
)

MEMOIRE_DEFAULT = 0.65
SAISON_ETE_FACTEUR_ALCOOL_ACCIDENTS = 1.5

# Probabilités de base cibles par type (calibration)
PROPORTIONS_ALCOOL = {
    "accidents": 0.45,
    "incendies": 0.65,
    "agressions": 0.70,
}


def evoluer_incidents_alcool_J1(
    incidents_alcool_J: Dict[str, Dict[str, int]],
    incidents_J: Dict[str, Dict[str, Dict[str, int]]],
    matrices_inter_type: Dict[str, Dict[str, Dict[str, List[float]]]],
    microzone_ids: List[str],
    saison: str,
    *,
    memoire: float = MEMOIRE_DEFAULT,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, Dict[str, int]]:
    """
    Évolution incidents alcool avec mémoire, corrélations, saisonnalité été.
    Calibration : proba de base par type pour atteindre ~45/65/70 % du total.
    """
    if rng is None:
        rng = np.random.default_rng()
    out: Dict[str, Dict[str, int]] = {}
    mem = max(0.0, min(1.0, memoire))

    for mz in microzone_ids:
        counts = _count_by_type(incidents_J, mz)
        out[mz] = {}
        for t in TYPES:
            total = counts.get(t, 0)
            if total == 0:
                out[mz][t] = 0
                continue
            # Évolution : mémoire + corrélations inter-type + saisonnalité été (accidents)
            prev = (incidents_alcool_J.get(mz) or {}).get(t, 0)
            corr = _inter_influence(mz, t, counts, matrices_inter_type)
            corr_scaled = min(max(0.0, corr), 10.0) * 0.3
            mu = mem * prev + (1.0 - mem) * corr_scaled
            if t == "accidents" and saison == "ete":
                mu *= SAISON_ETE_FACTEUR_ALCOOL_ACCIDENTS
            noise = rng.normal(0, 0.5)
            raw = max(0.0, mu + noise)
            # Calibration vers proportion cible
            p_base = PROPORTIONS_ALCOOL.get(t, 0.6)
            val = _calibrer_vers_proportion(raw, total, p_base, rng)
            out[mz][t] = min(val, total)
    return out
