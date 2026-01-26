# 📋 SESSION 4 - RÉSUMÉ COMPLET
## Brainstorming Interface & Modèle - Sessions 4.1, 4.2, 4.3

**Date:** 25 Janvier 2026  
**Statut:** ✅ Complété  
**Prochaine étape:** Session 5 (Validation Finale Brainstorm)

---

# 🎯 RÉSUMÉ EXÉCUTIF (5 minutes)

## Objectif Session 4
Définir flux utilisateur complet (démarrage → résultats) et décisions interface Streamlit + modèle scientifique de génération d'incidents.

---

# 📊 SESSION 4.1 - INTERFACE & MODES D'UTILISATION ✅

## Décisions Clés

### Interface
- ✅ **Streamlit** (application web interactive)

### Mode Principal
- ✅ **Mode Prédiction** (génération Monte Carlo autonome)
  - Génération mensuelle (≥1 mois) avec 4 semaines précédentes comme features
  - Choix modèle ML: **régression OU classification**
  - Comparaison: modèles calculés fonctions internes vs modèles ML entraînés
  - Réutilisation modèles: sauvegarde/chargement pour nouvelles générations

### Paramètres Configurables
- ✅ Type ML (régression/classification)
- ✅ Durée simulation
- ✅ Scénario (pessimiste/moyen/optimiste)
- ✅ Variabilité locale (faible/moyen/important)

---

# 📊 SESSION 4.2 - VALIDATIONS, PROGRESSION & SAUVEGARDES ✅

## Décisions Clés

### Validations
- ✅ Message d'erreur si paramètres invalides
- ✅ Confirmation relance simulation après 2 ans (warning)

### Interface Modèles ML (Haut droite)
- **Ligne supérieure:** Checkbox "Train a model" → choix type ML → sélection 2 modèles (sur 4)
- **Ligne inférieure:** Bouton radio "Use a prediction model" → chargement depuis `models/classification/` ou `models/regression/`
- Métadonnées modèles: nom, numéro entraînement, jours, accuracy

### Affichage Progression
- ✅ Jours simulés / Total (important)
- ✅ Vitesse: **1 jour = 1/3 seconde** (0.33s)
- ✅ Pop-ups événements majeurs + icônes carte
- ✅ Colonne gauche: liste événements/incidents (cliquable → détails)
- ✅ Codes couleur: Feu (jaune/orange/rouge), Accident (beige/marron), Agression (gris)
- ✅ Priorité affichage: Plus grave → Feu > Agression > Accident

### Sauvegardes
- ✅ Interrompre simulation
- ✅ Sauvegarder état (vecteurs, événements, variables cachées)
- ✅ Export résultats partiels
- ✅ Sauvegarde modèles ML avec métadonnées

---

# 📊 FLUX ENTRAÎNEMENT ML (Clarification Session 4)

## Description Complète

### Pendant le Run (Affichage Animé)
- ✅ **Carte Paris animée** selon vecteurs générés
- ✅ **Carte incidents** animée
- ✅ **Arrondissements** avec stats qui changent
- ✅ **Compteur jours** : "Jour X / Total" (affichage dynamique)
- ✅ **Compteur runs** : "Run 1/50" à droite du compteur jours (rectangle bas)
- ✅ **Paramètre "nb run"** : Modifiable par utilisateur (affiché en haut, valeur par défaut)

### Fin des Jours (Calcul Rapide)
- ✅ **Affichage dynamique s'arrête** (plus d'animation 1/3 seconde)
- ✅ **Calcul rapide** (sans affichage graphique) :
  - Suite Monte-Carlo journalière
  - Features hebdomadaires
  - Labels mensuels

### Entraînement Modèle
- ✅ **Modèle s'entraîne** : Features hebdo → Labels mensuels
- ✅ **Granularité** : Par arrondissement (20 arrondissements)
- ✅ **Répétition** : 50 runs (ou nombre choisi par utilisateur)

### Sauvegarde Modèle
- ✅ **Emplacement** : `models/regression/` ou `models/classification/`
- ✅ **Nom fichier** : `{algo}_{numero_entrainement}_{params}.joblib`
  - Exemple: `RandomForest_001_scenario-moyen_variabilite-0.5_duree-90.joblib`
- ✅ **Métadonnées incluses** :
  - Nom algorithme (RandomForest, LinearRegression, etc.)
  - Numéro entraînement
  - Paramètres génération données (scénario, variabilité, durée, etc.)

---

# 📊 SESSION 4.3 - OUTPUTS, MODÈLE SCIENTIFIQUE & IMPLÉMENTATION ✅

