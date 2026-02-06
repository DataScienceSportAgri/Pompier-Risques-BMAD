"""
Calculateur d'intensités calibrées avec triple pattern matricielle.
Story 2.2.1 - Génération vecteurs journaliers
Story 2.2.9 - Trois matrices de modulation (gravité, croisée, voisins)
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from ..data.vector import Vector
from ..state.regime_state import (
    REGIME_CRISE,
    REGIME_DETERIORATION,
    REGIME_STABLE,
)
from ..state.vectors_state import VectorsState
from .calibration import get_calibration_cross_probabilities
from .matrix_modulator import MatrixModulator

TYPES_INCIDENT = [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]


class IntensityCalculator:
    """
    Calculateur d'intensités λ calibrées avec triple pattern matricielle.
    
    Triple pattern matricielle :
    1. Probabilités croisées (bénin, moyen, grave) dans même incident
    2. Effet nb total des 2 autres types d'incidents sur génération
    3. Changement d'effet sur génération aléatoire J+1 selon historique J-1
    """
    
    def __init__(
        self,
        base_intensities: Dict[str, Dict[str, float]],
        cross_probabilities: Optional[Dict[str, np.ndarray]] = None,
        inter_type_effects: Optional[Dict[str, Dict[str, float]]] = None,
        historical_effects: Optional[Dict[str, float]] = None,
        matrix_modulator: Optional[MatrixModulator] = None
    ):
        """
        Initialise le calculateur d'intensités.
        
        Args:
            base_intensities: Intensités de base par microzone et type
                Dict[microzone_id, Dict[type_incident, float]]
            cross_probabilities: Probabilités croisées (bénin, moyen, grave)
                Dict[type_incident, np.ndarray 3x3] - matrice de probabilités croisées
            inter_type_effects: Effets inter-types (influence autres types)
                Dict[type_cible, Dict[type_source, float]]
            historical_effects: Effets historiques (conformité J-1)
                Dict[type_incident, float] - facteurs de conformité
            matrix_modulator: Modulateur de matrices (Story 2.2.9)
        """
        self.base_intensities = base_intensities
        self.matrix_modulator = matrix_modulator
        
        # Probabilités croisées : calibration réaliste par défaut
        if cross_probabilities is None:
            self.cross_probabilities = get_calibration_cross_probabilities()
        else:
            self.cross_probabilities = cross_probabilities
        
        # Effets inter-types par défaut (faibles)
        if inter_type_effects is None:
            self.inter_type_effects = self._create_default_inter_type_effects()
        else:
            self.inter_type_effects = inter_type_effects
        
        # Effets historiques par défaut (conformité modérée)
        if historical_effects is None:
            self.historical_effects = {
                INCIDENT_TYPE_AGRESSION: 0.3,
                INCIDENT_TYPE_INCENDIE: 0.3,
                INCIDENT_TYPE_ACCIDENT: 0.3
            }
        else:
            self.historical_effects = historical_effects
    
    def _create_default_cross_probabilities(self) -> Dict[str, np.ndarray]:
        """Crée des probabilités croisées par défaut (indépendantes)."""
        # Matrice 3x3 : probabilités (bénin, moyen, grave) × (bénin, moyen, grave)
        # Par défaut : indépendantes (diagonale dominante)
        default_matrix = np.array([
            [0.7, 0.2, 0.1],  # Si bénin J-1 -> (bénin, moyen, grave) J+1
            [0.2, 0.6, 0.2],  # Si moyen J-1 -> (bénin, moyen, grave) J+1
            [0.1, 0.2, 0.7],  # Si grave J-1 -> (bénin, moyen, grave) J+1
        ])
        
        return {
            INCIDENT_TYPE_AGRESSION: default_matrix.copy(),
            INCIDENT_TYPE_INCENDIE: default_matrix.copy(),
            INCIDENT_TYPE_ACCIDENT: default_matrix.copy()
        }
    
    def _create_default_inter_type_effects(self) -> Dict[str, Dict[str, float]]:
        """Crée des effets inter-types par défaut."""
        # Effet faible : +0.05 par incident des autres types
        effects = {}
        for target_type in TYPES_INCIDENT:
            effects[target_type] = {}
            for source_type in TYPES_INCIDENT:
                if source_type != target_type:
                    effects[target_type][source_type] = 0.05
        return effects
    
    def calculate_intensity(
        self,
        microzone_id: str,
        incident_type: str,
        regime_factor: float,
        season_factor: float,
        vectors_j_minus_1: Dict[str, Dict[str, Vector]],
        neighbor_effect: float = 0.0,
        pattern_effect: float = 0.0,
        # Paramètres pour MatrixModulator (Story 2.2.9)
        vectors_state: Optional[VectorsState] = None,
        jour: Optional[int] = None,
        regime: Optional[str] = None,
        events_grave: Optional[List] = None,
        events_positifs: Optional[List] = None,
        patterns_actifs: Optional[Dict[str, List[dict]]] = None,
        variabilite_locale: Optional[float] = None
    ) -> float:
        """
        Calcule l'intensité λ finale pour une microzone et un type d'incident.
        
        Si matrix_modulator est disponible, utilise la formule calibrée complète (Story 2.2.9).
        Sinon, utilise la méthode simplifiée (Story 2.2.1).
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident
            regime_factor: Facteur du régime (1.0, 1.3, 2.0)
            season_factor: Facteur saisonnier (×1.3 hiver incendies, etc.)
            vectors_j_minus_1: Vecteurs du jour J-1 par microzone et type
            neighbor_effect: Effet des voisins (0.0-1.0) - utilisé si pas de matrix_modulator
            pattern_effect: Effet des patterns détectés (0.0-1.0) - utilisé si pas de matrix_modulator
            vectors_state: État des vecteurs (pour historique 7 jours)
            jour: Jour actuel (pour historique)
            regime: Régime actuel (pour modulations dynamiques)
            events_grave: Événements graves actifs
            events_positifs: Événements positifs actifs
            patterns_actifs: Patterns actifs
            variabilite_locale: Variabilité locale
        
        Returns:
            Intensité λ finale (≥ 0)
        """
        # Intensité de base
        # Si matrix_modulator disponible, on peut utiliser intensités par gravité (Story 2.2.10)
        # Sinon, utiliser intensité totale (rétrocompatibilité)
        base = self.base_intensities.get(microzone_id, {}).get(incident_type, 0.0)
        if base <= 0:
            return 0.0
        
        # Si matrix_modulator disponible, utiliser formule calibrée complète (Story 2.2.9)
        if self.matrix_modulator is not None and vectors_state is not None and jour is not None:
            # Déterminer régime si non fourni
            if regime is None:
                # Utiliser regime_factor pour déterminer régime
                if regime_factor >= 2.0:
                    regime = REGIME_CRISE
                elif regime_factor >= 1.3:
                    regime = REGIME_DETERIORATION
                else:
                    regime = REGIME_STABLE
            
            # Utiliser formule calibrée complète
            return self.matrix_modulator.calculer_intensite_calibree(
                microzone_id=microzone_id,
                incident_type=incident_type,
                lambda_base=base,
                facteur_statique=season_factor,  # Saisonnalité = facteur statique
                vectors_state=vectors_state,
                vectors_j_minus_1=vectors_j_minus_1,
                jour=jour,
                regime=regime,
                events_grave=events_grave or [],
                events_positifs=events_positifs or [],
                patterns_actifs=patterns_actifs,
                variabilite_locale=variabilite_locale
            )
        
        # Sinon, utiliser méthode simplifiée (Story 2.2.1 - rétrocompatibilité)
        # Application facteur régime
        intensity = base * regime_factor
        
        # Application facteur saisonnier
        intensity *= season_factor
        
        # Effet des autres types d'incidents (inter-type)
        vectors_mz = vectors_j_minus_1.get(microzone_id, {})
        inter_effect = 0.0
        for other_type in TYPES_INCIDENT:
            if other_type != incident_type:
                vector = vectors_mz.get(other_type)
                if vector is not None:
                    total_other = vector.total()
                    effect_coef = self.inter_type_effects.get(incident_type, {}).get(other_type, 0.0)
                    inter_effect += total_other * effect_coef
        
        intensity += inter_effect
        
        # Effet historique (conformité J-1)
        historical_factor = self.historical_effects.get(incident_type, 0.0)
        vector_j_minus_1 = vectors_mz.get(incident_type)
        if vector_j_minus_1 is not None:
            # Plus il y a d'incidents J-1, plus l'effet historique augmente
            total_j_minus_1 = vector_j_minus_1.total()
            historical_effect = total_j_minus_1 * historical_factor * 0.1
            intensity += historical_effect
        
        # Effet voisins
        intensity *= (1.0 + neighbor_effect)
        
        # Effet patterns
        intensity *= (1.0 + pattern_effect)
        
        # S'assurer que l'intensité est positive
        return max(0.0, intensity)
    
    def get_cross_probabilities(
        self,
        incident_type: str,
        dominant_gravity_j_minus_1: int
    ) -> Tuple[float, float, float]:
        """
        Retourne les probabilités croisées (bénin, moyen, grave) selon la gravité dominante J-1.
        
        Args:
            incident_type: Type d'incident
            dominant_gravity_j_minus_1: Gravité dominante J-1 (0=bénin, 1=moyen, 2=grave)
        
        Returns:
            Tuple (prob_bénin, prob_moyen, prob_grave)
        """
        matrix = self.cross_probabilities.get(incident_type)
        if matrix is None:
            # Probabilités par défaut équilibrées
            return (0.33, 0.33, 0.34)
        
        # Clamp l'indice
        idx = max(0, min(2, dominant_gravity_j_minus_1))
        row = matrix[idx, :]
        
        # Normaliser pour s'assurer que la somme = 1
        row_sum = np.sum(row)
        if row_sum > 0:
            row = row / row_sum
        
        return tuple(float(x) for x in row)
