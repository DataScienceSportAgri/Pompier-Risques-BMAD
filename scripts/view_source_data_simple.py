"""
Script simple pour visualiser les premières lignes des DataFrames.
À exécuter dans l'environnement Conda: conda activate paris_risques
"""

import pickle
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Chemin vers les données (depuis le répertoire racine du projet)
# Le script peut être exécuté depuis n'importe où
script_dir = Path(__file__).parent
project_root = script_dir.parent  # Remonter d'un niveau depuis scripts/
source_data_dir = project_root / "data" / "source_data"

print("=" * 80)
print("VISUALISATION DES DONNÉES PRÉ-CALCULÉES")
print("=" * 80)
print(f"📁 Chemin des données: {source_data_dir}")
print(f"📁 Chemin existe: {source_data_dir.exists()}")
print()

# 1. Microzones
print("1️⃣  MICROZONES (microzones.pkl)")
print("-" * 80)
try:
    with open(source_data_dir / "microzones.pkl", 'rb') as f:
        microzones = pickle.load(f)
    print(f"Type: {type(microzones)}")
    print(f"Shape: {microzones.shape}")
    print(f"Colonnes: {list(microzones.columns)}")
    print("\nPremières lignes (sans géométrie):")
    display_cols = [col for col in microzones.columns if col != 'geometry']
    print(microzones[display_cols].head(10))
    print()
except Exception as e:
    print(f"❌ Erreur: {e}")
print()

# 2. Distances caserne → microzone
print("2️⃣  DISTANCES CASERNE → MICROZONE (distances_caserne_microzone.pkl)")
print("-" * 80)
try:
    with open(source_data_dir / "distances_caserne_microzone.pkl", 'rb') as f:
        df_caserne = pickle.load(f)
    print(f"Type: {type(df_caserne)}")
    print(f"Shape: {df_caserne.shape} (lignes × colonnes)")
    print(f"Colonnes: {list(df_caserne.columns)}")
    print("\nPremières lignes:")
    print(df_caserne.head(10))
    print(f"\nExemple microzones_traversees (première ligne):")
    if len(df_caserne) > 0 and 'microzones_traversees' in df_caserne.columns:
        first_traversed = df_caserne['microzones_traversees'].iloc[0]
        print(f"  {first_traversed}")
    print()
except Exception as e:
    print(f"❌ Erreur: {e}")
print()

# 3. Distances microzone → hôpital
print("3️⃣  DISTANCES MICROZONE → HÔPITAL (distances_microzone_hopital.pkl)")
print("-" * 80)
try:
    with open(source_data_dir / "distances_microzone_hopital.pkl", 'rb') as f:
        df_hopital = pickle.load(f)
    print(f"Type: {type(df_hopital)}")
    print(f"Shape: {df_hopital.shape} (lignes × colonnes)")
    print(f"Colonnes: {list(df_hopital.columns)}")
    print("\nPremières lignes:")
    print(df_hopital.head(10))
    print(f"\nExemple microzones_traversees (première ligne):")
    if len(df_hopital) > 0 and 'microzones_traversees' in df_hopital.columns:
        first_traversed = df_hopital['microzones_traversees'].iloc[0]
        print(f"  {first_traversed}")
    print()
except Exception as e:
    print(f"❌ Erreur: {e}")
print()

# 4. Locations casernes/hôpitaux
print("4️⃣  LOCATIONS CASERNES/HÔPITAUX (locations_casernes_hopitaux.pkl)")
print("-" * 80)
try:
    with open(source_data_dir / "locations_casernes_hopitaux.pkl", 'rb') as f:
        df_locations = pickle.load(f)
    print(f"Type: {type(df_locations)}")
    print(f"Shape: {df_locations.shape} (lignes × colonnes)")
    print(f"Colonnes: {list(df_locations.columns)}")
    print("\nPremières lignes:")
    print(df_locations.head(20))
    print(f"\nRépartition par type:")
    if 'type' in df_locations.columns:
        print(df_locations['type'].value_counts())
    print()
except Exception as e:
    print(f"❌ Erreur: {e}")
print()

# 5. Limites microzone → arrondissement
print("5️⃣  LIMITES MICROZONE → ARRONDISSEMENT (limites_microzone_arrondissement.pkl)")
print("-" * 80)
try:
    with open(source_data_dir / "limites_microzone_arrondissement.pkl", 'rb') as f:
        limits = pickle.load(f)
    print(f"Type: {type(limits)}")
    if isinstance(limits, dict):
        print(f"Nombre d'entrées: {len(limits)}")
        print("\nPremières entrées:")
        for i, (key, value) in enumerate(list(limits.items())[:10]):
            print(f"  {key}: {value}")
        if len(limits) > 10:
            print(f"  ... ({len(limits) - 10} autres)")
    else:
        print(f"Contenu: {limits}")
    print()
except Exception as e:
    print(f"❌ Erreur: {e}")
print()

print("=" * 80)
print("FIN DE LA VISUALISATION")
print("=" * 80)
