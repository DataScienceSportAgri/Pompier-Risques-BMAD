# Décisions Techniques - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Auteur:** Architect (Winston)  
**Statut:** Propositions pour validation

---

## 1. Format des Données et Sérialisation

### 1.1 Format des Pickles

**Décision:** Utiliser `pickle` standard Python avec compression `gzip` pour les fichiers volumineux.

**Structure recommandée:**
- **Petits fichiers** (< 10 MB) : `pickle` standard (`.pkl`)
- **Fichiers volumineux** (≥ 10 MB) : `pickle` compressé avec `gzip` (`.pkl.gz`)
- **Format interne:** Dictionnaires Python ou DataFrames Pandas selon le contexte

**Exemples de structures:**
```python
# Vecteurs journaliers (Story 2.2.1)
# IMPORTANT: Convention d'ordre des vecteurs (bénin, moyen, grave)
# Tous les vecteurs utilisent des tuples (int, int, int) pour économiser mémoire
# et simplifier les calculs vectoriels/matriciels
{
    'day': int,
    'microzone_id': str,
    'vectors': {
        'agressions': (int, int, int),  # (bénin, moyen, grave)
        'incendies': (int, int, int),    # (bénin, moyen, grave)
        'accidents': (int, int, int)     # (bénin, moyen, grave)
    },
    'regime': str  # 'Stable', 'Deterioration', 'Crise'
}

# Exemple concret:
vectors = {
    'agressions': (5, 2, 1),   # 5 bénins, 2 moyens, 1 grave
    'incendies': (3, 1, 0),     # 3 bénins, 1 moyen, 0 grave
    'accidents': (8, 3, 2)      # 8 bénins, 3 moyens, 2 graves
}

# Features hebdomadaires (Story 2.2.5)
DataFrame avec colonnes:
- arrondissement (int)
- semaine (int)
- feature_1 à feature_18 (float)
```

**Convention d'ordre des vecteurs:**
- **Index 0** : Bénin
- **Index 1** : Moyen
- **Index 2** : Grave

Cette convention doit être documentée dans le code (constantes, docstrings) et dans `docs/formules.md`.

**Rationale:** 
- **Économie mémoire:** Tuples plus légers que dictionnaires (pas de clés string)
- **Performance:** Accès par index O(1), opérations vectorielles numpy natives
- **Simplicité:** Calculs matriciels directs (addition, multiplication) sans conversion
- **Cohérence:** Format uniforme dans tout le système

**Exemples d'utilisation:**
```python
# Création d'un vecteur
agressions = (5, 2, 1)  # 5 bénins, 2 moyens, 1 grave

# Accès aux valeurs
benin = agressions[0]    # 5
moyen = agressions[1]    # 2
grave = agressions[2]   # 1

# Opérations vectorielles (numpy)
import numpy as np
v1 = np.array([5, 2, 1])
v2 = np.array([3, 1, 0])
somme = v1 + v2  # [8, 3, 1]

# Multiplication par facteur
facteur = 1.5
v_modifie = v1 * facteur  # [7.5, 3.0, 1.5]
```

**Documentation dans le code:**
```python
# Constantes à définir dans src/data/constants.py ou similaire
VECTOR_INDEX_BENIN = 0
VECTOR_INDEX_MOYEN = 1
VECTOR_INDEX_GRAVE = 2

# Ou utiliser un NamedTuple pour la clarté (optionnel)
from typing import NamedTuple

class Vector(NamedTuple):
    """Vecteur (bénin, moyen, grave) pour incidents."""
    benin: int
    moyen: int
    grave: int
    
# Usage: v = Vector(5, 2, 1) puis v.benin, v.moyen, v.grave
```

---

### 1.2 Format de trace.json

**Décision:** JSON standard avec structure fixe pour traçabilité.

