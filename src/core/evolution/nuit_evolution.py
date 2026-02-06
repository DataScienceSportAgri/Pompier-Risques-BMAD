"""
Évolution des incidents nuit J→J+1 (Story 1.4.4.2).

- Mémoire 60–70 %, corrélations inter-type, saisonnalité (+20 % été).
- Calibration par probabilité de base : raw (matrices + temporalités) modulé en %
  pour atteindre ~45 % accidents, ~65 % incendies, ~70 % agressions.
- Valeur toujours ≤ total, la plupart du temps strictement inférieure.
"""

from typing import Any, Dict, List, Optional

import numpy as np


TYPES = ("agressions", "incendies", "accidents")
MEMOIRE_DEFAULT = 0.65
SAISON_ETE_FACTEUR_NUIT = 1.2

# Probabilités de base cibles par type (calibration pour atteindre ces % du total)
PROPORTIONS_NUIT = {
    "accidents": 0.45,
    "incendies": 0.65,
    "agressions": 0.70,
}


def _count_by_type(incidents_J: Dict[str, Dict[str, Dict[str, int]]], mz: str) -> Dict[str, int]:
    by_type = incidents_J.get(mz, {})
    return {
        t: sum(by_type.get(t, {}).values()) or 0
        for t in TYPES
    }


def _inter_influence(
    mz: str,
    type_cible: str,
    counts: Dict[str, int],
    matrices_inter_type: Dict[str, Dict[str, Dict[str, List[float]]]],
) -> float:
    """Contribution des autres types sur type_cible (matrices de corrélation)."""
    inter = matrices_inter_type.get(mz, {})
    by_cible = inter.get(type_cible, {})
    acc = 0.0
    for t, c in counts.items():
        if t == type_cible or c <= 0:
            continue
        coefs = by_cible.get(t)
        if coefs:
            w = sum(coefs) / 3.0
            acc += w * c
    return acc


def _calibrer_vers_proportion(
    raw: float,
    total: int,
    p_base: float,
    rng: np.random.Generator,
) -> int:
    """
    Calibre la valeur raw (évolution) vers une proba de base p_base.
    Utilise raw comme modulation : plus raw est élevé, plus la proba effective
    s'approche de p_base (voire légèrement au-dessus).
    Amoindrit l'effet de raw pour viser ~p_base × total en moyenne.
    """
    if total <= 0:
        return 0
    ref = total * p_base + 0.5
    # raw modulé : factor ∈ [0.5, 1.2] environ
    factor = (raw + 1) / (ref + 1)
    factor = float(np.clip(factor, 0.5, 1.2))
    p_eff = float(np.clip(p_base * factor, 0.02, 0.98))
    return int(rng.binomial(total, p_eff))


def evoluer_incidents_nuit_J1(
    incidents_nuit_J: Dict[str, Dict[str, int]],
    incidents_J: Dict[str, Dict[str, Dict[str, int]]],
    matrices_inter_type: Dict[str, Dict[str, Dict[str, List[float]]]],
    microzone_ids: List[str],
    saison: str,
    *,
    memoire: float = MEMOIRE_DEFAULT,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, Dict[str, int]]:
    """
    Évolution incidents nuit avec mémoire, corrélations, saisonnalité.
    Calibration : proba de base par type pour atteindre ~45/65/70 % du total.
    """
    if rng is None:
        rng = np.random.default_rng()
    out: Dict[str, Dict[str, int]] = {}
    facteur_saison = SAISON_ETE_FACTEUR_NUIT if saison == "ete" else 1.0
    mem = max(0.0, min(1.0, memoire))

    for mz in microzone_ids:
        counts = _count_by_type(incidents_J, mz)
        out[mz] = {}
        for t in TYPES:
            total = counts.get(t, 0)
            if total == 0:
                out[mz][t] = 0
                continue
            # Évolution : mémoire + corrélations inter-type + saisonnalité
            prev = (incidents_nuit_J.get(mz) or {}).get(t, 0)
            corr = _inter_influence(mz, t, counts, matrices_inter_type)
            corr_scaled = min(max(0.0, corr), 10.0) * 0.3
            mu = mem * prev + (1.0 - mem) * corr_scaled
            mu *= facteur_saison
            noise = rng.normal(0, 0.5)
            raw = max(0.0, mu + noise)
            # Calibration vers proportion cible (amoindrissant / modulation %)
            p_base = PROPORTIONS_NUIT.get(t, 0.6)
            val = _calibrer_vers_proportion(raw, total, p_base, rng)
            out[mz][t] = min(val, total)
    return out
