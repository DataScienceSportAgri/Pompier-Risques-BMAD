"""
Gestionnaire de régimes cachés avec matrices de transition.
Story 2.2.1 - Génération vecteurs journaliers
"""

import numpy as np
from typing import Dict, List, Optional

from ..state.regime_state import (
    REGIME_CRISE,
    REGIME_DETERIORATION,
    REGIME_STABLE,
    RegimeState,
)


# Probabilités de base pour les régimes (80% Stable, 15% Détérioration, 5% Crise)
PROBA_REGIME_STABLE = 0.80
PROBA_REGIME_DETERIORATION = 0.15
PROBA_REGIME_CRISE = 0.05


class RegimeManager:
    """
    Gestionnaire de régimes cachés avec matrices de transition.
    
    Régimes : Stable (normal), Détérioration (dégradé), Crise
    Probabilités initiales : 80% Stable, 15% Détérioration, 5% Crise
    """
    
    def __init__(
        self,
        transition_matrix: Optional[np.ndarray] = None,
        initial_probas: Optional[Dict[str, float]] = None
    ):
        """
        Initialise le gestionnaire de régimes.
        
        Args:
            transition_matrix: Matrice de transition 3x3 (Stable, Détérioration, Crise)
                Si None, utilise une matrice par défaut
            initial_probas: Probabilités initiales par régime
                Si None, utilise les probabilités par défaut (80/15/5)
        """
        self.regimes = [REGIME_STABLE, REGIME_DETERIORATION, REGIME_CRISE]
        self.regime_to_idx = {r: i for i, r in enumerate(self.regimes)}
        
        # Probabilités initiales
        if initial_probas is None:
            self.initial_probas = {
                REGIME_STABLE: PROBA_REGIME_STABLE,
                REGIME_DETERIORATION: PROBA_REGIME_DETERIORATION,
                REGIME_CRISE: PROBA_REGIME_CRISE
            }
        else:
            self.initial_probas = initial_probas
        
        # Matrice de transition par défaut (tendance à rester stable)
        if transition_matrix is None:
            self.transition_matrix = self._create_default_transition_matrix()
        else:
            self.transition_matrix = transition_matrix
        
        # Valider la matrice
        self._validate_transition_matrix()
    
    def _create_default_transition_matrix(self) -> np.ndarray:
        """
        Crée une matrice de transition par défaut.
        
        Structure :
        - Stable a tendance à rester stable (0.85) ou se détériorer (0.12) ou crise (0.03)
        - Détérioration peut s'améliorer (0.20) ou rester (0.70) ou empirer (0.10)
        - Crise peut s'améliorer (0.15) ou se détériorer (0.20) ou rester (0.65)
        """
        matrix = np.array([
            [0.85, 0.12, 0.03],  # Stable -> (Stable, Détérioration, Crise)
            [0.20, 0.70, 0.10],  # Détérioration -> (Stable, Détérioration, Crise)
            [0.15, 0.20, 0.65],  # Crise -> (Stable, Détérioration, Crise)
        ])
        return matrix
    
    def _validate_transition_matrix(self) -> None:
        """Valide que la matrice de transition est correcte."""
        if self.transition_matrix.shape != (3, 3):
            raise ValueError("La matrice de transition doit être 3x3")
        
        # Vérifier que chaque ligne somme à 1
        for i, row in enumerate(self.transition_matrix):
            row_sum = np.sum(row)
            if not np.isclose(row_sum, 1.0, atol=1e-6):
                raise ValueError(
                    f"La ligne {i} de la matrice de transition ne somme pas à 1: {row_sum}"
                )
        
        # Vérifier qu'il n'y a pas de NaN
        if np.any(np.isnan(self.transition_matrix)):
            raise ValueError("La matrice de transition contient des NaN")
    
    def initialize_regime(
        self,
        microzone_id: str,
        rng: np.random.Generator,
        probas_custom: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Initialise le régime d'une microzone selon les probabilités initiales.
        
        Args:
            microzone_id: Identifiant de la microzone
            rng: Générateur aléatoire NumPy
            probas_custom: Probabilités personnalisées (si None, utilise self.initial_probas)
                Format: {REGIME_STABLE: float, REGIME_DETERIORATION: float, REGIME_CRISE: float}
        
        Returns:
            Régime initial assigné
        """
        if probas_custom is not None:
            # Utiliser probabilités personnalisées (ex: selon vecteurs statiques)
            regimes = list(probas_custom.keys())
            probas = [probas_custom[r] for r in regimes]
            
            # Normaliser pour s'assurer que la somme = 1
            total = sum(probas)
            if total > 0:
                probas = [p / total for p in probas]
        else:
            # Utiliser probabilités de base
            regimes = list(self.initial_probas.keys())
            probas = [self.initial_probas[r] for r in regimes]
        
        regime = rng.choice(regimes, p=probas)
        return regime
    
    def transition_regime(
        self,
        current_regime: str,
        rng: np.random.Generator
    ) -> str:
        """
        Effectue une transition de régime selon la matrice de transition.
        
        Args:
            current_regime: Régime actuel
            rng: Générateur aléatoire NumPy
        
        Returns:
            Nouveau régime après transition
        """
        if current_regime not in self.regime_to_idx:
            raise ValueError(f"Régime invalide: {current_regime}")
        
        idx = self.regime_to_idx[current_regime]
        transition_probas = self.transition_matrix[idx, :]
        
        new_idx = rng.choice(len(self.regimes), p=transition_probas)
        return self.regimes[new_idx]
    
    def get_regime_intensity_factor(self, regime: str) -> float:
        """
        Retourne le facteur d'intensité selon le régime.
        
        Args:
            regime: Régime actuel
        
        Returns:
            Facteur multiplicatif pour l'intensité λ
        """
        factors = {
            REGIME_STABLE: 1.0,
            REGIME_DETERIORATION: 1.3,  # +30% d'intensité
            REGIME_CRISE: 2.0  # +100% d'intensité
        }
        return factors.get(regime, 1.0)
    
    def update_transition_matrix(
        self,
        new_matrix: np.ndarray
    ) -> None:
        """
        Met à jour la matrice de transition (modifiable selon patterns).
        
        Args:
            new_matrix: Nouvelle matrice 3x3
        
        Raises:
            ValueError: Si la matrice est invalide
        """
        old_matrix = self.transition_matrix
        self.transition_matrix = new_matrix
        try:
            self._validate_transition_matrix()
        except ValueError as e:
            # Restaurer l'ancienne matrice en cas d'erreur
            self.transition_matrix = old_matrix
            raise e
