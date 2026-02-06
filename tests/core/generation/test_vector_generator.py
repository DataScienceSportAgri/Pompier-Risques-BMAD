"""
Tests unitaires pour VectorGenerator.
Story 2.2.1 - Génération vecteurs journaliers
"""

import numpy as np
import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.data.vector import Vector
from src.core.generation.intensity_calculator import IntensityCalculator
from src.core.generation.regime_manager import RegimeManager
from src.core.generation.vector_generator import VectorGenerator


class TestVectorGenerator:
    """Tests pour VectorGenerator."""
    
    @pytest.fixture
    def base_intensities(self):
        """Intensités de base pour les tests."""
        return {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: 1.0,
                INCIDENT_TYPE_INCENDIE: 0.8,
                INCIDENT_TYPE_ACCIDENT: 0.5
            },
            "MZ_11_02": {
                INCIDENT_TYPE_AGRESSION: 0.9,
                INCIDENT_TYPE_INCENDIE: 0.7,
                INCIDENT_TYPE_ACCIDENT: 0.6
            }
        }
    
    @pytest.fixture
    def generator(self, base_intensities):
        """Générateur pour les tests."""
        regime_manager = RegimeManager()
        intensity_calculator = IntensityCalculator(base_intensities)
        
        return VectorGenerator(
            regime_manager=regime_manager,
            intensity_calculator=intensity_calculator,
            base_intensities=base_intensities,
            matrices_intra_type={},
            matrices_inter_type={},
            matrices_voisin={},
            matrices_saisonnalite={},
            microzone_ids=["MZ_11_01", "MZ_11_02"],
            seed=42
        )
    
    def test_initialization(self, generator):
        """Test initialisation."""
        assert len(generator.microzone_ids) == 2
        assert generator.regime_manager is not None
        assert generator.intensity_calculator is not None
    
    def test_get_season(self, generator):
        """Test détermination de la saison."""
        assert generator._get_season(1) == "hiver"
        assert generator._get_season(80) == "hiver"
        assert generator._get_season(81) == "intersaison"
        assert generator._get_season(260) == "intersaison"
        assert generator._get_season(261) == "ete"
        assert generator._get_season(365) == "ete"
    
    def test_get_season_factor(self, generator):
        """Test facteurs saisonniers."""
        # Incendies : hiver +30%, été -10%
        assert generator._get_season_factor(INCIDENT_TYPE_INCENDIE, "hiver") == 1.3
        assert generator._get_season_factor(INCIDENT_TYPE_INCENDIE, "ete") == 0.9
        
        # Agressions : hiver -20%, été +20%
        assert generator._get_season_factor(INCIDENT_TYPE_AGRESSION, "hiver") == 0.8
        assert generator._get_season_factor(INCIDENT_TYPE_AGRESSION, "ete") == 1.2
        
        # Accidents : intersaison +7.5%
        assert generator._get_season_factor(INCIDENT_TYPE_ACCIDENT, "intersaison") == 1.075
    
    def test_generate_vectors_for_day_dimensions(self, generator):
        """Test dimensions des vecteurs générés."""
        vectors_j_minus_1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: Vector(0, 0, 0),
                INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0),
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)
            },
            "MZ_11_02": {
                INCIDENT_TYPE_AGRESSION: Vector(0, 0, 0),
                INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0),
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)
            }
        }
        
        vectors_j = generator.generate_vectors_for_day(1, vectors_j_minus_1)
        
        # Vérifier structure
        assert len(vectors_j) == 2  # 2 microzones
        for mz_id in vectors_j:
            assert len(vectors_j[mz_id]) == 3  # 3 types d'incidents
            for inc_type, vector in vectors_j[mz_id].items():
                assert isinstance(vector, Vector)
                assert vector.grave >= 0
                assert vector.moyen >= 0
                assert vector.benin >= 0
    
    def test_generate_vectors_for_day_types(self, generator):
        """Test types des vecteurs générés."""
        vectors_j_minus_1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: Vector(0, 0, 0),
                INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0),
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)
            },
            "MZ_11_02": {
                INCIDENT_TYPE_AGRESSION: Vector(0, 0, 0),
                INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0),
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)
            }
        }
        
        vectors_j = generator.generate_vectors_for_day(1, vectors_j_minus_1)
        
        # Vérifier que tous les types sont présents
        for mz_id in vectors_j:
            types_present = set(vectors_j[mz_id].keys())
            expected_types = {INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT}
            assert types_present == expected_types
    
    def test_generate_vectors_for_day_no_negative(self, generator):
        """Test qu'il n'y a pas de valeurs négatives."""
        vectors_j_minus_1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: Vector(1, 2, 3),
                INCIDENT_TYPE_INCENDIE: Vector(0, 1, 2),
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 1)
            },
            "MZ_11_02": {
                INCIDENT_TYPE_AGRESSION: Vector(0, 1, 1),
                INCIDENT_TYPE_INCENDIE: Vector(1, 0, 0),
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)
            }
        }
        
        vectors_j = generator.generate_vectors_for_day(2, vectors_j_minus_1)
        
        for mz_id in vectors_j:
            for inc_type, vector in vectors_j[mz_id].items():
                assert vector.grave >= 0
                assert vector.moyen >= 0
                assert vector.benin >= 0
    
    def test_regime_transition(self, generator):
        """Test que les régimes transitent."""
        initial_regimes = {}
        for mz_id in generator.microzone_ids:
            initial_regimes[mz_id] = generator.regime_state.get_regime_or_default(mz_id)
        
        vectors_j_minus_1 = {
            mz_id: {
                INCIDENT_TYPE_AGRESSION: Vector(0, 0, 0),
                INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0),
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)
            }
            for mz_id in generator.microzone_ids
        }
        
        generator.generate_vectors_for_day(1, vectors_j_minus_1)
        
        # Les régimes peuvent avoir changé (transition aléatoire)
        for mz_id in generator.microzone_ids:
            new_regime = generator.regime_state.get_regime_or_default(mz_id)
            assert new_regime in ["Stable", "Détérioration", "Crise"]
