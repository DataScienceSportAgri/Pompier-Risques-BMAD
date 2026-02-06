"""
Tests unitaires pour IntensityCalculator.
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


class TestIntensityCalculator:
    """Tests pour IntensityCalculator."""
    
    def test_initialization(self):
        """Test initialisation."""
        base_intensities = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: 1.0,
                INCIDENT_TYPE_INCENDIE: 0.8,
                INCIDENT_TYPE_ACCIDENT: 0.5
            }
        }
        
        calculator = IntensityCalculator(base_intensities)
        
        assert calculator.base_intensities == base_intensities
        assert len(calculator.cross_probabilities) == 3
        assert len(calculator.inter_type_effects) == 3
    
    def test_calculate_intensity_basic(self):
        """Test calcul d'intensité de base."""
        base_intensities = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: 2.0
            }
        }
        
        calculator = IntensityCalculator(base_intensities)
        
        intensity = calculator.calculate_intensity(
            microzone_id="MZ_11_01",
            incident_type=INCIDENT_TYPE_AGRESSION,
            regime_factor=1.0,
            season_factor=1.0,
            vectors_j_minus_1={},
            neighbor_effect=0.0,
            pattern_effect=0.0
        )
        
        assert intensity >= 0.0
        assert intensity == pytest.approx(2.0, abs=0.1)
    
    def test_calculate_intensity_with_regime_factor(self):
        """Test calcul d'intensité avec facteur régime."""
        base_intensities = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: 1.0
            }
        }
        
        calculator = IntensityCalculator(base_intensities)
        
        intensity_stable = calculator.calculate_intensity(
            "MZ_11_01", INCIDENT_TYPE_AGRESSION, 1.0, 1.0, {}, 0.0, 0.0
        )
        intensity_crise = calculator.calculate_intensity(
            "MZ_11_01", INCIDENT_TYPE_AGRESSION, 2.0, 1.0, {}, 0.0, 0.0
        )
        
        assert intensity_crise > intensity_stable
    
    def test_calculate_intensity_with_season_factor(self):
        """Test calcul d'intensité avec facteur saisonnier."""
        base_intensities = {
            "MZ_11_01": {
                INCIDENT_TYPE_INCENDIE: 1.0
            }
        }
        
        calculator = IntensityCalculator(base_intensities)
        
        intensity_hiver = calculator.calculate_intensity(
            "MZ_11_01", INCIDENT_TYPE_INCENDIE, 1.0, 1.3, {}, 0.0, 0.0
        )
        intensity_ete = calculator.calculate_intensity(
            "MZ_11_01", INCIDENT_TYPE_INCENDIE, 1.0, 0.9, {}, 0.0, 0.0
        )
        
        assert intensity_hiver > intensity_ete
    
    def test_calculate_intensity_with_inter_type_effect(self):
        """Test calcul d'intensité avec effet inter-type."""
        base_intensities = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: 1.0
            }
        }
        
        calculator = IntensityCalculator(base_intensities)
        
        vectors_j_minus_1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: Vector(1, 2, 3),
                INCIDENT_TYPE_INCENDIE: Vector(0, 1, 2)
            }
        }
        
        intensity = calculator.calculate_intensity(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, 1.0, 1.0,
            vectors_j_minus_1, 0.0, 0.0
        )
        
        # L'intensité devrait être augmentée par l'effet inter-type
        assert intensity > 1.0
    
    def test_calculate_intensity_positive(self):
        """Test que l'intensité est toujours positive."""
        base_intensities = {
            "MZ_11_01": {
                INCIDENT_TYPE_AGRESSION: 0.1
            }
        }
        
        calculator = IntensityCalculator(base_intensities)
        
        intensity = calculator.calculate_intensity(
            "MZ_11_01", INCIDENT_TYPE_AGRESSION, 0.5, 0.5,
            {}, -0.5, -0.5  # Effets négatifs
        )
        
        assert intensity >= 0.0
    
    def test_get_cross_probabilities(self):
        """Test récupération des probabilités croisées."""
        base_intensities = {"MZ_11_01": {INCIDENT_TYPE_AGRESSION: 1.0}}
        calculator = IntensityCalculator(base_intensities)
        
        probs = calculator.get_cross_probabilities(INCIDENT_TYPE_AGRESSION, 0)
        
        assert len(probs) == 3
        assert all(0.0 <= p <= 1.0 for p in probs)
        assert abs(sum(probs) - 1.0) < 1e-6
    
    def test_get_cross_probabilities_normalized(self):
        """Test que les probabilités croisées sont normalisées."""
        base_intensities = {"MZ_11_01": {INCIDENT_TYPE_AGRESSION: 1.0}}
        calculator = IntensityCalculator(base_intensities)
        
        for dominant_gravity in [0, 1, 2]:
            probs = calculator.get_cross_probabilities(INCIDENT_TYPE_AGRESSION, dominant_gravity)
            assert abs(sum(probs) - 1.0) < 1e-6
