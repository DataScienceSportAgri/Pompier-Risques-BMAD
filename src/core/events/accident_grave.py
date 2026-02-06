"""
Classe pour les accidents graves.
Story 2.1.1 - Infrastructure de base
"""

from typing import Dict, Optional

from .event_grave import EventGrave


class AccidentGrave(EventGrave):
    """Accident grave (incident majeur de type accident)."""
    
    def get_type(self) -> str:
        """Retourne le type d'événement."""
        return "accident_grave"
    
    def __init__(
        self,
        event_id: str,
        jour: int,
        arrondissement: int,
        duration: int,
        casualties_base: int = 0,
        characteristics: Optional[Dict[str, float]] = None
    ):
        """
        Initialise un accident grave.
        
        Args:
            event_id: Identifiant unique
            jour: Jour de déclenchement
            arrondissement: Numéro arrondissement (1-20)
            duration: Durée en jours
            casualties_base: Morts de base
            characteristics: Caractéristiques probabilistes
        """
        super().__init__(
            event_id=event_id,
            jour=jour,
            arrondissement=arrondissement,
            duration=duration,
            casualties_base=casualties_base,
            characteristics=characteristics
        )
