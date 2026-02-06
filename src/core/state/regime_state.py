"""
RegimeState : Gestion des régimes cachés par microzone.
Story 2.1.2 - Structure SimulationState avec domaines spécialisés

Régimes possibles : "Stable", "Détérioration", "Crise"
"""

from typing import Dict, List, Optional

# Régimes possibles
REGIME_STABLE = "Stable"
REGIME_DETERIORATION = "Détérioration"
REGIME_CRISE = "Crise"

REGIMES_VALIDES = {REGIME_STABLE, REGIME_DETERIORATION, REGIME_CRISE}


class RegimeState:
    """
    Gestion des régimes cachés par microzone.
    
    Structure : Dict[microzone_id, regime]
    Régimes : "Stable", "Détérioration", "Crise"
    """
    
    def __init__(self):
        """Initialise un état vide de régimes."""
        # Structure : Dict[microzone_id, str]
        self._regimes: Dict[str, str] = {}
    
    def set_regime(self, microzone_id: str, regime: str) -> None:
        """
        Définit le régime d'une microzone.
        
        Args:
            microzone_id: Identifiant de la microzone
            regime: Régime ("Stable", "Détérioration", "Crise")
        
        Raises:
            ValueError: Si le régime n'est pas valide
        """
        if regime not in REGIMES_VALIDES:
            raise ValueError(
                f"Régime invalide: {regime}. "
                f"Régimes valides: {REGIMES_VALIDES}"
            )
        self._regimes[microzone_id] = regime
    
    def get_regime(self, microzone_id: str) -> Optional[str]:
        """
        Récupère le régime d'une microzone.
        
        Args:
            microzone_id: Identifiant de la microzone
        
        Returns:
            Régime ou None si non défini
        """
        return self._regimes.get(microzone_id)
    
    def get_regime_or_default(self, microzone_id: str, default: str = REGIME_STABLE) -> str:
        """
        Récupère le régime d'une microzone avec valeur par défaut.
        
        Args:
            microzone_id: Identifiant de la microzone
            default: Régime par défaut si non défini
        
        Returns:
            Régime (toujours défini)
        """
        return self._regimes.get(microzone_id, default)
    
    def get_microzones_by_regime(self, regime: str) -> List[str]:
        """
        Récupère toutes les microzones ayant un régime donné.
        
        Args:
            regime: Régime recherché
        
        Returns:
            Liste des identifiants de microzones
        """
        if regime not in REGIMES_VALIDES:
            return []
        
        return [
            mz_id for mz_id, reg in self._regimes.items()
            if reg == regime
        ]
    
    def get_all_microzones(self) -> List[str]:
        """Retourne la liste de toutes les microzones avec régime défini."""
        return list(self._regimes.keys())
    
    def clear_microzone(self, microzone_id: str) -> None:
        """
        Supprime le régime d'une microzone.
        
        Args:
            microzone_id: Identifiant de la microzone
        """
        if microzone_id in self._regimes:
            del self._regimes[microzone_id]
    
    def to_dict(self) -> Dict:
        """
        Convertit l'état en dictionnaire (pour sérialisation).
        
        Returns:
            Dictionnaire représentant l'état
        """
        return self._regimes.copy()
    
    def __repr__(self) -> str:
        """Représentation string de l'état."""
        nb_microzones = len(self._regimes)
        if nb_microzones == 0:
            return "RegimeState(empty)"
        
        # Compter par régime
        counts = {}
        for regime in self._regimes.values():
            counts[regime] = counts.get(regime, 0) + 1
        
        return f"RegimeState(microzones={nb_microzones}, {counts})"
