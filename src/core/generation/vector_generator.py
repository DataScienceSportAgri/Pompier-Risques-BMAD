"""
Générateur de vecteurs journaliers avec modèle Zero-Inflated Poisson.
Story 2.2.1 - Génération vecteurs journaliers
"""

from typing import Dict, List, Optional

import numpy as np

from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from ..data.vector import Vector
from ..probability.matrix_applicator import apply_voisin
from ..state.regime_state import RegimeState
from .intensity_calculator import IntensityCalculator
from .regime_manager import RegimeManager
from .zero_inflated_poisson import (
    calculate_zero_inflation_probability,
    sample_multinomial_counts,
    sample_zero_inflated_poisson,
)

# Mapping pour compatibilité avec les strings utilisées dans probability
TYPES_INCIDENT = [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]


def _parse_arrondissement_from_microzone_id(microzone_id: str) -> int:
    """Extrait l'arrondissement depuis microzone_id (MZ_11_01 → 11 ; MZ031 → 7)."""
    try:
        parts = microzone_id.split("_")
        if len(parts) >= 2:
            return max(1, min(20, int(parts[1])))
        if (
            len(microzone_id) == 5
            and microzone_id.startswith("MZ")
            and microzone_id[2:].isdigit()
        ):
            idx = int(microzone_id[2:])
            return max(1, min(20, (idx - 1) // 5 + 1))
    except (ValueError, TypeError):
        pass
    return 1


TYPE_TO_STRING = {
    INCIDENT_TYPE_AGRESSION: "agressions",
    INCIDENT_TYPE_INCENDIE: "incendies",
    INCIDENT_TYPE_ACCIDENT: "accidents"
}
STRING_TO_TYPE = {v: k for k, v in TYPE_TO_STRING.items()}


class VectorGenerator:
    """
    Générateur de vecteurs journaliers avec modèle Zero-Inflated Poisson et régimes cachés.
    
    Génère 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave)
    par microzone pour chaque jour.
    """
    
    def __init__(
        self,
        regime_manager: RegimeManager,
        intensity_calculator: IntensityCalculator,
        base_intensities: Dict[str, Dict[str, float]],
        matrices_intra_type: Dict[str, Dict[str, np.ndarray]],
        matrices_inter_type: Dict[str, Dict[str, Dict[str, List[float]]]],
        matrices_voisin: Dict[str, any],
        matrices_saisonnalite: Dict[str, Dict[str, Dict[str, float]]],
        microzone_ids: List[str],
        seed: Optional[int] = None,
        limites_microzone_arrondissement: Optional[Dict[str, int]] = None,
        reduction_effet_patterns: float = 0.8,
    ):
        """
        Initialise le générateur de vecteurs.
        
        Args:
            regime_manager: Gestionnaire de régimes
            intensity_calculator: Calculateur d'intensités
            base_intensities: Intensités de base par microzone et type
            matrices_intra_type: Matrices intra-type (Story 1.4.4.3)
            matrices_inter_type: Matrices inter-type (Story 1.4.4.3)
            matrices_voisin: Matrices voisins (Story 1.4.4.3)
            matrices_saisonnalite: Matrices saisonnalité (Story 1.4.4.3)
            microzone_ids: Liste des identifiants de microzones
            seed: Seed pour reproductibilité
            limites_microzone_arrondissement: Mapping microzone_id → arrondissement (1..20) pour effets_reduction
            reduction_effet_patterns: Réduction des effets patterns 4j/7j/60j (0.8 = 80 % réduction, 20 % conservé)
        """
        self.regime_manager = regime_manager
        self.intensity_calculator = intensity_calculator
        self.base_intensities = base_intensities
        self.matrices_intra_type = matrices_intra_type
        self.matrices_inter_type = matrices_inter_type
        self.matrices_voisin = matrices_voisin
        self.matrices_saisonnalite = matrices_saisonnalite
        self.microzone_ids = microzone_ids
        self.limites_microzone_arrondissement = limites_microzone_arrondissement or {}
        self.reduction_effet_patterns = reduction_effet_patterns
        
        # Générateur aléatoire
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # État des régimes par microzone
        self.regime_state = RegimeState()
        
        # Initialiser les régimes pour toutes les microzones
        # Les probabilités initiales seront modifiées par StaticVectorLoader si disponible
        # (voir GenerationService pour l'intégration)
        for mz_id in microzone_ids:
            regime = self.regime_manager.initialize_regime(mz_id, self.rng)
            self.regime_state.set_regime(mz_id, regime)
    
    def _get_season(self, day: int) -> str:
        """
        Détermine la saison selon le jour.
        
        Jour 1-80 : Hiver
        Jour 81-260 : Intersaison
        Jour 261+ : Été
        
        Args:
            day: Numéro du jour (1-indexé)
        
        Returns:
            Saison ("hiver", "intersaison", "ete")
        """
        if day <= 80:
            return "hiver"
        elif day <= 260:
            return "intersaison"
        else:
            return "ete"
    
    def _get_season_factor(
        self,
        incident_type: str,
        season: str
    ) -> float:
        """
        Retourne le facteur saisonnier selon le type d'incident et la saison.
        
        Args:
            incident_type: Type d'incident
            season: Saison ("hiver", "intersaison", "ete")
        
        Returns:
            Facteur multiplicatif
        """
        factors = {
            INCIDENT_TYPE_INCENDIE: {
                "hiver": 1.3,  # +30% hiver
                "intersaison": 1.0,
                "ete": 0.9  # -10% été
            },
            INCIDENT_TYPE_AGRESSION: {
                "hiver": 0.8,  # -20% hiver
                "intersaison": 1.0,
                "ete": 1.2  # +20% été
            },
            INCIDENT_TYPE_ACCIDENT: {
                "hiver": 1.0,
                "intersaison": 1.075,  # +7.5% intersaison
                "ete": 1.0
            }
        }
        
        return factors.get(incident_type, {}).get(season, 1.0)
    
    def _calculate_neighbor_effect(
        self,
        microzone_id: str,
        incidents_j: Dict[str, Dict[str, tuple]]
    ) -> float:
        """
        Calcule l'effet des 8 zones adjacentes.
        
        Args:
            microzone_id: Identifiant de la microzone
            incidents_j: Incidents J-1 au format (grave, moyen, bénin) par type string
        
        Returns:
            Facteur d'effet voisin (0.0-1.0)
        """
        # Utiliser apply_voisin pour calculer l'effet
        prob_base = (0.0, 0.0, 0.0)
        prob_voisin = apply_voisin(
            prob_base,
            incidents_j,
            self.matrices_voisin,
            microzone_id
        )
        
        # Extraire le facteur (prob_voisin = prob_base * (1 + effet))
        # Si prob_base = 0, on utilise une heuristique
        total_effect = sum(prob_voisin)
        if total_effect > 0:
            return min(1.0, total_effect * 0.1)  # Normaliser
        
        return 0.0
    
    def _calculate_pattern_effect(
        self,
        microzone_id: str,
        patterns_actifs: Optional[Dict[str, List[dict]]] = None
    ) -> float:
        """
        Calcule l'effet des patterns détectés (4j/7j → occurrence 7j/60j).
        
        Args:
            microzone_id: Identifiant de la microzone
            patterns_actifs: Patterns actifs (Story 1.4.4.5)
        
        Returns:
            Facteur d'effet pattern (0.0-1.0)
        """
        if patterns_actifs is None:
            return 0.0
        
        patterns = patterns_actifs.get(microzone_id, [])
        if not patterns:
            return 0.0
        
        # Effet cumulatif des patterns (7j, 60j) — avec réduction configurable (hors réaléatoirisation)
        # Effet de base : 0.1 par pattern ; après réduction : on garde (1 - reduction) de l'effet
        keep = 1.0 - self.reduction_effet_patterns
        effet_par_pattern = 0.1 * keep  # ex. 0.8 réduction → 0.02 par pattern
        effect = 0.0
        for pattern in patterns:
            pattern_type = pattern.get("type", "")
            if pattern_type in ["7j", "60j"]:
                effect += effet_par_pattern

        return min(1.0, effect)
    
    def generate_vectors_for_day(
        self,
        day: int,
        vectors_j_minus_1: Dict[str, Dict[str, Vector]],
        patterns_actifs: Optional[Dict[str, List[dict]]] = None,
        dynamic_state: Optional[any] = None,
        effets_reduction: Optional[Dict[int, float]] = None,
        prix_m2_modulator: Optional[any] = None,
        vectors_state: Optional[any] = None,
        events_grave: Optional[List] = None,
        events_positifs: Optional[List] = None,
        variabilite_locale: float = 0.5,
        facteur_intensite: float = 1.0,
        proba_crise: float = 0.1,
    ) -> Dict[str, Dict[str, Vector]]:
        """
        Génère les vecteurs pour un jour donné.

        Scénario (pessimiste/standard/optimiste) : facteur_intensite appliqué après
        le calcul d'intensité ; proba_crise appliquée à la transition de régime (Crise).

        Args:
            day: Numéro du jour (1-indexé)
            vectors_j_minus_1: Vecteurs du jour J-1 par microzone et type
            patterns_actifs: Patterns actifs (optionnel)
            dynamic_state: État dynamique (optionnel)
            facteur_intensite: Facteur scénario (1.0 = standard, <1 optimiste, >1 pessimiste)
            proba_crise: Probabilité régime Crise du scénario (modulation transition)

        Returns:
            Dictionnaire {microzone_id: {type_incident: Vector}}
        """
        # Référence pour scaling proba Crise (config moyen = 0.10)
        PROBA_CRISE_REF = 0.10
        season = self._get_season(day)
        vectors_j = {}
        
        # Stocker paramètres pour MatrixModulator
        self.vectors_state = vectors_state
        self.events_grave = events_grave or []
        self.events_positifs = events_positifs or []
        self.variabilite_locale = variabilite_locale
        
        # Transition des régimes (modulation prix m² + scénario proba_crise)
        for mz_id in self.microzone_ids:
            current_regime = self.regime_state.get_regime_or_default(mz_id)
            regime_idx = self.regime_manager.regime_to_idx[current_regime]
            transition_probas = self.regime_manager.transition_matrix[regime_idx, :].copy()

            # Moduler selon prix m² si disponible (diminution Détérioration/Crise si quartier riche)
            if prix_m2_modulator is not None:
                prob_deterioration = transition_probas[1]
                prob_crise_mat = transition_probas[2]
                prob_deterioration_mod, prob_crise_mod = prix_m2_modulator.moduler_probabilites_regimes(
                    mz_id, prob_deterioration, prob_crise_mat
                )
                transition_probas[1] = prob_deterioration_mod
                transition_probas[2] = prob_crise_mod
                transition_probas[0] = 1.0 - prob_deterioration_mod - prob_crise_mod

            # Scénario : modulation proba régime Crise (Story 2.4.2.1)
            transition_probas[2] = transition_probas[2] * (proba_crise / PROBA_CRISE_REF)
            transition_probas = transition_probas / np.sum(transition_probas)

            new_idx = self.rng.choice(len(self.regime_manager.regimes), p=transition_probas)
            new_regime = self.regime_manager.regimes[new_idx]
            self.regime_state.set_regime(mz_id, new_regime)
        
        # Génération des vecteurs par microzone
        for mz_id in self.microzone_ids:
            vectors_j[mz_id] = {}
            regime = self.regime_state.get_regime_or_default(mz_id)
            regime_factor = self.regime_manager.get_regime_intensity_factor(regime)
            
            # Convertir les vecteurs en format attendu par apply_voisin (avec strings)
            incidents_j_for_voisin = {}
            for mz, vectors in vectors_j_minus_1.items():
                incidents_j_for_voisin[mz] = {}
                for inc_type, vector in vectors.items():
                    # Convertir type en string pour apply_voisin
                    type_str = TYPE_TO_STRING.get(inc_type, inc_type)
                    incidents_j_for_voisin[mz][type_str] = (vector.grave, vector.moyen, vector.benin)
            
            # Effet voisins
            neighbor_effect = self._calculate_neighbor_effect(mz_id, incidents_j_for_voisin)
            
            # Effet patterns
            pattern_effect = self._calculate_pattern_effect(mz_id, patterns_actifs)
            
            # Génération pour chaque type d'incident
            for incident_type in TYPES_INCIDENT:
                season_factor = self._get_season_factor(incident_type, season)
                
                # Calcul de l'intensité λ
                # Utiliser formule calibrée complète si matrix_modulator disponible (Story 2.2.9)
                intensity = self.intensity_calculator.calculate_intensity(
                    microzone_id=mz_id,
                    incident_type=incident_type,
                    regime_factor=regime_factor,
                    season_factor=season_factor,
                    vectors_j_minus_1=vectors_j_minus_1,
                    neighbor_effect=neighbor_effect,
                    pattern_effect=pattern_effect,
                    # Paramètres pour MatrixModulator (Story 2.2.9)
                    vectors_state=getattr(self, 'vectors_state', None),
                    jour=day - 1,  # Convertir 1-indexé en 0-indexé
                    regime=regime,
                    events_grave=getattr(self, 'events_grave', None) or [],
                    events_positifs=getattr(self, 'events_positifs', None) or [],
                    patterns_actifs=patterns_actifs,
                    variabilite_locale=getattr(self, 'variabilite_locale', 0.5)
                )

                # Scénario : facteur d'intensité (pessimiste / standard / optimiste)
                intensity = intensity * facteur_intensite

                # Modulation prix m² (pour agressions principalement)
                if prix_m2_modulator is not None:
                    intensity = prix_m2_modulator.moduler_intensite(
                        mz_id, incident_type, intensity
                    )
                
                # Application effets réduction événements positifs
                if effets_reduction is not None:
                    arr = self.limites_microzone_arrondissement.get(
                        mz_id, _parse_arrondissement_from_microzone_id(mz_id)
                    )
                    reduction = effets_reduction.get(arr, 0.0)
                    if reduction > 0:
                        intensity = intensity * (1.0 - reduction)  # Réduction
                
                # Probabilité de zero-inflation
                zero_inflation_prob = calculate_zero_inflation_probability(
                    intensity,
                    regime_factor
                )
                
                # Échantillonnage Zero-Inflated Poisson
                total_count = sample_zero_inflated_poisson(
                    intensity,
                    zero_inflation_prob,
                    self.rng
                )
                
                # Si total_count = 0, vecteur nul
                if total_count == 0:
                    vectors_j[mz_id][incident_type] = Vector(0, 0, 0)
                    continue
                
                # Déterminer la gravité dominante J-1 pour probabilités croisées
                vector_j_minus_1 = vectors_j_minus_1.get(mz_id, {}).get(incident_type)
                if vector_j_minus_1 is None:
                    dominant_gravity = 0  # Bénin par défaut
                else:
                    # Trouver la gravité dominante
                    gravities = [vector_j_minus_1.grave, vector_j_minus_1.moyen, vector_j_minus_1.benin]
                    dominant_gravity = int(np.argmax(gravities))
                
                # Probabilités croisées
                cross_probs = self.intensity_calculator.get_cross_probabilities(
                    incident_type,
                    dominant_gravity
                )
                
                # Échantillonnage multinomial
                counts = sample_multinomial_counts(
                    total_count,
                    cross_probs,
                    self.rng
                )
                
                # Créer le vecteur (grave, moyen, bénin)
                vectors_j[mz_id][incident_type] = Vector(
                    grave=counts[2],  # grave = index 2
                    moyen=counts[1],  # moyen = index 1
                    benin=counts[0]   # bénin = index 0
                )
        
        return vectors_j
