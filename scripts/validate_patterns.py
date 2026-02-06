"""
Validation des fichiers patterns Paris (4j, 7j, 60j) – Story 1.4.

Valide le format défini dans docs/patterns-reference.md via Pydantic.
Utilisable en CLI ou importé par run_precompute (--validate-patterns).

Usage:
    python scripts/validate_patterns.py
    python scripts/validate_patterns.py --path data/patterns
    python scripts/validate_patterns.py data/patterns/pattern_4j_example.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

try:
    from pydantic import BaseModel, Field, field_validator, model_validator
except ImportError:
    BaseModel = None  # type: ignore
    Field = None  # type: ignore
    field_validator = None  # type: ignore
    model_validator = None  # type: ignore


# ---------------------------------------------------------------------------
# Constantes alignées avec docs/patterns-reference.md et precompute_matrices
# ---------------------------------------------------------------------------
PATTERN_TYPES = {"4j", "7j", "60j"}
TYPES_INCIDENT = {"agressions", "incendies", "accidents"}
GRAVITES = {"benin", "moyen", "grave"}
REGIMES = {"stable", "deterioration", "crise"}
JOURS_SEMAINE = {"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}


def _check_multipliers(d: Dict[str, Any], context: str) -> None:
    """Vérifie que les multiplicateurs sont > 0."""
    if not isinstance(d, dict):
        raise ValueError(f"{context}: doit être un objet")
    for k, v in d.items():
        if isinstance(v, dict):
            _check_multipliers(v, f"{context}.{k}")
        elif isinstance(v, (int, float)):
            if v <= 0:
                raise ValueError(f"{context}.{k} = {v} : doit être > 0")


# ---------------------------------------------------------------------------
# Modèles Pydantic (optionnel si pydantic absent)
# ---------------------------------------------------------------------------
if BaseModel is not None:

    class GraviteBlock(BaseModel):
        probabilite_base: float
        facteurs_modulation: Dict[str, Any] = Field(default_factory=dict)
        influence_regimes: Optional[Dict[str, float]] = None
        influence_intensites: Optional[Dict[str, float]] = None

        @field_validator("probabilite_base")
        @classmethod
        def prob_in_0_1(cls, v: float) -> float:
            if not (0.0 <= v <= 1.0):
                raise ValueError("probabilite_base doit être entre 0.0 et 1.0")
            return v

        @field_validator("facteurs_modulation")
        @classmethod
        def check_facteurs(cls, v: Dict[str, Any]) -> Dict[str, Any]:
            if not isinstance(v, dict):
                raise ValueError("facteurs_modulation doit être un objet")
            if "regime" not in v or "saison" not in v:
                raise ValueError("facteurs_modulation doit contenir 'regime' et 'saison'")
            for regime_key in ["stable", "deterioration", "crise"]:
                if regime_key not in v.get("regime", {}):
                    raise ValueError(f"facteurs_modulation.regime doit contenir '{regime_key}'")
            _check_multipliers(v, "facteurs_modulation")
            return v

    class TypePatterns(BaseModel):
        agressions: Dict[str, GraviteBlock]
        incendies: Dict[str, GraviteBlock]
        accidents: Dict[str, GraviteBlock]

        @field_validator("agressions", "incendies", "accidents")
        @classmethod
        def check_gravites(cls, v: Dict[str, Any]) -> Dict[str, Any]:
            if not isinstance(v, dict):
                raise ValueError("chaque type doit être un objet benin/moyen/grave")
            for g in GRAVITES:
                if g not in v:
                    raise ValueError(f"gravité '{g}' manquante")
            return v

    class MicrozoneEntry(BaseModel):
        microzone_id: str
        patterns: TypePatterns

    class PatternFile(BaseModel):
        pattern_type: str
        pattern_name: str
        description: Optional[str] = None
        version: str
        created_at: str
        microzones: List[MicrozoneEntry]

        @field_validator("pattern_type")
        @classmethod
        def check_pattern_type(cls, v: str) -> str:
            if v not in PATTERN_TYPES:
                raise ValueError(f"pattern_type doit être parmi {PATTERN_TYPES}")
            return v

        @model_validator(mode="after")
        def check_microzones_non_vide(self) -> "PatternFile":
            if not self.microzones:
                raise ValueError("microzones ne doit pas être vide")
            return self

    def _parse_gravite(raw: Dict[str, Any]) -> GraviteBlock:
        return GraviteBlock(
            probabilite_base=raw["probabilite_base"],
            facteurs_modulation=raw.get("facteurs_modulation", {}),
            influence_regimes=raw.get("influence_regimes"),
            influence_intensites=raw.get("influence_intensites"),
        )

    def _parse_type_patterns(raw: Dict[str, Any]) -> TypePatterns:
        agressions = {g: _parse_gravite(raw["agressions"][g]) for g in GRAVITES}
        incendies = {g: _parse_gravite(raw["incendies"][g]) for g in GRAVITES}
        accidents = {g: _parse_gravite(raw["accidents"][g]) for g in GRAVITES}
        return TypePatterns(agressions=agressions, incendies=incendies, accidents=accidents)

    def _parse_microzone(raw: Dict[str, Any]) -> MicrozoneEntry:
        return MicrozoneEntry(
            microzone_id=raw["microzone_id"],
            patterns=_parse_type_patterns(raw["patterns"]),
        )

    def _parse_pattern_file(raw: Dict[str, Any]) -> PatternFile:
        return PatternFile(
            pattern_type=raw["pattern_type"],
            pattern_name=raw["pattern_name"],
            description=raw.get("description"),
            version=raw["version"],
            created_at=raw["created_at"],
            microzones=[_parse_microzone(m) for m in raw["microzones"]],
        )

else:
    PatternFile = None
    _parse_pattern_file = None


# ---------------------------------------------------------------------------
# Validation sans Pydantic (fallback)
# ---------------------------------------------------------------------------
def _validate_raw(raw: Dict[str, Any]) -> List[str]:
    """Valide la structure sans Pydantic. Retourne la liste d'erreurs (vide si OK)."""
    errs: List[str] = []
    if raw.get("pattern_type") not in PATTERN_TYPES:
        errs.append(f"pattern_type doit être parmi {list(PATTERN_TYPES)}")
    for key in ("pattern_name", "version", "created_at", "microzones"):
        if key not in raw:
            errs.append(f"Champ obligatoire manquant: {key}")
    if "microzones" in raw:
        mz = raw["microzones"]
        if not isinstance(mz, list) or len(mz) == 0:
            errs.append("microzones doit être un tableau non vide")
        else:
            for i, m in enumerate(mz):
                if not isinstance(m, dict):
                    errs.append(f"microzones[{i}] doit être un objet")
                    continue
                if "microzone_id" not in m or "patterns" not in m:
                    errs.append(f"microzones[{i}] doit contenir microzone_id et patterns")
                    continue
                pa = m.get("patterns", {})
                for t in TYPES_INCIDENT:
                    if t not in pa:
                        errs.append(f"microzones[{i}].patterns doit contenir '{t}'")
                        continue
                    for g in GRAVITES:
                        if g not in pa[t]:
                            errs.append(f"microzones[{i}].patterns.{t} doit contenir '{g}'")
                            continue
                        b = pa[t][g]
                        if not isinstance(b, dict):
                            errs.append(f"microzones[{i}].patterns.{t}.{g} doit être un objet")
                            continue
                        pb = b.get("probabilite_base")
                        if not isinstance(pb, (int, float)) or not (0 <= pb <= 1):
                            errs.append(f"microzones[{i}].patterns.{t}.{g}.probabilite_base doit être dans [0,1]")
                        fm = b.get("facteurs_modulation")
                        if not isinstance(fm, dict) or "regime" not in fm or "saison" not in fm:
                            errs.append(f"microzones[{i}].patterns.{t}.{g}.facteurs_modulation doit contenir regime et saison")
    return errs


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------
def load_and_validate(path: Path) -> Dict[str, Any]:
    """
    Charge et valide un fichier pattern JSON.

    Returns:
        Le dictionnaire JSON (structure validée).

    Raises:
        FileNotFoundError: fichier absent
        json.JSONDecodeError: JSON invalide
        ValueError: format ou contraintes non respectés
    """
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("Le fichier doit contenir un objet JSON")

    if _parse_pattern_file is not None:
        _parse_pattern_file(raw)
        return raw
    errs = _validate_raw(raw)
    if errs:
        raise ValueError("Validation échouée:\n  - " + "\n  - ".join(errs))
    return raw


