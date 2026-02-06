"""
Tests unitaires pour la validation de configuration avec Pydantic.
Story 2.1.3 - Validation configuration avec Pydantic
"""

from pathlib import Path
from typing import Dict

import pytest

from pydantic import ValidationError

from src.core.config.config_validator import (
    Config,
    MLConfig,
    PathsConfig,
    PrecomputeConfig,
    ScenarioConfig,
    ScenariosConfig,
    SimulationConfig,
    validate_config_dict,
)


class TestPathsConfig:
    """Tests pour PathsConfig."""
    
    def test_validation_paths_exist(self):
        """Test que les chemins doivent exister."""
        # Utiliser des chemins qui existent
        valid_paths = {
            "data_source": "data/source_data",
            "data_patterns": "data/patterns",
            "data_intermediate": "data/intermediate",
            "data_models": "data/models",
            "scripts": "scripts"
        }
        
        # Vérifier que les chemins existent avant de tester
        for key, path in valid_paths.items():
            if not Path(path).exists():
                pytest.skip(f"Chemin {path} n'existe pas, test ignoré")
        
        config = PathsConfig(**valid_paths)
        assert config.data_source == "data/source_data"
    
    def test_validation_paths_missing(self):
        """Test que les chemins manquants lèvent une erreur."""
        invalid_paths = {
            "data_source": "data/nonexistent",
            "data_patterns": "data/patterns",
            "data_intermediate": "data/intermediate",
            "data_models": "data/models",
            "scripts": "scripts"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PathsConfig(**invalid_paths)
        
        errors = exc_info.value.errors()
        assert any("introuvable" in str(error.get('msg', '')) for error in errors)


class TestSimulationConfig:
    """Tests pour SimulationConfig."""
    
    def test_validation_values(self):
        """Test validation des valeurs."""
        config = SimulationConfig(
            default_days=365,
            default_runs=50,
            speed_per_day_seconds=0.33,
            seed_default=42
        )
        assert config.default_days == 365
    
    def test_validation_days_out_of_range(self):
        """Test que les jours hors plage lèvent une erreur."""
        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(
                default_days=0,  # Trop petit
                default_runs=50,
                speed_per_day_seconds=0.33,
                seed_default=42
            )
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 1" in str(error.get('msg', '')) for error in errors)
    
    def test_validation_runs_out_of_range(self):
        """Test que les runs hors plage lèvent une erreur."""
        with pytest.raises(ValidationError) as exc_info:
            SimulationConfig(
                default_days=365,
                default_runs=2000,  # Trop grand
                speed_per_day_seconds=0.33,
                seed_default=42
            )
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 1000" in str(error.get('msg', '')) for error in errors)


class TestScenarioConfig:
    """Tests pour ScenarioConfig."""
    
    def test_validation_values(self):
        """Test validation des valeurs."""
        config = ScenarioConfig(
            facteur_intensite=1.3,
            proba_crise=0.15,
            variabilite_locale=0.5
        )
        assert config.facteur_intensite == 1.3
    
    def test_validation_proba_crise_out_of_range(self):
        """Test que proba_crise hors [0,1] lève une erreur."""
        with pytest.raises(ValidationError) as exc_info:
            ScenarioConfig(
                facteur_intensite=1.3,
                proba_crise=1.5,  # Trop grand
                variabilite_locale=0.5
            )
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 1" in str(error.get('msg', '')) for error in errors)


class TestScenariosConfig:
    """Tests pour ScenariosConfig."""
    
    def test_validation_all_scenarios_required(self):
        """Test que tous les scénarios sont requis."""
        config = ScenariosConfig(
            pessimiste=ScenarioConfig(1.3, 0.15, 0.5),
            moyen=ScenarioConfig(1.0, 0.10, 0.3),
            optimiste=ScenarioConfig(0.7, 0.05, 0.1)
        )
        assert config.pessimiste.facteur_intensite == 1.3
        assert config.moyen.facteur_intensite == 1.0
        assert config.optimiste.facteur_intensite == 0.7
    
    def test_validation_missing_scenario(self):
        """Test qu'un scénario manquant lève une erreur."""
        with pytest.raises(ValidationError):
            ScenariosConfig(
                pessimiste=ScenarioConfig(1.3, 0.15, 0.5),
                moyen=ScenarioConfig(1.0, 0.10, 0.3)
                # optimiste manquant
            )


class TestMLConfig:
    """Tests pour MLConfig."""
    
    def test_validation_values(self):
        """Test validation des valeurs."""
        config = MLConfig(
            features_central=18,
            features_voisins=4,
            total_features=90,
            algorithmes_regression=["RandomForest", "Ridge"],
            algorithmes_classification=["LogReg", "XGBoost"],
            metrics={
                "regression": ["MAE", "RMSE", "R2"],
                "classification": ["Accuracy", "Precision", "Recall", "F1"]
            }
        )
        assert config.features_central == 18
    
    def test_validation_algorithms_not_empty(self):
        """Test que les listes d'algorithmes ne peuvent pas être vides."""
        with pytest.raises(ValidationError) as exc_info:
            MLConfig(
                features_central=18,
                features_voisins=4,
                total_features=90,
                algorithmes_regression=[],  # Vide
                algorithmes_classification=["LogReg"],
                metrics={"regression": ["MAE"], "classification": ["Accuracy"]}
            )
        
        errors = exc_info.value.errors()
        assert any("vide" in str(error.get('msg', '')).lower() for error in errors)
    
    def test_validation_total_features_coherence(self):
        """Test cohérence total_features."""
        # total_features trop faible
        with pytest.raises(ValidationError) as exc_info:
            MLConfig(
                features_central=18,
                features_voisins=4,
                total_features=10,  # Trop faible (18 + 4*4 = 34 minimum)
                algorithmes_regression=["RandomForest"],
                algorithmes_classification=["LogReg"],
                metrics={"regression": ["MAE"], "classification": ["Accuracy"]}
            )
        
        errors = exc_info.value.errors()
        assert any("trop faible" in str(error.get('msg', '')).lower() for error in errors)


class TestPrecomputeConfig:
    """Tests pour PrecomputeConfig."""
    
    def test_validation_enabled_keys(self):
        """Test validation des clés enabled."""
        config = PrecomputeConfig(
            enabled={
                "distances": True,
                "microzones": True,
                "vectors_static": True,
                "prix_m2": True,
                "congestion_static": True
            }
        )
        assert config.enabled["distances"] is True
    
    def test_validation_invalid_enabled_keys(self):
        """Test que des clés invalides dans enabled lèvent une erreur."""
        with pytest.raises(ValidationError) as exc_info:
            PrecomputeConfig(
                enabled={
                    "distances": True,
                    "invalid_key": True  # Clé invalide
                }
            )
        
        errors = exc_info.value.errors()
        assert any("inattendues" in str(error.get('msg', '')).lower() for error in errors)


class TestConfig:
    """Tests pour Config complet."""
    
    def create_valid_config_dict(self) -> Dict:
        """Crée un dictionnaire de configuration valide."""
        return {
            "paths": {
                "data_source": "data/source_data",
                "data_patterns": "data/patterns",
                "data_intermediate": "data/intermediate",
                "data_models": "data/models",
                "scripts": "scripts"
            },
            "simulation": {
                "default_days": 365,
                "default_runs": 50,
                "speed_per_day_seconds": 0.33,
                "seed_default": 42
            },
            "scenarios": {
                "pessimiste": {
                    "facteur_intensite": 1.3,
                    "proba_crise": 0.15,
                    "variabilite_locale": 0.5
                },
                "moyen": {
                    "facteur_intensite": 1.0,
                    "proba_crise": 0.10,
                    "variabilite_locale": 0.3
                },
                "optimiste": {
                    "facteur_intensite": 0.7,
                    "proba_crise": 0.05,
                    "variabilite_locale": 0.1
                }
            },
            "microzones": {
                "nombre": 100,
                "source": "IRIS",
                "aggregation_method": "auto"
            },
            "golden_hour": {
                "seuil_minutes": 60,
                "facteur_congestion_base": 1.0,
                "facteur_stress_base": 1.0
            },
            "ml": {
                "features_central": 18,
                "features_voisins": 4,
                "total_features": 90,
                "algorithmes_regression": ["RandomForest", "Ridge"],
                "algorithmes_classification": ["LogReg", "XGBoost"],
                "metrics": {
                    "regression": ["MAE", "RMSE", "R2"],
                    "classification": ["Accuracy", "Precision", "Recall", "F1"]
                }
            },
            "precompute": {
                "enabled": {
                    "distances": True,
                    "microzones": True,
                    "vectors_static": True,
                    "prix_m2": True,
                    "congestion_static": True
                },
                "distances": {
                    "source_casernes": "internet",
                    "source_hopitaux": "internet",
                    "method": "geodesic"
                },
                "microzones": {
                    "source": "IRIS",
                    "output_format": "pickle"
                },
                "vectors_static": {
                    "patterns_dir": "data/patterns",
                    "default_if_missing": True
                },
                "prix_m2": {
                    "source": "internet_or_generated",
                    "fallback_generation": True
                },
                "congestion_static": {
                    "include_seasonality": True,
                    "base_factors": True
                }
            }
        }
    
    def test_validation_structure_complete(self):
        """Test validation structure complète."""
        config_dict = self.create_valid_config_dict()
        
        # Vérifier que les chemins existent
        for key, path in config_dict["paths"].items():
            if not Path(path).exists():
                pytest.skip(f"Chemin {path} n'existe pas, test ignoré")
        
        config = validate_config_dict(config_dict)
        assert config.simulation.default_days == 365
        assert config.scenarios.pessimiste.facteur_intensite == 1.3
    
    def test_validation_missing_section(self):
        """Test qu'une section manquante lève une erreur."""
        config_dict = self.create_valid_config_dict()
        del config_dict["simulation"]  # Section manquante
        
        with pytest.raises(ValidationError) as exc_info:
            validate_config_dict(config_dict)
        
        errors = exc_info.value.errors()
        assert any("simulation" in str(error.get('loc', [])) for error in errors)
    
    def test_validation_invalid_source(self):
        """Test qu'une source invalide lève une erreur."""
        config_dict = self.create_valid_config_dict()
        config_dict["microzones"]["source"] = "INVALID"  # Source invalide
        
        with pytest.raises(ValidationError) as exc_info:
            validate_config_dict(config_dict)
        
        errors = exc_info.value.errors()
        assert any("pattern" in str(error.get('type', '')).lower() for error in errors)
    
    def test_validation_coherence_microzones_source(self):
        """Test cohérence source microzones entre sections."""
        config_dict = self.create_valid_config_dict()
        config_dict["microzones"]["source"] = "OSM"
        config_dict["precompute"]["microzones"]["source"] = "IRIS"  # Incohérence
        
        with pytest.raises(ValidationError) as exc_info:
            validate_config_dict(config_dict)
        
        errors = exc_info.value.errors()
        assert any("incohérence" in str(error.get('msg', '')).lower() for error in errors)
    
    def test_validation_extra_fields_forbidden(self):
        """Test que les champs supplémentaires sont interdits."""
        config_dict = self.create_valid_config_dict()
        config_dict["extra_field"] = "should_fail"  # Champ supplémentaire
        
        with pytest.raises(ValidationError) as exc_info:
            validate_config_dict(config_dict)
        
        errors = exc_info.value.errors()
        assert any("extra" in str(error.get('type', '')).lower() for error in errors)
