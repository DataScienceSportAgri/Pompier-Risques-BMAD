# 📋 BRAINSTORMING SESSION RESULTS
## Spécifications Techniques pour Implémentation

**Date:** 25-26 Janvier 2026  
**Sessions:** 5.1, 5.2, 5.3  
**Statut:** ✅ Prêt pour implémentation  
**Objectif:** Document de référence pour Architect/Dev

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

**Référence:** `brainstorming/Modèle Prédiction Incidents J+1.pdf`

- **Régimes cachés:** Stable, Détérioration, Crise
- **Patterns court-terme:** 7 jours (détection 4+ événements moyens)
- **Patterns long-terme:** 60 jours (accumulation stress avec décroissance hyperbolique)
- **Intensités calibrées** par régime et gravité
- **Matrices de transition** modifiées selon patterns activés

## Algorithme Complet de Prédiction J → J+1 (Session 4)

**7 Étapes du modèle scientifique:**

1. **Détection Pattern Court-Terme (7 jours):**
   - `Ψ_court(t) = Σ_{s=t-6}^{t} Σ_{τ∈T} I_s^(τ, Moyen)`
   - Pattern activé si `Ψ_court(t) ≥ 4`

2. **Calcul Variable Cachée Long-Terme (60 jours):**
   - `Φ_long(t) = Σ_{ℓ=1}^{60} β_ℓ × Ψ_pondéré(t-ℓ)`
   - `β_ℓ = 0.20 / (1 + 0.05 × ℓ)` (décroissance hyperbolique)

3. **Mise à Jour Matrice Transition Régimes:**
   - Si pattern activé: Multiplier transitions dégradation par 3.5
   - Si `Φ_long(t) > 15`: Forcer probabilité vers régime Crise

4. **Prédiction Distribution Régime à J+1:**
   - `ℙ(S_{t+1} = s_j | H_t) = Σ_{i=1}^{3} ℙ(S_t = s_i | H_t) × q_{ij}(t)`

5. **Calcul Probabilité Zero-Inflation:**
   - `p_0^(s)(t) = p_0^(s, base) × exp(-0.05 × Φ_long(t)) × exp(-0.10 × Ψ_court(t))`

6. **Calcul Intensités et Normalisation:**
   - `facteur_long = 1 + κ_s × Φ_long(t)`
   - `λ_calibrated(τ,g) = λ_base(τ,g) × facteur_long × facteur_statique × facteur_gravité × facteur_croisé × facteur_voisins`
   - `Z(t) = Σ_{τ,g} λ_calibrated(τ,g)`
   - **Caps:** Min ×0.1, Max ×3.0

7. **Probabilités Finales à J+1:**
   - `ℙ(I_{t+1}^(τ',g') = 1 | H_t) = p_0^(s)(t) × 1[Rien] + (1 - p_0^(s)(t)) × λ_calibrated(τ',g') / Z(t)`

## Trois Matrices dans Calcul J+1 (Session 4)

**Intégration dans Étape 6:**

1. **Matrice Gravité Microzone:**
   - Même type, même microzone
   - Historique 7 jours avec décroissance exponentielle
   - `facteur_gravité = f(historique_7j)`

2. **Matrice Types Croisés:**
   - Autres types, même microzone
   - Corrélations spécifiques (ex: incendie→accidents ×1.3)
   - `facteur_croisé = f(autres_types_microzone)`

3. **Matrice Voisins:**
   - 8 zones alentours (radius 1)
   - Pondération: grave ×1.0, moyen ×0.5, bénin ×0.2
   - Modulée par variabilité locale (faible=0.3, moyen=0.5, important=0.7)
   - `facteur_voisins = f(8_zones_voisines, variabilite_locale)`

**Formule combinée:**
```
λ_calibrated(τ,g) = λ_base(τ,g) × facteur_statique × facteur_gravité × facteur_croisé × facteur_voisins × facteur_long
```

## Patterns (7 et 60 jours)

