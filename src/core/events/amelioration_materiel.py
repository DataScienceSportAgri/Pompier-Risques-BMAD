"""
Classe pour les événements d'amélioration de matériel.
Story 2.1.1 - Infrastructure de base
"""

from .positive_event import PositiveEvent


class AmeliorationMateriel(PositiveEvent):
    """Événement positif : amélioration du matériel des pompiers."""
    
    def get_type(self) -> str:
        """Retourne le type d'événement."""
        return "amelioration_materiel"
    
    def __init__(
        self,
        event_id: str,
        jour: int,
        arrondissement: int,
        impact_reduction: float = 0.05
    ):
        """
        Initialise un événement d'amélioration de matériel.
        
        Args:
            event_id: Identifiant unique
            jour: Jour de déclenchement
            arrondissement: Numéro arrondissement (1-20)
            impact_reduction: Réduction d'impact (défaut: 0.05 = 5%)
        """
        super().__init__(
            event_id=event_id,
            jour=jour,
            arrondissement=arrondissement,
            impact_reduction=impact_reduction
        )
