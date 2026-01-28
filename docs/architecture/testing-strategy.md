# Testing Strategy - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Auteur:** Architect (Winston)  
**Statut:** Validé

---

## Vue d'Ensemble

Cette stratégie de tests est basée sur les décisions validées lors de la session de questions techniques.

**Objectifs:**
- **Couverture cible:** 70% pour composants critiques
- **Focus:** Tests unitaires par domaine (pas d'intégration pour l'instant)
- **Reproductibilité:** Seeds aléatoires (pour voir effet du hasard)
- **Validation:** Tests automatisés de cohérence après chaque run

---

## Composants Critiques à Tester

**Priorité haute (70%+ couverture):**
1. **VectorGenerator** - Génération Zero-Inflated Poisson
2. **GoldenHourCalculator** - Calcul Golden Hour
3. **FeatureCalculator** - Calcul 18 features hebdomadaires
4. **LabelCalculator** - Calcul labels mensuels
5. **SimulationService** - Orchestration simulation
6. **MLService** - Entraînement et prédiction ML

**Priorité basse (tests manuels):**
- Adapters (UI, Persistence) - Tests manuels suffisants pour MVP

---

## Types de Tests

### 1. Tests Unitaires (Par Domaine)

**Focus:** Logique métier complexe par domaine.

**Structure:**
```
tests/
├── unit/
│   ├── core/
│   │   ├── generation/
│   │   │   └── test_vector_generator.py
│   │   ├── golden_hour/
│   │   │   └── test_golden_hour.py
│   │   └── state/
│   │       ├── test_vectors_state.py
│   │       ├── test_events_state.py
│   │       └── test_casualties_state.py
│   ├── services/
│   │   ├── test_feature_calculator.py
│   │   ├── test_label_calculator.py
│   │   ├── test_simulation_service.py
│   │   └── test_ml_service.py
│   └── adapters/
│       └── (tests manuels pour MVP)
```

**Exemples:**

```python
# tests/unit/core/generation/test_vector_generator.py
import pytest
import numpy as np
import random
from src.core.generation.vector_generator import ZeroInflatedPoissonGenerator

def test_vector_generator_generates_correct_shape():
    """Test que les vecteurs ont la bonne forme."""
    # Seed aléatoire (pour voir effet du hasard)
    seed = random.randint(0, 2**32)
    generator = ZeroInflatedPoissonGenerator(..., seed=seed)
    vectors = generator.generate(day=1, state=mock_state)
    
    assert len(vectors) == 100  # 100 microzones
    for microzone_id, types in vectors.items():
        assert len(types) == 3  # 3 types incidents
        for incident_type, vector in types.items():
            assert len(vector) == 3  # (bénin, moyen, grave)
            assert all(v >= 0 for v in vector)

def test_vector_generator_regimes_distribution():
    """
    Test validation distributions et régimes (statistiques uniquement).
    
    Pas de seeds fixes avec valeurs attendues - pour voir effet du hasard.
    """
    generator = ZeroInflatedPoissonGenerator(...)
    
    # Génération sur grand nombre de jours (seeds aléatoires)
    regimes_seen = set()
    aberrant_values = []
    
    for day in range(1, 1000):
        # Seed aléatoire à chaque jour (pour voir effet du hasard)
        seed = random.randint(0, 2**32)
        vectors = generator.generate(day, state)
        
        # Vérifier présence des 3 régimes
        for microzone_id in vectors.keys():
            regime = state.regime_state.get_regime(microzone_id)
            regimes_seen.add(regime)
        
        # Vérifier pas de valeurs aberrantes
        for microzone_data in vectors.values():
            for vector in microzone_data.values():
                if sum(vector) > 1000:  # Seuil aberrant
                    aberrant_values.append(sum(vector))
    
    # Validation: les 3 régimes apparaissent (statistiques)
    assert 'Stable' in regimes_seen
    assert 'Deterioration' in regimes_seen
    assert 'Crise' in regimes_seen
    
    # Validation: pas de valeurs aberrantes
    assert len(aberrant_values) == 0, f"Valeurs aberrantes détectées: {aberrant_values}"
```

