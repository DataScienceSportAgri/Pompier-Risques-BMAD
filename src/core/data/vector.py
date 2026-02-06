"""
Classe Vector pour représenter les incidents par niveau de gravité.
Story 2.1.1 - Infrastructure de base
"""

from typing import List

from .constants import VECTOR_INDEX_BENIN, VECTOR_INDEX_GRAVE, VECTOR_INDEX_MOYEN


class Vector:
    """
    Vecteur d'incidents par niveau de gravité : [grave, moyen, bénin].
    
    Attributes:
        grave (int): Nombre d'incidents graves
        moyen (int): Nombre d'incidents moyens
        benin (int): Nombre d'incidents bénins
    """
    
    def __init__(self, grave: int = 0, moyen: int = 0, benin: int = 0):
        """
        Initialise un vecteur d'incidents.
        
        Args:
            grave: Nombre d'incidents graves (défaut: 0)
            moyen: Nombre d'incidents moyens (défaut: 0)
            benin: Nombre d'incidents bénins (défaut: 0)
        
        Raises:
            ValueError: Si une valeur est négative
        """
        if grave < 0 or moyen < 0 or benin < 0:
            raise ValueError("Les valeurs du vecteur doivent être positives ou nulles")
        
        self.grave = grave
        self.moyen = moyen
        self.benin = benin
    
    def to_list(self) -> List[int]:
        """
        Convertit le vecteur en liste [grave, moyen, bénin].
        
        Returns:
            Liste [grave, moyen, bénin]
        """
        return [self.grave, self.moyen, self.benin]
    
    @classmethod
    def from_list(cls, values: List[int]) -> 'Vector':
        """
        Crée un Vector à partir d'une liste [grave, moyen, bénin].
        
        Args:
            values: Liste de 3 entiers [grave, moyen, bénin]
        
        Returns:
            Instance de Vector
        
        Raises:
            ValueError: Si la liste n'a pas 3 éléments ou contient des valeurs négatives
        """
        if len(values) != 3:
            raise ValueError("La liste doit contenir exactement 3 valeurs [grave, moyen, bénin]")
        return cls(grave=values[VECTOR_INDEX_GRAVE], 
                   moyen=values[VECTOR_INDEX_MOYEN], 
                   benin=values[VECTOR_INDEX_BENIN])
    
    def total(self) -> int:
        """
        Calcule le nombre total d'incidents.
        
        Returns:
            Somme de grave + moyen + bénin
        """
        return self.grave + self.moyen + self.benin
    
    def __eq__(self, other) -> bool:
        """Comparaison d'égalité."""
        if not isinstance(other, Vector):
            return False
        return (self.grave == other.grave and 
                self.moyen == other.moyen and 
                self.benin == other.benin)
    
    def __repr__(self) -> str:
        """Représentation string du vecteur."""
        return f"Vector(grave={self.grave}, moyen={self.moyen}, benin={self.benin})"
    
    def __str__(self) -> str:
        """Représentation string lisible."""
        return f"[{self.grave}, {self.moyen}, {self.benin}]"
