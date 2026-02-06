# Évolution J→J+1 des variables d'état (Story 1.4.4.2)

from typing import Any, Dict, List, Optional

import numpy as np

from .alcool_evolution import evoluer_incidents_alcool_J1
from .nuit_evolution import evoluer_incidents_nuit_J1
from .trafic_evolution import evoluer_trafic_J1

__all__ = [
    "evoluer_trafic_J1",
    "evoluer_incidents_nuit_J1",
    "evoluer_incidents_alcool_J1",
    "evoluer_dynamic_state",
]


def evoluer_dynamic_state(
    state: "DynamicState",
    incidents_J: Dict[str, Dict[str, Dict[str, int]]],
    matrices_trafic: Dict[str, Dict[str, Any]],
    matrices_inter_type: Dict[str, Dict[str, Dict[str, List[float]]]],
    microzone_ids: List[str],
    saison: str,
    *,
    rng: Optional[np.random.Generator] = None,
) -> None:
    """
    Fait évoluer state (trafic, incidents_nuit, incidents_alcool) J→J+1.

    Modifie state en place.
    """
    if rng is None:
        rng = np.random.default_rng()
    state.trafic.update(
        evoluer_trafic_J1(
            state.trafic,
            incidents_J,
            matrices_trafic,
            microzone_ids,
            rng=rng,
        )
    )
    state.incidents_nuit.update(
        evoluer_incidents_nuit_J1(
            state.incidents_nuit,
            incidents_J,
            matrices_inter_type,
            microzone_ids,
            saison,
            rng=rng,
        )
    )
    state.incidents_alcool.update(
        evoluer_incidents_alcool_J1(
            state.incidents_alcool,
            incidents_J,
            matrices_inter_type,
            microzone_ids,
            saison,
            rng=rng,
        )
    )