---

### 2. Tests d'Intégration

**⚠️ DÉCISION:** **Pas d'intégration pour l'instant** - Reporté à Phase 2.

**Raison:** Focus sur tests unitaires pour MVP.

---

### 3. Tests de Performance

**DÉCISION:** **Tests manuels occasionnels** pour MVP.

**Quand:** 
- Avant release MVP
- Si problèmes de performance signalés
- Profiling à la demande avec `cProfile`

**Métriques à vérifier:**
- Génération jour: ≤ 0.33s (NFR2)
- 50 runs parallèles: Temps acceptable

---

## Données de Test

### Fixtures et Données Mockées

**DÉCISION:** **Mockées + fixtures pré-calculées (A+C)**

**Approche:**
- **Mockées:** Pour tests unitaires (rapides, contrôlées)
- **Fixtures pré-calculées:** Pour tests réalistes (pickles de test)

**Structure:**
```
tests/
├── fixtures/
│   ├── test_data/
│   │   ├── microzones_test.geojson
│   │   ├── vectors_static_test.pkl
│   │   └── distances_test.pkl
│   └── conftest.py
```

**Exemple conftest.py:**
```python
# tests/fixtures/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_config():
    """Config de test minimale."""
    return {
        'nombre_jours': 7,
        'scenario': 'moyen',
        'variabilite_locale': 'moyen',
        'seed': None  # Aléatoire
    }

@pytest.fixture
def sample_microzones():
    """5 microzones de test."""
    return ['MZ_001', 'MZ_002', 'MZ_003', 'MZ_004', 'MZ_005']

@pytest.fixture
def mock_vectors_state():
    """VectorsState mocké pour tests."""
    from src.core.state.vectors_state import VectorsState
    state = VectorsState()
    # Remplir avec données de test
    return state
```

---

### Seeds Aléatoires

**DÉCISION:** **Seeds aléatoires** (pas de seeds fixes).

**Raison:** Pour voir l'effet du hasard dans les tests.

**Implémentation:**
```python
# Pas de seed fixe
import random
seed = random.randint(0, 2**32)  # Aléatoire à chaque test

# Ou seed depuis config (None = aléatoire)
seed = config.get('seed', None)
if seed is None:
    seed = random.randint(0, 2**32)
```

---

## Structure des Tests

### Organisation Hybride

**DÉCISION:** **Hybride (miroir + séparation unit/integration)**

**Structure:**
```
tests/
├── unit/                    # Tests unitaires
│   ├── core/               # Miroir de src/core/
│   │   ├── generation/
│   │   ├── golden_hour/
│   │   └── state/
│   ├── services/           # Miroir de src/services/
│   └── adapters/
├── integration/             # Tests d'intégration (Phase 2)
│   └── (vide pour MVP)
├── fixtures/                # Fixtures partagées
│   ├── test_data/
│   └── conftest.py
└── benchmarks/              # Tests performance (manuels)
    └── benchmark_simulation.py
```

---

## Validation des Données

### Assertions Simples + Tests Cohérence

**DÉCISION:** **Assertions simples + tests cohérence**

**Approche:**
- **Assertions simples:** Pour tests unitaires (valeurs, types, formes)
- **Tests cohérence:** Pour validation métier (NFR5, règles Golden Hour)

**Exemples:**

```python
# Assertions simples
def test_vectors_positive():
    """Vérifie que tous les vecteurs sont positifs."""
    vectors = generator.generate(day=1, state=state)
    for microzone_data in vectors.values():
        for vector in microzone_data.values():
            assert all(v >= 0 for v in vector), "Vecteurs doivent être positifs"

# Tests cohérence
def test_golden_hour_coherence():
    """
    Test cohérence Golden Hour: plus de morts si >60min.
    
    Séparer trajets >60min vs <60min et vérifier que sur grand nombre
    on a toujours plus de morts dans >60min.
    """
    casualties_over_60 = []
    casualties_under_60 = []
    
    # Simulation sur grand nombre de jours
    for day in range(1, 800):
        casualties = golden_hour.calculate(day, vectors, state)
        
        for microzone_id, data in casualties.items():
            temps = data['temps_total']
            morts = data['morts']
            
            if temps > 60:
                casualties_over_60.append(morts)
            else:
                casualties_under_60.append(morts)
    
    # Validation: moyenne morts >60min > moyenne morts <60min
    avg_over_60 = sum(casualties_over_60) / len(casualties_over_60) if casualties_over_60 else 0
    avg_under_60 = sum(casualties_under_60) / len(casualties_under_60) if casualties_under_60 else 0
    
    assert avg_over_60 > avg_under_60, \
        f"Golden Hour incohérent: {avg_over_60} morts >60min vs {avg_under_60} <60min"
```

