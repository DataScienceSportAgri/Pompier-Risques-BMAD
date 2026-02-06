"""
Script pour ajouter les quartiers administratifs aux microzones.

Ce script :
1. Charge le GeoJSON des quartiers administratifs
2. Charge le pickle des microzones
3. Fait une intersection spatiale pour trouver quels quartiers administratifs 
   intersectent chaque microzone
4. Ajoute une colonne 'quartiers_administratifs' avec la liste des quartiers
5. Sauvegarde le pickle mis à jour
"""

import logging
import pickle
from pathlib import Path
import geopandas as gpd
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_quartiers_to_microzones(
    quartiers_geojson_path: Path,
    microzones_pickle_path: Path,
    output_pickle_path: Path = None
) -> bool:
    """
    Ajoute les quartiers administratifs aux microzones.
    
    Args:
        quartiers_geojson_path: Chemin vers le fichier GeoJSON des quartiers administratifs
        microzones_pickle_path: Chemin vers le fichier pickle des microzones
        output_pickle_path: Chemin de sortie (par défaut, remplace le fichier d'entrée)
    
    Returns:
        True si succès, False sinon
    """
    try:
        # 1. Charger les quartiers administratifs
        logger.info(f"📂 Chargement des quartiers administratifs depuis {quartiers_geojson_path}...")
        quartiers_gdf = gpd.read_file(quartiers_geojson_path)
        logger.info(f"✅ {len(quartiers_gdf)} quartiers administratifs chargés")
        
        # Vérifier les colonnes disponibles
        logger.info(f"Colonnes quartiers: {quartiers_gdf.columns.tolist()}")
        
        # Identifier la colonne avec le nom du quartier
        # Le GeoJSON des quartiers administratifs de Paris utilise 'l_qu' pour le nom
        nom_col = None
        for col in ['l_qu', 'nom', 'quartier', 'name', 'NOM', 'QUARTIER']:
            if col in quartiers_gdf.columns:
                nom_col = col
                break
        
        if nom_col is None:
            # Prendre la première colonne de type string qui n'est pas 'geometry'
            for col in quartiers_gdf.columns:
                if col != 'geometry' and quartiers_gdf[col].dtype == 'object':
                    nom_col = col
                    break
        
        if nom_col is None:
            logger.warning("⚠️  Aucune colonne de nom trouvée, utilisation de l'index")
            quartiers_gdf['quartier_nom'] = quartiers_gdf.index.astype(str)
            nom_col = 'quartier_nom'
        
        logger.info(f"✅ Colonne de nom utilisée: {nom_col}")
        
        # 2. Charger les microzones
        logger.info(f"📂 Chargement des microzones depuis {microzones_pickle_path}...")
        with open(microzones_pickle_path, 'rb') as f:
            microzones = pickle.load(f)
        
        logger.info(f"✅ {len(microzones)} microzones chargées")
        logger.info(f"Colonnes microzones: {microzones.columns.tolist()}")
        
        # Vérifier que les deux GeoDataFrames ont le même CRS
        if microzones.crs != quartiers_gdf.crs:
            logger.info(f"🔄 Conversion CRS: microzones {microzones.crs} -> quartiers {quartiers_gdf.crs}")
            microzones = microzones.to_crs(quartiers_gdf.crs)
        
        # 3. Faire l'intersection spatiale
        logger.info("🔄 Calcul des intersections spatiales...")
        
        # Pour chaque microzone, trouver les quartiers qui l'intersectent
        quartiers_list = []
        
        for idx, mz in microzones.iterrows():
            microzone_geom = mz.geometry
            
            # Trouver les quartiers qui intersectent cette microzone
            intersecting = quartiers_gdf[quartiers_gdf.intersects(microzone_geom)]
            
            if len(intersecting) > 0:
                # Créer une liste des noms de quartiers
                quartiers_noms = intersecting[nom_col].tolist()
                quartiers_list.append(quartiers_noms)
            else:
                # Aucun quartier trouvé (peut arriver si la microzone est en dehors)
                logger.warning(f"⚠️  Aucun quartier trouvé pour {mz.get('microzone_id', idx)}")
                quartiers_list.append([])
        
        # 4. Ajouter la colonne aux microzones
        microzones['quartiers_administratifs'] = quartiers_list
        
        # Statistiques
        total_quartiers = sum(len(q) for q in quartiers_list)
        microzones_avec_quartiers = sum(1 for q in quartiers_list if len(q) > 0)
        logger.info(f"✅ Statistiques:")
        logger.info(f"   - Microzones avec quartiers: {microzones_avec_quartiers}/{len(microzones)}")
        logger.info(f"   - Total associations: {total_quartiers}")
        logger.info(f"   - Moyenne quartiers par microzone: {total_quartiers/len(microzones):.2f}")
        
        # 5. Sauvegarder
        output_path = output_pickle_path if output_pickle_path else microzones_pickle_path
        logger.info(f"💾 Sauvegarde dans {output_path}...")
        
        with open(output_path, 'wb') as f:
            pickle.dump(microzones, f)
        
        logger.info(f"✅ Microzones sauvegardées avec quartiers administratifs")
        
        # Afficher quelques exemples
        logger.info("\n📋 Exemples de microzones avec leurs quartiers:")
        for i in range(min(5, len(microzones))):
            mz_id = microzones.iloc[i].get('microzone_id', f'Index {i}')
            quartiers = microzones.iloc[i]['quartiers_administratifs']
            logger.info(f"   {mz_id}: {quartiers}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'ajout des quartiers: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    import sys
    
    # Chemins par défaut
    data_dir = Path(__file__).parent.parent / "data" / "source_data"
    quartiers_path = data_dir / "quartiers_administratifs.geojson"
    microzones_path = data_dir / "microzones.pkl"
    
    # Vérifier que les fichiers existent
    if not quartiers_path.exists():
        logger.error(f"❌ Fichier quartiers introuvable: {quartiers_path}")
        sys.exit(1)
    
    if not microzones_path.exists():
        logger.error(f"❌ Fichier microzones introuvable: {microzones_path}")
        sys.exit(1)
    
    # Exécuter
    success = add_quartiers_to_microzones(quartiers_path, microzones_path)
    
    if success:
        logger.info("✅ Script terminé avec succès")
        sys.exit(0)
    else:
        logger.error("❌ Script terminé avec erreur")
        sys.exit(1)
