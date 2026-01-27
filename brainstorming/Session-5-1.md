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

# 🔧 CLARIFICATIONS PRÉ-SESSION 5.2
## (26 Janvier 2026)

### 1. PRÉDICTION ML - CHANGEMENT MAJEUR ✅

**Décision:** Prédire la **semaine suivante** (pas le mois suivant)

**Structure:**
- **Entrée ML:** 4 semaines consécutives (semaines 1-4)
- **Sortie ML:** Prédiction pour la semaine suivante (semaine 5)
- **Objectif:** "Avec ces 4 semaines qui se sont suivies, selon les alentours, on arrive à quelque chose de dangereux en termes de temps"

---

### 2. 18 FEATURES HEBDOMADAIRES - STRUCTURE FINALE ✅

**Créées dans `StateCalculator` pour chaque semaine**

#### 2.1. 6 Features - Sommes Incidents par Type
Pour chaque type (accidents, incendies, agressions) :
- **Somme (moyen + grave)** = 3 features
- **Somme bénin** = 3 features

**Total:** 6 features

#### 2.2. 6 Features - Proportions (Monte-Carlo Hebdomadaire)
Générées via suite de Monte-Carlo hebdomadaire, basée sur études sciences sociales (comme les 3 vecteurs journaliers) :

- **Proportion incidents avec alcool** (par type : accidents, incendies, agressions) = 3 features
- **Proportion incidents la nuit** (incendies, agressions, accidents) = 3 features

**Total:** 6 features

#### 2.3. 3 Features - Morts Hebdomadaires
- Nombre de morts par accident
- Nombre de morts par incendie
- Nombre de morts par agression

**Calcul:**
- Utilise le **grand tableau des chemins** + **états routiers**
- Avec **GoldenHour** + **gravité des incidents plus aléatoire**
- Calcul hebdomadaire agrégé

**Total:** 3 features

#### 2.4. 3 Features - Blessés Graves Hebdomadaires
- Nombre de blessés graves par accident
- Nombre de blessés graves par incendie
- Nombre de blessés graves par agression

**Calcul:**
- Utilise les **trajets** (comme pour les morts)
- **Moins d'importance** pour la durée du trajet (GoldenHour)
- **Plus d'importance** pour la sévérité

**Total:** 3 features

**TOTAL GÉNÉRAL:** 6 + 6 + 3 + 3 = **18 features hebdomadaires**

---

### 3. CARACTÉRISTIQUES MODULABLES (Événements) ✅

**Concept:** ~15 caractéristiques modulables pouvant être générées

**Application:**
- Pour incidents **graves uniquement** (incendies, accidents, agressions)
- Créent un **objet séparé** avec :
  - **Durée d'effet aléatoire** (autour de 3 à 10 jours)
  - **Influence sur:**
    - La création des vecteurs
    - La génération aléatoire des proportions nuits/jours

**Exemples possibles:**
- Politique publique
- Renforts
- Fin travaux
- Chômage
- Météo
- etc.

**Architecture:** Système modulaire (plugins) pour ajouter de nouveaux modulateurs sans toucher au cœur

---

### 4. RÉSUMÉ CHANGEMENTS MAJEURS

| Aspect | Avant | Après |
|--------|-------|-------|
| **Prédiction** | Mois suivant 4 semaines | Semaine suivante 4 semaines |
| **Features** | 6 features (sum bénin/moyen, sum grave) | 18 features (sommes, proportions, morts, blessés) |
| **Structure** | 3 niveaux × 2 types | 2 catégories × 3 types + proportions + conséquences |
| **Calculs** | Sommes simples | Monte-Carlo + GoldenHour + trajets + sévérité |

---

**Créé:** 25 Janvier 2026  
**Clarifications:** 26 Janvier 2026  
**Statut:** ✅ Complété  
**Prochaine étape:** Session 5.2 (Questions approfondies)

---

# 🎯 RÉPONSES SESSION 5.2
## (26 Janvier 2026)

## 1. ARCHITECTURE ET IMPLÉMENTATION

### Q1.1 - StateCalculator : Structure des 18 Features ✅

**Réponse:** Calcul hebdomadaire des features dans `StateCalculator`

**Architecture:**
- **Base:** Calcul de données journalières avec les 3 vecteurs (comme dans le PDF)
- **En plus des 3 vecteurs de base:** Nécessité d'implémenter :
  - Patterns cachés qui génèrent ces valeurs (patterns hebdomadaires et 60 jours)
  - Patterns journaliers pour chaque type d'incident
  - Créer 3 valeurs à partir des vecteurs créés :
    - Nombre d'incidents (somme bénin, moyen, grave)
    - Nombre commis la nuit
    - Nombre commis sous alcool

