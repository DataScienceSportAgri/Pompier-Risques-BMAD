"""
Tests pour le script d'orchestration run_precompute.py (Story 1.1).

Tests:
- Structure des dossiers
- Imports
- Lancement partiel (arguments CLI)
- Configuration YAML
"""

import pytest
import sys
from pathlib import Path
import yaml
import tempfile
import shutil

# Ajouter le répertoire racine au path pour les imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


class TestStructureDossiers:
    """Tests de la structure des dossiers."""
    
    def test_dossier_scripts_existe(self):
        """Vérifie que le dossier scripts/ existe."""
        scripts_dir = ROOT_DIR / "scripts"
        assert scripts_dir.exists(), "Le dossier scripts/ doit exister"
        assert scripts_dir.is_dir(), "scripts/ doit être un dossier"
    
    def test_dossier_data_source_data_existe(self):
        """Vérifie que le dossier data/source_data/ existe."""
        data_dir = ROOT_DIR / "data" / "source_data"
        assert data_dir.exists(), "Le dossier data/source_data/ doit exister"
        assert data_dir.is_dir(), "data/source_data/ doit être un dossier"
    
    def test_dossier_config_existe(self):
        """Vérifie que le dossier config/ existe."""
        config_dir = ROOT_DIR / "config"
        assert config_dir.exists(), "Le dossier config/ doit exister"
        assert config_dir.is_dir(), "config/ doit être un dossier"
    
    def test_fichier_run_precompute_existe(self):
        """Vérifie que le fichier run_precompute.py existe."""
        script_file = ROOT_DIR / "scripts" / "run_precompute.py"
        assert script_file.exists(), "Le fichier scripts/run_precompute.py doit exister"
        assert script_file.is_file(), "run_precompute.py doit être un fichier"
    
    def test_fichier_config_yaml_existe(self):
        """Vérifie que le fichier config/config.yaml existe."""
        config_file = ROOT_DIR / "config" / "config.yaml"
        assert config_file.exists(), "Le fichier config/config.yaml doit exister"
        assert config_file.is_file(), "config.yaml doit être un fichier"


class TestImports:
    """Tests des imports."""
    
    def test_import_run_precompute(self):
        """Vérifie que le module run_precompute peut être importé."""
        try:
            # Ajouter scripts au path
            scripts_dir = ROOT_DIR / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            
            # Importer les fonctions principales
            from run_precompute import (
                load_config,
                should_run_block,
                run_distances,
                run_microzones,
                run_vectors_static,
                run_prix_m2,
                run_congestion_static,
                run_matrices_correlation,
                run_validate_patterns,
            )
            
            assert callable(load_config)
            assert callable(should_run_block)
            assert callable(run_distances)
            assert callable(run_microzones)
            assert callable(run_vectors_static)
            assert callable(run_prix_m2)
            assert callable(run_congestion_static)
            assert callable(run_matrices_correlation)
            assert callable(run_validate_patterns)
        except ImportError as e:
            pytest.fail(f"Impossible d'importer run_precompute: {e}")
    
    def test_import_yaml(self):
        """Vérifie que PyYAML est disponible."""
        try:
            import yaml
            assert yaml is not None
        except ImportError:
            pytest.fail("PyYAML n'est pas installé. Installez-le avec: pip install pyyaml")


class TestConfigurationYAML:
    """Tests de la configuration YAML."""
    
    def test_config_yaml_valide(self):
        """Vérifie que config/config.yaml est un YAML valide."""
        config_file = ROOT_DIR / "config" / "config.yaml"
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            assert config is not None, "Le fichier config.yaml ne doit pas être vide"
            assert isinstance(config, dict), "Le fichier config.yaml doit être un dictionnaire"
        except yaml.YAMLError as e:
            pytest.fail(f"Erreur parsing YAML: {e}")
    
    def test_config_contient_sections_requises(self):
        """Vérifie que la config contient les sections requises."""
        config_file = ROOT_DIR / "config" / "config.yaml"
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        sections_requises = ['paths', 'simulation', 'scenarios', 'precompute']
        for section in sections_requises:
            assert section in config, f"La section '{section}' doit être présente dans config.yaml"
    
    def test_config_precompute_enabled(self):
        """Vérifie que la section precompute.enabled existe."""
        config_file = ROOT_DIR / "config" / "config.yaml"
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        assert 'precompute' in config, "La section 'precompute' doit être présente"
        assert 'enabled' in config['precompute'], "La section 'precompute.enabled' doit être présente"
        
        enabled = config['precompute']['enabled']
        blocs_attendus = ['distances', 'microzones', 'vectors_static', 'prix_m2', 'congestion_static']
        for bloc in blocs_attendus:
            assert bloc in enabled, f"Le bloc '{bloc}' doit être présent dans precompute.enabled"


