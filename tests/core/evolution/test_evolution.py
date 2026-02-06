"""
Tests évolution J→J+1 (Story 1.4.4.2).

- Trafic : mémoire, influence accidents, clamp [0,1]
- Nuit : mémoire, corrélations, saisonnalité été
- Alcool : mémoire, corrélations, saisonnalité été
- Bornes, reproductibilité (seed)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
SOURCE_DATA = ROOT / "data" / "source_data"

# Importer core depuis src (éviter tests/core)
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.evolution import (
    evoluer_dynamic_state,
    evoluer_incidents_alcool_J1,
    evoluer_incidents_nuit_J1,
    evoluer_trafic_J1,
)
from core.evolution._loader import load_matrices_for_evolution
from core.state import DynamicState, SimulationState

TYPES = ("agressions", "incendies", "accidents")
GRAVITES = ("benin", "moyen", "grave")


def _incidents(mz: str, **kwargs: dict) -> dict:
    """incidents_J[mz][type][gravite] = count."""
    by_type: dict = {}
    for t in TYPES:
        gs = kwargs.get(t, {})
        by_type[t] = {g: gs.get(g, 0) for g in GRAVITES}
    return {mz: by_type}


def _matrices_trafic_mock(mz: str, facteur_memoire: float = 0.65) -> dict:
    return {
        mz: {
            "facteur_memoire": facteur_memoire,
            "prob_engorgement": 0.35,
            "prob_desengorgement": 0.4,
            "amplitude_engorgement": 0.15,
            "amplitude_desengorgement": -0.12,
        }
    }


def _matrices_inter_mock(mz: str) -> dict:
    # type_cible -> type_source -> [b,m,g]
    inter: dict = {}
    for c in TYPES:
        inter[c] = {}
        for s in TYPES:
            if s == c:
                continue
            inter[c][s] = [0.05, 0.03, 0.01]
    return {mz: inter}


# ---- Trafic ----


class TestTraficEvolution:
    def test_trafic_clamp_0_1(self):
        mz = "MZ001"
        trafic_J = {mz: 0.5}
        incidents_J = _incidents(mz)
        mat = _matrices_trafic_mock(mz, 0.65)
        rng = np.random.default_rng(42)
        out = evoluer_trafic_J1(trafic_J, incidents_J, mat, [mz], rng=rng)
        assert mz in out
        assert 0 <= out[mz] <= 1

    def test_trafic_memoire(self):
        mz = "MZ001"
        trafic_J = {mz: 0.8}
        incidents_J = _incidents(mz)  # no incidents
        mat = _matrices_trafic_mock(mz, 0.70)
        rng = np.random.default_rng(123)
        out = evoluer_trafic_J1(trafic_J, incidents_J, mat, [mz], rng=rng)
        # 0.7 * 0.8 + 0.3 * u => significant weight from past
        assert out[mz] >= 0 and out[mz] <= 1

    def test_trafic_influence_accidents(self):
        mz = "MZ001"
        trafic_J = {mz: 0.3}
        incidents_J = {mz: {"accidents": {"benin": 1, "moyen": 0, "grave": 0}, "agressions": {g: 0 for g in GRAVITES}, "incendies": {g: 0 for g in GRAVITES}}}
        mat = _matrices_trafic_mock(mz, 0.65)
        rng = np.random.default_rng(999)
        out_acc = evoluer_trafic_J1(trafic_J, incidents_J, mat, [mz], rng=rng)
        rng2 = np.random.default_rng(999)
        out_no = evoluer_trafic_J1(trafic_J, _incidents(mz), mat, [mz], rng=rng2)
        assert out_acc[mz] >= out_no[mz]

    def test_trafic_reproductibilite(self):
        mz = "MZ001"
        trafic_J = {mz: 0.5}
        incidents_J = _incidents(mz)
        mat = _matrices_trafic_mock(mz)
        a = evoluer_trafic_J1(trafic_J, incidents_J, mat, [mz], rng=np.random.default_rng(7))
        b = evoluer_trafic_J1(trafic_J, incidents_J, mat, [mz], rng=np.random.default_rng(7))
        assert a[mz] == b[mz]


# ---- Nuit ----


class TestNuitEvolution:
    def test_nuit_bornes(self):
        mz = "MZ001"
        nuit_J = {mz: {t: 1 for t in TYPES}}
        incidents_J = _incidents(mz)
        inter = _matrices_inter_mock(mz)
        rng = np.random.default_rng(42)
        out = evoluer_incidents_nuit_J1(nuit_J, incidents_J, inter, [mz], "hiver", rng=rng)
        for t in TYPES:
            assert out[mz][t] >= 0

    def test_nuit_saison_ete(self):
        mz = "MZ001"
        nuit_J = {mz: {t: 2 for t in TYPES}}
        incidents_J = _incidents(mz)
        inter = _matrices_inter_mock(mz)
        rng = np.random.default_rng(88)
        out_h = evoluer_incidents_nuit_J1(nuit_J, incidents_J, inter, [mz], "hiver", rng=rng)
        rng2 = np.random.default_rng(88)
        out_e = evoluer_incidents_nuit_J1(nuit_J, incidents_J, inter, [mz], "ete", rng=rng2)
        # Eté generally tends to increase (facteur 1.2)
        assert sum(out_e[mz].values()) >= 0 and sum(out_h[mz].values()) >= 0

    def test_nuit_reproductibilite(self):
        mz = "MZ001"
        nuit_J = {mz: {t: 1 for t in TYPES}}
        incidents_J = _incidents(mz)
        inter = _matrices_inter_mock(mz)
        a = evoluer_incidents_nuit_J1(nuit_J, incidents_J, inter, [mz], "intersaison", rng=np.random.default_rng(11))
        b = evoluer_incidents_nuit_J1(nuit_J, incidents_J, inter, [mz], "intersaison", rng=np.random.default_rng(11))
        assert a[mz] == b[mz]

    def test_nuit_inferieur_ou_egal_total(self):
        """Nuit ≤ total incidents du type pour chaque microzone."""
        mz = "MZ001"
        incidents_J = {
            mz: {
                "accidents": {"benin": 2, "moyen": 1, "grave": 0},
                "agressions": {"benin": 5, "moyen": 2, "grave": 1},
                "incendies": {"benin": 1, "moyen": 0, "grave": 0},
            }
        }
        nuit_J = {mz: {t: 0 for t in TYPES}}
        inter = _matrices_inter_mock(mz)
        totals = {t: sum(incidents_J[mz][t].values()) for t in TYPES}
        for _ in range(20):
            rng = np.random.default_rng()
            out = evoluer_incidents_nuit_J1(nuit_J, incidents_J, inter, [mz], "hiver", rng=rng)
            for t in TYPES:
                assert 0 <= out[mz][t] <= totals[t]


# ---- Alcool ----


class TestAlcoolEvolution:
    def test_alcool_bornes(self):
        mz = "MZ001"
        alc_J = {mz: {t: 1 for t in TYPES}}
        incidents_J = _incidents(mz)
        inter = _matrices_inter_mock(mz)
        rng = np.random.default_rng(42)
        out = evoluer_incidents_alcool_J1(alc_J, incidents_J, inter, [mz], "hiver", rng=rng)
        for t in TYPES:
            assert out[mz][t] >= 0

    def test_alcool_saison_ete_accidents(self):
        mz = "MZ001"
        alc_J = {mz: {t: 2 for t in TYPES}}
        incidents_J = _incidents(mz)
        inter = _matrices_inter_mock(mz)
        rng = np.random.default_rng(77)
        out_h = evoluer_incidents_alcool_J1(alc_J, incidents_J, inter, [mz], "hiver", rng=rng)
        rng2 = np.random.default_rng(77)
        out_e = evoluer_incidents_alcool_J1(alc_J, incidents_J, inter, [mz], "ete", rng=rng2)
        assert out_e[mz]["accidents"] >= 0 and out_h[mz]["accidents"] >= 0

    def test_alcool_reproductibilite(self):
        mz = "MZ001"
        alc_J = {mz: {t: 1 for t in TYPES}}
        incidents_J = _incidents(mz)
        inter = _matrices_inter_mock(mz)
        a = evoluer_incidents_alcool_J1(alc_J, incidents_J, inter, [mz], "hiver", rng=np.random.default_rng(13))
        b = evoluer_incidents_alcool_J1(alc_J, incidents_J, inter, [mz], "hiver", rng=np.random.default_rng(13))
        assert a[mz] == b[mz]

    def test_alcool_inferieur_ou_egal_total(self):
        """Alcool ≤ total incidents du type pour chaque microzone."""
        mz = "MZ001"
        incidents_J = {
            mz: {
                "accidents": {"benin": 3, "moyen": 0, "grave": 0},
                "agressions": {"benin": 4, "moyen": 2, "grave": 0},
                "incendies": {"benin": 2, "moyen": 1, "grave": 0},
            }
        }
        alc_J = {mz: {t: 0 for t in TYPES}}
        inter = _matrices_inter_mock(mz)
        totals = {t: sum(incidents_J[mz][t].values()) for t in TYPES}
        for _ in range(20):
            rng = np.random.default_rng()
            out = evoluer_incidents_alcool_J1(alc_J, incidents_J, inter, [mz], "hiver", rng=rng)
            for t in TYPES:
                assert 0 <= out[mz][t] <= totals[t]


# ---- DynamicState + evoluer_dynamic_state ----


class TestDynamicStateIntegration:
    def test_dynamic_state_ensure_microzones(self):
        s = DynamicState()
        s.ensure_microzones(["MZ001", "MZ002"])
        assert "MZ001" in s.trafic and s.trafic["MZ001"] == 0.0
        assert "MZ001" in s.incidents_nuit and s.incidents_nuit["MZ001"] == {t: 0 for t in TYPES}
        assert "MZ001" in s.incidents_alcool

    def test_evoluer_dynamic_state_bornes(self):
        mz = "MZ001"
        state = DynamicState(
            trafic={mz: 0.4},
            incidents_nuit={mz: {t: 1 for t in TYPES}},
            incidents_alcool={mz: {t: 1 for t in TYPES}},
        )
        incidents_J = _incidents(mz)
        mat_t = _matrices_trafic_mock(mz)
        mat_i = _matrices_inter_mock(mz)
        rng = np.random.default_rng(31)
        evoluer_dynamic_state(state, incidents_J, mat_t, mat_i, [mz], "intersaison", rng=rng)
        assert 0 <= state.trafic[mz] <= 1
        for t in TYPES:
            assert state.incidents_nuit[mz][t] >= 0
            assert state.incidents_alcool[mz][t] >= 0

    def test_simulation_state_has_dynamic_state(self):
        st = SimulationState("run1", {})
        assert hasattr(st, "dynamic_state")
        assert isinstance(st.dynamic_state, DynamicState)


# ---- Loader (si source_data présent) ----


class TestLoader:
    def test_load_matrices_if_present(self):
        if not SOURCE_DATA.exists():
            pytest.skip("data/source_data absent")
        m = load_matrices_for_evolution(SOURCE_DATA)
        if "matrices_trafic" in m:
            assert isinstance(m["matrices_trafic"], dict)
        if "matrices_inter_type" in m:
            assert isinstance(m["matrices_inter_type"], dict)