## Décisions Clés

### Layout Interface Final
```
┌─────────────────────────────────────────────────────────────┐
│  BANDEAU HAUT: Sélections (jours, scénario, variabilité)   │
├──────────┬──────────────────────────────┬───────────────────┤
│  LISTE   │     CARTE PARIS              │  LISTE           │
│  ÉVÉNTS  │     (Centre)                 │  ARRONDISSEMENTS │
│  &       │     - Événements             │  (Droite)         │
│  INCIDENTS│    - Couleurs changeantes   │  - Petits        │
│  (Gauche)│                              │    rectangles    │
│  Cliquable│                             │  - Évolution     │
│  → Détails│                             │    temporelle    │
│          │                              │  Cliquable       │
│          │                              │  → Graphiques    │
│          │                              │    détaillés     │
├──────────┴──────────────────────────────┴───────────────────┤
│  BANDEAU BAS: [Lancer] | Jours X/Total | Run 1/50 | [Stop]  │
└─────────────────────────────────────────────────────────────┘
```

### Statistiques Affichées
- **Colonne gauche:** Liste événements/incidents cliquable → features
- **Colonne droite:** Rectangles arrondissements avec évolution temporelle (cliquable → graphiques détaillés)
- **Indicateur catastrophe:** Calculé même en mode régression (pour comparaison)
- **Fenêtre détaillée:** Connectée temps réel à simulation

---

## 🧠 MODÈLE SCIENTIFIQUE - DÉCISIONS CRITIQUES

### Option Choisie
- ✅ **Option B: MVP Modèle Scientifique Complet**
  - Zero-Inflated Poisson + Régimes Cachés dès MVP
  - Variables cachées (stress 60j, patterns 7j)
  - Matrices de transition
  - Plus complexe mais scientifiquement crédible

### Vecteurs Statiques
- ✅ **Concept:** Vecteurs statiques (3×3 valeurs par microzone) = interface patterns Paris → modèle
- ✅ **Influence:** Régimes ET intensités (les deux)
- ✅ **Structure:** 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave)

### Règle Prix m²
- ✅ **Division probabilité agression:** `prob_agression_modulée = prob_agression_base / facteur_prix_m2`
- ✅ **Diminution probabilités régimes:** Prix m² élevé → probabilités Détérioration/Crise réduites

### Trois Matrices dans Calcul J+1
- ✅ **Matrice Gravité:** Même type, même microzone (historique 7 jours, décroissance exponentielle)
- ✅ **Matrice Types Croisés:** Autres types, même microzone (corrélations: incendie→accidents 1.3, etc.)
- ✅ **Matrice Voisins:** 8 zones alentours (pondération grave×1.0, moyen×0.5, bénin×0.2, modulée variabilité)

### Intégration Modèle Scientifique
- ✅ **Étape 6:** Intensités calibrées = `λ_base × facteur_statique × facteur_gravité × facteur_croisé × facteur_voisins × facteur_long`
- ✅ **Caps:** Min ×0.1, Max ×3.0 (évite explosions)
- ✅ **Normalisation:** Z(t) garantit probabilités cibles (82% bénin, 16% moyen, 2% grave)

### Classes Événements Graves
- ✅ **Héritabilité:** Classe parent `EventGrave` avec enfants `AccidentGrave`, `IncendieGrave`, `AgressionGrave`
- ✅ **Influence ligne temporelle:** Augmente stress long-terme, pattern court-terme, force transitions régimes

---

# 🔑 POINTS ESSENTIELS 4.3 vs 4.2

## 5 Lignes à Retenir (À Réécrire à la Main)

1. **Modèle scientifique complet dès MVP** : Zero-Inflated Poisson + Régimes Cachés avec variables cachées (stress 60j, patterns 7j) remplace modèle simplifié, garantissant crédibilité scientifique dès le départ.

2. **Vecteurs statiques comme interface patterns Paris** : 3×3 valeurs par microzone (type × gravité) influencent régimes initiaux ET intensités λ_base, avec prix m² divisant probabilités agressions et diminuant probabilités régimes Tension/Crise.

3. **Trois matrices intégrées dans calcul J+1** : Matrice gravité (même type/microzone, 7j décroissance), matrice types croisés (autres types/microzone, corrélations spécifiques), matrice voisins (8 zones, pondération gravité, modulée variabilité locale) combinées multiplicativement dans Étape 6 modèle scientifique.

