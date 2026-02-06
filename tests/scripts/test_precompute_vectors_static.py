"""
Tests pour le module precompute_vectors_static.py (Story 1.3).

Tests:
- Téléchargement données (prix m², chômage, délinquance)
- Calcul vecteurs statiques
- Calcul congestion statique
- Vérifications dimensions et plages
"""

import pytest
import sys
from pathlib import Path
import pickle
import pandas as pd
import numpy as np

# Ajouter le répertoire racine au path pour les imports
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


class TestDataDownloader:
    """Tests du téléchargement de données."""
    
    def test_generate_prix_m2(self):
        """Vérifie que la génération de prix m² par microzone fonctionne."""
        try:
            from scripts.precompute_vectors_static import DataDownloader
            import yaml
            import geopandas as gpd
            from shapely.geometry import Polygon
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            downloader = DataDownloader(config)
            # Microzones de test
            microzones_data = []
            for i in range(5):
                microzones_data.append({
                    'microzone_id': f'MZ{i+1:03d}',
                    'arrondissement': (i % 20) + 1,
                    'geometry': Polygon([(2.3, 48.8), (2.31, 48.8), (2.31, 48.81), (2.3, 48.81)])
                })
            microzones = gpd.GeoDataFrame(microzones_data, crs='EPSG:4326')

            prix_m2 = downloader.download_prix_m2(ROOT_DIR / "data" / "source_data", microzones)
            
            assert prix_m2 is not None
            assert len(prix_m2) == len(microzones), "Il doit y avoir une ligne par microzone"
            assert 'microzone_id' in prix_m2.columns
            assert 'arrondissement' in prix_m2.columns
            assert 'prix_m2' in prix_m2.columns
            assert (prix_m2['prix_m2'] > 0).all(), "Tous les prix doivent être positifs"
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")
    
    def test_generate_chomage(self):
        """Vérifie que la génération de chômage par microzone fonctionne."""
        try:
            from scripts.precompute_vectors_static import DataDownloader
            import yaml
            import geopandas as gpd
            from shapely.geometry import Polygon
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            downloader = DataDownloader(config)
            microzones_data = []
            for i in range(5):
                microzones_data.append({
                    'microzone_id': f'MZ{i+1:03d}',
                    'arrondissement': (i % 20) + 1,
                    'geometry': Polygon([(2.3, 48.8), (2.31, 48.8), (2.31, 48.81), (2.3, 48.81)])
                })
            microzones = gpd.GeoDataFrame(microzones_data, crs='EPSG:4326')

            chomage = downloader.download_chomage(ROOT_DIR / "data" / "source_data", microzones)
            
            assert chomage is not None
            assert len(chomage) == len(microzones)
            assert 'microzone_id' in chomage.columns
            assert 'arrondissement' in chomage.columns
            assert 'taux_chomage' in chomage.columns
            assert (chomage['taux_chomage'] >= 0).all()
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")
    
    def test_generate_delinquance(self):
        """Vérifie que la génération de délinquance par microzone fonctionne."""
        try:
            from scripts.precompute_vectors_static import DataDownloader
            import yaml
            import geopandas as gpd
            from shapely.geometry import Polygon
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            downloader = DataDownloader(config)
            microzones_data = []
            for i in range(5):
                microzones_data.append({
                    'microzone_id': f'MZ{i+1:03d}',
                    'arrondissement': (i % 20) + 1,
                    'geometry': Polygon([(2.3, 48.8), (2.31, 48.8), (2.31, 48.81), (2.3, 48.81)])
                })
            microzones = gpd.GeoDataFrame(microzones_data, crs='EPSG:4326')

            delinquance = downloader.download_delinquance(ROOT_DIR / "data" / "source_data", microzones)
            
            assert delinquance is not None
            assert len(delinquance) == len(microzones)
            assert 'microzone_id' in delinquance.columns
            assert 'arrondissement' in delinquance.columns
            assert 'indice_delinquance' in delinquance.columns
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")


