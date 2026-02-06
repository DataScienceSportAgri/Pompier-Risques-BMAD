"""
Classe de base abstraite pour les événements positifs.
Story 2.1.1 - Infrastructure de base
"""

from typing import Dict

from .event import Event


class PositiveEvent(Event):
    """
    Classe de base abstraite pour les événements positifs.
    
    Un événement positif représente une amélioration (fin travaux, nouvelle caserne, etc.)
    qui peut réduire les risques d'incidents.
    """
    
    def __init__(
        self,
        event_id: str,
        jour: int,
        arrondissement: int,
        impact_reduction: float = 0.0
    ):
        """
        Initialise un événement positif.
        
        Args:
            event_id: Identifiant unique de l'événement
            jour: Jour de déclenchement
            arrondissement: Numéro de l'arrondissement (1-20)
            impact_reduction: Réduction d'impact en pourcentage (0.0-1.0)
        """
        super().__init__(event_id, jour, arrondissement)
        self.impact_reduction = impact_reduction
    
    def to_dict(self) -> Dict:
        """Convertit l'événement positif en dictionnaire."""
        base_dict = super().to_dict()
        base_dict['impact_reduction'] = self.impact_reduction
        return base_dict
