# Review Architecture Document - Point de Vue Architect Manager

**Date:** 28 Janvier 2026  
**Reviewer:** Architect Manager (perspective critique)  
**Document reviewé:** `docs/architecture.md` v1

---

## 🟢 Points Forts

### 1. Structure et Complétude
- ✅ **Documentation complète:** Tous les aspects couverts (layers, patterns, data flow)
- ✅ **Traçabilité:** Références claires au PRD et décisions techniques
- ✅ **Diagrammes:** Mermaid utile pour visualisation
- ✅ **Exemples de code:** Concrets et actionnables

### 2. Décisions Techniques
- ✅ **Architecture hexagonale:** Choix approprié pour extensibilité (plugins, remplacement données)
- ✅ **NumPy pour calculs:** Bon choix performance
- ✅ **Dependency Injection:** Facilite tests
- ✅ **Patterns cohérents:** Strategy, Factory bien utilisés

### 3. Pragmatisme MVP
- ✅ **Direct pickle:** YAGNI respecté (pas de sur-abstraction)
- ✅ **Monolithique modulaire:** Approprié pour MVP
- ✅ **Streamlit:** Choix pragmatique pour UI rapide

---

## 🔴 Points Faibles et Risques

### 1. **CRITIQUE: SimulationState comme God Object**

**Problème:**
```python
class SimulationState:
    # 10+ responsabilités différentes
    - vectors
    - regimes
    - events_graves
    - events_positifs
    - morts
    - blesses_graves
    - features
    - labels
    # ...
```

**Risques:**
- ❌ **Violation SRP:** SimulationState fait trop de choses
- ❌ **Couplage fort:** Tous les composants dépendent de SimulationState
- ❌ **Testabilité réduite:** Difficile de tester composants isolément
- ❌ **Évolutivité:** Ajout nouvelles données = modification SimulationState partout

**Recommandation:**
```python
# Mieux: Agrégation de domaines
class SimulationState:
    def __init__(self):
        self.vectors_state = VectorsState()
        self.events_state = EventsState()
        self.casualties_state = CasualtiesState()
        self.ml_state = MLState()
```

**Impact:** 🔴 **HAUT** - Risque de dette technique importante

---

### 2. **CRITIQUE: Architecture Hexagonale Overkill pour MVP?**

**Question:** Est-ce vraiment nécessaire pour un MVP local, sans API, sans BDD?

**Risques:**
- ⚠️ **Complexité initiale:** Plus de code à écrire (interfaces, adapters)
- ⚠️ **Temps de développement:** Plus long pour livrer MVP
- ⚠️ **Over-engineering:** YAGNI violé si Phase 2 jamais atteinte

**Contre-argument valide:**
- ✅ Requirement PRD explicite: "plugins/modulateurs sans toucher le cœur"
- ✅ Phase 2: Remplacement données générées → vraies données BSPP

**Verdict:** ✅ **Justifié** mais nécessite discipline pour ne pas sur-abstraire

---

### 3. **CRITIQUE: Plugin Registry - Où est l'usage réel?**

**Problème:**
- Document décrit le pattern mais **aucun cas d'usage concret** dans le PRD
- Pas d'exemple de plugin réel nécessaire
- Risque de code mort (pattern jamais utilisé)

**Questions à poser:**
- Qui va créer des plugins? Quand? Pourquoi?
- Est-ce vraiment nécessaire en MVP?
- Phase 2 suffit?

**Recommandation:** 
- ⚠️ **Phase 2 uniquement** sauf si requirement explicite MVP
- Ou documenter **cas d'usage concret** justifiant MVP

---

### 4. **CRITIQUE: Gestion Multi-Runs - Complexité sous-estimée**

**Problème:**
```python
# Document mentionne "sauvegarde incrémentale" mais...
# - Comment gérer les erreurs pendant parallélisation?
# - Que faire si un run échoue?
# - Comment reprendre après crash?
# - Gestion mémoire: 49 runs × 200 MB = 10 GB (acceptable mais...)
```

**Risques:**
- ❌ **Pas de stratégie d'erreur:** Un run échoue → tout échoue?
- ❌ **Pas de retry:** Run silencieux échoue → perdu?
- ❌ **Pas de monitoring:** Comment savoir si runs silencieux progressent?
- ❌ **État partiel:** Run interrompu → données corrompues?

