"""
Tests application matrices fixes aux probabilités (Story 1.4.4.3).

- Intra-type, inter-type, voisin, saisonnalité
- Ordre d'application, probabilités [0,1]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
SOURCE_DATA = ROOT / "data" / "source_data"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.probability import (
    apply_intra_type,
    apply_inter_type,
    apply_voisin,
    apply_saisonnalite,
    calculer_probabilite_incidents_J1,
)
from core.probability._loader import load_matrices_for_probability

TYPES = ("agressions", "incendies", "accidents")


def _mat_intra_identite():
    """Matrice 3×3 identité (somme lignes = 1)."""
    return np.eye(3)


def _mat_intra_exemple():
    """Matrice ex. bénin→bénin 0.85, bénin→moyen 0.12, bénin→grave 0.03."""
    m = np.zeros((3, 3))
    m[0] = [0.85, 0.12, 0.03]
    m[1] = [0.10, 0.75, 0.15]
    m[2] = [0.05, 0.20, 0.75]
    return m


def _inter_mock(mz: str):
    """Inter-type mock : incendie → accidents [0.12, 0.08, 0.05]."""
    return {
        mz: {
            "agressions": {"incendies": [0.05, 0.03, 0.01], "accidents": [0.06, 0.04, 0.02]},
            "incendies": {"agressions": [0.04, 0.02, 0.01], "accidents": [0.08, 0.05, 0.02]},
            "accidents": {"agressions": [0.10, 0.06, 0.03], "incendies": [0.12, 0.08, 0.05]},
        }
    }


def _voisin_mock(mz: str, voisins: list[str]):
    return {
        mz: {"voisins": voisins, "poids_influence": [1.0 / 8] * 8, "seuil_activation": 5}
    }


def _saison_mock(mz: str):
    return {
        mz: {
            t: {"hiver": 0.9, "intersaison": 1.0, "ete": 1.1}
            for t in TYPES
        }
    }


# ---- Intra-type ----


class TestApplyIntraType:
    def test_intra_somme_ligne_conserve(self):
        m = _mat_intra_exemple()
        prob_base = 0.2
        incidents = (1, 0, 0)  # dominant bénin → row 0
        out = apply_intra_type(prob_base, incidents, m)
        assert abs(sum(out) - prob_base) < 1e-6
        assert all(0 <= x <= 1 for x in out)

    def test_intra_dominant_grave(self):
        m = _mat_intra_exemple()
        prob_base = 0.1
        incidents = (0, 0, 2)  # dominant grave → row 2
        out = apply_intra_type(prob_base, incidents, m)
        assert out[2] >= out[0] and out[2] >= out[1]
        assert all(0 <= x <= 1 for x in out)

    def test_intra_sans_incidents_row_zero(self):
        m = _mat_intra_exemple()
        out = apply_intra_type(0.15, (0, 0, 0), m)
        assert sum(out) == pytest.approx(0.15)
        assert all(0 <= x <= 1 for x in out)


# ---- Inter-type ----


class TestApplyInterType:
    def test_inter_incendie_accidents(self):
        mz = "MZ001"
        inter = _inter_mock(mz)
        prob = (0.05, 0.03, 0.02)
        inc = {mz: {"incendies": (0, 0, 1), "agressions": (0, 0, 0), "accidents": (0, 0, 0)}}
        out = apply_inter_type(prob, inc, inter, mz, "accidents")
        assert out[0] >= prob[0] and out[1] >= prob[1] and out[2] >= prob[2]
        assert all(0 <= x <= 1 for x in out)

    def test_inter_sans_autre_type_identique(self):
        mz = "MZ001"
        inter = _inter_mock(mz)
        prob = (0.1, 0.05, 0.02)
        inc = {mz: {t: (0, 0, 0) for t in TYPES}}
        out = apply_inter_type(prob, inc, inter, mz, "accidents")
        assert out == prob


# ---- Voisin ----


class TestApplyVoisin:
    def test_voisin_sous_seuil_pas_effet(self):
        mz = "MZ001"
        voisins = [f"MZ{i:03d}" for i in range(2, 10)]
        mat = _voisin_mock(mz, voisins)
        inc = {v: {t: (0, 0, 0) for t in TYPES} for v in [mz] + voisins}
        prob = (0.2, 0.1, 0.05)
        out = apply_voisin(prob, inc, mat, mz)
        assert out == prob

    def test_voisin_au_dessus_seuil_effet(self):
        mz = "MZ001"
        voisins = [f"MZ{i:03d}" for i in range(2, 10)]
        mat = _voisin_mock(mz, voisins)
        inc = {mz: {t: (0, 0, 0) for t in TYPES}}
        for v in voisins:
            inc[v] = {"agressions": (2, 2, 2), "incendies": (0, 0, 0), "accidents": (0, 0, 0)}
        # pondéré 8 * (0.2*2 + 0.5*2 + 1*2) = 8 * 3.4 > 5
        prob = (0.2, 0.1, 0.05)
        out = apply_voisin(prob, inc, mat, mz)
        assert out[0] > prob[0] and out[1] > prob[1] and out[2] > prob[2]
        assert all(0 <= x <= 1 for x in out)


# ---- Saisonnalité ----


class TestApplySaisonnalite:
    def test_saison_facteur_ete(self):
        mz = "MZ001"
        saison = _saison_mock(mz)
        prob = (0.2, 0.1, 0.05)
        out = apply_saisonnalite(prob, saison, mz, "agressions", "ete")
        assert out[0] == pytest.approx(prob[0] * 1.1)
        assert all(0 <= x <= 1 for x in out)

    def test_saison_intersaison_identique(self):
        mz = "MZ001"
        saison = _saison_mock(mz)
        prob = (0.2, 0.1, 0.05)
        out = apply_saisonnalite(prob, saison, mz, "agressions", "intersaison")
        assert out == prob


# ---- Calcul complet ----


class TestCalculerProbabiliteIncidentsJ1:
    def test_ordre_application_et_bornes(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.1 for t in TYPES}}
        inc = {mz: {t: (1, 0, 0) for t in TYPES}}
        intra = {mz: {t: _mat_intra_exemple() for t in TYPES}}
        inter = _inter_mock(mz)
        voisin = _voisin_mock(mz, [f"MZ{i:03d}" for i in range(2, 10)])
        for v in voisin[mz]["voisins"]:
            inc[v] = {t: (0, 0, 0) for t in TYPES}
        saison = _saison_mock(mz)
        out = calculer_probabilite_incidents_J1(
            prob_base, inc, intra, inter, voisin, saison, [mz], "intersaison"
        )
        assert mz in out
        for t in TYPES:
            p = out[mz][t]
            assert len(p) == 3
            assert all(0 <= x <= 1 for x in p)

    def test_combinaison_toutes_matrices(self):
        mz = "MZ001"
        prob_base = {mz: {t: 0.08 for t in TYPES}}
        inc = {mz: {"agressions": (2, 0, 0), "incendies": (0, 1, 0), "accidents": (0, 0, 0)}}
        intra = {mz: {t: _mat_intra_exemple() for t in TYPES}}
        inter = _inter_mock(mz)
        voisins = [f"MZ{i:03d}" for i in range(2, 10)]
        voisin = _voisin_mock(mz, voisins)
        for v in voisins:
            inc[v] = {t: (0, 0, 0) for t in TYPES}
        saison = _saison_mock(mz)
        out = calculer_probabilite_incidents_J1(
            prob_base, inc, intra, inter, voisin, saison, [mz], "ete"
        )
        assert all(0 <= x <= 1 for t in TYPES for x in out[mz][t])


# ---- Loader et intégration (IV1, IV2) ----


class TestLoader:
    def test_load_matrices_if_present(self):
        if not SOURCE_DATA.exists():
            pytest.skip("data/source_data absent")
        m = load_matrices_for_probability(SOURCE_DATA)
        for k in ("matrices_intra_type", "matrices_inter_type", "matrices_voisin", "matrices_saisonnalite"):
            if k in m:
                assert isinstance(m[k], dict)

    def test_calculer_avec_matrices_chargees(self):
        """IV1–IV2 : matrices chargées, probas modulées dans [0,1]."""
        if not SOURCE_DATA.exists():
            pytest.skip("data/source_data absent")
        m = load_matrices_for_probability(SOURCE_DATA)
        for k in ("matrices_intra_type", "matrices_inter_type", "matrices_voisin", "matrices_saisonnalite"):
            if k not in m or not m[k]:
                pytest.skip(f"matrices {k} manquantes")
        mz_ids = list(m["matrices_intra_type"].keys())[:3]
        prob_base = {mz: {t: 0.1 for t in TYPES} for mz in mz_ids}
        inc = {mz: {t: (1, 0, 0) for t in TYPES} for mz in mz_ids}
        for mz in mz_ids:
            v = m["matrices_voisin"].get(mz, {}).get("voisins", [])
            for u in v:
                if u not in inc:
                    inc[u] = {t: (0, 0, 0) for t in TYPES}
        out = calculer_probabilite_incidents_J1(
            prob_base,
            inc,
            m["matrices_intra_type"],
            m["matrices_inter_type"],
            m["matrices_voisin"],
            m["matrices_saisonnalite"],
            mz_ids,
            "intersaison",
        )
        for mz in mz_ids:
            for t in TYPES:
                p = out[mz][t]
                assert all(0 <= x <= 1 for x in p), f"{mz}/{t}: {p}"