def validate_patterns_dir(patterns_dir: Path) -> tuple[bool, List[str]]:
    """
    Valide tous les JSON dans un dossier (pattern_*_example.json ou pattern_*.json).

    Returns:
        (ok: bool, messages: list)
    """
    messages: List[str] = []
    files = sorted(patterns_dir.glob("pattern_*.json"))
    if not files:
        messages.append(f"Aucun fichier pattern_*.json dans {patterns_dir}")
        return False, messages
    all_ok = True
    for p in files:
        try:
            load_and_validate(p)
            messages.append(f"OK {p.name}")
        except Exception as e:
            all_ok = False
            messages.append(f"ERREUR {p.name}: {e}")
    return all_ok, messages


def run_validate_patterns(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Point d'entrée pour run_precompute (Story 1.4).
    Utilise config['paths']['data_patterns'] ou data/patterns par défaut.

    Returns:
        True si tous les patterns valident, False sinon.
    """
    if config and isinstance(config.get("paths"), dict) and config["paths"].get("data_patterns"):
        base = Path(config["paths"]["data_patterns"])
    else:
        base = Path("data/patterns")
    if not base.is_absolute():
        root = Path(__file__).resolve().parent.parent
        base = root / base
    base.mkdir(parents=True, exist_ok=True)
    ok, msgs = validate_patterns_dir(base)
    for m in msgs:
        if m.startswith("ERREUR"):
            logger.error(m)
        else:
            logger.info(m)
    return ok


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Valider les fichiers patterns Paris (Story 1.4)")
    ap.add_argument("path", nargs="?", default=None, help="Fichier ou dossier (défaut: data/patterns)")
    ap.add_argument("--path", "-p", dest="path_opt", default=None, help="Dossier patterns (alias)")
    args = ap.parse_args()
    path_arg = args.path_opt or args.path
    if path_arg is None:
        path_arg = "data/patterns"
    path = Path(path_arg)
    root = Path(__file__).resolve().parent.parent
    if not path.is_absolute():
        path = root / path
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if path.is_file():
        try:
            load_and_validate(path)
            logger.info("OK %s", path.name)
            return 0
        except Exception as e:
            logger.error("ERREUR %s: %s", path.name, e)
            return 1
    ok, msgs = validate_patterns_dir(path)
    for m in msgs:
        print(m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
