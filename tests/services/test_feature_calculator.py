"""
Tests unitaires pour StateCalculator (FeatureCalculator).
Story 2.2.5 - Features hebdomadaires
"""

import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.data.vector import Vector
from src.core.state.dynamic_state import DynamicState
from src.core.state.vectors_state import VectorsState
from src.services.feature_calculator import StateCalculator


class TestStateCalculator:
    """Tests pour StateCalculator."""
    
    @pytest.fixture
    def limites_microzone_arrondissement(self):
        """Limites microzone → arrondissement pour les tests."""
        return {
            "MZ_11_01": 11,
            "MZ_11_02": 11,
            "MZ_12_01": 12,
            "MZ_12_02": 12
        }
    
    @pytest.fixture
    def calculator(self, limites_microzone_arrondissement):
        """Calculateur de features pour les tests."""
        return StateCalculator(
            limites_microzone_arrondissement=limites_microzone_arrondissement
        )
    
    def test_agreger_microzones_arrondissements(self, calculator):
        """Test agrégation microzones → arrondissements."""
        valeurs_microzones = {
            "MZ_11_01": 5.0,
            "MZ_11_02": 3.0,
            "MZ_12_01": 2.0
        }
        
        result = calculator._agreger_microzones_arrondissements(valeurs_microzones)
        
        assert 11 in result
        assert 12 in result
        assert result[11] == 8.0  # 5.0 + 3.0
        assert result[12] == 2.0
    
    def test_calculer_sommes_incidents_semaine(self, calculator):
        """Test calcul sommes incidents pour une semaine."""
        vectors_state = VectorsState()
        
        # Ajouter vecteurs pour semaine 1 (jours 0-6)
        for jour in range(7):
            vectors_state.set_vector("MZ_11_01", jour, INCIDENT_TYPE_ACCIDENT, Vector(1, 2, 3))
            vectors_state.set_vector("MZ_11_01", jour, INCIDENT_TYPE_INCENDIE, Vector(0, 1, 2))
        
        sommes = calculator._calculer_sommes_incidents_semaine(1, vectors_state)
        
        assert 11 in sommes
        assert INCIDENT_TYPE_ACCIDENT in sommes[11]
        assert sommes[11][INCIDENT_TYPE_ACCIDENT]['moyen_grave'] == 7 * 3  # 7 jours × (1 grave + 2 moyen)
        assert sommes[11][INCIDENT_TYPE_ACCIDENT]['benin'] == 7 * 3  # 7 jours × 3 bénin
    
    def test_calculer_proportions_alcool_nuit_semaine(self, calculator):
        """Test calcul proportions alcool/nuit pour une semaine."""
        vectors_state = VectorsState()
        dynamic_state = DynamicState()
        
        # Ajouter vecteurs pour semaine 1 (jours 0-6)
        for jour in range(7):
            vectors_state.set_vector("MZ_11_01", jour, INCIDENT_TYPE_ACCIDENT, Vector(1, 1, 2))
        
        # Ajouter incidents alcool et nuit (clés pluriel comme dans dynamic_state)
        dynamic_state.incidents_alcool["MZ_11_01"] = {
            "accidents": 5,
            "incendies": 2,
            "agressions": 3
        }
        dynamic_state.incidents_nuit["MZ_11_01"] = {
            "accidents": 3,
            "incendies": 1,
            "agressions": 2
        }
        
        proportions = calculator._calculer_proportions_alcool_nuit_semaine(1, vectors_state, dynamic_state)
        
        assert 11 in proportions
        # Vérifier que les proportions sont calculées
        assert INCIDENT_TYPE_ACCIDENT in proportions[11]
    
    def test_calculer_features_semaine(self, calculator):
        """Test calcul features complètes pour une semaine."""
        vectors_state = VectorsState()
        dynamic_state = DynamicState()
        
        # Ajouter vecteurs pour semaine 1
        for jour in range(7):
            vectors_state.set_vector("MZ_11_01", jour, INCIDENT_TYPE_ACCIDENT, Vector(1, 1, 2))
        
        # Ajouter incidents alcool/nuit (clés pluriel)
        dynamic_state.incidents_alcool["MZ_11_01"] = {"accidents": 2}
        dynamic_state.incidents_nuit["MZ_11_01"] = {"accidents": 1}
        
        df = calculator.calculer_features_semaine(1, vectors_state, dynamic_state)
        
        assert len(df) > 0
        assert 'arrondissement' in df.columns
        assert 'semaine' in df.columns
        assert 'accidents_moyen_grave' in df.columns
        assert 'accidents_benin' in df.columns
        assert 'accidents_alcool' in df.columns
        assert 'accidents_nuit' in df.columns
        
        # Vérifier qu'il n'y a pas de NaN
        assert df.select_dtypes(include=['float64', 'int64']).isna().sum().sum() == 0
    
    def test_calculer_features_multiple_semaines(self, calculator):
        """Test calcul features pour plusieurs semaines."""
        vectors_state = VectorsState()
        dynamic_state = DynamicState()
        
        # Ajouter vecteurs pour semaines 1 et 2
        for semaine in [1, 2]:
            jour_debut = (semaine - 1) * 7
            for jour in range(jour_debut, jour_debut + 7):
                vectors_state.set_vector("MZ_11_01", jour, INCIDENT_TYPE_ACCIDENT, Vector(1, 0, 1))
        
        df = calculator.calculer_features_multiple_semaines(
            [1, 2], vectors_state, dynamic_state
        )
        
        assert len(df) > 0
        assert df['semaine'].nunique() == 2
    
    def test_features_format_ml(self, calculator):
        """Test que les features sont dans un format utilisable pour ML."""
        vectors_state = VectorsState()
        dynamic_state = DynamicState()
        
        # Ajouter quelques données
        for jour in range(7):
            vectors_state.set_vector("MZ_11_01", jour, INCIDENT_TYPE_ACCIDENT, Vector(1, 1, 1))
        
        df = calculator.calculer_features_semaine(1, vectors_state, dynamic_state)
        
        # Vérifier types numériques
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        assert len(numeric_cols) >= 16  # Au moins 16 features numériques
        
        # Vérifier pas de NaN
        assert df[numeric_cols].isna().sum().sum() == 0
        
        # Vérifier pas de valeurs infinies
        assert (df[numeric_cols] == float('inf')).sum().sum() == 0
        assert (df[numeric_cols] == float('-inf')).sum().sum() == 0
