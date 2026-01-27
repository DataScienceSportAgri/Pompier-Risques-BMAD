# 📋 SESSION 5 - RÉSUMÉ COMPLET
## Vision Future : Extensibilité et Innovations

**Date:** 25-26 Janvier 2026  
**Sessions:** 5.1, 5.2, 5.3  
**Statut:** ✅ Complété  
**Objectif:** Définir architecture complète, spécifications techniques et roadmap d'implémentation

---

# 🎯 VISION ET PRINCIPES FONDAMENTAUX

## Vision "North Star" (6-12 mois)

- **Données générées remplaçables par vraies données BSPP**
- **Séparation claire:** Features hebdo (générées) vs Features mensuelles (réelles BSPP)
- **Objectif ML:** Détecter patterns dangereux : "Avec ces 4 semaines qui se sont suivies, selon les alentours, on arrive à quelque chose de dangereux en termes de temps"

## First Principles

1. **Produit:** Aide à la décision
2. **Données:** Génération réaliste → vraies données plus tard
3. **Modèle ML:** **Interprétabilité prioritaire** (2500 données seulement, RandomForest + SHAP)
4. **Validation:** Comparer modèles enregistrés avec paramètres différents

## Innovations Clés

- **Fonctionnalité "Wow":** Utiliser modèle enregistré + SHAP values (explicabilité)
- **Boucle rétroactive positive:** Oui (politique publique, renforts, travaux)
- **Architecture plugins:** Très important (modulateurs sans toucher cœur)

---

# 🔧 ARCHITECTURE TECHNIQUE

## Ordre d'Implémentation

1. **Vecteurs journaliers** (3 vecteurs base : bénin, moyen, grave)
2. **Vecteurs alcool/nuit** (3 valeurs par type)
3. **Golden Hour** (calculs distances, stress pompiers) ⚠️ **Avant** morts/blessés
4. **Morts et blessés graves** (calcul hebdomadaire, utilise Golden Hour)
5. **Features hebdo** (18 features, utilise tout ce qui précède)
6. **Labels** (score ou classes, utilise morts + blessés)
7. **ML** (transition features hebdo → labels)

## 18 Features Hebdomadaires

**Créées dans `StateCalculator` pour chaque semaine:**

### 6 Features - Sommes Incidents
- Pour chaque type (accidents, incendies, agressions) :
  - **Somme (moyen + grave)** = 3 features
  - **Somme bénin** = 3 features

### 6 Features - Proportions (Monte-Carlo Hebdomadaire)
- **Proportion incidents avec alcool** (par type) = 3 features
- **Proportion incidents la nuit** (par type) = 3 features
- Générées journalièrement puis agrégées hebdomadairement

### 3 Features - Morts Hebdomadaires
- Nombre de morts par accident, incendie, agression
- Calcul: Grand tableau chemins + états routiers + Golden Hour + randomité (30% base aléatoire, 60% après Golden Hour)

### 3 Features - Blessés Graves Hebdomadaires
- Nombre de blessés graves par accident, incendie, agression
- Calcul: Trajets + sévérité + randomité (moins importance durée trajet, plus importance sévérité)

---

# 📊 BASE MATHÉMATIQUE

## Modèle Zero-Inflated Poisson (PDF)

**Référence:** "Modèle Prédiction Incidents J+1.pdf"

- **Régimes cachés:** Stable, Détérioration, Crise
- **Patterns court-terme:** 7 jours (détection 4+ événements moyens)
- **Patterns long-terme:** 60 jours (accumulation stress avec décroissance hyperbolique)
- **Intensités calibrées** par régime et gravité
- **Matrices de transition** modifiées selon patterns activés

## Patterns (7 et 60 jours)

- **2 DataFrames mobiles:**
  - DataFrame patterns 7 jours (hebdomadaires)
  - DataFrame patterns 60 jours (long-terme)
- **Lecture depuis fichier:** Patterns définis et lus automatiquement

## Ajouts sur Base Mathématique

1. **Effets caractéristiques événements graves:** Modulation intensités λ_base(τ,g), facteurs long/court-terme, matrices de transition
2. **Proportions nuit/alcool:** Monte-Carlo journalier (sciences sociales), agrégation hebdomadaire
3. **Problèmes trafic:** Calcul microzone/jour (accidents + hasard), effet bénéfique sur dangerosité
4. **Événements positifs:** Modification matrices en mieux (réduction intensités, amélioration transitions)

---

# 🏗️ STRUCTURE DE DONNÉES

## Vecteurs Journaliers

- **Classe Vector:** 3 valeurs (bénin, moyen, grave)
- **DataFrame:** Colonnes avec instances Vector + type incident
- **Sauvegarde:** Pickle pour données intermédiaires

## Golden Hour

- **Tableaux pré-calculés:** Distances 100 casernes + 10 hôpitaux (Pythagore sur carte Paris)
- **Double tableau:** Microzones traversées par trajet
- **Tableau dynamique:** États circulation microzones (journalier)
- **Calcul temps:** `temps_trajet = temps_base × (1 + stress_caserne × 0.1)`

## Stress Pompiers

- **30 pompiers par caserne** (3000 total)
- **+0.4 stress** par intervention ou pompiers arrêtés
- **Moyenne par caserne** pour calcul temps trajet

---

# 🎲 ÉVÉNEMENTS MODULABLES

## Structure Hiérarchique

```
Event (classe de base)
├── Incident (sous-classe)
│   ├── Accident
│   ├── Agression
│   └── Incendie
└── PositiveEvent (sous-classe)
```

## Caractéristiques

