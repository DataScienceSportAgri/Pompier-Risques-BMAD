"""
Tests Story 1.4 : validation du format patterns et chargement des exemples.

- Validation format (load_and_validate, validate_patterns_dir)
- Chargement des exemples pattern_4j, pattern_7j, pattern_60j sans erreur
"""

from pathlib import Path

import pytest

# Racine du projet (fichier dans tests/data/patterns/ -> parents[3])
ROOT = Path(__file__).resolve().parents[3]
PATTERNS_DIR = ROOT / "data" / "patterns"
SCRIPTS_DIR = ROOT / "scripts"


def _add_scripts_path():
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(scope="module")
def validate_module():
    _add_scripts_path()
    from validate_patterns import (
        load_and_validate,
        validate_patterns_dir,
        PATTERN_TYPES,
        TYPES_INCIDENT,
        GRAVITES,
    )
    return {
        "load_and_validate": load_and_validate,
        "validate_patterns_dir": validate_patterns_dir,
        "PATTERN_TYPES": PATTERN_TYPES,
        "TYPES_INCIDENT": TYPES_INCIDENT,
        "GRAVITES": GRAVITES,
    }


class TestValidationFormat:
    """Validation du format patterns (Story 1.4)."""

    def test_patterns_dir_exists(self):
        assert PATTERNS_DIR.is_dir(), f"data/patterns doit exister: {PATTERNS_DIR}"

    def test_example_files_exist(self):
        for name in ("pattern_4j_example.json", "pattern_7j_example.json", "pattern_60j_example.json"):
            p = PATTERNS_DIR / name
            assert p.is_file(), f"Fichier exemple manquant: {name}"

    def test_validate_pattern_4j(self, validate_module):
        load = validate_module["load_and_validate"]
        data = load(PATTERNS_DIR / "pattern_4j_example.json")
        assert data["pattern_type"] == "4j"
        assert "microzones" in data
        assert len(data["microzones"]) >= 1
        m = data["microzones"][0]
        assert "microzone_id" in m and "patterns" in m
        for t in validate_module["TYPES_INCIDENT"]:
            assert t in m["patterns"]
            for g in validate_module["GRAVITES"]:
                assert g in m["patterns"][t]
                b = m["patterns"][t][g]
                assert "probabilite_base" in b
                assert "facteurs_modulation" in b
                assert 0 <= b["probabilite_base"] <= 1

    def test_validate_pattern_7j(self, validate_module):
        load = validate_module["load_and_validate"]
        data = load(PATTERNS_DIR / "pattern_7j_example.json")
        assert data["pattern_type"] == "7j"
        assert "microzones" in data and len(data["microzones"]) >= 1
        fm = data["microzones"][0]["patterns"]["agressions"]["benin"]["facteurs_modulation"]
        assert "jour_semaine" in fm

    def test_validate_pattern_60j(self, validate_module):
        load = validate_module["load_and_validate"]
        data = load(PATTERNS_DIR / "pattern_60j_example.json")
        assert data["pattern_type"] == "60j"
        assert "microzones" in data and len(data["microzones"]) >= 1

    def test_validate_patterns_dir(self, validate_module):
        ok, msgs = validate_module["validate_patterns_dir"](PATTERNS_DIR)
        assert ok, f"Validation dossier patterns échouée: {msgs}"
        assert any("pattern_4j" in m for m in msgs)
        assert any("pattern_7j" in m for m in msgs)
        assert any("pattern_60j" in m for m in msgs)


class TestChargementExemples:
    """Chargement des exemples sans erreur (IV1 Story 1.4)."""

    def test_load_pattern_4j(self, validate_module):
        load = validate_module["load_and_validate"]
        load(PATTERNS_DIR / "pattern_4j_example.json")

    def test_load_pattern_7j(self, validate_module):
        load = validate_module["load_and_validate"]
        load(PATTERNS_DIR / "pattern_7j_example.json")

    def test_load_pattern_60j(self, validate_module):
        load = validate_module["load_and_validate"]
        load(PATTERNS_DIR / "pattern_60j_example.json")

    def test_load_missing_file_raises(self, validate_module):
        load = validate_module["load_and_validate"]
        with pytest.raises(FileNotFoundError):
            load(PATTERNS_DIR / "nonexistent.json")

    def test_load_invalid_json_raises(self, validate_module, tmp_path):
        load = validate_module["load_and_validate"]
        bad = tmp_path / "bad.json"
        bad.write_text("{ invalid")
        with pytest.raises(Exception):  # JSONDecodeError ou autre
            load(bad)


class TestIntegrationVectorsStatic:
    """IV1 Story 1.4 : patterns chargés sans erreur par Story 1.3 (vecteurs statiques)."""

    @pytest.fixture
    def vectors_calc(self):
        pytest.importorskip("pandas")
        _add_scripts_path()
        from precompute_vectors_static import VectorsStaticCalculator
        return VectorsStaticCalculator({})

    def test_load_patterns_from_dir(self, vectors_calc):
        patterns = vectors_calc.load_patterns(PATTERNS_DIR)
        assert "pattern_4j" in patterns or "pattern_7j" in patterns or "pattern_60j" in patterns

    def test_extract_base_probs_from_ref_60j(self, vectors_calc):
        import json
        path = PATTERNS_DIR / "pattern_60j_example.json"
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        probs = vectors_calc._extract_base_probs_from_ref(raw)
        for t in ("agressions", "incendies", "accidents"):
            assert t in probs
            for g in ("benin", "moyen", "grave"):
                assert g in probs[t]
                assert 0 <= probs[t][g] <= 1
