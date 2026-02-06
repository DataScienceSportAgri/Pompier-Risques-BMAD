"""
Évolution du trafic J→J+1 (Story 1.4.4.2).

- Mémoire 60–70% (facteur depuis matrices trafic).
- Influence incidents : accidents ↑ trafic, incendies moyen/grave ↓.
- Aléatoire 30–40%. Clamp [0, 1].
"""

from typing import Any, Dict, List, Optional

import numpy as np


def evoluer_trafic_J1(
    trafic_J: Dict[str, float],
    incidents_J: Dict[str, Dict[str, Dict[str, int]]],
    matrices_trafic: Dict[str, Dict[str, Any]],
    microzone_ids: List[str],
    *,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, float]:
    """
    Évolution du niveau de trafic (congestion) par microzone J→J+1.

    - Mémoire : facteur_memoire (60–70%) × trafic_J.
    - Aléatoire : (1 - facteur_memoire) × U(0,1).
    - Influence : accidents +delta, incendies moyen/grave -delta.
    - Clamp [0, 1].

    incidents_J[mz][type][gravite] = effectif.
    """
    if rng is None:
        rng = np.random.default_rng()
    out: Dict[str, float] = {}
    for mz in microzone_ids:
        mat = matrices_trafic.get(mz, {})
        mem = float(mat.get("facteur_memoire", 0.65))
        mem = max(0.0, min(1.0, mem))
        prev = trafic_J.get(mz, 0.0)

        # Mémoire + aléatoire (30–40%)
        x = mem * prev + (1.0 - mem) * float(rng.uniform(0.0, 1.0))

        # Influence incidents
        by_type = incidents_J.get(mz, {})
        acc = sum(by_type.get("accidents", {}).values()) or 0
        inc = by_type.get("incendies", {})
        fire_mg = (inc.get("moyen", 0) or 0) + (inc.get("grave", 0) or 0)
        if acc > 0:
            x += 0.05
        if fire_mg > 0:
            x -= 0.03

        x = max(0.0, min(1.0, x))
        out[mz] = x
    return out
