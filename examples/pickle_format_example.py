"""
Exemple d'utilisation du format pickle standardisé.
Story 2.1.4 - Système centralisé de résolution de chemins
"""

from datetime import datetime

from src.core.utils.path_resolver import PathResolver
from src.core.utils.pickle_utils import (
    create_pickle_data,
    get_pickle_metadata,
    load_pickle,
    save_pickle,
)


def example_save_vectors():
    """Exemple : Sauvegarde de vecteurs avec format standardisé."""
    # Données à sauvegarder
    vectors_data = {
        "MZ_11_01": {
            0: {"incendie": [1, 2, 3], "accident": [0, 1, 2]},
            1: {"incendie": [0, 1, 1], "accident": [1, 0, 1]}
        }
    }
    
    # Sauvegarde avec format standardisé
    path = PathResolver.data_intermediate("run_001", "generation", "vecteurs.pkl")
    
    save_pickle(
        data=vectors_data,
        path=path,
        data_type="vectors",
        description="Vecteurs journaliers pour 100 microzones",
        run_id="001",
        schema_version="1.0"
    )
    
    print(f"Vecteurs sauvegardés dans : {path}")


def example_load_vectors():
    """Exemple : Chargement de vecteurs avec validation."""
    path = PathResolver.data_intermediate("run_001", "generation", "vecteurs.pkl")
    
    # Chargement avec validation du type
    vectors_data = load_pickle(
        path=path,
        expected_type="vectors",
        expected_version="1.0"
    )
    
    print(f"Vecteurs chargés : {len(vectors_data)} microzones")
    return vectors_data


def example_get_metadata():
    """Exemple : Récupération des métadonnées uniquement."""
    path = PathResolver.data_intermediate("run_001", "generation", "vecteurs.pkl")
    
    metadata = get_pickle_metadata(path)
    
    print("Métadonnées :")
    print(f"  Type : {metadata['type']}")
    print(f"  Version : {metadata['version']}")
    print(f"  Créé le : {metadata['created_at']}")
    print(f"  Description : {metadata['description']}")
    if 'run_id' in metadata:
        print(f"  Run ID : {metadata['run_id']}")


def example_create_pickle_data():
    """Exemple : Création de structure pickle sans sauvegarde."""
    data = {"key": "value"}
    
    pickle_data = create_pickle_data(
        data=data,
        data_type="test",
        description="Données de test",
        run_id="001",
        custom_field="custom_value"  # Métadonnée supplémentaire
    )
    
    print("Structure pickle créée :")
    print(f"  Clés : {list(pickle_data.keys())}")
    print(f"  Métadonnées : {list(pickle_data['metadata'].keys())}")
    
    return pickle_data


def example_save_simulation_state():
    """Exemple : Sauvegarde d'un état de simulation."""
    # Simulation d'un état (en réalité, ce serait un SimulationState)
    state_data = {
        "current_day": 150,
        "vectors": {},
        "events": []
    }
    
    path = PathResolver.resolve("data", "safe_state", "run_001_day_150.pkl")
    
    save_pickle(
        data=state_data,
        path=path,
        data_type="simulation_state",
        description="État de simulation jour 150",
        run_id="001",
        schema_version="2.0"
    )
    
    print(f"État sauvegardé dans : {path}")


if __name__ == "__main__":
    print("=== Exemples d'utilisation du format pickle standardisé ===\n")
    
    print("1. Création de structure pickle :")
    example_create_pickle_data()
    print()
    
    print("2. Sauvegarde de vecteurs :")
    try:
        example_save_vectors()
    except Exception as e:
        print(f"  Erreur (normal si dossier n'existe pas) : {e}")
    print()
    
    print("3. Chargement de vecteurs :")
    try:
        example_load_vectors()
    except FileNotFoundError:
        print("  Fichier non trouvé (normal si pas encore créé)")
    except Exception as e:
        print(f"  Erreur : {e}")
    print()
    
    print("4. Récupération de métadonnées :")
    try:
        example_get_metadata()
    except FileNotFoundError:
        print("  Fichier non trouvé (normal si pas encore créé)")
    except Exception as e:
        print(f"  Erreur : {e}")
    print()
    
    print("5. Sauvegarde d'état de simulation :")
    try:
        example_save_simulation_state()
    except Exception as e:
        print(f"  Erreur (normal si dossier n'existe pas) : {e}")
