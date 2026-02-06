"""
VectorsState : Gestion des vecteurs d'incidents par microzone (données journalières).
Story 2.1.2 - Structure SimulationState avec domaines spécialisés
"""

from typing import Dict, Optional

from ..data.vector import Vector
from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE
)


class VectorsState:
    """
    Gestion des vecteurs d'incidents par microzone (données journalières uniquement).
    
    Structure : Dict[microzone_id, Dict[jour, Dict[type_incident, Vector]]]
    Exemple : {
        "MZ_11_01": {
            0: {
                "incendie": Vector(grave=0, moyen=1, benin=2),
                "accident": Vector(grave=0, moyen=0, benin=1),
                "agression": Vector(grave=0, moyen=0, benin=0)
            },
            1: { ... }
        }
    }
    """
    
    def __init__(self):
        """Initialise un état vide de vecteurs."""
        # Structure : Dict[microzone_id, Dict[jour, Dict[type_incident, Vector]]]
        self._vectors: Dict[str, Dict[int, Dict[str, Vector]]] = {}
    
    def set_vector(
        self,
        microzone_id: str,
        jour: int,
        type_incident: str,
        vector: Vector
    ) -> None:
        """
        Définit un vecteur pour une microzone, un jour et un type d'incident.
        
        Args:
            microzone_id: Identifiant de la microzone
            jour: Numéro du jour (0-indexé)
            type_incident: Type d'incident ("incendie", "accident", "agression")
            vector: Vecteur d'incidents
        """
        if microzone_id not in self._vectors:
            self._vectors[microzone_id] = {}
        if jour not in self._vectors[microzone_id]:
            self._vectors[microzone_id][jour] = {}
        
        self._vectors[microzone_id][jour][type_incident] = vector
    
    def get_vector(
        self,
        microzone_id: str,
        jour: int,
        type_incident: str
    ) -> Optional[Vector]:
        """
        Récupère un vecteur pour une microzone, un jour et un type d'incident.
        
        Args:
            microzone_id: Identifiant de la microzone
            jour: Numéro du jour
            type_incident: Type d'incident
        
        Returns:
            Vector ou None si non trouvé
        """
        return self._vectors.get(microzone_id, {}).get(jour, {}).get(type_incident)
    
    def get_vectors_for_day(
        self,
        microzone_id: str,
        jour: int
    ) -> Dict[str, Vector]:
        """
        Récupère tous les vecteurs d'une microzone pour un jour donné.
        
        Args:
            microzone_id: Identifiant de la microzone
            jour: Numéro du jour
        
        Returns:
            Dictionnaire {type_incident: Vector}
        """
        return self._vectors.get(microzone_id, {}).get(jour, {}).copy()
    
    def get_all_microzones(self) -> list:
        """Retourne la liste de toutes les microzones ayant des données."""
        return list(self._vectors.keys())
    
    def get_all_days(self, microzone_id: str) -> list:
        """
        Retourne la liste de tous les jours avec données pour une microzone.
        
        Args:
            microzone_id: Identifiant de la microzone
        
        Returns:
            Liste des jours (triés)
        """
        if microzone_id not in self._vectors:
            return []
        return sorted(self._vectors[microzone_id].keys())
    
    def clear_day(self, jour: int) -> None:
        """
        Supprime toutes les données pour un jour donné (toutes microzones).
        
        Args:
            jour: Numéro du jour à supprimer
        """
        for microzone_id in self._vectors:
            if jour in self._vectors[microzone_id]:
                del self._vectors[microzone_id][jour]
    
    def to_dict(self) -> Dict:
        """
        Convertit l'état en dictionnaire (pour sérialisation).
        
        Returns:
            Dictionnaire représentant l'état
        """
        result = {}
        for mz_id, jours in self._vectors.items():
            result[mz_id] = {}
            for jour, types in jours.items():
                result[mz_id][jour] = {
                    type_inc: vec.to_list()
                    for type_inc, vec in types.items()
                }
        return result
    
    def __repr__(self) -> str:
        """Représentation string de l'état."""
        nb_microzones = len(self._vectors)
        total_days = sum(len(jours) for jours in self._vectors.values())
        return f"VectorsState(microzones={nb_microzones}, total_days={total_days})"
