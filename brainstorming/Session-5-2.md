# 🚀 SESSION 5.2 - VISION FUTURE : Extensibilité et Innovations
## Questions Approfondies - Partie 2

**Date:** 26 Janvier 2026  
**Statut:** ✅ Complété  
**Objectif:** Clarifier détails techniques d'implémentation, architecture, et workflow

---

# 🎯 RÉPONSES SESSION 5.2

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

### Labels ML

- **Score:** (morts × 0.5 + blessés_graves) / ratio_normal × 5
- **Régression:** Score 0-10+
- **Classification:** Normal, Pre-catastrophique, Catastrophique

### Workflow Complet

1. Génération données journalières (vecteurs base + alcool + nuit)
2. Évolution trafic quotidienne
3. Calcul grands tableaux (casernes, hôpitaux, microzones traversées)
4. Calcul Golden Hour (temps aller-retour + stress pompiers)
5. Calcul 18 features hebdomadaires
6. Calcul labels (score ou classes)
7. Fenêtres glissantes 4 semaines → prédiction semaine 5
8. Entraînement ML
9. Utilisation modèle enregistré avec interface

---

**Créé:** 26 Janvier 2026  
**Statut:** ✅ Complété  
**Prochaine étape:** Implémentation selon spécifications
