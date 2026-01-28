# Data Flow - Pompier-Risques-BMAD

**Version:** v1  
**Date:** 28 Janvier 2026  
**Auteur:** Architect (Winston)  
**Objectif:** Récapitulatif complet des flux de données du système

---

## Vue d'Ensemble

Ce document décrit tous les flux de données du système, de la génération jusqu'à la prédiction ML.

---

## 1. Flux Principal : Simulation Jour-à-Jour

### Diagramme de Séquence

```mermaid
sequenceDiagram
    participant UI as Streamlit UI
    participant SS as SimulationService
    participant VG as VectorGenerator
    participant RM as RegimeManager
    participant PM as PatternManager
    participant EM as EventManager
    participant GH as GoldenHourCalculator
    participant FC as FeatureCalculator
    participant LC as LabelCalculator
    participant STATE as SimulationState
    participant PERSIST as PersistenceAdapter
    
    UI->>SS: run_day(day)
    
    Note over SS,EM: Début journée
    SS->>EM: generate_positive_events(day)
    EM-->>SS: [PositiveEvent, ...]
    SS->>STATE.events_state: add_positive_event(event)
    SS->>EM: apply_effects(state)
    
    Note over SS,VG: Génération vecteurs
    SS->>VG: generate(day, state)
    VG->>RM: get_regimes(day, state)
    RM->>STATE.regime_state: get_regime(microzone_id)
    STATE.regime_state-->>RM: regime
    RM-->>VG: regimes
    VG->>PM: get_patterns(day)
    PM-->>VG: patterns
    VG->>VG: calculate_intensities()
    VG->>VG: generate_zip_vectors()
    VG-->>SS: vectors
    SS->>STATE.vectors_state: update_vectors(day, microzone_id, type, vector)
    
    Note over SS,GH: Golden Hour
    SS->>GH: calculate(day, vectors, state)
    GH->>GH: calculate_trajet_times()
    GH->>GH: calculate_congestion()
    GH->>GH: calculate_stress()
    GH->>GH: apply_golden_hour_effect()
    GH-->>SS: casualties
    SS->>STATE.casualties_state: add_morts(semaine, arr, type, count)
    SS->>STATE.casualties_state: add_blesses_graves(semaine, arr, type, count)
    
    Note over SS,EM: Événements graves
    SS->>EM: generate_grave_events(day, vectors)
    EM-->>SS: [EventGrave, ...]
    SS->>STATE.events_state: add_grave_event(event)
    SS->>EM: apply_effects(state)
    
    Note over SS,FC: Features (fin semaine)
    alt fin_de_semaine (day % 7 == 0)
        SS->>FC: calculate_features(semaine, state)
        FC->>STATE.vectors_state: get_vectors(7 jours)
        FC->>STATE.casualties_state: get_morts_semaine(semaine)
        FC->>FC: aggregate_vectors_week()
        FC->>FC: calculate_18_features()
        FC-->>SS: features
        SS->>PERSIST: save_features(semaine, features)
    end
    
    Note over SS,LC: Labels (fin mois)
    alt fin_de_mois (day % 28 == 0)
        SS->>LC: calculate_labels(mois, features, casualties)
        LC->>PERSIST: load_features_month(mois)
        LC->>STATE.casualties_state: get_morts_month(mois)
        LC->>LC: calculate_score()
        LC->>LC: classify()
        LC-->>SS: labels
        SS->>PERSIST: save_labels(mois, labels)
    end
    
    SS->>STATE: advance_day()
    SS->>PERSIST: save_day(day, state)
    PERSIST-->>SS: ok
    
    SS-->>UI: day_completed(day, state)
```

---

## 2. Flux Multi-Runs (50 Runs)

### Diagramme de Processus

