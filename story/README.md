# Stories - Pompier-Risques-BMAD

Ce dossier contient toutes les user stories du projet, organisées par Epic.

## Epic 1 : Pré-calculs

- [1.1 - Infrastructure et script unique de pré-calcul](1.1-infrastructure-precompute.md)
- [1.2 - Pré-calcul des distances et 100 microzones](1.2-precompute-distances-microzones.md)
- [1.3 - Pré-calcul vecteurs statiques et prix m²](1.3-precompute-vectors-static-prix.md)

## Epic 2 : Système de Simulation et Prédiction

### Bloc 2.1 — Infra

- [2.1.1 - Infrastructure de base et structure de projet](2.1.1-infrastructure-base.md)

### Bloc 2.2 — Génération

**Ordre d'implémentation** : 2.2.1 → 2.2.2 → **2.2.2.5** → **2.2.9** → **2.2.10** → 2.2.3 → 2.2.4 → 2.2.5 → 2.2.6 → 2.2.7 → 2.2.8

- [2.2.1 - Génération vecteurs journaliers (Étape 1)](2.2.1-generation-vecteurs-journaliers.md)
- [2.2.2 - Vecteurs alcool/nuit et patterns (Étape 2)](2.2.2-vecteurs-alcool-nuit-patterns.md)
- [2.2.2.5 - Pré-calcul taux de ralentissement de trafic](2.2.2.5-precalcul-taux-ralentissement-trafic.md)
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

- Les stories marquées "*(à créer)*" doivent être créées selon le même format que les stories existantes
- Toutes les stories sont basées sur le PRD v4 et l'Architecture v2
- L'ordre d'implémentation pour le bloc 2.2 est spécifique (voir ci-dessus)
