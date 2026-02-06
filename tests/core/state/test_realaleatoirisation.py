"""
Tests pour les patterns de réaléatoirisation (Story 2.4.3.4).
Nom de fichier sans accent pour compatibilité shell/encodage.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# tests/core/state/test_xxx.py -> parents[3] = racine projet
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Charger le module par chemin (nom de fichier peut contenir accent)
_mod_dir = ROOT / "src" / "core" / "state"
_candidates = list(_mod_dir.glob("real*_state.py"))
if not _candidates:
    # Fallback: chercher un fichier contenant "real" et "_state"
    _candidates = [f for f in _mod_dir.glob("*.py") if "real" in f.name.lower() and "_state" in f.name]
if not _candidates:
    pytest.skip("Module realaléatoirisation_state non trouvé", allow_module_level=True)
_mod_path = _candidates[0].resolve()
_spec = importlib.util.spec_from_file_location("realaléatoirisation_state", _mod_path)
mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = mod
_spec.loader.exec_module(mod)


def test_generate_patterns_seed_reproductible() -> None:
    """Avec seed fixe, les patterns sont reproductibles."""
    mz_to_arr = {"MZ_11_01": 11, "MZ_11_02": 11, "MZ_12_01": 12}
    arrs = [11, 12]
    cfg = {"enabled": True}
    state1 = mod.generate_realaléatoirisation_patterns(arrs, 80, mz_to_arr, cfg, seed=42)
    state2 = mod.generate_realaléatoirisation_patterns(arrs, 80, mz_to_arr, cfg, seed=42)
    assert len(state1.patterns) == len(state2.patterns)
    for p1, p2 in zip(state1.patterns, state2.patterns):
        assert p1.arrondissement == p2.arrondissement
        assert p1.jour_debut == p2.jour_debut
        assert p1.duree_totale == p2.duree_totale


def test_at_least_one_pattern_in_60_days() -> None:
    """Sur 60 jours avec seed fixe, au moins un pattern pour au moins un arrondissement."""
    mz_to_arr = {"MZ_11_01": 11, "MZ_12_01": 12}
    arrs = [11, 12]
    cfg = {"enabled": True, "periode_moyenne_jours": (5, 10), "duree_pattern_jours": (10, 15)}
    state = mod.generate_realaléatoirisation_patterns(arrs, 60, mz_to_arr, cfg, seed=42)
    assert len(state.patterns) >= 1


def test_alpha_ramp_and_plateau() -> None:
    """3 positions : rampe début, rampe milieu (dip), rampe fin."""
    p = mod.RealaléatoirisationPattern(
        arrondissement=11,
        jour_debut=10,
        duree_totale=12,
        duree_rampe_debut=2,
        duree_rampe_milieu=2,
        duree_rampe_fin=2,
        taux_reduction_r=0.7,
    )
    assert p.alpha_at_day(9) == 0.0
    assert p.alpha_at_day(10) > 0
    assert p.alpha_at_day(11) == 1.0
    assert p.alpha_at_day(12) == 1.0
    # Rampe milieu : dip (α descend puis remonte)
    assert p.alpha_at_day(14) <= 1.0 and p.alpha_at_day(14) >= 0.0
    assert p.alpha_at_day(17) == 1.0  # plateau 2
    assert p.alpha_at_day(20) >= 0.0  # rampe fin
    assert p.alpha_at_day(21) == 0.0
    assert p.alpha_at_day(22) == 0.0


def test_max_four_patterns_per_arrondissement() -> None:
    """Aucun arrondissement n'a plus de 4 patterns actifs le même jour (Story)."""
    mz_to_arr = {f"MZ_{a:02d}_01": a for a in range(1, 21)}
    arrs = list(range(1, 21))
    cfg = {"enabled": True}
    state = mod.generate_realaléatoirisation_patterns(arrs, 200, mz_to_arr, cfg, seed=123)
    for jour in range(200):
        for arr in arrs:
            active = [p for p in state.patterns if p.arrondissement == arr and p.jour_debut <= jour <= p.jour_fin()]
            assert len(active) <= 4, f"arr={arr} jour={jour} active={len(active)}"


def test_dampening_only_affects_correct_arrondissement() -> None:
    """Le facteur n'affecte que les microzones de l'arrondissement concerné."""
    patterns = [mod.RealaléatoirisationPattern(11, 5, 10, 2, 0, 2, 0.8)]
    mz_to_arr = {"MZ_11_01": 11, "MZ_12_01": 12}
    state = mod.RealaléatoirisationState(patterns, mz_to_arr, {})
    d11 = state.get_matrix_dampening(10, "MZ_11_01")
    d12 = state.get_matrix_dampening(10, "MZ_12_01")
    assert d11 < 1.0
    assert d12 == 1.0
