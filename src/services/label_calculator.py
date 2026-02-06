"""
LabelCalculator - Calcul des labels mensuels (score et classes).
Story 2.2.6 - Labels mensuels
"""

from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..core.state.casualties_state import CasualtiesState
from ..core.state.events_state import EventsState
from ..core.utils.path_resolver import PathResolver
from ..core.utils.pickle_utils import save_pickle

# Constantes pour seuils
SEUIL_MORTS_NORMAL = 1  # 1 mort/mois = seuil normal
SEUIL_MORTS_PRE_CATASTROPHE = 2  # 2 morts/mois = seuil pré-catastrophe
SEUIL_MORTS_CATASTROPHE = 3  # 3 morts/mois = seuil catastrophe

SEUIL_BLESSES_NORMAL = 4  # 4 blessés graves/mois = seuil normal
SEUIL_BLESSES_PRE_CATASTROPHE = 5  # 5 blessés graves/mois = seuil pré-catastrophe
SEUIL_BLESSES_CATASTROPHE = 6  # 6 blessés graves/mois = seuil catastrophe

# Classes
CLASSE_NORMAL = "Normal"
CLASSE_PRE_CATASTROPHE = "Pre-catastrophique"
CLASSE_CATASTROPHE = "Catastrophique"

# Semaines par mois
SEMAINES_PAR_MOIS = 4

# Cibles calibration Story 2.4.4 : ~85% Normal, ~10% Pre-cata, ~5% Cata
CALIBRATION_PCT_NORMAL = 0.85
CALIBRATION_PCT_PRE_CATA = 0.10
CALIBRATION_PCT_CATA = 0.05


