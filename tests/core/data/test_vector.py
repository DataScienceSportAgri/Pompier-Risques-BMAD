"""
Tests unitaires pour la classe Vector.
Story 2.1.1 - Infrastructure de base
"""

import pytest

from src.core.data.vector import Vector
from src.core.data.constants import (
    VECTOR_INDEX_BENIN,
    VECTOR_INDEX_GRAVE,
    VECTOR_INDEX_MOYEN
)


class TestVector:
    """Tests pour la classe Vector."""
    
    def test_creation_par_defaut(self):
        """Test création d'un vecteur par défaut (tous à 0)."""
        vecteur = Vector()
        assert vecteur.grave == 0
        assert vecteur.moyen == 0
        assert vecteur.benin == 0
        assert vecteur.total() == 0
    
    def test_creation_avec_valeurs(self):
        """Test création d'un vecteur avec des valeurs."""
        vecteur = Vector(grave=1, moyen=2, benin=5)
        assert vecteur.grave == 1
        assert vecteur.moyen == 2
        assert vecteur.benin == 5
        assert vecteur.total() == 8
    
    def test_creation_valeurs_negatives_raise_error(self):
        """Test que des valeurs négatives lèvent une ValueError."""
        with pytest.raises(ValueError, match="doivent être positives ou nulles"):
            Vector(grave=-1, moyen=0, benin=0)
        
        with pytest.raises(ValueError, match="doivent être positives ou nulles"):
            Vector(grave=0, moyen=-1, benin=0)
        
        with pytest.raises(ValueError, match="doivent être positives ou nulles"):
            Vector(grave=0, moyen=0, benin=-1)
    
    def test_to_list(self):
        """Test conversion en liste."""
        vecteur = Vector(grave=1, moyen=2, benin=5)
        liste = vecteur.to_list()
        assert liste == [1, 2, 5]
        assert isinstance(liste, list)
    
    def test_from_list(self):
        """Test création depuis une liste."""
        vecteur = Vector.from_list([1, 2, 5])
        assert vecteur.grave == 1
        assert vecteur.moyen == 2
        assert vecteur.benin == 5
    
    def test_from_list_mauvaise_taille_raise_error(self):
        """Test que from_list avec mauvaise taille lève une erreur."""
        with pytest.raises(ValueError, match="doit contenir exactement 3 valeurs"):
            Vector.from_list([1, 2])
        
        with pytest.raises(ValueError, match="doit contenir exactement 3 valeurs"):
            Vector.from_list([1, 2, 3, 4])
    
    def test_from_list_valeurs_negatives_raise_error(self):
        """Test que from_list avec valeurs négatives lève une erreur."""
        with pytest.raises(ValueError, match="doivent être positives ou nulles"):
            Vector.from_list([-1, 0, 0])
    
    def test_total(self):
        """Test calcul du total."""
        vecteur = Vector(grave=1, moyen=2, benin=5)
        assert vecteur.total() == 8
        
        vecteur = Vector(grave=0, moyen=0, benin=0)
        assert vecteur.total() == 0
        
        vecteur = Vector(grave=10, moyen=20, benin=30)
        assert vecteur.total() == 60
    
    def test_equality(self):
        """Test comparaison d'égalité."""
        vecteur1 = Vector(grave=1, moyen=2, benin=5)
        vecteur2 = Vector(grave=1, moyen=2, benin=5)
        vecteur3 = Vector(grave=2, moyen=2, benin=5)
        
        assert vecteur1 == vecteur2
        assert vecteur1 != vecteur3
        assert vecteur1 != "not a vector"
    
    def test_repr(self):
        """Test représentation string."""
        vecteur = Vector(grave=1, moyen=2, benin=5)
        repr_str = repr(vecteur)
        assert "Vector" in repr_str
        assert "grave=1" in repr_str
        assert "moyen=2" in repr_str
        assert "benin=5" in repr_str
    
    def test_str(self):
        """Test représentation string lisible."""
        vecteur = Vector(grave=1, moyen=2, benin=5)
        str_repr = str(vecteur)
        assert str_repr == "[1, 2, 5]"
    
    def test_constantes_indices(self):
        """Test que les constantes d'indices sont correctes."""
        vecteur = Vector.from_list([10, 20, 30])
        liste = vecteur.to_list()
        
        assert liste[VECTOR_INDEX_GRAVE] == 10
        assert liste[VECTOR_INDEX_MOYEN] == 20
        assert liste[VECTOR_INDEX_BENIN] == 30
