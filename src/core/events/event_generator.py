"""
Générateur d'événements graves avec caractéristiques probabilistes.
Story 2.2.7 - Événements graves modulables
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from ..data.vector import Vector
from ..generation.congestion_calculator import CongestionCalculator
from ..state.events_state import EventsState
from ..state.vectors_state import VectorsState
from .accident_grave import AccidentGrave
from .agression_grave import AgressionGrave
from .incendie_grave import IncendieGrave

# Probabilités caractéristiques par défaut
PROB_TRAFFIC_SLOWDOWN = 0.7  # 70% probabilité
PROB_CANCEL_SPORTS = 0.3  # 30% probabilité
PROB_INCREASE_BAD_VECTORS = 0.5  # 50% probabilité
PROB_KILL_POMPIER = 0.05  # 5% probabilité (rare)

# Durées par défaut
DUREE_TRAFFIC_SLOWDOWN = 4  # jours
DUREE_CANCEL_SPORTS = 2  # jours
DUREE_INCREASE_BAD_VECTORS = 5  # jours

# Effets par défaut
EFFET_TRAFFIC_SLOWDOWN = 2.0  # ×2 temps
EFFET_INCREASE_BAD_VECTORS = 0.3  # +30% vecteurs
RADIUS_TRAFFIC_SLOWDOWN = 2  # microzones
RADIUS_INCREASE_BAD_VECTORS = 3  # microzones

# Durée événements (3-10 jours)
DUREE_MIN_EVENT = 3
DUREE_MAX_EVENT = 10


class EventGenerator:
    """
    Générateur d'événements graves avec caractéristiques probabilistes.
    
    Génère des événements graves à partir d'incidents graves (vecteur.grave >= 1)
    et applique des effets temporels et spatiaux.
    """
    
    def __init__(
        self,
        limites_microzone_arrondissement: Dict[str, int],
        matrices_voisin: Optional[Dict[str, any]] = None,
        seed: Optional[int] = None
    ):
        """
        Initialise le générateur d'événements.
        
        Args:
            limites_microzone_arrondissement: Mapping microzone_id → arrondissement
            matrices_voisin: Matrices de voisinage (optionnel)
            seed: Seed pour reproductibilité
        """
        self.limites_microzone_arrondissement = limites_microzone_arrondissement
        self.matrices_voisin = matrices_voisin or {}
        
        # Générateur aléatoire
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Compteur d'événements pour génération d'IDs uniques
        self.event_counter = 0
    
    def _generer_caracteristiques(self) -> Dict[str, float]:
        """
        Génère les caractéristiques probabilistes d'un événement.
        
        Returns:
            Dictionnaire des caractéristiques activées
        """
        characteristics = {}
        
        # Traffic slowdown (70% probabilité)
        if self.rng.uniform(0.0, 1.0) < PROB_TRAFFIC_SLOWDOWN:
            characteristics['traffic_slowdown'] = EFFET_TRAFFIC_SLOWDOWN
            characteristics['traffic_slowdown_duration'] = DUREE_TRAFFIC_SLOWDOWN
            characteristics['traffic_slowdown_radius'] = RADIUS_TRAFFIC_SLOWDOWN
        
        # Cancel sports (30% probabilité)
        if self.rng.uniform(0.0, 1.0) < PROB_CANCEL_SPORTS:
            characteristics['cancel_sports'] = 1.0
            characteristics['cancel_sports_duration'] = DUREE_CANCEL_SPORTS
        
        # Increase bad vectors (50% probabilité)
        if self.rng.uniform(0.0, 1.0) < PROB_INCREASE_BAD_VECTORS:
            characteristics['increase_bad_vectors'] = EFFET_INCREASE_BAD_VECTORS
            characteristics['increase_bad_vectors_duration'] = DUREE_INCREASE_BAD_VECTORS
            characteristics['increase_bad_vectors_radius'] = RADIUS_INCREASE_BAD_VECTORS
        
        # Kill pompier (5% probabilité, rare)
        if self.rng.uniform(0.0, 1.0) < PROB_KILL_POMPIER:
            characteristics['kill_pompier'] = 1.0
        
        return characteristics
    
    def _calculer_casualties_base(
        self,
        type_incident: str,
        vector: Vector
    ) -> int:
        """
        Calcule le nombre de morts de base pour un événement.
        
        Args:
            type_incident: Type d'incident
            vector: Vecteur d'incidents
        
        Returns:
            Nombre de morts de base
        """
        # Pour simplifier, casualties_base = nombre d'incidents graves
        # En réalité, cela pourrait être plus complexe
        return vector.grave
    
    def _generer_duree(self) -> int:
        """
        Génère une durée aléatoire pour l'événement (3-10 jours).
        
        Returns:
            Durée en jours
        """
        return int(self.rng.integers(DUREE_MIN_EVENT, DUREE_MAX_EVENT + 1))
    
    def _trouver_microzones_voisines(
        self,
        microzone_id: str,
        radius: int
    ) -> List[str]:
        """
        Trouve les microzones voisines dans un rayon donné.
        
        Args:
            microzone_id: Identifiant de la microzone
            radius: Rayon de recherche
        
        Returns:
            Liste des microzones voisines
        """
        voisin_data = self.matrices_voisin.get(microzone_id, {})
        voisins = voisin_data.get("voisins", [])
        
        # Pour simplifier, on retourne les voisins directs
        # En réalité, il faudrait implémenter un algorithme de recherche par rayon
        if radius == 1:
            return voisins
        else:
            # Pour radius > 1, on pourrait étendre récursivement
            # Pour l'instant, on retourne les voisins directs
            return voisins
    
    def generer_evenements_graves(
        self,
        jour: int,
        vectors: Dict[str, Dict[str, Vector]],
        events_state: EventsState
    ) -> List:
        """
        Génère des événements graves à partir des vecteurs du jour.
        
        Un événement grave est généré si vecteur.grave >= 1 pour un type d'incident.
        
        Args:
            jour: Numéro du jour (0-indexé)
            vectors: Vecteurs par microzone et type d'incident
            events_state: État des événements (sera mis à jour)
        
        Returns:
            Liste des événements graves générés
        """
        evenements_generes = []
        
        for microzone_id, vectors_mz in vectors.items():
            arrondissement = self.limites_microzone_arrondissement.get(microzone_id)
            
            if arrondissement is None:
                continue
            
            # Vérifier chaque type d'incident
            for type_incident, vector in vectors_mz.items():
                if vector is None or vector.grave == 0:
                    continue
                
                # Générer un événement grave pour chaque incident grave
                for _ in range(vector.grave):
                    # Générer caractéristiques
                    characteristics = self._generer_caracteristiques()
                    
                    # Calculer casualties_base
                    casualties_base = self._calculer_casualties_base(type_incident, vector)
                    
                    # Générer durée
                    duration = self._generer_duree()
                    
                    # Générer ID unique
                    self.event_counter += 1
                    event_id = f"EVT_{self.event_counter:06d}"
                    
                    # Créer l'événement selon le type
                    if type_incident == INCIDENT_TYPE_ACCIDENT:
                        event = AccidentGrave(
                            event_id=event_id,
                            jour=jour,
                            arrondissement=arrondissement,
                            duration=duration,
                            casualties_base=casualties_base,
                            characteristics=characteristics
                        )
                    elif type_incident == INCIDENT_TYPE_INCENDIE:
                        event = IncendieGrave(
                            event_id=event_id,
                            jour=jour,
                            arrondissement=arrondissement,
                            duration=duration,
                            casualties_base=casualties_base,
                            characteristics=characteristics
                        )
                    elif type_incident == INCIDENT_TYPE_AGRESSION:
                        event = AgressionGrave(
                            event_id=event_id,
                            jour=jour,
                            arrondissement=arrondissement,
                            duration=duration,
                            casualties_base=casualties_base,
                            characteristics=characteristics
                        )
                    else:
                        continue
                    
                    # Ajouter à l'état
                    events_state.add_event(event)
                    evenements_generes.append(event)
        
        return evenements_generes
    
    def appliquer_effets_congestion_temps_reel(
        self,
        jour: int,
        evenements: List,
        congestion_calculator: CongestionCalculator
    ) -> None:
        """
        Applique les effets des événements graves sur la congestion en temps réel.
        
        Les événements avec 'traffic_slowdown' modifient la congestion du jour
        pour que le calcul Golden Hour utilise la nouvelle congestion.
        
        Args:
            jour: Numéro du jour (0-indexé)
            evenements: Liste des événements graves générés
            congestion_calculator: Calculateur de congestion
        """
        for event in evenements:
            if 'traffic_slowdown' not in event.characteristics:
                continue
            
            effet = event.characteristics.get('traffic_slowdown', 1.0)
            radius = event.characteristics.get('traffic_slowdown_radius', 1)
            
            # Trouver microzones affectées
            # Pour simplifier, on utilise l'arrondissement de l'événement
            # En réalité, il faudrait trouver toutes les microzones de l'arrondissement
            arrondissement = event.arrondissement
            
            # Trouver microzones de cet arrondissement
            microzones_arr = [
                mz_id for mz_id, arr in self.limites_microzone_arrondissement.items()
                if arr == arrondissement
            ]
            
            # Appliquer effet sur chaque microzone
            for microzone_id in microzones_arr:
                # Récupérer congestion actuelle
                congestion_actuelle = congestion_calculator.get_congestion(microzone_id, jour)
                
                if congestion_actuelle is not None:
                    # Appliquer effet traffic slowdown
                    nouvelle_congestion = congestion_actuelle * effet
                    
                    # Mettre à jour en temps réel
                    congestion_calculator.update_congestion_realtime(
                        microzone_id, jour, nouvelle_congestion
                    )
                
                # Appliquer effet sur voisins (gravité décroissante)
                voisins = self._trouver_microzones_voisines(microzone_id, radius)
                for voisin_id in voisins:
                    if voisin_id in microzones_arr:  # Seulement voisins du même arrondissement
                        continue
                    
                    congestion_voisin = congestion_calculator.get_congestion(voisin_id, jour)
                    if congestion_voisin is not None:
                        # Effet décroissant avec distance
                        effet_voisin = 1.0 + (effet - 1.0) * 0.5  # 50% de l'effet
                        nouvelle_congestion_voisin = congestion_voisin * effet_voisin
                        
                        congestion_calculator.update_congestion_realtime(
                            voisin_id, jour, nouvelle_congestion_voisin
                        )
    
    def get_effets_vecteurs_actifs(
        self,
        jour: int,
        events_state: EventsState
    ) -> Dict[str, Dict[str, float]]:
        """
        Récupère les effets actifs sur les vecteurs pour un jour donné.
        
        Les événements avec 'increase_bad_vectors' créent des effets qui seront
        appliqués lors de la génération des vecteurs suivants.
        
        Args:
            jour: Numéro du jour (0-indexé)
            events_state: État des événements
        
        Returns:
            Dictionnaire {microzone_id: {'effet': float, 'radius': int}}
        """
        effets_actifs = {}
        
        # Récupérer tous les événements graves actifs
        # Un événement est actif si jour est dans [event.jour, event.jour + event.duration)
        for day_events in events_state._events.values():
            for event in day_events:
                if not hasattr(event, 'characteristics'):
                    continue
                
                if 'increase_bad_vectors' not in event.characteristics:
                    continue
                
                # Vérifier si l'événement est encore actif
                jour_fin = event.jour + event.duration
                if jour < event.jour or jour >= jour_fin:
                    continue
                
                effet = event.characteristics.get('increase_bad_vectors', 0.0)
                radius = event.characteristics.get('increase_bad_vectors_radius', 3)
                
                # Trouver microzones affectées
                arrondissement = event.arrondissement
                microzones_arr = [
                    mz_id for mz_id, arr in self.limites_microzone_arrondissement.items()
                    if arr == arrondissement
                ]
                
                # Enregistrer effets pour microzones de l'arrondissement
                for microzone_id in microzones_arr:
                    if microzone_id not in effets_actifs:
                        effets_actifs[microzone_id] = {'effet': 0.0, 'radius': 0}
                    
                    # Cumuler les effets (plusieurs événements peuvent affecter)
                    effets_actifs[microzone_id]['effet'] += effet
                    effets_actifs[microzone_id]['radius'] = max(effets_actifs[microzone_id]['radius'], radius)
        
        return effets_actifs
