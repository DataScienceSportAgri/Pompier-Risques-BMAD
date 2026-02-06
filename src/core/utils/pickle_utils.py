"""
Helpers pour sauvegarde/chargement pickle avec format standardisé.
Story 2.1.4 - Système centralisé de résolution de chemins

Format pickle standardisé avec métadonnées, version, et structure cohérente.
"""

import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .path_resolver import PathResolver


# Version du format pickle standardisé
PICKLE_FORMAT_VERSION = "1.0"


def create_pickle_data(
    data: Any,
    data_type: str,
    description: str = "",
    run_id: Optional[str] = None,
    schema_version: Optional[str] = None,
    **extra_metadata: Any
) -> Dict[str, Any]:
    """
    Crée une structure pickle standardisée avec métadonnées.
    
    Structure standardisée :
    {
        'data': ...,  # Données réelles
        'metadata': {
            'version': '1.0',        # Version format pickle
            'created_at': datetime,  # Timestamp création
            'run_id': str,          # ID run (si applicable)
            'description': str,     # Description courte
            'type': str,            # Type données (ex: "vectors", "congestion")
            'schema_version': str   # Version schéma (optionnel)
            ...extra_metadata      # Métadonnées supplémentaires
        }
    }
    
    Args:
        data: Données à encapsuler
        data_type: Type des données (ex: "vectors", "congestion", "events")
        description: Description courte des données
        run_id: ID de la run (si applicable)
        schema_version: Version du schéma des données (optionnel)
        **extra_metadata: Métadonnées supplémentaires
    
    Returns:
        Dictionnaire avec structure standardisée
    """
    metadata = {
        'version': PICKLE_FORMAT_VERSION,
        'created_at': datetime.now(),
        'type': data_type,
        'description': description,
        **extra_metadata
    }
    
    if run_id is not None:
        metadata['run_id'] = run_id
    
    if schema_version is not None:
        metadata['schema_version'] = schema_version
    
    return {
        'data': data,
        'metadata': metadata
    }


def save_pickle(
    data: Any,
    path: Path,
    data_type: str,
    description: str = "",
    run_id: Optional[str] = None,
    schema_version: Optional[str] = None,
    **extra_metadata: Any
) -> None:
    """
    Sauvegarde des données au format pickle standardisé.
    
    Args:
        data: Données à sauvegarder
        path: Chemin de destination (peut être relatif ou absolu)
        data_type: Type des données
        description: Description courte
        run_id: ID de la run (si applicable)
        schema_version: Version du schéma (optionnel)
        **extra_metadata: Métadonnées supplémentaires
    
    Raises:
        IOError: Si la sauvegarde échoue
    """
    # Créer la structure standardisée
    pickle_data = create_pickle_data(
        data=data,
        data_type=data_type,
        description=description,
        run_id=run_id,
        schema_version=schema_version,
        **extra_metadata
    )
    
    # Résoudre le chemin si nécessaire
    if not path.is_absolute():
        path = PathResolver.resolve(path)
    
    # Créer les dossiers parents si nécessaire
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'wb') as f:
            pickle.dump(pickle_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise IOError(f"Erreur lors de la sauvegarde pickle: {e}") from e


def load_pickle(
    path: Path,
    expected_type: Optional[str] = None,
    expected_version: Optional[str] = None
) -> Any:
    """
    Charge des données depuis un fichier pickle standardisé.
    
    Args:
        path: Chemin du fichier (peut être relatif ou absolu)
        expected_type: Type de données attendu (vérification optionnelle)
        expected_version: Version du format attendue (vérification optionnelle)
    
    Returns:
        Données chargées (extrait de la structure standardisée)
    
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        IOError: Si le chargement échoue
        ValueError: Si le format n'est pas standardisé ou si le type/version ne correspond pas
    """
    # Résoudre le chemin si nécessaire
    if not path.is_absolute():
        path = PathResolver.resolve(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Fichier pickle introuvable: {path}")
    
    try:
        with open(path, 'rb') as f:
            pickle_data = pickle.load(f)
    except Exception as e:
        raise IOError(f"Erreur lors du chargement pickle: {e}") from e
    
    # Format legacy (DataFrame, etc.) : retourner tel quel pour compatibilité pré-calculs Story 1.2
    if not isinstance(pickle_data, dict):
        return pickle_data
    
    if 'data' not in pickle_data or 'metadata' not in pickle_data:
        raise ValueError(
            "Format pickle non standardisé: clés 'data' et 'metadata' requises"
        )
    
    metadata = pickle_data['metadata']
    
    # Vérifications optionnelles
    if expected_type is not None:
        actual_type = metadata.get('type')
        if actual_type != expected_type:
            raise ValueError(
                f"Type de données inattendu: attendu '{expected_type}', "
                f"reçu '{actual_type}'"
            )
    
    if expected_version is not None:
        actual_version = metadata.get('version')
        if actual_version != expected_version:
            raise ValueError(
                f"Version du format inattendue: attendu '{expected_version}', "
                f"reçu '{actual_version}'"
            )
    
    return pickle_data['data']


def get_pickle_metadata(path: Path) -> Dict[str, Any]:
    """
    Récupère uniquement les métadonnées d'un fichier pickle standardisé.
    
    Args:
        path: Chemin du fichier (peut être relatif ou absolu)
    
    Returns:
        Dictionnaire de métadonnées
    
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        IOError: Si le chargement échoue
        ValueError: Si le format n'est pas standardisé
    """
    # Résoudre le chemin si nécessaire
    if not path.is_absolute():
        path = PathResolver.resolve(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Fichier pickle introuvable: {path}")
    
    try:
        with open(path, 'rb') as f:
            pickle_data = pickle.load(f)
    except Exception as e:
        raise IOError(f"Erreur lors du chargement pickle: {e}") from e
    
    # Vérifier la structure standardisée
    if not isinstance(pickle_data, dict) or 'metadata' not in pickle_data:
        raise ValueError("Format pickle non standardisé: métadonnées introuvables")
    
    return pickle_data['metadata']
