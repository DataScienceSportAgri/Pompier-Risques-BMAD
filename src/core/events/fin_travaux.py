"""
Classe pour les événements de fin de travaux.
Story 2.1.1 - Infrastructure de base
"""

from .positive_event import PositiveEvent


class FinTravaux(PositiveEvent):
    """Événement positif : fin de travaux d'infrastructure."""
    
    def get_type(self) -> str:
        """Retourne le type d'événement."""
        return "fin_travaux"
    
    def __init__(
        self,
        event_id: str,
        jour: int,
        arrondissement: int,
        impact_reduction: float = 0.1
    ):
        """
        Initialise un événement de fin de travaux.
        
        Args:
            event_id: Identifiant unique
            jour: Jour de déclenchement
            arrondissement: Numéro arrondissement (1-20)
            impact_reduction: Réduction d'impact (défaut: 0.1 = 10%)
        """
        super().__init__(
            event_id=event_id,
            jour=jour,
            arrondissement=arrondissement,
            impact_reduction=impact_reduction
        )
