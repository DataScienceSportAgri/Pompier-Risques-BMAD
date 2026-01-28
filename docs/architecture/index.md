# Architecture Shards Index - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Auteur:** Architect (Winston)

---

## Vue d'Ensemble

Ce document indexe tous les shards d'architecture (BMAD v4) pour navigation rapide.

**Document principal:** `docs/architecture.md` (vue d'ensemble complète)

---

## Shards Disponibles

### 1. Testing Strategy

**Fichier:** `docs/architecture/testing-strategy.md`

**Contenu:** Stratégie de tests validée (70% couverture, composants critiques, tests unitaires par domaine, etc.)

**Quand consulter:** Pour implémenter les tests, comprendre la stratégie validée.

---

### 2. Data Flow

**Fichier:** `docs/architecture/dataflow.md`

**Contenu:** Flux de données complets du système (simulation jour-à-jour, multi-runs, ML, erreurs, UI)

**Quand consulter:** Pour comprendre les flux de données, intégration entre composants.

---

### 3. Simulation State

**Fichier:** `docs/architecture/simulation-state.md`

**Contenu:** Détails du refactoring SimulationState (domaines séparés, structure, séparation features/labels)

**Quand consulter:** Pour implémenter SimulationState, comprendre la structure refactorée.

---

### 4. Error Handling

**Fichier:** `docs/architecture/error-handling.md`

**Contenu:** Gestion d'erreurs complète (CheckpointManager, ErrorHandler, RunRecoveryManager)

**Quand consulter:** Pour implémenter gestion d'erreurs, reprise après crash.

---

### 5. UI Reactive

**Fichier:** `docs/architecture/ui-reactive.md`

**Contenu:** UI réactive avec hover/tooltips (StateManager thread-safe, polling non-bloquant)

**Quand consulter:** Pour implémenter UI réactive, interaction pendant simulation.

---

### 6. Config Validation

**Fichier:** `docs/architecture/config-validation.md`

**Contenu:** Validation configuration au démarrage (ConfigValidator avec Pydantic)

**Quand consulter:** Pour implémenter validation config, éviter erreurs runtime.

---

### 7. Benchmarks

**Fichier:** `docs/architecture/benchmarks.md`

**Contenu:** Benchmarks et performance (métriques, outils, exemples)

**Quand consulter:** Pour valider performance, identifier bottlenecks.

---

### 8. Review

**Fichier:** `docs/architecture/review.md`

**Contenu:** Review critique de l'architecture (points forts, faibles, risques, recommandations)

**Quand consulter:** Pour comprendre les points d'attention, risques identifiés.

---

## Navigation BMAD

Les agents BMAD chargent automatiquement les shards pertinents selon le contexte :
- **Stories de tests** → `testing-strategy.md`
- **Stories de robustesse** → `error-handling.md`
- **Stories UI** → `ui-reactive.md`
- **Stories performance** → `benchmarks.md`
- **Stories SimulationState** → `simulation-state.md`

---

**Fin du document**