- **Caractéristiques peuvent être créées aléatoirement ou non**
- **Effets sur randomité** création caractéristiques dans autres événements
- **Complexité nécessaire:** Pour éviter que ML comprenne trop facilement
- **Durée d'effet:** 3-10 jours (aléatoire)

## Types de Caractéristiques (MVP)

1. **Propagation:** Part d'une microzone, pattern droite/gauche, gravité diminue avec distance
2. **Augmentation accidents bénins/moyens:** Dans microzones suivantes, effets zones adjacentes
3. **Réduction embouteillages:** Zone dangereuse → moins voitures → moins accidents

## Retour à la Normale

- **Événement positif:** Annuler tous événements négatifs pour 10 jours sur tout Paris

---

# 🤖 MACHINE LEARNING

## Prédiction

- **Entrée:** 4 semaines consécutives (18 features × 4 = 72 colonnes)
- **Sortie:** Prédiction semaine suivante (semaine 5)
- **Arrondissements adjacents:** Arrondissement central + 4 autour = 5 × 18 = **90 features**

## Labels

- **Pas les 18 features de la semaine 5**
- **Score calculé:** `(morts × 0.5 + blessés_graves) / (habitants_arr / 100000) × 3.25`
- **Régression:** Score 0-10+
- **Classification:** 3 classes :
  - **Normal:** ≤ 3.25 morts/semaine pour 100,000 habitants
  - **Pre-catastrophique:** > 4.2 morts
  - **Catastrophique:** > 4.8 morts × 0.5 blessés graves

## Fenêtres Glissantes

- **Workflow:** 2 parties
  1. Run qui crée tout (features hebdo + labels)
  2. 5 runs puis 49 runs supplémentaires
- **Entraînement:** Sur grand DataFrame final avec 18 features × 4 arrondissements pour 1 arrondissement
- **Limitation:** Seulement 4 semaines précédentes de l'arrondissement (pas toutes semaines, pas tout Paris)

## Modèles et Métriques

- **4 algos:** 2 régression, 2 classification
- **Hyperparamètres:** Phase 2 (valeurs fixes au début)
- **Métriques:**
  - **Régression:** MAE, RMSE, R²
  - **Classification:** Accuracy, Precision, Recall, F1
- **SHAP values:** Pour importance des 18 features

---

# 🖥️ INTERFACE UTILISATEUR

## Web App Simple

- **Tkinter/Folium:** Tests de départ seulement
- **Update 2.5 secondes:** Chaque jour dure 1/3 seconde (7 × 1/3 = 2.5s)
- **Fonctionnalités:**
  - Modèles enregistrés (trained models)
  - Choix algos (4 total)
  - 3 cartes: Incidents graves, "Semaine prédite", "Semaine réelle"
  - Affichage match/gap toutes les 2.5 secondes

---

# ✅ TESTS ET VALIDATION

## Tests Unitaires

- **Vérifier cohérence données:**
  - Si 0 morts ou < 2 morts sur arrondissement sur 400 jours → problème
  - Si > 200 morts → problème

## Validation Patterns

- **Vérifier qu'il n'y a pas de packaging** (regroupement dans une direction)
- **Suivre graphiques** nombre de morts, etc.

---

# ⚡ PERFORMANCE ET OPTIMISATION

## Options

1. **Faire tous les runs puis ML à la fin**
2. **Commencer à entraîner sur nouvelles données générées** (parallélisation possible mais pas vraiment voulu)

## Parallélisation

- **Calculs vecteurs vs calculs proportions:** Pourraient être parallélisés (dépendants l'un de l'autre)

## Scalabilité

- **Nombres entiers (ints) ou floats** → pas énormes
- **Architecture modulaire** pour mettre vraies données (Phase 2)

---

# 📝 CORRÉLATIONS ET EFFETS TEMPORELS

## Corrélations entre Types d'Incidents

- **Matrices de corrélation** avec facteurs multiplicatifs
- **Exemple:** Plus d'incendies la nuit → moins d'accidents (réveil, concentration)
- **Ordre de calcul:** D'abord incendies, puis accidents, puis agressions

## Effets Temporels

- **Agressions:** Diminuent jour même, augmentent jour suivant
- **Patterns 3 jours → 1 semaine:** Si proportions > 60% d'agressions pendant 3 jours → augmentation probabilité agressions pendant 1 semaine suivante (même zone + zones adjacentes)
- **Saisonnalité:** Plus probabilité incidents la nuit en été qu'en hiver (agressions), pas pour incendies

---

# 🎯 RÉSUMÉ DÉCISIONS CLÉS

## MVP vs Phase 2

- **Tous les composants sont MVP**
- **Phase 2:** Ajustement paramètres, fine-tuning, hyperparamètres
- **Événements modulables:** Nécessaires dès le début (complexité requise)

## Traçabilité

- **Journal complet:** Seed, paramètres, événements (à voir plus tard)
- **Format données intermédiaires:** À déterminer

## Versioning Modèles

- **Chaque run = nouveau modèle** sauvegardé avec numéro incrémenté
- **Nom fichier:** Algo + numéro + paramètres simulation + hyperparamètres
- **Objectif:** Comparaisons entre modèles (pour plus tard, complexe)

---

# 📚 RÉFÉRENCES

- **PDF Modèle Mathématique:** "Modèle Prédiction Incidents J+1.pdf"
- **PDF Schéma Projet:** "Schéma Projet Data BSPP.pdf"
- **PDF Échange 3.1:** "Echange 3.1 Récapitulatif.pdf"

---

**Créé:** 26 Janvier 2026  
**Statut:** ✅ Complété  
**Prochaine étape:** Implémentation selon spécifications