**Manques:**
- Stratégie de retry
- Gestion d'erreurs robuste
- Monitoring/observabilité
- Validation état après crash

**Impact:** 🔴 **HAUT** - Risque de perte de données, frustration utilisateur

---

### 5. **CRITIQUE: Streamlit + Simulation Temps Réel - Blocage UI**

**Problème:**
```python
# Streamlit bloque pendant calculs
for day in range(365):
    service.run_day(day)  # Bloque UI pendant 0.33s × 365 = 2 minutes
    update_ui()  # Jamais appelé pendant le calcul
```

**Risques:**
- ❌ **UI non réactive:** Streamlit bloque pendant calculs
- ❌ **Pas de vrai "temps réel":** UI se met à jour après, pas pendant
- ❌ **Stop difficile:** Comment arrêter si UI bloquée?

**Solutions possibles:**
- Threading (mais GIL limite)
- `st.rerun()` périodique (hack)
- Async/await (complexe avec Streamlit)

**Manque dans document:** ⚠️ **Pas de solution proposée**

**Impact:** 🟡 **MOYEN** - UX dégradée mais acceptable pour MVP

---

### 6. **CRITIQUE: Pas de Gestion d'Erreurs**

**Problème:**
- Aucune section sur gestion d'erreurs
- Pas de stratégie de retry
- Pas de logging structuré
- Pas de validation des données

**Exemples manquants:**
```python
# Que se passe-t-il si:
- Fichier pickle corrompu?
- Données pré-calculées manquantes?
- Modèle ML invalide?
- Erreur calcul Golden Hour?
- Run interrompu brutalement?
```

**Recommandation:**
- Section "Error Handling Strategy"
- Logging structuré (structlog ou logging standard)
- Validation données (pydantic?)
- Retry pour I/O

**Impact:** 🔴 **HAUT** - Système fragile, difficile à déboguer

---

### 7. **CRITIQUE: Performance - Pas de Benchmarks**

**Problème:**
- Objectif: ≤ 0.33s/jour
- Mais **aucune validation** que c'est réaliste
- Pas de profiling strategy
- Pas de métriques de performance

**Questions:**
- Comment mesurer si 0.33s atteint?
- Que faire si dépassé?
- Quels composants sont les bottlenecks?

**Recommandation:**
- Section "Performance Monitoring"
- Profiling strategy (cProfile, line_profiler)
- Métriques à collecter
- Plan d'action si objectif non atteint

**Impact:** 🟡 **MOYEN** - Risque de non-respect NFR

---

### 8. **CRITIQUE: Tests - Couverture Vague**

**Problème:**
```python
# Document dit: "Couverture cible: 70%+ pour composants critiques"
# Mais:
- Quels sont les "composants critiques"?
- Comment mesurer?
- Quand tester? (TDD? Après?)
- Tests d'intégration: combien?
```

**Manques:**
- Stratégie de test claire
- Définition "composants critiques"
- Outils (pytest-cov)
- CI/CD (quand tests lancés?)

**Impact:** 🟡 **MOYEN** - Qualité code incertaine

---

### 9. **CRITIQUE: Data Flow - Ordre d'Exécution Flou**

**Problème:**
```python
# Document montre séquence mais...
# - Ordre exact des opérations?
# - Dépendances entre étapes?
# - Que faire si étape échoue?
# - Rollback possible?
```

**Exemple concret:**
```python
# Story 2.2.1 → 2.2.9 → 2.2.10 → 2.2.3
# Mais dans le code, ordre réel?
```

**Manque:** Diagramme de dépendances explicite

**Impact:** 🟡 **MOYEN** - Risque d'implémentation incorrecte

---

### 10. **CRITIQUE: Configuration - Pas de Validation**

**Problème:**
```yaml
# config.yaml
scenarios:
  pessimiste:
    facteur_intensite: 1.3  # Que faire si négatif? > 10?
```

**Risques:**
- ❌ Pas de validation config au démarrage
- ❌ Erreurs découvertes en runtime
- ❌ Pas de schéma config (JSON Schema?)

**Recommandation:**
- Validation config avec pydantic
- Schéma config documenté
- Valeurs par défaut claires

**Impact:** 🟡 **MOYEN** - Erreurs runtime évitables

---

## 🟡 Points d'Attention

### 11. **Dependency Injection - Pas de Container**

