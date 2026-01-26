# 🚀 SESSION 5.1 - VISION FUTURE : Extensibilité et Innovations
## First Principles + Blue Sky - Partie 1

**Date:** 25 Janvier 2026  
**Statut:** ✅ Complété  
**Objectif:** Clarifier vision, principes, innovations clés

---

# 🎯 RÉPONSES SESSION 5.1

## 1. CADRAGE INITIAL

### Q1.1 - Vision "North Star" (6-12 mois) ✅

**Réponse:** Données générées remplaçables par vraies données BSPP

**Points clés:**
- ✅ **Séparation claire** entre features hebdo (générées) et features mensuelles (réelles BSPP)
- ✅ **Features hebdo** doivent ressembler à ce qu'un responsable parisien peut accéder quotidiennement/hebdomadairement
- ✅ **Objectif:** Détecter patterns dangereux avec ML : "Avec ces 4 semaines qui se sont suivies, selon les alentours, on arrive à quelque chose de dangereux en termes de temps"

**Réflexion sur features hebdo:**
- Actuellement: Sum bénin/moyen, Sum grave (6 features)
- À repenser: Qu'est-ce qu'un responsable parisien peut accéder réellement ?
- Avec événements: Calculer autres choses avec les événements pour que features hebdo ressemblent à données accessibles

### Q1.4 - Sortie Attendue ✅

**Réponse:** Retour sur tout ce qui a été dit, enlever incertitudes, avoir un fichier technique propre pour spécifications

**Objectif:** Document technique complet sans incertitudes pour passer à l'implémentation

---

## 2. FIRST PRINCIPLES (Fondations)

### Q2.1 - Principe Produit ✅

**Réponse:** **Aide à la décision**

- L'outil sert d'abord à **aider à la décision**
- Génération données réalistes pour l'instant (pas d'accès vraies données)
- Vraies données quand recruté plus tard

### Q2.2 - Principe Données ✅

**Réponse:** Génération réaliste pour l'instant, vraies données plus tard

- **Pour l'instant:** Génération avec modèles les plus réalistes possibles
- **Plus tard:** Vraies données BSPP quand recruté
- **Séparation claire:** Features hebdo (générées) vs Features mensuelles (réelles)

### Q2.3 - Principe Modèle ML ✅

**Réponse:** **Interprétabilité prioritaire** (pas performance)

**Raison:**
- Seulement **2500 données** (50 runs × 50 semaines)
- Pas assez de données pour performance optimale
- Priorité: **Interprétabilité** (RandomForest, SHAP)
- Performance viendra avec plus de données

### Q2.4 - Principe Validation ✅

**Réponse:** Relancer un run et utiliser un modèle déjà entraîné

**Méthode:**
- Relancer un run avec paramètres différents
- Utiliser modèle déjà entraîné (enregistré)
- Comparer: Est-ce que le modèle fonctionne mieux avec nouveaux paramètres ?
- **C'est le point d'enregistrer les modèles** : Comparer performances selon paramètres

---

## 3. BLUE SKY (Innovations)

### Q3.1 - Fonctionnalité "Wow" #1 ✅

**Réponse:** Pouvoir utiliser un modèle enregistré

**Points clés:**
- **Différenciation claire** entre entraînement et utilisation
- Souvent on mélange tout (features, données, etc.)
- **Fonctionnalité wow:** Utiliser modèle enregistré pour voir comment il fonctionne
- **SHAP values:** Voir importance des 10 features (explicabilité)

### Q3.2 - Explicabilité ✅

**Réponse:** SHAP values pour voir importance des features

- Voir quelles features sont importantes
- Comprendre comment le modèle fonctionne
- Différencier ce qu'on peut recalculer quand on utilise un modèle (vs entraînement)

### Q3.4 - Boucle Rétroactive Positive ✅

**Réponse:** Oui, très bon

- Politique publique
- Renforts
- Fin travaux
- Tous ces éléments sont pertinents

---

## 4. EXTENSIBILITÉ TECHNIQUE

### Q4.1 - Architecture Plugins ✅

**Réponse:** **Oui, très important**

- Architecture modulaire pour brancher nouveaux modulateurs
- Exemple: Chômage, météo, etc.
- **Sans toucher au cœur** du système
- **Point 13 très important**

### Q4.2 - Format Données Phase 2 ✅

**Réponse:** Ne sait pas quelles données on aura

- Flexible selon données disponibles
- Pipeline + validation + mapping si nécessaire
- S'adaptera selon données réelles BSPP

### Q4.3 - Traçabilité ✅

