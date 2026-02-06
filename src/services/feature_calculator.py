"""
StateCalculator - Calcul des 18 features hebdomadaires par arrondissement.
Story 2.2.5 - Features hebdomadaires
"""

from typing import Dict, List, Optional

import pandas as pd

from ..core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)

# dynamic_state utilise clés pluriel (agressions, incendies, accidents)
_SINGULAR_TO_PLURAL = {
    INCIDENT_TYPE_AGRESSION: "agressions",
    INCIDENT_TYPE_INCENDIE: "incendies",
    INCIDENT_TYPE_ACCIDENT: "accidents",
}
from ..core.state.dynamic_state import DynamicState
from ..core.state.vectors_state import VectorsState
from ..core.utils.path_resolver import PathResolver
from ..core.utils.pickle_utils import save_pickle
from .casualty_calculator import CasualtyCalculator


class StateCalculator:
    """
    Calculateur de 18 features hebdomadaires par arrondissement.
    
    Features :
    - 6 features sommes incidents : (moyen+grave) et bénin par type
    - 6 features proportions : alcool et nuit par type
    - 3 features morts : par type
    - 3 features blessés graves : par type
    """
    
    def __init__(
        self,
        limites_microzone_arrondissement: Dict[str, int],
        casualty_calculator: Optional[CasualtyCalculator] = None
    ):
        """
        Initialise le calculateur de features.
        
        Args:
            limites_microzone_arrondissement: Mapping microzone_id → arrondissement
            casualty_calculator: Calculateur de casualties (optionnel, pour morts/blessés)
        """
        self.limites_microzone_arrondissement = limites_microzone_arrondissement
        self.casualty_calculator = casualty_calculator
    
    def _agreger_microzones_arrondissements(
        self,
        valeurs_microzones: Dict[str, float]
    ) -> Dict[int, float]:
        """
        Agrège des valeurs de microzones vers arrondissements.
        
        Args:
            valeurs_microzones: Valeurs par microzone
        
        Returns:
            Dictionnaire {arrondissement: somme_valeurs}
        """
        valeurs_arrondissements = {}
        
        for microzone_id, valeur in valeurs_microzones.items():
            arrondissement = self.limites_microzone_arrondissement.get(microzone_id)
            
            if arrondissement is None:
                continue
            
            if arrondissement not in valeurs_arrondissements:
                valeurs_arrondissements[arrondissement] = 0.0
            
            valeurs_arrondissements[arrondissement] += valeur
        
        return valeurs_arrondissements
    
    def _calculer_sommes_incidents_semaine(
        self,
        semaine: int,
        vectors_state: VectorsState
    ) -> Dict[int, Dict[str, Dict[str, int]]]:
        """
        Calcule les 6 features sommes incidents pour une semaine.
        
        Features : (moyen+grave) et bénin par type (agressions, incendies, accidents)
        
        Args:
            semaine: Numéro de la semaine (1-indexé)
            vectors_state: État des vecteurs
        
        Returns:
            Dictionnaire {arrondissement: {type_incident: {'moyen_grave': int, 'benin': int}}}
        """
        # Calculer jours de la semaine (0-indexé)
        jour_debut = (semaine - 1) * 7
        jours_semaine = list(range(jour_debut, jour_debut + 7))
        
        # Agrégation par microzone
        sommes_microzones = {}
        
        for microzone_id in self.limites_microzone_arrondissement.keys():
            sommes_microzones[microzone_id] = {
                INCIDENT_TYPE_AGRESSION: {'moyen_grave': 0, 'benin': 0},
                INCIDENT_TYPE_INCENDIE: {'moyen_grave': 0, 'benin': 0},
                INCIDENT_TYPE_ACCIDENT: {'moyen_grave': 0, 'benin': 0}
            }
            
            for jour in jours_semaine:
                vectors_jour = vectors_state.get_vectors_for_day(microzone_id, jour)
                
                for type_incident, vector in vectors_jour.items():
                    if vector:
                        sommes_microzones[microzone_id][type_incident]['moyen_grave'] += vector.grave + vector.moyen
                        sommes_microzones[microzone_id][type_incident]['benin'] += vector.benin
        
        # Agrégation microzones → arrondissements
        sommes_arrondissements = {}
        
        for microzone_id, sommes_mz in sommes_microzones.items():
            arrondissement = self.limites_microzone_arrondissement.get(microzone_id)
            
            if arrondissement is None:
                continue
            
            if arrondissement not in sommes_arrondissements:
                sommes_arrondissements[arrondissement] = {
                    INCIDENT_TYPE_AGRESSION: {'moyen_grave': 0, 'benin': 0},
                    INCIDENT_TYPE_INCENDIE: {'moyen_grave': 0, 'benin': 0},
                    INCIDENT_TYPE_ACCIDENT: {'moyen_grave': 0, 'benin': 0}
                }
            
            for type_incident in [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]:
                sommes_arrondissements[arrondissement][type_incident]['moyen_grave'] += sommes_mz[type_incident]['moyen_grave']
                sommes_arrondissements[arrondissement][type_incident]['benin'] += sommes_mz[type_incident]['benin']
        
        return sommes_arrondissements
    
    def _calculer_proportions_alcool_nuit_semaine(
        self,
        semaine: int,
        vectors_state: VectorsState,
        dynamic_state: DynamicState
    ) -> Dict[int, Dict[str, Dict[str, float]]]:
        """
        Calcule les 6 features proportions alcool et nuit pour une semaine.
        
        Features : alcool et nuit par type (agressions, incendies, accidents)
        
        Args:
            semaine: Numéro de la semaine (1-indexé)
            vectors_state: État des vecteurs (pour calculer totaux incidents)
            dynamic_state: État dynamique (contient incidents_alcool et incidents_nuit)
        
        Returns:
            Dictionnaire {arrondissement: {type_incident: {'alcool': float, 'nuit': float}}}
        """
        # Calculer jours de la semaine (0-indexé)
        jour_debut = (semaine - 1) * 7
        jours_semaine = list(range(jour_debut, jour_debut + 7))
        
        # Agrégation par microzone
        proportions_microzones = {}
        totaux_microzones = {}
        
        for microzone_id in self.limites_microzone_arrondissement.keys():
            proportions_microzones[microzone_id] = {
                INCIDENT_TYPE_AGRESSION: {'alcool': 0, 'nuit': 0},
                INCIDENT_TYPE_INCENDIE: {'alcool': 0, 'nuit': 0},
                INCIDENT_TYPE_ACCIDENT: {'alcool': 0, 'nuit': 0}
            }
            totaux_microzones[microzone_id] = {
                INCIDENT_TYPE_AGRESSION: 0,
                INCIDENT_TYPE_INCENDIE: 0,
                INCIDENT_TYPE_ACCIDENT: 0
            }
            
            # Calculer total incidents depuis vecteurs
            total_incidents = {
                INCIDENT_TYPE_AGRESSION: 0,
                INCIDENT_TYPE_INCENDIE: 0,
                INCIDENT_TYPE_ACCIDENT: 0
            }
            
            for jour in jours_semaine:
                vectors_jour = vectors_state.get_vectors_for_day(microzone_id, jour)
                for type_incident, vector in vectors_jour.items():
                    if vector:
                        total_incidents[type_incident] += vector.total()
            
            # Récupérer incidents alcool et nuit depuis dynamic_state
            incidents_alcool = dynamic_state.incidents_alcool.get(microzone_id, {})
            incidents_nuit = dynamic_state.incidents_nuit.get(microzone_id, {})
            
            for type_incident in [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]:
                # Compter incidents alcool et nuit (dynamic_state utilise clés pluriel)
                key = _SINGULAR_TO_PLURAL.get(type_incident, type_incident)
                alcool_count = incidents_alcool.get(key, 0)
                nuit_count = incidents_nuit.get(key, 0)
                total = total_incidents[type_incident]
                
                # Calculer proportions
                if total > 0:
                    proportions_microzones[microzone_id][type_incident]['alcool'] = alcool_count / total
                    proportions_microzones[microzone_id][type_incident]['nuit'] = nuit_count / total
                else:
                    proportions_microzones[microzone_id][type_incident]['alcool'] = 0.0
                    proportions_microzones[microzone_id][type_incident]['nuit'] = 0.0
                
                totaux_microzones[microzone_id][type_incident] = total
        
        # Agrégation microzones → arrondissements (moyenne pondérée)
        proportions_arrondissements = {}
        totaux_arrondissements = {}
        
        for microzone_id, proportions_mz in proportions_microzones.items():
            arrondissement = self.limites_microzone_arrondissement.get(microzone_id)
            
            if arrondissement is None:
                continue
            
            if arrondissement not in proportions_arrondissements:
                proportions_arrondissements[arrondissement] = {
                    INCIDENT_TYPE_AGRESSION: {'alcool': 0.0, 'nuit': 0.0},
                    INCIDENT_TYPE_INCENDIE: {'alcool': 0.0, 'nuit': 0.0},
                    INCIDENT_TYPE_ACCIDENT: {'alcool': 0.0, 'nuit': 0.0}
                }
                totaux_arrondissements[arrondissement] = {
                    INCIDENT_TYPE_AGRESSION: 0,
                    INCIDENT_TYPE_INCENDIE: 0,
                    INCIDENT_TYPE_ACCIDENT: 0
                }
            
            for type_incident in [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]:
                total_mz = totaux_microzones[microzone_id][type_incident]
                totaux_arrondissements[arrondissement][type_incident] += total_mz
                
                # Moyenne pondérée
                proportions_arrondissements[arrondissement][type_incident]['alcool'] += proportions_mz[type_incident]['alcool'] * total_mz
                proportions_arrondissements[arrondissement][type_incident]['nuit'] += proportions_mz[type_incident]['nuit'] * total_mz
        
        # Normaliser (diviser par total)
        for arrondissement in proportions_arrondissements:
            for type_incident in [INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE, INCIDENT_TYPE_ACCIDENT]:
                total_arr = totaux_arrondissements[arrondissement][type_incident]
                if total_arr > 0:
                    proportions_arrondissements[arrondissement][type_incident]['alcool'] /= total_arr
                    proportions_arrondissements[arrondissement][type_incident]['nuit'] /= total_arr
        
        return proportions_arrondissements
    
    def calculer_features_semaine(
        self,
        semaine: int,
        vectors_state: VectorsState,
        dynamic_state: DynamicState,
        events_state=None
    ) -> pd.DataFrame:
        """
        Calcule les 18 features hebdomadaires pour une semaine.
        
        Args:
            semaine: Numéro de la semaine (1-indexé)
            vectors_state: État des vecteurs
            dynamic_state: État dynamique (alcool/nuit)
            events_state: État des événements (optionnel, pour casualties)
        
        Returns:
            DataFrame avec colonnes : arrondissement, semaine, feature_1, ..., feature_18
        """
        # 1. Calculer 6 features sommes incidents
        sommes = self._calculer_sommes_incidents_semaine(semaine, vectors_state)
        
        # 2. Calculer 6 features proportions alcool/nuit
        proportions = self._calculer_proportions_alcool_nuit_semaine(semaine, vectors_state, dynamic_state)
        
        # 3. Calculer 3 features morts (si casualty_calculator disponible)
        morts = {}
        if self.casualty_calculator and events_state:
            morts_dict, _ = self.casualty_calculator.calculer_casualties_semaine(
                semaine, vectors_state, events_state
            )
            # Convertir en format par type
            for arr, morts_arr in morts_dict.items():
                morts[arr] = {
                    INCIDENT_TYPE_ACCIDENT: morts_arr.get(INCIDENT_TYPE_ACCIDENT, 0),
                    INCIDENT_TYPE_INCENDIE: morts_arr.get(INCIDENT_TYPE_INCENDIE, 0),
                    INCIDENT_TYPE_AGRESSION: morts_arr.get(INCIDENT_TYPE_AGRESSION, 0)
                }
        
        # 4. Calculer 3 features blessés graves (si casualty_calculator disponible)
        blesses_graves = {}
        if self.casualty_calculator and events_state:
            _, blesses_dict = self.casualty_calculator.calculer_casualties_semaine(
                semaine, vectors_state, events_state
            )
            # Convertir en format par type
            for arr, blesses_arr in blesses_dict.items():
                blesses_graves[arr] = {
                    INCIDENT_TYPE_ACCIDENT: blesses_arr.get(INCIDENT_TYPE_ACCIDENT, 0),
                    INCIDENT_TYPE_INCENDIE: blesses_arr.get(INCIDENT_TYPE_INCENDIE, 0),
                    INCIDENT_TYPE_AGRESSION: blesses_arr.get(INCIDENT_TYPE_AGRESSION, 0)
                }
        
        # Construire DataFrame
        rows = []
        arrondissements = set()
        arrondissements.update(sommes.keys())
        arrondissements.update(proportions.keys())
        arrondissements.update(morts.keys())
        arrondissements.update(blesses_graves.keys())
        
        for arrondissement in arrondissements:
            row = {
                'arrondissement': arrondissement,
                'semaine': semaine
            }
            
            # Features sommes incidents (6)
            sommes_arr = sommes.get(arrondissement, {})
            row['agressions_moyen_grave'] = sommes_arr.get(INCIDENT_TYPE_AGRESSION, {}).get('moyen_grave', 0)
            row['agressions_benin'] = sommes_arr.get(INCIDENT_TYPE_AGRESSION, {}).get('benin', 0)
            row['incendies_moyen_grave'] = sommes_arr.get(INCIDENT_TYPE_INCENDIE, {}).get('moyen_grave', 0)
            row['incendies_benin'] = sommes_arr.get(INCIDENT_TYPE_INCENDIE, {}).get('benin', 0)
            row['accidents_moyen_grave'] = sommes_arr.get(INCIDENT_TYPE_ACCIDENT, {}).get('moyen_grave', 0)
            row['accidents_benin'] = sommes_arr.get(INCIDENT_TYPE_ACCIDENT, {}).get('benin', 0)
            
            # Features proportions (6)
            proportions_arr = proportions.get(arrondissement, {})
            row['agressions_alcool'] = proportions_arr.get(INCIDENT_TYPE_AGRESSION, {}).get('alcool', 0.0)
            row['agressions_nuit'] = proportions_arr.get(INCIDENT_TYPE_AGRESSION, {}).get('nuit', 0.0)
            row['incendies_alcool'] = proportions_arr.get(INCIDENT_TYPE_INCENDIE, {}).get('alcool', 0.0)
            row['incendies_nuit'] = proportions_arr.get(INCIDENT_TYPE_INCENDIE, {}).get('nuit', 0.0)
            row['accidents_alcool'] = proportions_arr.get(INCIDENT_TYPE_ACCIDENT, {}).get('alcool', 0.0)
            row['accidents_nuit'] = proportions_arr.get(INCIDENT_TYPE_ACCIDENT, {}).get('nuit', 0.0)
            
            # Features morts (3)
            morts_arr = morts.get(arrondissement, {})
            row['morts_accidents'] = morts_arr.get(INCIDENT_TYPE_ACCIDENT, 0)
            row['morts_incendies'] = morts_arr.get(INCIDENT_TYPE_INCENDIE, 0)
            row['morts_agressions'] = morts_arr.get(INCIDENT_TYPE_AGRESSION, 0)
            
            # Features blessés graves (3)
            blesses_arr = blesses_graves.get(arrondissement, {})
            row['blesses_graves_accidents'] = blesses_arr.get(INCIDENT_TYPE_ACCIDENT, 0)
            row['blesses_graves_incendies'] = blesses_arr.get(INCIDENT_TYPE_INCENDIE, 0)
            row['blesses_graves_agressions'] = blesses_arr.get(INCIDENT_TYPE_AGRESSION, 0)
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # S'assurer que toutes les colonnes sont numériques (sauf arrondissement et semaine)
        for col in df.columns:
            if col not in ['arrondissement', 'semaine']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    def calculer_features_multiple_semaines(
        self,
        semaines: List[int],
        vectors_state: VectorsState,
        dynamic_state: DynamicState,
        events_state=None
    ) -> pd.DataFrame:
        """
        Calcule les features pour plusieurs semaines.
        
        Args:
            semaines: Liste des numéros de semaines
            vectors_state: État des vecteurs
            dynamic_state: État dynamique
            events_state: État des événements (optionnel)
        
        Returns:
            DataFrame avec toutes les semaines
        """
        dfs = []
        
        for semaine in semaines:
            df_semaine = self.calculer_features_semaine(
                semaine, vectors_state, dynamic_state, events_state
            )
            dfs.append(df_semaine)
        
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def save_features(
        self,
        df_features: pd.DataFrame,
        run_id: str,
        output_path: Optional[str] = None
    ) -> None:
        """
        Sauvegarde les features au format pickle standardisé.
        
        Args:
            df_features: DataFrame des features
            run_id: Identifiant du run
            output_path: Chemin de sortie (si None, utilise data/intermediate/run_{run_id}/ml/features.pkl)
        """
        if output_path is None:
            path = PathResolver.data_intermediate(f"run_{run_id}", "ml", "features.pkl")
        else:
            from pathlib import Path
            path = Path(output_path)
        
        # Convertir DataFrame en dict pour pickle
        data_dict = {
            'data': df_features.to_dict('records'),
            'columns': list(df_features.columns),
            'index': df_features.index.tolist()
        }
        
        save_pickle(
            data=data_dict,
            path=path,
            data_type="features",
            description=f"Features hebdomadaires pour {len(df_features)} lignes",
            run_id=run_id,
            schema_version="1.0"
        )
    
    @classmethod
    def load_features(cls, run_id: str) -> pd.DataFrame:
        """
        Charge les features depuis un fichier pickle.
        
        Args:
            run_id: Identifiant du run
        
        Returns:
            DataFrame des features
        """
        from ..core.utils.pickle_utils import load_pickle
        
        path = PathResolver.data_intermediate(f"run_{run_id}", "ml", "features.pkl")
        
        if not path.exists():
            raise FileNotFoundError(f"Fichier features.pkl introuvable: {path}")
        
        data = load_pickle(path, expected_type="features")
        
        # Reconstruire DataFrame
        if isinstance(data, dict):
            if 'data' in data:
                df = pd.DataFrame(data['data'])
                if 'columns' in data:
                    df = df.reindex(columns=data['columns'])
                return df
            else:
                return pd.DataFrame(data)
        else:
            return pd.DataFrame(data)