**Structure:**
```json
{
    "run_id": "run_042",
    "timestamp_start": "2026-01-28T10:30:00Z",
    "timestamp_end": "2026-01-28T11:45:00Z",
    "seed": 12345,
    "parameters": {
        "scenario": "moyen",
        "variabilite_locale": "moyen",
        "nombre_jours": 365,
        "nombre_runs": 50
    },
    "patterns_utilises": {
        "pattern_4j": "data/patterns/pattern_4j.json",
        "pattern_7j": "data/patterns/pattern_7j.json",
        "pattern_60j": "data/patterns/pattern_60j.json"
    },
    "statistiques": {
        "jours_simules": 365,
        "evenements_graves": 12,
        "evenements_positifs": 3,
        "total_morts": 45,
        "total_blesses_graves": 120
    },
    "alertes": [
        {
            "arrondissement": 18,
            "type": "coherence",
            "message": "0 mort sur 800 jours agrégés",
            "timestamp": "2026-01-28T11:00:00Z"
        }
    ],
    "modeles_entraines": [
        {
            "algorithme": "RandomForest",
            "type": "regression",
            "fichier": "models/regression/RandomForest_001_params.yaml.joblib",
            "metriques": {"MAE": 0.23, "RMSE": 0.45, "R2": 0.78}
        }
    ]
}
```

**Rationale:** JSON est lisible, standard, et facilement parsable. Structure fixe garantit la cohérence entre runs.

---

### 1.3 Format des Patterns

**Décision:** JSON avec structure hiérarchique pour patterns 4j, 7j, 60j.

**Structure:**
```json
{
    "pattern_type": "4j",
    "description": "Pattern court-terme 4 jours",
    "jours": [
        {
            "jour": 1,
            "facteur_agressions": 1.0,
            "facteur_incendies": 1.0,
            "facteur_accidents": 1.0,
            "modification_regimes": {
                "Stable": 0.8,
                "Deterioration": 0.15,
                "Crise": 0.05
            }
        }
    ],
    "regles_generation": {
        "seuil_activation": 4,
        "type_seuil": "incidents_moyen_ou_grave",
        "facteur_multiplication": 3.5
    }
}
```

**Emplacement:** `data/patterns/pattern_4j.json`, `pattern_7j.json`, `pattern_60j.json`

**Rationale:** JSON permet de stocker des structures complexes tout en restant lisible et modifiable manuellement si besoin.

---

## 2. Sources de Données Géospatiales

### 2.1 100 Microzones

**Décision:** Utiliser les données **IRIS (Insee)** comme source principale, avec agrégation pour viser ~100 zones.

