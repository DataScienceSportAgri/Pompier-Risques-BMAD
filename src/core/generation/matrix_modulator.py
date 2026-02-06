"""
Modulateur de matrices pour calcul intensités calibrées.
Story 2.2.9 - Trois matrices de modulation (gravité, croisée, voisins)
Story 2.4.3.4 - Réaléatoirisation : atténuation (1 - r·α) par microzone
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    from ..state.realaléatoirisation_state import RealaléatoirisationState

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

TYPES_INCIDENT = [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]

# Décroissance exponentielle pour historique 7 jours
DECAY_FACTOR = 0.85  # Chaque jour précédent a 85% du poids du jour suivant

# Pondération voisins (grave ×1.0, moyen ×0.5, bénin ×0.2)
POIDS_VOISIN = (0.2, 0.5, 1.0)  # bénin, moyen, grave

# Caps pour intensités calibrées
MIN_FACTOR = 0.1  # ×0.1 minimum
MAX_FACTOR = 3.0  # ×3.0 maximum


class MatrixModulator:
    """
    Modulateur de matrices pour calcul intensités calibrées.
    
    Calcule trois facteurs de modulation :
    1. Facteur gravité microzone (historique 7 jours, décroissance exponentielle)
    2. Facteur types croisés (effet nb total autres types, conformité J-1)
    3. Facteur voisins (8 zones radius 1, pondération, variabilité locale)
    """
    
    def __init__(
        self,
        matrices_intra_type: Dict[str, Dict[str, np.ndarray]],
        matrices_inter_type: Dict[str, Dict[str, Dict[str, List[float]]]],
        matrices_voisin: Dict[str, any],
        variabilite_locale: float = 0.5,
        realaléatoirisation_state: Optional["RealaléatoirisationState"] = None,
        reduction_base_matrices: float = 0.80,
        reduction_effet_patterns: float = 0.8,
    ):
        """
        Initialise le modulateur de matrices.

        Args:
            matrices_intra_type: Matrices intra-type (gravité)
            matrices_inter_type: Matrices inter-type (types croisés)
            matrices_voisin: Matrices voisins
            variabilite_locale: Variabilité locale (0.3 faible, 0.5 moyen, 0.7 important)
            realaléatoirisation_state: État des patterns de réaléatoirisation (Story 2.4.3.4), optionnel
            reduction_base_matrices: Décorélation de base (0.8 = 80 % de réduction, on garde 20 % de l'effet)
            reduction_effet_patterns: Réduction des effets patterns 4j/7j/60j (0.8 = 80 % réduction, 20 % conservé)
        """
        self.matrices_intra_type = matrices_intra_type
        self.matrices_inter_type = matrices_inter_type
        self.matrices_voisin = matrices_voisin
        self.variabilite_locale = variabilite_locale
        self.realaléatoirisation_state = realaléatoirisation_state
        self.reduction_base_matrices = reduction_base_matrices
        self.reduction_effet_patterns = reduction_effet_patterns
    
    def calculer_facteur_gravite(
        self,
        microzone_id: str,
        incident_type: str,
        vectors_state: VectorsState,
        jour: int
    ) -> float:
        """
        Calcule le facteur gravité microzone avec historique 7 jours.
        
        Utilise l'historique J-6 à J-1 avec décroissance exponentielle.
        Même type, même microzone.
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident
            vectors_state: État des vecteurs (historique)
            jour: Jour actuel (0-indexé)
        
        Returns:
            Facteur gravité (≥ 0)
        """
        # Récupérer matrice intra-type
        matrice = self.matrices_intra_type.get(microzone_id, {}).get(incident_type)
        if matrice is None:
            return 1.0  # Pas de modulation si matrice absente
        
        # Calculer historique pondéré sur 7 jours (J-6 à J-1)
        historique_pondere = np.zeros(3)  # [bénin, moyen, grave]
        
        for offset in range(1, 8):  # J-1 à J-7
            jour_historique = jour - offset
            if jour_historique < 0:
                continue
            
            # Récupérer vecteur historique
            vector = vectors_state.get_vector(microzone_id, jour_historique, incident_type)
            if vector is None:
                continue
            
            # Poids avec décroissance exponentielle
            poids = DECAY_FACTOR ** (offset - 1)  # J-1 = 1.0, J-2 = 0.85, J-3 = 0.72, etc.
            
            # Ajouter au historique pondéré
            historique_pondere[0] += vector.benin * poids
            historique_pondere[1] += vector.moyen * poids
            historique_pondere[2] += vector.grave * poids
        
        # Trouver gravité dominante dans l'historique
        if np.sum(historique_pondere) == 0:
            gravite_dominante = 0  # Bénin par défaut
        else:
            gravite_dominante = int(np.argmax(historique_pondere))
        
        # Clamp l'indice
        gravite_dominante = max(0, min(2, gravite_dominante))
        
        # Extraire ligne de la matrice
        ligne = matrice[gravite_dominante, :]
        
        # Calculer facteur (moyenne pondérée des probabilités)
        # Plus de grave dans l'historique → facteur plus élevé
        facteur = np.sum(ligne * np.array([0.5, 1.0, 1.5]))  # Poids croissants
        
        return float(facteur)
    
    def calculer_facteur_croise(
        self,
        microzone_id: str,
        incident_type: str,
        vectors_j_minus_1: Dict[str, Dict[str, Vector]],
        vectors_state: VectorsState,
        jour: int
    ) -> float:
        """
        Calcule le facteur types croisés avec effet nb total et conformité J-1.
        
        Autres types, même microzone, corrélations spécifiques.
        Effet nb total des 2 autres types d'incidents.
        Changement d'effet J+1 selon historique J-1 (conformité).
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident cible
            vectors_j_minus_1: Vecteurs J-1
            vectors_state: État des vecteurs (pour conformité)
            jour: Jour actuel
        
        Returns:
            Facteur croisé (≥ 0)
        """
        # Récupérer matrices inter-type
        matrices_inter = self.matrices_inter_type.get(microzone_id, {})
        matrice_cible = matrices_inter.get(incident_type, {})
        
        if not matrice_cible:
            return 1.0  # Pas de modulation si matrice absente
        
        facteur = 1.0
        vectors_mz = vectors_j_minus_1.get(microzone_id, {})
        
        # Calculer nb total des 2 autres types
        nb_total_autres = 0
        for other_type in TYPES_INCIDENT:
            if other_type != incident_type:
                vector = vectors_mz.get(other_type)
                if vector is not None:
                    nb_total_autres += vector.total()
        
        # Effet nb total autres types
        if nb_total_autres > 0:
            # Récupérer coefficients pour chaque type source
            for source_type in TYPES_INCIDENT:
                if source_type == incident_type:
                    continue
                
                coefs = matrice_cible.get(source_type)
                if not coefs:
                    continue
                
                vector_source = vectors_mz.get(source_type)
                if vector_source is None:
                    continue
                
                # Effet selon gravité (pondération)
                effet_grave = vector_source.grave * (coefs[2] if len(coefs) > 2 else 0.0)
                effet_moyen = vector_source.moyen * (coefs[1] if len(coefs) > 1 else 0.0)
                effet_benin = vector_source.benin * (coefs[0] if len(coefs) > 0 else 0.0)
                
                facteur += effet_grave + effet_moyen + effet_benin
        
        # Conformité J-1 : changement d'effet J+1 selon historique J-1
        vector_j_minus_1 = vectors_mz.get(incident_type)
        if vector_j_minus_1 is not None:
            total_j_minus_1 = vector_j_minus_1.total()
            
            # Plus d'incidents J-1 → plus de conformité (tendance à continuer)
            if total_j_minus_1 > 0:
                facteur_conformite = 1.0 + (total_j_minus_1 * 0.1)  # +10% par incident
                facteur *= facteur_conformite
        
        return float(max(0.0, facteur))
    
    def calculer_facteur_voisins(
        self,
        microzone_id: str,
        incident_type: str,
        vectors_j_minus_1: Dict[str, Dict[str, Vector]],
        variabilite_locale: Optional[float] = None
    ) -> float:
        """
        Calcule le facteur voisins avec pondération et variabilité locale.
        
        8 zones radius 1, pondération grave×1.0, moyen×0.5, bénin×0.2.
        Modulé par variabilité locale.
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident
            vectors_j_minus_1: Vecteurs J-1 par microzone et type
            variabilite_locale: Variabilité locale (si None, utilise self.variabilite_locale)
        
        Returns:
            Facteur voisins (≥ 0)
        """
        variabilite = variabilite_locale if variabilite_locale is not None else self.variabilite_locale
        
        # Récupérer données voisins
        voisin_data = self.matrices_voisin.get(microzone_id, {})
        voisins = voisin_data.get("voisins", [])
        
        if not voisins:
            return 1.0  # Pas de voisins
        
        # Calculer incidents pondérés dans les voisins
        incidents_ponderes = 0.0
        
        for voisin_id in voisins:
            vectors_voisin = vectors_j_minus_1.get(voisin_id, {})
            vector = vectors_voisin.get(incident_type)
            
            if vector is None:
                continue
            
            # Pondération : grave×1.0, moyen×0.5, bénin×0.2
            incidents_ponderes += (
                vector.grave * POIDS_VOISIN[2] +  # grave × 1.0
                vector.moyen * POIDS_VOISIN[1] +  # moyen × 0.5
                vector.benin * POIDS_VOISIN[0]    # bénin × 0.2
            )
        
        # Effet base (seuil d'activation)
        seuil = voisin_data.get("seuil_activation", 5)
        if incidents_ponderes > seuil:
            effet_base = 0.1  # +10% si seuil dépassé
        else:
            effet_base = 0.0
        
        # Modulation par variabilité locale
        # Variabilité faible (0.3) → moins d'influence
        # Variabilité importante (0.7) → plus d'influence
        facteur = 1.0 + (effet_base * variabilite)
        
        return float(facteur)
    
    def calculer_modulations_dynamiques(
        self,
        microzone_id: str,
        incident_type: str,
        regime: str,
        events_grave: List,
        events_positifs: List,
        patterns_actifs: Optional[Dict[str, List[dict]]] = None
    ) -> Dict[str, float]:
        """
        Calcule les modulations dynamiques par événements, incidents, régimes, patterns.
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident
            regime: Régime actuel (Stable, Détérioration, Crise)
            events_grave: Événements graves actifs
            events_positifs: Événements positifs actifs
            patterns_actifs: Patterns actifs
        
        Returns:
            Dictionnaire {facteur_events, facteur_regime, facteur_patterns}
        """
        modulations = {
            'facteur_events': 1.0,
            'facteur_regime': 1.0,
            'facteur_patterns': 1.0
        }
        
        # Modulation par événements graves
        for event in events_grave:
            if 'increase_bad_vectors' in event.characteristics:
                effet = event.characteristics.get('increase_bad_vectors', 0.0)
                modulations['facteur_events'] *= (1.0 + effet)
        
        # Modulation par événements positifs
        for event in events_positifs:
            reduction = event.impact_reduction
            modulations['facteur_events'] *= (1.0 - reduction)
        
        # Modulation par régime
        if regime == REGIME_STABLE:
            modulations['facteur_regime'] = 1.0
        elif regime == REGIME_DETERIORATION:
            modulations['facteur_regime'] = 1.3  # +30%
        elif regime == REGIME_CRISE:
            modulations['facteur_regime'] = 2.0  # +100%
        
        # Modulation par patterns (4j, 7j, 60j) — avec réduction configurable (hors réaléatoirisation)
        # Effet de base : +10 % par pattern ; après réduction : on garde (1 - reduction) de l'effet
        keep = 1.0 - self.reduction_effet_patterns
        effet_par_pattern = 1.0 + 0.1 * keep  # ex. 0.8 réduction → 1 + 0.02 = 1.02
        if patterns_actifs:
            patterns = patterns_actifs.get(microzone_id, [])
            for pattern in patterns:
                pattern_type = pattern.get("type", "")
                if pattern_type in ["4j", "7j", "60j"]:
                    modulations['facteur_patterns'] *= effet_par_pattern

        return modulations
    
    def calculer_intensite_calibree(
        self,
        microzone_id: str,
        incident_type: str,
        lambda_base: float,
        facteur_statique: float,
        vectors_state: VectorsState,
        vectors_j_minus_1: Dict[str, Dict[str, Vector]],
        jour: int,
        regime: str,
        events_grave: List,
        events_positifs: List,
        patterns_actifs: Optional[Dict[str, List[dict]]] = None,
        variabilite_locale: Optional[float] = None
    ) -> float:
        """
        Calcule l'intensité calibrée avec formule complète.
        
        Formule : λ_calibrated = λ_base × facteur_statique × facteur_gravité × 
                  facteur_croisé × facteur_voisins × facteur_long
        
        où facteur_long = facteur_events × facteur_regime × facteur_patterns
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident
            lambda_base: Intensité de base
            facteur_statique: Facteur statique (saisonnalité, etc.)
            vectors_state: État des vecteurs (historique)
            vectors_j_minus_1: Vecteurs J-1
            jour: Jour actuel
            regime: Régime actuel
            events_grave: Événements graves actifs
            events_positifs: Événements positifs actifs
            patterns_actifs: Patterns actifs
            variabilite_locale: Variabilité locale
        
        Returns:
            Intensité calibrée (≥ 0)
        """
        if lambda_base <= 0:
            return 0.0
        
        # Calculer facteurs de modulation (gravité, croisé, voisins)
        facteur_gravite = self.calculer_facteur_gravite(
            microzone_id, incident_type, vectors_state, jour
        )
        
        facteur_croise = self.calculer_facteur_croise(
            microzone_id, incident_type, vectors_j_minus_1, vectors_state, jour
        )
        
        facteur_voisins = self.calculer_facteur_voisins(
            microzone_id, incident_type, vectors_j_minus_1, variabilite_locale
        )
        
        # Décorélation de base : on ne garde que (1 - reduction_base) de l'effet des matrices (ex. 80 % réduction → 20 % conservé)
        keep_base = 1.0 - self.reduction_base_matrices
        facteur_gravite = 1.0 + (facteur_gravite - 1.0) * keep_base
        facteur_croise = 1.0 + (facteur_croise - 1.0) * keep_base
        facteur_voisins = 1.0 + (facteur_voisins - 1.0) * keep_base
        # Story 2.4.3.4 : réaléatoirisation — en plus de la base, atténuer par (1 - r·α) quand un pattern est actif
        # F' = 1 + (F_base - 1) * dampening ; dampening=1 → pas de pattern, dampening<1 → réduction supplémentaire
        if self.realaléatoirisation_state is not None:
            dampening = self.realaléatoirisation_state.get_matrix_dampening(jour, microzone_id)
            facteur_gravite = 1.0 + (facteur_gravite - 1.0) * dampening
            facteur_croise = 1.0 + (facteur_croise - 1.0) * dampening
            facteur_voisins = 1.0 + (facteur_voisins - 1.0) * dampening
        
        # Modulations dynamiques
        modulations = self.calculer_modulations_dynamiques(
            microzone_id, incident_type, regime, events_grave, events_positifs, patterns_actifs
        )
        facteur_long = (
            modulations['facteur_events'] *
            modulations['facteur_regime'] *
            modulations['facteur_patterns']
        )
        
        # Formule complète
        lambda_calibrated = (
            lambda_base *
            facteur_statique *
            facteur_gravite *
            facteur_croise *
            facteur_voisins *
            facteur_long
        )
        
        # Caps : Min ×0.1, Max ×3.0
        lambda_calibrated = max(MIN_FACTOR * lambda_base, min(MAX_FACTOR * lambda_base, lambda_calibrated))
        
        return float(lambda_calibrated)
    
    def calculer_normalisation(
        self,
        microzone_id: str,
        lambda_calibrated: Dict[str, float]
    ) -> float:
        """
        Calcule la normalisation Z(t) = Σ_{τ,g} λ_calibrated(τ,g).
        
        Args:
            microzone_id: Identifiant de la microzone
            lambda_calibrated: Intensités calibrées par type d'incident
        
        Returns:
            Normalisation Z(t)
        """
        return float(sum(lambda_calibrated.values()))
