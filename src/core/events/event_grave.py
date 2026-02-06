"""
Classe de base abstraite pour les événements graves (incidents).
Story 2.1.1 - Infrastructure de base
"""

from typing import Dict, Optional

from .event import Event


class EventGrave(Event):
    """
    Classe de base abstraite pour les événements graves (incidents).
    
    Un événement grave est un incident majeur qui peut avoir des conséquences
    sur les pompiers, le trafic, les activités, etc.
    """
    
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
        Initialise un événement grave.
        
        Args:
            event_id: Identifiant unique de l'événement
            jour: Jour de déclenchement
            arrondissement: Numéro de l'arrondissement (1-20)
            duration: Durée de l'événement en jours
            casualties_base: Nombre de morts de base (défaut: 0)
            characteristics: Caractéristiques probabilistes de l'événement
                (ex: {"traffic_slowdown": 0.7, "cancel_sports": 0.3})
        """
        super().__init__(event_id, jour, arrondissement)
        self.duration = duration
        self.casualties_base = casualties_base
        self.characteristics = characteristics or {}

    def is_active(self, jour: int) -> bool:
        """L'événement grave est actif tant que jour est dans [self.jour, self.jour + self.duration)."""
        return self.jour <= jour < self.jour + self.duration

    def to_dict(self) -> Dict:
        """Convertit l'événement grave en dictionnaire."""
        base_dict = super().to_dict()
        base_dict.update({
            'duration': self.duration,
            'casualties_base': self.casualties_base,
            'characteristics': self.characteristics
        })
        return base_dict
