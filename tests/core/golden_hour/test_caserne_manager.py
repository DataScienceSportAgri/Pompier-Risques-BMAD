"""
Tests unitaires pour CaserneManager.
Story 2.2.3 - Golden Hour
"""

import pytest

from src.core.golden_hour.caserne_manager import (
    CaserneManager,
    POMPIERS_PAR_INTERVENTION,
    SEUIL_MIN_POMPIERS,
    STAFF_TOTAL_PAR_CASERNE,
)


class TestCaserneManager:
    """Tests pour CaserneManager."""
    
    @pytest.fixture
    def caserne_manager(self):
        """Gestionnaire de casernes pour les tests."""
        return CaserneManager(
            caserne_ids=["CASERNE_1", "CASERNE_2", "CASERNE_3"],
            seed=42
        )
    
    def test_initialization(self, caserne_manager):
        """Test initialisation."""
        assert len(caserne_manager.caserne_ids) == 3
        assert caserne_manager.get_staff_disponible("CASERNE_1") == STAFF_TOTAL_PAR_CASERNE
    
    def test_retirer_pompiers(self, caserne_manager):
        """Test retrait de pompiers."""
        # Retirer 4 pompiers
        success = caserne_manager.retirer_pompiers("CASERNE_1", 4, jour=0)
        
        assert success is True
        assert caserne_manager.get_staff_disponible("CASERNE_1") == STAFF_TOTAL_PAR_CASERNE - 4
    
    def test_retirer_pompiers_insuffisant(self, caserne_manager):
        """Test retrait avec staff insuffisant."""
        # Retirer plus que disponible
        success = caserne_manager.retirer_pompiers("CASERNE_1", STAFF_TOTAL_PAR_CASERNE + 1, jour=0)
        
        assert success is False
        assert caserne_manager.get_staff_disponible("CASERNE_1") == STAFF_TOTAL_PAR_CASERNE
    
    def test_remettre_pompiers(self, caserne_manager):
        """Test remise progressive des pompiers."""
        # Retirer pompiers jour 0
        caserne_manager.retirer_pompiers("CASERNE_1", 4, jour=0, duree_retour=1)
        
        assert caserne_manager.get_staff_disponible("CASERNE_1") == STAFF_TOTAL_PAR_CASERNE - 4
        
        # Jour 1 : pas encore retour (jour_retour = 0 + 1 = 1, donc jour 1 n'est pas > jour_retour)
        caserne_manager.remettre_pompiers(jour=1)
        assert caserne_manager.get_staff_disponible("CASERNE_1") == STAFF_TOTAL_PAR_CASERNE - 4
        
        # Jour 2 : retour (jour_retour = 1, donc jour 2 > jour_retour)
        caserne_manager.remettre_pompiers(jour=2)
        assert caserne_manager.get_staff_disponible("CASERNE_1") == STAFF_TOTAL_PAR_CASERNE
    
    def test_get_stress_caserne(self, caserne_manager):
        """Test calcul stress caserne."""
        # Pas d'interventions
        stress = caserne_manager.get_stress_caserne("CASERNE_1")
        assert stress == 0.0
        
        # Ajouter interventions
        caserne_manager.retirer_pompiers("CASERNE_1", 4, jour=0)
        caserne_manager.retirer_pompiers("CASERNE_1", 4, jour=0)
        
        stress = caserne_manager.get_stress_caserne("CASERNE_1")
        assert stress == 2 * 0.4  # 2 interventions × 0.4
    
    def test_trouver_caserne_disponible(self, caserne_manager):
        """Test recherche caserne disponible."""
        distances = {
            "CASERNE_1": {"MZ_11_01": 2.0},
            "CASERNE_2": {"MZ_11_01": 1.5},
            "CASERNE_3": {"MZ_11_01": 3.0}
        }
        
        # Toutes disponibles
        result = caserne_manager.trouver_caserne_disponible("MZ_11_01", distances)
        assert result is not None
        caserne_id, distance = result
        assert caserne_id == "CASERNE_2"  # Plus proche
        assert distance == 1.5
        
        # Retirer tous les pompiers de CASERNE_2
        caserne_manager.retirer_pompiers("CASERNE_2", STAFF_TOTAL_PAR_CASERNE, jour=0)
        
        # Devrait prendre CASERNE_1 (deuxième plus proche)
        result = caserne_manager.trouver_caserne_disponible("MZ_11_01", distances)
        assert result is not None
        caserne_id, distance = result
        assert caserne_id == "CASERNE_1"
    
    def test_trouver_caserne_disponible_demande_effective(self, caserne_manager):
        """Test demande effective (aucune caserne avec staff suffisant)."""
        distances = {
            "CASERNE_1": {"MZ_11_01": 2.0},
            "CASERNE_2": {"MZ_11_01": 1.5}
        }
        
        # Retirer tous les pompiers
        caserne_manager.retirer_pompiers("CASERNE_1", STAFF_TOTAL_PAR_CASERNE, jour=0)
        caserne_manager.retirer_pompiers("CASERNE_2", STAFF_TOTAL_PAR_CASERNE, jour=0)
        
        # Devrait quand même retourner la plus proche (demande effective)
        result = caserne_manager.trouver_caserne_disponible("MZ_11_01", distances)
        assert result is not None
        caserne_id, distance = result
        assert caserne_id == "CASERNE_2"  # Plus proche même si pas de staff