- **2 DataFrames mobiles:**
  - DataFrame patterns 7 jours (hebdomadaires)
  - DataFrame patterns 60 jours (long-terme)
- **Lecture depuis fichier:** Patterns définis et lus automatiquement
- **Format à définir:** CSV, JSON, ou YAML (à décider lors implémentation)

## Ajouts sur Base Mathématique

1. **Effets caractéristiques événements graves:** Modulation intensités λ_base(τ,g), facteurs long/court-terme, matrices de transition
2. **Proportions nuit/alcool:** Monte-Carlo journalier (sciences sociales), agrégation hebdomadaire
3. **Problèmes trafic:** Calcul microzone/jour (accidents + hasard), effet bénéfique sur dangerosité
4. **Événements positifs:** Modification matrices en mieux (réduction intensités, amélioration transitions)

## Règle Prix m² (Session 4)

- **Division probabilité agression:** `prob_agression_modulée = prob_agression_base / facteur_prix_m2`
- **Diminution probabilités régimes:** Prix m² élevé → probabilités Détérioration/Crise réduites
- **Facteur prix m²:** `facteur_prix_m2 = prix_m2_microzone / prix_m2_moyen_paris`

---

# 🏗️ STRUCTURE DE DONNÉES

## Architecture 5 Niveaux (Session 3)

**Référence:** `Contexte-Sessions-1-a-3.md` et `Schéma Projet Data BSPP.pdf`

### Niveau 1 : Données Statiques (Fixes)
- **Géographiques:** Arrondissements, microzones, population, prix m², scénario (pessimiste/moyen/optimiste)
- **Non géographiques:** Constantes, variabilité locale (fort/moyen/faible)
- **Infrastructure:** Casernes (100), hôpitaux (10), positions, capacités

### Niveau 2 : Données Mobiles Journalières (Microzones)
- **Vecteurs journaliers:** 3 vecteurs × 3 valeurs (bénin, moyen, grave) par microzone
- **Monte-Carlo:** Génération jour-à-jour avec aléatoire + logique
- **Variables cachées:** Fatigue pompiers, congestion, stress long-terme (60j), patterns court-terme (7j)
- **État circulation:** Ralentissement par microzone au jour J

### Niveau 3 : Événements Graves (Ponctuels)
- **Incidents graves:** Accident, Agression, Incendie
- **Caractéristiques probabilistes:** Traffic slowdown, cancel sports, increase bad vectors, kill pompier
- **Événements positifs:** Fin travaux, nouvelle caserne, amélioration matériel, etc.

### Niveau 4 : Features Hebdomadaires (Arrondissements)
- **18 features** calculées par semaine et arrondissement
- **StateCalculator:** Agrège données microzones → arrondissements

### Niveau 5 : Labels Mensuels (Arrondissements)
- **Score ou classes:** Calculés à partir de morts + blessés graves
- **LabelCalculator:** Utilise SEULEMENT casualties des événements (évite double comptage)

## Vecteurs Journaliers

- **Classe Vector:** 3 valeurs (bénin, moyen, grave)
- **DataFrame:** Colonnes avec instances Vector + type incident
- **Sauvegarde:** Pickle pour données intermédiaires
- **Structure proposée:**
  ```python
  class Vector:
      def __init__(self, benin, moyen, grave):
          self.benin = benin
          self.moyen = moyen
          self.grave = grave
  ```
- **Historique:** `deque(maxlen=60)` pour patterns long-terme (Session 4)

## Vecteurs Statiques (Session 4)

- **Concept:** 3×3 valeurs par microzone = interface patterns Paris → modèle
- **Influence:** Régimes ET intensités (les deux)
- **Structure:** 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave)
- **Prix m²:** Division probabilité agression, diminution probabilités régimes

## Golden Hour - Détails Complets

**Référence:** `Echange 3.1 Récapitulatif.pdf` et `Schéma Projet Data BSPP.pdf`

