"""
Calculateur de morts et blessés graves hebdomadaires.
Story 2.2.4 - Morts et blessés graves hebdomadaires
"""

import pickle
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from ..core.data.vector import Vector
from ..core.golden_hour.golden_hour_calculator import GoldenHourCalculator
from ..core.state.casualties_state import CasualtiesState
from ..core.state.events_state import EventsState
from ..core.state.vectors_state import VectorsState
from ..core.utils.path_resolver import PathResolver
from ..core.utils.pickle_utils import load_pickle

# Probabilités mort/blessé grave : désormais dans GoldenHourCalculator (1 % mort si GH non respectée, 15 %/3 % blessé grave)
# Constantes conservées pour compatibilité éventuelle
PONDERATION_MORTS_ALEATOIRE = 0.3
PONDERATION_MORTS_GOLDEN_HOUR = 0.7
PONDERATION_BLESSES_ALEATOIRE = 0.6
PONDERATION_BLESSES_GOLDEN_HOUR = 0.4

# Seuils alertes
ALERTE_MORTS_MIN = 1
ALERTE_MORTS_MAX = 500
ALERTE_JOURS_AGREGES = 800


class CasualtyCalculator:
    """
    Calculateur de morts et blessés graves hebdomadaires par arrondissement.
    
    Calcule à partir de :
    - Vecteurs normaux (Story 2.2.1)
    - Événements (Story 2.2.7)
    - Golden Hour (Story 2.2.3)
    
    Avec agrégation microzones → arrondissements et totaux hebdomadaires.
    """
    
    def __init__(
        self,
        golden_hour_calculator: GoldenHourCalculator,
        limites_microzone_arrondissement: Dict[str, int],
        seed: Optional[int] = None
    ):
        """
        Initialise le calculateur de casualties.
        
        Args:
            golden_hour_calculator: Calculateur de Golden Hour (Story 2.2.3)
            limites_microzone_arrondissement: Mapping microzone_id → arrondissement
            seed: Seed pour reproductibilité
        """
        self.golden_hour_calculator = golden_hour_calculator
        self.limites_microzone_arrondissement = limites_microzone_arrondissement
        
        # Générateur aléatoire
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Historique pour alertes (800 jours agrégés)
        self.historique_morts: Dict[int, List[int]] = {}  # Dict[arrondissement, List[morts_par_jour]]
    
    @classmethod
    def load_limites_microzone_arrondissement(cls) -> Dict[str, int]:
        """
        Charge les limites microzone → arrondissement depuis data/source_data/.
        
        Accepte format standardisé (load_pickle) ou legacy (dict brut pré-calcul).
        
        Returns:
            Dictionnaire {microzone_id: arrondissement}
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        path = PathResolver.data_source("limites_microzone_arrondissement.pkl")
        
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier limites_microzone_arrondissement.pkl introuvable: {path}. "
                f"Assurez-vous que les pré-calculs (Epic 1, Story 1.2) ont été exécutés."
            )
        
        try:
            data = load_pickle(path, expected_type="limites")
        except ValueError:
            with open(path, "rb") as f:
                data = pickle.load(f)
        
        if isinstance(data, dict):
            if "data" in data and "metadata" in data:
                data = data["data"]
            if isinstance(data, dict):
                return {str(k): int(v) for k, v in data.items()}
            return data
        raise ValueError(f"Format de limites_microzone_arrondissement inattendu: {type(data)}")
    
    def _calculer_morts_et_blesses_vecteurs(
        self,
        vectors: Dict[str, Dict[str, Vector]],
        jour: int,
        is_nuit: Optional[Dict[str, bool]] = None,
        is_alcool: Optional[Dict[str, Dict[str, bool]]] = None,
    ) -> Tuple[Dict[str, Dict[str, int]], Dict[str, Dict[str, int]]]:
        """
        Un seul passage par incident > bénin (moyen+grave) : un tirage Golden Hour par incident,
        remplit morts (1 % si GH non respectée) et blessés graves (15 % / 3 %).
        Returns:
            (morts, blesses_graves) par microzone et type.
        """
        morts: Dict[str, Dict[str, int]] = {}
        blesses_graves: Dict[str, Dict[str, int]] = {}
        for microzone_id, vectors_mz in vectors.items():
            morts[microzone_id] = {}
            blesses_graves[microzone_id] = {}
            is_nuit_mz = is_nuit.get(microzone_id, False) if is_nuit else False
            is_alcool_mz = is_alcool.get(microzone_id, {}) if is_alcool else {}
            for type_incident, vector in vectors_mz.items():
                nb = getattr(vector, "grave", 0) + getattr(vector, "moyen", 0)
                morts[microzone_id][type_incident] = 0
                blesses_graves[microzone_id][type_incident] = 0
                if nb == 0:
                    continue
                for _ in range(nb):
                    is_mort, is_blesse_grave, _, _ = self.golden_hour_calculator.calculer_golden_hour(
                        microzone_id=microzone_id,
                        jour=jour,
                        type_incident=type_incident,
                        is_nuit=is_nuit_mz,
                        is_alcool=is_alcool_mz.get(type_incident, False),
                    )
                    if is_mort:
                        morts[microzone_id][type_incident] += 1
                    if is_blesse_grave:
                        blesses_graves[microzone_id][type_incident] += 1
        return (morts, blesses_graves)

    def _calculer_morts_vecteurs(
        self,
        vectors: Dict[str, Dict[str, Vector]],
        jour: int,
        is_nuit: Optional[Dict[str, bool]] = None,
        is_alcool: Optional[Dict[str, Dict[str, bool]]] = None
    ) -> Dict[str, Dict[str, int]]:
        """Morts à partir des vecteurs (délègue à _calculer_morts_et_blesses_vecteurs)."""
        morts, _ = self._calculer_morts_et_blesses_vecteurs(vectors, jour, is_nuit, is_alcool)
        return morts

    def _calculer_blesses_graves_vecteurs(
        self,
        vectors: Dict[str, Dict[str, Vector]],
        jour: int,
        is_nuit: Optional[Dict[str, bool]] = None,
        is_alcool: Optional[Dict[str, Dict[str, bool]]] = None
    ) -> Dict[str, Dict[str, int]]:
        """Blessés graves à partir des vecteurs (délègue à _calculer_morts_et_blesses_vecteurs)."""
        _, blesses_graves = self._calculer_morts_et_blesses_vecteurs(vectors, jour, is_nuit, is_alcool)
        return blesses_graves
    
    def _calculer_morts_evenements(
        self,
        events: List,
        jour: int
    ) -> Dict[str, Dict[str, int]]:
        """
        Calcule les morts à partir des événements.
        
        Args:
            events: Liste des événements graves du jour
            jour: Numéro du jour (0-indexé)
        
        Returns:
            Dictionnaire {microzone_id: {type_incident: nb_morts}}
        """
        morts = {}
        
        for event in events:
            # Récupérer microzone depuis arrondissement (simplification)
            # En réalité, il faudrait un mapping arrondissement → microzones
            arrondissement = getattr(event, 'arrondissement', None)
            if arrondissement is None:
                continue
            
            # Trouver microzones de cet arrondissement
            microzones = [
                mz_id for mz_id, arr in self.limites_microzone_arrondissement.items()
                if arr == arrondissement
            ]
            
            if not microzones:
                continue
            
            # Utiliser la première microzone (simplification)
            microzone_id = microzones[0]
            
            # Récupérer casualties_base de l'événement
            casualties_base = getattr(event, 'casualties_base', 0)
            
            if microzone_id not in morts:
                morts[microzone_id] = {}
            
            type_incident = getattr(event, 'type', 'accident')
            if type_incident not in morts[microzone_id]:
                morts[microzone_id][type_incident] = 0
            
            # Morts événements : utiliser casualties_base directement
            morts[microzone_id][type_incident] += casualties_base
        
        return morts
    
    def _agreger_microzones_arrondissements(
        self,
        casualties_microzones: Dict[str, Dict[str, int]]
    ) -> Dict[int, Dict[str, int]]:
        """
        Agrège les casualties de microzones vers arrondissements.
        
        Args:
            casualties_microzones: Casualties par microzone et type
        
        Returns:
            Dictionnaire {arrondissement: {type_incident: total}}
        """
        casualties_arrondissements = {}
        
        for microzone_id, casualties_mz in casualties_microzones.items():
            arrondissement = self.limites_microzone_arrondissement.get(microzone_id)
            
            if arrondissement is None:
                continue
            
            if arrondissement not in casualties_arrondissements:
                casualties_arrondissements[arrondissement] = {}
            
            for type_incident, count in casualties_mz.items():
                if type_incident not in casualties_arrondissements[arrondissement]:
                    casualties_arrondissements[arrondissement][type_incident] = 0
                
                casualties_arrondissements[arrondissement][type_incident] += count
        
        return casualties_arrondissements
    
    def calculer_casualties_jour(
        self,
        jour: int,
        vectors_state: VectorsState,
        events_state: EventsState,
        is_nuit: Optional[Dict[str, bool]] = None,
        is_alcool: Optional[Dict[str, Dict[str, bool]]] = None
    ) -> Tuple[Dict[int, Dict[str, int]], Dict[int, Dict[str, int]]]:
        """
        Calcule les morts et blessés graves pour un jour donné.
        
        Args:
            jour: Numéro du jour (0-indexé)
            vectors_state: État des vecteurs (Story 2.2.1)
            events_state: État des événements (Story 2.2.7)
            is_nuit: Indicateurs nuit par microzone (optionnel)
            is_alcool: Indicateurs alcool par microzone et type (optionnel)
        
        Returns:
            Tuple (morts_arrondissements, blesses_graves_arrondissements)
        """
        # Récupérer vecteurs du jour
        vectors = {}
        for microzone_id in self.limites_microzone_arrondissement.keys():
            vectors[microzone_id] = {}
            for type_incident in [INCIDENT_TYPE_ACCIDENT, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_AGRESSION]:
                vector = vectors_state.get_vector(microzone_id, jour, type_incident)
                if vector:
                    vectors[microzone_id][type_incident] = vector
        
        # Un seul passage vecteurs : morts + blessés graves (1 tirage GH par incident > bénin)
        morts_vecteurs, blesses_graves_vecteurs = self._calculer_morts_et_blesses_vecteurs(
            vectors, jour, is_nuit, is_alcool
        )
        
        # Calculer morts depuis événements (casualties_base)
        events_grave = events_state.get_grave_events_for_day(jour)
        morts_evenements = self._calculer_morts_evenements(events_grave, jour)
        
        # Combiner morts vecteurs + événements
        morts_totales = morts_vecteurs.copy()
        for microzone_id, morts_evt in morts_evenements.items():
            if microzone_id not in morts_totales:
                morts_totales[microzone_id] = {}
            for type_incident, count in morts_evt.items():
                if type_incident not in morts_totales[microzone_id]:
                    morts_totales[microzone_id][type_incident] = 0
                morts_totales[microzone_id][type_incident] += count
        
        # Agrégation microzones → arrondissements
        morts_arrondissements = self._agreger_microzones_arrondissements(morts_totales)
        blesses_graves_arrondissements = self._agreger_microzones_arrondissements(blesses_graves_vecteurs)
        
        return (morts_arrondissements, blesses_graves_arrondissements)

    def calculer_casualties_jour_avec_details(
        self,
        jour: int,
        vectors_state: VectorsState,
        events_state: EventsState,
        is_nuit: Optional[Dict[str, bool]] = None,
        is_alcool: Optional[Dict[str, Dict[str, bool]]] = None,
    ) -> Tuple[
        Dict[int, Dict[str, int]],
        Dict[int, Dict[str, int]],
        List[Dict],
        List[Dict],
    ]:
        """
        Calcule les morts et blessés graves pour un jour et retourne les agrégats
        plus les listes détaillées (tous arrondissements, dont le 1) pour affichage Golden Hour.
        Un seul passage par incident pour cohérence RNG et agrégats.
        Story 2.4.5.2 — Liste morts / blessés graves sous la carte + détail Golden Hour.
        """
        vectors = {}
        for microzone_id in self.limites_microzone_arrondissement.keys():
            vectors[microzone_id] = {}
            for type_incident in [INCIDENT_TYPE_ACCIDENT, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_AGRESSION]:
                vector = vectors_state.get_vector(microzone_id, jour, type_incident)
                if vector:
                    vectors[microzone_id][type_incident] = vector

        list_morts: List[Dict] = []
        list_blesses_graves: List[Dict] = []
        morts_totales: Dict[str, Dict[str, int]] = {}
        blesses_totales: Dict[str, Dict[str, int]] = {}

        # Vecteurs : un seul appel Golden Hour par incident > bénin (moyen+grave), tirage direct (1 % mort, 15 %/3 % blessé grave)
        for microzone_id, vectors_mz in vectors.items():
            arrondissement = self.limites_microzone_arrondissement.get(microzone_id)
            if arrondissement is None:
                continue
            is_nuit_mz = is_nuit.get(microzone_id, False) if is_nuit else False
            is_alcool_mz = is_alcool.get(microzone_id, {}) if is_alcool else {}

            for type_incident, vector in vectors_mz.items():
                nb_incidents_moyen_grave = getattr(vector, "grave", 0) + getattr(vector, "moyen", 0)
                if nb_incidents_moyen_grave == 0:
                    continue
                if microzone_id not in morts_totales:
                    morts_totales[microzone_id] = {}
                if type_incident not in morts_totales[microzone_id]:
                    morts_totales[microzone_id][type_incident] = 0
                if microzone_id not in blesses_totales:
                    blesses_totales[microzone_id] = {}
                if type_incident not in blesses_totales[microzone_id]:
                    blesses_totales[microzone_id][type_incident] = 0

                for _ in range(nb_incidents_moyen_grave):
                    is_mort, is_blesse_grave, _, details = self.golden_hour_calculator.calculer_golden_hour(
                        microzone_id=microzone_id,
                        jour=jour,
                        type_incident=type_incident,
                        is_nuit=is_nuit_mz,
                        is_alcool=is_alcool_mz.get(type_incident, False),
                    )
                    if is_mort:
                        morts_totales[microzone_id][type_incident] += 1
                        list_morts.append({
                            "jour": jour,
                            "microzone_id": microzone_id,
                            "arrondissement": arrondissement,
                            "type_incident": type_incident,
                            "statut": "mort",
                            "detail_golden_hour": details,
                        })
                    if is_blesse_grave:
                        blesses_totales[microzone_id][type_incident] += 1
                        list_blesses_graves.append({
                            "jour": jour,
                            "microzone_id": microzone_id,
                            "arrondissement": arrondissement,
                            "type_incident": type_incident,
                            "statut": "blessé grave",
                            "detail_golden_hour": details,
                            })

        # Événements : morts sans détail Golden Hour (N/A)
        events_grave = events_state.get_grave_events_for_day(jour)
        morts_evenements = self._calculer_morts_evenements(events_grave, jour)
        for microzone_id, morts_evt in morts_evenements.items():
            if microzone_id not in morts_totales:
                morts_totales[microzone_id] = {}
            arrondissement = self.limites_microzone_arrondissement.get(microzone_id)
            for type_incident, count in morts_evt.items():
                if type_incident not in morts_totales[microzone_id]:
                    morts_totales[microzone_id][type_incident] = 0
                morts_totales[microzone_id][type_incident] += count
                if arrondissement is not None:
                    for _ in range(count):
                        list_morts.append({
                            "jour": jour,
                            "microzone_id": microzone_id,
                            "arrondissement": arrondissement,
                            "type_incident": type_incident,
                            "statut": "mort",
                            "detail_golden_hour": None,
                        })

        morts_arrondissements = self._agreger_microzones_arrondissements(morts_totales)
        blesses_graves_arrondissements = self._agreger_microzones_arrondissements(blesses_totales)
        return (morts_arrondissements, blesses_graves_arrondissements, list_morts, list_blesses_graves)

    def calculer_casualties_semaine(
        self,
        semaine: int,
        vectors_state: VectorsState,
        events_state: EventsState,
        is_nuit: Optional[Dict[int, Dict[str, bool]]] = None,
        is_alcool: Optional[Dict[int, Dict[str, Dict[str, bool]]]] = None
    ) -> Tuple[Dict[int, Dict[str, int]], Dict[int, Dict[str, int]]]:
        """
        Calcule les morts et blessés graves pour une semaine (agrégation de 7 jours).
        
        Args:
            semaine: Numéro de la semaine (1-indexé)
            vectors_state: État des vecteurs
            events_state: État des événements
            is_nuit: Indicateurs nuit par jour et microzone (optionnel)
            is_alcool: Indicateurs alcool par jour, microzone et type (optionnel)
        
        Returns:
            Tuple (morts_arrondissements, blesses_graves_arrondissements)
        """
        # Calculer jours de la semaine (0-indexé)
        jour_debut = (semaine - 1) * 7
        jours_semaine = list(range(jour_debut, jour_debut + 7))
        
        # Agrégation par arrondissement
        morts_semaine = {}
        blesses_graves_semaine = {}
        
        for jour in jours_semaine:
            is_nuit_jour = is_nuit.get(jour, {}) if is_nuit else None
            is_alcool_jour = is_alcool.get(jour, {}) if is_alcool else None
            
            morts_jour, blesses_jour = self.calculer_casualties_jour(
                jour, vectors_state, events_state, is_nuit_jour, is_alcool_jour
            )
            
            # Agréger par arrondissement
            for arrondissement, morts_arr in morts_jour.items():
                if arrondissement not in morts_semaine:
                    morts_semaine[arrondissement] = {}
                
                for type_incident, count in morts_arr.items():
                    if type_incident not in morts_semaine[arrondissement]:
                        morts_semaine[arrondissement][type_incident] = 0
                    morts_semaine[arrondissement][type_incident] += count
            
            for arrondissement, blesses_arr in blesses_jour.items():
                if arrondissement not in blesses_graves_semaine:
                    blesses_graves_semaine[arrondissement] = {}
                
                for type_incident, count in blesses_arr.items():
                    if type_incident not in blesses_graves_semaine[arrondissement]:
                        blesses_graves_semaine[arrondissement][type_incident] = 0
                    blesses_graves_semaine[arrondissement][type_incident] += count
        
        return (morts_semaine, blesses_graves_semaine)
    
    def verifier_alertes(
        self,
        arrondissement: int,
        morts_semaine: int
    ) -> Optional[str]:
        """
        Vérifie les alertes pour un arrondissement (800 jours agrégés, 1-500 morts).
        
        Args:
            arrondissement: Numéro de l'arrondissement
            morts_semaine: Nombre de morts de la semaine
        
        Returns:
            Message d'alerte si seuil dépassé, None sinon
        """
        # Ajouter à l'historique
        if arrondissement not in self.historique_morts:
            self.historique_morts[arrondissement] = []
        
        self.historique_morts[arrondissement].append(morts_semaine)
        
        # Garder seulement les 800 derniers jours
        if len(self.historique_morts[arrondissement]) > ALERTE_JOURS_AGREGES:
            self.historique_morts[arrondissement] = self.historique_morts[arrondissement][-ALERTE_JOURS_AGREGES:]
        
        # Calculer total sur 800 jours
        total_morts = sum(self.historique_morts[arrondissement])
        
        # Vérifier seuils
        if total_morts == 0:
            return f"ALERTE: Arrondissement {arrondissement} - 0 mort sur {len(self.historique_morts[arrondissement])} jours agrégés"
        elif total_morts >= ALERTE_MORTS_MAX:
            return f"ALERTE: Arrondissement {arrondissement} - {total_morts} morts sur {len(self.historique_morts[arrondissement])} jours agrégés (≥ {ALERTE_MORTS_MAX})"
        
        return None
