"""
Chargement et utilisation des vecteurs statiques pour intensités de base et régimes.
Story 2.2.10 - Utilisation vecteurs statiques pour régimes et intensités de base
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..utils.path_resolver import PathResolver
from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from ..state.regime_state import (
    REGIME_CRISE,
    REGIME_DETERIORATION,
    REGIME_STABLE,
)
from .calibration import (
    BASE_INTENSITY_ACCIDENT,
    BASE_INTENSITY_AGRESSION,
    BASE_INTENSITY_INCENDIE,
    DEFAULT_INTENSITES_BY_TYPE,
)

TYPES_INCIDENT = [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]

# Cibles calibration : moyenne par type (ancrage réaliste)
_TARGET_BASE_BY_TYPE = {
    INCIDENT_TYPE_ACCIDENT: BASE_INTENSITY_ACCIDENT,
    INCIDENT_TYPE_AGRESSION: BASE_INTENSITY_AGRESSION,
    INCIDENT_TYPE_INCENDIE: BASE_INTENSITY_INCENDIE,
}

# Clés fichier (pluriel) → clés code (singulier) — scripts pré-calcul sauvegardent "agressions", etc.
TYPE_KEY_PLURAL_TO_SINGULAR = {
    "agressions": INCIDENT_TYPE_AGRESSION,
    "incendies": INCIDENT_TYPE_INCENDIE,
    "accidents": INCIDENT_TYPE_ACCIDENT,
}

# Facteurs de conversion vecteurs statiques → intensités Poisson
# Les vecteurs statiques sont normalisés [0, 1], on les convertit en intensités λ > 0
FACTEUR_BENIN = 0.5   # Intensité bénin
FACTEUR_MOYEN = 1.0   # Intensité moyen
FACTEUR_GRAVE = 2.0   # Intensité grave (plus rare mais plus impactant)


class StaticVectorLoader:
    """
    Chargeur et processeur de vecteurs statiques.
    
    Charge les vecteurs statiques pré-calculés (Story 1.3) et les utilise pour :
    1. Calculer les intensités de base λ_base(τ,g) par type et gravité
    2. Influencer les probabilités initiales des régimes cachés
    """
    
    def __init__(
        self,
        vecteurs_statiques: Optional[Dict[str, Dict[str, Tuple[float, float, float]]]] = None,
        lissage_alpha: float = 1.0,
    ):
        """
        Initialise le chargeur de vecteurs statiques.
        
        Args:
            vecteurs_statiques: Vecteurs statiques (si None, chargés depuis fichier)
                Format: Dict[microzone_id, Dict[type_incident, tuple(bénin, moyen, grave)]]
            lissage_alpha: Alpha de lissage (1=aucun, 0.7≈−30% disparité).
                v_lissé = α * v_brut + (1−α) * moyenne_par_type_gravité
        """
        if vecteurs_statiques is None:
            vecteurs_statiques = self.load_static_vectors()
        
        self.vecteurs_statiques = vecteurs_statiques
        
        if lissage_alpha < 1.0:
            self.vecteurs_statiques = self._appliquer_lissage(lissage_alpha)
        
        # Calculer moyenne globale pour normalisation
        self.moyenne_globale = self._calculer_moyenne_globale()
    
    @classmethod
    def load_static_vectors(cls) -> Dict[str, Dict[str, Tuple[float, float, float]]]:
        """
        Charge les vecteurs statiques depuis data/source_data/vecteurs_statiques.pkl.
        
        Returns:
            Dict[microzone_id, Dict[type_incident, tuple(bénin, moyen, grave)]]
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        path = PathResolver.data_source("vecteurs_statiques.pkl")
        
        if not path.exists():
            raise FileNotFoundError(f"Fichier vecteurs_statiques.pkl introuvable: {path}")
        
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            # Si format standardisé, extraire les données
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            
            # Convertir en format attendu
            vecteurs = {}
            if isinstance(data, dict):
                for mz_id, vectors in data.items():
                    vecteurs[mz_id] = {}
                    if isinstance(vectors, dict):
                        for inc_type, vector in vectors.items():
                            # Clé normalisée : fichier peut avoir "agressions", code attend "agression"
                            key = TYPE_KEY_PLURAL_TO_SINGULAR.get(inc_type, inc_type)
                            # Extraire le vecteur (bénin, moyen, grave)
                            if isinstance(vector, (list, tuple)) and len(vector) == 3:
                                vecteurs[mz_id][key] = tuple(float(x) for x in vector)
                            elif hasattr(vector, 'benin') and hasattr(vector, 'moyen') and hasattr(vector, 'graves'):
                                vecteurs[mz_id][key] = (float(vector.benin), float(vector.moyen), float(vector.graves))
                            elif hasattr(vector, 'benin') and hasattr(vector, 'moyen') and hasattr(vector, 'grave'):
                                vecteurs[mz_id][key] = (float(vector.benin), float(vector.moyen), float(vector.grave))
                            else:
                                vecteurs[mz_id][key] = (0.0, 0.0, 0.0)
            
            return vecteurs
        except Exception as e:
            raise IOError(f"Erreur lors du chargement des vecteurs statiques: {e}") from e
    
    def _appliquer_lissage(
        self,
        alpha: float,
    ) -> Dict[str, Dict[str, Tuple[float, float, float]]]:
        """
        Lissage par mélange avec la moyenne par (type, gravité).
        v_lissé = α * v_brut + (1−α) * moyenne_globale_type_gravité
        Réduit l'écart-type entre microzones (ex. α=0.7 → ~−30% disparité).
        """
        if not self.vecteurs_statiques or alpha >= 1.0:
            return self.vecteurs_statiques
        
        # Moyennes par (type_incident, indice_gravité 0=bénin, 1=moyen, 2=grave)
        sums: Dict[str, List[float]] = {}
        counts: Dict[str, List[int]] = {}
        for mz_id, vectors in self.vecteurs_statiques.items():
            for inc_type, vector in vectors.items():
                if inc_type not in sums:
                    sums[inc_type] = [0.0, 0.0, 0.0]
                    counts[inc_type] = [0, 0, 0]
                if isinstance(vector, (list, tuple)) and len(vector) == 3:
                    for i, x in enumerate(vector):
                        sums[inc_type][i] += float(x)
                        counts[inc_type][i] += 1
        
        means: Dict[str, Tuple[float, float, float]] = {}
        for inc_type, tot in sums.items():
            c = counts[inc_type]
            means[inc_type] = tuple(
                tot[i] / c[i] if c[i] > 0 else 0.0 for i in range(3)
            )
        
        # Appliquer v_lissé = α * v_brut + (1−α) * moyenne
        result: Dict[str, Dict[str, Tuple[float, float, float]]] = {}
        for mz_id, vectors in self.vecteurs_statiques.items():
            result[mz_id] = {}
            for inc_type, vector in vectors.items():
                if not isinstance(vector, (list, tuple)) or len(vector) != 3:
                    result[mz_id][inc_type] = vector if isinstance(vector, tuple) else (0.0, 0.0, 0.0)
                    continue
                m = means.get(inc_type, (0.0, 0.0, 0.0))
                smoothed = tuple(
                    alpha * float(v) + (1.0 - alpha) * m[i]
                    for i, v in enumerate(vector)
                )
                result[mz_id][inc_type] = smoothed
        return result

    def _calculer_moyenne_globale(self) -> float:
        """
        Calcule la moyenne globale des vecteurs statiques (toutes microzones, tous types, toutes gravités).
        
        Returns:
            Moyenne globale
        """
        if not self.vecteurs_statiques:
            return 1.0
        
        total = 0.0
        count = 0
        
        for mz_id, vectors in self.vecteurs_statiques.items():
            for inc_type, vector in vectors.items():
                if isinstance(vector, (list, tuple)) and len(vector) == 3:
                    total += sum(vector)
                    count += 3
        
        return total / count if count > 0 else 1.0
    
    def calculer_intensites_base(
        self,
        microzone_id: str,
        incident_type: str
    ) -> Dict[str, float]:
        """
        Calcule les intensités de base λ_base(τ,g) à partir des vecteurs statiques.
        
        Conversion : vecteur statique (valeurs 0-1) → intensité Poisson (λ > 0)
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident
        
        Returns:
            Dictionnaire {'benin': float, 'moyen': float, 'grave': float}
        """
        vecteur = self.vecteurs_statiques.get(microzone_id, {}).get(incident_type)
        
        if vecteur is None:
            # Calibration réaliste : intensités de base par type (microzone moyenne)
            raw = DEFAULT_INTENSITES_BY_TYPE.get(incident_type, (0.1, 0.1, 0.05))
            benin, moyen, grave = raw
            return {
                'benin': float(benin * FACTEUR_BENIN),
                'moyen': float(moyen * FACTEUR_MOYEN),
                'grave': float(grave * FACTEUR_GRAVE)
            }
        
        if not isinstance(vecteur, (list, tuple)) or len(vecteur) != 3:
            raw = DEFAULT_INTENSITES_BY_TYPE.get(incident_type, (0.1, 0.1, 0.05))
            benin, moyen, grave = raw
            return {
                'benin': float(benin * FACTEUR_BENIN),
                'moyen': float(moyen * FACTEUR_MOYEN),
                'grave': float(grave * FACTEUR_GRAVE)
            }
        
        benin, moyen, grave = vecteur
        
        # Conversion en intensités Poisson
        return {
            'benin': float(benin * FACTEUR_BENIN),
            'moyen': float(moyen * FACTEUR_MOYEN),
            'grave': float(grave * FACTEUR_GRAVE)
        }
    
    def calculer_intensite_base_totale(
        self,
        microzone_id: str,
        incident_type: str
    ) -> float:
        """
        Calcule l'intensité de base totale (somme des intensités par gravité).
        
        Utilisé pour rétrocompatibilité avec le code existant qui attend une valeur unique.
        
        Args:
            microzone_id: Identifiant de la microzone
            incident_type: Type d'incident
        
        Returns:
            Intensité de base totale
        """
        intensites = self.calculer_intensites_base(microzone_id, incident_type)
        return intensites['benin'] + intensites['moyen'] + intensites['grave']
    
    def calculer_facteur_regimes(
        self,
        microzone_id: str
    ) -> float:
        """
        Calcule le facteur d'influence des vecteurs statiques sur les probabilités régimes.
        
        Args:
            microzone_id: Identifiant de la microzone
        
        Returns:
            Facteur d'influence (1.0 = moyenne, >1.0 = zone à risque, <1.0 = zone calme)
        """
        # Somme des vecteurs statiques (tous types, toutes gravités)
        somme_totale = 0.0
        
        for inc_type in TYPES_INCIDENT:
            vecteur = self.vecteurs_statiques.get(microzone_id, {}).get(inc_type)
            if vecteur is not None and isinstance(vecteur, (list, tuple)) and len(vecteur) == 3:
                somme_totale += sum(vecteur)
        
        # Normalisation par rapport à la moyenne globale
        if self.moyenne_globale > 0:
            facteur = somme_totale / (self.moyenne_globale * len(TYPES_INCIDENT) * 3)
        else:
            facteur = 1.0
        
        return float(facteur)
    
    def calculer_probabilites_regimes(
        self,
        microzone_id: str
    ) -> Dict[str, float]:
        """
        Calcule les probabilités initiales des régimes selon les vecteurs statiques.
        
        Zones à risque élevé → plus de Crise
        Zones calmes → plus de Stable
        
        Args:
            microzone_id: Identifiant de la microzone
        
        Returns:
            Dictionnaire {REGIME_STABLE: float, REGIME_DETERIORATION: float, REGIME_CRISE: float}
        """
        facteur = self.calculer_facteur_regimes(microzone_id)
        
        # Probabilités de base
        prob_stable_base = 0.80
        prob_deterioration_base = 0.15
        prob_crise_base = 0.05
        
        # Modifier selon facteur
        if facteur > 1.5:  # Zone à risque élevé
            # Plus de Crise, moins de Stable
            prob_stable = 0.6
            prob_deterioration = 0.25
            prob_crise = 0.15
        elif facteur < 0.7:  # Zone calme
            # Plus de Stable, moins de Crise
            prob_stable = 0.9
            prob_deterioration = 0.08
            prob_crise = 0.02
        else:  # Zone moyenne
            # Probabilités de base
            prob_stable = prob_stable_base
            prob_deterioration = prob_deterioration_base
            prob_crise = prob_crise_base
        
        # Normaliser pour s'assurer que la somme = 1
        total = prob_stable + prob_deterioration + prob_crise
        if total > 0:
            prob_stable /= total
            prob_deterioration /= total
            prob_crise /= total
        
        return {
            REGIME_STABLE: float(prob_stable),
            REGIME_DETERIORATION: float(prob_deterioration),
            REGIME_CRISE: float(prob_crise)
        }
    
    def get_base_intensities_dict(
        self,
        microzone_ids: Optional[list] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Retourne les intensités de base au format attendu par le code existant.
        
        Les vecteurs statiques servent de **poids relatifs** (zones à plus d'agressions
        en ont plus), mais la **moyenne par type** est ramenée aux cibles de calibration,
        pour éviter des valeurs aberrantes partout tout en gardant le réalisme spatial.
        
        Format: Dict[microzone_id, Dict[type_incident, float]]
        Utilisé pour rétrocompatibilité avec load_base_intensities().
        
        Args:
            microzone_ids: Liste des microzones (si None, utilise toutes les microzones disponibles)
        
        Returns:
            Dictionnaire des intensités de base (recalibrées en moyenne par type)
        """
        if microzone_ids is None:
            microzone_ids = list(self.vecteurs_statiques.keys())
        
        # 1) Intensités "brutes" depuis vecteurs statiques (ou défaut calibration)
        raw = {}
        for mz_id in microzone_ids:
            raw[mz_id] = {}
            for inc_type in TYPES_INCIDENT:
                raw[mz_id][inc_type] = self.calculer_intensite_base_totale(mz_id, inc_type)
        
        # 2) Recalibration : moyenne par type = cible calibration, rapports relatifs conservés
        intensities = {}
        for inc_type in TYPES_INCIDENT:
            values = [raw[mz_id][inc_type] for mz_id in microzone_ids]
            mean_raw = sum(values) / len(values) if values else 0.0
            target = _TARGET_BASE_BY_TYPE.get(inc_type, 0.2)
            for mz_id in microzone_ids:
                if mz_id not in intensities:
                    intensities[mz_id] = {}
                if mean_raw > 0:
                    # Poids relatif × cible : moyenne = target, différences entre mz conservées
                    intensities[mz_id][inc_type] = (raw[mz_id][inc_type] / mean_raw) * target
                else:
                    intensities[mz_id][inc_type] = target
        
        return intensities
