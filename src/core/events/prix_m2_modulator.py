"""
Modulateur de probabilités basé sur le prix m².
Story 2.2.8 - Événements positifs et règle prix m²
"""

import pickle
from typing import Dict, Optional

import numpy as np
import pandas as pd

from ..data.constants import INCIDENT_TYPE_AGRESSION
from ..utils.path_resolver import PathResolver


def _normalize_prix_m2_data(data: object) -> Dict[str, float]:
    """
    Normalise les données prix m² en Dict[microzone_id, float].
    Accepte DataFrame (colonnes microzone_id, prix_m2) ou dict brut.
    """
    if isinstance(data, pd.DataFrame):
        if "microzone_id" not in data.columns or "prix_m2" not in data.columns:
            return {}
        return {
            str(row["microzone_id"]): float(row["prix_m2"])
            for _, row in data.iterrows()
            if pd.notna(row.get("prix_m2"))
        }
    if isinstance(data, dict):
        if "data" in data and "metadata" in data:
            data = data["data"]
        if isinstance(data, dict):
            out = {}
            for k, v in data.items():
                if v is None or (isinstance(v, str) and not v.strip()):
                    continue
                try:
                    out[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue
            return out
    return {}


class PrixM2Modulator:
    """
    Modulateur de probabilités basé sur le prix m².
    
    Applique la règle prix m² :
    - Modulation probabilités agressions : prob_agression_base / facteur_prix_m2
    - Diminution probabilités Détérioration/Crise si prix m² élevé
    """
    
    def __init__(self, prix_m2_data: Optional[Dict[str, float]] = None):
        """
        Initialise le modulateur prix m².
        
        Args:
            prix_m2_data: Données prix m² par microzone (si None, chargées depuis fichier)
        """
        if prix_m2_data is None:
            prix_m2_data = self.load_prix_m2()
        
        self.prix_m2_data = prix_m2_data

        # Calculer prix m² moyen Paris (valeurs numériques uniquement)
        if prix_m2_data:
            vals = [float(v) for v in prix_m2_data.values() if v is not None]
            self.prix_m2_moyen_paris = float(np.mean(vals)) if vals else 1.0
        else:
            self.prix_m2_moyen_paris = 1.0  # Valeur par défaut
    
    @classmethod
    def load_prix_m2(cls) -> Dict[str, float]:
        """
        Charge les données prix m² depuis le fichier pickle.
        
        Returns:
            Dictionnaire {microzone_id: prix_m2}
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        prix_m2_path = PathResolver.data_source("prix_m2.pkl")

        if not prix_m2_path.exists():
            raise FileNotFoundError(
                f"Fichier prix m² introuvable: {prix_m2_path}"
            )
        
        try:
            with open(prix_m2_path, "rb") as f:
                data = pickle.load(f)
            return _normalize_prix_m2_data(data)
        except Exception as e:
            raise IOError(f"Erreur lors du chargement prix m²: {e}") from e
    
    def get_facteur_prix_m2(self, microzone_id: str) -> float:
        """
        Calcule le facteur prix m² pour une microzone.
        
        Formule : facteur_prix_m2 = prix_m2_microzone / prix_m2_moyen_paris
        
        Args:
            microzone_id: Identifiant de la microzone
        
        Returns:
            Facteur prix m² (1.0 si données non disponibles)
        """
        prix_m2_microzone = self.prix_m2_data.get(microzone_id)
        
        if prix_m2_microzone is None or self.prix_m2_moyen_paris == 0:
            return 1.0
        
        return prix_m2_microzone / self.prix_m2_moyen_paris
    
    def moduler_probabilite_agression(
        self,
        microzone_id: str,
        prob_agression_base: float
    ) -> float:
        """
        Module la probabilité d'agression selon le prix m².
        
        Formule : prob_agression_modulée = prob_agression_base / facteur_prix_m2
        
        Args:
            microzone_id: Identifiant de la microzone
            prob_agression_base: Probabilité de base
        
        Returns:
            Probabilité modulée
        """
        facteur = self.get_facteur_prix_m2(microzone_id)
        
        if facteur == 0:
            return prob_agression_base
        
        return prob_agression_base / facteur
    
    def moduler_probabilites_regimes(
        self,
        microzone_id: str,
        prob_deterioration: float,
        prob_crise: float
    ) -> tuple[float, float]:
        """
        Module les probabilités de régimes (Détérioration/Crise) selon le prix m².
        
        Si facteur_prix_m2 > 1.2 (quartier riche) :
        - prob_deterioration *= 0.8
        - prob_crise *= 0.7
        
        Args:
            microzone_id: Identifiant de la microzone
            prob_deterioration: Probabilité de détérioration de base
            prob_crise: Probabilité de crise de base
        
        Returns:
            Tuple (prob_deterioration_modulée, prob_crise_modulée)
        """
        facteur = self.get_facteur_prix_m2(microzone_id)
        
        if facteur > 1.2:  # Quartier riche
            prob_deterioration_mod = prob_deterioration * 0.8
            prob_crise_mod = prob_crise * 0.7
        else:
            prob_deterioration_mod = prob_deterioration
            prob_crise_mod = prob_crise
        
        return prob_deterioration_mod, prob_crise_mod
    
    def moduler_intensite(
        self,
        microzone_id: str,
        type_incident: str,
        intensite_base: float
    ) -> float:
        """
        Module l'intensité selon le prix m² (pour agressions principalement).
        
        Args:
            microzone_id: Identifiant de la microzone
            type_incident: Type d'incident
            intensite_base: Intensité de base
        
        Returns:
            Intensité modulée
        """
        if type_incident == INCIDENT_TYPE_AGRESSION:
            # Pour agressions, utiliser modulation probabilité
            # On convertit probabilité en intensité (approximation)
            facteur = self.get_facteur_prix_m2(microzone_id)
            if facteur > 0:
                return intensite_base / facteur
        
        return intensite_base
