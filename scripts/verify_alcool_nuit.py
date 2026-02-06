#!/usr/bin/env python
"""
Vérification que les totaux alcool et nuit ne sont pas systématiquement nuls.
Lance une simulation courte et affiche les totaux incidents_alcool et incidents_nuit.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.config.config_validator import load_and_validate_config
from src.core.utils.path_resolver import PathResolver
from src.services.simulation_service import SimulationService


def main():
    config_path = PathResolver.get_project_root() / "config" / "config.yaml"
    config = load_and_validate_config(config_path)
    svc = SimulationService(config=config)

    # Simuler 10 jours via run_one
    num_days = 10
    state = svc.run_one(
        days=num_days,
        run_id="verify_alcool_nuit",
        save_pickles=False,
        save_trace=False,
    )

    dynamic = state.dynamic_state

    # Totaux par type pour alcool et nuit
    def _totals(d: dict) -> dict:
        out = {"agressions": 0, "incendies": 0, "accidents": 0}
        for mz, by_type in d.items():
            for t, v in by_type.items():
                out[t] = out.get(t, 0) + v
        return out

    alcool = _totals(dynamic.incidents_alcool)
    nuit = _totals(dynamic.incidents_nuit)

    print("=== Vérification incidents alcool et nuit ===\n")
    print(f"Après {num_days} jours de simulation :\n")
    print("Incidents alcool par type :")
    for t, v in alcool.items():
        print(f"  {t}: {v}")
    print("\nIncidents nuit par type :")
    for t, v in nuit.items():
        print(f"  {t}: {v}")

    total_alcool = sum(alcool.values())
    total_nuit = sum(nuit.values())

    print(f"\nTotal alcool: {total_alcool}")
    print(f"Total nuit: {total_nuit}")

    if total_alcool == 0 and total_nuit == 0:
        print("\n⚠ ERREUR: Tous les totaux sont nuls - l'évolution alcool/nuit ne fonctionne pas correctement.")
        sys.exit(1)
    else:
        print("\n✓ OK: Les totaux alcool et nuit contiennent des valeurs non nulles.")
        sys.exit(0)


if __name__ == "__main__":
    main()
