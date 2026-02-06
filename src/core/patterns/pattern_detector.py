"""
Détection des patterns dynamiques 4j→7j et 60j (Story 1.4.4.5).

- 4j→7j : 1 agression par jour (n'importe quel niveau) pendant 4 jours consécutifs.
- 60j : aucune agression pendant 7 jours consécutifs.
"""

from typing import Dict, List, Tuple

FENETRE_4J = 4
FENETRE_60J = 7


def _total(d: Tuple[int, int, int]) -> int:
    return d[0] + d[1] + d[2]


def detect_pattern_4j(
    historique: Dict[str, List[Tuple[int, int, int]]],
    mz: str,
) -> bool:
    """
    Détecte un pattern 4j→7j : 1 agression par jour (tout niveau) pendant 4 jours consécutifs.

    historique[mz] = liste des (n_benin, n_moyen, n_grave) par jour, du plus ancien au plus récent.
    On utilise les 4 derniers jours.
    """
    h = historique.get(mz) or []
    if len(h) < FENETRE_4J:
        return False
    last4 = h[-FENETRE_4J:]
    return all(_total(j) >= 1 for j in last4)


def detect_pattern_60j(
    historique: Dict[str, List[Tuple[int, int, int]]],
    mz: str,
) -> bool:
    """
    Détecte un pattern 60j : aucune agression pendant 7 jours consécutifs.

    On utilise les 7 derniers jours.
    """
    h = historique.get(mz) or []
    if len(h) < FENETRE_60J:
        return False
    last7 = h[-FENETRE_60J:]
    return all(_total(j) == 0 for j in last7)


def create_pattern_7j(jour_sim: int) -> dict:
    """
    Crée un pattern 7j : début, pic jour 3, fin jour 7, amplitude base +0.1, pic +0.15.
    """
    return {
        "type": "7j",
        "type_incident": "agressions",
        "jour_debut": jour_sim,
        "jour_actuel": 0,
        "amplitude_base": 0.1,
        "amplitude_pic": 0.15,
        "jour_pic": 3,
        "duree": 7,
    }


def create_pattern_60j(jour_sim: int) -> dict:
    """
    Crée un pattern 60j : 3 phases (1–20, 21–40, 41–60), amplitudes +0.05, -0.05, +0.1.
    """
    return {
        "type": "60j",
        "type_incident": "agressions",
        "jour_debut": jour_sim,
        "jour_actuel": 0,
        "phase": 1,
        "amplitude_phase1": 0.05,
        "amplitude_phase2": -0.05,
        "amplitude_phase3": 0.1,
        "phase1_jours": (1, 20),
        "phase2_jours": (21, 40),
        "phase3_jours": (41, 60),
        "duree": 60,
    }