**Structure:**
- **Méthode dédiée pour chaque catégorie de features** (sommes, proportions, morts, blessés)
- **Séparation claire:** Base de données → Calcul features hebdo → Calcul labels (différents)

---

### Q1.2 - Monte-Carlo Hebdomadaire : Implémentation ✅

**Réponse:** Génération journalière puis agrégation hebdomadaire

**Approche:**
1. **Créer proportions journalières** (alcool, nuit) pour chaque jour
2. **Compter en hebdomadaire** (somme/agrégation)
3. **Phénomène matriciel équivalent:** Corrélations entre types d'incidents
   - Exemple: Plus d'incendies la nuit → moins d'accidents la même nuit (réveil, concentration)
   - **Ordre de calcul:** D'abord incendies, puis accidents, puis agressions
   - **Effets temporels:**
     - Agressions diminuent le jour même en moyenne
     - Mais peuvent augmenter le jour suivant
     - Si proportions > 60% d'agressions pendant 3 jours → augmentation probabilité agressions pendant 1 semaine suivante (même zone + zones adjacentes)
   - **Saisonnalité:**
     - Plus de probabilité incidents la nuit en été qu'en hiver
     - En hiver pour agressions
     - Pour incendies, ce n'est pas le cas

**Générateur:**
- **Générateur séparé** pour proportions alcool/nuit
- **Réutiliser système existant** pour les vecteurs de base
- **Séparer calcul features hebdo de la base de données**

**Études sciences sociales:**
- Rester sur ce qui a été dit (corrélations, patterns temporels, saisonnalité)

---

### Q1.3 - Calcul Morts et Blessés Graves : Intégration GoldenHour ✅

**Réponse:** Calcul au niveau hebdomadaire directement