class TestVectorsStatic:
    """Tests du calcul des vecteurs statiques."""
    
    def test_calculate_vecteurs_statiques(self):
        """Vérifie que le calcul des vecteurs statiques fonctionne."""
        try:
            from scripts.precompute_vectors_static import VectorsStaticCalculator, DataDownloader
            import yaml
            import geopandas as gpd
            from shapely.geometry import Polygon
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Créer des microzones de test
            microzones_data = []
            for i in range(5):
                microzones_data.append({
                    'microzone_id': f'MZ{i+1:03d}',
                    'arrondissement': (i % 20) + 1,
                    'geometry': Polygon([(2.3, 48.8), (2.31, 48.8), (2.31, 48.81), (2.3, 48.81)])
                })
            microzones = gpd.GeoDataFrame(microzones_data, crs='EPSG:4326')
            
            # Données de test
            downloader = DataDownloader(config)
            prix_m2 = downloader.download_prix_m2(ROOT_DIR / "data" / "source_data", microzones)
            chomage = downloader.download_chomage(ROOT_DIR / "data" / "source_data", microzones)
            delinquance = downloader.download_delinquance(ROOT_DIR / "data" / "source_data", microzones)
            
            # Patterns par défaut
            calculator = VectorsStaticCalculator(config)
            patterns = calculator._get_default_patterns()
            
            # Calculer vecteurs
            vecteurs = calculator.calculate_vecteurs_statiques(
                microzones, patterns, prix_m2, chomage, delinquance
            )
            
            assert vecteurs is not None
            assert len(vecteurs) == len(microzones)
            
            for mz_id, vecteurs_mz in vecteurs.items():
                assert len(vecteurs_mz) == 3, f"3 types d'incidents pour {mz_id}"
                for incident_type, vector in vecteurs_mz.items():
                    assert len(vector) == 3, f"3 valeurs (bénin, moyen, grave) pour {incident_type}"
                    assert all(v >= 0 for v in vector), f"Valeurs positives pour {incident_type}"
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")


class TestCongestionStatic:
    """Tests du calcul de la congestion statique."""
    
    def test_calculate_congestion_static(self):
        """Vérifie que le calcul de la congestion statique fonctionne."""
        try:
            from scripts.precompute_vectors_static import CongestionStaticCalculator, DataDownloader
            import yaml
            import geopandas as gpd
            from shapely.geometry import Polygon
            
            config_file = ROOT_DIR / "config" / "config.yaml"
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Créer des microzones de test
            microzones_data = []
            for i in range(5):
                microzones_data.append({
                    'microzone_id': f'MZ{i+1:03d}',
                    'arrondissement': (i % 20) + 1,
                    'geometry': Polygon([(2.3, 48.8), (2.31, 48.8), (2.31, 48.81), (2.3, 48.81)])
                })
            microzones = gpd.GeoDataFrame(microzones_data, crs='EPSG:4326')
            
            # Données de test
            downloader = DataDownloader(config)
            prix_m2 = downloader.download_prix_m2(ROOT_DIR / "data" / "source_data", microzones)
            
            # Calculer congestion
            calculator = CongestionStaticCalculator(config)
            congestion = calculator.calculate_congestion_static(microzones, prix_m2)
            
            assert congestion is not None
            assert len(congestion) == len(microzones)
            assert 'microzone_id' in congestion.columns
            assert 'congestion_base_hiver' in congestion.columns
            assert 'congestion_base_ete' in congestion.columns
            assert 'congestion_base_intersaison' in congestion.columns
            
            # Vérifier que intersaison > hiver et été
            assert (congestion['congestion_base_intersaison'] > congestion['congestion_base_hiver']).all()
            assert (congestion['congestion_base_intersaison'] > congestion['congestion_base_ete']).all()
            
        except ImportError as e:
            pytest.skip(f"Imports manquants: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
