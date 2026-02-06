"""
Script pour vérifier que les données scrapées depuis internet sont bien sauvegardées.
"""

import pickle
import pandas as pd
from pathlib import Path

# Chemin vers les données (depuis le répertoire racine du projet)
script_dir = Path(__file__).parent
project_root = script_dir.parent
source_data_dir = project_root / "data" / "source_data"

print("=" * 80)
print("VÉRIFICATION DES DONNÉES SCRAPÉES DEPUIS INTERNET")
print("=" * 80)
print(f"📁 Chemin des données: {source_data_dir}")
print()

# Liste des fichiers de données scrapées
scraped_files = {
    "prix_m2.pkl": "Prix m² par arrondissement/IRIS",
    "chomage.pkl": "Taux de chômage par arrondissement/IRIS",
    "delinquance.pkl": "Indice de délinquance par arrondissement/IRIS"
}

print("📊 DONNÉES SCRAPÉES SAUVEGARDÉES:")
print("-" * 80)

for filename, description in scraped_files.items():
    filepath = source_data_dir / filename
    
    if filepath.exists():
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            print(f"\n✅ {filename}")
            print(f"   Description: {description}")
            print(f"   Type: {type(data)}")
            
            if isinstance(data, pd.DataFrame):
                print(f"   Shape: {data.shape} (lignes × colonnes)")
                print(f"   Colonnes: {list(data.columns)}")
                print(f"\n   Premières lignes:")
                print(data.head(10))
            else:
                print(f"   Contenu: {data}")
                
        except Exception as e:
            print(f"\n❌ {filename}: Erreur lors du chargement: {e}")
    else:
        print(f"\n⚠️  {filename}: Fichier non trouvé")
        print(f"   → Les données seront générées lors du prochain run de precompute_vectors_static")

print("\n" + "=" * 80)
print("RÉSUMÉ:")
print("=" * 80)
print("Les données scrapées depuis internet sont sauvegardées dans:")
print(f"  {source_data_dir}/")
print("\nFichiers créés par precompute_vectors_static.py:")
print("  - prix_m2.pkl (données scrapées ou générées)")
print("  - chomage.pkl (données scrapées ou générées)")
print("  - delinquance.pkl (données scrapées ou générées)")
print("  - vecteurs_statiques.pkl (calculés à partir des données scrapées)")
print("  - congestion_statique.pkl (calculée à partir des données scrapées)")
print("=" * 80)