---

### Validation Cohérence NFR5

**DÉCISION:** **Tests automatisés après chaque run**

**NFR5:** Par arrondissement, sur 800 jours agrégés: au moins 1 mort, moins de 500 morts.

**Implémentation:**
```python
# tests/unit/services/test_coherence_nfr5.py
def test_coherence_nfr5_after_run():
    """Valide cohérence NFR5 après un run complet."""
    # Simulation 800 jours
    for day in range(1, 801):
        service.run_day(day)
    
    # Agrégation par arrondissement
    for arrondissement in range(1, 21):
        total_morts = state.casualties_state.get_total_morts(arrondissement)
        
        # Validation NFR5
        assert total_morts >= 1, \
            f"Arrondissement {arrondissement}: 0 mort sur 800 jours (alerte)"
        assert total_morts < 500, \
            f"Arrondissement {arrondissement}: {total_morts} morts ≥ 500 (alerte)"
```

---

## Tests Spécifiques par Composant

### Tests Zero-Inflated Poisson

**DÉCISION:** **Tests statistiques uniquement** - Validation distributions et régimes, pas de seeds fixes.

**Approche:**
- Validation que les 3 régimes apparaissent (Stable, Détérioration, Crise)
- Validation distributions (pas de valeurs aberrantes)
- Pas de seeds fixes avec valeurs attendues (pour voir effet du hasard)

**Exemples:**
```python
def test_zip_regimes_presence():
    """Vérifie que les 3 régimes apparaissent (statistiques)."""
    generator = ZeroInflatedPoissonGenerator(...)
    regimes_seen = set()
    
    # Génération sur grand nombre (seed aléatoire)
    for day in range(1, 1000):
        vectors = generator.generate(day, state)
        # Extraire régimes utilisés
        for microzone_id in vectors.keys():
            regime = state.regime_state.get_regime(microzone_id)
            regimes_seen.add(regime)
    
    # Validation: les 3 régimes apparaissent
    assert 'Stable' in regimes_seen
    assert 'Deterioration' in regimes_seen
    assert 'Crise' in regimes_seen

def test_zip_no_aberrant_values():
    """Vérifie qu'il n'y a pas de valeurs aberrantes."""
    generator = ZeroInflatedPoissonGenerator(...)
    
    for day in range(1, 100):
        vectors = generator.generate(day, state)
        for microzone_data in vectors.values():
            for vector in microzone_data.values():
                # Pas de valeurs négatives
                assert all(v >= 0 for v in vector)
                # Pas de valeurs extrêmes (ex: > 1000 incidents/jour)
                assert sum(vector) < 1000, "Valeur aberrante détectée"
```

---

### Tests Golden Hour

**DÉCISION:** **Validation cohérence** - Séparer trajets >60min vs <60min, vérifier plus de morts dans >60min.

**Approche:**
- Séparer tous les trajets >60min vs <60min
- Compter morts/blessés dans chaque groupe
- Vérifier que sur grand nombre, on a toujours plus de morts dans >60min

