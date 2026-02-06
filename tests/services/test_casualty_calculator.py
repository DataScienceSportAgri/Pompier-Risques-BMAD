"""
Tests unitaires pour CasualtyCalculator.
Story 2.2.4 - Morts et blessés graves hebdomadaires
"""

import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.data.vector import Vector
from src.core.golden_hour.caserne_manager import CaserneManager
from src.core.golden_hour.golden_hour_calculator import GoldenHourCalculator
from src.core.state.casualties_state import CasualtiesState
from src.core.state.events_state import EventsState
from src.core.state.vectors_state import VectorsState
from src.services.casualty_calculator import (
    ALERTE_JOURS_AGREGES,
    ALERTE_MORTS_MAX,
    ALERTE_MORTS_MIN,
    CasualtyCalculator,
    PONDERATION_BLESSES_ALEATOIRE,
    PONDERATION_BLESSES_GOLDEN_HOUR,
    PONDERATION_MORTS_ALEATOIRE,
    PONDERATION_MORTS_GOLDEN_HOUR,
)


class TestCasualtyCalculator:
    """Tests pour CasualtyCalculator."""
    
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
    def caserne_manager(self):
        """Gestionnaire de casernes pour les tests."""
        return CaserneManager(
            caserne_ids=["CASERNE_1", "CASERNE_2"],
            seed=42
        )
    
    @pytest.fixture
    def golden_hour_calculator(self, caserne_manager):
        """Calculateur de Golden Hour pour les tests."""
        distances_cm = {
            "CASERNE_1": {"MZ_11_01": 5.0},
            "CASERNE_2": {"MZ_12_01": 7.0}
        }
        distances_mh = {
            "MZ_11_01": {"HOPITAL_1": 2.0},
            "MZ_12_01": {"HOPITAL_1": 1.5}
        }
        temps_base_cm = {
            "CASERNE_1": {"MZ_11_01": 6.0},
            "CASERNE_2": {"MZ_12_01": 8.4}
        }
        temps_base_mh = {
            "MZ_11_01": {"HOPITAL_1": 2.4},
            "MZ_12_01": {"HOPITAL_1": 1.8}
        }
        
        return GoldenHourCalculator(
            caserne_manager=caserne_manager,
            distances_caserne_microzone=distances_cm,
            distances_microzone_hopital=distances_mh,
            temps_base_caserne_microzone=temps_base_cm,
            temps_base_microzone_hopital=temps_base_mh,
            seed=42
        )
    
    @pytest.fixture
    def calculator(self, golden_hour_calculator, limites_microzone_arrondissement):
        """Calculateur de casualties pour les tests."""
        return CasualtyCalculator(
            golden_hour_calculator=golden_hour_calculator,
            limites_microzone_arrondissement=limites_microzone_arrondissement,
            seed=42
        )
    
    def test_agreger_microzones_arrondissements(self, calculator):
        """Test agrégation microzones → arrondissements."""
        casualties_microzones = {
            "MZ_11_01": {INCIDENT_TYPE_ACCIDENT: 2, INCIDENT_TYPE_INCENDIE: 1},
            "MZ_11_02": {INCIDENT_TYPE_ACCIDENT: 1},
            "MZ_12_01": {INCIDENT_TYPE_AGRESSION: 3}
        }
        
        result = calculator._agreger_microzones_arrondissements(casualties_microzones)
        
        assert 11 in result
        assert 12 in result
        assert result[11][INCIDENT_TYPE_ACCIDENT] == 3  # 2 + 1
        assert result[11][INCIDENT_TYPE_INCENDIE] == 1
        assert result[12][INCIDENT_TYPE_AGRESSION] == 3
    
    def test_calculer_morts_vecteurs(self, calculator):
        """Test calcul morts depuis vecteurs."""
        vectors = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(1, 0, 0)  # 1 grave
            }
        }
        
        morts = calculator._calculer_morts_vecteurs(vectors, jour=0)
        
        assert "MZ_11_01" in morts
        assert INCIDENT_TYPE_ACCIDENT in morts["MZ_11_01"]
        # Morts devrait être calculé (peut être 0 ou 1 selon tirage au sort)
        assert morts["MZ_11_01"][INCIDENT_TYPE_ACCIDENT] >= 0
    
    def test_calculer_blesses_graves_vecteurs(self, calculator):
        """Test calcul blessés graves depuis vecteurs."""
        vectors = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(1, 1, 0)  # 1 grave + 1 moyen
            }
        }
        
        blesses = calculator._calculer_blesses_graves_vecteurs(vectors, jour=0)
        
        assert "MZ_11_01" in blesses
        assert INCIDENT_TYPE_ACCIDENT in blesses["MZ_11_01"]
        # Blessés graves devrait être calculé
        assert blesses["MZ_11_01"][INCIDENT_TYPE_ACCIDENT] >= 0
    
    def test_calculer_casualties_jour(self, calculator):
        """Test calcul casualties pour un jour."""
        vectors_state = VectorsState()
        vectors_state.set_vector("MZ_11_01", 0, INCIDENT_TYPE_ACCIDENT, Vector(1, 0, 0))
        
        events_state = EventsState()
        
        morts, blesses = calculator.calculer_casualties_jour(
            0, vectors_state, events_state
        )
        
        # Vérifier agrégation arrondissement
        assert 11 in morts or len(morts) == 0  # Peut être 0 selon tirage au sort
    
    def test_calculer_casualties_semaine(self, calculator):
        """Test calcul casualties pour une semaine."""
        vectors_state = VectorsState()
        # Ajouter vecteurs pour plusieurs jours
        for jour in range(7):
            vectors_state.set_vector("MZ_11_01", jour, INCIDENT_TYPE_ACCIDENT, Vector(1, 0, 0))
        
        events_state = EventsState()
        
        morts, blesses = calculator.calculer_casualties_semaine(
            1, vectors_state, events_state
        )
        
        # Vérifier agrégation
        assert isinstance(morts, dict)
        assert isinstance(blesses, dict)
    
    def test_verifier_alertes(self, calculator):
        """Test vérification alertes."""
        # Ajouter morts pour arrondissement 11
        for _ in range(ALERTE_JOURS_AGREGES):
            calculator.verifier_alertes(11, 0)
        
        # 0 morts → alerte
        alerte = calculator.verifier_alertes(11, 0)
        assert alerte is not None
        assert "0 mort" in alerte
        
        # Réinitialiser
        calculator.historique_morts[11] = []
        
        # Ajouter beaucoup de morts
        for _ in range(ALERTE_JOURS_AGREGES):
            calculator.verifier_alertes(11, 1)
        
        # ≥ 500 morts → alerte
        alerte = calculator.verifier_alertes(11, 1)
        assert alerte is not None
        assert f"≥ {ALERTE_MORTS_MAX}" in alerte
        
        # Réinitialiser
        calculator.historique_morts[11] = []
        
        # Ajouter morts dans la plage normale
        for _ in range(ALERTE_JOURS_AGREGES):
            calculator.verifier_alertes(11, 0)
        
        # Ajouter 1 mort (dans plage 1-500)
        alerte = calculator.verifier_alertes(11, 1)
        assert alerte is None  # Pas d'alerte