class TestLancementPartiel:
    """Tests du lancement partiel (arguments CLI)."""
    
    def test_load_config_fonctionne(self):
        """Vérifie que load_config charge correctement un fichier YAML."""
        from run_precompute import load_config
        
        config_file = ROOT_DIR / "config" / "config.yaml"
        config = load_config(config_file)
        
        assert isinstance(config, dict)
        assert 'paths' in config
    
    def test_should_run_block_avec_config(self):
        """Vérifie que should_run_block fonctionne avec la config."""
        from run_precompute import should_run_block
        from argparse import Namespace
        
        config_file = ROOT_DIR / "config" / "config.yaml"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Test sans arguments CLI (utilise config)
        args = Namespace()
        result = should_run_block('distances', config, args)
        assert isinstance(result, bool)
    
    def test_should_run_block_avec_skip(self):
        """Vérifie que should_run_block respecte --skip-*."""
        from run_precompute import should_run_block
        from argparse import Namespace
        
        config_file = ROOT_DIR / "config" / "config.yaml"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Test avec --skip-distances
        args = Namespace(skip_distances=True, skip_microzones=False,
                        skip_vectors=False, skip_prix_m2=False, skip_congestion=False,
                        only_distances=False, only_microzones=False, only_vectors=False,
                        only_prix_m2=False, only_congestion=False)
        
        result = should_run_block('distances', config, args)
        assert result is False, "should_run_block doit retourner False pour distances avec --skip-distances"
        
        # Test avec un autre bloc (non skip)
        result = should_run_block('microzones', config, args)
        assert result is True, "should_run_block doit retourner True pour microzones sans --skip-microzones"
    
    def test_should_run_block_avec_only(self):
        """Vérifie que should_run_block respecte --only-*."""
        from run_precompute import should_run_block
        from argparse import Namespace
        
        config_file = ROOT_DIR / "config" / "config.yaml"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Test avec --only-distances
        args = Namespace(skip_distances=False, skip_microzones=False,
                        skip_vectors=False, skip_prix_m2=False, skip_congestion=False,
                        only_distances=True, only_microzones=False, only_vectors=False,
                        only_prix_m2=False, only_congestion=False)
        
        result = should_run_block('distances', config, args)
        assert result is True, "should_run_block doit retourner True pour distances avec --only-distances"
        
        result = should_run_block('microzones', config, args)
        assert result is False, "should_run_block doit retourner False pour microzones avec --only-distances"

    def test_run_validate_patterns(self):
        """Story 1.4 : run_validate_patterns avec config projet."""
        from run_precompute import load_config, run_validate_patterns
        config = load_config(ROOT_DIR / "config" / "config.yaml")
        result = run_validate_patterns(config)
        assert result is True, "Validation des patterns doit réussir (exemples data/patterns)"


class TestIntegrationVerification:
    """Tests d'intégration (IV1, IV2 de la story)."""
    
    def test_iv1_dossiers_n_ecrasent_pas_src_docs(self):
        """IV1: Vérifie que scripts/, data/source_data/, config/ n'écrasent pas src/, docs/, brainstorming/."""
        dossiers_crees = ['scripts', 'data/source_data', 'config']
        dossiers_existants = ['src', 'docs', 'brainstorming']
        
        # Vérifier que les dossiers créés n'écrasent pas les dossiers existants
        # (on vérifie seulement ceux qui existent réellement)
        for dossier_creé in dossiers_crees:
            dossier_path = ROOT_DIR / dossier_creé
            if dossier_path.exists():
                # Vérifier qu'aucun dossier existant n'a été écrasé
                for dossier_existant in dossiers_existants:
                    dossier_existant_path = ROOT_DIR / dossier_existant
                    # Si le dossier existant existe, vérifier qu'il n'a pas été écrasé
                    if dossier_existant_path.exists():
                        # Vérifier que les chemins sont différents (pas d'écrasement)
                        assert dossier_path != dossier_existant_path, \
                            f"Le dossier {dossier_creé} ne doit pas écraser {dossier_existant}"
                        # Vérifier que le dossier existant est toujours un dossier
                        assert dossier_existant_path.is_dir(), \
                            f"Le dossier {dossier_existant} doit rester un dossier (pas écrasé par {dossier_creé})"
    
    def test_iv2_imports_ok_dans_env(self):
        """IV2: Vérifie que les imports fonctionnent dans l'environnement."""
        # Test que les modules Python standards sont disponibles
        try:
            import sys
            import pathlib
            import argparse
            import logging
            import yaml
            assert True
        except ImportError as e:
            pytest.fail(f"Imports échoués dans l'environnement: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
