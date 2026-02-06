"""
Code à copier-coller dans un notebook Python ou un script pour visualiser les données.

Usage:
    conda activate paris_risques
    python -c "exec(open('scripts/view_data_code.py').read())"
"""

import pickle
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Chemin vers les données (depuis le répertoire racine du projet)
script_dir = Path(__file__).parent
project_root = script_dir.parent
source_data_dir = project_root / "data" / "source_data"

# 1. Microzones
print("1. MICROZONES")
with open(source_data_dir / "microzones.pkl", 'rb') as f:
    microzones = pickle.load(f)
print(f"Shape: {microzones.shape}")
print(microzones[['microzone_id', 'arrondissement']].head(10))

# 2. Distances caserne → microzone
print("\n2. DISTANCES CASERNE → MICROZONE")
with open(source_data_dir / "distances_caserne_microzone.pkl", 'rb') as f:
    df_caserne = pickle.load(f)
print(f"Shape: {df_caserne.shape}")
print(df_caserne.head(20))

# 3. Distances microzone → hôpital
print("\n3. DISTANCES MICROZONE → HÔPITAL")
with open(source_data_dir / "distances_microzone_hopital.pkl", 'rb') as f:
    df_hopital = pickle.load(f)
print(f"Shape: {df_hopital.shape}")
print(df_hopital.head(20))

# 4. Locations
print("\n4. LOCATIONS CASERNES/HÔPITAUX")
with open(source_data_dir / "locations_casernes_hopitaux.pkl", 'rb') as f:
    df_locations = pickle.load(f)
print(f"Shape: {df_locations.shape}")
print(df_locations.head(30))

# 5. Limites
print("\n5. LIMITES MICROZONE → ARRONDISSEMENT")
with open(source_data_dir / "limites_microzone_arrondissement.pkl", 'rb') as f:
    limits = pickle.load(f)
print(f"Type: {type(limits)}, Nombre: {len(limits)}")
for i, (key, value) in enumerate(list(limits.items())[:20]):
    print(f"  {key}: {value}")
