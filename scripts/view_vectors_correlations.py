"""
Script pour visualiser les correspondances entre données socio-économiques
(prix m², chômage, délinquance) et vecteurs statiques par microzone.
"""

import pickle
import pandas as pd
from pathlib import Path

# Chemin vers les données (depuis le répertoire racine du projet)
script_dir = Path(__file__).parent
project_root = script_dir.parent
source_data_dir = project_root / "data" / "source_data"

print("=" * 100)
print("CORRÉLATIONS ENTRE DONNÉES SOCIO-ÉCONOMIQUES ET VECTEURS STATIQUES")
print("=" * 100)
print(f"📁 Chemin des données: {source_data_dir}")
print()

# Charger les microzones pour avoir les arrondissements
try:
    with open(source_data_dir / "microzones.pkl", 'rb') as f:
        microzones = pickle.load(f)
    print(f"✅ {len(microzones)} microzones chargées")
except Exception as e:
    print(f"❌ Erreur chargement microzones: {e}")
    microzones = None

# Charger les données socio-économiques
print("\n" + "=" * 100)
print("1️⃣  DONNÉES SOCIO-ÉCONOMIQUES")
print("=" * 100)

prix_m2 = None
chomage = None
delinquance = None

# Prix m²
try:
    with open(source_data_dir / "prix_m2.pkl", 'rb') as f:
        prix_m2 = pickle.load(f)
    print(f"\n✅ Prix m² chargé: {len(prix_m2)} entrées")
    print(f"   Colonnes: {list(prix_m2.columns)}")
    if isinstance(prix_m2, pd.DataFrame):
        print(f"\n   Aperçu:")
        print(prix_m2.head(10))
except Exception as e:
    print(f"\n⚠️  Prix m² non trouvé: {e}")

# Chômage
try:
    with open(source_data_dir / "chomage.pkl", 'rb') as f:
        chomage = pickle.load(f)
    print(f"\n✅ Chômage chargé: {len(chomage)} entrées")
    print(f"   Colonnes: {list(chomage.columns)}")
    if isinstance(chomage, pd.DataFrame):
        print(f"\n   Aperçu:")
        print(chomage.head(10))
except Exception as e:
    print(f"\n⚠️  Chômage non trouvé: {e}")

# Délinquance
try:
    with open(source_data_dir / "delinquance.pkl", 'rb') as f:
        delinquance = pickle.load(f)
    print(f"\n✅ Délinquance chargée: {len(delinquance)} entrées")
    print(f"   Colonnes: {list(delinquance.columns)}")
    if isinstance(delinquance, pd.DataFrame):
        print(f"\n   Aperçu:")
        print(delinquance.head(10))
except Exception as e:
    print(f"\n⚠️  Délinquance non trouvée: {e}")

# Charger les vecteurs statiques
print("\n" + "=" * 100)
print("2️⃣  VECTEURS STATIQUES")
print("=" * 100)

vecteurs_statiques = None
try:
    with open(source_data_dir / "vecteurs_statiques.pkl", 'rb') as f:
        vecteurs_statiques = pickle.load(f)
    print(f"\n✅ Vecteurs statiques chargés: {len(vecteurs_statiques)} microzones")
except Exception as e:
    print(f"\n⚠️  Vecteurs statiques non trouvés: {e}")