### Données Fixes (Pré-calculées)
- **Trajets caserne → microzone:**
  - Colonnes: Distance totale, distance par microzone
  - Lignes: Caserne vers microzone
- **Trajets microzone → hôpital:**
  - Colonnes: Distance totale, distance par microzone
  - Lignes: Microzone vers hôpital
- **Microzones traversées:** Liste des microzones sur chaque trajet

### Données Mobiles (Journalières)
- **État ralentissement:** Par microzone au jour J
- **Casernes:** Nombre pompiers, fatigue
- **Hôpitaux:** Efficacité, charge

### Calcul Temps Trajet
```
temps_trajet_reel = temps_base × ∏(congestion_microzone_traversee)
temps_total = temps_trajet + temps_traitement + temps_hopital_retour
if temps_total > 60 min → casualties × 1.3
```

### Formule Complète avec Stress
```
temps_trajet = temps_base × (1 + stress_caserne × 0.1) × ∏(congestion_microzone)
```

## Stress Pompiers

- **30 pompiers par caserne** (3000 total)
- **+0.4 stress** par intervention ou pompiers arrêtés
- **Moyenne par caserne** pour calcul temps trajet
- **Fatigue:** Variable cachée par caserne (Session 4)

---

# 🎲 ÉVÉNEMENTS MODULABLES

## Structure Hiérarchique