**Réponse:** Oui, journal complet serait bien, mais pas trop compliqué

**Points:**
- Journal complet (seed, paramètres, événements) = bien
- **Seed:** Utilisation horloge processeur (pas besoin de choses compliquées)
- Pas trop compliqué à mettre en place
- Utile pour rejouer exactement un run

---

## 5. ENTRAÎNEMENT ML (Détails Techniques)

### Q5.1 - Paramètres Modifiables pour N Runs ✅

**Réponse:** Exactement les mêmes paramètres que le run initial

**Clarification:**
- **49 runs supplémentaires** (car premier run déjà lancé et affiché)
- **Mêmes paramètres:** Scénario, variabilité, durée, etc.
- **Même scénario** en reprenant au 1er janvier
- **Données statiques** identiques
- Relance un run complet: génère données journalières, hebdo, labels, puis entraîne

### Q5.2 - Critère d'Arrêt Entraînement ✅

**Réponse:** Exactement N runs (déterministe)

- Toujours exactement le nombre choisi (50 par défaut)
- Pas d'early stopping
- Déterministe et prévisible

### Q5.3 - Métriques Évaluation ✅

**Réponse:** Graphiques de base créés à la fin de l'entraînement

- Ne sait pas encore exactement quelle métrique prioriser
- **Graphiques de base** créés à la fin de l'entraînement
- À déterminer selon résultats

### Q5.5 - Versioning Modèles ✅

**Réponse:** Sauvegarder autant de modèles que de runs lancés

**Points clés:**
- **Chaque run** = nouveau modèle sauvegardé
- **Nouveau numéro** à chaque fois (incrémentation)
- **Architecture:** Deux dossiers (regression, classification)
- **Nom fichier:** Algo utilisé + numéro + paramètres simulation + hyperparamètres
- **Objectif:** Pouvoir faire des **comparaisons** entre modèles
- **Différenciation:** Chaque modèle différencié par numéro et paramètres

**Exemple:**
- `RandomForest_001_scenario-moyen_variabilite-0.5_duree-90_hyperparams-xxx.joblib`
- `RandomForest_002_scenario-pessimiste_variabilite-0.7_duree-90_hyperparams-xxx.joblib`

---

# 📋 SYNTHÈSE DÉCISIONS SESSION 5.1

## Vision North Star
- ✅ Données générées remplaçables par vraies données BSPP
- ✅ Séparation claire features hebdo (générées) vs mensuelles (réelles)
- ✅ Features hebdo = données accessibles responsables parisiens (quotidien/hebdo)

## First Principles
- ✅ **Produit:** Aide à la décision
- ✅ **Données:** Génération réaliste → vraies données plus tard
- ✅ **Modèle ML:** Interprétabilité prioritaire (2500 données seulement)
- ✅ **Validation:** Comparer modèles enregistrés avec paramètres différents

## Innovations Clés
- ✅ **Fonctionnalité "Wow":** Utiliser modèle enregistré + SHAP values
- ✅ **Explicabilité:** SHAP pour importance features
- ✅ **Boucle rétroactive positive:** Oui (politique, renforts, travaux)

## Extensibilité
- ✅ **Architecture plugins:** Très important (modulateurs sans toucher cœur)
- ✅ **Format données Phase 2:** Flexible selon données disponibles
- ✅ **Traçabilité:** Journal complet (seed = horloge processeur, simple)

## Entraînement ML
- ✅ **49 runs supplémentaires** (premier déjà lancé)
- ✅ **Mêmes paramètres** que run initial
- ✅ **Chaque run = nouveau modèle** sauvegardé avec numéro incrémenté
- ✅ **Nom fichier:** Algo + numéro + paramètres simulation + hyperparamètres
- ✅ **Objectif:** Comparaisons entre modèles

---

# ⚠️ POINTS À CLARIFIER (Session 5.2)

## Features Hebdo à Repenser
- ⏳ Qu'est-ce qu'un responsable parisien peut accéder réellement ?
- ⏳ Calculer autres choses avec événements pour features hebdo
- ⏳ Rendre features hebdo plus réalistes (accessibles quotidiennement/hebdomadairement)

## Métriques Évaluation
- ⏳ Quelles métriques exactes dans graphiques de base ?
- ⏳ Comment décider si modèle est "bon" ?

## Split Données
- ⏳ Train/Val/Test ou Cross-Validation ?

---

**Créé:** 25 Janvier 2026  
**Statut:** ✅ Complété  
**Prochaine étape:** Session 5.2 (Questions approfondies)
