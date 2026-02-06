"""
Script pour visualiser les premières lignes des DataFrames dans data/source_data/.
"""

import pickle
import pandas as pd
import geopandas as gpd
from pathlib import Path
import sys

# Ajouter le répertoire racine au path
script_dir = Path(__file__).parent
ROOT_DIR = script_dir.parent
sys.path.insert(0, str(ROOT_DIR))

source_data_dir = ROOT_DIR / "data" / "source_data"

print("=" * 80)
print("VISUALISATION DES DONNÉES PRÉ-CALCULÉES")
print("=" * 80)
print()

# Liste des fichiers à afficher
files_to_display = [
    "microzones.pkl",
    "distances_caserne_microzone.pkl",
    "distances_microzone_hopital.pkl",
    "locations_casernes_hopitaux.pkl",
    "limites_microzone_arrondissement.pkl"
]

for filename in files_to_display:
    filepath = source_data_dir / filename
    
    if not filepath.exists():
        print(f"❌ {filename}: Fichier non trouvé")
        print()
        continue
    
    print(f"📄 {filename}")
    print("-" * 80)
    
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        # Afficher le type et les infos de base
        print(f"Type: {type(data)}")
        
        if isinstance(data, pd.DataFrame):
            print(f"Shape: {data.shape} (lignes × colonnes)")
            print(f"Colonnes: {list(data.columns)}")
            print()
            print("Premières lignes:")
            # Filtrer seulement si la colonne 'type' existe
            if 'type' in data.columns:
                print(data[data['type']!='caserne'].head(10))
            else:
                print(data.head(10))
            
            # Si certaines colonnes contiennent des listes, afficher un exemple
            for col in data.columns:
                if data[col].dtype == 'object':
                    # Vérifier si c'est une liste
                    sample = data[col].iloc[0] if len(data) > 0 else None
                    if isinstance(sample, list):
                        print(f"\nExemple de {col} (première ligne): {sample[:10]}..." if len(sample) > 50 else f"\nExemple de {col} (première ligne): {sample}")
        
        elif isinstance(data, dict):
            print(f"Nombre de clés: {len(data)}")
            print(f"Clés (premières 50): {list(data.keys())[:50]}")
            print()
            # Afficher quelques exemples
            for i, (key, value) in enumerate(list(data.items())[:50]):
                print(f"  {key}: {value}")
            if len(data) > 50:
                print(f"  ... ({len(data) - 50} autres entrées)")
        
        elif isinstance(data, gpd.GeoDataFrame):
            print(f"Shape: {data.shape} (lignes × colonnes)")
            print(f"Colonnes: {list(data.columns)}")
            print()
            print("Premières lignes (sans géométrie):")
            # Afficher sans la colonne geometry pour la lisibilité
            display_cols = [col for col in data.columns if col != 'geometry']
            print(data[display_cols].head(50))
            print(f"\nGéométrie: {data.geometry.iloc[0].geom_type} (exemple)")
        
        else:
            print(f"Contenu (premiers éléments):")
            if hasattr(data, '__len__'):
                print(f"  Longueur: {len(data)}")
                if len(data) > 0:
                    print(f"  Premier élément: {data[0] if isinstance(data, (list, tuple)) else list(data.items())[0]}")
            else:
                print(f"  {data}")
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print()