**Morts:**
- **Calcul hebdomadaire** (pas journalier puis agrégation)
- **Plus de morts = plus le trajet est long et important**
- **60% après Golden Hour** (si temps > 60 min)
- **30% de base complètement aléatoire** et non corrélé (morts sur place dans accidents très graves, sans intervention pompiers)
- **Sévérité:** Moins importante pour morts (une fois mort, c'est mort)

**Blessés Graves:**
- **Calcul hebdomadaire** directement
- **Plus lié à la randomité** que Golden Hour
- **Une fois qu'une personne n'est pas morte:**
  - Temps de trajet a moins d'impact
  - Plus le temps est long, moins de chance d'être gravement blessé
  - Mais une fois décidé qu'elle n'est pas morte → **plus de randomité** pour calculer blessé grave vs blessé moyen
- **Sévérité:** Plus importante que durée trajet pour blessés

**Code GoldenHour:**
- **À créer** (pas encore de code, brainstorming actuel)
- Utilise **grand tableau des distances** (100 casernes + 10 hôpitaux Paris)
- **Double tableau:** Microzones traversées par trajet
- **Tableau dynamique:** Taux de ralentissement trafic par microzone (variable)

**Intégration:**
- Temps de calcul + randomité → détermine si personne morte ou non
- Avec un peu plus de randomité pour blessés graves

---

## 2. CARACTÉRISTIQUES MODULABLES (Événements)

### Q2.1 - Structure des Événements ✅

**Réponse:** Classes avec caractéristiques modulables

**Structure:**
- **Événements = Classes**
- **Caractéristiques dans ces classes** qui influencent :
  - Niveau matriciel
  - Génération de données futures
  - Aspects particuliers

**Durée d'effet aléatoire (3-10 jours):**
- Caractéristiques en action pendant cette durée
- **Paramètres des caractéristiques:** Exemple +15% chance d'apparition sur 8 arrondissements
- **Effets:** Bouger une artère, augmenter dans toutes zones adjacentes, etc.

**Influence:**
- **Retour en opération possible:** Si +30% appliqué, besoin de diminution sur zones affectées après
- **Même zone:** Si +15% déjà appliqué, effet cumulatif
- **Toujours une part aléatoire:** Jamais de causalité parfaite

---

### Q2.2 - Liste des 15 Caractéristiques Modulables ✅

**Réponse:** Priorités et spécificités

**Priorités à implémenter en premier:**
- **Augmenter probabilité incidents moyen ou grave** dans zones environnantes
- **Spécificité par type:**
  - **Accidents:** Tendront à ralentir, modifier caractéristiques microzone (taux ralentissement trafic)
  - **Incendies:** Tendront à augmenter probabilités incendies dans zones adjacentes
  - **Agressions:** Tendront à augmenter probabilités agressions dans zones adjacentes

**Caractéristiques nécessaires:**
- **Chaque calcul Golden Hour** doit être défini
- **Nombre de victimes impliquées** dans chaque événement (absolument nécessaire)
- **Plus le nombre de victimes est important** → plus d'impact
- **Génération nombre de personnel déployé:** Entre 10 et 30 pour événement grave
  - **Dépeupler les pompiers** pendant un moment
  - **Augmenter dans microzones adjacentes** la matrice de calcul génération (augmenter probabilité problème)

---

### Q2.3 - Architecture Plugins pour Événements ✅

**Réponse:** Système de modulation dans génération de vecteurs

**Architecture:**
- **Fonction de génération de vecteurs** de base
- **Génération vecteurs alcool/nuit** séparée
- **Matrices internes:**
  - Inter-accident (même type)
  - Inter-zone (zones adjacentes)
  - Prendre en compte effets de tous ces nombres
- **Modulation:** Tous ces nombres doivent être **modulés par caractéristiques des événements**
- **Effets J7 et J60:** Implémentent patterns généraux

**Chargement dynamique:**
- Système de plugins pour événements (détails à préciser)

---

## 3. WORKFLOW ML ET DONNÉES

### Q3.1 - Préparation Données ML : Fenêtre Glissante ✅

**Réponse:** Fenêtres glissantes de 4 semaines

**Méthode:**
- **Dès qu'une simulation est terminée:** Semaines générées entièrement
- **Besoin d'au moins 5 semaines complètes** pour générer
- **Prendre 4 semaines, prédire la 5ème**, etc. pour tous les runs
- **Faire pareil avec une semaine de plus, etc.**

**Éviter chevauchement:**
- **Chaque fois, avec 4 semaines, prédire la suivante**
- **Cacher la semaine qu'on prédit** (éviter fuite de données)
- **Reformater tableau:** Chaque fois, semaine prédite devient semaine à prédire (pas de confusion)

---

### Q3.2 - Labels pour Prédiction Semaine Suivante ✅

**Réponse:** Score agrégé (pas les 18 features)

**Labels:**
- **Pas les 18 features de la semaine 5**
- **Score calculé:** Nombre de morts × 0.5 + nombre de blessés graves
- **Moyenné sur 5** (normalisé par rapport à ratio normal)
- **Pour régression:** Score de 0 à 10 (peut-être un peu plus)
- **Pour classification:** 3 classes calculées à partir du même calcul :
  - **Normal**
  - **Pre-catastrophique**
  - **Catastrophique**

**Formule:**
```
score = (morts × 0.5 + blessés_graves) / ratio_normal × 5
```

---

### Q3.3 - Split Données et Validation ✅

**Réponse:** Split par fenêtres, cacher semaine N+1

**Stratégie:**
- **Cacher semaine N+1** comme si on ne l'avait pas
- **Essayer de la voir depuis les 4 semaines précédentes**
- **Comme un énorme tableau:** Chaque fois répéter semaines précédentes
- **Labels caractérisés** selon utilisateur (régression ou classification)
- **Labels de la 5ème semaine**
- **Prendre 4 semaines précédentes** et faire un grand tableau
- **Réorganiser tout pour un run**, puis pour les 50 runs de base
- **Générer très grand tableau** et essayer de prédire N+1
- **Modèle enregistré** et peut être réutilisé dans simulation
- **Voir pour premier run** ce qu'il a prédit vs ce qui a été réellement généré

---

### Q3.4 - Métriques d'Évaluation ✅

**Réponse:** Métriques standards, pas de graphiques par type

**Métriques:**
- **Régression:** MAE, RMSE, R²
- **Classification:** Accuracy, Precision, Recall, F1

**Graphiques:**
- **Pas de graphiques par type d'incident** (tout est agrégé)
- **Ce qu'on essaie de prédire:** Un seul score ou 3 classes
- **Visualisation SHAP:** Pour importance des 18 features (à implémenter)

---

## 4. INTÉGRATION ET WORKFLOW

### Q4.1 - Workflow Complet : Génération → ML ✅

**Réponse:** Workflow étape par étape détaillé

**Workflow:**
1. **Génération données journalières de base:** 3 vecteurs B&I (bénin, moyen, grave) pour le jour
   - **Vecteurs nuit** (3 nombres au lieu de 9)
   - **Vecteurs alcool** (3 nombres au lieu de 9)
   - **Par type d'incident:** Un vecteur par microzone (3 nombres au lieu de 9)
   - **Par jour**

2. **Évolution trafic:** Chaque jour, évolution trafic dans microzone (ralenti, beaucoup ralenti, etc.)

3. **Grands tableaux de calcul:**
   - **Microzone touchée par événement → toutes casernes les plus proches**
   - **Toutes casernes Paris**
   - **De cette microzone → hôpital**
   - **En colonnes:** Toutes microzones traversées par cette route
   - **Proportion pour chaque microzone traversée**

4. **Calcul simple aller-retour:** Temps total

5. **Golden Hour:** Joue en proportion pour calculer nombre de morts et blessés graves

6. **18 features:** Nombre de morts et blessés graves permettent calculer scores problématiques

7. **Labels:** Calculés à partir des scores

8. **Intégration stress pompiers:** Dans calcul Golden Hour, stress pompiers de caserne choisie augmente durée trajet

**Script:**
- **Tout faire en une fois** (comme dit)
- **Tests de génération** à chaque étape (vecteurs, génitalia, etc.)

**Gestion erreurs:**
- Tests de génération à chaque étape

---

### Q4.2 - Utilisation Modèle Enregistré ✅

**Réponse:** Interface utilisateur avec choix modèle

**Interface:**
- **En haut à droite:** Utilisateur peut choisir soit entraîner modèle, soit charger modèle utilisé
- **Charger modèle utilisé:** Sans entraînement avec données qu'il a
- **Prédiction systématique:** Prendre 4 semaines, dès qu'il a 4 semaines, prédire la 5ème
- **Nouveau round:** Partir de la 4ème semaine pour 20 rounds
- **Fenêtre avec 20 arrondissements**
- **Carte à côté** qui sépare incidents graves
- **3 cartes au total:**
  - Incidents graves
  - "Semaine prédite"
  - "Semaine réelle"

**Affichage:**
- **Semaine pré-prédite et semaine réelle**
- **Pour 20 arrondissements:** État pré-prédiction (classification ou chiffre risque global pour régression)
- **Prédiction des 2 colonnes**
- **Toutes les 2.5 secondes:** Voir si prédiction était correcte
- **Match sur arrondissement** ou gap en chiffres qui apparaît pour une seconde
- **Pendant tout:** Voir combien machine learning a bien prédit ou non

---

### Q4.3 - Versioning et Comparaison Modèles ✅

**Réponse:** Pour plus tard (complexe)

- Comparaison modèles pour plus tard (un peu complexe)
- Peut-être pas horloge processeur pour seed (à voir plus tard, un peu compliqué)

---

## 5. DONNÉES ET TRAÇABILITÉ

### Q5.1 - Journal de Traçabilité ✅

**Réponse:** À voir plus tard

- Seed, paramètres, événements (détails à préciser plus tard)

---

### Q5.2 - Format Données Intermédiaires ✅

**Réponse:** À déterminer

- Format et stockage des données intermédiaires (journalières, hebdomadaires) à déterminer

---

## 6. RÉSUMÉ ARCHITECTURE FINALE

### Structure des Vecteurs Journaliers

**Base (3 vecteurs par microzone):**
- Vecteurs bénin/moyen/grave pour chaque type (incendies, accidents, agressions)
- Patterns cachés (hebdomadaires, 60 jours)

**En plus:**
- **Vecteurs journaliers alcool:** 3 valeurs par type (au lieu de 9)
- **Vecteurs journaliers nuit:** 3 valeurs par type (au lieu de 9)
- **Par microzone:** Un vecteur par type d'incident (3 nombres)

### Calcul Features Hebdomadaires (18)

1. **6 features - Sommes:** (moyen+grave) et bénin par type
2. **6 features - Proportions:** Alcool et nuit (agrégées depuis journalier)
3. **3 features - Morts:** Calcul hebdomadaire avec Golden Hour + randomité
4. **3 features - Blessés graves:** Calcul hebdomadaire avec trajets + sévérité + randomité

### Golden Hour

- **Grand tableau:** Distances 100 casernes + 10 hôpitaux
- **Double tableau:** Microzones traversées
- **Tableau dynamique:** Taux ralentissement trafic par microzone
- **Calcul aller-retour:** Temps total
- **Stress pompiers:** Augmente durée trajet

### Événements Modulables

- **Classes** avec caractéristiques
- **Durée 3-10 jours** (aléatoire)
- **Influence:** Matrices, génération données, proportions
- **Priorités:** Augmenter probabilités incidents, nombre victimes, personnel déployé

---

**Créé:** 25 Janvier 2026  
**Clarifications:** 26 Janvier 2026  
**Réponses Session 5.2:** 26 Janvier 2026  
**Statut:** ✅ Complété
