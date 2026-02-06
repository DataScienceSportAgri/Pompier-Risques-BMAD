"""
Tests détection et gestion des patterns dynamiques (Story 1.4.4.5).

- Détection 4j (1 agression/jour tout niveau, 4 jours consécutifs)
- Détection 60j (aucune agression 7 jours)
- Création 7j / 60j, limitation 3, priorisation, cycle de vie
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.patterns import (
    detect_pattern_4j,
    detect_pattern_60j,
    create_pattern_7j,
    create_pattern_60j,
    add_pattern,
    update_patterns,
    remove_expired_patterns,
)
from core.state import SimulationState

MZ = "MZ001"


def _hist(os: list[tuple[int, int, int]]) -> dict:
    return {MZ: os}


class TestDetection4j:
    def test_4j_quatre_jours_un_agression_par_jour(self):
        h = _hist([(0, 0, 0)] * 3 + [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)])
        assert detect_pattern_4j(h, MZ) is True

    def test_4j_benin_seul_suffit(self):
        h = _hist([(1, 0, 0)] * 4)
        assert detect_pattern_4j(h, MZ) is True

    def test_4j_moins_de_quatre_jours_false(self):
        h = _hist([(1, 0, 0)] * 3)
        assert detect_pattern_4j(h, MZ) is False

    def test_4j_un_jour_sans_agression_false(self):
        h = _hist([(1, 0, 0), (1, 0, 0), (0, 0, 0), (1, 0, 0)])
        assert detect_pattern_4j(h, MZ) is False


class TestDetection60j:
    def test_60j_sept_jours_sans_agression(self):
        h = _hist([(0, 0, 0)] * 7)
        assert detect_pattern_60j(h, MZ) is True

    def test_60j_moins_de_sept_false(self):
        h = _hist([(0, 0, 0)] * 6)
        assert detect_pattern_60j(h, MZ) is False

    def test_60j_un_jour_avec_agression_false(self):
        h = _hist([(0, 0, 0)] * 6 + [(1, 0, 0)])
        assert detect_pattern_60j(h, MZ) is False


class TestCreationPatterns:
    def test_create_pattern_7j_structure(self):
        p = create_pattern_7j(100)
        assert p["type"] == "7j"
        assert p["jour_debut"] == 100
        assert p["jour_actuel"] == 0
        assert p["jour_pic"] == 3
        assert p["duree"] == 7
        assert p["amplitude_base"] == 0.1
        assert p["amplitude_pic"] == 0.15

    def test_create_pattern_60j_structure(self):
        p = create_pattern_60j(200)
        assert p["type"] == "60j"
        assert p["jour_debut"] == 200
        assert p["jour_actuel"] == 0
        assert p["phase"] == 1
        assert p["duree"] == 60
        assert p["amplitude_phase1"] == 0.05
        assert p["amplitude_phase2"] == -0.05
        assert p["amplitude_phase3"] == 0.1


class TestLimitationMax3:
    def test_max_trois_patterns_par_microzone(self):
        actifs = {}
        for i in range(5):
            add_pattern(actifs, MZ, create_pattern_7j(i), max_par_mz=3)
        assert len(actifs[MZ]) == 3

    def test_priorisation_7j_gardes_sur_60j(self):
        actifs = {MZ: []}
        add_pattern(actifs, MZ, create_pattern_60j(0), max_par_mz=3)
        add_pattern(actifs, MZ, create_pattern_7j(1), max_par_mz=3)
        add_pattern(actifs, MZ, create_pattern_60j(2), max_par_mz=3)
        add_pattern(actifs, MZ, create_pattern_7j(3), max_par_mz=3)
        types = [p["type"] for p in actifs[MZ]]
        assert types.count("7j") == 2 and types.count("60j") == 1


class TestCycleDeVie:
    def test_update_avance_jour_actuel(self):
        actifs = {MZ: [create_pattern_7j(0)]}
        update_patterns(actifs)
        assert actifs[MZ][0]["jour_actuel"] == 1
        update_patterns(actifs)
        assert actifs[MZ][0]["jour_actuel"] == 2

    def test_60j_phase_update(self):
        actifs = {MZ: [create_pattern_60j(0)]}
        for _ in range(19):
            update_patterns(actifs)
        assert actifs[MZ][0]["phase"] == 1
        update_patterns(actifs)
        assert actifs[MZ][0]["phase"] == 2
        for _ in range(19):
            update_patterns(actifs)
        assert actifs[MZ][0]["phase"] == 2
        update_patterns(actifs)
        assert actifs[MZ][0]["phase"] == 3

    def test_remove_expired_7j(self):
        actifs = {MZ: [create_pattern_7j(0)]}
        for _ in range(7):
            update_patterns(actifs)
        remove_expired_patterns(actifs)
        assert MZ not in actifs or len(actifs[MZ]) == 0

    def test_remove_expired_60j(self):
        actifs = {MZ: [create_pattern_60j(0)]}
        for _ in range(60):
            update_patterns(actifs)
        remove_expired_patterns(actifs)
        assert MZ not in actifs or len(actifs[MZ]) == 0


class TestIntegrationSimulationState:
    def test_simulation_state_a_patterns_actifs(self):
        st = SimulationState("run1", {})
        assert hasattr(st, "patterns_actifs")
        assert st.patterns_actifs == {}
        add_pattern(st.patterns_actifs, MZ, create_pattern_7j(0))
        assert len(st.patterns_actifs[MZ]) == 1
