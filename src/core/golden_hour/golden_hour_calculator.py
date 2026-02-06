"""
Calculateur de Golden Hour - Temps trajets caserne→microzone→hôpital avec congestion et stress.
Story 2.2.3 - Golden Hour
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

from ..data.constants import INCIDENT_TYPE_ACCIDENT, INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE
from ..utils.path_resolver import PathResolver
from ..utils.pickle_utils import load_pickle
from .caserne_manager import CaserneManager, POMPIERS_PAR_INTERVENTION

# Constantes
GOLDEN_HOUR_MINUTES = 60  # Golden Hour = 60 minutes
TEMPS_TRAITEMENT_BASE = 15  # Temps de traitement sur place (minutes)
AJOUT_ALCOOL_MINUTES = 5  # Ajout de 5 minutes si alcool
# Vitesse moyenne Paris (circonvolutions, trafic) — Story 2.4.5.2 / pré-calculs
VITESSE_MOYENNE_KMH = 20.0

# Probabilités mort / blessé grave selon respect Golden Hour (incident > bénin)
PROB_MORT_GH_NON_RESPECTE = 0.01  # 1 % si Golden Hour non respectée
PROB_BLESSE_GRAVE_GH_NON_RESPECTE = 0.15  # 15 % si Golden Hour non respectée
PROB_MORT_GH_RESPECTE = 0.0  # 0 % si Golden Hour respectée
PROB_BLESSE_GRAVE_GH_RESPECTE = 0.03  # 3 % si Golden Hour respectée


class GoldenHourCalculator:
    """
    Calculateur de Golden Hour pour incidents graves.
    
    Calcule le temps total : caserne → microzone → hôpital
    avec congestion, stress, et différenciation nuit/alcool.
    """
    
    def __init__(
        self,
        caserne_manager: CaserneManager,
        distances_caserne_microzone: Dict[str, Dict[str, float]],
        distances_microzone_hopital: Dict[str, Dict[str, float]],
        temps_base_caserne_microzone: Optional[Dict[str, Dict[str, float]]] = None,
        temps_base_microzone_hopital: Optional[Dict[str, Dict[str, float]]] = None,
        seed: Optional[int] = None
    ):
        """
        Initialise le calculateur de Golden Hour.
        
        Args:
            caserne_manager: Gestionnaire de casernes
            distances_caserne_microzone: Distances caserne→microzone (km)
            distances_microzone_hopital: Distances microzone→hôpital (km)
            temps_base_caserne_microzone: Temps de base caserne→microzone (minutes, optionnel)
            temps_base_microzone_hopital: Temps de base microzone→hôpital (minutes, optionnel)
            seed: Seed pour reproductibilité
        """
        self.caserne_manager = caserne_manager
        self.distances_caserne_microzone = distances_caserne_microzone
        self.distances_microzone_hopital = distances_microzone_hopital
        self.temps_base_caserne_microzone = temps_base_caserne_microzone or {}
        self.temps_base_microzone_hopital = temps_base_microzone_hopital or {}
        
        # Générateur aléatoire
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Table de congestion (chargée dynamiquement)
        self.congestion_table: Optional[Dict[str, Dict[int, float]]] = None
    
    @classmethod
    def load_trajets(cls) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
        """
        Charge les trajets pré-calculés depuis data/source_data/.
        
        Returns:
            Tuple (distances_caserne_microzone, distances_microzone_hopital,
                   temps_base_caserne_microzone, temps_base_microzone_hopital)
        
        Raises:
            FileNotFoundError: Si les fichiers n'existent pas
        """
        from ..utils.path_resolver import PathResolver
        from ..utils.pickle_utils import load_pickle
        
        # Charger distances caserne→microzone
        path_distances_cm = PathResolver.data_source("distances_caserne_microzone.pkl")
        if not path_distances_cm.exists():
            raise FileNotFoundError(
                f"Fichier distances_caserne_microzone.pkl introuvable: {path_distances_cm}. "
                f"Assurez-vous que les pré-calculs (Epic 1, Story 1.2) ont été exécutés."
            )
        distances_cm_data = load_pickle(path_distances_cm)
        
        # Charger distances microzone→hôpital
        path_distances_mh = PathResolver.data_source("distances_microzone_hopital.pkl")
        if not path_distances_mh.exists():
            raise FileNotFoundError(
                f"Fichier distances_microzone_hopital.pkl introuvable: {path_distances_mh}. "
                f"Assurez-vous que les pré-calculs (Epic 1, Story 1.2) ont été exécutés."
            )
        distances_mh_data = load_pickle(path_distances_mh)
        
        # Accepter format legacy DataFrame (pré-calculs Story 1.2 : colonnes microzone, caserne/hopital, distance_km)
        try:
            import pandas as pd
        except ImportError:
            pd = None
        if pd is not None and isinstance(distances_cm_data, pd.DataFrame):
            distances_cm = {}
            temps_base_cm = {}
            for _, row in distances_cm_data.iterrows():
                caserne_id = str(row.get('caserne', row.get('caserne_id', '')))
                microzone_id = str(row.get('microzone', row.get('microzone_id', '')))
                dist_km = float(row.get('distance_km', row.get('distance', 0.0)))
                if caserne_id not in distances_cm:
                    distances_cm[caserne_id] = {}
                    temps_base_cm[caserne_id] = {}
                distances_cm[caserne_id][microzone_id] = dist_km
                temps_base_cm[caserne_id][microzone_id] = dist_km / VITESSE_MOYENNE_KMH * 60.0 if dist_km else 0.0
        elif isinstance(distances_cm_data, dict):
            if 'data' in distances_cm_data:
                distances_cm_data = distances_cm_data['data']
            distances_cm = {}
            temps_base_cm = {}
            for caserne_id, microzones in distances_cm_data.items():
                distances_cm[caserne_id] = {}
                temps_base_cm[caserne_id] = {}
                for microzone_id, value in microzones.items():
                    if isinstance(value, dict):
                        d = value.get('distance', value.get('distance_km', 0.0))
                        t = value.get('temps_base', value.get('temps_base_min', 0.0))
                        distances_cm[caserne_id][microzone_id] = float(d)
                        temps_base_cm[caserne_id][microzone_id] = float(t) if t else float(d) / VITESSE_MOYENNE_KMH * 60.0
                    else:
                        d = float(value)
                        distances_cm[caserne_id][microzone_id] = d
                        temps_base_cm[caserne_id][microzone_id] = d / VITESSE_MOYENNE_KMH * 60.0
        else:
            distances_cm = {}
            temps_base_cm = {}

        if pd is not None and isinstance(distances_mh_data, pd.DataFrame):
            distances_mh = {}
            temps_base_mh = {}
            for _, row in distances_mh_data.iterrows():
                microzone_id = str(row.get('microzone', row.get('microzone_id', '')))
                hopital_id = str(row.get('hopital', row.get('hopital_id', '')))
                dist_km = float(row.get('distance_km', row.get('distance', 0.0)))
                if microzone_id not in distances_mh:
                    distances_mh[microzone_id] = {}
                    temps_base_mh[microzone_id] = {}
                distances_mh[microzone_id][hopital_id] = dist_km
                temps_base_mh[microzone_id][hopital_id] = dist_km / VITESSE_MOYENNE_KMH * 60.0 if dist_km else 0.0
        elif isinstance(distances_mh_data, dict):
            if 'data' in distances_mh_data:
                distances_mh_data = distances_mh_data['data']
            distances_mh = {}
            temps_base_mh = {}
            for microzone_id, hopitaux in distances_mh_data.items():
                distances_mh[microzone_id] = {}
                temps_base_mh[microzone_id] = {}
                for hopital_id, value in hopitaux.items():
                    if isinstance(value, dict):
                        d = value.get('distance', value.get('distance_km', 0.0))
                        t = value.get('temps_base', value.get('temps_base_min', 0.0))
                        distances_mh[microzone_id][hopital_id] = float(d)
                        temps_base_mh[microzone_id][hopital_id] = float(t) if t else float(d) / VITESSE_MOYENNE_KMH * 60.0
                    else:
                        d = float(value)
                        distances_mh[microzone_id][hopital_id] = d
                        temps_base_mh[microzone_id][hopital_id] = d / VITESSE_MOYENNE_KMH * 60.0
        else:
            distances_mh = {}
            temps_base_mh = {}

        return distances_cm, distances_mh, temps_base_cm, temps_base_mh
    
    def load_congestion_table(self, run_id: str) -> None:
        """
        Charge la table de congestion depuis data/intermediate/run_XXX/generation/congestion.pkl.
        
        Args:
            run_id: Identifiant du run
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        path = PathResolver.data_intermediate(f"run_{run_id}", "generation", "congestion.pkl")
        
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier congestion.pkl introuvable: {path}. "
                f"Assurez-vous que Story 2.2.2.5 a été exécutée."
            )
        
        data = load_pickle(path, expected_type="congestion")
        
        # Extraire la table de congestion
        if isinstance(data, dict):
            if 'data' in data:
                self.congestion_table = data['data']
            else:
                self.congestion_table = data
        else:
            raise ValueError(f"Format de congestion_table inattendu: {type(data)}")
    
    def trouver_hopital_plus_proche(
        self,
        microzone_id: str
    ) -> Optional[Tuple[str, float, float]]:
        """
        Trouve l'hôpital le plus proche pour une microzone.
        
        Args:
            microzone_id: Identifiant de la microzone
        
        Returns:
            Tuple (hopital_id, distance, temps_base) ou None
        """
        if microzone_id not in self.distances_microzone_hopital:
            return None
        
        hopitaux = self.distances_microzone_hopital[microzone_id]
        
        if not hopitaux:
            return None
        
        # Trouver l'hôpital le plus proche
        hopital_plus_proche = None
        distance_min = float('inf')
        
        for hopital_id, distance in hopitaux.items():
            if distance < distance_min:
                distance_min = distance
                hopital_plus_proche = hopital_id
        
        if hopital_plus_proche is None:
            return None
        
        # Récupérer temps de base
        temps_base = self.temps_base_microzone_hopital.get(microzone_id, {}).get(hopital_plus_proche, 0.0)
        if temps_base == 0.0:
            # Estimer depuis distance (vitesse Paris)
            temps_base = distance_min / VITESSE_MOYENNE_KMH * 60.0
        
        return (hopital_plus_proche, distance_min, temps_base)
    
    def calculer_temps_trajet_reel(
        self,
        caserne_id: str,
        microzone_id: str,
        jour: int,
        is_nuit: bool = False,
        is_alcool: bool = False,
        microzones_traversees: Optional[List[str]] = None
    ) -> float:
        """
        Calcule le temps de trajet réel avec congestion.
        
        Formule : temps_trajet_reel = temps_base × ∏(congestion_microzone_traversee)
        
        Différenciation nuit/alcool :
        - Si nuit : × congestion_nuit
        - Si alcool : + 5 min
        - Si nuit + alcool : × congestion_nuit + 5 min
        
        Args:
            caserne_id: Identifiant de la caserne
            microzone_id: Identifiant de la microzone
            jour: Numéro du jour (0-indexé)
            is_nuit: Si l'incident s'est produit la nuit
            is_alcool: Si l'incident implique de l'alcool
            microzones_traversees: Liste des microzones traversées (optionnel)
        
        Returns:
            Temps de trajet réel (minutes)
        """
        # Récupérer temps de base
        temps_base = self.temps_base_caserne_microzone.get(caserne_id, {}).get(microzone_id, 0.0)
        if temps_base == 0.0:
            # Estimer depuis distance
            distance = self.distances_caserne_microzone.get(caserne_id, {}).get(microzone_id, 0.0)
            if distance == 0.0:
                return 0.0
            temps_base = distance / VITESSE_MOYENNE_KMH * 60.0
        
        # Appliquer congestion si table disponible
        facteur_congestion = 1.0
        
        if self.congestion_table is not None:
            # Si microzones traversées spécifiées, utiliser celles-ci
            if microzones_traversees:
                for mz in microzones_traversees:
                    congestion = self.congestion_table.get(mz, {}).get(jour, 1.0)
                    facteur_congestion *= congestion
            else:
                # Sinon, utiliser uniquement la microzone de destination
                congestion = self.congestion_table.get(microzone_id, {}).get(jour, 1.0)
                facteur_congestion *= congestion
        
        # Calculer temps avec congestion
        temps_trajet = temps_base * facteur_congestion
        
        # Différenciation nuit/alcool
        if is_nuit:
            # Congestion nuit (divisée par 3 en moyenne, déjà appliquée dans congestion_table)
            # Mais on peut appliquer un facteur supplémentaire si nécessaire
            # Pour l'instant, on suppose que la congestion nuit est déjà dans la table
            pass
        
        if is_alcool:
            # Ajouter 5 minutes
            temps_trajet += AJOUT_ALCOOL_MINUTES
        
        return max(0.0, temps_trajet)
    
    def calculer_temps_total(
        self,
        caserne_id: str,
        microzone_id: str,
        jour: int,
        is_nuit: bool = False,
        is_alcool: bool = False,
        microzones_traversees: Optional[List[str]] = None
    ) -> Tuple[float, float, float, float]:
        """
        Calcule le temps total : trajet + traitement + hôpital retour.
        
        Args:
            caserne_id: Identifiant de la caserne
            microzone_id: Identifiant de la microzone
            jour: Numéro du jour (0-indexé)
            is_nuit: Si l'incident s'est produit la nuit
            is_alcool: Si l'incident implique de l'alcool
            microzones_traversees: Liste des microzones traversées (optionnel)
        
        Returns:
            Tuple (temps_trajet, temps_traitement, temps_hopital_retour, temps_total)
        """
        # Temps trajet caserne → microzone
        temps_trajet = self.calculer_temps_trajet_reel(
            caserne_id, microzone_id, jour, is_nuit, is_alcool, microzones_traversees
        )
        
        # Temps traitement sur place
        temps_traitement = TEMPS_TRAITEMENT_BASE
        
        # Temps hôpital retour (microzone → hôpital)
        hopital_info = self.trouver_hopital_plus_proche(microzone_id)
        if hopital_info:
            hopital_id, distance_hopital, temps_base_hopital = hopital_info
            
            # Appliquer congestion pour le retour
            facteur_congestion_retour = 1.0
            if self.congestion_table is not None:
                congestion = self.congestion_table.get(microzone_id, {}).get(jour, 1.0)
                facteur_congestion_retour *= congestion
            
            temps_hopital_retour = temps_base_hopital * facteur_congestion_retour
            
            if is_alcool:
                temps_hopital_retour += AJOUT_ALCOOL_MINUTES
        else:
            temps_hopital_retour = 0.0
        
        # Temps total
        temps_total = temps_trajet + temps_traitement + temps_hopital_retour
        
        return (temps_trajet, temps_traitement, temps_hopital_retour, temps_total)
    
    def calculer_golden_hour(
        self,
        microzone_id: str,
        jour: int,
        type_incident: str,
        is_nuit: bool = False,
        is_alcool: bool = False,
        microzones_traversees: Optional[List[str]] = None
    ) -> Tuple[bool, bool, float, Dict]:
        """
        Calcule la Golden Hour et détermine mort/blessé grave par tirage au sort.
        
        Args:
            microzone_id: Identifiant de la microzone
            jour: Numéro du jour (0-indexé)
            type_incident: Type d'incident (INCIDENT_TYPE_*)
            is_nuit: Si l'incident s'est produit la nuit
            is_alcool: Si l'incident implique de l'alcool
            microzones_traversees: Liste des microzones traversées (optionnel)
        
        Returns:
            Tuple (is_mort, is_blesse_grave, temps_total, details)
            details contient : caserne_id, hopital_id, temps_trajet, temps_traitement, temps_hopital_retour, stress
        """
        # Trouver caserne disponible la plus proche
        caserne_info = self.caserne_manager.trouver_caserne_disponible(
            microzone_id,
            self.distances_caserne_microzone
        )
        
        if caserne_info is None:
            # Pas de caserne disponible, considérer comme mort
            return (True, False, float('inf'), {
                'caserne_id': None,
                'hopital_id': None,
                'temps_trajet': float('inf'),
                'temps_traitement': 0.0,
                'temps_hopital_retour': 0.0,
                'stress': 0.0
            })
        
        caserne_id, _ = caserne_info
        
        # Calculer temps total
        temps_trajet, temps_traitement, temps_hopital_retour, temps_total = self.calculer_temps_total(
            caserne_id, microzone_id, jour, is_nuit, is_alcool, microzones_traversees
        )
        
        # Calculer stress caserne
        stress = self.caserne_manager.get_stress_caserne(caserne_id)
        
        # Appliquer stress au temps de trajet
        temps_trajet_avec_stress = temps_trajet * (1.0 + stress * 0.1)
        temps_total_avec_stress = temps_trajet_avec_stress + temps_traitement + temps_hopital_retour
        
        # Trouver hôpital
        hopital_info = self.trouver_hopital_plus_proche(microzone_id)
        hopital_id = hopital_info[0] if hopital_info else None
        
        # Probabilités mort / blessé grave : 1 % mort si GH non respectée, 15 % / 3 % blessé grave
        if temps_total_avec_stress > GOLDEN_HOUR_MINUTES:
            prob_mort = PROB_MORT_GH_NON_RESPECTE
            prob_blesse_grave = PROB_BLESSE_GRAVE_GH_NON_RESPECTE
        else:
            prob_mort = PROB_MORT_GH_RESPECTE
            prob_blesse_grave = PROB_BLESSE_GRAVE_GH_RESPECTE
        
        # Tirage au sort
        rand = self.rng.uniform(0.0, 1.0)
        
        is_mort = False
        is_blesse_grave = False
        
        if rand < prob_mort:
            is_mort = True
        elif rand < prob_mort + prob_blesse_grave:
            is_blesse_grave = True
        
        details = {
            'caserne_id': caserne_id,
            'hopital_id': hopital_id,
            'temps_trajet': temps_trajet_avec_stress,
            'temps_traitement': temps_traitement,
            'temps_hopital_retour': temps_hopital_retour,
            'temps_total': temps_total_avec_stress,
            'stress': stress,
            'prob_mort': prob_mort,
            'prob_blesse_grave': prob_blesse_grave,
            'tirage': rand,
            'seuil_golden_hour_minutes': GOLDEN_HOUR_MINUTES,
        }
        
        return (is_mort, is_blesse_grave, temps_total_avec_stress, details)
