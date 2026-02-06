"""
EventsState : Gestion des événements (graves et positifs) - données journalières.
Story 2.1.2 - Structure SimulationState avec domaines spécialisés
"""

from typing import Dict, List, Optional

from ..events.event import Event
from ..events.event_grave import EventGrave
from ..events.positive_event import PositiveEvent


class EventsState:
    """
    Gestion des événements journaliers (graves et positifs).
    
    Structure : Dict[jour, List[Event]]
    Les événements sont stockés par jour de déclenchement.
    """
    
    def __init__(self):
        """Initialise un état vide d'événements."""
        # Structure : Dict[jour, List[Event]]
        self._events: Dict[int, List[Event]] = {}
    
    def add_event(self, event: Event) -> None:
        """
        Ajoute un événement à l'état.
        
        Args:
            event: Événement à ajouter (EventGrave ou PositiveEvent)
        """
        jour = event.jour
        if jour not in self._events:
            self._events[jour] = []
        self._events[jour].append(event)
    
    def get_events_for_day(self, jour: int) -> List[Event]:
        """
        Récupère tous les événements d'un jour donné.
        
        Args:
            jour: Numéro du jour
        
        Returns:
            Liste des événements (copie)
        """
        return self._events.get(jour, []).copy()
    
    def get_grave_events_for_day(self, jour: int) -> List[EventGrave]:
        """
        Récupère uniquement les événements graves d'un jour donné.
        
        Args:
            jour: Numéro du jour
        
        Returns:
            Liste des événements graves
        """
        return [
            event for event in self.get_events_for_day(jour)
            if isinstance(event, EventGrave)
        ]
    
    def get_positive_events_for_day(self, jour: int) -> List[PositiveEvent]:
        """
        Récupère uniquement les événements positifs d'un jour donné.
        
        Args:
            jour: Numéro du jour
        
        Returns:
            Liste des événements positifs
        """
        return [
            event for event in self.get_events_for_day(jour)
            if isinstance(event, PositiveEvent)
        ]
    
    def get_events_for_arrondissement(
        self,
        arrondissement: int,
        jour: Optional[int] = None
    ) -> List[Event]:
        """
        Récupère les événements d'un arrondissement.
        
        Args:
            arrondissement: Numéro de l'arrondissement (1-20)
            jour: Jour spécifique (None = tous les jours)
        
        Returns:
            Liste des événements
        """
        if jour is not None:
            events = self.get_events_for_day(jour)
        else:
            events = []
            for day_events in self._events.values():
                events.extend(day_events)
        
        return [
            event for event in events
            if event.arrondissement == arrondissement
        ]
    
    def get_all_days(self) -> List[int]:
        """Retourne la liste de tous les jours avec événements (triés)."""
        return sorted(self._events.keys())

    def get_active_events_for_day(self, jour: int) -> List[Event]:
        """
        Retourne tous les événements actifs à un jour donné (graves en cours + positifs du jour).
        Un événement grave est actif si jour in [event.jour, event.jour + event.duration).
        """
        active = []
        for day_events in self._events.values():
            for event in day_events:
                if hasattr(event, "is_active") and event.is_active(jour):
                    active.append(event)
        return active
    
    def clear_day(self, jour: int) -> None:
        """
        Supprime tous les événements d'un jour donné.
        
        Args:
            jour: Numéro du jour à supprimer
        """
        if jour in self._events:
            del self._events[jour]
    
    def to_dict(self) -> Dict:
        """
        Convertit l'état en dictionnaire (pour sérialisation).
        
        Returns:
            Dictionnaire représentant l'état
        """
        result = {}
        for jour, events in self._events.items():
            result[jour] = [event.to_dict() for event in events]
        return result
    
    def __repr__(self) -> str:
        """Représentation string de l'état."""
        nb_days = len(self._events)
        total_events = sum(len(events) for events in self._events.values())
        return f"EventsState(days={nb_days}, total_events={total_events})"
