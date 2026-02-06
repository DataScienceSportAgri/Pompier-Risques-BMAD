# Stories - Pompier-Risques-BMAD

Ce dossier contient toutes les user stories du projet, organisées par Epic.

## Epic 1 : Pré-calculs

- [1.1 - Infrastructure et script unique de pré-calcul](1.1-infrastructure-precompute.md)
- [1.2 - Pré-calcul des distances et 100 microzones](1.2-precompute-distances-microzones.md)
- [1.3 - Pré-calcul vecteurs statiques, prix m² et congestion statique](1.3-precompute-vectors-static-prix.md)
- [1.4.4.1 - Pré-calcul matrices de corrélation fixes](1.4.4.1-precompute-matrices-correlation.md)
- [1.4 - Fichier de référence patterns Paris](1.4-patterns-reference.md)

## Epic 2 : Système de Simulation et Prédiction

### Bloc 2.1 — Infra

- [2.1.1 - Infrastructure de base et structure de projet](2.1.1-infrastructure-base.md)
- [2.1.2 - Structure SimulationState avec domaines spécialisés](2.1.2-simulation-state-structure.md)
- [2.1.3 - Validation configuration avec Pydantic](2.1.3-validation-config-pydantic.md)
- [2.1.4 - Système centralisé de résolution de chemins](2.1.4-chemins-centralises.md)

### Bloc 2.2 — Génération

**Ordre d'implémentation** : 2.2.1 (vecteurs) → 2.2.2 (patterns) → **2.2.9** (matrices) → **2.2.10** (vecteurs statiques) → **2.2.2.5** (congestion) → 2.2.3 (Golden Hour) → 2.2.4 (morts/blessés) → 2.2.5 (features) → 2.2.6 (labels) → 2.2.7 (événements graves) → 2.2.8 (événements positifs)

**Stories découpage 1.4.4 (matrices et patterns)** :
- [1.4.4.2 - Évolution Variables d'État Dynamiques](1.4.4.2-evolution-variables-etat.md)
- [1.4.4.3 - Application Matrices Fixes aux Probabilités](1.4.4.3-application-matrices-fixes.md)
- [1.4.4.4 - Intégration Variables d'État dans Calcul Probabilités](1.4.4.4-integration-variables-etat.md)
- [1.4.4.5 - Détection et Gestion Patterns Dynamiques](1.4.4.5-detection-patterns-dynamiques.md)
- [1.4.4.6 - Application Patterns dans Calcul Probabilités](1.4.4.6-application-patterns.md)

**Ordre d'implémentation découpage 1.4.4** : 1.4.4.2 → 1.4.4.3 (peut être en parallèle avec 1.4.4.5) → 1.4.4.4 → 1.4.4.6

- [2.2.1 - Génération vecteurs journaliers (Étape 1)](2.2.1-generation-vecteurs-journaliers.md)
- [2.2.2 - Vecteurs alcool/nuit et patterns (Étape 2)](2.2.2-vecteurs-alcool-nuit-patterns.md)
- [2.2.2.5 - Calcul taux de ralentissement de trafic (congestion dynamique)](2.2.2.5-calcul-taux-ralentissement-trafic.md)
- [2.2.3 - Golden Hour — calculs distances et stress (Étape 3)](2.2.3-golden-hour.md)
- [2.2.4 - Morts et blessés graves hebdomadaires (Étape 4)](2.2.4-morts-blesses-hebdo.md)
- [2.2.5 - Features hebdomadaires — StateCalculator (Étape 5)](2.2.5-features-hebdo.md)
- [2.2.6 - Labels mensuels — LabelCalculator (Étape 6)](2.2.6-labels-mensuels.md)
- [2.2.7 - Événements graves modulables](2.2.7-evenements-graves.md)
- [2.2.8 - Événements positifs et règle prix m²](2.2.8-evenements-positifs-prix.md)
- [2.2.9 - Trois matrices de modulation](2.2.9-matrices-modulation.md)
- [2.2.10 - Vecteurs statiques et interface patterns Paris](2.2.10-vecteurs-statiques-patterns.md)

### Bloc 2.3 — ML

- [2.3.1 - Préparation données ML — fenêtres glissantes](2.3.1-preparation-donnees-ml.md)
- [2.3.2 - Entraînement modèles ML — régression et classification](2.3.2-entrainement-modeles-ml.md)
- [2.3.3 - SHAP values pour interprétabilité](2.3.3-shap-values.md)

### Bloc 2.4 — UI

- [2.4.1 - Interface Streamlit — layout et contrôles de base](2.4.1-interface-streamlit-layout.md)
- [2.4.2 - Orchestration (main.py, config, simulation sans UI)](2.4.2-orchestration-main.md)
- [2.4.3 - Simulation et visualisation (Lancer, Stop, minimal UI)](2.4.3-simulation-visualisation.md)
- [2.4.4 - Interface Streamlit — ML et modèles sauvegardés](2.4.4-interface-ml-modeles.md)
- [2.4.5 - Sauvegarde / reprise état simulation et export](2.4.5-sauvegarde-reprise-export.md)
- [2.4.6 - Graphiques détaillés par arrondissement (Phase 2)](2.4.6-graphiques-detaille-phase2.md)

### Bloc 2.5 — Qualité

- [2.5.1 - Validation et tests de cohérence](2.5.1-validation-tests-coherence.md)
- [2.5.2 - Documentation technique et utilisateur](2.5.2-documentation-technique.md)

## Notes

- Toutes les stories sont basées sur le PRD v4 et l'Architecture v2
- L'ordre d'implémentation pour le bloc 2.2 est spécifique (voir ci-dessus)
- **Story 1.4.4 découpée** : La story 1.4.4 (matrices de corrélation et patterns) a été découpée en 6 sous-stories :
  - **1.4.4.1** (Epic 1) : Pré-calcul matrices fixes
  - **1.4.4.2 à 1.4.4.6** (Epic 2) : Variables d'état, application matrices, patterns dynamiques
  - **Voir `1.4.4-DECOUPAGE-STORIES.md`** pour le découpage complet
  - **Voir `1.4.4-DIAGRAMME-DECOUPAGE.md`** pour le diagramme de flux et les dépendances
- **Ordre d'implémentation découpage 1.4.4** :
  1. 1.4.4.1 (Epic 1) : Matrices fixes
  2. 1.4.4.2 : Évolution variables d'état
  3. 1.4.4.3 et 1.4.4.5 (en parallèle) : Application matrices + Détection patterns
  4. 1.4.4.4 : Intégration variables d'état
  5. 1.4.4.6 : Application patterns
- **Voir `REORGANISATION-RESUME.md`** pour le résumé des modifications majeures
- **Voir `QUESTIONS-CLARIFICATIONS.md`** pour les questions nécessitant clarification avec le PO