**Question:**
- Comment créer les objets? Manuellement partout?
- Pas de DI container (injector, dependency-injector)?

**Risque:**
- Code répétitif pour création objets
- Difficile à maintenir si beaucoup de dépendances

**Recommandation:**
- DI container simple (ou manuel si < 10 classes)
- Factory pour création objets complexes

---

### 12. **NumPy Arrays - Conversion Overhead**

**Question:**
- Tuples → NumPy arrays: conversion à chaque fois?
- Ou garder arrays dès le début?

**Risque:**
- Overhead conversion si fait souvent
- Cohérence: tuples vs arrays?

**Recommandation:**
- Décision claire: tuples partout ou arrays partout?
- Documenter choix

---

### 13. **Golden Hour - Complexité Sous-estimée**

**Question:**
- Calcul congestion: comment modélisé?
- Stress pompiers: comment suivi?
- Performance: 100 microzones × calculs = ?

**Risque:**
- Complexité algorithmique non documentée
- Performance bottleneck potentiel

**Recommandation:**
- Algorithme détaillé dans `docs/formules.md`
- Profiling prévu

---

### 14. **ML Service - Pas de Détails**

**Question:**
- Comment prépare-t-on les 90 features?
- Fenêtres glissantes: implémentation?
- Validation données ML?

**Manque:**
- Détails préparation données ML
- Pipeline ML complet

---

### 15. **Extensibilité Phase 2 - Pas de Migration Path**

**Question:**
- Comment migrer pickle → BDD?
- Breaking changes?
- Compatibilité données?

**Manque:**
- Stratégie migration
- Plan de transition

---

## ✅ Recommandations Prioritaires

### Priorité 1 (Critique - À faire maintenant)

1. **Refactor SimulationState:**
   - Découper en domaines (VectorsState, EventsState, etc.)
   - Réduire couplage

2. **Gestion d'erreurs:**
   - Section complète "Error Handling Strategy"
   - Logging structuré
   - Retry strategy

3. **Gestion multi-runs robuste:**
   - Stratégie erreurs
   - Retry automatique
   - Monitoring

4. **Streamlit + temps réel:**
   - Solution proposée (threading? async?)
   - Ou accepter limitation et documenter

### Priorité 2 (Important - À planifier)

5. **Performance monitoring:**
   - Profiling strategy
   - Métriques à collecter
   - Benchmarks

6. **Tests:**
   - Stratégie claire
   - Définition "composants critiques"
   - CI/CD

7. **Configuration:**
   - Validation (pydantic)
   - Schéma config

### Priorité 3 (Amélioration - Phase 2)

8. **Plugin Registry:**
   - Cas d'usage concret ou Phase 2

9. **Migration path:**
   - Stratégie pickle → BDD

10. **Observabilité:**
    - Monitoring avancé
    - Métriques business

---

## 📊 Score Global

| Critère | Score | Commentaire |
|---------|-------|-------------|
| **Complétude** | 8/10 | Bien couvert mais manques critiques |
| **Cohérence** | 7/10 | Quelques incohérences (SimulationState) |
| **Pragmatisme** | 6/10 | Hexagonale peut-être overkill MVP |
| **Testabilité** | 7/10 | DI bon mais SimulationState couplé |
| **Performance** | 5/10 | Pas de stratégie monitoring |
| **Robustesse** | 4/10 | ⚠️ **CRITIQUE:** Pas de gestion erreurs |
| **Maintenabilité** | 7/10 | Structure bonne mais SimulationState problématique |
| **Extensibilité** | 8/10 | Hexagonale + plugins bien pensés |

**Score moyen: 6.5/10**

**Verdict:** 
- ✅ **Bon départ** mais **manques critiques** à adresser
- ⚠️ **Risque de dette technique** si SimulationState non refactoré
- ⚠️ **Risque de frustration** si gestion erreurs absente
- ✅ **Architecture solide** mais besoin de **robustesse opérationnelle**

---

## 🎯 Actions Immédiates Recommandées

1. **Refactor SimulationState** (1-2 jours)
2. **Ajouter section Error Handling** (0.5 jour)
3. **Détailler gestion multi-runs** (1 jour)
4. **Solution Streamlit temps réel** (0.5 jour)

**Total: ~3-4 jours de travail architecture avant implémentation**

---

**Fin du review**
