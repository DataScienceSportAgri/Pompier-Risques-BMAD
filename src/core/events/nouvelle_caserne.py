"""
Classe pour les événements de nouvelle caserne.
Story 2.1.1 - Infrastructure de base
"""

from .positive_event import PositiveEvent


class NouvelleCaserne(PositiveEvent):
    """Événement positif : ouverture d'une nouvelle caserne de pompiers."""
    
    def get_type(self) -> str:
        """Retourne le type d'événement."""
        return "nouvelle_caserne"
    
    def __init__(
        self,
        event_id: str,
        jour: int,
        arrondissement: int,
        impact_reduction: float = 0.15
    ):
        """
        Initialise un événement de nouvelle caserne.
        
        Args:
            event_id: Identifiant unique
            jour: Jour de déclenchement
            arrondissement: Numéro arrondissement (1-20)
            impact_reduction: Réduction d'impact (défaut: 0.15 = 15%)
        """
        super().__init__(
            event_id=event_id,
            jour=jour,
            arrondissement=arrondissement,
            impact_reduction=impact_reduction
        )
