"""
Script pour lancer l'entraînement ML complet : 50 runs headless, extraction, entraînement.
Story 2.4.4 - Interface ML modèles

Usage:
  python scripts/run_ml_training.py [--runs 50] [--days 365] [--regression|--classification]
"""

import argparse
import sys
from pathlib import Path

# Ajouter la racine au path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from src.core.config.config_validator import load_and_validate_config
from src.services.ml_service import MLService, MLTrainer
from src.services.simulation_service import SimulationService
from src.core.utils.path_resolver import PathResolver


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, default=50)
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--regression", action="store_true", help="Entraîner régression (défaut)")
    p.add_argument("--classification", action="store_true", help="Entraîner classification")
    args = p.parse_args()

    mode = "classification" if args.classification else "regression"
    label_col = "classe" if args.classification else "score"

    config_path = PathResolver.config_file("config.yaml")
    config = load_and_validate_config(str(config_path))

    print(f"1. Simulation {args.runs} runs × {args.days} jours...")
    sim = SimulationService(config=config)
    sim.run_headless(
        days=args.days,
        runs=args.runs,
        save_pickles=True,
        save_trace=True,
        verbose=True,
    )

    print("\n2. Extraction features/labels + préparation ML...")
    ml_svc = MLService()
    df_ml = ml_svc.workflow_extract_then_prepare(
        run_ids=[f"{i:03d}" for i in range(args.runs)],
        label_column=label_col,
        verbose=True,
        calibrate_classification=args.classification,
    )

    if df_ml.empty or len(df_ml) < 10:
        print("ERREUR: Données ML insuffisantes")
        return 1

    print(f"\n3. Entraînement ({mode})...")
    trainer = MLTrainer()
    if mode == "regression":
        res = trainer.train_regression_models(df_ml, label_column="score")
        for algo, data in res.items():
            print(f"  {algo}: MAE={data['metrics']['MAE']:.3f}, R²={data['metrics']['R2']:.3f}")
    else:
        res = trainer.train_classification_models(df_ml, label_column="classe")
        for algo, data in res.items():
            if data:
                print(f"  {algo}: Accuracy={data['metrics']['accuracy']:.2%}, F1={data['metrics']['f1']:.3f}")

    print("\nTerminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
