# Convention de Nommage des Fichiers

**Version** : 1.0  
**Date** : 29 Janvier 2026

---

## Principes

Tous les fichiers du projet suivent une convention de nommage standardisée pour faciliter :
- **Maintenance** : Localisation rapide des fichiers
- **Cohérence** : Structure prévisible
- **Traçabilité** : Identification claire du contenu et de la version

---

## Fichiers Pickle

### Source Data (Epic 1 - Pré-calculs)

**Format** : `{nom}_{version}.pkl`

**Emplacement** : `data/source_data/`

**Exemples** :
- `microzones_1.0.pkl`
- `vecteurs_statiques_1.0.pkl`
- `congestion_statique_1.0.pkl`
- `prix_m2_1.0.pkl`
- `distances_caserne_microzone_1.0.pkl`
- `distances_microzone_hopital_1.0.pkl`
- `matrices_correlation_inter_type_1.0.pkl`
- `matrices_correlation_intra_type_1.0.pkl`
- `matrices_voisin_1.0.pkl`
- `matrices_saisonnalite_1.0.pkl`
- `matrices_trafic_1.0.pkl`
- `matrices_alcool_nuit_1.0.pkl`
- `regles_patterns_1.0.pkl`
- `regles_effet_augmentation_1.0.pkl`

### Intermediate Data (Epic 2 - Simulation)

**Format** : `data/intermediate/run_{run_id}/{type}/{nom}.pkl`

**Types de dossiers** :
- `generation/` : Vecteurs, congestion, événements générés
- `ml/` : Features, labels, modèles
- `state/` : États de simulation

**Exemples** :
- `data/intermediate/run_001/generation/vecteurs.pkl`
- `data/intermediate/run_001/generation/congestion.pkl`
- `data/intermediate/run_001/generation/events.pkl`
- `data/intermediate/run_001/ml/features.pkl`
- `data/intermediate/run_001/ml/labels.pkl`
- `data/intermediate/run_001/ml/model_rf_001.joblib`
- `data/intermediate/run_001/state/simulation_state.pkl`

### Safe State (Interruption/Reprise)

**Format** : `data/safe_state/run_{run_id}_day_{day}.pkl`

**Exemples** :
- `data/safe_state/run_001_day_150.pkl`
- `data/safe_state/run_002_day_300.pkl`

### Models (ML)

**Format** : `{algo}_{numero}_{params}.joblib` ou `.pkl`

**Emplacement** : `data/models/`

**Exemples** :
- `rf_001_default.joblib`
- `xgb_001_tuned.joblib`
- `ridge_001_alpha0.1.joblib`

---

## Fichiers JSON

### Patterns

**Format** : `{pattern_name}.json`

**Emplacement** : `data/patterns/`

**Exemples** :
- `pattern_7j_example.json`
- `pattern_4j_example.json`
- `pattern_60j_example.json`

### Trace (Run)

**Format** : `trace.json`

**Emplacement** : `data/intermediate/run_{run_id}/`

**Champs (paramètres de run, voir orchestration-parametres-run-architect) :**
- `scenario` (string) : clé config `pessimiste` | `moyen` | `optimiste`
- `variabilite` (string) : libellé UI `Faible` | `Moyenne` | `Forte`
- `variabilite_locale` (number) : valeur utilisée en génération 0.3 | 0.5 | 0.7
- `seed` (number) : seed du run (reproductibilité)
- `run_id`, `days`, `completed`, `final_day` : inchangés

**Exemples** :
- `data/intermediate/run_001/trace.json`

---

## Fichiers YAML

### Configuration

**Format** : `{name}.yaml`

**Emplacement** : `config/`

**Exemples** :
- `config.yaml` (configuration principale)

---

## Fichiers Python

### Scripts

**Format** : `{action}_{target}.py` (snake_case)

**Emplacement** : `scripts/`

**Exemples** :
- `precompute_distances.py`
- `precompute_matrices_correlation.py`
- `precompute_vectors_static.py`
- `run_simulation.py`

---

## Utilisation du PathResolver

Tous les chemins doivent être résolus via `PathResolver` :

```python
from src.core.utils.path_resolver import PathResolver

# Chemins source data
path = PathResolver.data_source("microzones_1.0.pkl")

# Chemins patterns
path = PathResolver.data_patterns("pattern_7j_example.json")

# Chemins intermediate
path = PathResolver.data_intermediate("run_001", "generation", "vecteurs.pkl")

# Chemins models
path = PathResolver.data_models("rf_001_default.joblib")

# Chemins config
path = PathResolver.config_file("config.yaml")

# Chemin générique
path = PathResolver.resolve("data", "source_data", "microzones.pkl")
```

---

## Notes

- Tous les chemins sont **relatifs à la racine du projet**
- Utiliser `PathResolver` pour garantir la cohérence
- Respecter les conventions de nommage pour faciliter la maintenance
- Versionner les fichiers source data avec `_{version}`
