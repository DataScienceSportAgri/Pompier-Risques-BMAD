"""
Tests intégration variables d'état dans calcul probabilités (Story 1.4.4.4).

- Trafic > 0.7 → +15% accidents/agressions
- Incidents nuit > 2 (seuil) → +10%
- Incidents alcool > 2 (seuil) → +8%
- Combinaison, probabilités finales [0,1]
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
    apply_variables_etat,
    SEUIL_TRAFIC_HAUT,
    SEUIL_INCIDENTS_NUIT,
    SEUIL_INCIDENTS_ALCOOL,
    EFFET_TRAFIC,
    EFFET_NUIT,
    EFFET_ALCOOL,
)

TYPES = ("agressions", "incendies", "accidents")


def _mat_intra():
    m = np.zeros((3, 3))
    m[0] = [0.85, 0.12, 0.03]
    m[1] = [0.10, 0.75, 0.15]
    m[2] = [0.05, 0.20, 0.75]
    return m


def _inter_mock(mz: str):
    return {
        mz: {
            t: {s: [0.02, 0.02, 0.01] for s in TYPES if s != t}
            for t in TYPES
        }
    }


def _voisin_mock(mz: str, voisins: list):
    return {mz: {"voisins": voisins, "poids_influence": [1.0 / 8] * 8, "seuil_activation": 5}}


def _saison_mock(mz: str):
    return {mz: {t: {"hiver": 1.0, "intersaison": 1.0, "ete": 1.0} for t in TYPES}}


def _dynamic_state(trafic=None, incidents_nuit=None, incidents_alcool=None):
    return SimpleNamespace(
        trafic=trafic or {},
        incidents_nuit=incidents_nuit or {},
        incidents_alcool=incidents_alcool or {},
    )


def _run_calcul(mz: str, prob_base: dict, inc: dict, intra, inter, voisin, matrices_saison, state=None, saison_str: str = "intersaison"):
    voisins = [f"MZ{i:03d}" for i in range(2, 10)]
    inc = dict(inc)
    for v in voisins:
        if v not in inc:
            inc[v] = {t: (0, 0, 0) for t in TYPES}
    return calculer_probabilite_incidents_J1(
        prob_base, inc, intra, inter, voisin, matrices_saison, [mz], saison_str, dynamic_state=state
    )


class TestIntegrationTrafic:
    def test_trafic_eleve_augmente_accidents_agressions(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.12 for t in TYPES}}
        inc = {mz: {t: (1, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        sans = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=None)
        state = _dynamic_state(trafic={mz: 0.8}, incidents_nuit={mz: {t: 0 for t in TYPES}}, incidents_alcool={mz: {t: 0 for t in TYPES}})
        avec = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=state)
        for t in ("agressions", "accidents"):
            assert sum(avec[mz][t]) >= sum(sans[mz][t])
        assert sum(avec[mz]["incendies"]) == pytest.approx(sum(sans[mz]["incendies"]))

    def test_trafic_faible_pas_effet(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.1 for t in TYPES}}
        inc = {mz: {t: (0, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        state = _dynamic_state(trafic={mz: 0.5}, incidents_nuit={mz: {t: 0 for t in TYPES}}, incidents_alcool={mz: {t: 0 for t in TYPES}})
        out = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=state)
        assert all(0 <= x <= 1 for t in TYPES for x in out[mz][t])


class TestIntegrationIncidentsNuit:
    def test_nuit_au_dessus_seuil_augmente(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.1 for t in TYPES}}
        inc = {mz: {t: (0, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        sans = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=None)
        nuit_3 = {mz: {"agressions": 1, "incendies": 1, "accidents": 1}}
        state = _dynamic_state(trafic={mz: 0.0}, incidents_nuit=nuit_3, incidents_alcool={mz: {t: 0 for t in TYPES}})
        avec = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=state)
        assert sum(avec[mz]["agressions"]) >= sum(sans[mz]["agressions"])
        assert all(0 <= x <= 1 for t in TYPES for x in avec[mz][t])

    def test_seuil_nuit_egal_2(self):
        assert SEUIL_INCIDENTS_NUIT == 2


class TestIntegrationIncidentsAlcool:
    def test_alcool_au_dessus_seuil_augmente(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.1 for t in TYPES}}
        inc = {mz: {t: (0, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        sans = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=None)
        alcool_3 = {mz: {"agressions": 1, "incendies": 1, "accidents": 1}}
        state = _dynamic_state(trafic={mz: 0.0}, incidents_nuit={mz: {t: 0 for t in TYPES}}, incidents_alcool=alcool_3)
        avec = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=state)
        assert sum(avec[mz]["agressions"]) >= sum(sans[mz]["agressions"])
        assert all(0 <= x <= 1 for t in TYPES for x in avec[mz][t])

    def test_seuil_alcool_egal_2(self):
        assert SEUIL_INCIDENTS_ALCOOL == 2


class TestIntegrationCombinaison:
    def test_toutes_variables_ensemble(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.08 for t in TYPES}}
        inc = {mz: {t: (1, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        state = _dynamic_state(
            trafic={mz: 0.8},
            incidents_nuit={mz: {"agressions": 2, "incendies": 1, "accidents": 0}},
            incidents_alcool={mz: {"agressions": 1, "incendies": 0, "accidents": 2}},
        )
        out = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=state)
        for t in TYPES:
            assert all(0 <= x <= 1 for x in out[mz][t])

    def test_apply_variables_etat_direct(self):
        p = (0.2, 0.1, 0.05)
        trafic = {"MZ001": 0.8}
        nuit = {"MZ001": {"agressions": 3, "incendies": 0, "accidents": 0}}
        alcool = {"MZ001": {"agressions": 0, "incendies": 0, "accidents": 0}}
        out = apply_variables_etat(p, "MZ001", "accidents", trafic, nuit, alcool)
        assert out[0] >= p[0] and out[1] >= p[1] and out[2] >= p[2]
        assert all(0 <= x <= 1 for x in out)


class TestProbabilitesFinales:
    def test_cohérence_valeurs_0_1(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.15 for t in TYPES}}
        inc = {mz: {t: (2, 1, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        saison = _saison_mock(mz)
        state = _dynamic_state(
            trafic={mz: 0.9},
            incidents_nuit={mz: {t: 3 for t in TYPES}},
            incidents_alcool={mz: {t: 3 for t in TYPES}},
        )
        out = _run_calcul(mz, prob_base, inc, intra, inter, voisin, saison, state=state)
        for t in TYPES:
            for x in out[mz][t]:
                assert 0 <= x <= 1, f"{t}: {out[mz][t]}"
