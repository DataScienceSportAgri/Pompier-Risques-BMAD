"""
Gestion du cycle de vie des patterns (Story 1.4.4.5).

- add_pattern : ajout avec priorisation, max 3 par microzone.
- update_patterns : avance jour_actuel, mise à jour phase (60j).
- remove_expired_patterns : suppression après durée (7j ou 60j).
"""

from typing import Any, Dict, List

MAX_PATTERNS = 3
ORDRE_PRIORITE = ["7j", "60j"]


def _priorite(p: dict) -> int:
    t = p.get("type", "")
    try:
        return ORDRE_PRIORITE.index(t)
    except ValueError:
        return len(ORDRE_PRIORITE)


def add_pattern(
    patterns_actifs: Dict[str, List[dict]],
    mz: str,
    pattern: dict,
    max_par_mz: int = MAX_PATTERNS,
) -> None:
    """
    Ajoute un pattern pour la microzone. Limite à max_par_mz (défaut 3).
    Priorité : 7j > 60j ; on supprime le moins prioritaire si dépassement.
    """
    if mz not in patterns_actifs:
        patterns_actifs[mz] = []
    lst = patterns_actifs[mz]
    lst.append(pattern)
    lst.sort(key=_priorite)
    while len(lst) > max_par_mz:
        lst.pop()


def _avance_jour_actuel(p: dict) -> None:
    j = p.get("jour_actuel", 0) + 1
    p["jour_actuel"] = j
    if p.get("type") != "60j":
        return
    if j < 20:
        p["phase"] = 1
    elif j < 40:
        p["phase"] = 2
    else:
        p["phase"] = 3


def update_patterns(patterns_actifs: Dict[str, List[dict]]) -> None:
    """
    Avance jour_actuel de 1 pour chaque pattern actif et met à jour la phase (60j).
    Ne supprime pas les patterns expirés (voir remove_expired_patterns).
    """
    for lst in patterns_actifs.values():
        for p in lst:
            _avance_jour_actuel(p)


def remove_expired_patterns(patterns_actifs: Dict[str, List[dict]]) -> None:
    """Supprime les patterns dont jour_actuel >= duree (7j ou 60j)."""
    for mz in list(patterns_actifs.keys()):
        patterns_actifs[mz] = [
            p for p in patterns_actifs[mz]
            if p.get("jour_actuel", 0) < p.get("duree", 7)
        ]
        if not patterns_actifs[mz]:
            del patterns_actifs[mz]
