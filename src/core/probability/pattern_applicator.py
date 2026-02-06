"""
Application des patterns dynamiques aux probabilités (Story 1.4.4.6).

- 7j : amplitude base +0.1 (jours 1-2, 4-7), pic +0.15 (jour 3).
- 60j : phase 1 (1-20) +0.05, phase 2 (21-40) -0.05, phase 3 (41-60) +0.1.
- Plusieurs patterns : addition des amplitudes, puis ajout aux probabilités.
- Appliqué uniquement au type « agressions ».
"""

from typing import Dict, List, Tuple

from .matrix_applicator import _vec_clamp

TYPE_PATTERN = "agressions"


def _amplitude_7j(p: dict) -> float:
    """Amplitude du pattern 7j selon jour_actuel (0-based). Jour 3 = pic +0.15."""
    j = p.get("jour_actuel", 0)
    jour_pic = p.get("jour_pic", 3) - 1  # 1-based → 0-based
    base = p.get("amplitude_base", 0.1)
    pic = p.get("amplitude_pic", 0.15)
    return pic if j == jour_pic else base


def _amplitude_60j(p: dict) -> float:
    """Amplitude du pattern 60j selon phase (jour_actuel 0-based)."""
    ph = p.get("phase", 1)
    if ph == 1:
        return p.get("amplitude_phase1", 0.05)
    if ph == 2:
        return p.get("amplitude_phase2", -0.05)
    return p.get("amplitude_phase3", 0.1)


def _amplitude_pattern(p: dict) -> float:
    t = p.get("type", "")
    if t == "7j":
        return _amplitude_7j(p)
    if t == "60j":
        return _amplitude_60j(p)
    return 0.0


def apply_patterns(
    prob: Tuple[float, float, float],
    mz: str,
    type_incident: str,
    patterns_actifs: Dict[str, List[dict]],
) -> Tuple[float, float, float]:
    """
    Applique les patterns actifs (7j, 60j) aux probabilités modulées.

    - Uniquement pour type_incident « agressions ».
    - Plusieurs patterns : somme des amplitudes, puis addition au vecteur prob.
    - Résultat clampé dans [0, 1].
    """
    if type_incident != TYPE_PATTERN:
        return prob
    lst = patterns_actifs.get(mz) or []
    delta = 0.0
    for p in lst:
        if p.get("type_incident") != TYPE_PATTERN:
            continue
        delta += _amplitude_pattern(p)
    out = (prob[0] + delta, prob[1] + delta, prob[2] + delta)
    return _vec_clamp(out)
