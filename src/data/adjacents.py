"""
Arrondissements adjacents de Paris — définis en dur (contraintes techniques).
Story 2.3.1 - Préparation données ML

Chaque arrondissement (1-20) a exactement 4 voisins géographiquement adjacents.
Source : découpage administratif Paris (spirale depuis le centre).
"""

from typing import Dict, List

# Arrondissements de Paris : 1 central + 4 voisins par arrondissement.
# Mapping arrondissement -> [v1, v2, v3, v4] (4 voisins, ordre stable).
ADJACENTS_PARIS: Dict[int, List[int]] = {
    1: [2, 3, 4, 8],
    2: [1, 3, 9, 10],
    3: [1, 2, 4, 11],
    4: [1, 3, 11, 12],
    5: [4, 6, 13, 14],
    6: [1, 5, 7, 14],
    7: [1, 6, 8, 15],
    8: [1, 2, 7, 9],
    9: [2, 8, 10, 18],
    10: [2, 3, 9, 11],
    11: [3, 4, 10, 12],
    12: [4, 11, 19, 20],
    13: [5, 6, 12, 14],
    14: [5, 6, 13, 15],
    15: [6, 7, 14, 16],
    16: [7, 8, 15, 17],
    17: [8, 9, 16, 18],
    18: [9, 10, 17, 19],
    19: [10, 11, 18, 20],
    20: [11, 12, 18, 19],
}


def get_voisins(arrondissement: int) -> List[int]:
    """
    Retourne les 4 voisins de l'arrondissement (ordre stable).

    Args:
        arrondissement: Numéro d'arrondissement (1-20)

    Returns:
        Liste de 4 arrondissements adjacents

    Raises:
        KeyError: Si l'arrondissement n'est pas dans 1-20
    """
    if arrondissement not in ADJACENTS_PARIS:
        raise KeyError(f"Arrondissement inconnu: {arrondissement}")
    return list(ADJACENTS_PARIS[arrondissement])