**Exemples:**
```python
def test_golden_hour_effect_coherence():
    """
    Test cohérence effet Golden Hour.
    
    Séparer trajets >60min vs <60min et vérifier que sur grand nombre
    on a toujours plus de morts dans >60min.
    """
    golden_hour = GoldenHourCalculator(...)
    
    morts_over_60 = []
    morts_under_60 = []
    blesses_over_60 = []
    blesses_under_60 = []
    
    # Simulation sur grand nombre
    for day in range(1, 800):
        casualties = golden_hour.calculate(day, vectors, state)
        
        for microzone_id, data in casualties.items():
            temps = data['temps_total']
            morts = data['morts']
            blesses = data['blesses_graves']
            
            if temps > 60:
                morts_over_60.append(morts)
                blesses_over_60.append(blesses)
            else:
                morts_under_60.append(morts)
                blesses_under_60.append(blesses)
    
    # Validation: moyenne >60min > moyenne <60min
    avg_morts_over = sum(morts_over_60) / len(morts_over_60) if morts_over_60 else 0
    avg_morts_under = sum(morts_under_60) / len(morts_under_60) if morts_under_60 else 0
    
    assert avg_morts_over > avg_morts_under, \
        f"Golden Hour incohérent: {avg_morts_over} morts >60min vs {avg_morts_under} <60min"
    
    # Validation blessés aussi
    avg_blesses_over = sum(blesses_over_60) / len(blesses_over_60) if blesses_over_60 else 0
    avg_blesses_under = sum(blesses_under_60) / len(blesses_under_60) if blesses_under_60 else 0
    
    assert avg_blesses_over > avg_blesses_under, \
        f"Golden Hour incohérent blessés: {avg_blesses_over} >60min vs {avg_blesses_under} <60min"
```

---

### Tests ML

**DÉCISION:** **Métriques + matrices de confusion + tests prédiction automatiques**

**Approche:**
- Métriques standard (MAE, RMSE, R², Accuracy, F1)
- Matrices de confusion pour classification
- Tests de prédiction automatiques (prédiction vs réalité)

**Exemples:**
```python
def test_ml_metrics_regression():
    """Test métriques régression."""
    ml_service = MLService(...)
    model = ml_service.train_regression(X_train, y_train, algorithm='RandomForest')
    
    y_pred = model.predict(X_test)
    metrics = ml_service.calculate_metrics(y_test, y_pred, task='regression')
    
    # Validation métriques
    assert metrics['MAE'] >= 0
    assert metrics['RMSE'] >= 0
    assert 0 <= metrics['R2'] <= 1

def test_ml_confusion_matrix_classification():
    """
    Test matrice de confusion pour classification.
    
    Matrices de confusion pour visualiser performance classification.
    """
    ml_service = MLService(...)
    model = ml_service.train_classification(X_train, y_train, algorithm='XGBoost')
    
    y_pred = model.predict(X_test)
    cm = ml_service.calculate_confusion_matrix(y_test, y_pred)
    
    # Validation matrice
    assert cm.shape == (3, 3)  # 3 classes: Normal, Pre-catastrophique, Catastrophique
    assert cm.sum() == len(y_test)  # Tous échantillons classés
    
    # Visualisation (optionnel, pour analyse)
    # ml_service.plot_confusion_matrix(cm)  # Graphique simple

def test_ml_prediction_accuracy():
    """Test précision prédictions (prédiction vs réalité)."""
    ml_service = MLService(...)
    model = ml_service.load_model('models/classification/XGBoost_001.joblib')
    
    # Prédictions semaine 5+
    predictions = []
    realities = []
    
    for semaine in range(5, 10):
        features = get_features_for_week(semaine)
        pred = model.predict(features)
        predictions.append(pred)
        
        # Réalité (semaine suivante)
        reality = get_labels_for_week(semaine + 1)
        realities.append(reality)
    
    # Validation: précision acceptable
    accuracy = calculate_accuracy(predictions, realities)
    assert accuracy > 0.5, f"Précision trop faible: {accuracy}"
```

---

## Mocking

### Mocking Adapters

**DÉCISION:** **Mocking pour unitaires, réels pour intégration**

**Approche:**
- **Tests unitaires:** Mocking adapters (pickle, UI) pour isolation
- **Tests intégration (Phase 2):** Adapters réels pour réalisme

