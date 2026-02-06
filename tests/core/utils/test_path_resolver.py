"""
Tests unitaires pour PathResolver.
Story 2.1.4 - Système centralisé de résolution de chemins
"""

import tempfile
from pathlib import Path

import pytest

from src.core.utils.path_resolver import PathResolver


class TestPathResolver:
    """Tests pour PathResolver."""
    
    def test_get_project_root(self):
        """Test détection de la racine du projet."""
        root = PathResolver.get_project_root()
        
        assert root.exists()
        assert (root / "README.md").exists() or (root / "config" / "config.yaml").exists()
    
    def test_resolve_simple_path(self):
        """Test résolution d'un chemin simple."""
        path = PathResolver.resolve("config", "config.yaml")
        
        assert path.is_absolute()
        assert path.name == "config.yaml"
        assert path.parent.name == "config"
    
    def test_resolve_single_string_path(self):
        """Test résolution avec un seul argument contenant des séparateurs."""
        path = PathResolver.resolve("config/config.yaml")
        
        assert path.is_absolute()
        assert path.name == "config.yaml"
        assert path.parent.name == "config"
    
    def test_data_source(self):
        """Test résolution chemin data/source_data."""
        path = PathResolver.data_source("microzones.pkl")
        
        assert path.is_absolute()
        assert path.name == "microzones.pkl"
        assert "source_data" in str(path)
    
    def test_data_patterns(self):
        """Test résolution chemin data/patterns."""
        path = PathResolver.data_patterns("pattern_7j.json")
        
        assert path.is_absolute()
        assert path.name == "pattern_7j.json"
        assert "patterns" in str(path)
    
    def test_data_intermediate(self):
        """Test résolution chemin data/intermediate."""
        path = PathResolver.data_intermediate("run_001", "generation", "vecteurs.pkl")
        
        assert path.is_absolute()
        assert path.name == "vecteurs.pkl"
        assert "intermediate" in str(path)
        assert "run_001" in str(path)
        assert "generation" in str(path)
    
    def test_data_models(self):
        """Test résolution chemin data/models."""
        path = PathResolver.data_models("rf_model.joblib")
        
        assert path.is_absolute()
        assert path.name == "rf_model.joblib"
        assert "models" in str(path)
    
    def test_config_file(self):
        """Test résolution chemin config."""
        path = PathResolver.config_file("config.yaml")
        
        assert path.is_absolute()
        assert path.name == "config.yaml"
        assert "config" in str(path)
    
    def test_scripts_dir(self):
        """Test résolution chemin scripts."""
        path = PathResolver.scripts_dir()
        
        assert path.is_absolute()
        assert path.name == "scripts" or "scripts" in str(path)
    
    def test_relative_to_root(self):
        """Test conversion en chemin relatif depuis la racine."""
        root = PathResolver.get_project_root()
        test_file = root / "config" / "config.yaml"
        
        relative = PathResolver.relative_to_root(test_file)
        
        assert relative == "config/config.yaml" or relative == "config\\config.yaml"
    
    def test_relative_to_root_absolute_outside(self):
        """Test conversion d'un chemin absolu en dehors du projet."""
        # Créer un chemin temporaire en dehors du projet
        with tempfile.TemporaryDirectory() as tmpdir:
            outside_path = Path(tmpdir) / "file.txt"
            relative = PathResolver.relative_to_root(outside_path)
            
            # Devrait retourner le chemin tel quel
            assert str(outside_path) in relative or relative == str(outside_path)


class TestPathResolverConventions:
    """Tests pour vérifier les conventions de nommage."""
    
    def test_convention_source_data(self):
        """Test convention nommage source data."""
        # Format attendu : {nom}_{version}.pkl
        path = PathResolver.data_source("microzones_1.0.pkl")
        
        assert path.suffix == ".pkl"
        assert "microzones" in path.stem
        assert "1.0" in path.stem
    
    def test_convention_intermediate(self):
        """Test convention nommage intermediate."""
        # Format attendu : run_{run_id}/{type}/{nom}.pkl
        path = PathResolver.data_intermediate("run_001", "generation", "vecteurs.pkl")
        
        assert path.suffix == ".pkl"
        assert "run_001" in str(path)
        assert "generation" in str(path)
        assert path.name == "vecteurs.pkl"
    
    def test_convention_safe_state(self):
        """Test convention nommage safe state."""
        # Format attendu : run_{run_id}_day_{day}.pkl
        path = PathResolver.resolve("data", "safe_state", "run_001_day_150.pkl")
        
        assert path.suffix == ".pkl"
        assert "run_001" in path.stem
        assert "day_150" in path.stem
    
    def test_convention_models(self):
        """Test convention nommage models."""
        # Format attendu : {algo}_{numero}_{params}.joblib
        path = PathResolver.data_models("rf_001_default.joblib")
        
        assert path.suffix == ".joblib"
        assert "rf" in path.stem
        assert "001" in path.stem