class LabelCalculator:
    """
    Calculateur de labels mensuels (score et classes) par arrondissement.
    
    Calcule à partir de :
    - Casualties des événements uniquement (éviter double comptage)
    - Agrégation mensuelle glissante (exactement 4 semaines)
    - Score : morts + 0.5 × blessés_graves
    - Classes : Normal / Pre-catastrophique / Catastrophique
    """
    
    def __init__(
        self,
        seuils_morts: Optional[Dict[int, Tuple[int, int, int]]] = None,
        seuils_blesses: Optional[Dict[int, Tuple[int, int, int]]] = None
    ):
        """
        Initialise le calculateur de labels.
        
        Args:
            seuils_morts: Seuils morts par arrondissement (normal, pre-catastrophe, catastrophe)
            seuils_blesses: Seuils blessés graves par arrondissement (normal, pre-catastrophe, catastrophe)
        """
        # Seuils par arrondissement
        # Si None, utilise seuils par défaut
        self.seuils_morts = seuils_morts or {}
        self.seuils_blesses = seuils_blesses or {}
    
    def _get_seuils_morts(self, arrondissement: int) -> Tuple[int, int, int]:
        """
        Retourne les seuils morts pour un arrondissement.
        
        Args:
            arrondissement: Numéro de l'arrondissement
        
        Returns:
            Tuple (seuil_normal, seuil_pre_catastrophe, seuil_catastrophe)
        """
        if arrondissement in self.seuils_morts:
            return self.seuils_morts[arrondissement]
        
        # Seuils par défaut : 1, 2, 3 morts/mois
        return (SEUIL_MORTS_NORMAL, SEUIL_MORTS_PRE_CATASTROPHE, SEUIL_MORTS_CATASTROPHE)
    
    def _get_seuils_blesses(self, arrondissement: int) -> Tuple[int, int, int]:
        """
        Retourne les seuils blessés graves pour un arrondissement.
        
        Args:
            arrondissement: Numéro de l'arrondissement
        
        Returns:
            Tuple (seuil_normal, seuil_pre_catastrophe, seuil_catastrophe)
        """
        if arrondissement in self.seuils_blesses:
            return self.seuils_blesses[arrondissement]
        
        # Seuils par défaut : 4, 5, 6 blessés graves/mois
        return (SEUIL_BLESSES_NORMAL, SEUIL_BLESSES_PRE_CATASTROPHE, SEUIL_BLESSES_CATASTROPHE)
    
    def _calculer_casualties_evenements_mois(
        self,
        mois: int,
        events_state: EventsState
    ) -> Dict[int, Dict[str, int]]:
        """
        Calcule les casualties des événements uniquement pour un mois (4 semaines).
        
        Args:
            mois: Numéro du mois (1-indexé)
            events_state: État des événements
        
        Returns:
            Dictionnaire {arrondissement: {'morts': int, 'blesses_graves': int}}
        """
        # Calculer semaines du mois (1-indexé)
        semaine_debut = (mois - 1) * SEMAINES_PAR_MOIS + 1
        semaines_mois = list(range(semaine_debut, semaine_debut + SEMAINES_PAR_MOIS))
        
        # Calculer jours du mois (0-indexé)
        jour_debut = (semaine_debut - 1) * 7
        jours_mois = list(range(jour_debut, jour_debut + SEMAINES_PAR_MOIS * 7))
        
        casualties_mois = {}
        
        # Parcourir tous les jours du mois
        for jour in jours_mois:
            # Récupérer événements graves du jour
            events_grave = events_state.get_grave_events_for_day(jour)
            
            for event in events_grave:
                arrondissement = getattr(event, 'arrondissement', None)
                if arrondissement is None:
                    continue
                
                if arrondissement not in casualties_mois:
                    casualties_mois[arrondissement] = {'morts': 0, 'blesses_graves': 0}
                
                # Récupérer casualties_base de l'événement
                casualties_base = getattr(event, 'casualties_base', 0)
                
                # Pour simplifier, on considère que casualties_base = morts
                # Les blessés graves pourraient être calculés différemment selon l'événement
                casualties_mois[arrondissement]['morts'] += casualties_base
                
                # Estimer blessés graves (simplification : 2×morts)
                # En réalité, cela devrait venir de l'événement lui-même
                casualties_mois[arrondissement]['blesses_graves'] += casualties_base * 2
        
        return casualties_mois
    
    def _calculer_score(
        self,
        morts: int,
        blesses_graves: int
    ) -> float:
        """
        Calcule le score mensuel.
        
        Formule : morts + 0.5 × blessés_graves
        
        Args:
            morts: Nombre de morts
            blesses_graves: Nombre de blessés graves
        
        Returns:
            Score calculé
        """
        return morts + 0.5 * blesses_graves
    
    def _determiner_classe(
        self,
        arrondissement: int,
        morts: int,
        blesses_graves: int
    ) -> str:
        """
        Détermine la classe selon les seuils.
        
        Args:
            arrondissement: Numéro de l'arrondissement
            morts: Nombre de morts
            blesses_graves: Nombre de blessés graves
        
        Returns:
            Classe (Normal, Pre-catastrophique, Catastrophique)
        """
        seuils_morts = self._get_seuils_morts(arrondissement)
        seuils_blesses = self._get_seuils_blesses(arrondissement)
        
        seuil_normal_morts, seuil_pre_cat_morts, seuil_cat_morts = seuils_morts
        seuil_normal_blesses, seuil_pre_cat_blesses, seuil_cat_blesses = seuils_blesses
        
        # Déterminer classe selon morts OU blessés graves (le plus élevé)
        # Prendre le maximum entre classe_morts et classe_blesses
        
        # Classe selon morts
        if morts >= seuil_cat_morts:
            classe_morts = CLASSE_CATASTROPHE
        elif morts >= seuil_pre_cat_morts:
            classe_morts = CLASSE_PRE_CATASTROPHE
        elif morts >= seuil_normal_morts:
            classe_morts = CLASSE_NORMAL
        else:
            classe_morts = CLASSE_NORMAL
        
        # Classe selon blessés graves
        if blesses_graves >= seuil_cat_blesses:
            classe_blesses = CLASSE_CATASTROPHE
        elif blesses_graves >= seuil_pre_cat_blesses:
            classe_blesses = CLASSE_PRE_CATASTROPHE
        elif blesses_graves >= seuil_normal_blesses:
            classe_blesses = CLASSE_NORMAL
        else:
            classe_blesses = CLASSE_NORMAL
        
        # Prendre la classe la plus grave
        if classe_morts == CLASSE_CATASTROPHE or classe_blesses == CLASSE_CATASTROPHE:
            return CLASSE_CATASTROPHE
        elif classe_morts == CLASSE_PRE_CATASTROPHE or classe_blesses == CLASSE_PRE_CATASTROPHE:
            return CLASSE_PRE_CATASTROPHE
        else:
            return CLASSE_NORMAL
    
    def calculer_labels_mois(
        self,
        mois: int,
        events_state: EventsState
    ) -> pd.DataFrame:
        """
        Calcule les labels mensuels pour un mois.
        
        Args:
            mois: Numéro du mois (1-indexé)
            events_state: État des événements
        
        Returns:
            DataFrame avec colonnes : arrondissement, mois, score, classe, morts, blesses_graves
        """
        # Calculer casualties événements pour le mois
        casualties_mois = self._calculer_casualties_evenements_mois(mois, events_state)
        
        # Construire DataFrame
        rows = []
        
        for arrondissement, casualties in casualties_mois.items():
            morts = casualties.get('morts', 0)
            blesses_graves = casualties.get('blesses_graves', 0)
            
            # Calculer score
            score = self._calculer_score(morts, blesses_graves)
            
            # Déterminer classe
            classe = self._determiner_classe(arrondissement, morts, blesses_graves)
            
            rows.append({
                'arrondissement': arrondissement,
                'mois': mois,
                'score': score,
                'classe': classe,
                'morts': morts,
                'blesses_graves': blesses_graves
            })
        
        df = pd.DataFrame(rows)
        
        # S'assurer que toutes les colonnes sont du bon type
        if len(df) > 0:
            df['arrondissement'] = df['arrondissement'].astype(int)
            df['mois'] = df['mois'].astype(int)
            df['score'] = df['score'].astype(float)
            df['morts'] = df['morts'].astype(int)
            df['blesses_graves'] = df['blesses_graves'].astype(int)
        
        return df
    
    def calculer_labels_multiple_mois(
        self,
        mois: List[int],
        events_state: EventsState
    ) -> pd.DataFrame:
        """
        Calcule les labels pour plusieurs mois.
        
        Args:
            mois: Liste des numéros de mois
            events_state: État des événements
        
        Returns:
            DataFrame avec tous les mois
        """
        dfs = []
        
        for m in mois:
            df_mois = self.calculer_labels_mois(m, events_state)
            dfs.append(df_mois)
        
        if dfs:
            return pd.concat(dfs, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def combiner_labels_features(
        self,
        df_labels: pd.DataFrame,
        df_features: pd.DataFrame,
        mois: int
    ) -> pd.DataFrame:
        """
        Combine labels et features pour un mois.
        
        Pour chaque mois, on prend 3 semaines des voisins avant la dernière semaine
        (les 4 semaines des voisins sont prises avant la dernière semaine).
        
        Args:
            df_labels: DataFrame des labels
            df_features: DataFrame des features
            mois: Numéro du mois
        
        Returns:
            DataFrame combiné labels + features
        """
        # Filtrer labels pour ce mois
        labels_mois = df_labels[df_labels['mois'] == mois].copy()
        
        # Calculer semaines du mois
        semaine_debut = (mois - 1) * SEMAINES_PAR_MOIS + 1
        semaines_mois = list(range(semaine_debut, semaine_debut + SEMAINES_PAR_MOIS))
        
        # Pour correspondance avec features :
        # - 3 semaines précédentes pour voisins (avant dernière semaine)
        # - 4 semaines pour central (dernière semaine + 3 précédentes)
        semaines_features_central = semaines_mois  # 4 semaines
        semaines_features_voisins = list(range(semaine_debut - 3, semaine_debut))  # 3 semaines avant
        
        # Filtrer features pour ces semaines
        features_central = df_features[df_features['semaine'].isin(semaines_features_central)].copy()
        features_voisins = df_features[df_features['semaine'].isin(semaines_features_voisins)].copy()
        
        # Combiner avec labels
        result = labels_mois.copy()
        
        # Ajouter features central (agrégation par arrondissement)
        for arrondissement in labels_mois['arrondissement'].unique():
            features_arr = features_central[features_central['arrondissement'] == arrondissement]
            
            # Agréger features par arrondissement (moyenne pour proportions, somme pour sommes)
            for col in features_arr.columns:
                if col not in ['arrondissement', 'semaine']:
                    if 'alcool' in col or 'nuit' in col:
                        # Proportions : moyenne
                        valeur = features_arr[col].mean()
                    else:
                        # Sommes : somme
                        valeur = features_arr[col].sum()
                    
                    result.loc[result['arrondissement'] == arrondissement, f'feature_{col}'] = valeur
        
        # Ajouter features voisins (simplification : on prend les mêmes features pour tous les voisins)
        # En réalité, il faudrait identifier les voisins de chaque arrondissement
        for arrondissement in labels_mois['arrondissement'].unique():
            features_arr = features_voisins[features_voisins['arrondissement'] == arrondissement]
            
            for col in features_arr.columns:
                if col not in ['arrondissement', 'semaine']:
                    if 'alcool' in col or 'nuit' in col:
                        valeur = features_arr[col].mean()
                    else:
                        valeur = features_arr[col].sum()
                    
                    result.loc[result['arrondissement'] == arrondissement, f'voisin_{col}'] = valeur
        
        return result
    
    def save_labels(
        self,
        df_labels: pd.DataFrame,
        run_id: str,
        output_path: Optional[str] = None
    ) -> None:
        """
        Sauvegarde les labels au format pickle standardisé.
        
        Args:
            df_labels: DataFrame des labels
            run_id: Identifiant du run
            output_path: Chemin de sortie (si None, utilise data/intermediate/run_{run_id}/ml/labels.pkl)
        """
        if output_path is None:
            path = PathResolver.data_intermediate(f"run_{run_id}", "ml", "labels.pkl")
        else:
            from pathlib import Path
            path = Path(output_path)
        
        # Convertir DataFrame en dict pour pickle
        data_dict = {
            'data': df_labels.to_dict('records'),
            'columns': list(df_labels.columns),
            'index': df_labels.index.tolist()
        }
        
        save_pickle(
            data=data_dict,
            path=path,
            data_type="labels",
            description=f"Labels mensuels pour {len(df_labels)} lignes",
            run_id=run_id,
            schema_version="1.0"
        )
    
    @classmethod
    def load_labels(cls, run_id: str) -> pd.DataFrame:
        """
        Charge les labels depuis un fichier pickle.
        
        Args:
            run_id: Identifiant du run
        
        Returns:
            DataFrame des labels
        """
        from ..core.utils.pickle_utils import load_pickle
        
        path = PathResolver.data_intermediate(f"run_{run_id}", "ml", "labels.pkl")
        
        if not path.exists():
            raise FileNotFoundError(f"Fichier labels.pkl introuvable: {path}")
        
        data = load_pickle(path, expected_type="labels")
        
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
