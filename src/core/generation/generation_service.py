"""
Service de génération de vecteurs journaliers (orchestration complète).
Story 2.2.1 - Génération vecteurs journaliers

Prend en charge scénario (facteur_intensite, proba_crise) et variabilité locale
pour la modulation des intensités et des matrices.
"""

from typing import Any, Dict, List, Optional

import numpy as np

from ..data.vector import Vector
from ..state.simulation_state import SimulationState
from ..state.vectors_state import VectorsState
from ..utils.path_resolver import PathResolver
from ..utils.pickle_utils import save_pickle
from ._loader import load_base_intensities, load_matrices_for_generation
from .congestion_calculator import CongestionCalculator
from .intensity_calculator import IntensityCalculator
from .regime_manager import RegimeManager
from .static_vector_loader import StaticVectorLoader
from .vector_generator import VectorGenerator
from ..events.event_generator import EventGenerator
from ..events.positive_event_generator import PositiveEventGenerator
from ..events.prix_m2_modulator import PrixM2Modulator
from ..evolution import evoluer_incidents_alcool_J1, evoluer_incidents_nuit_J1

_DEFAULT_SCENARIO_CONFIG = {"facteur_intensite": 1.0, "proba_crise": 0.1}

# Mapping singulier (vecteurs) → pluriel (évolution)
_TYPE_TO_EVOLUTION = {"agression": "agressions", "incendie": "incendies", "accident": "accidents"}

# Mapping des types d'incidents
TYPE_MAPPING = {
    "agression": "agression",
    "incendie": "incendie",
    "accident": "accident"
}