```mermaid
graph TB
    START[Lancer Simulation<br/>50 runs]
    START --> VALIDATE[Validation Config]
    VALIDATE -->|Erreur| ERROR[Erreur Config]
    VALIDATE -->|OK| CREATE_FACTORY[SimulationFactory.create_runs]
    
    CREATE_FACTORY --> RUN_1[Run 1: Affiché UI]
    CREATE_FACTORY --> RUN_2_50[Run 2-50: Pool multiprocessing]
    
    RUN_1 --> LOOP_1[Loop jour-à-jour<br/>0.33s/jour]
    LOOP_1 --> CHECK_ERROR_1{Erreur?}
    CHECK_ERROR_1 -->|Oui| SAVE_ERROR_1[Sauvegarde état<br/>d'erreur]
    CHECK_ERROR_1 -->|Non| UPDATE_UI[Mise à jour UI<br/>Streamlit]
    UPDATE_UI --> SAVE_CHECKPOINT_1[Sauvegarde checkpoint<br/>tous les N jours]
    SAVE_CHECKPOINT_1 --> CHECK_1{365 jours<br/>terminés?}
    CHECK_1 -->|Non| LOOP_1
    CHECK_1 -->|Oui| SAVE_1[Sauvegarde run_001<br/>complet]
    
    RUN_2_50 --> POOL[multiprocessing.Pool<br/>4 processus]
    POOL --> RUN_2[Run 2]
    POOL --> RUN_3[Run 3]
    POOL --> RUN_4[Run 4]
    POOL --> RUN_5[Run 5]
    POOL --> ...[...]
    
    RUN_2 --> LOOP_2[Loop jour-à-jour<br/>Sans UI]
    LOOP_2 --> CHECK_ERROR_2{Erreur?}
    CHECK_ERROR_2 -->|Oui| RETRY[Retry automatique<br/>max 3 fois]
    RETRY -->|Échec| SAVE_ERROR_2[Sauvegarde erreur<br/>+ log]
    RETRY -->|Succès| SAVE_INCR[Sauvegarde<br/>incrémentale]
    CHECK_ERROR_2 -->|Non| SAVE_INCR
    SAVE_INCR --> CHECK_2{365 jours<br/>terminés?}
    CHECK_2 -->|Non| LOOP_2
    CHECK_2 -->|Oui| SAVE_2[Sauvegarde run_002<br/>complet]
    
    SAVE_1 --> WAIT[Attente 50 runs<br/>+ gestion erreurs]
    SAVE_2 --> WAIT
    SAVE_ERROR_1 --> WAIT
    SAVE_ERROR_2 --> WAIT
    ... --> WAIT
    
    WAIT --> CHECK_ALL{50 runs<br/>terminés?}
    CHECK_ALL -->|Non| WAIT
    CHECK_ALL -->|Oui| AGGREGATE[Agrégation features/labels<br/>50 runs]
    AGGREGATE --> VALIDATE_DATA[Validation cohérence<br/>NFR5: 1-500 morts/800j]
    VALIDATE_DATA -->|Incohérence| ALERT[Alerte utilisateur]
    VALIDATE_DATA -->|OK| TRAIN_ML[Entraînement ML<br/>4 modèles]
    TRAIN_ML --> SAVE_MODELS[Sauvegarde modèles<br/>data/models/]
    SAVE_MODELS --> END[Fin]
```

---

## 3. Flux Pré-calculs → Simulation

### Diagramme de Flux

```mermaid
graph LR
    subgraph "Epic 1: Pré-calculs"
        PRE_COMPUTE[run_precompute.py]
        PRE_COMPUTE --> MICROZONES[100 microzones<br/>GeoJSON]
        PRE_COMPUTE --> DISTANCES[Distances<br/>caserne↔microzone↔hôpital]
        PRE_COMPUTE --> VECTORS_STATIC[Vecteurs statiques<br/>3×3 par microzone]
        PRE_COMPUTE --> PRIX_M2[Prix m²<br/>par microzone]
    end
    
    subgraph "Stockage"
        SOURCE_DATA[data/source_data/]
        MICROZONES --> SOURCE_DATA
        DISTANCES --> SOURCE_DATA
        VECTORS_STATIC --> SOURCE_DATA
        PRIX_M2 --> SOURCE_DATA
    end
    
    subgraph "Epic 2: Simulation"
        SIM_START[Simulation démarre]
        SOURCE_DATA --> DATA_LOADER[DataLoaderAdapter]
        DATA_LOADER --> SIM_START
        SIM_START --> STATE[SimulationState<br/>initialisé]
    end
    
    style SOURCE_DATA fill:#99ff99
    style STATE fill:#ff9999
```

---

## 4. Flux Features et Labels

### Agrégation Hebdomadaire → Mensuelle

```mermaid
graph TB
    subgraph "Données Journalières (SimulationState)"
        VECTORS[VectorsState<br/>Vecteurs jour par jour]
        CASUALTIES[CasualtiesState<br/>Morts/blessés par semaine]
        PROPORTIONS[Proportions alcool/nuit<br/>Agrégation hebdomadaire]
    end
    
    subgraph "Agrégation Hebdomadaire"
        FC[FeatureCalculator<br/>Fin semaine]
        VECTORS -->|7 jours| FC
        CASUALTIES -->|Semaine| FC
        PROPORTIONS -->|Semaine| FC
        FC --> FEATURES[18 Features<br/>par arrondissement]
    end
    
    subgraph "Stockage Features"
        FEATURES_PKL[features_hebdo.pkl<br/>{semaine: {arr: array[18]}}]
        FEATURES --> FEATURES_PKL
    end
    
    subgraph "Agrégation Mensuelle"
        LC[LabelCalculator<br/>Fin mois 4 semaines]
        FEATURES_PKL -->|4 semaines| LC
        CASUALTIES -->|4 semaines| LC
        LC --> LABELS[Labels<br/>Score + Classe]
    end
    
    subgraph "Stockage Labels"
        LABELS_PKL[labels_mensuels.pkl<br/>{mois: {arr: {score, classe}}}]
        LABELS --> LABELS_PKL
    end
    
    style VECTORS fill:#99ccff
    style FEATURES fill:#ffcc99
    style LABELS fill:#ff99cc
```

