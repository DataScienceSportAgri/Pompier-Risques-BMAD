"""
Tests unitaires pour StaticVectorLoader.
Story 2.2.10 - Utilisation vecteurs statiques pour régimes et intensités de base
"""

import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.generation.static_vector_loader import (
    FACTEUR_BENIN,
    FACTEUR_GRAVE,
    FACTEUR_MOYEN,
    StaticVectorLoader,
)
from src.core.state.regime_state import (
    REGIME_CRISE,
    REGIME_DETERIORATION,
    REGIME_STABLE,
)


class TestStaticVectorLoader:
    """Tests pour StaticVectorLoader."""
    
    @pytest.fixture
    def vecteurs_statiques(self):
        """Vecteurs statiques pour les tests."""
        return {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: (0.5, 0.3, 0.1),  # (bénin, moyen, grave)
                INCIDENT_TYPE_INCENDIE: (0.4, 0.2, 0.05),
                INCIDENT_TYPE_AGRESSION: (0.6, 0.4, 0.2)  # Zone à risque
            },
            "MZ_12_01": {
                INCIDENT_TYPE_ACCIDENT: (0.1, 0.05, 0.01),  # Zone calme
                INCIDENT_TYPE_INCENDIE: (0.1, 0.05, 0.01),
                INCIDENT_TYPE_AGRESSION: (0.1, 0.05, 0.01)
            }
        }
    
    @pytest.fixture
    def static_vector_loader(self, vecteurs_statiques):
        """Chargeur de vecteurs statiques pour les tests."""
        return StaticVectorLoader(vecteurs_statiques=vecteurs_statiques)
    
    def test_load_static_vectors(self):
        """Test chargement vecteurs statiques depuis fichier."""
        # Ce test nécessite que le fichier existe
        # On teste juste que la méthode existe et peut être appelée
        try:
            loader = StaticVectorLoader()
            assert loader.vecteurs_statiques is not None
        except FileNotFoundError:
            # Si le fichier n'existe pas, c'est OK pour les tests
            pytest.skip("Fichier vecteurs_statiques.pkl non disponible")
    
    def test_calculer_intensites_base(self, static_vector_loader):
        """Test calcul intensités de base par gravité."""
        intensites = static_vector_loader.calculer_intensites_base(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT
        )
        
        # Vérifier structure
        assert 'benin' in intensites
        assert 'moyen' in intensites
        assert 'grave' in intensites
        
        # Vérifier valeurs positives
        assert intensites['benin'] >= 0.0
        assert intensites['moyen'] >= 0.0
        assert intensites['grave'] >= 0.0
        
        # Vérifier conversion (vecteur × facteur)
        # Vecteur = (0.5, 0.3, 0.1)
        assert abs(intensites['benin'] - (0.5 * FACTEUR_BENIN)) < 0.01
        assert abs(intensites['moyen'] - (0.3 * FACTEUR_MOYEN)) < 0.01
        assert abs(intensites['grave'] - (0.1 * FACTEUR_GRAVE)) < 0.01
    
    def test_calculer_intensite_base_totale(self, static_vector_loader):
        """Test calcul intensité de base totale (rétrocompatibilité)."""
        intensite_totale = static_vector_loader.calculer_intensite_base_totale(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT
        )
        
        # Vérifier que c'est la somme des intensités par gravité
        intensites = static_vector_loader.calculer_intensites_base(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT
        )
        somme_attendue = intensites['benin'] + intensites['moyen'] + intensites['grave']
        
        assert abs(intensite_totale - somme_attendue) < 0.01
    
    def test_calculer_facteur_regimes(self, static_vector_loader):
        """Test calcul facteur influence régimes."""
        # Zone à risque (MZ_11_01)
        facteur_risque = static_vector_loader.calculer_facteur_regimes("MZ_11_01")
        
        # Zone calme (MZ_12_01)
        facteur_calme = static_vector_loader.calculer_facteur_regimes("MZ_12_01")
        
        # Zone à risque devrait avoir un facteur plus élevé
        assert facteur_risque > facteur_calme
        
        # Facteurs devraient être positifs
        assert facteur_risque > 0.0
        assert facteur_calme > 0.0
    
    def test_calculer_probabilites_regimes(self, static_vector_loader):
        """Test calcul probabilités régimes selon vecteurs statiques."""
        # Zone à risque (MZ_11_01)
        probas_risque = static_vector_loader.calculer_probabilites_regimes("MZ_11_01")
        
        # Zone calme (MZ_12_01)
        probas_calme = static_vector_loader.calculer_probabilites_regimes("MZ_12_01")
        
        # Vérifier structure
        assert REGIME_STABLE in probas_risque
        assert REGIME_DETERIORATION in probas_risque
        assert REGIME_CRISE in probas_risque
        
        # Vérifier normalisation (somme = 1)
        assert abs(sum(probas_risque.values()) - 1.0) < 0.01
        assert abs(sum(probas_calme.values()) - 1.0) < 0.01
        
        # Zone à risque devrait avoir plus de Crise
        assert probas_risque[REGIME_CRISE] > probas_calme[REGIME_CRISE]
        
        # Zone calme devrait avoir plus de Stable
        assert probas_calme[REGIME_STABLE] > probas_risque[REGIME_STABLE]
    
    def test_get_base_intensities_dict(self, static_vector_loader):
        """Test conversion en format attendu par code existant."""
        microzone_ids = ["MZ_11_01", "MZ_12_01"]
        intensities = static_vector_loader.get_base_intensities_dict(microzone_ids)
        
        # Vérifier structure
        assert "MZ_11_01" in intensities
        assert "MZ_12_01" in intensities
        
        # Vérifier types d'incidents
        assert INCIDENT_TYPE_ACCIDENT in intensities["MZ_11_01"]
        assert INCIDENT_TYPE_INCENDIE in intensities["MZ_11_01"]
        assert INCIDENT_TYPE_AGRESSION in intensities["MZ_11_01"]
        
        # Vérifier valeurs positives
        for mz_id in microzone_ids:
            for inc_type in intensities[mz_id]:
                assert intensities[mz_id][inc_type] >= 0.0
    
    def test_calculer_intensites_base_microzone_inexistante(self, static_vector_loader):
        """Test calcul intensités base pour microzone inexistante."""
        intensites = static_vector_loader.calculer_intensites_base(
            "MZ_INEXISTANT", INCIDENT_TYPE_ACCIDENT
        )
        
        # Devrait retourner valeurs par défaut
        assert 'benin' in intensites
        assert 'moyen' in intensites
        assert 'grave' in intensites
        assert intensites['benin'] >= 0.0
        assert intensites['moyen'] >= 0.0
        assert intensites['grave'] >= 0.0