def _microzone_to_arrondissement_fallback(microzone_ids: List[str]) -> Dict[str, int]:
    """Mapping microzone_id → arrondissement (1..20) quand limites.pkl est absent.
    Formats : MZ_11_01 → 11 ; MZ031 (MZ + 3 chiffres, 5 microzones/arr) → 7."""
    out: Dict[str, int] = {}
    for mz_id in microzone_ids:
        try:
            parts = mz_id.split("_")
            if len(parts) >= 2:
                out[mz_id] = max(1, min(20, int(parts[1])))
            elif (
                len(mz_id) == 5
                and mz_id.startswith("MZ")
                and mz_id[2:].isdigit()
            ):
                idx = int(mz_id[2:])
                out[mz_id] = max(1, min(20, (idx - 1) // 5 + 1))
            else:
                out[mz_id] = 1
        except (ValueError, TypeError):
            out[mz_id] = 1
    return out


class GenerationService:
    """
    Service orchestrant la génération de vecteurs journaliers.
    
    Utilise le modèle Zero-Inflated Poisson avec régimes cachés et triple pattern matricielle.
    """
    
    def __init__(
        self,
        microzone_ids: List[str],
        seed: Optional[int] = None,
        base_intensities: Optional[Dict[str, Dict[str, float]]] = None,
        matrices: Optional[Dict[str, Any]] = None,
        scenario_config: Optional[Dict[str, float]] = None,
        variabilite_locale: float = 0.5,
        debug_prints: bool = False,
        lissage_alpha: float = 0.7,
        reduction_base_matrices: float = 0.80,
        reduction_effet_patterns: float = 0.8,
    ):
        """
        Initialise le service de génération.

        Args:
            microzone_ids: Liste des identifiants de microzones
            seed: Seed pour reproductibilité
            base_intensities: Intensités de base (si None, chargées depuis fichiers)
            matrices: Matrices (si None, chargées depuis fichiers)
            scenario_config: {"facteur_intensite": float, "proba_crise": float} ou None → défaut
            variabilite_locale: Variabilité locale (0.3 faible, 0.5 moyen, 0.7 fort)
            debug_prints: Si True, affiche des prints lors des événements graves, positifs, microzones > 6
            lissage_alpha: Alpha de lissage vecteurs statiques (1=aucun, 0.7≈−30% disparité)
            reduction_base_matrices: Décorélation de base (0.8 = 80 % réduction de l'effet des matrices)
            reduction_effet_patterns: Réduction des effets patterns 4j/7j/60j (0.8 = 80 % de réduction, 20 % conservé)
        """
        self.microzone_ids = microzone_ids
        self.scenario_config = scenario_config or _DEFAULT_SCENARIO_CONFIG
        self.variabilite_locale = variabilite_locale
        self.debug_prints = debug_prints

        # Charger les données si non fournies
        if matrices is None:
            matrices = load_matrices_for_generation()

        self.matrices_inter_type = matrices.get("matrices_inter_type", {})

        # Intensités de base : si non fournies, charger avec recalibration pour éviter trop d'incidents
        # Priorité : StaticVectorLoader.get_base_intensities_dict() (recalibration en moyenne par type)
        if base_intensities is None:
            try:
                self.static_vector_loader = StaticVectorLoader(lissage_alpha=lissage_alpha)
                base_intensities = self.static_vector_loader.get_base_intensities_dict(microzone_ids)
            except (FileNotFoundError, IOError):
                self.static_vector_loader = None
                base_intensities = load_base_intensities()
        else:
            # base_intensities fourni (ex. tests) : ne pas écraser
            try:
                self.static_vector_loader = StaticVectorLoader(lissage_alpha=lissage_alpha)
            except (FileNotFoundError, IOError):
                self.static_vector_loader = None

        # Initialiser les composants
        self.regime_manager = RegimeManager()

        # Créer MatrixModulator pour Story 2.2.9 (realaléatoirisation injectée au run — Story 2.4.3.4)
        from .matrix_modulator import MatrixModulator
        matrix_modulator = MatrixModulator(
            matrices_intra_type=matrices.get("matrices_intra_type", {}),
            matrices_inter_type=matrices.get("matrices_inter_type", {}),
            matrices_voisin=matrices.get("matrices_voisin", {}),
            variabilite_locale=variabilite_locale,
            realaléatoirisation_state=None,
            reduction_base_matrices=reduction_base_matrices,
            reduction_effet_patterns=reduction_effet_patterns,
        )
        
        self.intensity_calculator = IntensityCalculator(
            base_intensities=base_intensities,
            matrix_modulator=matrix_modulator
        )
        self._matrix_modulator = matrix_modulator
        
        # Charger limites microzone → arrondissement (avant VectorGenerator et EventGenerator)
        try:
            from ...services.casualty_calculator import CasualtyCalculator
            limites_microzone_arrondissement = CasualtyCalculator.load_limites_microzone_arrondissement()
        except FileNotFoundError:
            limites_microzone_arrondissement = _microzone_to_arrondissement_fallback(microzone_ids)
        
        # Créer le générateur (avec limites pour effets_reduction par arrondissement)
        self.generator = VectorGenerator(
            regime_manager=self.regime_manager,
            intensity_calculator=self.intensity_calculator,
            base_intensities=base_intensities,
            matrices_intra_type=matrices.get("matrices_intra_type", {}),
            matrices_inter_type=matrices.get("matrices_inter_type", {}),
            matrices_voisin=matrices.get("matrices_voisin", {}),
            matrices_saisonnalite=matrices.get("matrices_saisonnalite", {}),
            microzone_ids=microzone_ids,
            seed=seed,
            limites_microzone_arrondissement=limites_microzone_arrondissement,
            reduction_effet_patterns=reduction_effet_patterns,
        )
        
        # Réinitialiser les régimes avec probabilités modifiées selon vecteurs statiques (Story 2.2.10)
        # Cela remplace l'initialisation par défaut faite dans VectorGenerator.__init__
        if self.static_vector_loader is not None:
            for mz_id in microzone_ids:
                probas_regimes = self.static_vector_loader.calculer_probabilites_regimes(mz_id)
                regime = self.regime_manager.initialize_regime(mz_id, self.generator.rng, probas_regimes)
                self.generator.regime_state.set_regime(mz_id, regime)
        
        # Charger congestion statique et créer calculateur de congestion
        try:
            congestion_statique = CongestionCalculator.load_static_congestion()
        except FileNotFoundError:
            # Si pas disponible, utiliser valeurs par défaut
            congestion_statique = {mz_id: 0.5 for mz_id in microzone_ids}
        
        self.congestion_calculator = CongestionCalculator(
            congestion_statique=congestion_statique,
            microzone_ids=microzone_ids,
            matrices_voisin=matrices.get("matrices_voisin", {}),
            seed=seed
        )
        
        # Créer générateur d'événements
        self.event_generator = EventGenerator(
            limites_microzone_arrondissement=limites_microzone_arrondissement,
            matrices_voisin=matrices.get("matrices_voisin", {}),
            seed=seed
        )
        
        # Créer générateur d'événements positifs
        # Extraire arrondissements uniques depuis limites_microzone_arrondissement
        arrondissements = sorted(set(limites_microzone_arrondissement.values()))
        self.positive_event_generator = PositiveEventGenerator(
            limites_microzone_arrondissement=limites_microzone_arrondissement,
            arrondissements=arrondissements,
            seed=seed
        )
        
        # Créer modulateur prix m²
        try:
            self.prix_m2_modulator = PrixM2Modulator()
        except (FileNotFoundError, IOError):
            # Si pas disponible, créer avec données vides
            self.prix_m2_modulator = PrixM2Modulator(prix_m2_data={})

    def set_realaléatoirisation_state(self, state):  # Story 2.4.3.4
        """Injecte l'état des patterns de réaléatoirisation pour le run en cours."""
        self._matrix_modulator.realaléatoirisation_state = state
    
    def _vectors_to_incidents_j(
        self, vectors_j: Dict[str, Dict[str, Vector]]
    ) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Convertit les vecteurs du jour au format incidents_J attendu par l'évolution.
        incidents_J[mz][type_plural][gravity] = count avec type in (agressions, incendies, accidents).
        """
        incidents_J: Dict[str, Dict[str, Dict[str, int]]] = {}
        for mz_id in self.microzone_ids:
            vecs = vectors_j.get(mz_id, {})
            incidents_J[mz_id] = {}
            for inc_singular, inc_plural in _TYPE_TO_EVOLUTION.items():
                vec = vecs.get(inc_singular)
                if vec is None:
                    vec = Vector(0, 0, 0)
                incidents_J[mz_id][inc_plural] = {
                    "benin": vec.benin,
                    "moyen": vec.moyen,
                    "grave": vec.grave,
                }
        return incidents_J

    def _get_season(self, day: int) -> str:
        """Retourne la saison (hiver, intersaison, ete) pour un jour 1-indexé."""
        if day <= 80:
            return "hiver"
        if day <= 260:
            return "intersaison"
        return "ete"

    def generate_day(
        self,
        day: int,
        simulation_state: SimulationState,
        patterns_actifs: Optional[Dict[str, List[dict]]] = None
    ) -> None:
        """
        Génère les vecteurs pour un jour et les ajoute au SimulationState.
        
        Args:
            day: Numéro du jour (0-indexé pour SimulationState, converti en 1-indexé)
            simulation_state: État de simulation à mettre à jour
            patterns_actifs: Patterns actifs (optionnel)
        """
        # Convertir jour 0-indexé en 1-indexé pour la génération
        day_1_indexed = day + 1
        
        # Récupérer les vecteurs J-1
        vectors_j_minus_1 = {}
        if day > 0:
            day_minus_1 = day - 1
            for mz_id in self.microzone_ids:
                vectors_j_minus_1[mz_id] = {}
                for inc_type in ["agression", "incendie", "accident"]:
                    vector = simulation_state.vectors_state.get_vector(
                        mz_id, day_minus_1, inc_type
                    )
                    if vector is None:
                        vector = Vector(0, 0, 0)
                    vectors_j_minus_1[mz_id][inc_type] = vector
        else:
            # Jour 0 : initialiser avec vecteurs nuls
            for mz_id in self.microzone_ids:
                vectors_j_minus_1[mz_id] = {
                    "agression": Vector(0, 0, 0),
                    "incendie": Vector(0, 0, 0),
                    "accident": Vector(0, 0, 0)
                }
        
        # Utiliser les patterns actifs du simulation_state si non fournis
        if patterns_actifs is None:
            patterns_actifs = simulation_state.patterns_actifs
        
        # Effets de réduction (événements positifs actifs sur J+1)
        if day > 0:
            effets_reduction = self.positive_event_generator.get_effets_reduction_actifs(
                day - 1, simulation_state.events_state
            )
        else:
            effets_reduction = None

        # Générer les vecteurs (scénario et variabilité locale appliqués)
        facteur = self.scenario_config.get("facteur_intensite", 1.0)
        proba_crise = self.scenario_config.get("proba_crise", 0.1)
        vectors_j = self.generator.generate_vectors_for_day(
            day=day_1_indexed,
            vectors_j_minus_1=vectors_j_minus_1,
            patterns_actifs=patterns_actifs or simulation_state.patterns_actifs,
            dynamic_state=simulation_state.dynamic_state,
            effets_reduction=effets_reduction,
            prix_m2_modulator=self.prix_m2_modulator,
            vectors_state=simulation_state.vectors_state,
            events_grave=simulation_state.events_state.get_grave_events_for_day(day),
            events_positifs=simulation_state.events_state.get_positive_events_for_day(day),
            variabilite_locale=self.variabilite_locale,
            facteur_intensite=facteur,
            proba_crise=proba_crise,
        )
        
        # Ajouter au SimulationState
        for mz_id, vectors in vectors_j.items():
            for inc_type, vector in vectors.items():
                simulation_state.vectors_state.set_vector(
                    microzone_id=mz_id,
                    jour=day,
                    type_incident=inc_type,
                    vector=vector
                )
        
        # Calculer congestion après génération des vecteurs
        # vectors_j utilise les constantes (INCIDENT_TYPE_*), congestion_calculator aussi
        # Pas besoin de conversion
        
        # Récupérer événements du jour
        events_grave = simulation_state.events_state.get_grave_events_for_day(day)
        events_positifs = simulation_state.events_state.get_positive_events_for_day(day)
        
        # Récupérer incidents nocturnes depuis dynamic_state
        incidents_nuit = simulation_state.dynamic_state.incidents_nuit if hasattr(simulation_state.dynamic_state, 'incidents_nuit') else None
        
        # Calculer congestion
        congestion_jour = self.congestion_calculator.calculate_congestion_for_day(
            day=day,
            vectors=vectors_j,
            events_grave=events_grave,
            events_positifs=events_positifs,
            incidents_nuit=incidents_nuit
        )
        
        # Mettre à jour dynamic_state.trafic (normaliser [0, 1])
        for mz_id, congestion in congestion_jour.items():
            simulation_state.dynamic_state.trafic[mz_id] = min(1.0, congestion / 5.0)
        
        # Générer événements graves juste après les vecteurs
        evenements_graves = self.event_generator.generer_evenements_graves(
            day, vectors_j, simulation_state.events_state
        )
        if self.debug_prints and evenements_graves:
            print(f"  [J{day}] Événements graves: {len(evenements_graves)} — {evenements_graves}")
        
        # Appliquer effets congestion temps réel (avant Golden Hour)
        if evenements_graves:
            self.event_generator.appliquer_effets_congestion_temps_reel(
                day, evenements_graves, self.congestion_calculator
            )
        
        # Les effets sur vecteurs suivants seront appliqués lors de la génération
        # des jours suivants via les patterns actifs (Story 2.2.2)
        # Les événements sont stockés dans events_state et peuvent être utilisés
        # pour modifier les patterns de génération via get_effets_vecteurs_actifs()
        
        # Générer événements positifs (après événements graves)
        evenements_positifs = self.positive_event_generator.generer_evenements_positifs(
            day, simulation_state.events_state
        )
        if self.debug_prints and evenements_positifs:
            print(f"  [J{day}] Événements positifs: {len(evenements_positifs)} — {evenements_positifs}")
        
        # Microzones avec somme des 3 vecteurs (agr+inc+acc) > 6
        if self.debug_prints:
            for mz_id, vecs in vectors_j.items():
                total = sum(v.total() for v in vecs.values())
                if total > 6:
                    print(f"  [J{day}] Microzone {mz_id} total incidents = {total} (agr+inc+acc)")

        # Évolution incidents_nuit et incidents_alcool J→J+1 (Story 1.4.4.2)
        # Convertisse les vecteurs du jour en format incidents_J pour l'évolution
        incidents_J = self._vectors_to_incidents_j(vectors_j)
        saison = self._get_season(day_1_indexed)
        dynamic_state = simulation_state.dynamic_state
        dynamic_state.ensure_microzones(self.microzone_ids)

        new_nuit = evoluer_incidents_nuit_J1(
            dynamic_state.incidents_nuit,
            incidents_J,
            self.matrices_inter_type,
            self.microzone_ids,
            saison,
            rng=self.generator.rng,
        )
        dynamic_state.incidents_nuit.update(new_nuit)

        new_alcool = evoluer_incidents_alcool_J1(
            dynamic_state.incidents_alcool,
            incidents_J,
            self.matrices_inter_type,
            self.microzone_ids,
            saison,
            rng=self.generator.rng,
        )
        dynamic_state.incidents_alcool.update(new_alcool)

        # Les effets des événements positifs seront appliqués lors de la génération J+1
        # via get_effets_reduction_actifs() qui sera appelé dans generate_day pour day+1
    
    def generate_multiple_days(
        self,
        simulation_state: SimulationState,
        start_day: int,
        num_days: int,
        patterns_actifs: Optional[Dict[str, List[dict]]] = None,
        on_day_completed: Optional[Any] = None,
    ) -> None:
        """
        Génère les vecteurs pour plusieurs jours consécutifs.

        Args:
            simulation_state: État de simulation à mettre à jour
            start_day: Jour de départ (0-indexé)
            num_days: Nombre de jours à générer
            patterns_actifs: Patterns actifs (optionnel)
            on_day_completed: Callback(day_index, state) appelé après chaque jour (optionnel)
        """
        for day in range(start_day, start_day + num_days):
            self.generate_day(day, simulation_state, patterns_actifs)
            simulation_state.current_day = day + 1
            if on_day_completed is not None:
                on_day_completed(day, simulation_state)
    
    def save_congestion(
        self,
        run_id: str,
        output_dir: Optional[str] = None
    ) -> None:
        """
        Sauvegarde la table de congestion.
        
        Args:
            run_id: Identifiant du run
            output_dir: Dossier de sortie (optionnel)
        """
        self.congestion_calculator.save(run_id, output_dir)
    
    def save_vectors(
        self,
        simulation_state: SimulationState,
        run_id: str,
        output_dir: Optional[str] = None
    ) -> None:
        """
        Sauvegarde les vecteurs générés au format pickle standardisé.
        
        Args:
            simulation_state: État de simulation contenant les vecteurs
            run_id: Identifiant du run
            output_dir: Dossier de sortie (si None, utilise data/intermediate/run_{run_id}/generation/)
        """
        if output_dir is None:
            path = PathResolver.data_intermediate("run_{}".format(run_id), "generation", "vecteurs.pkl")
        else:
            from pathlib import Path
            path = Path(output_dir) / "vecteurs.pkl"
        
        # Extraire les vecteurs du SimulationState
        vectors_data = {}
        for mz_id in self.microzone_ids:
            vectors_data[mz_id] = {}
            days = simulation_state.vectors_state.get_all_days(mz_id)
            for day in days:
                vectors_data[mz_id][day] = {}
                vectors = simulation_state.vectors_state.get_vectors_for_day(mz_id, day)
                for inc_type, vector in vectors.items():
                    vectors_data[mz_id][day][inc_type] = vector.to_list()
        
        # Sauvegarder avec format standardisé
        save_pickle(
            data=vectors_data,
            path=path,
            data_type="vectors",
            description=f"Vecteurs journaliers pour {len(self.microzone_ids)} microzones",
            run_id=run_id,
            schema_version="1.0"
        )
