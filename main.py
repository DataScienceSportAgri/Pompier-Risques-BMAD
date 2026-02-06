"""
Point d'entrée principal — orchestration config, simulation, Streamlit.
Story 2.4.2 : Orchestration (main.py, config, simulation sans UI).

Usage:
  python main.py --ui
  python main.py --headless [--runs 50] [--days 365]
  python main.py --headless --runs 2 --days 3   # tests rapides
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from src.core.config.config_validator import Config, load_and_validate_config
from src.core.utils.path_resolver import PathResolver
from src.services.simulation_service import SimulationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Simulation Risques Paris — orchestration")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--ui", action="store_true", help="Lancer l'interface Streamlit")
    g.add_argument("--headless", action="store_true", help="Simulation sans UI (N runs × M jours)")
    p.add_argument("--runs", type=int, default=50, help="Nombre de runs (headless). Défaut: 50")
    p.add_argument("--days", type=int, default=365, help="Nombre de jours par run. Défaut: 365")
    p.add_argument(
        "--config",
        type=str,
        default=None,
        help="Chemin config YAML (défaut: config/config.yaml)",
    )
    p.add_argument("--no-pickles", action="store_true", help="Ne pas sauvegarder les pickles (headless)")
    p.add_argument("--no-trace", action="store_true", help="Ne pas sauvegarder les trace JSON (headless)")
    p.add_argument(
        "--scenario",
        type=str,
        choices=["Pessimiste", "Standard", "Optimiste"],
        default="Standard",
        help="Scénario (headless). Défaut: Standard",
    )
    p.add_argument(
        "--variabilite",
        type=str,
        choices=["Faible", "Moyenne", "Forte"],
        default="Moyenne",
        help="Variabilité locale (headless). Défaut: Moyenne",
    )
    p.add_argument(
        "--debug-prints",
        action="store_true",
        help="Afficher des prints pendant le run (événements graves, positifs, microzones > 6)",
    )
    return p.parse_args()


def _run_ui(config_path: str) -> None:
    root = PathResolver.get_project_root()
    app = root / "src" / "adapters" / "ui" / "streamlit_app.py"
    if not app.exists():
        app = root / "src" / "ui" / "web_app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app), "--server.headless", "true"]
    logger.info("Lancement Streamlit: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=str(root), check=True)


def _run_headless(args: argparse.Namespace, config: Config) -> None:
    svc = SimulationService(config=config)
    svc.run_headless(
        days=args.days,
        runs=args.runs,
        save_pickles=not args.no_pickles,
        save_trace=not args.no_trace,
        verbose=True,
        scenario_ui=args.scenario,
        variabilite_ui=args.variabilite,
        debug_prints=args.debug_prints,
    )
    logger.info(
        "Headless terminé: %s runs × %s jours (scénario=%s, variabilité=%s).",
        args.runs, args.days, args.scenario, args.variabilite,
    )


def main() -> None:
    args = _parse_args()

    config_path = args.config
    if config_path is None:
        config_path = str(PathResolver.config_file("config.yaml"))

    if not Path(config_path).exists():
        logger.error("Config introuvable: %s", config_path)
        sys.exit(1)

    try:
        config = load_and_validate_config(config_path)
    except Exception as e:
        logger.error("Configuration invalide: %s", e)
        sys.exit(1)

    if args.ui:
        _run_ui(config_path)
        return

    if args.headless:
        _run_headless(args, config)
        return

    # Défaut: mode UI
    _run_ui(config_path)


if __name__ == "__main__":
    main()
