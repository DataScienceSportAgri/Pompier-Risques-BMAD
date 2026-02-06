"""
CasualtiesState : Gestion des morts et blessés graves (agrégés par semaine).
Story 2.1.2 - Structure SimulationState avec domaines spécialisés

Note: Casualties sont agrégés par semaine, pas journaliers.
Structure: Dict[semaine, Dict[arrondissement, Dict['morts'|'blesses_graves', int]]]
"""

from typing import Dict, List, Optional


class CasualtiesState:
    """
    Gestion des morts et blessés graves (agrégés par semaine).
    
    Structure : Dict[semaine, Dict[arrondissement, Dict['morts'|'blesses_graves', int]]]
    Exemple : {
        1: {
            11: {"morts": 2, "blesses_graves": 5},
            12: {"morts": 0, "blesses_graves": 1}
        },
        2: { ... }
    }
    """
    
    def __init__(self):
        """Initialise un état vide de casualties."""
        # Structure : Dict[semaine, Dict[arrondissement, Dict[str, int]]]
        self._casualties: Dict[int, Dict[int, Dict[str, int]]] = {}
    
    def add_casualties(
        self,
        semaine: int,
        arrondissement: int,
        morts: int = 0,
        blesses_graves: int = 0
    ) -> None:
        """
        Ajoute des casualties pour une semaine et un arrondissement.
        
        Args:
            semaine: Numéro de la semaine (1-indexé)
            arrondissement: Numéro de l'arrondissement (1-20)
            morts: Nombre de morts
            blesses_graves: Nombre de blessés graves
        """
        if semaine not in self._casualties:
            self._casualties[semaine] = {}
        if arrondissement not in self._casualties[semaine]:
            self._casualties[semaine][arrondissement] = {
                "morts": 0,
                "blesses_graves": 0
            }
        
        self._casualties[semaine][arrondissement]["morts"] += morts
        self._casualties[semaine][arrondissement]["blesses_graves"] += blesses_graves
    
    def get_casualties(
        self,
        semaine: int,
        arrondissement: Optional[int] = None
    ) -> Dict:
        """
        Récupère les casualties pour une semaine.
        
        Args:
            semaine: Numéro de la semaine
            arrondissement: Arrondissement spécifique (None = tous)
        
        Returns:
            Dictionnaire des casualties
        """
        if semaine not in self._casualties:
            return {}
        
        if arrondissement is not None:
            return self._casualties[semaine].get(arrondissement, {}).copy()
        else:
            return self._casualties[semaine].copy()
    
    def get_score(
        self,
        semaine: int,
        arrondissement: int
    ) -> float:
        """
        Calcule le score de casualties pour une semaine et un arrondissement.
        Formule : morts + 0.5 × blessés graves
        
        Args:
            semaine: Numéro de la semaine
            arrondissement: Numéro de l'arrondissement
        
        Returns:
            Score calculé (0.0 si pas de données)
        """
        casualties = self.get_casualties(semaine, arrondissement)
        if not casualties:
            return 0.0
        
        morts = casualties.get("morts", 0)
        blesses_graves = casualties.get("blesses_graves", 0)
        return morts + 0.5 * blesses_graves
    
    def get_all_semaines(self) -> List[int]:
        """Retourne la liste de toutes les semaines avec données (triées)."""
        return sorted(self._casualties.keys())
    
    def clear_semaine(self, semaine: int) -> None:
        """
        Supprime toutes les données d'une semaine.
        
        Args:
            semaine: Numéro de la semaine à supprimer
        """
        if semaine in self._casualties:
            del self._casualties[semaine]
    
    def to_dict(self) -> Dict:
        """
        Convertit l'état en dictionnaire (pour sérialisation).
        
        Returns:
            Dictionnaire représentant l'état
        """
        return self._casualties.copy()
    
    def __repr__(self) -> str:
        """Représentation string de l'état."""
        nb_semaines = len(self._casualties)
        total_arr = sum(len(arrs) for arrs in self._casualties.values())
        return f"CasualtiesState(semaines={nb_semaines}, total_arr={total_arr})"
