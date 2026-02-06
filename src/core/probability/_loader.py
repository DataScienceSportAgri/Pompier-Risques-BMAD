"""Chargement des matrices fixes pour l'application aux probabilités (Story 1.4.4.3)."""

import pickle
from pathlib import Path
from typing import Any, Dict


def load_matrices_for_probability(source_dir: Path) -> Dict[str, Any]:
    """
    Charge matrices intra-type, inter-type, voisin, saisonnalité depuis data/source_data.

    Returns:
        {
            "matrices_intra_type": Dict[mz, Dict[type, ndarray 3×3]],
            "matrices_inter_type": Dict[mz, Dict[type_cible, Dict[type_source, [f,f,f]]]],
            "matrices_voisin": Dict[mz, {voisins, poids_influence, seuil_activation}],
            "matrices_saisonnalite": Dict[mz, Dict[type, Dict[saison, float]]],
        }
    """
    source_dir = Path(source_dir)
    out: Dict[str, Any] = {}
    for name, key in (
        ("matrices_correlation_intra_type.pkl", "matrices_intra_type"),
        ("matrices_correlation_inter_type.pkl", "matrices_inter_type"),
        ("matrices_voisin.pkl", "matrices_voisin"),
        ("matrices_saisonnalite.pkl", "matrices_saisonnalite"),
    ):
        p = source_dir / name
        if not p.exists():
            continue
        with open(p, "rb") as f:
            out[key] = pickle.load(f)
    return out
