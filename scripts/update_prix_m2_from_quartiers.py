"""
Script pour mettre à jour les prix m² en utilisant les données des notaires par quartier.

Ce script :
1. Charge les microzones avec leurs quartiers administratifs
2. Utilise un dictionnaire de prix par quartier (basé sur les données des notaires T4 2024)
3. Calcule la moyenne des prix des quartiers pour chaque microzone
4. Met à jour le fichier prix_m2.pkl
"""

import logging
import pickle
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Prix au m² standardisés par quartier administratif (fin décembre 2024)
# Source: https://paris.notaires.fr/sites/default/files/Prix_communes_arrd_quartiers_T42024.pdf
# Format: {nom_quartier: prix_m2}
PRIX_M2_PAR_QUARTIER = {
    # 1er arrondissement
    "St-Germain-l'Auxerrois": None,  # n.s.
    "Les Halles": 11240,
    "Palais-Royal": None,  # n.s.
    "Place Vendôme": None,  # n.s.
    
    # 2e arrondissement
    "Gaillon": None,  # n.s.
    "Vivienne": None,  # n.s.
    "Mail": 12220,
    "Bonne-Nouvelle": 10950,
    
    # 3e arrondissement
    "Arts-et-Métiers": 11170,
    "Enfants-Rouges": 12160,
    "Archives": 12730,
    "Sainte-Avoye": 12340,
    
    # 4e arrondissement
    "Saint-Merri": 11840,
    "Saint-Gervais": 12510,
    "Arsenal": 12580,
    "Notre-Dame": 13310,
    
    # 5e arrondissement
    "Saint-Victor": 12230,
    "Jardin des Plantes": 10580,
    "Val-de-Grâce": 11830,
    "Sorbonne": 12100,
    
    # 6e arrondissement
    "Monnaie": 13890,
    "Odéon": 14100,
    "N-D-des-Champs": 13610,
    "St-Germain-des-Prés": 15500,
    
    # 7e arrondissement
    "St.-Thomas-d'Aquin": 14890,
    "Les Invalides": 13950,
    "Ecole-Militaire": 11750,
    "Gros-Caillou": 11670,
    
    # 8e arrondissement
    "Champs-Elysées": 13800,
    "Faubourg du Roule": 12340,
    "La Madeleine": 12590,
    "Europe": 10380,
    
    # 9e arrondissement
    "Saint-Georges": 9620,
    "Chaussée-d'Antin": 10730,
    "Faubourg Montmartre": 9640,
    "Rochechouart": 9850,
    
    # 10e arrondissement
    "St.-Vincent-de-Paul": 8170,
    "Porte Saint-Denis": 9470,
    "Porte Saint-Martin": 9650,
    "Hopital St.-Louis": 9160,
    
    # 11e arrondissement
    "Folie-Méricourt": 9780,
    "Saint-Ambroise": 9830,
    "La Roquette": 9090,
    "Sainte-Marguerite": 8820,
    
    # 12e arrondissement
    "Bel-Air": 8030,
    "Picpus": 8270,
    "Bercy": 8490,
    "Quinze-Vingts": 9820,
    
    # 13e arrondissement
    "Salpétrière": 9340,
    "Gare": 7760,
    "Maison-Blanche": 8530,
    "Croulebarbe": 9380,
    
    # 14e arrondissement
    "Montparnasse": 10120,
    "Parc Montsouris": 8910,
    "Petit Montrouge": 8540,
    "Plaisance": 8690,
    
    # 15e arrondissement
    "Saint-Lambert": 8300,
    "Necker": 8840,
    "Grenelle": 9820,
    "Javel": 8710,
    
    # 16e arrondissement
    "Auteuil": 9100,
    "La Muette": 10350,
    "Porte Dauphine": 10590,
    "Chaillot": 11960,
    
    # 17e arrondissement
    "Ternes": 9650,
    "Plaine Monceau": 9880,
    "Batignolles": 9260,
    "Epinettes": 8360,
    
    # 18e arrondissement
    "Grandes-Carrières": 8970,
    "Clignancourt": 8410,
    "La Goutte-d'Or": 6890,
    "La Chapelle": 6610,
    
    # 19e arrondissement
    "La Villette": 7220,
    "Pont de Flandre": 7010,
    "Amérique": 7650,
    "Combat": 8250,
    
    # 20e arrondissement
    "Belleville": 8290,
    "Saint-Fargeau": 7900,
    "Père-Lachaise": 8110,
    "Charonne": 8080,
}