# Créer un tableau comparatif par microzone
if microzones is not None and vecteurs_statiques is not None:
    print("\n" + "=" * 100)
    print("3️⃣  TABLEAU COMPARATIF PAR MICROZONE (10 premiers exemples)")
    print("=" * 100)
    
    comparison_data = []
    
    for idx, mz in microzones.head(10).iterrows():
        microzone_id = mz['microzone_id']
        arrondissement = int(mz['arrondissement'])
        
        # Récupérer données socio-économiques
        prix_m2_val = None
        chomage_val = None
        delinquance_val = None
        
        if prix_m2 is not None and isinstance(prix_m2, pd.DataFrame):
            if 'microzone_id' in prix_m2.columns:
                filtered = prix_m2[prix_m2['microzone_id'] == microzone_id]
                if len(filtered) > 0 and 'prix_m2' in filtered.columns:
                    prix_m2_val = filtered.iloc[0]['prix_m2']
            elif 'arrondissement' in prix_m2.columns:
                filtered = prix_m2[prix_m2['arrondissement'] == arrondissement]
                if len(filtered) > 0 and 'prix_m2' in filtered.columns:
                    prix_m2_val = filtered.iloc[0]['prix_m2']
        
        if chomage is not None and isinstance(chomage, pd.DataFrame):
            if 'microzone_id' in chomage.columns:
                filtered = chomage[chomage['microzone_id'] == microzone_id]
                if len(filtered) > 0 and 'taux_chomage' in filtered.columns:
                    chomage_val = filtered.iloc[0]['taux_chomage']
            elif 'arrondissement' in chomage.columns:
                filtered = chomage[chomage['arrondissement'] == arrondissement]
                if len(filtered) > 0 and 'taux_chomage' in filtered.columns:
                    chomage_val = filtered.iloc[0]['taux_chomage']
        
        if delinquance is not None and isinstance(delinquance, pd.DataFrame):
            if 'microzone_id' in delinquance.columns:
                filtered = delinquance[delinquance['microzone_id'] == microzone_id]
                if len(filtered) > 0 and 'indice_delinquance' in filtered.columns:
                    delinquance_val = filtered.iloc[0]['indice_delinquance']
            elif 'arrondissement' in delinquance.columns:
                filtered = delinquance[delinquance['arrondissement'] == arrondissement]
                if len(filtered) > 0 and 'indice_delinquance' in filtered.columns:
                    delinquance_val = filtered.iloc[0]['indice_delinquance']
        
        # Récupérer vecteurs statiques
        vecteurs_mz = vecteurs_statiques.get(microzone_id, {})
        agressions = vecteurs_mz.get('agressions', (0, 0, 0))
        incendies = vecteurs_mz.get('incendies', (0, 0, 0))
        accidents = vecteurs_mz.get('accidents', (0, 0, 0))
        
        comparison_data.append({
            'Microzone': microzone_id,
            'Arrondissement': arrondissement,
            'Prix m² (€)': f"{prix_m2_val:.0f}" if prix_m2_val else "N/A",
            'Chômage (%)': f"{chomage_val:.1f}" if chomage_val else "N/A",
            'Délinquance': f"{delinquance_val:.0f}" if delinquance_val else "N/A",
            'Agressions (b,m,g)': f"{agressions[0]},{agressions[1]},{agressions[2]}",
            'Incendies (b,m,g)': f"{incendies[0]},{incendies[1]},{incendies[2]}",
            'Accidents (b,m,g)': f"{accidents[0]},{accidents[1]},{accidents[2]}"
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    print("\n")
    print(df_comparison.to_string(index=False))
    
    # Analyse des corrélations
    print("\n" + "=" * 100)
    print("4️⃣  ANALYSE DES CORRÉLATIONS")
    print("=" * 100)
    
    # Calculer quelques statistiques
    if prix_m2 is not None and isinstance(prix_m2, pd.DataFrame) and 'prix_m2' in prix_m2.columns:
        print(f"\n📊 Prix m²:")
        print(f"   Min: {prix_m2['prix_m2'].min():.0f} €/m²")
        print(f"   Max: {prix_m2['prix_m2'].max():.0f} €/m²")
        print(f"   Moyenne: {prix_m2['prix_m2'].mean():.0f} €/m²")
    
    if chomage is not None and isinstance(chomage, pd.DataFrame) and 'taux_chomage' in chomage.columns:
        print(f"\n📊 Chômage:")
        print(f"   Min: {chomage['taux_chomage'].min():.1f} %")
        print(f"   Max: {chomage['taux_chomage'].max():.1f} %")
        print(f"   Moyenne: {chomage['taux_chomage'].mean():.1f} %")
    
    if delinquance is not None and isinstance(delinquance, pd.DataFrame) and 'indice_delinquance' in delinquance.columns:
        print(f"\n📊 Délinquance:")
        print(f"   Min: {delinquance['indice_delinquance'].min():.0f}")
        print(f"   Max: {delinquance['indice_delinquance'].max():.0f}")
        print(f"   Moyenne: {delinquance['indice_delinquance'].mean():.0f}")
    
    # Analyser les vecteurs statiques
    print(f"\n📊 Vecteurs statiques (toutes microzones):")
    total_agressions = sum(sum(v.get('agressions', (0, 0, 0))) for v in vecteurs_statiques.values())
    total_incendies = sum(sum(v.get('incendies', (0, 0, 0))) for v in vecteurs_statiques.values())
    total_accidents = sum(sum(v.get('accidents', (0, 0, 0))) for v in vecteurs_statiques.values())
    
    print(f"   Total agressions (b+m+g): {total_agressions}")
    print(f"   Total incendies (b+m+g): {total_incendies}")
    print(f"   Total accidents (b+m+g): {total_accidents}")
    
    # Exemples de corrélations attendues
    print(f"\n💡 CORRÉLATIONS ATTENDUES:")
    print(f"   - Zones avec prix m² élevé → moins d'agressions (règle prix m²)")
    print(f"   - Zones avec chômage élevé → plus d'agressions")
    print(f"   - Zones avec délinquance élevée → plus d'agressions (tous niveaux)")
    print(f"   - Zones avec prix m² élevé → plus d'incendies (densité)")
    print(f"   - Zones avec prix m² élevé → plus d'accidents (trafic)")
    
    # Exemples concrets de microzones avec caractéristiques différentes
    print(f"\n" + "=" * 100)
    print("5️⃣  EXEMPLES CONCRETS PAR TYPE DE ZONE")
    print("=" * 100)
    
    if prix_m2 is not None and isinstance(prix_m2, pd.DataFrame) and 'prix_m2' in prix_m2.columns:
        # Zone chère (prix m² élevé) - on prend directement la microzone max si dispo
        if 'microzone_id' in prix_m2.columns:
            mz_cher_id = prix_m2.loc[prix_m2['prix_m2'].idxmax(), 'microzone_id']
            mz_cher = microzones[microzones['microzone_id'] == mz_cher_id].iloc[0]
            arr_cher = int(mz_cher['arrondissement'])
            prix_cher = prix_m2[prix_m2['microzone_id'] == mz_cher_id].iloc[0]['prix_m2']
        else:
            arr_cher = int(prix_m2.loc[prix_m2['prix_m2'].idxmax(), 'arrondissement'])
            mz_cher = microzones[microzones['arrondissement'] == arr_cher].iloc[0]
            mz_cher_id = mz_cher['microzone_id']
            prix_cher = prix_m2[prix_m2['arrondissement'] == arr_cher].iloc[0]['prix_m2']
        vecteurs_cher = vecteurs_statiques.get(mz_cher_id, {})
        
        print(f"\n🏘️  ZONE CHÈRE (Arrondissement {arr_cher}, Microzone {mz_cher_id}):")
        print(f"   Prix m²: {prix_cher:.0f} €/m²")
        if chomage is not None and isinstance(chomage, pd.DataFrame):
            if 'microzone_id' in chomage.columns:
                chom_cher = chomage[chomage['microzone_id'] == mz_cher_id].iloc[0]['taux_chomage']
            else:
                chom_cher = chomage[chomage['arrondissement'] == arr_cher].iloc[0]['taux_chomage']
            print(f"   Chômage: {chom_cher:.1f} %")
        print(f"   Vecteurs agressions: {vecteurs_cher.get('agressions', (0,0,0))}")
        print(f"   Vecteurs incendies: {vecteurs_cher.get('incendies', (0,0,0))}")
        print(f"   Vecteurs accidents: {vecteurs_cher.get('accidents', (0,0,0))}")
        
        # Zone moins chère (prix m² faible)
        if 'microzone_id' in prix_m2.columns:
            mz_pas_cher_id = prix_m2.loc[prix_m2['prix_m2'].idxmin(), 'microzone_id']
            mz_pas_cher = microzones[microzones['microzone_id'] == mz_pas_cher_id].iloc[0]
            arr_pas_cher = int(mz_pas_cher['arrondissement'])
            prix_pas_cher = prix_m2[prix_m2['microzone_id'] == mz_pas_cher_id].iloc[0]['prix_m2']
        else:
            arr_pas_cher = int(prix_m2.loc[prix_m2['prix_m2'].idxmin(), 'arrondissement'])
            mz_pas_cher = microzones[microzones['arrondissement'] == arr_pas_cher].iloc[0]
            mz_pas_cher_id = mz_pas_cher['microzone_id']
            prix_pas_cher = prix_m2[prix_m2['arrondissement'] == arr_pas_cher].iloc[0]['prix_m2']
        vecteurs_pas_cher = vecteurs_statiques.get(mz_pas_cher_id, {})
        
        print(f"\n🏘️  ZONE MOINS CHÈRE (Arrondissement {arr_pas_cher}, Microzone {mz_pas_cher_id}):")
        print(f"   Prix m²: {prix_pas_cher:.0f} €/m²")
        if chomage is not None and isinstance(chomage, pd.DataFrame):
            if 'microzone_id' in chomage.columns:
                chom_pas_cher = chomage[chomage['microzone_id'] == mz_pas_cher_id].iloc[0]['taux_chomage']
            else:
                chom_pas_cher = chomage[chomage['arrondissement'] == arr_pas_cher].iloc[0]['taux_chomage']
            print(f"   Chômage: {chom_pas_cher:.1f} %")
        print(f"   Vecteurs agressions: {vecteurs_pas_cher.get('agressions', (0,0,0))}")
        print(f"   Vecteurs incendies: {vecteurs_pas_cher.get('incendies', (0,0,0))}")
        print(f"   Vecteurs accidents: {vecteurs_pas_cher.get('accidents', (0,0,0))}")
        
        print(f"\n📊 COMPARAISON:")
        agressions_cher = sum(vecteurs_cher.get('agressions', (0,0,0)))
        agressions_pas_cher = sum(vecteurs_pas_cher.get('agressions', (0,0,0)))
        print(f"   Agressions zone chère: {agressions_cher} vs zone moins chère: {agressions_pas_cher}")
        if agressions_cher < agressions_pas_cher:
            print(f"   ✅ Confirme: zones chères ont moins d'agressions (règle prix m²)")
        else:
            print(f"   ⚠️  Attendu: zones chères devraient avoir moins d'agressions")

print("\n" + "=" * 100)
print("FIN DE L'ANALYSE")
print("=" * 100)
