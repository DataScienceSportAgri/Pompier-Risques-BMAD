"""
Tests d'intégration pour main.py (Story 2.4.2).
Pipeline config → simulation headless, lancement Streamlit depuis main.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Racine projet
ROOT = Path(__file__).resolve().parents[2]


def test_config_load_and_validate() -> None:
    """Charge et valide config/config.yaml (structure, valeurs, chemins)."""
    from src.core.config.config_validator import load_and_validate_config
    from src.core.utils.path_resolver import PathResolver

    path = PathResolver.config_file("config.yaml")
    assert path.exists(), "config/config.yaml doit exister"
    config = load_and_validate_config(str(path))
    assert config is not None
    assert config.simulation.default_days >= 1
    assert config.simulation.default_runs >= 1
    assert config.paths.data_source
    assert config.paths.data_intermediate


def test_headless_pipeline() -> None:
    """Pipeline config → simulation headless OK (2 runs × 3 jours, sans Streamlit)."""
    from src.core.config.config_validator import load_and_validate_config
    from src.core.utils.path_resolver import PathResolver
    from src.services.simulation_service import SimulationService

    path = PathResolver.config_file("config.yaml")
    config = load_and_validate_config(str(path))
    svc = SimulationService(config=config)

    base = ROOT / "data" / "intermediate"
    svc.run_headless(
        days=3,
        runs=2,
        output_dir=base,
        save_pickles=True,
        save_trace=True,
        verbose=False,
    )

    for i in range(2):
        run_id = f"run_{i:03d}"
        run_dir = base / run_id
        assert run_dir.exists(), f"{run_id} doit exister"
        assert (run_dir / "simulation_state.pkl").exists()
        assert (run_dir / "trace.json").exists()


def test_main_headless_cli() -> None:
    """main.py --headless --runs 2 --days 3 s'exécute sans erreur."""
    cmd = [
        sys.executable,
        "-m",
        "main",
        "--headless",
        "--runs",
        "2",
        "--days",
        "3",
        "--no-pickles",
        "--no-trace",
    ]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, (r.stdout, r.stderr)


def test_main_ui_launch() -> None:
    """main.py --ui lance Streamlit sans erreur immédiate (timeout après démarrage)."""
    cmd = [
        sys.executable,
        "-m",
        "main",
        "--ui",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        proc.terminate()
        proc.wait(timeout=5)
        return  # still running after 10s → Streamlit a démarré
    assert proc.returncode == 0, (stdout, stderr)