```python
class Event:
    """Classe de base pour tous les événements"""
    pass

class Incident(Event):
    """Sous-classe pour incidents graves"""
    pass

class Accident(Incident):
    pass

class Agression(Incident):
    pass

class Incendie(Incident):
    pass

class PositiveEvent(Event):
    """Sous-classe pour événements positifs"""
    pass
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

## Classes Événements Graves (Session 4)

- **Héritabilité:** Classe parent `EventGrave` avec enfants `AccidentGrave`, `IncendieGrave`, `AgressionGrave`
- **Influence ligne temporelle:** Augmente stress long-terme, pattern court-terme, force transitions régimes
- **Caractéristiques probabilistes:**
  - Traffic slowdown (70% prob, ×2 temps, 4j, radius 2)
  - Cancel sports (30% prob, 2j)
  - Increase bad vectors (50% prob, +30%, 5j, radius 3)
  - Kill pompier (5% prob)

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

- **4 algos:** 2 régression, 2 classification (algorithmes spécifiques à définir)
- **Hyperparamètres:** Phase 2 (valeurs fixes au début)
- **Métriques:**
  - **Régression:** MAE, RMSE, R²
  - **Classification:** Accuracy, Precision, Recall, F1
- **SHAP values:** Pour importance des 18 features

---

# 🖥️ INTERFACE UTILISATEUR

## Streamlit (Session 4)

**Décision:** Application web interactive Streamlit (pas Tkinter/Folium pour production)

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

### Paramètres Configurables

- **Type ML:** Régression ou Classification
- **Durée simulation:** Modifiable par utilisateur
- **Scénario:** Pessimiste, Moyen, Optimiste
- **Variabilité locale:** Faible, Moyen, Important
- **Nombre runs:** Modifiable (défaut 50)

### Affichage Progression

- **Jours simulés / Total:** Important, affiché en temps réel
- **Vitesse:** **1 jour = 1/3 seconde** (0.33s)
- **Runs:** "Run 1/50" à droite du compteur jours
- **Pop-ups:** Événements majeurs + icônes carte
- **Colonne gauche:** Liste événements/incidents (cliquable → détails)
- **Colonne droite:** Rectangles arrondissements avec évolution temporelle (cliquable → graphiques détaillés)

### Codes Couleur

- **Feu:** Jaune/Orange/Rouge (selon gravité)
- **Accident:** Beige/Marron
- **Agression:** Gris
- **Priorité affichage:** Plus grave → Feu > Agression > Accident

### Interface Modèles ML (Haut droite)

- **Ligne supérieure:** Checkbox "Train a model" → choix type ML → sélection 2 modèles (sur 4)
- **Ligne inférieure:** Bouton radio "Use a prediction model" → chargement depuis `models/classification/` ou `models/regression/`
- **Métadonnées modèles:** Nom, numéro entraînement, jours, accuracy

### Sauvegardes

- **Interrompre simulation:** Bouton Stop
- **Sauvegarder état:** Vecteurs, événements, variables cachées
- **Export résultats partiels:** Possible
- **Sauvegarde modèles ML:** Avec métadonnées dans `models/regression/` ou `models/classification/`

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

## Décisions Figées Session 4 (Ne Plus Changer)

### Interface
- ✅ **Streamlit** (application web)
- ✅ **Layout:** Carte centre, colonne gauche événements, colonne droite arrondissements, bandeaux haut/bas
- ✅ **Vitesse:** 1 jour = 0.33s
- ✅ **Codes couleur** par type/gravité
- ✅ **Priorité affichage:** Grave → Feu > Agression > Accident

### Modèle
- ✅ **Zero-Inflated Poisson + Régimes Cachés** (MVP)
- ✅ **Vecteurs statiques** (3×3 par microzone)
- ✅ **Trois matrices** (gravité, croisée, voisins)
- ✅ **Prix m²:** Division agressions, diminution régimes
- ✅ **Classes événements graves** avec héritabilité

### Paramètres
- ✅ **Type ML** (régression/classification)
- ✅ **Durée simulation**
- ✅ **Scénario** (pessimiste/moyen/optimiste)
- ✅ **Variabilité locale** (faible/moyen/important)

## MVP vs Phase 2

- **Tous les composants sont MVP**
- **Phase 2:** Ajustement paramètres, fine-tuning, hyperparamètres
- **Événements modulables:** Nécessaires dès le début (complexité requise)

## Traçabilité

- **Journal complet:** Seed, paramètres, événements (à voir plus tard)
- **Format données intermédiaires:** À déterminer

## Versioning Modèles

- **Chaque run = nouveau modèle** sauvegardé avec numéro incrémenté
- **Nom fichier:** `{algo}_{numero_entrainement}_{params}.joblib`
  - Exemple: `RandomForest_001_scenario-moyen_variabilite-0.5_duree-90.joblib`
- **Emplacement:** `models/regression/` ou `models/classification/`
- **Métadonnées incluses:** Nom algorithme, numéro entraînement, paramètres génération données
- **Objectif:** Comparaisons entre modèles (pour plus tard, complexe)

## Trois Fonctions Nucléaires (Session 3)

**Priorisation:**
1. **Fonction Génération J+1** (PRIORITÉ ABSOLUE) : Créer vecteurs jour-à-jour
2. **Fonction Features Hebdo** : Calculer 18 features ostensibles
3. **Fonction Labels** : morts + 0.5×blessés graves → classes ou score

---

# 📁 STRUCTURE DE DOSSIERS PROPOSÉE

```
Pompier-Risques-BMAD/
├── docs/
│   └── brain-storming-session-results.md (ce fichier)
├── brainstorming/
│   ├── Session-5-*.md
│   └── *.pdf (références)
├── src/
│   ├── data/
│   │   ├── vectors.py (classe Vector)
│   │   ├── daily_data.py (génération données journalières)
│   │   └── weekly_features.py (StateCalculator)
│   ├── golden_hour/
│   │   ├── distances.py (calculs distances)
│   │   ├── stress.py (stress pompiers)
│   │   └── casualties.py (morts/blessés)
│   ├── events/
│   │   ├── base.py (Event, Incident, PositiveEvent)
│   │   ├── characteristics.py (caractéristiques)
│   │   └── propagation.py (propagation spatiale)
│   ├── patterns/
│   │   ├── patterns_7d.py (patterns hebdomadaires)
│   │   └── patterns_60d.py (patterns long-terme)
│   ├── ml/
│   │   ├── data_preparation.py (fenêtres glissantes)
│   │   ├── training.py (entraînement)
│   │   ├── models.py (modèles)
│   │   └── evaluation.py (métriques)
│   └── ui/
│       └── web_app.py (interface utilisateur)
├── data/
│   ├── intermediate/ (pickle)
│   ├── models/ (modèles sauvegardés)
│   └── patterns/ (fichiers patterns)
├── tests/
│   └── test_*.py
└── main.py
```

---

# 🔑 POINTS CLÉS POUR IMPLÉMENTATION

## Priorités

1. **Implémenter dans l'ordre** défini (7 étapes)
2. **Golden Hour avant** morts/blessés (dépendance critique)
3. **Événements modulables dès le début** (complexité requise)

## Contraintes Techniques

- **DataFrame avec instances Vector** (pas juste valeurs)
- **Pickle pour sauvegarde** données intermédiaires
- **2 DataFrames mobiles** pour patterns (7j et 60j)
- **Tableau statique** arrondissements adjacents

## Formules Importantes

### Golden Hour
- **Stress pompiers:** `temps_trajet = temps_base × (1 + stress_caserne × 0.1)`
- **Temps total:** `temps_total = temps_trajet + temps_traitement + temps_hopital_retour`
- **Congestion:** `temps_trajet_reel = temps_base × ∏(congestion_microzone_traversee)`
- **Golden Hour:** Si `temps_total > 60 min → casualties × 1.3`

### Labels
- **Score labels:** `(morts × 0.5 + blessés_graves) / (habitants_arr / 100000) × 3.25`
- **Morts:** 30% base aléatoire + 60% après Golden Hour
- **Blessés graves:** Plus randomité, moins importance durée trajet

### Modèle Scientifique (Session 4)
- **Intensités calibrées:** `λ_calibrated = λ_base × facteur_statique × facteur_gravité × facteur_croisé × facteur_voisins × facteur_long`
- **Normalisation:** `Z(t) = Σ_{τ,g} λ_calibrated(τ,g)`
- **Probabilités finales:** `P(incident) = (1 - p0) × λ_calibrated / Z(t)`
- **Prix m² agression:** `prob_agression_modulée = prob_agression_base / facteur_prix_m2`

---

# 📚 RÉFÉRENCES

## Documents Principaux

- **PDF Modèle Mathématique:** `brainstorming/Modèle Prédiction Incidents J+1.pdf`
- **PDF Schéma Projet:** `brainstorming/Schéma Projet Data BSPP.pdf`
- **PDF Échange 3.1:** `brainstorming/Echange 3.1 Récapitulatif.pdf`

## Sessions Détaillées

- **Session 4:** `brainstorming/Session-4-resume.md`, `Session-4.1.md`, `Session-4.2.md`, `Session-4.3.md`
- **Session 5:** `brainstorming/Session-5-1.md`, `Session-5-2.md`, `Session-5-3.md`, `Session-5-Resume.md`
- **Contexte Sessions 1-3:** `Contexte-Sessions-1-a-3.md`

---

# ⚠️ POINTS À CLARIFIER LORS IMPLÉMENTATION

1. **Format fichiers patterns** (CSV, JSON, YAML ?)
2. **Algorithmes ML spécifiques** (quels 2 régression, quels 2 classification ?)
3. **Structure exacte tableau statique** arrondissements adjacents
4. **Format journal de traçabilité** (JSON, YAML ?)
5. **Noms exacts classes/méthodes** (conventions de nommage)
6. **Formule exacte division agression par prix m²** (ratio, seuils ?)
7. **Formule exacte diminution probabilités régimes par prix m²**
8. **Détails implémentation vecteurs statiques** (calcul depuis patterns Paris)
9. **Validation probabilités cibles** après toutes modulations
10. **Gestion événements graves** (stockage, accès, performance)

---

**Créé:** 26 Janvier 2026  
**Statut:** ✅ Prêt pour implémentation  
**Prochaine étape:** Passer à l'agent Architect/Dev
