"""
Tests unitaires pour RegimeManager.
Story 2.2.1 - Génération vecteurs journaliers
"""

import numpy as np
import pytest

from src.core.generation.regime_manager import (
    PROBA_REGIME_CRISE,
    PROBA_REGIME_DETERIORATION,
    PROBA_REGIME_STABLE,
    RegimeManager,
)
from src.core.state.regime_state import REGIME_CRISE, REGIME_DETERIORATION, REGIME_STABLE


class TestRegimeManager:
    """Tests pour RegimeManager."""
    
    def test_initialization(self):
        """Test initialisation avec matrice par défaut."""
        manager = RegimeManager()
        
        assert manager.transition_matrix.shape == (3, 3)
        assert len(manager.regimes) == 3
        assert REGIME_STABLE in manager.regimes
        assert REGIME_DETERIORATION in manager.regimes
        assert REGIME_CRISE in manager.regimes
    
    def test_initial_probas(self):
        """Test probabilités initiales (80% Stable, 15% Détérioration, 5% Crise)."""
        manager = RegimeManager()
        
        assert manager.initial_probas[REGIME_STABLE] == PROBA_REGIME_STABLE
        assert manager.initial_probas[REGIME_DETERIORATION] == PROBA_REGIME_DETERIORATION
        assert manager.initial_probas[REGIME_CRISE] == PROBA_REGIME_CRISE
        
        # Vérifier que la somme = 1
        total = sum(manager.initial_probas.values())
        assert abs(total - 1.0) < 1e-6
    
    def test_transition_matrix_validation(self):
        """Test validation de la matrice de transition."""
        manager = RegimeManager()
        
        # Vérifier que chaque ligne somme à 1
        for i, row in enumerate(manager.transition_matrix):
            row_sum = np.sum(row)
            assert np.isclose(row_sum, 1.0, atol=1e-6), f"Ligne {i} ne somme pas à 1"
        
        # Vérifier qu'il n'y a pas de NaN
        assert not np.any(np.isnan(manager.transition_matrix))
    
    def test_initialize_regime(self):
        """Test initialisation d'un régime."""
        manager = RegimeManager()
        rng = np.random.Generator(np.random.PCG64(42))
        
        regime = manager.initialize_regime("MZ_11_01", rng)
        
        assert regime in [REGIME_STABLE, REGIME_DETERIORATION, REGIME_CRISE]
    
    def test_transition_regime(self):
        """Test transition de régime."""
        manager = RegimeManager()
        rng = np.random.Generator(np.random.PCG64(42))
        
        # Transition depuis Stable
        new_regime = manager.transition_regime(REGIME_STABLE, rng)
        assert new_regime in [REGIME_STABLE, REGIME_DETERIORATION, REGIME_CRISE]
        
        # Transition depuis Détérioration
        new_regime = manager.transition_regime(REGIME_DETERIORATION, rng)
        assert new_regime in [REGIME_STABLE, REGIME_DETERIORATION, REGIME_CRISE]
        
        # Transition depuis Crise
        new_regime = manager.transition_regime(REGIME_CRISE, rng)
        assert new_regime in [REGIME_STABLE, REGIME_DETERIORATION, REGIME_CRISE]
    
    def test_invalid_transition_matrix_raises_error(self):
        """Test qu'une matrice invalide lève une erreur."""
        invalid_matrix = np.array([
            [0.5, 0.3, 0.1],  # Ne somme pas à 1
            [0.2, 0.7, 0.1],
            [0.1, 0.2, 0.7]
        ])
        
        with pytest.raises(ValueError, match="ne somme pas à 1"):
            RegimeManager(transition_matrix=invalid_matrix)
    
    def test_get_regime_intensity_factor(self):
        """Test facteurs d'intensité par régime."""
        manager = RegimeManager()
        
        assert manager.get_regime_intensity_factor(REGIME_STABLE) == 1.0
        assert manager.get_regime_intensity_factor(REGIME_DETERIORATION) == 1.3
        assert manager.get_regime_intensity_factor(REGIME_CRISE) == 2.0
    
    def test_update_transition_matrix(self):
        """Test mise à jour de la matrice de transition."""
        manager = RegimeManager()
        old_matrix = manager.transition_matrix.copy()
        
        # Nouvelle matrice valide
        new_matrix = np.array([
            [0.9, 0.08, 0.02],
            [0.25, 0.65, 0.10],
            [0.20, 0.25, 0.55]
        ])
        
        manager.update_transition_matrix(new_matrix)
        
        assert np.array_equal(manager.transition_matrix, new_matrix)
        
        # Test restauration en cas d'erreur
        invalid_matrix = np.array([
            [0.5, 0.3, 0.1],  # Invalide
            [0.2, 0.7, 0.1],
            [0.1, 0.2, 0.7]
        ])
        
        with pytest.raises(ValueError):
            manager.update_transition_matrix(invalid_matrix)
        
        # Vérifier que l'ancienne matrice est restaurée
        assert np.array_equal(manager.transition_matrix, new_matrix)
