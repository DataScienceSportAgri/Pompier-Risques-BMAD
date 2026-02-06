"""
Générateur d'événements positifs avec fréquence Poisson.
Story 2.2.8 - Événements positifs et règle prix m²
"""

from typing import Dict, List, Optional

import numpy as np
import pickle
from pathlib import Path

from ..data.constants import INCIDENT_TYPE_AGRESSION
from ..state.events_state import EventsState
from .amelioration_materiel import AmeliorationMateriel
from .fin_travaux import FinTravaux
from .nouvelle_caserne import NouvelleCaserne

# Fréquence événements positifs : Poisson 60 jours (moyenne 1 événement tous les 60 jours)
LAMBDA_POSITIVE_EVENTS = 1.0 / 60.0  # Probabilité par jour

# Types d'événements positifs avec probabilités
PROB_FIN_TRAVAUX = 0.4  # 40%
PROB_NOUVELLE_CASERNE = 0.35  # 35%
PROB_AMELIORATION_MATERIEL = 0.25  # 25%


class PositiveEventGenerator:
    """
    Générateur d'événements positifs avec fréquence Poisson.
    
    Génère des événements positifs (Fin travaux, Nouvelle caserne, Amélioration matériel)
    selon une distribution de Poisson (moyenne 1 événement tous les 60 jours sur Paris).
    """
    
    def __init__(
        self,
        limites_microzone_arrondissement: Dict[str, int],
        arrondissements: List[int],
        seed: Optional[int] = None
    ):
        """
        Initialise le générateur d'événements positifs.
        
        Args:
            limites_microzone_arrondissement: Mapping microzone_id → arrondissement
            arrondissements: Liste des arrondissements disponibles (1-20)
            seed: Seed pour reproductibilité
        """
        self.limites_microzone_arrondissement = limites_microzone_arrondissement
        self.arrondissements = arrondissements
        
        # Générateur aléatoire
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Compteur d'événements pour génération d'IDs uniques
        self.event_counter = 0
    
    def generer_evenements_positifs(
        self,
        jour: int,
        events_state: EventsState
    ) -> List:
        """
        Génère des événements positifs pour un jour donné.
        
        Utilise une distribution de Poisson pour déterminer le nombre d'événements
        (moyenne 1 événement tous les 60 jours sur Paris entière).
        
        Args:
            jour: Numéro du jour (0-indexé)
            events_state: État des événements (sera mis à jour)
        
        Returns:
            Liste des événements positifs générés
        """
        evenements_generes = []
        
        # Tirage Poisson : nombre d'événements pour ce jour
        nb_events = self.rng.poisson(LAMBDA_POSITIVE_EVENTS)
        
        if nb_events == 0:
            return evenements_generes
        
        # Générer nb_events événements
        for _ in range(nb_events):
            # Choisir arrondissement aléatoirement
            arrondissement = self.rng.choice(self.arrondissements)
            
            # Choisir type d'événement selon probabilités
            type_event = self._choisir_type_event()
            
            # Générer ID unique
            self.event_counter += 1
            event_id = f"POS_{self.event_counter:06d}"
            
            # Créer l'événement selon le type
            if type_event == "fin_travaux":
                event = FinTravaux(
                    event_id=event_id,
                    jour=jour,
                    arrondissement=arrondissement,
                    impact_reduction=0.1  # 10% réduction
                )
            elif type_event == "nouvelle_caserne":
                event = NouvelleCaserne(
                    event_id=event_id,
                    jour=jour,
                    arrondissement=arrondissement,
                    impact_reduction=0.15  # 15% réduction
                )
            elif type_event == "amelioration_materiel":
                event = AmeliorationMateriel(
                    event_id=event_id,
                    jour=jour,
                    arrondissement=arrondissement,
                    impact_reduction=0.05  # 5% réduction
                )
            else:
                continue
            
            # Ajouter à l'état
            events_state.add_event(event)
            evenements_generes.append(event)
        
        return evenements_generes
    
    def _choisir_type_event(self) -> str:
        """
        Choisit un type d'événement positif selon les probabilités.
        
        Returns:
            Type d'événement ("fin_travaux", "nouvelle_caserne", "amelioration_materiel")
        """
        rand = self.rng.uniform(0.0, 1.0)
        
        if rand < PROB_FIN_TRAVAUX:
            return "fin_travaux"
        elif rand < PROB_FIN_TRAVAUX + PROB_NOUVELLE_CASERNE:
            return "nouvelle_caserne"
        else:
            return "amelioration_materiel"
    
    def get_effets_reduction_actifs(
        self,
        jour: int,
        events_state: EventsState
    ) -> Dict[int, float]:
        """
        Récupère les effets de réduction actifs par arrondissement pour un jour donné.
        
        Les événements positifs créent des effets qui seront appliqués lors de la
        génération des vecteurs J+1.
        
        Args:
            jour: Numéro du jour (0-indexé)
            events_state: État des événements
        
        Returns:
            Dictionnaire {arrondissement: reduction_factor} (0.0-1.0)
        """
        effets_actifs = {}
        
        # Récupérer tous les événements positifs actifs
        # Un événement est actif si jour est dans [event.jour, event.jour + duration)
        # Pour simplifier, on considère que les événements positifs ont une durée de 1 jour
        # (effet immédiat sur J+1)
        for day_events in events_state._events.values():
            for event in day_events:
                if not isinstance(event, (FinTravaux, NouvelleCaserne, AmeliorationMateriel)):
                    continue
                
                # Vérifier si l'événement est actif (jour suivant le déclenchement)
                if jour == event.jour + 1:
                    arrondissement = event.arrondissement
                    
                    # Cumuler les effets (plusieurs événements peuvent affecter)
                    if arrondissement not in effets_actifs:
                        effets_actifs[arrondissement] = 0.0
                    
                    effets_actifs[arrondissement] += event.impact_reduction
        
        # Limiter à 1.0 maximum (100% réduction)
        for arr in effets_actifs:
            effets_actifs[arr] = min(1.0, effets_actifs[arr])
        
        return effets_actifs
