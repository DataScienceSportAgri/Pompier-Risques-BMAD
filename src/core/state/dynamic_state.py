"""
Variables d'état dynamiques J→J+1 (Story 1.4.4.2).

Stockées dans SimulationState.dynamic_state. Structure :
- trafic: niveau de congestion par microzone [0, 1]
- incidents_nuit: nombre d'incidents la nuit par microzone et type
- incidents_alcool: nombre d'incidents alcool par microzone et type
"""

from typing import Dict, List


TYPES_INCIDENT = ("agressions", "incendies", "accidents")


def _default_incidents_par_type() -> Dict[str, int]:
    return {t: 0 for t in TYPES_INCIDENT}


class DynamicState:
    """
    État dynamique évoluant J→J+1.

    - trafic: Dict[microzone_id, float] — niveau congestion 0–1
    - incidents_nuit: Dict[microzone_id, Dict[type_incident, int]]
    - incidents_alcool: Dict[microzone_id, Dict[type_incident, int]]
    """

    __slots__ = ("trafic", "incidents_nuit", "incidents_alcool")

    def __init__(
        self,
        trafic: Dict[str, float] | None = None,
        incidents_nuit: Dict[str, Dict[str, int]] | None = None,
        incidents_alcool: Dict[str, Dict[str, int]] | None = None,
    ):
        self.trafic = trafic if trafic is not None else {}
        self.incidents_nuit = incidents_nuit if incidents_nuit is not None else {}
        self.incidents_alcool = incidents_alcool if incidents_alcool is not None else {}

    def ensure_microzones(self, microzone_ids: List[str]) -> None:
        """Remplit les entrées manquantes pour chaque microzone (trafic 0, incidents 0)."""
        for mz in microzone_ids:
            if mz not in self.trafic:
                self.trafic[mz] = 0.0
            if mz not in self.incidents_nuit:
                self.incidents_nuit[mz] = _default_incidents_par_type().copy()
            if mz not in self.incidents_alcool:
                self.incidents_alcool[mz] = _default_incidents_par_type().copy()

    def copy(self) -> "DynamicState":
        """Copie shallow des dicts (les sous-dicts sont partagés)."""
        return DynamicState(
            trafic=dict(self.trafic),
            incidents_nuit={mz: dict(v) for mz, v in self.incidents_nuit.items()},
            incidents_alcool={mz: dict(v) for mz, v in self.incidents_alcool.items()},
        )