---

## 5. Flux ML : Entraînement et Prédiction

### Entraînement (50 Runs)

```mermaid
graph TB
    subgraph "50 Runs Terminés"
        RUNS[50 runs<br/>features + labels]
    end
    
    subgraph "Agrégation"
        AGG[Agrégation features/labels<br/>50 runs]
        RUNS --> AGG
        AGG --> DATASET[Dataset ML<br/>90 features × N échantillons]
    end
    
    subgraph "Préparation"
        PREP[Préparation données<br/>Fenêtres glissantes<br/>1 central + 4 voisins]
        DATASET --> PREP
        PREP --> X_TRAIN[Features X<br/>90 colonnes]
        PREP --> Y_TRAIN[Labels y<br/>Score ou Classe]
    end
    
    subgraph "Entraînement"
        TRAIN[Entraînement 4 modèles]
        X_TRAIN --> TRAIN
        Y_TRAIN --> TRAIN
        TRAIN --> RF[RandomForest<br/>Régression]
        TRAIN --> RIDGE[Ridge<br/>Régression]
        TRAIN --> LOGREG[LogisticRegression<br/>Classification]
        TRAIN --> XGB[XGBoost<br/>Classification]
    end
    
    subgraph "Évaluation"
        EVAL[Calcul métriques]
        RF --> EVAL
        RIDGE --> EVAL
        LOGREG --> EVAL
        XGB --> EVAL
        EVAL --> METRICS[Métriques:<br/>MAE, RMSE, R²<br/>Accuracy, F1]
    end
    
    subgraph "Sauvegarde"
        SAVE[Modèles + métadonnées<br/>data/models/]
        RF --> SAVE
        RIDGE --> SAVE
        LOGREG --> SAVE
        XGB --> SAVE
        METRICS --> SAVE
    end
```

### Prédiction (1 Run)

```mermaid
graph TB
    subgraph "Chargement Modèle"
        LOAD[Charger modèle<br/>depuis data/models/]
        LOAD --> MODEL[Modèle ML<br/>chargé]
    end
    
    subgraph "Simulation 1 Run"
        SIM[Simulation jour-à-jour]
        SIM --> FEATURES_WEEK[Features semaine 5+]
    end
    
    subgraph "Prédiction"
        PRED[Prédiction semaine n+1]
        MODEL --> PRED
        FEATURES_WEEK --> PRED
        PRED --> PRED_SCORE[Score prédit<br/>ou Classe prédite]
    end
    
    subgraph "Comparaison"
        COMP[Comparaison prédiction vs réalité]
        PRED_SCORE --> COMP
        FEATURES_WEEK -->|Semaine suivante| COMP
        COMP --> RESULT[+ / -<br/>ou match / mismatch]
    end
    
    subgraph "Affichage UI"
        UI[Afficher prédiction<br/>+ résultat comparaison]
        RESULT --> UI
    end
```

---

## 6. Flux Gestion d'Erreurs et Reprise

### Gestion d'Erreurs Multi-Runs

```mermaid
graph TB
    subgraph "Run en Cours"
        RUN[Run X jour Y]
        RUN --> ERROR{Erreur?}
    end
    
    subgraph "Détection Erreur"
        ERROR -->|Oui| CATCH[Capture exception]
        ERROR -->|Non| CONTINUE[Continue]
    end
    
    subgraph "Classification Erreur"
        CATCH --> TYPE{Type erreur?}
        TYPE -->|Pickle corrompu| PICKLE_ERR[PickleError]
        TYPE -->|Données manquantes| MISSING_ERR[MissingDataError]
        TYPE -->|Calcul invalide| CALC_ERR[CalculationError]
        TYPE -->|Autre| OTHER_ERR[GenericError]
    end
    
    subgraph "Stratégie de Récupération"
        PICKLE_ERR --> RETRY_PICKLE[Retry avec backup<br/>max 3 fois]
        MISSING_ERR --> REGEN[Régénération données<br/>ou alerte]
        CALC_ERR --> SKIP_DAY[Skip jour<br/>+ log erreur]
        OTHER_ERR --> SAVE_STATE[Sauvegarde état<br/>+ arrêt]
    end
    
    subgraph "Résultat"
        RETRY_PICKLE -->|Succès| CONTINUE
        RETRY_PICKLE -->|Échec| SAVE_STATE
        REGEN -->|Succès| CONTINUE
        REGEN -->|Échec| ALERT_USER[Alerte utilisateur]
        SKIP_DAY --> CONTINUE
        SAVE_STATE --> RESUME[État sauvegardé<br/>pour reprise]
    end
```

