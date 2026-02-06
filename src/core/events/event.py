"""
Classe de base abstraite pour les événements.
Story 2.1.1 - Infrastructure de base
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Event(ABC):
    """
    Classe de base abstraite pour tous les événements.
    
    Un événement peut être grave (incident) ou positif (amélioration).
    """
    
    def __init__(self, event_id: str, jour: int, arrondissement: int):
        """
        Initialise un événement de base.
        
        Args:
            event_id: Identifiant unique de l'événement
            jour: Jour de déclenchement de l'événement
            arrondissement: Numéro de l'arrondissement concerné (1-20)
        """
        self.event_id = event_id
        self.jour = jour
        self.arrondissement = arrondissement
    
    @abstractmethod
    def get_type(self) -> str:
        """
        Retourne le type de l'événement.
        
        Returns:
            Type de l'événement (ex: "incendie_grave", "fin_travaux", etc.)
        """
        pass

    def is_active(self, jour: int) -> bool:
        """
        Indique si l'événement est actif à un jour donné (à surcharger si durée > 1 jour).
        Par défaut : actif uniquement le jour de déclenchement.
        """
        return jour == self.jour

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'événement en dictionnaire.
        
        Returns:
            Dictionnaire représentant l'événement
        """
        return {
            'event_id': self.event_id,
            'type': self.get_type(),
            'jour': self.jour,
            'arrondissement': self.arrondissement
        }
    
    def __repr__(self) -> str:
        """Représentation string de l'événement."""
        return (f"{self.__class__.__name__}(id={self.event_id}, "
                f"jour={self.jour}, arr={self.arrondissement})")
