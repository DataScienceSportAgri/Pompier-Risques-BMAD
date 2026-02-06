"""
Service d'orchestration de la simulation (headless / UI).
Story 2.4.2 - Orchestration main.py, config, simulation sans UI.

Utilise GenerationService et SimulationState pour exécuter N runs × M jours
en mode headless, ou expose un run unique pour l'UI Streamlit.

Scénario (pessimiste / standard / optimiste) et variabilité locale (faible / moyenne / forte)
sont pris en compte dans la génération des runs et enregistrés dans trace.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.core.config.config_validator import Config
from src.core.generation.generation_service import GenerationService
from src.core.generation.static_vector_loader import StaticVectorLoader
from src.core.state.simulation_state import SimulationState
from src.core.utils.path_resolver import PathResolver

logger = logging.getLogger(__name__)

# Mapping UI → config (scénario) et UI → variabilité locale (float)
SCENARIO_UI_TO_CONFIG = {
    "Pessimiste": "pessimiste",
    "Standard": "moyen",
    "Optimiste": "optimiste",
}
VARIABILITE_UI_TO_FLOAT = {
    "Faible": 0.3,
    "Moyenne": 0.5,
    "Forte": 0.7,
}
DEFAULT_SCENARIO = "moyen"
DEFAULT_VARIABILITE = "Moyenne"
DEFAULT_VARIABILITE_LOCALE = 0.5


def _resolve_run_params(
    config: Config,
    scenario_ui: Optional[str] = None,
    variabilite_ui: Optional[str] = None,
) -> Tuple[Dict[str, Any], float, str, str]:
    """
    Déduit scenario_config, variabilite_locale et libellés à partir des sélections UI.

    Args:
        config: Config validée
        scenario_ui: Libellé UI (Pessimiste, Standard, Optimiste) ou None → moyen
        variabilite_ui: Libellé UI (Faible, Moyenne, Forte) ou None → Moyenne

    Returns:
        (scenario_config, variabilite_locale, scenario_key, variabilite_label)
    """
    scenario_key = SCENARIO_UI_TO_CONFIG.get(
        scenario_ui or "Standard", DEFAULT_SCENARIO
    )
    if scenario_key not in ("pessimiste", "moyen", "optimiste"):
        scenario_key = DEFAULT_SCENARIO
    sc = getattr(config.scenarios, scenario_key)
    scenario_config = {
        "facteur_intensite": sc.facteur_intensite,
        "proba_crise": sc.proba_crise,
    }

    variabilite_label = variabilite_ui or DEFAULT_VARIABILITE
    variabilite_locale = VARIABILITE_UI_TO_FLOAT.get(
        variabilite_label, DEFAULT_VARIABILITE_LOCALE
    )
    return scenario_config, variabilite_locale, scenario_key, variabilite_label


def _limites_microzone_arrondissement_or_parse(microzone_ids: List[str]) -> Dict[str, int]:
    """Mapping microzone_id → arrondissement (1..20). Charge limites si dispo, sinon parse MZ_XX_YY."""
    try:
        from src.services.casualty_calculator import CasualtyCalculator
        limites = CasualtyCalculator.load_limites_microzone_arrondissement()
        if limites:
            return {mz: limites.get(mz, _parse_arr(mz)) for mz in microzone_ids}
    except (FileNotFoundError, ValueError, Exception):
        pass
    return {mz: _parse_arr(mz) for mz in microzone_ids}


def _parse_arr(microzone_id: str) -> int:
    """Extrait l'arrondissement depuis microzone_id.
    Formats : MZ_11_01 → 11 ; MZ031 (MZ + 3 chiffres, 5 microzones/arr) → 7."""
    try:
        parts = microzone_id.split("_")
        if len(parts) >= 2:
            return max(1, min(20, int(parts[1])))
        if (
            len(microzone_id) == 5
            and microzone_id.startswith("MZ")
            and microzone_id[2:].isdigit()
        ):
            idx = int(microzone_id[2:])
            return max(1, min(20, (idx - 1) // 5 + 1))
    except (ValueError, TypeError):
        pass
    return 1


def _get_microzone_ids(config: Optional[Config] = None) -> List[str]:
    """Charge les identifiants de microzones depuis vecteurs_statiques.pkl."""
    lissage_alpha = 0.7
    if config and config.vecteurs_statiques is not None:
        lissage_alpha = config.vecteurs_statiques.lissage_alpha
    loader = StaticVectorLoader(lissage_alpha=lissage_alpha)
    return list(loader.vecteurs_statiques.keys())


class SimulationService:
    """
    Orchestre la simulation : chargement config, runs headless, intégration GenerationService.
    """

    def __init__(self, config: Config, seed: Optional[int] = None):
        self.config = config
        self._seed = seed if seed is not None else config.simulation.seed_default
        self._microzone_ids: Optional[List[str]] = None
        # Cache du GenerationService pour advance_one_day (évite de réinitialiser le RNG à chaque jour)
        self._cached_gen: Optional[GenerationService] = None
        self._cached_gen_run_id: Optional[str] = None

    def _microzone_ids_or_load(self) -> List[str]:
        if self._microzone_ids is None:
            self._microzone_ids = _get_microzone_ids(self.config)
        return self._microzone_ids

    def run_headless(
        self,
        days: int,
        runs: int,
        output_dir: Optional[Path] = None,
        save_pickles: bool = True,
        save_trace: bool = True,
        verbose: bool = True,
        scenario_ui: Optional[str] = None,
        variabilite_ui: Optional[str] = None,
        debug_prints: bool = False,
    ) -> None:
        """
        Exécute N runs × M jours sans UI.
        Optionnellement sauvegarde état (pickle) et trace par run.

        Args:
            days: Nombre de jours par run
            runs: Nombre de runs
            output_dir: Dossier de sortie (défaut: data/intermediate)
            save_pickles: Sauvegarder simulation_state.pkl par run
            save_trace: Sauvegarder trace JSON par run
            verbose: Logger progression
            scenario_ui: Scénario UI (Pessimiste, Standard, Optimiste) ou None → moyen
            variabilite_ui: Variabilité UI (Faible, Moyenne, Forte) ou None → Moyenne
            debug_prints: Si True, affiche des prints (événements graves, positifs, microzones > 6)
        """
        base = output_dir or PathResolver.get_project_root() / "data" / "intermediate"
        microzone_ids = self._microzone_ids_or_load()
        config_dict = self.config.model_dump()
        scenario_config, variabilite_locale, scenario_key, variabilite_label = (
            _resolve_run_params(self.config, scenario_ui, variabilite_ui)
        )

        for run_idx in range(runs):
            self._run_one_headless_iteration(
                run_idx=run_idx,
                runs=runs,
                days=days,
                base=base,
                microzone_ids=microzone_ids,
                scenario_config=scenario_config,
                variabilite_locale=variabilite_locale,
                scenario_key=scenario_key,
                variabilite_label=variabilite_label,
                save_pickles=save_pickles,
                save_trace=save_trace,
                verbose=verbose,
                debug_prints=debug_prints,
                on_vectors_progress=None,
            )

    VECTORS_PRINT_INTERVAL = 10000  # Print sample every ~10000 vectors (console)

    def _run_one_headless_iteration(
        self,
        run_idx: int,
        runs: int,
        days: int,
        base: Path,
        microzone_ids: List[str],
        scenario_config: Dict[str, Any],
        variabilite_locale: float,
        scenario_key: str,
        variabilite_label: str,
        save_pickles: bool,
        save_trace: bool,
        verbose: bool,
        debug_prints: bool,
        on_vectors_progress: Optional[Any] = None,
    ) -> None:
        """Une itération headless : un run complet, sauvegarde pickle/trace, optionnel callback vecteurs."""
        run_id = f"run_{run_idx:03d}"
        if verbose:
            logger.info(
                "Run %s/%s (%s jours) — scénario=%s, variabilité=%s",
                run_idx + 1, runs, days, scenario_key, variabilite_label,
            )

        state = SimulationState(run_id=run_id, config=self.config.model_dump())
        state.dynamic_state.ensure_microzones(microzone_ids)

        seed_run = self._seed + run_idx
        limites_mz_arr = _limites_microzone_arrondissement_or_parse(microzone_ids)
        arrondissements = sorted(set(limites_mz_arr.values()))
        realaléatoirisation_config = {}
        if getattr(self.config, "realaléatoirisation", None) is not None:
            realaléatoirisation_config = self.config.realaléatoirisation.model_dump()
        from src.core.state.realaléatoirisation_state import generate_realaléatoirisation_patterns
        state.realaléatoirisation_state = generate_realaléatoirisation_patterns(
            arrondissements=arrondissements,
            num_days=days,
            microzone_to_arrondissement=limites_mz_arr,
            config=realaléatoirisation_config,
            seed=seed_run,
        )
        lissage_alpha = (
            self.config.vecteurs_statiques.lissage_alpha
            if self.config.vecteurs_statiques is not None
            else 0.7
        )
        reduction_base = 0.80
        if getattr(self.config, "matrices_base", None) is not None:
            reduction_base = self.config.matrices_base.reduction_effet
        elif getattr(self.config, "realaléatoirisation", None) is not None:
            rb = getattr(self.config.realaléatoirisation, "reduction_base_matrices", None)
            if rb is not None:
                reduction_base = rb
        reduction_effet_patterns = (
            self.config.effets_patterns.reduction_effet
            if getattr(self.config, "effets_patterns", None) is not None
            else 0.8
        )
        gen = GenerationService(
            microzone_ids=microzone_ids,
            seed=seed_run,
            scenario_config=scenario_config,
            variabilite_locale=variabilite_locale,
            debug_prints=debug_prints,
            lissage_alpha=lissage_alpha,
            reduction_base_matrices=reduction_base,
            reduction_effet_patterns=reduction_effet_patterns,
        )
        gen.set_realaléatoirisation_state(state.realaléatoirisation_state)

        # Callback : compteur de vecteurs (~1 par microzone par jour), print échantillon tous les 10000
        total_vectors = [0]  # mutable pour closure

        def on_day_completed(day: int, sim_state: SimulationState) -> None:
            total_vectors[0] += len(microzone_ids)
            if total_vectors[0] >= self.VECTORS_PRINT_INTERVAL:
                if on_vectors_progress is not None:
                    on_vectors_progress(total_vectors[0], sim_state)
                total_vectors[0] = 0
                # Échantillon : quelques vecteurs au hasard (run_id, jour, microzone, types)
                import random as _r
                mz_sample = _r.choice(microzone_ids) if microzone_ids else None
                if mz_sample is not None and hasattr(sim_state, "vectors_state"):
                    vecs = sim_state.vectors_state.get_vectors_for_day(mz_sample, day)
                    if vecs:
                        sample = {k: (v.to_list()[:5] if hasattr(v, "to_list") else str(v)[:80]) for k, v in list(vecs.items())[:3]}
                        print(
                            f"[Simulation] ~10000 vecteurs générés — run_id={sim_state.run_id} jour={day} "
                            f"microzone={mz_sample} échantillon={sample}"
                        )
                    else:
                        dyn = getattr(sim_state.dynamic_state, "incidents_alcool", {})
                        sample = dict(list(dyn.get(mz_sample, {}).items())[:3]) if isinstance(dyn, dict) else {}
                        print(
                            f"[Simulation] ~10000 vecteurs générés — run_id={sim_state.run_id} jour={day} "
                            f"microzone={mz_sample} dynamic_sample={sample}"
                        )

        gen.generate_multiple_days(
            state, start_day=0, num_days=days,
            on_day_completed=on_day_completed,
        )

        run_dir = base / run_id
        if save_pickles or save_trace:
            run_dir.mkdir(parents=True, exist_ok=True)

        if save_pickles:
            pkl_path = run_dir / "simulation_state.pkl"
            state.save(str(pkl_path))
            if verbose:
                logger.info("  → %s", pkl_path)

        if save_trace:
            trace = {
                "run_id": run_id,
                "days": days,
                "completed": True,
                "final_day": state.current_day,
                "scenario": scenario_key,
                "variabilite": variabilite_label,
                "variabilite_locale": variabilite_locale,
                "seed": seed_run,
            }
            trace_path = run_dir / "trace.json"
            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(trace, f, indent=2)
            if verbose:
                logger.info("  → %s", trace_path)

    def run_single_headless_run(
        self,
        run_idx: int,
        days: int,
        output_dir: Optional[Path] = None,
        save_pickles: bool = True,
        save_trace: bool = True,
        scenario_ui: Optional[str] = None,
        variabilite_ui: Optional[str] = None,
        verbose: bool = False,
        debug_prints: bool = False,
        console_vector_prints: bool = True,
    ) -> None:
        """
        Exécute un seul run headless (pour boucle UI : afficher Run 2/50, 3/50, ...).
        Même logique qu'une itération de run_headless, avec prints console tous les ~10000 vecteurs si demandé.
        """
        base = output_dir or PathResolver.get_project_root() / "data" / "intermediate"
        microzone_ids = self._microzone_ids_or_load()
        config_dict = self.config.model_dump()
        scenario_config, variabilite_locale, scenario_key, variabilite_label = (
            _resolve_run_params(self.config, scenario_ui, variabilite_ui)
        )
        self._run_one_headless_iteration(
            run_idx=run_idx,
            runs=50,
            days=days,
            base=base,
            microzone_ids=microzone_ids,
            scenario_config=scenario_config,
            variabilite_locale=variabilite_locale,
            scenario_key=scenario_key,
            variabilite_label=variabilite_label,
            save_pickles=save_pickles,
            save_trace=save_trace,
            verbose=verbose,
            debug_prints=debug_prints,
            on_vectors_progress=None,
        )

    def run_one(
        self,
        days: int,
        run_id: str = "run_000",
        scenario_ui: Optional[str] = None,
        variabilite_ui: Optional[str] = None,
        output_dir: Optional[Path] = None,
        save_pickles: bool = False,
        save_trace: bool = False,
        debug_prints: bool = False,
    ) -> SimulationState:
        """
        Exécute un seul run (pour usage UI).
        Retourne l'état de simulation après M jours.

        Args:
            days: Nombre de jours
            run_id: Identifiant du run
            scenario_ui: Scénario UI (Pessimiste, Standard, Optimiste) ou None → moyen
            variabilite_ui: Variabilité UI (Faible, Moyenne, Forte) ou None → Moyenne
            output_dir: Dossier de sortie (défaut: data/intermediate)
            save_pickles: Sauvegarder simulation_state.pkl
            save_trace: Sauvegarder trace.json (scenario, variabilité, etc.)
            debug_prints: Si True, affiche des prints (événements graves, positifs, microzones > 6)

        Returns:
            SimulationState à jour
        """
        microzone_ids = self._microzone_ids_or_load()
        config_dict = self.config.model_dump()
        scenario_config, variabilite_locale, scenario_key, variabilite_label = (
            _resolve_run_params(self.config, scenario_ui, variabilite_ui)
        )

        state = SimulationState(run_id=run_id, config=config_dict)
        state.dynamic_state.ensure_microzones(microzone_ids)

        # Story 2.4.3.4 : patterns de réaléatoirisation déterminés à l'avance (reproductibles)
        limites_mz_arr = _limites_microzone_arrondissement_or_parse(microzone_ids)
        arrondissements = sorted(set(limites_mz_arr.values()))
        realaléatoirisation_config = {}
        if getattr(self.config, "realaléatoirisation", None) is not None:
            realaléatoirisation_config = self.config.realaléatoirisation.model_dump()
        from src.core.state.realaléatoirisation_state import (
            RealaléatoirisationState,
            generate_realaléatoirisation_patterns,
        )
        state.realaléatoirisation_state = generate_realaléatoirisation_patterns(
            arrondissements=arrondissements,
            num_days=days,
            microzone_to_arrondissement=limites_mz_arr,
            config=realaléatoirisation_config,
            seed=self._seed,
        )

        lissage_alpha = (
            self.config.vecteurs_statiques.lissage_alpha
            if self.config.vecteurs_statiques is not None
            else 0.7
        )
        reduction_base = 0.80
        if getattr(self.config, "matrices_base", None) is not None:
            reduction_base = self.config.matrices_base.reduction_effet
        elif getattr(self.config, "realaléatoirisation", None) is not None:
            rb = getattr(self.config.realaléatoirisation, "reduction_base_matrices", None)
            if rb is not None:
                reduction_base = rb
        reduction_effet_patterns = (
            self.config.effets_patterns.reduction_effet
            if getattr(self.config, "effets_patterns", None) is not None
            else 0.8
        )
        gen = GenerationService(
            microzone_ids=microzone_ids,
            seed=self._seed,
            scenario_config=scenario_config,
            variabilite_locale=variabilite_locale,
            debug_prints=debug_prints,
            lissage_alpha=lissage_alpha,
            reduction_base_matrices=reduction_base,
            reduction_effet_patterns=reduction_effet_patterns,
        )
        gen.set_realaléatoirisation_state(state.realaléatoirisation_state)
        gen.generate_multiple_days(state, start_day=0, num_days=days)
        # Cache pour advance_one_day (même run, RNG préservé)
        self._cached_gen = gen
        self._cached_gen_run_id = state.run_id

        if save_pickles or save_trace:
            base = output_dir or PathResolver.get_project_root() / "data" / "intermediate"
            run_dir = base / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            if save_pickles:
                pkl_path = run_dir / "simulation_state.pkl"
                state.save(str(pkl_path))
            if save_trace:
                trace = {
                    "run_id": run_id,
                    "days": days,
                    "completed": True,
                    "final_day": state.current_day,
                    "scenario": scenario_key,
                    "variabilite": variabilite_label,
                    "variabilite_locale": variabilite_locale,
                    "seed": self._seed,
                }
                trace_path = run_dir / "trace.json"
                with open(trace_path, "w", encoding="utf-8") as f:
                    json.dump(trace, f, indent=2)

        return state

    def advance_one_day(
        self,
        state: SimulationState,
        scenario_ui: Optional[str] = None,
        variabilite_ui: Optional[str] = None,
        debug_prints: bool = False,
    ) -> None:
        """
        Avance l'état de simulation d'un jour (pour UI : simulation graphique jour par jour).

        Args:
            state: État de simulation à jour (sera modifié)
            scenario_ui: Scénario UI (Pessimiste, Standard, Optimiste) ou None
            variabilite_ui: Variabilité UI (Faible, Moyenne, Forte) ou None
            debug_prints: Si True, affiche des prints
        """
        microzone_ids = self._microzone_ids_or_load()
        scenario_config, variabilite_locale, _, _ = _resolve_run_params(
            self.config, scenario_ui, variabilite_ui
        )
        from src.core.generation.generation_service import GenerationService
        lissage_alpha = (
            self.config.vecteurs_statiques.lissage_alpha
            if self.config.vecteurs_statiques is not None
            else 0.7
        )
        reduction_base = 0.80
        if getattr(self.config, "matrices_base", None) is not None:
            reduction_base = self.config.matrices_base.reduction_effet
        elif getattr(self.config, "realaléatoirisation", None) is not None:
            rb = getattr(self.config.realaléatoirisation, "reduction_base_matrices", None)
            if rb is not None:
                reduction_base = rb
        reduction_effet_patterns = (
            self.config.effets_patterns.reduction_effet
            if getattr(self.config, "effets_patterns", None) is not None
            else 0.8
        )
        # Réutiliser le GenerationService entre les jours pour préserver l'état du RNG
        if (
            self._cached_gen is not None
            and self._cached_gen_run_id == state.run_id
        ):
            gen = self._cached_gen
            gen.set_realaléatoirisation_state(
                getattr(state, "realaléatoirisation_state", None)
            )
        else:
            gen = GenerationService(
                microzone_ids=microzone_ids,
                seed=self._seed,
                scenario_config=scenario_config,
                variabilite_locale=variabilite_locale,
                debug_prints=debug_prints,
                lissage_alpha=lissage_alpha,
                reduction_base_matrices=reduction_base,
                reduction_effet_patterns=reduction_effet_patterns,
            )
            if getattr(state, "realaléatoirisation_state", None) is not None:
                gen.set_realaléatoirisation_state(state.realaléatoirisation_state)
            self._cached_gen = gen
            self._cached_gen_run_id = state.run_id
        day = state.current_day
        gen.generate_day(day, state)
        state.current_day = day + 1
