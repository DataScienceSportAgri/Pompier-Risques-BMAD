# Configuration Validation - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Auteur:** Architect (Winston)  
**Statut:** Validé

---

## Vue d'Ensemble

Ce document décrit la validation de configuration au démarrage pour éviter les erreurs runtime.

**Objectif:** Valider configuration au démarrage pour éviter erreurs runtime.

**Validation effectuée:**
1. **Structure:** Sections requises présentes
2. **Valeurs:** Types et plages avec Pydantic
3. **Chemins:** Existence fichiers/dossiers
4. **Cohérence:** Scénarios, paramètres cohérents

---

## ConfigValidator

```python
# src/core/config/config_validator.py
from typing import Dict, List, Tuple
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum
import logging

class ScenarioType(str, Enum):
    PESSIMISTE = "pessimiste"
    MOYEN = "moyen"
    OPTIMISTE = "optimiste"

class VariabiliteType(str, Enum):
    FAIBLE = "faible"
    MOYEN = "moyen"
    IMPORTANT = "important"

class SimulationConfig(BaseModel):
    """Schéma de validation pour config simulation."""
    
    default_days: int = Field(..., ge=1, le=10000)
    default_runs: int = Field(..., ge=1, le=100)
    speed_per_day_seconds: float = Field(..., gt=0, le=10)
    seed_default: int = Field(..., ge=0)
    
    class Config:
        use_enum_values = True

class ScenarioConfig(BaseModel):
    """Schéma validation scénarios."""
    
    facteur_intensite: float = Field(..., gt=0, le=5)
    proba_crise: float = Field(..., ge=0, le=1)

class ConfigValidator:
    """Valide la configuration au démarrage."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Valide la configuration.
        
        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # 1. Vérifier fichier existe
        if not self.config_path.exists():
            self.errors.append(f"Fichier config introuvable: {self.config_path}")
            return False, self.errors, self.warnings
        
        # 2. Charger et parser YAML
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Erreur parsing YAML: {e}")
            return False, self.errors, self.warnings
        
        # 3. Valider structure
        self._validate_structure(config)
        
        # 4. Valider valeurs
        self._validate_values(config)
        
        # 5. Valider chemins
        self._validate_paths(config)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_structure(self, config: dict) -> None:
        """Valide la structure de base."""
        required_sections = ['simulation', 'scenarios', 'microzones', 'golden_hour', 'ml']
        
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Section manquante: {section}")
    
    def _validate_values(self, config: dict) -> None:
        """Valide les valeurs avec Pydantic."""
        try:
            sim_config = SimulationConfig(**config.get('simulation', {}))
        except Exception as e:
            self.errors.append(f"Erreur validation simulation: {e}")
        
        # Validation scénarios
        for scenario_name, scenario_data in config.get('scenarios', {}).items():
            try:
                ScenarioConfig(**scenario_data)
            except Exception as e:
                self.errors.append(f"Erreur validation scénario {scenario_name}: {e}")
    
    def _validate_paths(self, config: dict) -> None:
        """Valide que les chemins existent."""
        paths_config = config.get('paths', {})
        
        for path_name, path_str in paths_config.items():
            path = Path(path_str)
            if not path.exists() and path_name in ['data_source', 'data_patterns']:
                self.warnings.append(f"Chemin n'existe pas: {path_str} (sera créé)")
            elif not path.exists():
                self.errors.append(f"Chemin requis introuvable: {path_str}")

# Usage
def load_and_validate_config(config_path: Path) -> dict:
    """Charge et valide la config."""
    validator = ConfigValidator(config_path)
    is_valid, errors, warnings = validator.validate()
    
    if warnings:
        for warning in warnings:
            logging.warning(warning)
    
    if not is_valid:
        error_msg = "Erreurs de configuration:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    # Charger config validée
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
```

---

## Erreurs Détectées

| Erreur | Détection | Action |
|--------|-----------|--------|
| **Fichier introuvable** | `config_path.exists() == False` | Erreur bloquante |
| **Erreur parsing YAML** | `yaml.YAMLError` | Erreur bloquante |
| **Section manquante** | Section absente de `required_sections` | Erreur bloquante |
| **Valeur hors plage** | Pydantic validation (ex: `default_days < 1`) | Erreur bloquante |
| **Chemin introuvable** | `Path.exists() == False` | Erreur ou warning selon contexte |

---

## Intégration au Démarrage

```python
# main.py
from pathlib import Path
from src.core.config.config_validator import load_and_validate_config

def main():
    # Validation config au démarrage
    config_path = Path("config/config.yaml")
    try:
        config = load_and_validate_config(config_path)
        print("✅ Configuration validée")
    except ValueError as e:
        print(f"❌ Erreur configuration: {e}")
        return
    
    # ... suite du démarrage ...
```

---

**Fin du document**
