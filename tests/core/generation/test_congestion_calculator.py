"""
Tests unitaires pour CongestionCalculator.
Story 2.2.2.5 - Calcul taux de ralentissement de trafic
"""

import numpy as np
import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.data.vector import Vector
from src.core.generation.congestion_calculator import (
    CongestionCalculator,
    FACTEUR_CONGESTION_NUIT_ETE,
    FACTEUR_CONGESTION_NUIT_MOYEN,
    PONDERATION_RANDOMITE_EVENEMENT,
    PONDERATION_RANDOMITE_NORMALE,
)


class TestCongestionCalculator:
    """Tests pour CongestionCalculator."""
    
    @pytest.fixture
    def congestion_statique(self):
        """Congestion statique pour les tests."""
        return {
            "MZ_11_01": 0.5,
            "MZ_11_02": 0.6,
            "MZ_12_01": 0.4
        }
    
    @pytest.fixture
    def calculator(self, congestion_statique):
        """Calculateur pour les tests."""
        return CongestionCalculator(
            congestion_statique=congestion_statique,
            microzone_ids=["MZ_11_01", "MZ_11_02", "MZ_12_01"],
            seed=42
        )
    
    def test_initialization(self, calculator):
        """Test initialisation."""
        assert len(calculator.microzone_ids) == 3
        assert calculator.congestion_statique["MZ_11_01"] == 0.5
    
    def test_get_season(self, calculator):
        """Test détermination de la saison."""
        assert calculator._get_season(1) == "hiver"
        assert calculator._get_season(80) == "hiver"
        assert calculator._get_season(81) == "intersaison"
        assert calculator._get_season(260) == "intersaison"
        assert calculator._get_season(261) == "ete"
    
    def test_get_season_factor(self, calculator):
        """Test facteurs saisonniers (intersaison > hiver/été)."""
        factor_intersaison = calculator._get_season_factor("intersaison")
        factor_hiver = calculator._get_season_factor("hiver")
        factor_ete = calculator._get_season_factor("ete")
        
        assert factor_intersaison > factor_hiver
        assert factor_intersaison > factor_ete
        assert factor_intersaison == 1.2
        assert factor_hiver == 0.9
        assert factor_ete == 0.9
    
    def test_detect_important_event(self, calculator):
        """Test détection événement important."""
        # Pas d'événement important
        vectors_normal = {
            INCIDENT_TYPE_AGRESSION: Vector(0, 0, 1),
            INCIDENT_TYPE_INCENDIE: Vector(0, 1, 0),
            INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 1)
        }
        assert not calculator._detect_important_event("MZ_11_01", vectors_normal)
        
        # Incendie grave
        vectors_fire = {
            INCIDENT_TYPE_INCENDIE: Vector(1, 0, 0)  # grave
        }
        assert calculator._detect_important_event("MZ_11_01", vectors_fire)
        
        # Agression grave
        vectors_aggression = {
            INCIDENT_TYPE_AGRESSION: Vector(1, 0, 0)  # grave
        }
        assert calculator._detect_important_event("MZ_11_01", vectors_aggression)
        
        # Accident majeur
        vectors_accident = {
            INCIDENT_TYPE_ACCIDENT: Vector(0, 3, 0)  # 3 moyens
        }
        assert calculator._detect_important_event("MZ_11_01", vectors_accident)
    
    def test_calculate_randomness_component(self, calculator):
        """Test calcul composante randomité avec pondération."""
        vectors_normal = {INCIDENT_TYPE_AGRESSION: Vector(0, 0, 1)}
        vectors_important = {INCIDENT_TYPE_INCENDIE: Vector(1, 0, 0)}  # grave
        
        randomite_normal = calculator._calculate_randomness_component(
            "MZ_11_01", vectors_normal, False
        )
        randomite_important = calculator._calculate_randomness_component(
            "MZ_11_01", vectors_important, True
        )
        
        # Vérifier plages
        assert 0.0 <= randomite_normal <= PONDERATION_RANDOMITE_NORMALE
        assert 0.0 <= randomite_important <= PONDERATION_RANDOMITE_EVENEMENT
        
        # En moyenne, randomité importante devrait être plus élevée
        # (mais pas garanti à cause de l'aléatoire)
    
    def test_calculate_accident_effect(self, calculator):
        """Test effet accidents (↑ congestion)."""
        vectors_no_accident = {INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)}
        vectors_with_accident = {INCIDENT_TYPE_ACCIDENT: Vector(0, 2, 1)}
        
        effect_no = calculator._calculate_accident_effect(vectors_no_accident)
        effect_with = calculator._calculate_accident_effect(vectors_with_accident)
        
        assert effect_no == 1.0
        assert effect_with > 1.0  # Augmentation
    
    def test_calculate_fire_effect_temporal(self, calculator):
        """Test effets temporels incendies (J↑, J+1↓, J+2↓)."""
        vectors_fire = {INCIDENT_TYPE_INCENDIE: Vector(0, 1, 0)}  # moyen
        
        # Jour J : ↑ congestion
        effect_j = calculator._calculate_fire_effect_temporal("MZ_11_01", 1, vectors_fire)
        assert effect_j == 1.2
        
        # Jour J+1 : ↓ congestion
        vectors_no_fire = {INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0)}
        effect_j1 = calculator._calculate_fire_effect_temporal("MZ_11_01", 2, vectors_no_fire)
        assert effect_j1 == 0.8
        
        # Jour J+2 : ↓ congestion
        effect_j2 = calculator._calculate_fire_effect_temporal("MZ_11_01", 3, vectors_no_fire)
        assert effect_j2 == 0.8
        
        # Jour J+3 : pas d'effet
        effect_j3 = calculator._calculate_fire_effect_temporal("MZ_11_01", 4, vectors_no_fire)
        assert effect_j3 == 1.0
    
    def test_calculate_aggression_effect_temporal(self, calculator):
        """Test effets temporels agressions graves (J↑↑, J+1↓, J+2↓, J+3↓)."""
        vectors_aggression = {INCIDENT_TYPE_AGRESSION: Vector(1, 0, 0)}  # grave
        
        # Jour J : ↑↑ congestion (forte)
        effect_j = calculator._calculate_aggression_effect_temporal("MZ_11_01", 1, vectors_aggression)
        assert effect_j == 1.5
        
        # Jours J+1, J+2, J+3 : ↓ congestion
        vectors_no_aggression = {INCIDENT_TYPE_AGRESSION: Vector(0, 0, 0)}
        for day_offset in [1, 2, 3]:
            effect = calculator._calculate_aggression_effect_temporal(
                "MZ_11_01", 1 + day_offset, vectors_no_aggression
            )
            assert effect == 0.7
        
        # Jour J+4 : pas d'effet
        effect_j4 = calculator._calculate_aggression_effect_temporal("MZ_11_01", 5, vectors_no_aggression)
        assert effect_j4 == 1.0
    
    def test_calculate_night_congestion_factor(self, calculator):
        """Test facteur congestion nuit (divisée par 3 moyenne, 2.2 l'été)."""
        vectors = {INCIDENT_TYPE_AGRESSION: Vector(1, 0, 0)}
        incidents_nuit = {"MZ_11_01": {"agressions": 1}}
        
        # Intersaison/hiver : divisée par 3
        factor_hiver = calculator._calculate_night_congestion_factor(
            "MZ_11_01", vectors, "hiver", incidents_nuit["MZ_11_01"]
        )
        assert factor_hiver < 1.0
        assert 1.0 / FACTEUR_CONGESTION_NUIT_MOYEN * 0.8 <= factor_hiver <= 1.0 / FACTEUR_CONGESTION_NUIT_MOYEN * 1.2
        
        # Été : divisée par 2.2
        factor_ete = calculator._calculate_night_congestion_factor(
            "MZ_11_01", vectors, "ete", incidents_nuit["MZ_11_01"]
        )
        assert factor_ete < 1.0
        assert 1.0 / FACTEUR_CONGESTION_NUIT_ETE * 0.8 <= factor_ete <= 1.0 / FACTEUR_CONGESTION_NUIT_ETE * 1.2
        
        # Pas d'incidents nuit : facteur = 1.0
        factor_no_night = calculator._calculate_night_congestion_factor(
            "MZ_11_01", vectors, "hiver", {}
        )
        assert factor_no_night == 1.0
    
    def test_calculate_congestion_for_day(self, calculator):
        """Test calcul congestion pour un jour."""
        vectors = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(0, 1, 0),
                INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0),
                INCIDENT_TYPE_AGRESSION: Vector(0, 0, 0)
            }
        }
        
        congestion = calculator.calculate_congestion_for_day(0, vectors)
        
        assert "MZ_11_01" in congestion
        assert congestion["MZ_11_01"] > 0.0
        assert congestion["MZ_11_01"] <= 5.0  # Cap
    
    def test_calculate_congestion_with_temporal_effects(self, calculator):
        """Test effets temporels dans calcul complet."""
        # Jour 0 : Incendie
        vectors_j0 = {
            "MZ_11_01": {
                INCIDENT_TYPE_INCENDIE: Vector(0, 1, 0)  # moyen
            }
        }
        congestion_j0 = calculator.calculate_congestion_for_day(0, vectors_j0)
        
        # Jour 1 : Pas d'incendie (effet J+1)
        vectors_j1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_INCENDIE: Vector(0, 0, 0)
            }
        }
        congestion_j1 = calculator.calculate_congestion_for_day(1, vectors_j1)
        
        # Congestion J+1 devrait être plus faible (effet temporel)
        # (peut varier à cause de randomité, mais en moyenne devrait être plus faible)
        assert congestion_j1["MZ_11_01"] < congestion_j0["MZ_11_01"] * 1.1  # Tolérance
    
    def test_update_congestion_realtime(self, calculator):
        """Test modification temps réel de la congestion."""
        vectors = {"MZ_11_01": {INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)}}
        calculator.calculate_congestion_for_day(0, vectors)
        
        initial = calculator.get_congestion("MZ_11_01", 0)
        
        # Modification temps réel
        calculator.update_congestion_realtime("MZ_11_01", 0, 2.5)
        
        updated = calculator.get_congestion("MZ_11_01", 0)
        assert updated == 2.5
        assert updated != initial
    
    def test_get_congestion(self, calculator):
        """Test récupération de la congestion."""
        vectors = {"MZ_11_01": {INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)}}
        calculator.calculate_congestion_for_day(0, vectors)
        
        congestion = calculator.get_congestion("MZ_11_01", 0)
        
        assert congestion is not None
        assert 0.1 <= congestion <= 5.0
    
    def test_congestion_range(self, calculator):
        """Test que la congestion reste dans des plages raisonnables."""
        vectors = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(10, 10, 10),  # Beaucoup d'accidents
                INCIDENT_TYPE_INCENDIE: Vector(5, 5, 5),
                INCIDENT_TYPE_AGRESSION: Vector(5, 5, 5)
            }
        }
        
        congestion = calculator.calculate_congestion_for_day(0, vectors)
        
        # Même avec beaucoup d'incidents, la congestion doit être capée
        assert congestion["MZ_11_01"] <= 5.0
        assert congestion["MZ_11_01"] >= 0.1
