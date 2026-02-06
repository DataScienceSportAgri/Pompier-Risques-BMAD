"""
Données de référence (arrondissements adjacents, etc.).
Story 2.3.1 - Préparation données ML
"""

from .adjacents import (
    ADJACENTS_PARIS,
    get_voisins,
)

__all__ = [
    "ADJACENTS_PARIS",
    "get_voisins",
]