def normalize_quartier_name(name: str) -> str:
    """
    Normalise le nom d'un quartier pour faciliter le matching.
    """
    if not name:
        return ""
    name = name.strip()
    # Remplacer les tirets par des espaces pour uniformiser
    name = name.replace("-", " ").replace("_", " ")
    # Enlever les articles en début
    articles = ["le ", "la ", "les ", "l'", "l "]
    for article in articles:
        if name.lower().startswith(article):
            name = name[len(article):].strip()
    # Normaliser les espaces multiples
    name = " ".join(name.split())
    return name.lower()


# Mapping spécifique entre noms GeoJSON et noms PDF
QUARTIER_NAME_MAPPING = {
    # GeoJSON -> PDF
    "Halles": "Les Halles",
    "Goutte-d'Or": "La Goutte-d'Or",
    "Faubourg-Montmartre": "Faubourg Montmartre",
    "Faubourg-du-Roule": "Faubourg du Roule",
    "Notre-Dame-des-Champs": "N-D-des-Champs",
    "Parc-de-Montsouris": "Parc Montsouris",
    "Petit-Montrouge": "Petit Montrouge",
    "Pont-de-Flandre": "Pont de Flandre",
    "Porte-Dauphine": "Porte Dauphine",
    "Porte-Saint-Denis": "Porte Saint-Denis",
    "Porte-Saint-Martin": "Porte Saint-Martin",
    "Roquette": "La Roquette",
    "Sainte-Avoie": "Sainte-Avoye",
    "Val-de-Grace": "Val-de-Grâce",
    "Villette": "La Villette",
    "Invalides": "Les Invalides",
    "Muette": "La Muette",
    "Madeleine": "La Madeleine",
    "Hôpital-Saint-Louis": "Hopital St.-Louis",
    "Plaine de Monceaux": "Plaine Monceau",
}


def find_prix_for_quartier(quartier_name: str) -> float:
    """
    Trouve le prix m² pour un quartier donné.
    Retourne None si non trouvé.
    """
    # 1. Essayer le mapping direct
    if quartier_name in QUARTIER_NAME_MAPPING:
        mapped_name = QUARTIER_NAME_MAPPING[quartier_name]
        if mapped_name in PRIX_M2_PAR_QUARTIER:
            return PRIX_M2_PAR_QUARTIER[mapped_name]
    
    # 2. Essayer le nom exact
    if quartier_name in PRIX_M2_PAR_QUARTIER:
        return PRIX_M2_PAR_QUARTIER[quartier_name]
    
    # 3. Essayer avec normalisation
    normalized = normalize_quartier_name(quartier_name)
    for key, value in PRIX_M2_PAR_QUARTIER.items():
        if normalize_quartier_name(key) == normalized:
            return value
    
    # 4. Essayer un matching partiel (insensible à la casse)
    quartier_lower = quartier_name.lower()
    for key, value in PRIX_M2_PAR_QUARTIER.items():
        key_lower = key.lower()
        # Vérifier si l'un contient l'autre (au moins 5 caractères)
        if len(quartier_lower) >= 5 and len(key_lower) >= 5:
            if quartier_lower in key_lower or key_lower in quartier_lower:
                return value
    
    return None


