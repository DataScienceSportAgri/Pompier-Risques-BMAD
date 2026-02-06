"""
Tests unitaires pour MatrixModulator.
Story 2.2.9 - Trois matrices de modulation
"""

import numpy as np
import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.data.vector import Vector
from src.core.generation.matrix_modulator import (
    MAX_FACTOR,
    MIN_FACTOR,
    MatrixModulator,
)
from src.core.state.regime_state import (
    REGIME_CRISE,
    REGIME_DETERIORATION,
    REGIME_STABLE,
)
from src.core.state.vectors_state import VectorsState


class TestMatrixModulator:
    """Tests pour MatrixModulator."""
    
    @pytest.fixture
    def matrices_intra_type(self):
        """Matrices intra-type pour les tests."""
        # Matrice 3x3 par défaut
        default_matrix = np.array([
            [0.7, 0.2, 0.1],  # Bénin J-1 -> (bénin, moyen, grave) J+1
            [0.2, 0.6, 0.2],  # Moyen J-1 -> (bénin, moyen, grave) J+1
            [0.1, 0.2, 0.7],  # Grave J-1 -> (bénin, moyen, grave) J+1
        ])
        return {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: default_matrix.copy(),
                INCIDENT_TYPE_INCENDIE: default_matrix.copy(),
                INCIDENT_TYPE_AGRESSION: default_matrix.copy()
            }
        }
    
    @pytest.fixture
    def matrices_inter_type(self):
        """Matrices inter-type pour les tests."""
        return {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: {
                    INCIDENT_TYPE_INCENDIE: [0.1, 0.2, 0.3],  # [bénin, moyen, grave]
                    INCIDENT_TYPE_AGRESSION: [0.05, 0.1, 0.15]
                }
            }
        }
    
    @pytest.fixture
    def matrices_voisin(self):
        """Matrices voisins pour les tests."""
        return {
            "MZ_11_01": {
                "voisins": ["MZ_11_02", "MZ_12_01"],
                "seuil_activation": 5
            }
        }
    
    @pytest.fixture
    def matrix_modulator(self, matrices_intra_type, matrices_inter_type, matrices_voisin):
        """Modulateur de matrices pour les tests."""
        return MatrixModulator(
            matrices_intra_type=matrices_intra_type,
            matrices_inter_type=matrices_inter_type,
            matrices_voisin=matrices_voisin,
            variabilite_locale=0.5
        )
    
    @pytest.fixture
    def vectors_state(self):
        """État des vecteurs pour les tests."""
        state = VectorsState()
        # Ajouter historique 7 jours
        for day in range(7):
            state.set_vector("MZ_11_01", day, INCIDENT_TYPE_ACCIDENT, Vector(1, 1, 1))
        return state
    
    def test_calculer_facteur_gravite(self, matrix_modulator, vectors_state):
        """Test calcul facteur gravité avec historique 7 jours."""
        facteur = matrix_modulator.calculer_facteur_gravite(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, vectors_state, 7
        )
        
        # Vérifier que le facteur est calculé
        assert facteur >= 0.0
        assert isinstance(facteur, float)
    
    def test_calculer_facteur_gravite_pas_historique(self, matrix_modulator, vectors_state):
        """Test calcul facteur gravité sans historique."""
        facteur = matrix_modulator.calculer_facteur_gravite(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, vectors_state, 0
        )
        
        # Sans historique, devrait retourner valeur par défaut
        assert facteur >= 0.0
    
    def test_calculer_facteur_croise(self, matrix_modulator, vectors_state):
        """Test calcul facteur croisé avec effet nb total et conformité."""
        vectors_j_minus_1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_INCENDIE: Vector(2, 1, 0),
                INCIDENT_TYPE_AGRESSION: Vector(1, 1, 1),
                INCIDENT_TYPE_ACCIDENT: Vector(1, 0, 0)
            }
        }
        
        facteur = matrix_modulator.calculer_facteur_croise(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, vectors_j_minus_1, vectors_state, 7
        )
        
        # Vérifier que le facteur est calculé
        assert facteur >= 0.0
        assert isinstance(facteur, float)
    
    def test_calculer_facteur_voisins(self, matrix_modulator):
        """Test calcul facteur voisins avec pondération."""
        vectors_j_minus_1 = {
            "MZ_11_02": {
                INCIDENT_TYPE_ACCIDENT: Vector(2, 2, 2)  # Grave×1.0, moyen×0.5, bénin×0.2
            },
            "MZ_12_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(1, 1, 1)
            }
        }
        
        facteur = matrix_modulator.calculer_facteur_voisins(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, vectors_j_minus_1
        )
        
        # Vérifier que le facteur est calculé
        assert facteur >= 0.0
        assert isinstance(facteur, float)
    
    def test_calculer_facteur_voisins_variabilite(self, matrices_intra_type, matrices_inter_type, matrices_voisin):
        """Test calcul facteur voisins avec variabilité locale."""
        modulator_faible = MatrixModulator(
            matrices_intra_type=matrices_intra_type,
            matrices_inter_type=matrices_inter_type,
            matrices_voisin=matrices_voisin,
            variabilite_locale=0.3  # Faible
        )
        
        modulator_important = MatrixModulator(
            matrices_intra_type=matrices_intra_type,
            matrices_inter_type=matrices_inter_type,
            matrices_voisin=matrices_voisin,
            variabilite_locale=0.7  # Important
        )
        
        vectors_j_minus_1 = {
            "MZ_11_02": {
                INCIDENT_TYPE_ACCIDENT: Vector(5, 5, 5)  # Au-dessus du seuil
            }
        }
        
        facteur_faible = modulator_faible.calculer_facteur_voisins(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, vectors_j_minus_1
        )
        
        facteur_important = modulator_important.calculer_facteur_voisins(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, vectors_j_minus_1
        )
        
        # Variabilité importante devrait donner un facteur plus élevé
        assert facteur_important >= facteur_faible
    
    def test_calculer_modulations_dynamiques(self, matrix_modulator):
        """Test calcul modulations dynamiques."""
        from src.core.events.accident_grave import AccidentGrave
        from src.core.events.fin_travaux import FinTravaux
        
        events_grave = [
            AccidentGrave(
                event_id="EVT_001",
                jour=0,
                arrondissement=11,
                duration=5,
                casualties_base=1,
                characteristics={'increase_bad_vectors': 0.3}
            )
        ]
        
        events_positifs = [
            FinTravaux(
                event_id="POS_001",
                jour=0,
                arrondissement=11,
                impact_reduction=0.1
            )
        ]
        
        modulations = matrix_modulator.calculer_modulations_dynamiques(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, REGIME_STABLE,
            events_grave, events_positifs
        )
        
        # Vérifier que les modulations sont calculées
        assert 'facteur_events' in modulations
        assert 'facteur_regime' in modulations
        assert 'facteur_patterns' in modulations
        
        # Facteur événements devrait être > 1.0 (augmentation) mais < 1.3 (réduction)
        assert modulations['facteur_events'] > 0.0
    
    def test_calculer_modulations_dynamiques_regimes(self, matrix_modulator):
        """Test modulations dynamiques selon régimes."""
        modulations_stable = matrix_modulator.calculer_modulations_dynamiques(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, REGIME_STABLE, [], []
        )
        
        modulations_deterioration = matrix_modulator.calculer_modulations_dynamiques(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, REGIME_DETERIORATION, [], []
        )
        
        modulations_crise = matrix_modulator.calculer_modulations_dynamiques(
            "MZ_11_01", INCIDENT_TYPE_ACCIDENT, REGIME_CRISE, [], []
        )
        
        # Régime crise devrait avoir le facteur le plus élevé
        assert modulations_crise['facteur_regime'] > modulations_deterioration['facteur_regime']
        assert modulations_deterioration['facteur_regime'] > modulations_stable['facteur_regime']
    
    def test_calculer_intensite_calibree(self, matrix_modulator, vectors_state):
        """Test calcul intensité calibrée complète."""
        vectors_j_minus_1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(1, 1, 1),
                INCIDENT_TYPE_INCENDIE: Vector(1, 0, 0),
                INCIDENT_TYPE_AGRESSION: Vector(0, 1, 0)
            }
        }
        
        lambda_base = 2.0
        facteur_statique = 1.0
        
        lambda_calibrated = matrix_modulator.calculer_intensite_calibree(
            microzone_id="MZ_11_01",
            incident_type=INCIDENT_TYPE_ACCIDENT,
            lambda_base=lambda_base,
            facteur_statique=facteur_statique,
            vectors_state=vectors_state,
            vectors_j_minus_1=vectors_j_minus_1,
            jour=7,
            regime=REGIME_STABLE,
            events_grave=[],
            events_positifs=[],
            patterns_actifs=None
        )
        
        # Vérifier que l'intensité calibrée est calculée
        assert lambda_calibrated >= 0.0
        
        # Vérifier caps : Min ×0.1, Max ×3.0
        assert lambda_calibrated >= MIN_FACTOR * lambda_base
        assert lambda_calibrated <= MAX_FACTOR * lambda_base
    
    def test_calculer_intensite_calibree_caps(self, matrix_modulator, vectors_state):
        """Test que les caps sont appliqués correctement."""
        vectors_j_minus_1 = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)
            }
        }
        
        lambda_base = 1.0
        
        # Test avec facteurs très élevés (devrait être capé à ×3.0)
        # Créer un modulateur avec facteurs très élevés
        lambda_calibrated = matrix_modulator.calculer_intensite_calibree(
            microzone_id="MZ_11_01",
            incident_type=INCIDENT_TYPE_ACCIDENT,
            lambda_base=lambda_base,
            facteur_statique=10.0,  # Facteur très élevé
            vectors_state=vectors_state,
            vectors_j_minus_1=vectors_j_minus_1,
            jour=7,
            regime=REGIME_CRISE,  # Régime crise = ×2.0
            events_grave=[],
            events_positifs=[],
            patterns_actifs=None
        )
        
        # Vérifier que le cap maximum est appliqué
        assert lambda_calibrated <= MAX_FACTOR * lambda_base
    
    def test_calculer_normalisation(self, matrix_modulator):
        """Test calcul normalisation Z(t)."""
        lambda_calibrated = {
            INCIDENT_TYPE_ACCIDENT: 2.0,
            INCIDENT_TYPE_INCENDIE: 1.5,
            INCIDENT_TYPE_AGRESSION: 1.0
        }
        
        Z = matrix_modulator.calculer_normalisation("MZ_11_01", lambda_calibrated)
        
        # Normalisation = somme des intensités calibrées
        assert Z == 4.5  # 2.0 + 1.5 + 1.0
