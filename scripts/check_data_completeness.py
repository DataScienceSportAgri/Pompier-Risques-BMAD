"""
Script pour vérifier la complétude des données de distances.
"""

import pickle
import pandas as pd
from pathlib import Path

# Chemin vers les données (depuis le répertoire racine du projet)
script_dir = Path(__file__).parent
project_root = script_dir.parent  # Remonter d'un niveau depuis scripts/
source_data_dir = project_root / "data" / "source_data"

print("=" * 80)
print("VÉRIFICATION COMPLÉTUDE DES DONNÉES")
print("=" * 80)
print(f"📁 Chemin des données: {source_data_dir}")
print(f"📁 Chemin existe: {source_data_dir.exists()}")
print()

# Charger les microzones
with open(source_data_dir / "microzones.pkl", 'rb') as f:
    microzones = pickle.load(f)
nb_microzones = len(microzones)
print(f"📊 Nombre de microzones: {nb_microzones}")

# Charger les distances caserne → microzone
with open(source_data_dir / "distances_caserne_microzone.pkl", 'rb') as f:
    df_caserne = pickle.load(f)

print(f"\n1️⃣  DISTANCES CASERNE → MICROZONE")
print(f"   Nombre de lignes: {len(df_caserne)}")
nb_casernes = df_caserne['caserne'].nunique()
print(f"   Nombre de casernes uniques: {nb_casernes}")
print(f"   Nombre de microzones uniques: {df_caserne['microzone'].nunique()}")
expected = nb_casernes * nb_microzones
print(f"   Attendu: {nb_casernes} × {nb_microzones} = {expected}")
if len(df_caserne) == expected:
    print(f"   ✅ Toutes les combinaisons sont présentes")
else:
    print(f"   ⚠️  Manque {expected - len(df_caserne)} lignes")
    
# Vérifier microzones traversées
print(f"\n   Vérification microzones traversées:")
nb_vides = df_caserne['microzones_traversees'].apply(lambda x: len(x) if isinstance(x, list) else 0).eq(0).sum()
nb_insuffisant = df_caserne['microzones_traversees'].apply(lambda x: len(x) if isinstance(x, list) else 0).lt(2).sum()
print(f"   - Lignes avec 0 microzone traversée: {nb_vides}")
print(f"   - Lignes avec < 2 microzones traversées: {nb_insuffisant}")
if nb_insuffisant > 0:
    print(f"   ⚠️  {nb_insuffisant} lignes ont moins de 2 microzones traversées")
else:
    print(f"   ✅ Toutes les lignes ont au moins 2 microzones traversées")

# Charger les distances microzone → hôpital
with open(source_data_dir / "distances_microzone_hopital.pkl", 'rb') as f:
    df_hopital = pickle.load(f)

print(f"\n2️⃣  DISTANCES MICROZONE → HÔPITAL")
print(f"   Nombre de lignes: {len(df_hopital)}")
nb_hopitaux = df_hopital['hopital'].nunique()
print(f"   Nombre d'hôpitaux uniques: {nb_hopitaux}")
print(f"   Nombre de microzones uniques: {df_hopital['microzone'].nunique()}")
expected = nb_hopitaux * nb_microzones
print(f"   Attendu: {nb_hopitaux} × {nb_microzones} = {expected}")
if len(df_hopital) == expected:
    print(f"   ✅ Toutes les combinaisons sont présentes")
else:
    print(f"   ⚠️  Manque {expected - len(df_hopital)} lignes")
    
# Vérifier microzones traversées
print(f"\n   Vérification microzones traversées:")
nb_vides = df_hopital['microzones_traversees'].apply(lambda x: len(x) if isinstance(x, list) else 0).eq(0).sum()
nb_insuffisant = df_hopital['microzones_traversees'].apply(lambda x: len(x) if isinstance(x, list) else 0).lt(2).sum()
print(f"   - Lignes avec 0 microzone traversée: {nb_vides}")
print(f"   - Lignes avec < 2 microzones traversées: {nb_insuffisant}")
if nb_insuffisant > 0:
    print(f"   ⚠️  {nb_insuffisant} lignes ont moins de 2 microzones traversées")
else:
    print(f"   ✅ Toutes les lignes ont au moins 2 microzones traversées")

print("\n" + "=" * 80)
print("RECOMMANDATION:")
if nb_insuffisant > 0 or len(df_caserne) < expected or len(df_hopital) < expected:
    print("⚠️  Il est recommandé de relancer precompute_distances.py pour")
    print("   régénérer les données avec les améliorations (complétion automatique).")
else:
    print("✅ Les données existantes sont complètes. Pas besoin de régénération.")
print("=" * 80)