def update_prix_m2_from_quartiers(
    microzones_pickle_path: Path,
    prix_m2_pickle_path: Path,
    output_pickle_path: Path = None
) -> bool:
    """
    Met à jour les prix m² en calculant la moyenne des quartiers pour chaque microzone.
    
    Args:
        microzones_pickle_path: Chemin vers le fichier pickle des microzones
        prix_m2_pickle_path: Chemin vers le fichier pickle des prix m² existant
        output_pickle_path: Chemin de sortie (par défaut, remplace le fichier d'entrée)
    
    Returns:
        True si succès, False sinon
    """
    try:
        # 1. Charger les microzones avec leurs quartiers
        logger.info(f"📂 Chargement des microzones depuis {microzones_pickle_path}...")
        with open(microzones_pickle_path, 'rb') as f:
            microzones = pickle.load(f)
        
        logger.info(f"✅ {len(microzones)} microzones chargées")
        
        if 'quartiers_administratifs' not in microzones.columns:
            logger.error("❌ Colonne 'quartiers_administratifs' introuvable dans les microzones")
            logger.error("   Exécutez d'abord: python scripts/add_quartiers_to_microzones.py")
            return False
        
        # 2. Charger les prix m² existants (pour garder la structure)
        logger.info(f"📂 Chargement des prix m² existants depuis {prix_m2_pickle_path}...")
        with open(prix_m2_pickle_path, 'rb') as f:
            prix_m2_df = pickle.load(f)
        
        logger.info(f"✅ Prix m² existants chargés: {len(prix_m2_df)} lignes")
        
        # 3. Calculer les nouveaux prix pour chaque microzone
        logger.info("🔄 Calcul des nouveaux prix m² basés sur les quartiers...")
        
        nouveaux_prix = []
        quartiers_trouves = 0
        quartiers_manquants = 0
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            quartiers = mz['quartiers_administratifs']
            
            # Calculer la moyenne des prix des quartiers
            prix_quartiers = []
            for quartier in quartiers:
                prix = find_prix_for_quartier(quartier)
                if prix is not None:
                    prix_quartiers.append(prix)
                    quartiers_trouves += 1
                else:
                    quartiers_manquants += 1
                    logger.debug(f"⚠️  Prix non trouvé pour quartier: {quartier}")
            
            if len(prix_quartiers) > 0:
                prix_moyen = np.mean(prix_quartiers)
            else:
                # Fallback: utiliser le prix moyen de l'arrondissement
                # Prix moyens par arrondissement (fin décembre 2024, source PDF)
                prix_par_arr = {
                    1: 12180, 2: 11580, 3: 12040, 4: 12390, 5: 11070,
                    6: 13460, 7: 12420, 8: 11760, 9: 9650, 10: 8780,
                    11: 9220, 12: 8410, 13: 8530, 14: 8840, 15: 8900,
                    16: 10160, 17: 9260, 18: 8380, 19: 7590, 20: 8080
                }
                prix_moyen = prix_par_arr.get(arrondissement, 9000)
                logger.warning(f"⚠️  Aucun prix trouvé pour {microzone_id}, utilisation prix arrondissement: {prix_moyen}")
            
            nouveaux_prix.append({
                'microzone_id': microzone_id,
                'arrondissement': arrondissement,
                'prix_m2': round(prix_moyen, 2)
            })
        
        # 4. Créer le nouveau DataFrame
        nouveau_df = pd.DataFrame(nouveaux_prix)
        
        logger.info(f"✅ Statistiques:")
        logger.info(f"   - Quartiers avec prix trouvé: {quartiers_trouves}")
        logger.info(f"   - Quartiers sans prix: {quartiers_manquants}")
        logger.info(f"   - Prix moyen calculé: {nouveau_df['prix_m2'].mean():.2f} €/m²")
        logger.info(f"   - Prix min: {nouveau_df['prix_m2'].min():.2f} €/m²")
        logger.info(f"   - Prix max: {nouveau_df['prix_m2'].max():.2f} €/m²")
        
        # 5. Sauvegarder
        output_path = output_pickle_path if output_pickle_path else prix_m2_pickle_path
        logger.info(f"💾 Sauvegarde dans {output_path}...")
        
        with open(output_path, 'wb') as f:
            pickle.dump(nouveau_df, f)
        
        logger.info(f"✅ Prix m² mis à jour avec succès")
        
        # Afficher quelques exemples
        logger.info("\n📋 Exemples de prix m² mis à jour:")
        for i in range(min(10, len(nouveau_df))):
            row = nouveau_df.iloc[i]
            mz_id = row['microzone_id']
            prix = row['prix_m2']
            arr = row['arrondissement']
            quartiers = microzones[microzones['microzone_id'] == mz_id]['quartiers_administratifs'].iloc[0]
            logger.info(f"   {mz_id} (arr {arr}): {prix:.0f} €/m² (quartiers: {', '.join(quartiers[:3])})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la mise à jour des prix m²: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    import sys
    
    # Chemins par défaut
    data_dir = Path(__file__).parent.parent / "data" / "source_data"
    microzones_path = data_dir / "microzones.pkl"
    prix_m2_path = data_dir / "prix_m2.pkl"
    
    # Vérifier que les fichiers existent
    if not microzones_path.exists():
        logger.error(f"❌ Fichier microzones introuvable: {microzones_path}")
        sys.exit(1)
    
    if not prix_m2_path.exists():
        logger.error(f"❌ Fichier prix_m2 introuvable: {prix_m2_path}")
        sys.exit(1)
    
    # Exécuter
    success = update_prix_m2_from_quartiers(microzones_path, prix_m2_path)
    
    if success:
        logger.info("✅ Script terminé avec succès")
        sys.exit(0)
    else:
        logger.error("❌ Script terminé avec erreur")
        sys.exit(1)