4. **Layout interface finalisé** : Carte Paris centre, colonne gauche événements/incidents cliquables, colonne droite arrondissements avec rectangles évolution temporelle cliquables → graphiques détaillés, indicateur catastrophe même en régression, fenêtre détaillée temps réel.

5. **Classes événements graves avec héritabilité** : Structure parent `EventGrave` avec enfants spécifiques (`AccidentGrave`, `IncendieGrave`, `AgressionGrave`) influençant ligne temporelle (stress, patterns, régimes) et implémentation technique prête (structure données, cache, normalisation Z(t)).

---

# 📋 ARCHITECTURE TECHNIQUE VALIDÉE

## Structure Données
- `MicrozoneData` avec `deque(maxlen=60)` pour historique
- Vecteurs statiques calculés une fois au début
- Cache pour optimisation performance

## Formules Clés
- **Intensités calibrées:** `λ_calibrated = λ_base × facteur_statique × facteur_gravité × facteur_croisé × facteur_voisins × facteur_long`
- **Normalisation:** `Z(t) = Σ(λ_calibrated)` → probabilités conditionnelles
- **Probabilités finales:** `P(incident) = (1 - p0) × λ_calibrated / Z(t)`

## Performance
- Cache intelligent (invalidation par jour)
- Structure efficace pour 100 microzones
- Caps pour éviter explosions

---

# ✅ DÉCISIONS FIGÉES (Ne Plus Changer)

## Interface
- ✅ Streamlit (application web)
- ✅ Layout: Carte centre, colonne gauche événements, colonne droite arrondissements, bandeaux haut/bas
- ✅ Vitesse: 1 jour = 0.33s
- ✅ Codes couleur par type/gravité
- ✅ Priorité affichage: Grave → Feu > Agression > Accident

## Modèle
- ✅ Zero-Inflated Poisson + Régimes Cachés (MVP)
- ✅ Vecteurs statiques (3×3 par microzone)
- ✅ Trois matrices (gravité, croisée, voisins)
- ✅ Prix m²: division agressions, diminution régimes
- ✅ Classes événements graves avec héritabilité

## Paramètres
- ✅ Type ML (régression/classification)
- ✅ Durée simulation
- ✅ Scénario (pessimiste/moyen/optimiste)
- ✅ Variabilité locale (faible/moyen/important)

---

# ⚠️ POINTS ENCORE À CLARIFIER (Session 5)

## Formules Exactes
- ⏳ Formule exacte division agression par prix m² (ratio, seuils, autre ?)
- ⏳ Formule exacte diminution probabilités régimes par prix m²
- ⏳ Autres facteurs socio-économiques (chômage, densité, revenus) → influence ?

## Intégration Technique
- ⏳ Détails implémentation vecteurs statiques (calcul depuis patterns Paris)
- ⏳ Validation probabilités cibles après toutes modulations
- ⏳ Gestion événements graves (stockage, accès, performance)

## Phase 2
- ⏳ Format CSV exact pour import données réelles BSPP
- ⏳ Calibration modèle scientifique avec vraies données
- ⏳ Roadmap évolutions Phase 2/3

---

# 🔗 LIENS AVEC SESSIONS PRÉCÉDENTES

## Depuis Session 3
- Architecture données (5 niveaux) → Structure interface
- Fonction génération J+1 (7 étapes simplifiées) → Modèle scientifique complet (7 étapes sophistiquées)
- Codes couleur → Reflètent structure vecteur [grave, moyen, bénin]
- Influence voisins → Intégrée dans matrice voisins

## Vers Session 5
- Session 4 complète → Validation finale brainstorm
- Architecture figée → Prêt implémentation
- Questions restantes → À résoudre Session 5

---

# 📖 RÉFÉRENCES

- **Contexte complet:** `Contexte-Sessions-1-a-3.md`
- **Session 4.1:** `Session-4.1.md`
- **Session 4.2:** `Session-4.2.md`
- **Session 4.3:** `Session-4.3.md` (avec pistes implémentation)
- **Modèle scientifique:** `.bmad-core/utils/Modèle Prédiction Incidents J+1.pdf`

---

# 🎯 OBJECTIF SESSION 5

**Validation finale brainstorm** avant passage MAPPING (Étape 2 BMAD).

**À faire:**
1. Valider toutes décisions Session 4
2. Résoudre points encore ouverts
3. Synthèse finale architecture
4. Préparation implémentation

---

**Créé:** 25 Janvier 2026  
**Dernière mise à jour:** 25 Janvier 2026  
**Statut:** ✅ Session 4 complète, prêt Session 5
