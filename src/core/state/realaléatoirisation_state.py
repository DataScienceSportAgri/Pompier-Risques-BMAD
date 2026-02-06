"""
État des patterns de réaléatoirisation (Story 2.4.3.4).

Génère et stocke les patterns par arrondissement : fenêtres pendant lesquelles
l'effet des matrices de corrélation est réduit (60–85 %) pour les microzones
de l'arrondissement, avec 3 positions d'effet (rampes début, milieu, fin) et
au plus 4 patterns actifs simultanément par arrondissement (Story : 7–12 j entre déclenchements).

Module nommé realaléatoirisation_state (sans accent) pour compatibilité encodage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class RealaléatoirisationPattern:
    """Un pattern de réaléatoirisation pour un arrondissement (3 positions : début, milieu, fin)."""

    arrondissement: int
    jour_debut: int
    duree_totale: int
    duree_rampe_debut: int
    duree_rampe_milieu: int  # rampe au milieu (dip 1→0.5→1 sur 2–4 j)
    duree_rampe_fin: int
    taux_reduction_r: float  # 0.60 à 0.85

    def jour_fin(self) -> int:
        return self.jour_debut + self.duree_totale - 1

    def alpha_at_day(self, jour: int) -> float:
        """
        Intensité α du pattern au jour donné (0 = pas de réduction, 1 = plateau).
        3 positions : rampe début (0→1), plateau, rampe milieu (1→0.5→1), plateau, rampe fin (1→0).
        """
        if jour < self.jour_debut or jour > self.jour_fin():
            return 0.0
        offset = jour - self.jour_debut
        rd, rm, rf = self.duree_rampe_debut, self.duree_rampe_milieu, self.duree_rampe_fin
        plateau_total = self.duree_totale - rd - rm - rf
        if plateau_total < 0:
            # Durée trop courte : pas de rampe milieu
            plateau1 = max(0, (self.duree_totale - rd - rf) // 2)
            plateau_end = self.duree_totale - rf
            if offset < rd:
                return (offset + 1) / rd if rd > 0 else 1.0
            if offset < plateau_end:
                return 1.0
            jours_avant_fin = self.jour_fin() - jour
            if rf <= 0 or jours_avant_fin >= rf:
                return 1.0
            return (jours_avant_fin / (rf - 1)) if rf > 1 else 0.0
        plateau1 = plateau_total // 2
        debut_milieu = rd + plateau1
        fin_milieu = debut_milieu + rm
        debut_fin = self.duree_totale - rf
        # Rampe début : 0 → 1
        if offset < rd:
            return (offset + 1) / rd if rd > 0 else 1.0
        # Plateau 1
        if offset < debut_milieu:
            return 1.0
        # Rampe milieu : 1 → 0.5 → 1 (dip)
        if offset < fin_milieu:
            pos = offset - debut_milieu
            if rm <= 0:
                return 1.0
            demi = rm / 2.0
            if pos <= demi:
                return 1.0 - 0.5 * (pos / demi) if demi > 0 else 1.0
            return 0.5 + 0.5 * ((pos - demi) / demi) if demi > 0 else 1.0
        # Plateau 2
        if offset < debut_fin:
            return 1.0
        # Rampe fin : 1 → 0
        jours_avant_fin = self.jour_fin() - jour
        if rf <= 0:
            return 1.0
        if jours_avant_fin >= rf:
            return 1.0
        if rf == 1:
            return 0.0
        return jours_avant_fin / (rf - 1)


def _default_config() -> Dict[str, Any]:
    return {
        "enabled": True,
        "periode_moyenne_jours": (7, 12),
        "duree_pattern_jours": (15, 20),
        "duree_rampe_jours": (2, 4),
        "taux_reduction_min": 0.60,
        "taux_reduction_max": 0.85,
        "max_patterns_simultanes_par_arrondissement": 4,
    }


class RealaléatoirisationState:
    """
    État des patterns de réaléatoirisation par arrondissement.

    Patterns précalculés pour toute la durée de la simulation (reproductible avec seed).
    Expose get_matrix_dampening(jour, microzone_id) pour le pipeline J→J+1.
    """

    def __init__(
        self,
        patterns: List[RealaléatoirisationPattern],
        microzone_to_arrondissement: Dict[str, int],
        config: Optional[Dict[str, Any]] = None,
    ):
        self.patterns = patterns
        self.microzone_to_arrondissement = microzone_to_arrondissement
        self.config = config or _default_config()
        self._by_arr: Dict[int, List[RealaléatoirisationPattern]] = {}
        for p in patterns:
            self._by_arr.setdefault(p.arrondissement, []).append(p)
        for arr in self._by_arr:
            self._by_arr[arr].sort(key=lambda x: x.jour_debut)

    def get_arrondissement(self, microzone_id: str) -> int:
        """Retourne l'arrondissement (1..20) pour une microzone."""
        return self.microzone_to_arrondissement.get(
            microzone_id,
            _parse_arrondissement_from_microzone_id(microzone_id),
        )

    def get_alpha_and_r(
        self,
        jour: int,
        microzone_id: str,
    ) -> Tuple[float, float]:
        """
        Retourne (α_eff, r_eff) pour ce jour et cette microzone.
        En cas de plusieurs patterns actifs : α_eff = min(1, Σ αᵢ), r_eff = moyenne pondérée par α.
        """
        arr = self.get_arrondissement(microzone_id)
        patterns_arr = self._by_arr.get(arr, [])
        active = [p for p in patterns_arr if p.jour_debut <= jour <= p.jour_fin()]
        if not active:
            return 0.0, 0.0
        alphas = [p.alpha_at_day(jour) for p in active]
        rs = [p.taux_reduction_r for p in active]
        alpha_eff = min(1.0, sum(alphas))
        if alpha_eff <= 0:
            return 0.0, 0.0
        r_eff = sum(r * a for r, a in zip(rs, alphas)) / sum(alphas)
        return alpha_eff, r_eff

    def get_matrix_dampening(self, jour: int, microzone_id: str) -> float:
        """
        Facteur d'atténuation des matrices : (1 - r·α).
        Pour chaque facteur matriciel F : F' = 1 + (F - 1) * dampening.
        """
        alpha_eff, r_eff = self.get_alpha_and_r(jour, microzone_id)
        return 1.0 - r_eff * alpha_eff

    def to_dict(self) -> Dict[str, Any]:
        """Sérialisation pour état de simulation."""
        return {
            "patterns": [
                {
                    "arrondissement": p.arrondissement,
                    "jour_debut": p.jour_debut,
                    "duree_totale": p.duree_totale,
                    "duree_rampe_debut": p.duree_rampe_debut,
                    "duree_rampe_milieu": getattr(p, "duree_rampe_milieu", 0),
                    "duree_rampe_fin": p.duree_rampe_fin,
                    "taux_reduction_r": p.taux_reduction_r,
                }
                for p in self.patterns
            ],
            "config": self.config,
        }


