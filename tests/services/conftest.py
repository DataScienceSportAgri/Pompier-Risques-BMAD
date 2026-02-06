"""
Configuration pytest pour tests services.
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path Python
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