**Exemples:**
```python
# Tests unitaires: mocking
@pytest.fixture
def mock_persistence():
    """Mock PersistenceAdapter pour tests unitaires."""
    from unittest.mock import Mock
    adapter = Mock(spec=PersistenceAdapter)
    adapter.save_day.return_value = None
    adapter.load_checkpoint.return_value = mock_state
    return adapter

def test_simulation_service_unit(mock_persistence):
    """Test unitaire avec adapter mocké."""
    service = SimulationService(..., persistence=mock_persistence)
    # Test isolé, pas de vraie I/O
```

---

### Mocking Services

**DÉCISION:** **Selon contexte**

**Approche:**
- Mocking si dépendances lourdes (ex: MLService pour tests SimulationService)
- Services réels si tests rapides

---

## CI/CD et Automatisation

### CI/CD

**DÉCISION:** **Optionnel (configuré mais pas obligatoire)**

**Approche:**
- GitHub Actions configuré mais pas bloquant pour MVP
- Phase 2: CI obligatoire

---

### Pre-commit Hooks

**DÉCISION:** **Recommandation seulement (pas de blocage)**

**Approche:**
- Recommandation d'exécuter tests avant commit
- Pas de hook bloquant pour MVP

---

## Documentation des Tests

### Docstrings et README

**DÉCISION:** **Docstrings complets + README**

**Approche:**
- **Docstrings:** Chaque test documenté (objectif, approche)
- **README:** `tests/README.md` avec stratégie globale

**Exemple docstring:**
```python
def test_golden_hour_effect_coherence():
    """
    Test cohérence effet Golden Hour.
    
    Séparer TOUS les trajets >60min vs <60min et vérifier que sur grand nombre
    on a TOUJOURS plus de morts dans >60min.
    
    Voir aussi nombre de morts et blessés graves dans les deux cas.
    """
    # Voir code complet dans section "Tests Golden Hour" ci-dessus
```

**Structure README:**
```markdown
# Tests - Pompier-Risques-BMAD

## Stratégie
- Couverture: 70% composants critiques
- Focus: Tests unitaires par domaine
- Seeds: Aléatoires (pour voir effet hasard)

## Exécution
```bash
pytest tests/unit/ -v
pytest tests/unit/ --cov=src --cov-report=html
```

## Composants testés
- VectorGenerator
- GoldenHourCalculator
- FeatureCalculator
- LabelCalculator
- SimulationService
- MLService
```
```

---

## Résumé des Décisions

| Aspect | Décision | Implémentation |
|--------|----------|---------------|
| **Couverture** | 70% composants critiques | pytest-cov |
| **Composants** | 6 composants prioritaires | Tests unitaires |
| **Intégration** | Reporté Phase 2 | Pas de tests intégration MVP |
| **Performance** | Manuels occasionnels | Profiling à la demande |
| **Données** | Mockées + fixtures | conftest.py + fixtures/ |
| **Seeds** | Aléatoires | random.randint() |
| **Structure** | Hybride | tests/unit/ + tests/integration/ |
| **Validation** | Assertions + cohérence | Tests unitaires + NFR5 |
| **NFR5** | Automatisés après run | test_coherence_nfr5.py |
| **CI/CD** | Optionnel | GitHub Actions configuré |
| **Pre-commit** | Recommandation | Pas de blocage |
| **ZIP tests** | Statistiques uniquement | Validation distributions |
| **Golden Hour** | Cohérence >60min vs <60min | Tests validation effet |
| **ML tests** | Métriques + confusion + prédiction | Tests complets |
| **Mocking** | Unitaires mockés, intégration réels | Selon type test |
| **Documentation** | Docstrings + README | Complète |

---

## Prochaines Étapes

1. **Créer structure tests:**
   ```bash
   mkdir -p tests/unit/{core,services,adapters}
   mkdir -p tests/fixtures/test_data
   touch tests/conftest.py
   touch tests/README.md
   ```

2. **Créer fixtures de base:**
   - Config de test
   - Microzones mockées
   - VectorsState mocké

3. **Implémenter premiers tests:**
   - VectorGenerator (statistiques)
   - GoldenHourCalculator (cohérence)
   - FeatureCalculator (calculs)

4. **Configurer pytest:**
   - `pytest.ini` ou `pyproject.toml`
   - Coverage 70%

---

**Fin du document**
