# Performance Benchmarks - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Auteur:** Architect (Winston)  
**Statut:** Validé

---

## Vue d'Ensemble

Ce document décrit les benchmarks suggérés pour valider les performances du système.

**Objectifs:**
- Validation performance 0.33s/jour (NFR2)
- Identification bottlenecks
- Optimisation ciblée

---

## Métriques à Mesurer

### 1. Génération Jour

**Cible:** ≤ 0.33s par jour

**Benchmark:**
```python
# tests/benchmarks/benchmark_simulation.py
import pytest
from src.services.simulation_service import SimulationService

@pytest.mark.benchmark
def test_benchmark_day_generation(benchmark):
    """Benchmark génération d'un jour."""
    service = SimulationService(...)
    state = SimulationState(...)
    
    def run_day():
        service.run_day(1)
    
    result = benchmark(run_day)
    
    # Validation: < 0.33s
    assert result.stats.mean < 0.33, f"Trop lent: {result.stats.mean}s"
```

---

### 2. Golden Hour

**Cible:** Temps calcul acceptable pour 100 microzones

**Benchmark:**
```python
@pytest.mark.benchmark
def test_benchmark_golden_hour(benchmark):
    """Benchmark calcul Golden Hour (100 microzones)."""
    golden_hour = GoldenHourCalculator(...)
    vectors = generate_test_vectors(100)  # 100 microzones
    
    def calculate():
        return golden_hour.calculate(day=1, vectors=vectors, state=state)
    
    result = benchmark(calculate)
    # Pas de seuil strict, mais identifier bottleneck
```

---

### 3. Features

**Cible:** Temps calcul 18 features pour 20 arrondissements

**Benchmark:**
```python
@pytest.mark.benchmark
def test_benchmark_features(benchmark):
    """Benchmark calcul 18 features (20 arrondissements)."""
    calculator = FeatureCalculator(...)
    state = generate_7_days_state()
    
    def calculate():
        return calculator.calculate_features(semaine=1, state=state)
    
    result = benchmark(calculate)
```

---

### 4. ML

**Cible:** Temps entraînement 4 modèles sur 50 runs

**Benchmark:**
```python
@pytest.mark.benchmark
def test_benchmark_ml_training(benchmark):
    """Benchmark entraînement 4 modèles (50 runs)."""
    ml_service = MLService(...)
    dataset = load_50_runs_dataset()
    
    def train():
        return ml_service.train_all_models(dataset)
    
    result = benchmark(train)
    # Identifier temps total et par modèle
```

---

### 5. Parallélisation

**Cible:** Speedup ~4× pour 49 runs parallèles vs séquentiel

**Benchmark:**
```python
@pytest.mark.benchmark
def test_benchmark_parallelization(benchmark):
    """Benchmark parallélisation 49 runs."""
    # Séquentiel
    def sequential():
        for i in range(2, 51):
            run_simulation_silent(i, config)
    
    # Parallèle
    def parallel():
        with Pool(processes=4) as pool:
            pool.starmap(run_simulation_silent, [(i, config) for i in range(2, 51)])
    
    seq_result = benchmark(sequential)
    par_result = benchmark(parallel)
    
    speedup = seq_result.stats.mean / par_result.stats.mean
    assert speedup > 3.0, f"Speedup insuffisant: {speedup}x (attendu ~4x)"
```

---

## Outils Recommandés

### pytest-benchmark

**Usage:** Benchmarks automatisés dans tests

```python
# Installation
pip install pytest-benchmark

# Exécution
pytest tests/benchmarks/ --benchmark-only
```

---

### cProfile

**Usage:** Profiling détaillé (fonctions appelées)

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code à profiler
service.run_day(1)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 fonctions
```

---

### line_profiler

**Usage:** Profiling ligne par ligne

```python
# Installation
pip install line_profiler

# Décorateur
@profile
def run_day(self, day: int):
    # ...

# Exécution
kernprof -l -v script.py
```

---

### memory_profiler

**Usage:** Usage mémoire

```python
# Installation
pip install memory-profiler

# Décorateur
@profile
def run_day(self, day: int):
    # ...

# Exécution
python -m memory_profiler script.py
```

---

## Stratégie de Benchmarking

**MVP:** Tests manuels occasionnels
- Profiling à la demande si problèmes
- Validation 0.33s/jour manuelle

**Phase 2:** Benchmarks automatisés
- Intégration dans CI/CD
- Alertes si dégradation

---

**Fin du document**
