"""
Calculateur de taux de ralentissement de trafic (congestion dynamique).
Story 2.2.2.5 - Calcul taux de ralentissement de trafic
"""

import pickle
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from ..data.vector import Vector
from ..utils.path_resolver import PathResolver
from ..utils.pickle_utils import load_pickle

# Pondération randomité
PONDERATION_RANDOMITE_NORMALE = 0.2  # 20% du score total
PONDERATION_RANDOMITE_EVENEMENT = 0.7  # 70% du score total (événement important)

# Facteurs de congestion nuit
FACTEUR_CONGESTION_NUIT_MOYEN = 3.0  # Divisé par 3 en moyenne
FACTEUR_CONGESTION_NUIT_ETE = 2.2  # Divisé par 2.2 l'été


def _looks_like_metadata(d: dict) -> bool:
    """Indique si le dict est une enveloppe standardisée {data, metadata}."""
    return "data" in d and "metadata" in d


def _is_congestion_dataframe(obj: object) -> bool:
    """Indique si l'objet est un DataFrame pré-calcul congestion (microzone_id + congestion_base_*)."""
    if not isinstance(obj, pd.DataFrame):
        return False
    cols = set(obj.columns)
    return "microzone_id" in cols and "congestion_base_intersaison" in cols


def _congestion_dataframe_to_dict(df: pd.DataFrame) -> Dict[str, float]:
    """Convertit le DataFrame pré-calcul en Dict[microzone_id, float] (moyenne des 3 saisons)."""
    out: Dict[str, float] = {}
    for _, row in df.iterrows():
        mz = str(row["microzone_id"])
        h = float(row.get("congestion_base_hiver", 0.5))
        e = float(row.get("congestion_base_ete", 0.5))
        i = float(row.get("congestion_base_intersaison", 0.5))
        out[mz] = (h + e + i) / 3.0
    return out


