"""Chargement des matrices fixes (trafic, alcool/nuit, inter-type) pour l'évolution J→J+1."""

import pickle
from pathlib import Path
from typing import Any, Dict


def load_matrices_for_evolution(source_dir: Path) -> Dict[str, Any]:
    """
    Charge matrices trafic, alcool/nuit et inter-type depuis data/source_data.

    Returns:
        {
            "matrices_trafic": Dict[mz, {...}],
            "matrices_alcool_nuit": Dict[mz, Dict[type, {...}]],
            "matrices_inter_type": Dict[mz, Dict[type_cible, Dict[type_source, [f,f,f]]]],
        }
    """
    out: Dict[str, Any] = {}
    for name, key in (
        ("matrices_trafic.pkl", "matrices_trafic"),
        ("matrices_alcool_nuit.pkl", "matrices_alcool_nuit"),
        ("matrices_correlation_inter_type.pkl", "matrices_inter_type"),
    ):
        p = Path(source_dir) / name
        if not p.exists():
            continue
        with open(p, "rb") as f:
            out[key] = pickle.load(f)
    return out
