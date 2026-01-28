# SimulationState Refactoring - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Auteur:** Architect (Winston)  
**Statut:** Validé

---

## Vue d'Ensemble

Ce document décrit le refactoring de SimulationState pour découpler en domaines indépendants.

**Problème initial:** SimulationState était un God Object avec 10+ responsabilités.

**Solution:** Découpage en domaines spécialisés (Composition + Aggregate Root).

---

## Structure Refactorée

### SimulationState (Aggregate Root)

```python
# src/core/state/simulation_state.py
from .vectors_state import VectorsState
from .events_state import EventsState
from .casualties_state import CasualtiesState
from .regime_state import RegimeState

class SimulationState:
    """
    État global de la simulation (Aggregate Root).
    
    ⚠️ IMPORTANT: SimulationState contient UNIQUEMENT les données journalières.
    Les features (hebdomadaires) et labels (mensuels) sont calculés et stockés
    séparément par les services FeatureCalculator et LabelCalculator.
    """
    
    def __init__(self, run_id: str, config: dict):
        self.run_id = run_id
        self.config = config
        self.current_day: int = 0
        
        # Domaines spécialisés (composition) - DONNÉES JOURNALIÈRES UNIQUEMENT
        self.vectors_state = VectorsState()          # Vecteurs journaliers
        self.events_state = EventsState()            # Événements journaliers
        self.casualties_state = CasualtiesState()     # Casualties (agrégés par semaine)
        self.regime_state = RegimeState()            # Régimes par microzone
```

---

## Domaines Composants

### 1. VectorsState

**Responsabilité:** Gestion des vecteurs d'incidents par microzone.

**Structure:** `{day: {microzone_id: {type_incident: (bénin, moyen, grave)}}}`

**Méthodes principales:**
- `update_vectors(day, microzone_id, incident_type, vector)`
- `get_vectors(day, microzone_id)`
- `get_history(microzone_id, incident_type, days)`
- `get_total_incidents(day, microzone_id)`

**Voir code complet dans `architecture-simulation-state-refactor.md` section 1.**

---

### 2. EventsState

**Responsabilité:** Gestion des événements graves et positifs.

**Structure:** Listes d'événements + index par jour pour accès rapide.

**Méthodes principales:**
- `add_grave_event(event)`
- `add_positive_event(event)`
- `get_events_for_day(day)`
- `get_active_events(current_day)`

**Voir code complet dans `architecture-simulation-state-refactor.md` section 2.**

---

### 3. CasualtiesState

**Responsabilité:** Gestion des morts et blessés graves.

**Structure:** `{semaine: {arrondissement: {type_incident: count}}}`

**Méthodes principales:**
- `add_morts(semaine, arrondissement, incident_type, count)`
- `add_blesses_graves(semaine, arrondissement, incident_type, count)`
- `get_morts_semaine(semaine, arrondissement)`
- `get_total_morts(arrondissement)`

**Voir code complet dans `architecture-simulation-state-refactor.md` section 3.**

---

### 4. RegimeState

**Responsabilité:** Gestion des régimes cachés (Stable, Détérioration, Crise).

**Structure:** `{microzone_id: 'Stable'|'Deterioration'|'Crise'}`

**Méthodes principales:**
- `set_regime(microzone_id, regime, day)`
- `get_regime(microzone_id)`
- `get_transitions(microzone_id, days)`

**Voir code complet dans `architecture-simulation-state-refactor.md` section 5.**

---

## Séparation Features/Labels

**⚠️ IMPORTANT:** Features et labels ne font PAS partie de SimulationState.

**Raison:**
- SimulationState = données journalières uniquement
- Features = agrégation hebdomadaire (7 jours) → calculées par `FeatureCalculator`
- Labels = agrégation mensuelle (4 semaines) → calculés par `LabelCalculator`

**Stockage:**
- Features: `data/intermediate/run_XXX/ml/features_hebdo.pkl`
- Labels: `data/intermediate/run_XXX/ml/labels_mensuels.pkl`

**Voir `architecture-simulation-state-refactor.md` section "Séparation Features/Labels" pour détails.**

---

## Avantages du Refactoring

1. **Séparation des Responsabilités (SRP):** Chaque domaine a une responsabilité unique
2. **Testabilité Améliorée:** Tests isolés par domaine
3. **Réduction du Couplage:** Composants dépendent de domaines spécifiques
4. **Évolutivité:** Ajout nouvelles données = nouveau domaine
5. **Réutilisabilité:** Domaines utilisables indépendamment

---

## Migration Path

1. **Créer domaines** (sans casser l'existant)
2. **Migrer progressivement** (wrappers de compatibilité)
3. **Supprimer ancien code** (après migration complète)

**Voir `architecture-simulation-state-refactor.md` section "Migration Path" pour détails.**

---

**Fin du document**
