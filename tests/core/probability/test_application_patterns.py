"""
Tests application des patterns dans le calcul des probabilités (Story 1.4.4.6).

- Pattern 7j (amplitude base, pic jour 3)
- Pattern 60j (3 phases)
- Combinaison patterns + matrices + variables d'état
- Plusieurs patterns (addition amplitudes)
- Probabilités finales [0, 1], agressions uniquement modulées
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.probability import (
    calculer_probabilite_incidents_J1,
    apply_patterns,
)
from core.patterns import create_pattern_7j, create_pattern_60j

TYPES = ("agressions", "incendies", "accidents")


def _mat_intra():
    m = np.zeros((3, 3))
    m[0] = [0.85, 0.12, 0.03]
    m[1] = [0.10, 0.75, 0.15]
    m[2] = [0.05, 0.20, 0.75]
    return m


def _inter_mock(mz):
    return {mz: {t: {s: [0.0, 0.0, 0.0] for s in TYPES if s != t} for t in TYPES}}


def _voisin_mock(mz, voisins):
    return {mz: {"voisins": voisins, "poids_influence": [1.0 / 8] * 8, "seuil_activation": 999}}


def _saison_mock(mz):
    return {mz: {t: {"hiver": 1.0, "intersaison": 1.0, "ete": 1.0} for t in TYPES}}


def _run(prob_base, inc, intra, inter, voisin, saison, mz_ids, saison_str="intersaison", patterns_actifs=None, dynamic_state=None):
    inc = dict(inc)
    voisins = voisin.get(mz_ids[0], {}).get("voisins", [])
    for v in voisins:
        if v not in inc:
            inc[v] = {t: (0, 0, 0) for t in TYPES}
    return calculer_probabilite_incidents_J1(
        prob_base, inc, intra, inter, voisin, saison, mz_ids, saison_str,
        dynamic_state=dynamic_state, patterns_actifs=patterns_actifs,
    )


class TestPattern7j:
    def test_amplitude_base_jour_1_2(self):
        p = create_pattern_7j(0)
        p["jour_actuel"] = 0
        prob = (0.1, 0.05, 0.02)
        out = apply_patterns(prob, "MZ001", "agressions", {"MZ001": [p]})
        assert out[0] == pytest.approx(0.1 + 0.1, abs=1e-6)
        assert out[1] == pytest.approx(0.05 + 0.1, abs=1e-6)
        assert out[2] == pytest.approx(0.02 + 0.1, abs=1e-6)

    def test_amplitude_pic_jour_3(self):
        p = create_pattern_7j(0)
        p["jour_actuel"] = 2
        prob = (0.1, 0.05, 0.02)
        out = apply_patterns(prob, "MZ001", "agressions", {"MZ001": [p]})
        assert out[0] == pytest.approx(0.1 + 0.15, abs=1e-6)
        assert out[1] == pytest.approx(0.05 + 0.15, abs=1e-6)
        assert out[2] == pytest.approx(0.02 + 0.15, abs=1e-6)


class TestPattern60j:
    def test_phase1_amplitude(self):
        p = create_pattern_60j(0)
        p["phase"] = 1
        prob = (0.1, 0.05, 0.02)
        out = apply_patterns(prob, "MZ001", "agressions", {"MZ001": [p]})
        assert out[0] == pytest.approx(0.1 + 0.05, abs=1e-6)

    def test_phase2_amplitude(self):
        p = create_pattern_60j(0)
        p["phase"] = 2
        prob = (0.1, 0.05, 0.02)
        out = apply_patterns(prob, "MZ001", "agressions", {"MZ001": [p]})
        assert out[0] == pytest.approx(0.1 - 0.05, abs=1e-6)

    def test_phase3_amplitude(self):
        p = create_pattern_60j(0)
        p["phase"] = 3
        prob = (0.1, 0.05, 0.02)
        out = apply_patterns(prob, "MZ001", "agressions", {"MZ001": [p]})
        assert out[0] == pytest.approx(0.1 + 0.1, abs=1e-6)


class TestApplicationAgressionsUniquement:
    def test_incendies_accidents_unchanged(self):
        p = create_pattern_7j(0)
        pat = {"MZ001": [p]}
        for t in ("incendies", "accidents"):
            out = apply_patterns((0.2, 0.1, 0.05), "MZ001", t, pat)
            assert out == (0.2, 0.1, 0.05)


class TestPlusieursPatterns:
    def test_combinaison_addition_amplitudes(self):
        p7 = create_pattern_7j(0)
        p7["jour_actuel"] = 0
        p60 = create_pattern_60j(0)
        p60["phase"] = 1
        prob = (0.05, 0.02, 0.01)
        out = apply_patterns(prob, "MZ001", "agressions", {"MZ001": [p7, p60]})
        delta = 0.1 + 0.05
        assert out[0] == pytest.approx(0.05 + delta, abs=1e-6)
        assert out[1] == pytest.approx(0.02 + delta, abs=1e-6)
        assert out[2] == pytest.approx(0.01 + delta, abs=1e-6)


class TestIntegrationCalculerProbabilite:
    def test_patterns_actifs_integration(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.1 for t in TYPES}}
        inc = {mz: {t: (1, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        pat = {mz: [create_pattern_7j(0)]}
        pat[mz][0]["jour_actuel"] = 2
        out = _run(prob_base, inc, intra, inter, voisin, saison, [mz], "intersaison", patterns_actifs=pat)
        assert mz in out
        for t in TYPES:
            assert all(0 <= x <= 1 for x in out[mz][t])

    def test_combinaison_matrices_variables_patterns(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.08 for t in TYPES}}
        inc = {mz: {"agressions": (2, 0, 0), "incendies": (0, 1, 0), "accidents": (0, 0, 0)}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        state = SimpleNamespace(trafic={}, incidents_nuit={}, incidents_alcool={})
        pat = {mz: [create_pattern_60j(0)]}
        pat[mz][0]["phase"] = 3
        out = _run(prob_base, inc, intra, inter, voisin, saison, [mz], "ete", patterns_actifs=pat, dynamic_state=state)
        assert all(0 <= x <= 1 for t in TYPES for x in out[mz][t])

    def test_probabilites_finales_0_1(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.2 for t in TYPES}}
        inc = {mz: {t: (0, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [])
        saison = _saison_mock(mz)
        p7 = create_pattern_7j(0)
        p7["jour_actuel"] = 2
        p60 = create_pattern_60j(0)
        p60["phase"] = 1
        pat = {mz: [p7, p60]}
        out = _run(prob_base, inc, intra, inter, voisin, saison, [mz], "intersaison", patterns_actifs=pat)
        for t in TYPES:
            assert all(0 <= x <= 1 for x in out[mz][t]), f"{t}: {out[mz][t]}"