class CongestionCalculator:
    """
    Calculateur de taux de ralentissement de trafic (congestion dynamique).
    
    Combine congestion statique (pré-calculée) avec effets dynamiques :
    - Accidents, incendies, agressions
    - Effets temporels (incendies J+1/J+2, agressions graves J+1/J+2/J+3)
    - Saisonnalité, voisins, récurrence
    - Événements graves/positifs
    - Congestion nuit
    """
    
    def __init__(
        self,
        congestion_statique: Dict[str, float],
        microzone_ids: List[str],
        matrices_voisin: Optional[Dict[str, any]] = None,
        seed: Optional[int] = None
    ):
        """
        Initialise le calculateur de congestion.
        
        Args:
            congestion_statique: Congestion statique de base par microzone
            microzone_ids: Liste des identifiants de microzones
            matrices_voisin: Matrices de voisinage (optionnel)
            seed: Seed pour reproductibilité
        """
        self.congestion_statique = congestion_statique
        self.microzone_ids = microzone_ids
        self.matrices_voisin = matrices_voisin or {}
        
        # Générateur aléatoire
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Historique pour effets temporels
        # Structure : Dict[microzone_id, List[Tuple[jour, type_incident, gravite]]]
        self.historique_incidents: Dict[str, List[Tuple[int, str, str]]] = {
            mz_id: [] for mz_id in microzone_ids
        }
        
        # Table de congestion dynamique
        # Structure : Dict[microzone_id, Dict[jour, float]]
        self.congestion_table: Dict[str, Dict[int, float]] = {
            mz_id: {} for mz_id in microzone_ids
        }
    
    @classmethod
    def load_static_congestion(cls) -> Dict[str, float]:
        """
        Charge la congestion statique depuis data/source_data/congestion_statique.pkl.
        
        Accepte soit le format standardisé (load_pickle), soit le format legacy
        (DataFrame pré-calcul : microzone_id, congestion_base_*), soit un dict brut.
        
        Returns:
            Dictionnaire {microzone_id: congestion_statique}
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        path = PathResolver.data_source("congestion_statique.pkl")
        
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier congestion_statique.pkl introuvable: {path}. "
                f"Assurez-vous que les pré-calculs (Epic 1, Story 1.3) ont été exécutés."
            )
        
        try:
            data = load_pickle(path, expected_type="congestion")
        except ValueError:
            with open(path, "rb") as f:
                data = pickle.load(f)
        
        if isinstance(data, dict) and not _looks_like_metadata(data):
            return data
        if _is_congestion_dataframe(data):
            return _congestion_dataframe_to_dict(data)
        raise ValueError(f"Format de congestion_statique inattendu: {type(data)}")
    
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
    
    def _get_season_factor(self, season: str) -> float:
        """
        Retourne le facteur saisonnier pour la congestion.
        
        Intersaison > hiver/été (congestion plus forte en printemps/automne).
        
        Args:
            season: Saison ("hiver", "intersaison", "ete")
        
        Returns:
            Facteur multiplicatif
        """
        factors = {
            "intersaison": 1.2,  # +20% congestion (plus forte)
            "hiver": 0.9,  # -10% congestion
            "ete": 0.9  # -10% congestion
        }
        return factors.get(season, 1.0)
    
    def _detect_important_event(
        self,
        microzone_id: str,
        vectors: Dict[str, Vector]
    ) -> bool:
        """
        Détecte si un événement important a eu lieu (pour basculer randomité 0.2 → 0.7).
        
        Événements importants : incendies graves, accidents majeurs, agressions graves.
        
        Args:
            microzone_id: Identifiant de la microzone
            vectors: Vecteurs du jour par type d'incident
        
        Returns:
            True si événement important détecté
        """
        # Incendie grave
        incendie = vectors.get(INCIDENT_TYPE_INCENDIE)
        if incendie and incendie.grave > 0:
            return True
        
        # Accident majeur (grave ou beaucoup de moyen)
        accident = vectors.get(INCIDENT_TYPE_ACCIDENT)
        if accident and (accident.grave > 0 or accident.moyen >= 3):
            return True
        
        # Agression grave
        agression = vectors.get(INCIDENT_TYPE_AGRESSION)
        if agression and agression.grave > 0:
            return True
        
        return False
    
    def _calculate_randomness_component(
        self,
        microzone_id: str,
        vectors: Dict[str, Vector],
        is_important_event: bool
    ) -> float:
        """
        Calcule la composante randomité avec pondération dynamique.
        
        Args:
            microzone_id: Identifiant de la microzone
            vectors: Vecteurs du jour
            is_important_event: Si événement important détecté
        
        Returns:
            Composante randomité (0.0-1.0)
        """
        # Randomité de base
        randomite = float(self.rng.uniform(0.0, 1.0))
        
        # Pondération selon événement important
        if is_important_event:
            poids = PONDERATION_RANDOMITE_EVENEMENT  # 70%
        else:
            poids = PONDERATION_RANDOMITE_NORMALE  # 20%
        
        return randomite * poids
    
    def _calculate_accident_effect(
        self,
        vectors: Dict[str, Vector]
    ) -> float:
        """
        Calcule l'effet des accidents sur la congestion (↑).
        
        Args:
            vectors: Vecteurs du jour
        
        Returns:
            Facteur multiplicatif (≥ 1.0)
        """
        accident = vectors.get(INCIDENT_TYPE_ACCIDENT)
        if accident is None:
            return 1.0
        
        total_accidents = accident.total()
        if total_accidents == 0:
            return 1.0
        
        # Effet : +5% par accident (avec cap)
        effect = 1.0 + min(0.3, total_accidents * 0.05)  # Max +30%
        return effect
    
    def _calculate_fire_effect_temporal(
        self,
        microzone_id: str,
        day: int,
        vectors: Dict[str, Vector]
    ) -> float:
        """
        Calcule l'effet des incendies avec effets temporels.
        
        - Jour J : ↑ congestion (×1.2)
        - Jours J+1 et J+2 : ↓ congestion (×0.8 - état de choc)
        
        Args:
            microzone_id: Identifiant de la microzone
            day: Numéro du jour (1-indexé)
            vectors: Vecteurs du jour
        
        Returns:
            Facteur multiplicatif
        """
        incendie = vectors.get(INCIDENT_TYPE_INCENDIE)
        
        # Vérifier si incendie moyen/grave aujourd'hui
        if incendie and (incendie.moyen > 0 or incendie.grave > 0):
            # Jour J : ↑ congestion
            self.historique_incidents[microzone_id].append((day, INCIDENT_TYPE_INCENDIE, "moyen_grave"))
            return 1.2
        
        # Vérifier effets temporels (J+1, J+2)
        historique = self.historique_incidents.get(microzone_id, [])
        for jour_incendie, inc_type, gravite in historique:
            if inc_type == INCIDENT_TYPE_INCENDIE and gravite == "moyen_grave":
                if day == jour_incendie + 1 or day == jour_incendie + 2:
                    return 0.8  # ↓ congestion (état de choc)
        
        return 1.0
    
    def _calculate_aggression_effect_temporal(
        self,
        microzone_id: str,
        day: int,
        vectors: Dict[str, Vector]
    ) -> float:
        """
        Calcule l'effet des agressions graves avec effets temporels.
        
        - Jour J : ↑↑ congestion (×1.5 - augmentation forte)
        - Jours J+1, J+2, J+3 : ↓ congestion (×0.7 - augmentation circulation)
        
        Args:
            microzone_id: Identifiant de la microzone
            day: Numéro du jour (1-indexé)
            vectors: Vecteurs du jour
        
        Returns:
            Facteur multiplicatif
        """
        agression = vectors.get(INCIDENT_TYPE_AGRESSION)
        
        # Vérifier si agression grave aujourd'hui
        if agression and agression.grave > 0:
            # Jour J : ↑↑ congestion (forte)
            self.historique_incidents[microzone_id].append((day, INCIDENT_TYPE_AGRESSION, "grave"))
            return 1.5
        
        # Vérifier effets temporels (J+1, J+2, J+3)
        historique = self.historique_incidents.get(microzone_id, [])
        for jour_agression, inc_type, gravite in historique:
            if inc_type == INCIDENT_TYPE_AGRESSION and gravite == "grave":
                if day in [jour_agression + 1, jour_agression + 2, jour_agression + 3]:
                    return 0.7  # ↓ congestion
        
        return 1.0
    
    def _calculate_neighbor_effect(
        self,
        microzone_id: str,
        day: int
    ) -> float:
        """
        Calcule l'effet des voisins (propagation spatiale).
        
        Args:
            microzone_id: Identifiant de la microzone
            day: Numéro du jour (0-indexé pour table)
        
        Returns:
            Facteur multiplicatif
        """
        voisin_data = self.matrices_voisin.get(microzone_id, {})
        voisins = voisin_data.get("voisins", [])
        
        if not voisins:
            return 1.0
        
        # Calculer congestion moyenne des voisins
        total_voisin = 0.0
        count = 0
        
        for voisin_id in voisins:
            if voisin_id in self.congestion_table:
                congestion_voisin = self.congestion_table[voisin_id].get(day, 0.0)
                if congestion_voisin > 0:
                    total_voisin += congestion_voisin
                    count += 1
        
        if count == 0:
            return 1.0
        
        # Effet : +10% si voisins ont congestion élevée
        congestion_moyenne_voisins = total_voisin / count
        if congestion_moyenne_voisins > 0.5:  # Seuil
            return 1.1
        
        return 1.0
    
    def _calculate_recurrence_effect(
        self,
        microzone_id: str,
        day: int
    ) -> float:
        """
        Calcule l'effet de récurrence (historique de la microzone).
        
        Args:
            microzone_id: Identifiant de la microzone
            day: Numéro du jour (0-indexé)
        
        Returns:
            Facteur multiplicatif
        """
        # Regarder les 7 derniers jours
        recent_congestion = []
        for d in range(max(0, day - 7), day):
            if d in self.congestion_table.get(microzone_id, {}):
                recent_congestion.append(self.congestion_table[microzone_id][d])
        
        if not recent_congestion:
            return 1.0
        
        # Si congestion récente élevée, effet persistant
        moyenne_recente = np.mean(recent_congestion)
        if moyenne_recente > 0.6:
            return 1.05  # +5% effet persistant
        
        return 1.0
    
    def _calculate_night_congestion_factor(
        self,
        microzone_id: str,
        vectors: Dict[str, Vector],
        season: str,
        incidents_nuit: Optional[Dict[str, int]] = None
    ) -> float:
        """
        Calcule le facteur de congestion nuit pour incidents nocturnes.
        
        Congestion divisée par 3 en moyenne (avec effet aléatoire) ou 2.2 l'été.
        Application uniquement pour incidents s'étant produit la nuit.
        
        Args:
            microzone_id: Identifiant de la microzone
            vectors: Vecteurs du jour
            season: Saison actuelle
            incidents_nuit: Incidents nocturnes pour cette microzone (optionnel, Dict[type_incident, count])
        
        Returns:
            Facteur multiplicatif (≤ 1.0)
        """
        # Vérifier s'il y a des incidents nocturnes
        if incidents_nuit is None or len(incidents_nuit) == 0:
            return 1.0
        
        # incidents_nuit est déjà le dictionnaire pour cette microzone (Dict[type_incident, count])
        total_nuit = sum(incidents_nuit.values())
        
        if total_nuit == 0:
            return 1.0
        
        # Facteur selon saison
        if season == "ete":
            facteur_base = FACTEUR_CONGESTION_NUIT_ETE  # 2.2
        else:
            facteur_base = FACTEUR_CONGESTION_NUIT_MOYEN  # 3.0
        
        # Ajouter effet aléatoire (±20%)
        variation = self.rng.uniform(0.8, 1.2)
        facteur_final = facteur_base * variation
        
        # Retourner facteur inverse (diviser = multiplier par 1/facteur)
        return 1.0 / facteur_final
    
    def calculate_congestion_for_day(
        self,
        day: int,
        vectors: Dict[str, Dict[str, Vector]],
        events_grave: Optional[List] = None,
        events_positifs: Optional[List] = None,
        incidents_nuit: Optional[Dict[str, Dict[str, int]]] = None
    ) -> Dict[str, float]:
        """
        Calcule le taux de ralentissement (congestion) pour toutes les microzones un jour donné.
        
        Args:
            day: Numéro du jour (0-indexé pour table, converti en 1-indexé pour saison)
            vectors: Vecteurs par microzone et type d'incident
            events_grave: Événements graves du jour (optionnel, pour modification temps réel)
            events_positifs: Événements positifs du jour (optionnel)
            incidents_nuit: Incidents nocturnes par microzone (optionnel)
        
        Returns:
            Dictionnaire {microzone_id: taux_ralentissement}
        """
        day_1_indexed = day + 1  # Conversion pour saison
        season = self._get_season(day_1_indexed)
        season_factor = self._get_season_factor(season)
        
        congestion_jour = {}
        
        for mz_id in self.microzone_ids:
            # Congestion statique de base
            congestion_base = self.congestion_statique.get(mz_id, 0.5)  # Valeur par défaut
            
            # Vecteurs de la microzone
            vectors_mz = vectors.get(mz_id, {})
            
            # Détecter événement important
            is_important_event = self._detect_important_event(mz_id, vectors_mz)
            
            # Composante randomité avec pondération dynamique
            randomite = self._calculate_randomness_component(mz_id, vectors_mz, is_important_event)
            
            # Composante déterministe (1 - poids randomité)
            poids_deterministe = 1.0 - (PONDERATION_RANDOMITE_EVENEMENT if is_important_event else PONDERATION_RANDOMITE_NORMALE)
            
            # Effets déterministes
            accident_effect = self._calculate_accident_effect(vectors_mz)
            fire_effect = self._calculate_fire_effect_temporal(mz_id, day_1_indexed, vectors_mz)
            aggression_effect = self._calculate_aggression_effect_temporal(mz_id, day_1_indexed, vectors_mz)
            neighbor_effect = self._calculate_neighbor_effect(mz_id, day)
            recurrence_effect = self._calculate_recurrence_effect(mz_id, day)
            
            # Facteur déterministe agrégé
            facteur_deterministe = (
                accident_effect *
                fire_effect *
                aggression_effect *
                neighbor_effect *
                recurrence_effect *
                season_factor
            )
            
            # Congestion nuit (si incidents nocturnes)
            incidents_nuit_mz = incidents_nuit.get(mz_id, {}) if incidents_nuit else {}
            night_factor = self._calculate_night_congestion_factor(
                mz_id, vectors_mz, season, incidents_nuit_mz
            )
            
            # Calcul final : congestion_statique × (randomité + déterministe) × nuit
            congestion_deterministe = congestion_base * facteur_deterministe * poids_deterministe
            congestion_randomite = congestion_base * randomite
            
            congestion_finale = (congestion_deterministe + congestion_randomite) * night_factor
            
            # Effets événements (modification temps réel)
            # Note: Les événements affectent les arrondissements, pas directement les microzones
            # Pour simplifier, on applique un effet global si événements présents
            if events_grave:
                # Effet cumulatif modéré
                effect_grave = 1.0 + min(0.5, len(events_grave) * 0.1)  # Max +50%
                congestion_finale *= effect_grave
            
            if events_positifs:
                # Effet cumulatif modéré
                effect_positif = 1.0 - min(0.2, len(events_positifs) * 0.05)  # Max -20%
                congestion_finale *= effect_positif
            
            # Clamp dans plage raisonnable [0.1, 5.0]
            congestion_finale = max(0.1, min(5.0, congestion_finale))
            
            congestion_jour[mz_id] = congestion_finale
            
            # Stocker dans la table
            if mz_id not in self.congestion_table:
                self.congestion_table[mz_id] = {}
            self.congestion_table[mz_id][day] = congestion_finale
        
        return congestion_jour
    
    def get_congestion(
        self,
        microzone_id: str,
        day: int
    ) -> Optional[float]:
        """
        Récupère le taux de ralentissement pour une microzone et un jour.
        
        Args:
            microzone_id: Identifiant de la microzone
            day: Numéro du jour (0-indexé)
        
        Returns:
            Taux de ralentissement ou None si non calculé
        """
        return self.congestion_table.get(microzone_id, {}).get(day)
    
    def update_congestion_realtime(
        self,
        microzone_id: str,
        day: int,
        new_congestion: float
    ) -> None:
        """
        Met à jour la congestion en temps réel (pour événements graves).
        
        Args:
            microzone_id: Identifiant de la microzone
            day: Numéro du jour (0-indexé)
            new_congestion: Nouveau taux de ralentissement
        """
        if microzone_id not in self.congestion_table:
            self.congestion_table[microzone_id] = {}
        
        self.congestion_table[microzone_id][day] = max(0.1, min(5.0, new_congestion))
    
    def to_dict(self) -> Dict:
        """
        Convertit la table de congestion en dictionnaire (pour sérialisation).
        
        Returns:
            Dictionnaire représentant la table
        """
        return self.congestion_table.copy()
    
    def save(self, run_id: str, output_path: Optional[str] = None) -> None:
        """
        Sauvegarde la table de congestion au format pickle standardisé.
        
        Args:
            run_id: Identifiant du run
            output_path: Chemin de sortie (si None, utilise data/intermediate/run_{run_id}/generation/congestion.pkl)
        """
        from ..utils.pickle_utils import save_pickle
        from ..utils.path_resolver import PathResolver
        
        if output_path is None:
            path = PathResolver.data_intermediate(f"run_{run_id}", "generation", "congestion.pkl")
        else:
            from pathlib import Path
            path = Path(output_path)
        
        save_pickle(
            data=self.to_dict(),
            path=path,
            data_type="congestion",
            description=f"Table de congestion dynamique pour {len(self.microzone_ids)} microzones",
            run_id=run_id,
            schema_version="1.0"
        )
