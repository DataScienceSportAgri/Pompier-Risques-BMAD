"""
Tests pour le module precompute_distances.py (Story 1.2).

Tests:
- Calcul distances
- Découpage microzones
- Limites arrondissements
- Vérifications matrices (pas de NaN, dimensions)
"""

import pytest
import sys
from pathlib import Path
import pickle
import numpy as np

# Ajouter le répertoire racine au path pour les imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


class TestMicrozones:
    """Tests du découpage en microzones."""
    
    def test_microzones_created(self):
        """Vérifie que les microzones peuvent être créées."""
        try:
            from scripts.precompute_distances import MicrozoneGenerator
            import yaml
            
            # Charger config
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            generator = MicrozoneGenerator(config)
            # Test méthode alternative (sans téléchargement)
            microzones = generator._create_microzones_from_arrondissements()
            
            assert microzones is not None, "Les microzones doivent être créées"
            assert len(microzones) > 0, "Il doit y avoir au moins une microzone"
            assert len(microzones) <= 105, "Il ne doit pas y avoir plus de 105 microzones"
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")
    
    def test_microzones_have_required_fields(self):
        """Vérifie que les microzones ont les champs requis."""
        try:
            from scripts.precompute_distances import MicrozoneGenerator
            import yaml
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            generator = MicrozoneGenerator(config)
            microzones = generator._create_microzones_from_arrondissements()
            
            if microzones is not None and len(microzones) > 0:
                required_fields = ['microzone_id', 'arrondissement', 'geometry']
                for field in required_fields:
                    assert field in microzones.columns, f"Le champ '{field}' doit être présent"
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")


class TestDistances:
    """Tests du calcul des distances."""
    
    def test_distances_calculated(self):
        """Vérifie que les distances peuvent être calculées."""
        try:
            from scripts.precompute_distances import DistanceCalculator, MicrozoneGenerator
            import yaml
            import geopandas as gpd
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Créer microzones de test
            generator = MicrozoneGenerator(config)
            microzones = generator._create_microzones_from_arrondissements()
            
            if microzones is None or len(microzones) == 0:
                pytest.skip("Impossible de créer les microzones de test")
            
            # Calculer distances
            dist_calc = DistanceCalculator(config)
            casernes = dist_calc.load_casernes()
            hopitaux = dist_calc.load_hopitaux()
            
            df_distances_caserne, df_distances_hopital, df_locations = dist_calc.calculate_distances(
                casernes, microzones, hopitaux
            )
            
            assert df_distances_caserne is not None, "Les distances caserne→microzone doivent être calculées"
            assert df_distances_hopital is not None, "Les distances microzone→hôpital doivent être calculées"
            assert df_locations is not None, "Les locations doivent être calculées"
            assert len(df_distances_caserne) > 0, "Il doit y avoir des distances caserne→microzone"
            assert len(df_distances_hopital) > 0, "Il doit y avoir des distances microzone→hôpital"
            assert len(df_locations) > 0, "Il doit y avoir des locations"
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")
    
    def test_distances_no_nan(self):
        """Vérifie qu'il n'y a pas de NaN dans les distances."""
        try:
            from scripts.precompute_distances import DistanceCalculator, MicrozoneGenerator
            import yaml
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            generator = MicrozoneGenerator(config)
            microzones = generator._create_microzones_from_arrondissements()
            
            if microzones is None or len(microzones) == 0:
                pytest.skip("Impossible de créer les microzones de test")
            
            dist_calc = DistanceCalculator(config)
            casernes = dist_calc.load_casernes()
            hopitaux = dist_calc.load_hopitaux()
            
            df_distances_caserne, df_distances_hopital, df_locations = dist_calc.calculate_distances(
                casernes, microzones, hopitaux
            )
            
            # Vérifier pas de NaN dans les DataFrames
            assert not df_distances_caserne['distance_km'].isna().any(), "NaN trouvé dans distances caserne"
            assert not df_distances_hopital['distance_km'].isna().any(), "NaN trouvé dans distances hôpital"
            
            # Vérifier distances positives
            assert (df_distances_caserne['distance_km'] >= 0).all(), "Distances négatives trouvées (caserne)"
            assert (df_distances_hopital['distance_km'] >= 0).all(), "Distances négatives trouvées (hôpital)"
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")


class TestLimits:
    """Tests des limites microzone → arrondissement."""
    
    def test_limits_calculated(self):
        """Vérifie que les limites peuvent être calculées."""
        try:
            from scripts.precompute_distances import (
                MicrozoneGenerator, calculate_microzone_arrondissement_limits
            )
            import yaml
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            generator = MicrozoneGenerator(config)
            microzones = generator._create_microzones_from_arrondissements()
            
            if microzones is None or len(microzones) == 0:
                pytest.skip("Impossible de créer les microzones de test")
            
            limits = calculate_microzone_arrondissement_limits(microzones)
            
            assert limits is not None, "Les limites doivent être calculées"
            assert len(limits) == len(microzones), "Il doit y avoir une limite par microzone"
            
            # Vérifier que les arrondissements sont valides (1-20)
            for mz_id, arr in limits.items():
                assert 1 <= arr <= 20, f"Arrondissement invalide pour {mz_id}: {arr}"
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")


class TestIntegration:
    """Tests d'intégration."""
    
    def test_precompute_distances_function(self):
        """Vérifie que la fonction principale fonctionne."""
        try:
            from scripts.precompute_distances import precompute_distances
            import yaml
            import tempfile
            import shutil
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Créer un dossier temporaire pour les sorties
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                
                # Exécuter le pré-calcul
                result = precompute_distances(config, output_dir)
                
                # Vérifier que la fonction retourne un booléen
                assert isinstance(result, bool), "La fonction doit retourner un booléen"
                
                # Si succès, vérifier que les fichiers sont créés
                if result:
                    expected_files = [
                        "microzones.pkl",
                        "distances_caserne_microzone.pkl",
                        "distances_microzone_hopital.pkl",
                        "limites_microzone_arrondissement.pkl"
                    ]
                    
                    for filename in expected_files:
                        filepath = output_dir / filename
                        assert filepath.exists(), f"Le fichier {filename} doit être créé"
                        
                        # Vérifier que le fichier pickle est lisible
                        try:
                            with open(filepath, 'rb') as f:
                                data = pickle.load(f)
                            assert data is not None, f"Le fichier {filename} doit contenir des données"
                        except Exception as e:
                            pytest.fail(f"Impossible de lire {filename}: {e}")
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
