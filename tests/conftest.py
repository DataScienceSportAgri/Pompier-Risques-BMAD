"""pytest conftest racine tests/ (marqueurs partagés)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config):
    """Enregistre les marqueurs personnalisés."""
    config.addinivalue_line("markers", "slow: marque les tests lents (simulation longue)")
