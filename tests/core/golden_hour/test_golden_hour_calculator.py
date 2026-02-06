"""
Tests unitaires pour GoldenHourCalculator.
Story 2.2.3 - Golden Hour
"""

import pytest

from src.core.data.constants import INCIDENT_TYPE_ACCIDENT, INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE
from src.core.golden_hour.caserne_manager import CaserneManager
from src.core.golden_hour.golden_hour_calculator import (
    AJOUT_ALCOOL_MINUTES,
    GOLDEN_HOUR_MINUTES,
    GoldenHourCalculator,
    TEMPS_TRAITEMENT_BASE,
)


class TestGoldenHourCalculator:
    """Tests pour GoldenHourCalculator."""
    
    @pytest.fixture
    def caserne_manager(self):
        """Gestionnaire de casernes pour les tests."""
        return CaserneManager(
            caserne_ids=["CASERNE_1", "CASERNE_2"],
            seed=42
        )
    
    @pytest.fixture
    def distances_cm(self):
        """Distances caserne→microzone."""
        return {
            "CASERNE_1": {"MZ_11_01": 5.0, "MZ_11_02": 3.0},
            "CASERNE_2": {"MZ_11_01": 7.0, "MZ_11_02": 4.0}
        }
    
    @pytest.fixture
    def distances_mh(self):
        """Distances microzone→hôpital."""
        return {
            "MZ_11_01": {"HOPITAL_1": 2.0, "HOPITAL_2": 3.0},
            "MZ_11_02": {"HOPITAL_1": 1.5, "HOPITAL_2": 2.5}
        }
    
    @pytest.fixture
    def temps_base_cm(self):
        """Temps de base caserne→microzone."""
        return {
            "CASERNE_1": {"MZ_11_01": 6.0, "MZ_11_02": 3.6},
            "CASERNE_2": {"MZ_11_01": 8.4, "MZ_11_02": 4.8}
        }
    
    @pytest.fixture
    def temps_base_mh(self):
        """Temps de base microzone→hôpital."""
        return {
            "MZ_11_01": {"HOPITAL_1": 2.4, "HOPITAL_2": 3.6},
            "MZ_11_02": {"HOPITAL_1": 1.8, "HOPITAL_2": 3.0}
        }
    
    @pytest.fixture
    def calculator(
        self,
        caserne_manager,
        distances_cm,
        distances_mh,
        temps_base_cm,
        temps_base_mh
    ):
        """Calculateur de Golden Hour pour les tests."""
        return GoldenHourCalculator(
            caserne_manager=caserne_manager,
            distances_caserne_microzone=distances_cm,
            distances_microzone_hopital=distances_mh,
            temps_base_caserne_microzone=temps_base_cm,
            temps_base_microzone_hopital=temps_base_mh,
            seed=42
        )
    
    def test_trouver_hopital_plus_proche(self, calculator):
        """Test recherche hôpital le plus proche."""
        result = calculator.trouver_hopital_plus_proche("MZ_11_01")
        
        assert result is not None
        hopital_id, distance, temps_base = result
        assert hopital_id == "HOPITAL_1"  # Plus proche (2.0 < 3.0)
        assert distance == 2.0
    
    def test_calculer_temps_trajet_reel_sans_congestion(self, calculator):
        """Test calcul temps trajet réel sans congestion."""
        temps = calculator.calculer_temps_trajet_reel(
            "CASERNE_1", "MZ_11_01", jour=0, is_nuit=False, is_alcool=False
        )
        
        assert temps == 6.0  # Temps de base
    
    def test_calculer_temps_trajet_reel_avec_congestion(self, calculator):
        """Test calcul temps trajet réel avec congestion."""
        # Charger table de congestion
        calculator.congestion_table = {
            "MZ_11_01": {0: 1.5}  # Congestion ×1.5
        }
        
        temps = calculator.calculer_temps_trajet_reel(
            "CASERNE_1", "MZ_11_01", jour=0, is_nuit=False, is_alcool=False
        )
        
        assert temps == 6.0 * 1.5  # Temps de base × congestion
    
    def test_calculer_temps_trajet_reel_avec_alcool(self, calculator):
        """Test calcul temps trajet réel avec alcool (+5 min)."""
        temps = calculator.calculer_temps_trajet_reel(
            "CASERNE_1", "MZ_11_01", jour=0, is_nuit=False, is_alcool=True
        )
        
        assert temps == 6.0 + AJOUT_ALCOOL_MINUTES
    
    def test_calculer_temps_total(self, calculator):
        """Test calcul temps total."""
        temps_trajet, temps_traitement, temps_hopital_retour, temps_total = calculator.calculer_temps_total(
            "CASERNE_1", "MZ_11_01", jour=0, is_nuit=False, is_alcool=False
        )
        
        assert temps_trajet == 6.0
        assert temps_traitement == TEMPS_TRAITEMENT_BASE
        assert temps_hopital_retour > 0.0
        assert temps_total == temps_trajet + temps_traitement + temps_hopital_retour
    
    def test_calculer_golden_hour_sous_60min(self, calculator):
        """Test Golden Hour avec temps < 60 min."""
        is_mort, is_blesse_grave, temps_total, details = calculator.calculer_golden_hour(
            "MZ_11_01", jour=0, type_incident=INCIDENT_TYPE_ACCIDENT,
            is_nuit=False, is_alcool=False
        )
        
        assert temps_total < GOLDEN_HOUR_MINUTES
        assert details['prob_mort'] == 0.1  # Probabilité de base
        assert details['prob_blesse_grave'] == 0.2
    
    def test_calculer_golden_hour_sur_60min(self, calculator):
        """Test Golden Hour avec temps > 60 min."""
        # Forcer congestion élevée pour dépasser 60 min
        calculator.congestion_table = {
            "MZ_11_01": {0: 10.0}  # Congestion très élevée
        }
        
        is_mort, is_blesse_grave, temps_total, details = calculator.calculer_golden_hour(
            "MZ_11_01", jour=0, type_incident=INCIDENT_TYPE_ACCIDENT,
            is_nuit=False, is_alcool=False
        )
        
        if temps_total > GOLDEN_HOUR_MINUTES:
            assert details['prob_mort'] > 0.3  # Probabilité augmentée
            assert details['prob_blesse_grave'] > 0.4
    
    def test_calculer_golden_hour_avec_stress(self, calculator):
        """Test Golden Hour avec stress caserne."""
        # Ajouter interventions pour augmenter stress
        calculator.caserne_manager.retirer_pompiers("CASERNE_1", 4, jour=0)
        calculator.caserne_manager.retirer_pompiers("CASERNE_1", 4, jour=0)
        
        is_mort, is_blesse_grave, temps_total, details = calculator.calculer_golden_hour(
            "MZ_11_01", jour=0, type_incident=INCIDENT_TYPE_ACCIDENT,
            is_nuit=False, is_alcool=False
        )
        
        assert details['stress'] > 0.0
        # Temps avec stress devrait être > temps sans stress
        assert details['temps_trajet'] >= 6.0
