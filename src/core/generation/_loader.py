"""
Chargement des données nécessaires pour la génération de vecteurs.
Story 2.2.1 - Génération vecteurs journaliers
"""

import pickle
from pathlib import Path
from typing import Any, Dict

from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from ..utils.path_resolver import PathResolver

# Clés fichier (pluriel) → clés code (singulier)
_TYPE_KEY_NORMALIZE = {
    "agressions": INCIDENT_TYPE_AGRESSION,
    "incendies": INCIDENT_TYPE_INCENDIE,
    "accidents": INCIDENT_TYPE_ACCIDENT,
}


def load_base_intensities() -> Dict[str, Dict[str, float]]:
    """
    Charge les intensités de base depuis data/source_data.
    
    Returns:
        Dict[microzone_id, Dict[type_incident, float]]
    """
    path = PathResolver.data_source("vecteurs_statiques.pkl")
    
    if not path.exists():
        raise FileNotFoundError(f"Fichier vecteurs_statiques.pkl introuvable: {path}")
    
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    # Si format standardisé, extraire les données
    if isinstance(data, dict) and 'data' in data:
        data = data['data']
    
    # Convertir en format attendu
    intensities = {}
    # Structure attendue : Dict[microzone_id, Dict[type, float]]
    # Adapter selon la structure réelle des données
    if isinstance(data, dict):
        for mz_id, vectors in data.items():
            intensities[mz_id] = {}
            if isinstance(vectors, dict):
                for inc_type, vector in vectors.items():
                    # Clé normalisée : fichier "agressions" → code "agression"
                    key = _TYPE_KEY_NORMALIZE.get(inc_type, inc_type)
                    if hasattr(vector, 'total'):
                        intensities[mz_id][key] = float(vector.total())
                    elif isinstance(vector, (list, tuple)) and len(vector) == 3:
                        intensities[mz_id][key] = float(sum(vector))
                    else:
                        intensities[mz_id][key] = 1.0
    
    return intensities


def load_matrices_for_generation() -> Dict[str, Any]:
    """
    Charge toutes les matrices nécessaires pour la génération.
    
    Returns:
        Dictionnaire avec matrices_intra_type, matrices_inter_type, matrices_voisin, matrices_saisonnalite
    """
    from ..probability._loader import load_matrices_for_probability
    
    source_dir = PathResolver.data_source("")
    return load_matrices_for_probability(source_dir)
