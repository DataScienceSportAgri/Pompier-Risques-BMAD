"""
SimulationState (Story 2.1.2). Structure refactorée v2 avec domaines spécialisés.

Contient :
- dynamic_state (évolution J→J+1) - Story 1.4.4.2
- patterns_actifs (Story 1.4.4.5)
- realaléatoirisation_state (Story 2.4.3.4) — patterns de réaléatoirisation par arrondissement
- Domaines spécialisés (Story 2.1.2) :
  - vectors_state : Vecteurs journaliers par microzone
  - events_state : Événements journaliers (graves et positifs)
  - casualties_state : Morts et blessés graves (agrégés par semaine)
  - regime_state : Régimes cachés par microzone
"""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .casualties_state import CasualtiesState
from .dynamic_state import DynamicState
from .events_state import EventsState
from .regime_state import RegimeState
from .vectors_state import VectorsState

if TYPE_CHECKING:
    from .realaléatoirisation_state import RealaléatoirisationState


class SimulationState:
    """
    État global de la simulation (Aggregate Root).
    
    Contient UNIQUEMENT les données journalières.
    Features (hebdomadaires) et labels (mensuels) sont calculés et stockés séparément.
    """

    def __init__(self, run_id: str, config: Dict[str, Any]):
        """
        Initialise un état de simulation.
        
        Args:
            run_id: Identifiant unique de la simulation
            config: Configuration de la simulation
        """
        self.run_id = run_id
        self.config = config
        self.current_day: int = 0
        
        # État dynamique (évolution J→J+1) - Story 1.4.4.2
        self.dynamic_state = DynamicState()
        
        # Patterns actifs - Story 1.4.4.5
        self.patterns_actifs: Dict[str, List[dict]] = {}
        
        # Réaléatoirisation (Story 2.4.3.4) — patterns par arrondissement, déterminés à l'avance
        self.realaléatoirisation_state: Optional["RealaléatoirisationState"] = None
        
        # Domaines spécialisés (composition) - DONNÉES JOURNALIÈRES UNIQUEMENT
        self.vectors_state = VectorsState()          # Vecteurs journaliers
        self.events_state = EventsState()            # Événements journaliers
        self.casualties_state = CasualtiesState()     # Casualties (agrégés par semaine)
        self.regime_state = RegimeState()            # Régimes par microzone
    
    def save(self, path: str) -> None:
        """
        Sauvegarde l'état en pickle (format standardisé).
        
        Args:
            path: Chemin du fichier de sauvegarde
        
        Raises:
            IOError: Si la sauvegarde échoue
        """
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'wb') as f:
                pickle.dump(self, f)
        except Exception as e:
            raise IOError(f"Erreur lors de la sauvegarde de l'état: {e}") from e
    
    @classmethod
    def load(cls, path: str) -> 'SimulationState':
        """
        Charge un état depuis un fichier pickle.
        
        Args:
            path: Chemin du fichier de sauvegarde
        
        Returns:
            Instance de SimulationState chargée
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            IOError: Si le chargement échoue
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Fichier de sauvegarde introuvable: {path}")
        
        try:
            with open(path, 'rb') as f:
                state = pickle.load(f)
                if not isinstance(state, SimulationState):
                    raise ValueError(
                        f"Le fichier ne contient pas un SimulationState: {type(state)}"
                    )
                return state
        except Exception as e:
            raise IOError(f"Erreur lors du chargement de l'état: {e}") from e
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'état en dictionnaire (pour sérialisation JSON alternative).
        
        Returns:
            Dictionnaire représentant l'état
        """
        return {
            'run_id': self.run_id,
            'config': self.config,
            'current_day': self.current_day,
            'vectors_state': self.vectors_state.to_dict(),
            'events_state': self.events_state.to_dict(),
            'casualties_state': self.casualties_state.to_dict(),
            'regime_state': self.regime_state.to_dict(),
            'patterns_actifs': self.patterns_actifs,
            'realaléatoirisation_state': self.realaléatoirisation_state.to_dict() if self.realaléatoirisation_state else None,
            # Note: dynamic_state n'a pas de to_dict() pour l'instant
        }
    
    def __repr__(self) -> str:
        """Représentation string de l'état."""
        return (
            f"SimulationState(run_id={self.run_id}, "
            f"day={self.current_day}, "
            f"vectors={self.vectors_state}, "
            f"events={self.events_state}, "
            f"casualties={self.casualties_state}, "
            f"regimes={self.regime_state})"
        )