**Approche:**
1. Télécharger les données IRIS Paris depuis [data.gouv.fr](https://www.data.gouv.fr) ou [Insee](https://www.insee.fr)
2. Filtrer les IRIS parisiens (20 arrondissements)
3. Agréger les IRIS pour obtenir ~5 microzones par arrondissement (total ~100)
4. Stratégie d'agrégation: par proximité géographique (k-means clustering ou Voronoi)

**Format de sortie:** GeoJSON sauvegardé dans `data/source_data/microzones.geojson`

**Alternative si IRIS indisponible:** Grille géométrique régulière (grid 10×10) avec ajustement aux limites des arrondissements.

**Rationale:** IRIS est la source officielle, fiable, et déjà utilisée pour les statistiques parisiennes. L'agrégation permet d'atteindre le nombre cible de 100 zones.

---

### 2.2 Casernes et Hôpitaux

**Décision:** Utiliser **OpenStreetMap (OSM)** via `osmnx` pour extraire les positions des casernes et hôpitaux parisiens.

**Approche:**
1. Utiliser `osmnx` pour requêter OSM avec tags:
   - Casernes: `amenity=fire_station` + `addr:city=Paris`
   - Hôpitaux: `amenity=hospital` + `addr:city=Paris`
2. Extraire coordonnées (lat, lon) et noms
3. Sauvegarder dans `data/source_data/casernes.geojson` et `data/source_data/hopitaux.geojson`

**Alternative si OSM incomplet:** Compléter avec données Ville de Paris ([opendata.paris.fr](https://opendata.paris.fr)) ou données BSPP si disponibles.

**Rationale:** OSM est à jour, gratuit, et `osmnx` facilite l'extraction. Les tags sont standardisés.

---

### 2.3 Prix m²

**Décision:** Générer des prix m² réalistes par microzone basés sur les données publiques de la Ville de Paris.

**Approche:**
1. Source de référence: [Données foncières DVF (Demandes de Valeurs Foncières)](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/) ou [Prix m² par arrondissement INSEE](https://www.insee.fr)
2. Si données indisponibles: Générer des prix m² par arrondissement basés sur des valeurs connues (ex: 1er arrondissement ~12k€/m², 20e ~6k€/m²)
3. Interpolation par microzone selon position dans l'arrondissement
4. Sauvegarder dans `data/source_data/prix_m2.pkl` (DataFrame: microzone_id, prix_m2)

**Valeurs de référence (approximatives):**
- Arrondissements centraux (1er-4e): 10-12k€/m²
- Arrondissements périphériques (12e-20e): 5-8k€/m²
- Arrondissements intermédiaires (5e-11e): 8-10k€/m²

**Rationale:** Les données réelles sont préférables, mais la génération réaliste permet de démarrer sans dépendance externe.

---

## 3. Configuration

### 3.1 Structure du fichier config.yaml

**Décision:** YAML unique partagé entre pré-calculs et application.

**Structure:**
```yaml
# config/config.yaml

project:
  name: "Pompier-Risques-BMAD"
  version: "1.0.0"

paths:
  data_source: "data/source_data"
  data_intermediate: "data/intermediate"
  data_models: "data/models"
  data_patterns: "data/patterns"
  scripts: "scripts"
  config: "config"

simulation:
  default_days: 365
  default_runs: 50
  speed_per_day_seconds: 0.33
  seed_default: 42
  
scenarios:
  pessimiste:
    facteur_intensite: 1.3
    proba_crise: 0.15
  moyen:
    facteur_intensite: 1.0
    proba_crise: 0.10
  optimiste:
    facteur_intensite: 0.7
    proba_crise: 0.05

variabilite_locale:
  faible: 0.1
  moyen: 0.3
  important: 0.5

microzones:
  nombre_cible: 100
  source: "IRIS"  # ou "grid"
  
golden_hour:
  seuil_minutes: 60
  facteur_casualties: 1.3
  stress_pompiers_par_caserne: 30
  stress_increment_intervention: 0.4

ml:
  features_central: 18
  features_voisins: 4
  features_total: 90
  algorithms:
    regression:
      - "RandomForest"
      - "Ridge"
    classification:
      - "LogisticRegression"
      - "XGBoost"
  hyperparameters_default:
    RandomForest:
      n_estimators: 100
      max_depth: 10
    Ridge:
      alpha: 1.0
    LogisticRegression:
      C: 1.0
      max_iter: 1000
    XGBoost:
      n_estimators: 100
      max_depth: 6

validation:
  seuil_morts_min: 1
  seuil_morts_max: 500
  jours_agregation: 800

ui:
  theme: "light"
  font: "Inter"
  colors:
    feu_benin: "#FFE5B4"  # Jaune pastel
    feu_moyen: "#FFA500"   # Orange
    feu_grave: "#FF4500"   # Rouge
    accident_benin: "#F5DEB3"  # Beige
    accident_moyen: "#8B4513"  # Marron
    accident_grave: "#654321"
    agression: "#808080"   # Gris
    evenement_positif: "#90EE90"  # Vert clair
```

**Rationale:** YAML est lisible, supporte les commentaires, et permet une structure hiérarchique claire. Un seul fichier évite la duplication.

---

## 4. Arrondissements Adjacents

### 4.1 Définition en dur

**Décision:** Définir les adjacences dans un dictionnaire Python dans le code (pas de fichier externe).

**Structure:**
```python
# src/data/adjacents.py

ARRONDISSEMENTS_ADJACENTS = {
    1: [2, 3, 4, 7, 8],      # 1er arrondissement
    2: [1, 3, 9],             # 2e arrondissement
    3: [1, 2, 4, 10, 11],    # 3e arrondissement
    4: [1, 3, 11, 12],       # 4e arrondissement
    5: [6, 13, 14],          # 5e arrondissement
    6: [5, 7, 14, 15],       # 6e arrondissement
    7: [1, 6, 8, 15, 16],    # 7e arrondissement
    8: [1, 7, 9, 16, 17],    # 8e arrondissement
    9: [2, 8, 10, 17, 18],   # 9e arrondissement
    10: [3, 9, 11, 18, 19],  # 10e arrondissement
    11: [3, 4, 10, 12, 20],  # 11e arrondissement
    12: [4, 11, 20],         # 12e arrondissement
    13: [5, 14],             # 13e arrondissement
    14: [5, 6, 13, 15],      # 14e arrondissement
    15: [6, 7, 14, 16],      # 15e arrondissement
    16: [7, 8, 15, 17],      # 16e arrondissement
    17: [8, 9, 16, 18],      # 17e arrondissement
    18: [9, 10, 17, 19],     # 18e arrondissement
    19: [10, 11, 18, 20],    # 19e arrondissement
    20: [11, 12, 19]         # 20e arrondissement
}

def get_adjacents(arrondissement: int, n_voisins: int = 4) -> List[int]:
    """
    Retourne les n_voisins premiers arrondissements adjacents.
    Si moins de n_voisins disponibles, retourne tous les adjacents.
    """
    adjacents = ARRONDISSEMENTS_ADJACENTS.get(arrondissement, [])
    return adjacents[:n_voisins]
```

**Note:** Les adjacences sont basées sur la géographie réelle de Paris. Pour ML, on prend les 4 premiers voisins de la liste.

**Rationale:** Simple, performant, et évite un fichier externe pour des données statiques. Facile à maintenir et tester.

---

## 5. Intégration Streamlit + Folium

### 5.1 Méthode d'intégration

**Décision:** Utiliser `st.folium_static()` (méthode native Streamlit) en priorité.

**Code d'exemple:**
```python
import streamlit as st
import folium

# Création de la carte Folium
m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)

# Ajout des microzones, événements, etc.
# ...

# Affichage dans Streamlit
st.folium_static(m, width=700, height=500)
```

**Alternative si problème:** `st.components.v1.html()` avec `m._repr_html_()`.

**Rationale:** `st.folium_static()` est la méthode officielle Streamlit, optimisée pour l'intégration. Plus simple et maintenu.

---

## 6. Gestion Mémoire et Performance

### 6.1 Parallélisation des 50 runs

**Décision:** Utiliser `multiprocessing.Pool` pour paralléliser les 49 runs en calcul seul (pas le run affiché).

**Approche:**
```python
from multiprocessing import Pool

def run_simulation_silent(run_id: int, config: dict) -> dict:
    """Exécute un run sans UI, retourne les données ML."""
    # Simulation complète sans affichage
    # Retourne features, labels pour ce run
    pass

# Dans main.py ou orchestration
if config['nombre_runs'] > 1:
    with Pool(processes=min(4, config['nombre_runs'] - 1)) as pool:
        # Run 1 affiché à l'écran (séparé)
        # Runs 2-50 en parallèle
        results = pool.starmap(
            run_simulation_silent,
            [(i, config) for i in range(2, config['nombre_runs'] + 1)]
        )
```

**Limitation:** Maximum 4 processus en parallèle pour éviter surcharge mémoire.

**Rationale:** `multiprocessing` est natif Python, évite le GIL, et permet de tirer parti des CPU multi-cœurs.

---

### 6.2 Gestion mémoire pour 50 runs

**Décision:** Sauvegarder les données intermédiaires par run au fur et à mesure, puis les agréger pour ML.

**Stratégie:**
1. Chaque run sauvegarde ses features/labels dans `data/intermediate/run_XXX/ml/`
2. Après les 50 runs, chargement et agrégation pour entraînement ML
3. Option: Supprimer les pickles individuels après agrégation (garder seulement le run affiché)

**Code d'exemple:**
```python
# Après chaque run
features_run = calculate_features(run_data)
save_pickle(f"data/intermediate/run_{run_id}/ml/features.pkl", features_run)

# Après 50 runs
all_features = []
for run_id in range(1, 51):
    features = load_pickle(f"data/intermediate/run_{run_id}/ml/features.pkl")
    all_features.append(features)
    
# Agrégation et entraînement
df_ml = pd.concat(all_features, ignore_index=True)
train_models(df_ml)
```

**Rationale:** Évite de garder 50 runs en mémoire simultanément. Permet reprise après interruption.

---

## 7. Métadonnées Modèles ML

### 7.1 Format de sauvegarde

**Décision:** Utiliser `joblib` pour les modèles, avec fichier YAML séparé pour métadonnées.

**Structure:**
```
models/
├── regression/
│   ├── RandomForest_001_20260128_103045.joblib
│   ├── RandomForest_001_20260128_103045.yaml
│   └── Ridge_002_20260128_103045.joblib
└── classification/
    ├── LogisticRegression_001_20260128_103045.joblib
    └── XGBoost_002_20260128_103045.joblib
```

**Format YAML métadonnées:**
```yaml
# RandomForest_001_20260128_103045.yaml
model:
  algorithme: "RandomForest"
  type: "regression"
  numero_entrainement: 1
  timestamp: "2026-01-28T10:30:45Z"
  
entrainement:
  nombre_runs: 50
  nombre_jours_par_run: 365
  seed: 12345
  scenario: "moyen"
  variabilite_locale: "moyen"
  
hyperparametres:
  n_estimators: 100
  max_depth: 10
  random_state: 42
  
metriques:
  MAE: 0.23
  RMSE: 0.45
  R2: 0.78
  
features:
  nombre_total: 90
  features_central: 18
  features_voisins: 72
  
donnees:
  nombre_echantillons: 18250  # 50 runs × 365 jours
  nombre_arrondissements: 20
```

**Rationale:** `joblib` est optimisé pour scikit-learn. YAML séparé permet de lire les métadonnées sans charger le modèle.

---

## 8. Hyperparamètres ML par défaut

### 8.1 Valeurs fixes MVP

**Décision:** Hyperparamètres conservateurs mais performants.

**Valeurs:**
```python
HYPERPARAMETERS_DEFAULT = {
    'RandomForest': {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42,
        'n_jobs': -1
    },
    'Ridge': {
        'alpha': 1.0,
        'solver': 'auto',
        'random_state': 42
    },
    'LogisticRegression': {
        'C': 1.0,
        'max_iter': 1000,
        'random_state': 42,
        'solver': 'lbfgs'
    },
    'XGBoost': {
        'n_estimators': 100,
        'max_depth': 6,
        'learning_rate': 0.1,
        'random_state': 42,
        'n_jobs': -1
    }
}
```

**Rationale:** Valeurs standards de la littérature, équilibrées entre performance et temps d'entraînement. Phase 2 pourra optimiser avec GridSearch.

---

## 9. Structure des Données Intermédiaires par Run

### 9.1 Organisation des pickles

**Décision:** Structure de dossiers claire avec un fichier par type de données.

**Structure:**
```
data/intermediate/run_042/
├── generation/
│   ├── vecteurs_base.pkl          # Vecteurs journaliers bruts
│   ├── vecteurs_proportions.pkl    # Proportions alcool/nuit
│   └── regimes.pkl                 # Historique des régimes
├── events/
│   ├── evenements_graves.pkl       # DataFrame événements graves
│   ├── evenements_positifs.pkl    # DataFrame événements positifs
│   └── incidents.pkl              # DataFrame tous incidents
├── golden_hour/
│   ├── temps_trajets.pkl          # Temps trajets par jour
│   └── stress_pompiers.pkl         # Stress par caserne
├── ml/
│   ├── features_hebdo.pkl         # 18 features par semaine
│   ├── labels_mensuels.pkl        # Labels (score + classes)
│   └── features_ml_90.pkl        # 90 features format ML (central + voisins)
├── casualties/
│   ├── morts.pkl                   # Morts par type, par semaine
│   └── blesses_graves.pkl         # Blessés graves par type, par semaine
└── trace.json                     # Métadonnées du run
```

**Format des DataFrames:**
- `vecteurs_base.pkl`: DataFrame avec colonnes `[day, microzone_id, type_incident, vector_tuple]`
  - `vector_tuple`: tuple `(bénin, moyen, grave)` - voir convention section 1.1
  - Alternative: colonnes `[day, microzone_id, agressions, incendies, accidents]` où chaque type est un tuple `(bénin, moyen, grave)`
- `features_hebdo.pkl`: DataFrame avec colonnes `[arrondissement, semaine, feature_1, ..., feature_18]`
- `labels_mensuels.pkl`: DataFrame avec colonnes `[arrondissement, mois, score, classe]`

**Rationale:** Séparation claire par fonctionnalité, facilite le débogage et la reprise après interruption.

---

## 10. Propagation Directionnelle

### 10.1 Implémentation

**Décision:** Implémenter la propagation directionnelle comme modulation des matrices de transition, pas comme modification directe des vecteurs.

**Approche:**
```python
def apply_directional_propagation(
    event: EventGrave,
    microzones: List[str],
    direction: str,  # 'bas', 'gauche', 'droite', 'haut'
    days: int = 3
) -> Dict[str, float]:
    """
    Modifie les matrices de transition pour les microzones
    dans la direction spécifiée pendant 'days' jours.
    """
    affected_zones = get_zones_in_direction(
        event.microzone, direction, microzones
    )
    
    # Modulation des matrices (pas remplacement)
    for zone in affected_zones:
        transition_matrix[zone] *= factor_propagation
        # Factor décroît avec distance et temps
```

**Rationale:** La propagation via matrices préserve la cohérence du modèle et évite les effets indésirables mentionnés dans Story 2.5.1.

---

## 11. Tests et Validation

### 11.1 Structure des tests

**Décision:** Utiliser `pytest` avec structure de dossiers miroir de `src/`.

**Structure:**
```
tests/
├── conftest.py                    # Fixtures partagées
├── test_data/
│   ├── test_vectors.py
│   └── test_features.py
├── test_golden_hour/
│   └── test_golden_hour.py
├── test_ml/
│   ├── test_preparation.py
│   ├── test_entrainement.py
│   └── test_shap.py
├── test_events/
│   └── test_events.py
└── integration/
    └── test_workflow_complet.py
```

**Fixtures communes:**
```python
# tests/conftest.py
import pytest
import pandas as pd

@pytest.fixture
def sample_config():
    """Config de test minimale."""
    return {
        'nombre_jours': 7,
        'scenario': 'moyen',
        'variabilite_locale': 'moyen'
    }

@pytest.fixture
def sample_microzones():
    """5 microzones de test."""
    return ['MZ_001', 'MZ_002', 'MZ_003', 'MZ_004', 'MZ_005']
```

**Rationale:** `pytest` est moderne, flexible, et supporte bien les fixtures. Structure miroir facilite la navigation.

---

## 12. Documentation Technique

### 12.1 Structure des documents

**Décision:** Créer 3 documents techniques principaux comme spécifié dans Story 2.5.2.

**Fichiers:**
1. `docs/architecture.md` - Architecture système complète
2. `docs/formules.md` - Formules mathématiques et matrices
3. `docs/modele-j1-et-generation.md` - Explication du modèle J+1 et génération

**Format:** Markdown avec diagrammes Mermaid pour les flux.

**Rationale:** Séparation claire des préoccupations. Markdown est versionnable et lisible.

---

## 13. Points à Valider avec l'Équipe

### 13.1 Décisions nécessitant validation

1. **Sources de données:** Confirmer disponibilité IRIS et OSM pour casernes/hôpitaux
2. **Prix m²:** Valider approche génération vs données réelles
3. **Parallélisation:** Valider nombre de processus (4 proposé)
4. **Hyperparamètres:** Valider valeurs par défaut avec data scientist
5. **Format patterns:** Valider structure JSON proposée

---

## 14. Résumé des Décisions

| Point | Décision | Fichier/Emplacement |
|-------|----------|---------------------|
| **Format vecteurs** | **Tuples (bénin, moyen, grave)** | **Convention documentée section 1.1** |
| Format pickles | Pickle standard + gzip si >10MB | `data/source_data/`, `data/intermediate/` |
| Format trace.json | JSON structuré | `data/intermediate/run_XXX/trace.json` |
| Format patterns | JSON hiérarchique | `data/patterns/pattern_*.json` |
| 100 microzones | IRIS (Insee) agrégé | `data/source_data/microzones.geojson` |
| Casernes/hôpitaux | OSM via osmnx | `data/source_data/casernes.geojson` |
| Prix m² | Génération réaliste par arrondissement | `data/source_data/prix_m2.pkl` |
| Config | YAML unique | `config/config.yaml` |
| Adjacents | Dictionnaire Python en dur | `src/data/adjacents.py` |
| Streamlit+Folium | `st.folium_static()` | `src/ui/web_app.py` |
| Parallélisation | `multiprocessing.Pool` (max 4) | `main.py` |
| Métadonnées ML | YAML séparé + joblib | `models/*/model_*.yaml` |
| Hyperparamètres | Valeurs conservatrices | `config/config.yaml` |
| Tests | pytest, structure miroir | `tests/` |

---

**Fin du document**
