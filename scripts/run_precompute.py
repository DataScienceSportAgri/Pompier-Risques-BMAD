#!/usr/bin/env python
"""
Script unique d'orchestration pour tous les pré-calculs.

Ce script lance tous les pré-calculs nécessaires pour la simulation :
- Distances caserne ↔ microzone ↔ hôpital (Story 1.2)
- 100 microzones (Story 1.2)
- Vecteurs statiques, prix m², congestion statique (Story 1.3)
- Matrices de corrélation (intra-type, inter-type, voisin, trafic, alcool/nuit, saisonnalité) (Story 1.4.4)

Usage:
    python scripts/run_precompute.py                    # Lance tous les pré-calculs
    python scripts/run_precompute.py --skip-distances   # Saute le calcul des distances
    python scripts/run_precompute.py --skip-vectors     # Saute les vecteurs statiques
    python scripts/run_precompute.py --only-distances  # Lance uniquement les distances
"""

import argparse
import sys
import yaml
from pathlib import Path
import logging
from typing import Dict, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> Dict[str, Any]:
    """Charge la configuration depuis le fichier YAML."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"✅ Configuration chargée depuis {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"❌ Fichier config introuvable: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"❌ Erreur parsing YAML: {e}")
        sys.exit(1)


def should_run_block(block_name: str, config: Dict[str, Any], args: argparse.Namespace) -> bool:
    """
    Détermine si un bloc de pré-calcul doit être exécuté.
    
    Priorité:
    1. Arguments CLI (--skip-*, --only-*)
    2. Section config precompute.enabled
    3. Par défaut: True
    """
    # Vérifier les arguments CLI
    if hasattr(args, 'skip_distances') and args.skip_distances and block_name == 'distances':
        return False
    # Note: microzones n'est plus un bloc séparé (créées dans distances)
    # On garde la vérification pour compatibilité mais elle ne sera jamais utilisée
    if hasattr(args, 'skip_microzones') and args.skip_microzones and block_name == 'microzones':
        return False
    if hasattr(args, 'skip_vectors') and args.skip_vectors and block_name == 'vectors_static':
        return False
    if hasattr(args, 'skip_prix_m2') and args.skip_prix_m2 and block_name == 'prix_m2':
        return False
    if hasattr(args, 'skip_congestion') and args.skip_congestion and block_name == 'congestion_static':
        return False
    if hasattr(args, 'skip_matrices') and args.skip_matrices and block_name == 'matrices_correlation':
        return False
    
    # Vérifier --only-* (si spécifié, seul ce bloc doit tourner)
    if hasattr(args, 'only_distances') and args.only_distances:
        return block_name == 'distances'
    # Note: microzones n'est plus un bloc séparé (créées dans distances)
    if hasattr(args, 'only_microzones') and args.only_microzones:
        logger.warning("⚠️  --only-microzones est obsolète. Les microzones sont créées avec --only-distances")
        return block_name == 'distances'  # Rediriger vers distances
    if hasattr(args, 'only_vectors') and args.only_vectors:
        return block_name == 'vectors_static'
    if hasattr(args, 'only_prix_m2') and args.only_prix_m2:
        return block_name == 'prix_m2'
    if hasattr(args, 'only_congestion') and args.only_congestion:
        return block_name == 'congestion_static'
    if hasattr(args, 'only_matrices') and args.only_matrices:
        return block_name == 'matrices_correlation'
    
    # Vérifier la config
    precompute_enabled = config.get('precompute', {}).get('enabled', {})
    if block_name in precompute_enabled:
        return precompute_enabled[block_name]
    
    # Par défaut: True
    return True


def run_distances(config: Dict[str, Any], output_dir: Path) -> bool:
    """
    Lance le pré-calcul des distances (Story 1.2).
    
    Returns:
        True si succès, False sinon
    """
    logger.info("🔄 Démarrage pré-calcul distances...")
    try:
        # Import relatif depuis le dossier scripts
        import sys
        scripts_dir = Path(__file__).parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        
        from precompute_distances import precompute_distances
        return precompute_distances(config, output_dir)
    except ImportError as e:
        logger.error(f"❌ Module precompute_distances non trouvé: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur pré-calcul distances: {e}")
        return False


def run_microzones(config: Dict[str, Any], output_dir: Path) -> bool:
    """
    Lance le pré-calcul des 100 microzones (Story 1.2).
    
    Note: Les microzones sont créées automatiquement dans precompute_distances
    lors du calcul des distances. Cette fonction est conservée uniquement pour
    compatibilité avec la config, mais ne fait rien car les microzones sont
    déjà créées dans run_distances.
    
    Returns:
        True si succès, False sinon
    """
    logger.info("🔄 Pré-calcul microzones...")
    logger.info("   ⚠️  Les microzones sont créées automatiquement dans run_distances")
    logger.info("   ⚠️  Cette fonction est redondante - utilisez --only-distances pour créer les microzones")
    return True


def run_vectors_static(config: Dict[str, Any], output_dir: Path) -> bool:
    """
    Lance le pré-calcul des vecteurs statiques (Story 1.3).
    
    Returns:
        True si succès, False sinon
    """
    logger.info("🔄 Démarrage pré-calcul vecteurs statiques...")
    try:
        import sys
        scripts_dir = Path(__file__).parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        
        from precompute_vectors_static import precompute_vectors_static
        return precompute_vectors_static(config, output_dir)
    except ImportError as e:
        logger.error(f"❌ Module precompute_vectors_static non trouvé: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur pré-calcul vecteurs statiques: {e}")
        return False


def run_prix_m2(config: Dict[str, Any], output_dir: Path) -> bool:
    """
    Lance le pré-calcul des prix m² (Story 1.3).
    
    Note: Les prix m² sont calculés dans precompute_vectors_static.
    
    Returns:
        True si succès, False sinon
    """
    logger.info("🔄 Démarrage pré-calcul prix m²...")
    # Les prix m² sont calculés dans run_vectors_static
    logger.info("   Les prix m² sont calculés avec les vecteurs statiques (run_vectors_static)")
    return True


def run_congestion_static(config: Dict[str, Any], output_dir: Path) -> bool:
    """
    Lance le pré-calcul de la congestion statique de base (Story 1.3).
    
    Note: La congestion statique est calculée dans precompute_vectors_static.
    
    Returns:
        True si succès, False sinon
    """
    logger.info("🔄 Démarrage pré-calcul congestion statique...")
    # La congestion statique est calculée dans run_vectors_static
    logger.info("   La congestion statique est calculée avec les vecteurs statiques (run_vectors_static)")
    return True


def run_matrices_correlation(config: Dict[str, Any], output_dir: Path) -> bool:
    """
    Lance le pré-calcul des matrices de corrélation (Story 1.4.4).
    
    Returns:
        True si succès, False sinon
    """
    logger.info("🔄 Démarrage pré-calcul matrices de corrélation...")
    try:
        import sys
        scripts_dir = Path(__file__).parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from precompute_matrices_correlation import precompute_matrices_correlation
        success = precompute_matrices_correlation(config, output_dir)
        if success:
            logger.info("✅ Pré-calcul matrices de corrélation terminé avec succès")
        else:
            logger.error("❌ Pré-calcul matrices de corrélation échoué")
        return success
    except ImportError as e:
        logger.error(f"❌ Module precompute_matrices_correlation non trouvé: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur pré-calcul matrices de corrélation: {e}", exc_info=True)
        return False


def run_validate_patterns(config: Dict[str, Any]) -> bool:
    """
    Valide les fichiers patterns Paris (Story 1.4).
    Utilise config['paths']['data_patterns'] ou data/patterns par défaut.
    
    Returns:
        True si tous les patterns sont valides, False sinon
    """
    logger.info("🔄 Validation des patterns (Story 1.4)...")
    try:
        import sys
        scripts_dir = Path(__file__).parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from validate_patterns import run_validate_patterns as _run
        return _run(config)
    except ImportError as e:
        logger.error(f"❌ Module validate_patterns non trouvé: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur validation patterns: {e}", exc_info=True)
        return False


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description='Script unique d\'orchestration pour tous les pré-calculs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python scripts/run_precompute.py                    # Lance tous les pré-calculs
  python scripts/run_precompute.py --skip-distances   # Saute le calcul des distances
  python scripts/run_precompute.py --only-vectors     # Lance uniquement les vecteurs statiques
        """
    )
    
    # Arguments pour sauter des blocs
    parser.add_argument('--skip-distances', action='store_true',
                       help='Sauter le pré-calcul des distances (Story 1.2)')
    parser.add_argument('--skip-microzones', action='store_true',
                       help='Sauter le pré-calcul des microzones (Story 1.2)')
    parser.add_argument('--skip-vectors', action='store_true',
                       help='Sauter le pré-calcul des vecteurs statiques (Story 1.3)')
    parser.add_argument('--skip-prix-m2', action='store_true',
                       help='Sauter le pré-calcul des prix m² (Story 1.3)')
    parser.add_argument('--skip-congestion', action='store_true',
                       help='Sauter le pré-calcul de la congestion statique (Story 1.3)')
    parser.add_argument('--skip-matrices', action='store_true',
                       help='Sauter le pré-calcul des matrices de corrélation (Story 1.4.4)')
    
    # Arguments pour lancer uniquement un bloc
    parser.add_argument('--only-distances', action='store_true',
                       help='Lancer uniquement le pré-calcul des distances')
    parser.add_argument('--only-microzones', action='store_true',
                       help='Lancer uniquement le pré-calcul des microzones')
    parser.add_argument('--only-vectors', action='store_true',
                       help='Lancer uniquement le pré-calcul des vecteurs statiques')
    parser.add_argument('--only-prix-m2', action='store_true',
                       help='Lancer uniquement le pré-calcul des prix m²')
    parser.add_argument('--only-congestion', action='store_true',
                       help='Lancer uniquement le pré-calcul de la congestion statique')
    parser.add_argument('--only-matrices', action='store_true',
                       help='Lancer uniquement le pré-calcul des matrices de corrélation')
    parser.add_argument('--validate-patterns', action='store_true',
                       help='Valider les patterns (Story 1.4) avant les pré-calculs')
    parser.add_argument('--only-validate-patterns', action='store_true',
                       help='Uniquement valider les patterns puis quitter')
    
    # Option pour spécifier le fichier config
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Chemin vers le fichier de configuration (défaut: config/config.yaml)')
    
    args = parser.parse_args()
    
    # Vérifier que les arguments --only-* sont mutuellement exclusifs
    only_args = [args.only_distances, args.only_microzones, args.only_vectors,
                 args.only_prix_m2, args.only_congestion, args.only_matrices,
                 args.only_validate_patterns]
    if sum(only_args) > 1:
        logger.error("❌ Les arguments --only-* sont mutuellement exclusifs")
        sys.exit(1)
    
    # Charger la configuration
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent.parent / config_path
    
    config = load_config(config_path)
    
    # Mode validation patterns uniquement (Story 1.4)
    if args.only_validate_patterns:
        ok = run_validate_patterns(config)
        sys.exit(0 if ok else 1)
    
    # Optionnel : valider les patterns avant les pré-calculs
    if getattr(args, 'validate_patterns', False):
        if not run_validate_patterns(config):
            logger.error("❌ Validation des patterns échouée, abandon")
            sys.exit(1)
    
    # Créer le dossier de sortie
    output_dir = Path(config['paths']['data_source'])
    if not output_dir.is_absolute():
        output_dir = Path(__file__).parent.parent / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Dossier de sortie: {output_dir}")
    
    # Lancer les pré-calculs
    results = {}
    
    # Distances (Story 1.2) - Les microzones sont créées automatiquement dans run_distances
    if should_run_block('distances', config, args):
        results['distances'] = run_distances(config, output_dir)
        # Les microzones sont créées dans run_distances, donc on marque aussi microzones comme fait
        results['microzones'] = results['distances']
    else:
        logger.info("⏭️  Pré-calcul distances ignoré (--skip-distances ou config)")
        results['distances'] = None
        results['microzones'] = None
    
    # Note: run_microzones n'est plus appelé car les microzones sont créées dans run_distances
    # On garde la vérification pour compatibilité avec la config
    if should_run_block('microzones', config, args) and results.get('microzones') is None:
        logger.info("⚠️  Pré-calcul microzones demandé mais distances non exécutées")
        logger.info("   Les microzones sont créées automatiquement avec --only-distances")
        results['microzones'] = None
    
    # Vecteurs statiques, prix m², congestion (Story 1.3)
    if should_run_block('vectors_static', config, args):
        results['vectors_static'] = run_vectors_static(config, output_dir)
    else:
        logger.info("⏭️  Pré-calcul vecteurs statiques ignoré (--skip-vectors ou config)")
        results['vectors_static'] = None
    
    if should_run_block('prix_m2', config, args):
        results['prix_m2'] = run_prix_m2(config, output_dir)
    else:
        logger.info("⏭️  Pré-calcul prix m² ignoré (--skip-prix-m2 ou config)")
        results['prix_m2'] = None
    
    if should_run_block('congestion_static', config, args):
        results['congestion_static'] = run_congestion_static(config, output_dir)
    else:
        logger.info("⏭️  Pré-calcul congestion statique ignoré (--skip-congestion ou config)")
        results['congestion_static'] = None
    
    # Matrices de corrélation (Story 1.4.4)
    if should_run_block('matrices_correlation', config, args):
        results['matrices_correlation'] = run_matrices_correlation(config, output_dir)
    else:
        logger.info("⏭️  Pré-calcul matrices de corrélation ignoré (--skip-matrices ou config)")
        results['matrices_correlation'] = None
    
    # Résumé
    logger.info("\n" + "="*60)
    logger.info("📊 RÉSUMÉ DES PRÉ-CALCULS")
    logger.info("="*60)
    
    success_count = sum(1 for v in results.values() if v is True)
    skipped_count = sum(1 for v in results.values() if v is None)
    failed_count = sum(1 for v in results.values() if v is False)
    
    for block_name, result in results.items():
        if result is True:
            logger.info(f"✅ {block_name}: Succès")
        elif result is False:
            logger.error(f"❌ {block_name}: Échec")
        else:
            logger.info(f"⏭️  {block_name}: Ignoré")
    
    logger.info("="*60)
    logger.info(f"Total: {success_count} succès, {skipped_count} ignorés, {failed_count} échecs")
    
    if failed_count > 0:
        logger.error("❌ Certains pré-calculs ont échoué")
        sys.exit(1)
    else:
        logger.info("✅ Tous les pré-calculs demandés sont terminés")
        sys.exit(0)


if __name__ == '__main__':
    main()