def _parse_arrondissement_from_microzone_id(microzone_id: str) -> int:
    """Extrait l'arrondissement depuis microzone_id.
    Formats : MZ_11_01 → 11 ; MZ031 (MZ + 3 chiffres, 5 microzones/arr) → 7."""
    try:
        parts = microzone_id.split("_")
        if len(parts) >= 2:
            return max(1, min(20, int(parts[1])))
        if (
            len(microzone_id) == 5
            and microzone_id.startswith("MZ")
            and microzone_id[2:].isdigit()
        ):
            idx = int(microzone_id[2:])
            return max(1, min(20, (idx - 1) // 5 + 1))
    except (ValueError, TypeError):
        pass
    return 1


def generate_realaléatoirisation_patterns(
    arrondissements: List[int],
    num_days: int,
    microzone_to_arrondissement: Dict[str, int],
    config: Dict[str, Any],
    seed: Optional[int] = None,
) -> RealaléatoirisationState:
    """
    Génère tous les patterns de réaléatoirisation pour la durée de la simulation.
    Période 7–12 j entre déclenchements, au plus 4 patterns actifs par arrondissement, 3 rampes (début, milieu, fin).
    """
    cfg = _default_config()
    cfg.update(config)
    if not cfg.get("enabled", True):
        return RealaléatoirisationState(
            patterns=[],
            microzone_to_arrondissement=microzone_to_arrondissement,
            config=cfg,
        )

    rng = np.random.Generator(np.random.PCG64(seed))
    periode_min, periode_max = cfg.get("periode_moyenne_jours", (7, 12))
    duree_min, duree_max = cfg.get("duree_pattern_jours", (15, 20))
    rampe_min, rampe_max = cfg.get("duree_rampe_jours", (2, 4))
    r_min = cfg.get("taux_reduction_min", 0.60)
    r_max = cfg.get("taux_reduction_max", 0.85)
    max_simult = cfg.get("max_patterns_simultanes_par_arrondissement", 4)

    all_patterns: List[RealaléatoirisationPattern] = []

    for arr in arrondissements:
        next_start = rng.integers(0, max(1, periode_max))
        active: List[RealaléatoirisationPattern] = []

        while next_start < num_days:
            duree = rng.integers(duree_min, duree_max + 1)
            rampe_debut = rng.integers(rampe_min, rampe_max + 1)
            rampe_milieu = rng.integers(rampe_min, rampe_max + 1)
            rampe_fin = rng.integers(rampe_min, rampe_max + 1)
            if rampe_debut + rampe_milieu + rampe_fin > duree:
                rampe_milieu = min(rampe_milieu, max(0, duree - rampe_debut - rampe_fin))
            if rampe_debut + rampe_milieu + rampe_fin > duree:
                rampe_debut = min(rampe_debut, duree // 3)
                rampe_fin = min(rampe_fin, (duree - rampe_debut) // 2)
                rampe_milieu = max(0, duree - rampe_debut - rampe_fin)
            r = float(rng.uniform(r_min, r_max))

            active_at_next = [p for p in active if p.jour_fin() >= next_start]
            if len(active_at_next) >= max_simult:
                first_ending = min(active_at_next, key=lambda p: p.jour_fin())
                next_start = first_ending.jour_fin() + 1
                active = [p for p in active if p.jour_fin() >= next_start]
                if next_start >= num_days:
                    break
                continue

            pattern = RealaléatoirisationPattern(
                arrondissement=arr,
                jour_debut=next_start,
                duree_totale=duree,
                duree_rampe_debut=rampe_debut,
                duree_rampe_milieu=rampe_milieu,
                duree_rampe_fin=rampe_fin,
                taux_reduction_r=r,
            )
            all_patterns.append(pattern)
            active = [p for p in active if p.jour_fin() >= next_start]
            active.append(pattern)

            period = rng.integers(periode_min, periode_max + 1)
            next_start = pattern.jour_fin() + 1 + period

    return RealaléatoirisationState(
        patterns=all_patterns,
        microzone_to_arrondissement=microzone_to_arrondissement,
        config=cfg,
    )
