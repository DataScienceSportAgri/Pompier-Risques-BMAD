# Philosophie du Format Pickle Standardisé

**Version** : 1.0  
**Date** : 28 Janvier 2026

---

## Principes Fondamentaux

### 1. Structure Standardisée

Tous les fichiers pickle du projet suivent une structure standardisée pour garantir :
- **Compatibilité** : Lecture/écriture cohérente
- **Traçabilité** : Métadonnées pour comprendre l'origine et la version
- **Maintenabilité** : Facilite la migration et l'évolution du format

### 2. Structure Exacte

```python
{
    'data': ...,              # Données réelles (structure spécifique selon type)
    'metadata': {
        'version': str,       # Version du format (ex: "1.0")
        'created_at': datetime,  # Timestamp création
        'run_id': str,       # ID du run (si applicable, None sinon)
        'description': str,  # Description courte du contenu
        'type': str,         # Type de données (ex: "vectors", "congestion", "features", "labels", "simulation_state")
        'schema_version': str  # Version du schéma de données (si applicable)
    }
}
```

### 3. Types de Données

#### 3.1 SimulationState
- **Type** : `"simulation_state"`
- **Data** : Objet `SimulationState` (VectorsState, EventsState, CasualtiesState, RegimeState)
- **Usage** : Sauvegarde état d'urgence (interruption) ou état final

#### 3.2 Vecteurs
- **Type** : `"vectors"`
- **Data** : DataFrame ou dict avec vecteurs journaliers par microzone
- **Usage** : Vecteurs générés (Story 2.2.1)

#### 3.3 Congestion
- **Type** : `"congestion"`
- **Data** : DataFrame ou dict avec taux de ralentissement par microzone par jour
- **Usage** : Table congestion (Story 2.2.2.5)

#### 3.4 Features
- **Type** : `"features"`
- **Data** : DataFrame avec 18 features hebdomadaires par arrondissement
- **Usage** : Features calculées (Story 2.2.5)

#### 3.5 Labels
- **Type** : `"labels"`
- **Data** : DataFrame avec labels mensuels (score, classes)
- **Usage** : Labels calculés (Story 2.2.6)

#### 3.6 Modèles ML
- **Type** : `"ml_model"`
- **Data** : Modèle entraîné (joblib ou pickle)
- **Usage** : Modèles ML sauvegardés (Story 2.3.x)

### 4. Conventions de Nommage

#### 4.1 Fichiers Source Data (Epic 1)
```
data/source_data/{nom}_{version}.pkl
```
Exemples :
- `vecteurs_statiques_1.0.pkl`
- `congestion_statique_1.0.pkl`
- `prix_m2_1.0.pkl`
- `distances_caserne_microzone_1.0.pkl`

#### 4.2 Fichiers Intermediate (Epic 2)
```
data/intermediate/run_{run_id}/{type}/{nom}.pkl
```
Exemples :
- `data/intermediate/run_001/generation/vecteurs.pkl`
- `data/intermediate/run_001/generation/congestion.pkl`
- `data/intermediate/run_001/ml/features.pkl`
- `data/intermediate/run_001/ml/labels.pkl`
- `data/intermediate/run_001/state/simulation_state.pkl`

#### 4.3 Fichiers Safe State (Interruption)
```
data/safe_state/run_{run_id}_day_{day}.pkl
```
Exemple :
- `data/safe_state/run_001_day_150.pkl`

### 5. Métadonnées Obligatoires

Tous les fichiers pickle DOIVENT contenir :
- `version` : Version du format pickle (actuellement "1.0")
- `created_at` : Timestamp de création (datetime ISO format)
- `type` : Type de données (voir section 3)
- `description` : Description courte (ex: "Vecteurs journaliers pour 100 microzones")

Métadonnées optionnelles :
- `run_id` : ID du run (si applicable)
- `schema_version` : Version du schéma de données (si applicable)
- `config_hash` : Hash de la configuration utilisée (pour traçabilité)

### 6. Helpers Python

#### 6.1 Sauvegarde
```python
from src.core.utils.pickle_utils import save_pickle_standardized

# Sauvegarde avec format standardisé
save_pickle_standardized(
    data=my_data,
    filepath="data/intermediate/run_001/generation/vecteurs.pkl",
    data_type="vectors",
    description="Vecteurs journaliers pour 100 microzones",
    run_id="001"
)
```

#### 6.2 Chargement
```python
from src.core.utils.pickle_utils import load_pickle_standardized

# Chargement avec validation
data, metadata = load_pickle_standardized(
    filepath="data/intermediate/run_001/generation/vecteurs.pkl"
)
```

### 7. Validation

#### 7.1 Vérifications au Chargement
- Structure dict avec 'data' et 'metadata'
- Métadonnées obligatoires présentes
- Type de données cohérent avec le fichier
- Version format compatible

#### 7.2 Gestion Versions
- Version actuelle : "1.0"
- Migration automatique si version < "1.0" (si nécessaire)
- Erreur si version > version supportée

### 8. Exemples

#### 8.1 Exemple SimulationState
```python
{
    'data': SimulationState(...),  # Objet SimulationState
    'metadata': {
        'version': '1.0',
        'created_at': datetime(2026, 1, 28, 10, 30, 0),
        'run_id': '001',
        'description': 'État simulation jour 150',
        'type': 'simulation_state',
        'schema_version': '2.0'
    }
}
```

#### 8.2 Exemple Vecteurs
```python
{
    'data': DataFrame(...),  # DataFrame avec colonnes [microzone, jour, type, gravite, count]
    'metadata': {
        'version': '1.0',
        'created_at': datetime(2026, 1, 28, 10, 30, 0),
        'run_id': '001',
        'description': 'Vecteurs journaliers pour 100 microzones',
        'type': 'vectors'
    }
}
```

#### 8.3 Exemple Congestion Statique
```python
{
    'data': DataFrame(...),  # DataFrame avec colonnes [microzone, congestion_base, saisonnalite]
    'metadata': {
        'version': '1.0',
        'created_at': datetime(2026, 1, 28, 10, 30, 0),
        'run_id': None,  # Pas de run_id pour données pré-calculées
        'description': 'Congestion statique de base par microzone',
        'type': 'congestion'
    }
}
```

---

## Migration et Évolution

### Changements de Version
- **Version 1.0** : Format initial standardisé
- **Futures versions** : Ajout de champs métadonnées, modification structure (avec migration automatique)

### Compatibilité
- Lecture rétroactive : Support des anciennes versions (si nécessaire)
- Migration automatique : Conversion vers version actuelle au chargement

---

**Document de référence** : À utiliser par toutes les stories nécessitant sauvegarde/chargement pickle.
