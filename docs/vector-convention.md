# Convention des Vecteurs - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Statut:** Décision technique validée

---

## Convention d'Ordre

Tous les vecteurs d'incidents dans le système utilisent la structure de tuple suivante :

```python
vector = (bénin, moyen, grave)
```

**Ordre fixe:**
- **Index 0** : Nombre d'incidents **bénins**
- **Index 1** : Nombre d'incidents **moyens**
- **Index 2** : Nombre d'incidents **graves**

---

## Exemples

### Vecteur simple
```python
# 5 incidents bénins, 2 moyens, 1 grave
agressions = (5, 2, 1)

# Accès aux valeurs
benin = agressions[0]    # 5
moyen = agressions[1]   # 2
grave = agressions[2]  # 1
```

### Vecteurs par type d'incident
```python
# Structure complète pour une microzone
vectors = {
    'agressions': (5, 2, 1),   # (bénin, moyen, grave)
    'incendies': (3, 1, 0),     # (bénin, moyen, grave)
    'accidents': (8, 3, 2)      # (bénin, moyen, grave)
}
```

### Opérations vectorielles
```python
import numpy as np

# Conversion en array numpy pour calculs
v1 = np.array([5, 2, 1])
v2 = np.array([3, 1, 0])

# Addition
somme = v1 + v2  # [8, 3, 1]

# Multiplication par facteur
facteur = 1.5
v_modifie = v1 * facteur  # [7.5, 3.0, 1.5]

# Somme totale d'incidents
total = v1.sum()  # 8

# Somme incidents graves (moyen + grave)
graves = v1[1] + v1[2]  # 3
```

---

## Implémentation dans le Code

### Constantes recommandées

Créer un fichier `src/data/constants.py` :

```python
"""
Constantes pour la convention des vecteurs.
Tous les vecteurs suivent l'ordre: (bénin, moyen, grave)
"""

# Indices pour accès aux vecteurs
VECTOR_INDEX_BENIN = 0
VECTOR_INDEX_MOYEN = 1
VECTOR_INDEX_GRAVE = 2

# Types d'incidents
INCIDENT_TYPES = ['agressions', 'incendies', 'accidents']

# Gravités
GRAVITIES = ['benin', 'moyen', 'grave']
```

### Utilisation dans le code

```python
from src.data.constants import (
    VECTOR_INDEX_BENIN,
    VECTOR_INDEX_MOYEN,
    VECTOR_INDEX_GRAVE
)

# Création
vector = (5, 2, 1)

# Accès avec constantes (plus lisible)
benin = vector[VECTOR_INDEX_BENIN]
moyen = vector[VECTOR_INDEX_MOYEN]
grave = vector[VECTOR_INDEX_GRAVE]

# Fonctions utilitaires
def get_total_incidents(vector):
    """Retourne le total d'incidents (bénin + moyen + grave)."""
    return sum(vector)

def get_graves_only(vector):
    """Retourne la somme des incidents moyens et graves."""
    return vector[VECTOR_INDEX_MOYEN] + vector[VECTOR_INDEX_GRAVE]

def get_ratio_graves(vector):
    """Retourne le ratio d'incidents graves sur le total."""
    total = get_total_incidents(vector)
    if total == 0:
        return 0.0
    return vector[VECTOR_INDEX_GRAVE] / total
```

### Alternative: NamedTuple (optionnel)

Pour plus de clarté dans le code, on peut utiliser un `NamedTuple` :

```python
from typing import NamedTuple

class Vector(NamedTuple):
    """Vecteur d'incidents (bénin, moyen, grave)."""
    benin: int
    moyen: int
    grave: int
    
    def total(self) -> int:
        """Retourne le total d'incidents."""
        return self.benin + self.moyen + self.grave
    
    def to_tuple(self) -> tuple:
        """Convertit en tuple pour compatibilité."""
        return (self.benin, self.moyen, self.grave)

# Usage
v = Vector(5, 2, 1)
print(v.benin)   # 5
print(v.total()) # 8

# Conversion depuis tuple
v_from_tuple = Vector(*(5, 2, 1))
```

**Note:** Le NamedTuple est optionnel. Les tuples simples sont recommandés pour la performance et la simplicité.

---

## Avantages de cette Convention

1. **Économie mémoire:** Tuples plus légers que dictionnaires (pas de clés string)
2. **Performance:** Accès par index O(1), opérations vectorielles numpy natives
3. **Simplicité:** Calculs matriciels directs (addition, multiplication) sans conversion
4. **Cohérence:** Format uniforme dans tout le système
5. **Compatibilité:** Facilement convertible en array numpy pour calculs scientifiques

---

## Où Documenter cette Convention

1. **Code:** Constantes dans `src/data/constants.py`
2. **Documentation technique:** `docs/formules.md` (section sur les vecteurs)
3. **Documentation architecture:** `docs/architecture.md` (section structures de données)
4. **Docstrings:** Toutes les fonctions manipulant des vecteurs doivent mentionner la convention

---

## Exemple de Docstring

```python
def calculate_intensity(vector: tuple, factor: float) -> tuple:
    """
    Calcule l'intensité modulée d'un vecteur d'incidents.
    
    Args:
        vector: Tuple (bénin, moyen, grave) d'incidents
        factor: Facteur de modulation
        
    Returns:
        Tuple (bénin, moyen, grave) avec intensités modulées
        
    Note:
        Convention: tous les vecteurs suivent l'ordre (bénin, moyen, grave)
    """
    return tuple(v * factor for v in vector)
```

---

**Fin du document**