### Reprise après Crash

```mermaid
graph TB
    START[Démarrage après crash]
    START --> CHECK[Vérifier runs existants]
    
    CHECK --> SCAN[Scanner data/intermediate/]
    SCAN --> RUNS_EXIST{Runs existants?}
    
    RUNS_EXIST -->|Oui| ANALYZE[Analyser chaque run]
    RUNS_EXIST -->|Non| NEW[Créer nouveaux runs]
    
    ANALYZE --> STATUS{Statut run?}
    STATUS -->|Complet| SKIP[Skip run]
    STATUS -->|Incomplet| RESUME[Reprendre run]
    STATUS -->|Erreur| FIX[Corriger ou recréer]
    
    RESUME --> LOAD[Charger dernier checkpoint]
    LOAD --> VALIDATE[Valider checkpoint]
    VALIDATE -->|Valide| CONTINUE[Continuer simulation]
    VALIDATE -->|Invalide| FIX
    
    FIX --> OPTIONS{Options?}
    OPTIONS -->|Régénérer| REGEN[Recréer run]
    OPTIONS -->|Ignorer| SKIP
    OPTIONS -->|Manuel| MANUAL[Intervention manuelle]
    
    CONTINUE --> END[Fin reprise]
    SKIP --> END
    REGEN --> END
    NEW --> END
```

---

## 7. Flux UI Réactive (Hover pendant Run)

### Architecture UI Réactive

```mermaid
graph TB
    subgraph "Simulation Thread"
        SIM[SimulationService<br/>run_day en cours]
        SIM --> STATE_UPDATE[Mise à jour<br/>SimulationState]
    end
    
    subgraph "State Manager"
        STATE_UPDATE --> STATE_MGR[StateManager<br/>Thread-safe]
        STATE_MGR --> QUEUE[Queue thread-safe<br/>État partagé]
    end
    
    subgraph "Streamlit UI Thread"
        UI[Streamlit UI<br/>Main thread]
        UI --> POLL[Polling état<br/>toutes les 0.1s]
        POLL --> QUEUE
        QUEUE -->|Non vide| GET_STATE[Lire état<br/>dernier jour]
        GET_STATE --> UPDATE_UI[Mise à jour UI<br/>Carte, listes, rectangles]
    end
    
    subgraph "Hover Events"
        UPDATE_UI --> HOVER[Événements hover<br/>Microzones, arrondissements]
        HOVER --> TOOLTIP[Tooltip avec infos<br/>Jour courant, vecteurs, événements]
    end
    
    style STATE_MGR fill:#99ff99
    style QUEUE fill:#ffcc99
    style HOVER fill:#99ccff
```

---

## 8. Résumé des Flux

### Tableau Récapitulatif

| Flux | Source | Destination | Fréquence | Format |
|------|--------|-------------|------------|--------|
| **Pré-calculs** | Scripts | `data/source_data/` | Une fois | Pickle/GeoJSON |
| **Vecteurs journaliers** | VectorGenerator | SimulationState.vectors_state | Chaque jour | Dict[day, microzone, type, tuple] |
| **Casualties** | GoldenHourCalculator | SimulationState.casualties_state | Chaque jour (agrégé semaine) | Dict[semaine, arr, type, count] |
| **Features** | FeatureCalculator | `data/intermediate/run_XXX/ml/` | Fin semaine | Pickle {semaine: {arr: array[18]}} |
| **Labels** | LabelCalculator | `data/intermediate/run_XXX/ml/` | Fin mois | Pickle {mois: {arr: {score, classe}}} |
| **Modèles ML** | MLService | `data/models/` | Après 50 runs | Joblib + YAML |
| **État simulation** | SimulationState | `data/intermediate/run_XXX/` | Checkpoint (tous les N jours) | Pickle |
| **UI updates** | SimulationState | Streamlit session_state | Polling 0.1s | Dict (état partagé) |

---

## 9. Points d'Intégration

### Interfaces Clés

1. **Pré-calculs → Simulation:** `DataLoaderAdapter.load_*()`
2. **Simulation → Features:** `FeatureCalculator.calculate_features(state)`
3. **Features → Labels:** `LabelCalculator.calculate_labels(features, casualties)`
4. **Labels → ML:** `MLService.prepare_dataset(features, labels)`
5. **ML → Prédiction:** `MLService.predict(model, features)`
6. **Simulation → UI:** `StateManager.get_state()` (thread-safe)

---

**Fin du document**
