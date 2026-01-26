# 📋 CONTEXTE COMPLET : SESSIONS 1.1 → 3.3
## Brainstorming Projet BSPP - Simulation & Prédiction Catastrophes Paris

**Date de création:** 24-25 Janvier 2026  
**Statut:** Fin Session 3 (Scenarios), avant Session 4 (Interactions)  
**Niveau de détail:** COMPLET - Permet relais à autre agent/personne

---

# 🎯 RÉSUMÉ EXÉCUTIF (2 min de lecture)

## Objectif Global
Créer une **simulation Monte-Carlo crédible d'incidents urbains Paris** (incendies, accidents, agressions) jour-à-jour sur microzones, puis **entraîner RandomForest** pour prédire "catastrophe" vs "normal" mois suivant par arrondissement.

## Public Cible
- **Commandant BSPP** (données réalistes, modifiables, exportables)
- **Data Scientist** (ML défi intéressant, pas trivial)
- **Manager Opérations** (POC étudiant montrer compétences)
- **Innovateur Tech** (architecture extensible, Phase 2/3)

## Scope MVP
- **Durée:** 90 jours (3 mois)
- **Granularité:** 100 microzones (5 par arr × 20 arr)
- **Données:** 100% synthétiques (Poisson + aléatoire + variables cachées)
- **Output ML:** Classification 3 classes (normal / pré-catastrophe / catastrophe)
- **Temps dev:** 3-4 jours étudiant

---

# 🔵 SESSION 1 - ESSENCE (Échanges 1.1, 1.2, 1.3)

## Ce Qu'On A Fait
Exploration ouverte → cristallisation vision → **13 titres structurés** définissant le projet.

## Les 13 Titres Originaux (1.3)

### BLOC A - Simulation & ML (5 titres)
- **A.1** : Chaque run différent → variabilité, authenticité (pas déterministe)
- **A.2** : Séparation génération vecteurs ↔ prédiction morts (deux fonctions distinctes)
- **A.3** : Entiers naturels jour-à-jour, cascade logique (pas flottants, cohérence temporelle)
- (Implicites : saisons, variables cachées, événements)

### BLOC B - Périmètre MVP (2 titres)
- **B.1** : Carte + stats temps réel, simulation 3-4j sans ML (juste vecteurs)
- **B.2** : Synthétiques Poisson plausibles Paris, **interchangeables vraies données Phase 2**

### BLOC C - Implémentation (5 titres)
- **C.1** : 4 niveaux data interconnectés (statiques → mobiles → features → labels)
- **C.1.a** : Seuil acceptabilité pondéré population (pas absolu)
- **C.1.b** : Mode Train vs Predict (joblib sauvegarde modèles)
- **C.2** : Scikit-Learn RandomForest Classification (pas TensorFlow overkill)
- **C.3** : Boucle jour-à-jour cascade variables cachées

### BLOC D - Contexte BSPP (2 titres)
- **D.1** : Angle quantitatif (vecteurs incidents) + ML (prédiction) = synérgie
- **D.2** : Architecture prête vraies données (CSV import Phase 2)

---

# 🟢 SESSION 2 - PERSONAS (Échanges 2.1, 2.2)

## Objectif
Approfondir **4 personas utilisateurs** → répondre "pourquoi ce choix ?" pour chaque décision.

## Échange 2.1 : Réponses aux 4 Personas

### Commandant BSPP
- ✅ Données inventées mais réalistes (Poisson, prix m², démographie)
- ✅ Modifiables via UI (scénario pessimiste/moyen/optimiste, variabilité)
- ✅ Exportable CSV, intégrables vraies données Phase 2
- **Insight:** "Je dois montrer mes compétences, pas révolutionner la prédiction"

### Data Scientist
- ✅ Vecteur = [grave, moyen, bénin] (structure simple, puissante)
- ✅ Position dans vecteur = gravité (plus la position élevée, plus grave)
- ✅ ML apprend patterns simulation MAIS aléa + variables cachées atténuent codépendance
- **Insight:** "Je ne vais pas révolutionner en 1 mois, montrer compétences ML"

### Manager Opérations
- ✅ POC étudiant pragmatique (3-4 jours, 1 mois solo possible)
- ✅ Exploration données, pas système production
- ✅ Architecture extensible (Phase 2, Phase 3 possibles)
- **Insight:** "J'ignore missions exactes BSPP, c'est montrer compétences"

### Innovateur Tech
- ✅ Saisons/météo intégrer intelligemment (Phase 2)
- ✅ **CRITIQUE : Événements POSITIFS** (fin travaux, amélioration) sinon système négatif
- ✅ Boucle rétroactive long-terme possible Phase 2
- **Insight:** "Faut ajouter positif, pas juste catastrophes"

### Découvertes Majeures 2.1
1. **Vecteur [grave, moyen, bénin] par position** = structure de base
2. **Deux outputs différents** : heatmap quantitatif + probabilité % ML
3. **Événements positifs = CRITIQUES** (non pas juste négatif)
4. **Saisons/météo Phase 2** (mais structure MVP prête)
5. **POC étudiant pragmatique** (pas révolution, montrer compétences)

---

## Échange 2.2 : 5 Whys Approfondis

### Sujet 1 : Seuil Event Majeur & Agrégation

**Q:** Si vecteur[grave] ≥ 1 → event majeur, comment agréger arrondissement ?

**Réponse cristallisée :**
```
Jour 5, Arr_11 (5 microzones) :
  MZ_11_01 : incendies (1, 0, 2) → grave = 1
  MZ_11_02 : incendies (0, 1, 3) → grave = 0
  MZ_11_03 : incendies (2, 0, 1) → grave = 2
  ...
→ ∑graves = 1+0+2+... = N
→ Si N ≥ 1 → Créer N events majeurs arr_11 (indépendants, pas 1 mega-event)
```

**Caractéristiques events (probabilistes) :**
- Traffic slowdown (70% prob, ×2 temps, 4j, radius 2)
- Cancel sports (30% prob, 2j)
- Increase bad vectors (50% prob, +30%, 5j, radius 3)
- Kill pompier (5% prob)

### Sujet 2 : Granularité Semaine vs Mois

**Q:** Pourquoi 4 semaines pour patterns reproductibles ?

**Réponse :**
- 2 semaines = trop faible (juste tendance, pas patterns)
- 4 semaines = **sweet spot** (cycles détectables)
- Runs doivent être longs (12-24 mois pour voir saisons complètes)

### Sujet 3 : Événements Positifs

**Q:** Quels types ? Quand déclenchés ?

**Réponse :**
- **Types :** Fin travaux, nouvelle caserne, nouvelle équipe pompiers, meilleure signalisation, amélioration matériel, programme violence
- **Trigger :** Contrôle via paramètres (pessimiste = -événements positifs, optimiste = +)
- **Boucle rétroactive Phase 2 :** Moins incidents → travaux finissent plus vite → encore moins incidents (cycle vertueux)

### Sujet 4 : Formule Label

**Q:** Comment calculer morts (casualties) sans double comptage ?

**Réponse :**
```python
score = SUM(morts_events) + 0.5 × SUM(blessés_graves_events)
```
**CRITIQUE :** Casualties = **SEULEMENT events** (pas vecteurs, évite double comptage)

### Sujet 5 : Saisons

**Q:** Incendie hiver +30% ? Agression été +20% ?

**Réponse :**
```
Été : +20% agressions, -10% incendies
Hiver : +30% incendies, -20% agressions
Insérer dans features semaines ET labels mois
```

### Découvertes Majeures 2.2
1. ✅ **Agrégation par arrondissement** (∑graves microzones)
2. ✅ **Events indépendants avec caractéristiques probabilistes**
3. ✅ **Golden Hour critique** (>60min = +30% morts)
4. ✅ **Boucle rétroactive events positifs** (Phase 2)
5. ✅ **Saisons avec impact λ** (MVP structure, Phase 2 vraies valeurs)
6. ✅ **Casualties = events SEULEMENT** (formule label OK)

---

## Les 20 Titres Finaux (2.2)

Remplaçant les 13 originaux, intégrant tous les approfondissements :

### BLOC A - Simulation (7 titres)
- **A.1** : Montecarlo + Aléa + Variables Cachées (Fatigue, Congestion, Golden Hour) = Patterns 4 Semaines
- **A.2** : StateCalculator (Vecteurs + Events) ≠ LabelCalculator (Casualties Events Seulement) : Double-Comptage Évité
- **A.3** : Vecteurs [Grave, Moyen, Bénin] par Microzone : Agrégation Arr + ∑grave≥1 = event
- **A.3.a** : Events Majeurs Caractéristiques Probabilistes (Durée, Casualties, Traffic×2, Cancel Sports, +Vecteurs Mauvais, Kill Pompier)
- **A.3.b** : Éléments Secondaires Infrastructure (Pompiers, Casernes, Temps Circulation, Golden Hour >60min = +30% morts)

### BLOC B - Périmètre MVP (2 titres)
- **B.1** : Heatmap Animée (Jour 1→N, Microzones) + Classification 3 Classes (Normal/Pré-Catastrophe/Catastrophe) : MVP 3-4j
- **B.2** : Synthétiques Poisson(λ) Paris + Saisons (Fausse MVP, Vraie Phase 2) : CSV Upload Phase 2

### BLOC C - Implémentation (8 titres)
- **C.1** : 5 Niveaux : Statiques (Arr, Pop, Infra) + Mobiles (Vecteurs Jour) + Events Majeurs (Jour) + Features Hebdo (StateCalculator) + Labels Mois (LabelCalculator Casualties)
- **C.1.a** : Seuil Catastrophe : 3.25 Morts/Arr/Mois × (Pop_Arr / Pop_Moyenne) = Pondération Auto
- **C.1.b** : Mode Train (Multi-Runs joblib, MVP 1 run, Phase 2 10+) vs Mode Predict (Load+Use) : Expansion Progressive
- **C.1.c** : Durée Simulations : MVP 90j vs Phase 2 12-24 mois (Voir Saisons)
- **C.2** : RandomForest Classification 3 Classes + Confusion Matrix, ROC, SHAP
- **C.2.a** : Scikit-Learn MVP vs TensorFlow Overkill vs XGBoost Phase 2+ (Régression)
- **C.3** : Boucle Jour 1→N : Génération Poisson → Agrégation Arr → Events → Update Cachées → Features → Heatmap/Stats
- **C.3.a** : Events Indépendants par Microzone (4 graves = 4 events, pas 1 mega)

### BLOC D - Contexte BSPP (4 titres)
- **D.1** : Deux Outputs Utilisateur : Heatmap Charge Jour-à-Jour (Quantitatif) + Probabilité % Catastrophe Mois Suivant (ML)
- **D.2** : POC Étudiant Montrer Compétences ML : Synthétiques MVP (90j) → Vraies Données Phase 2 (Une Ligne Config)
- **D.3** : Boucle Rétroactive Phase 2 : Moins Incidents → Events Positifs → Cycle Vertueux
- **D.4** : Saisons (MVP: Étiquette / Phase 2: Impact λ) - Été/Hiver différencié

---

# 🟣 SESSION 3 - SCENARIOS (Échanges 3.1, 3.2, 3.3)

## Objectif
Anticiper **cas critiques, edge cases, boucles infinies, overflow** → solidifier architecture avant implémentation.

---

## Échange 3.1 : Game Changers

### Découverte Majeure 1 : Entités Infrastructure Géolocalisées

**Impact :** Casernes + Hôpitaux deviennent entités critiques.

```python
# NOUVELLES ENTITÉS
df_casernes = {
    'caserne_id', 'nom', 'arr', 'lat', 'lon', 
    'nb_pompiers', 'fatigue', 'rayon_couverture_km'
}

df_hopitaux = {
    'hopital_id', 'nom', 'lat', 'lon', 'capacite_urgences'
}

# MATRICES TRAJECTOIRES PRÉCALCULÉES (10,000 trajets)
df_trajets_caserne_microzone = {
    'caserne_id', 'microzone_id', 'distance_km', 'temps_base_min',
    'microzones_traversees'  # Liste microzones sur trajet
}

df_trajets_microzone_hopital = {
    'microzone_id', 'hopital_id', 'distance_km', 'temps_base_min',
    'microzones_traversees'
}
```

**Golden Hour Dynamique :**
```
temps_trajet_reel = temps_base × ∏(congestion_microzone_traversee)
temps_total = temps_trajet + temps_traitement + temps_hopital_retour
if temps_total > 60 min → casualties × 1.3
```

### Découverte Majeure 2 : Features Hebdomadaires À Redéfinir

**Problème :** "Dégâts personnes / matériels" = pas ostensibles, difficiles à obtenir réellement.

**Solution :** Features **simples, remontées facilement par BSPP** :
```python
features_hebdo = {
    'incendies_benin_moyen': SUM(benin + moyen),
    'incendies_grave': SUM(grave),
    'accidents_benin_moyen': SUM(benin + moyen),
    'accidents_grave': SUM(grave),
    'agressions_benin_moyen': SUM(benin + moyen),
    'agressions_grave': SUM(grave)
}
```
**6 features** simples, facilement remontables, pas Golden Hour dedans (trop complexe pour temps réel).

### Découverte Majeure 3 : Trois Fonctions Nucléaires

**Priorisation :**
1. **Fonction Génération J+1** (PRIORITÉ ABSOLUE) : Créer vecteurs jour-à-jour
2. **Fonction Features Hebdo** (À redéfinir) : Calculer 6 features ostensibles
3. **Fonction Labels Mois** (VALIDÉE) : morts + 0.5×blessés graves → classes

### Découverte Majeure 4 : Saisonnalité MVP Obligatoire

**Avant :** Saisons Phase 2 (optionnel)  
**Après :** Saisons **MVP OBLIGATOIRE** pour cohérence

**Raison :** Sans saisons, simulation "parle pas aux pompiers" (pas réaliste). Avec saisons = patterns reconnaissables.

---

## Échange 3.2 : Formules Finalisées

### Décision 1 : Infrastructure MVP Simplifié ✅

```
✅ Casernes fictives (1 par arrondissement = 20)
✅ Pas de géolocalisation (distance Manhattan)
✅ Golden Hour simplifié (aléatoire 30-90 min)
✅ Trajets précalculés (excellente base Phase 2)
✅ Temps dev : MVP 3-4 jours maintenu
```

### Décision 2 : Features Hebdomadaires = 6 features ostensibles ✅

```python
def calcul_features_hebdo(arr, semaine):
    return {
        'incendies_benin_moyen': ...,  # Facile à compter
        'incendies_grave': ...,
        'accidents_benin_moyen': ...,
        'accidents_grave': ...,
        'agressions_benin_moyen': ...,
        'agressions_grave': ...
    }
```

### Décision 3 : Lambda Base = Catégoriel Prix m² ✅

```python
# Basé données réelles Paris 2026
if prix_m2 > 12000:  # Quartiers riches
    lambda_incendies = 0.8
    lambda_accidents = 0.7
    lambda_agressions = 0.5
elif prix_m2 > 8500:  # Quartiers moyens
    lambda_incendies = 1.2
    lambda_accidents = 1.3
    lambda_agressions = 1.5
else:  # Quartiers pauvres
    lambda_incendies = 1.5
    lambda_accidents = 1.6
    lambda_agressions = 2.0
```

### Décision 4 : Influence Voisins = Moyenne Pondérée ✅

```python
# 8 voisins immédiats (radius 1)
# Pondérés par type incident (grave ×1.0, moyen ×0.5, bénin ×0.2)
# + Corrélations croisées (incendie → accidents)
# × Variabilité locale (fort=0.7, moyen=0.5, faible=0.3)
```

### Décision 5 : Répartition Gravités = Multinomial Exponentiel ✅

```python
# 80% bénin, 18-19% moyen, 1-2% grave
# Multinomial conserve total incidents par type

# Distribution cible :
# - Bénin : ~tous les 5 jours/microzone
# - Moyen : ~tous les 5-10 jours/microzone
# - Grave : ~1 fois par an/microzone (très rare)
```

### Fonction Génération J+1 Complète ✅

```python
def generer_vecteur_j_plus_1(microzone_id, jour_j, saison, scenario, variabilite):
    # 1. Lambda base (prix m², scenario)
    # 2. Lambda saison (hiver +30% incendies, été +20% agressions, etc.)
    # 3. Lambda voisins (8 microzones radius 1 + corrélations)
    # 4. Lambda cachées (fatigue, congestion)
    # 5. Lambda final (produit tous)
    # 6. Poisson(lambda_final) → total incidents
    # 7. Multinomial(total, [grave%, moyen%, bénin%]) → vecteur [grave, moyen, bénin]
    
    return vecteur_incendies, vecteur_accidents, vecteur_agressions
```

---

## Échange 3.3 : Edge Cases & Stabilité

### Réponses Critiques Données

#### Q3.3.1 - Cap Maximum Incidents
**Réponse :** Pas de cap quotidien utile
- Vecteurs ne s'additionnent pas (régénération jour-à-jour)
- Aléatoire empêche explosions systématiques
- Avec 100 MZ, toujours "un peu de grave quelque part" statistiquement
- Distribution ciblée : grave très rare (1 fois/an/MZ)

#### Q3.3.2 - Jours Simulation
**Réponse :** Max **10,000 jours** accepté, mais MVP pragmatique **90-365j**
- 30j minimum (besoin features hebdo)
- 365j = voir saisons complètes
- 10,000j = pour cas extrêmes/recherche

#### Q3.3.3 - Variabilité Locale
**Réponse :** **3 niveaux fixes** (menu déroulant)
- Faible (0.3) : moins influence voisins
- Moyen (0.5) : influence normale
- Important (0.7) : influence forte

#### Q3.3.4 - Saisons
**Réponse :** Toujours démarrage **1er janvier**
- Jour 1-80 : Hiver
- Jour 81-260 : Intersaison
- Jour 261+ : Été
- Simple, lisible, pas calendrier réel complexe

#### Q3.3.5 - Cascade Catastrophique
**Réponse :** **Pas de cascade infinie** grâce à :
- Aléatoire systématique dans génération
- Events indépendants spatialement
- Fatigue pompiers diminue disponibilité (pas mobilisables = réponse réduite)
- Baisse progressive effectifs utilisés

#### Q3.3.6 - Événements Positifs
**Réponse :** **Poisson 60 jours** sur Paris entière
- En moyenne 1 event positif tous les 60j
- Pas de rétroaction complexe MVP
- Phase 2 : possibilité plus sophistiquée

#### Q3.3.7 - Données Réelles BSPP
**Réponse :** Pas d'accès actuellement
- MVP = 100% synthétique (pas objectif)
- Phase 2 = travail ensemble pour vraies données
- Même format que synthétique (permettra swap facile)

#### Q3.3.8 - Features Hebdo Réalistes
**Réponse :** Session 4 déterminera **3-4 features vraiment utiles**
- Doit ressembler ce qu'officier/chef centre peut avoir facilement
- Pas trop de variables (4-6 maximum)
- Permettre patterns ML (pas surparamétré)

---

## Synthèse Session 3

### Découvertes Fondamentales
1. ✅ Fréquences visées : bénin ~tous 5j, moyen ~tous 5-10j, grave ~1 fois/an (par microzone)
2. ✅ Pas de caps quotidiens (structure Poisson j-à-j empêche explosions)
3. ✅ Saisons MVP obligatoire (cohérence), calendrier simple (1er janvier)
4. ✅ Variabilité locale = 3 niveaux (dropdown)
5. ✅ Pas de cascade infinie (aléatoire + indépendance spatiale + fatigue pompiers)
6. ✅ Events positifs rares (Poisson 60j Paris-wide)
7. ✅ Features hebdo = 6 simples (à affiner Session 4)

### Ce Qu'on Ne Changeait Plus
- **Fonction génération J+1** : 7 étapes figées
- **Fonction labels mois** : morts + 0.5×blessés (validée)
- **Structure vecteurs** : [grave, moyen, bénin] (stable)
- **Agrégation arrondissement** : ∑graves microzones (décisive)

### Ce Qui Attend Session 4
- **Flux utilisateur** (démarrage, paramètres, outputs)
- **Interface MVP** (Python script / Notebook / Streamlit)
- **Visualisations** (heatmap, stats, confusion matrix)
- **Features vraiment réalistes** (3-4 variables critiques)

---

# 📊 ARCHITECTURE CRISTALLISÉE (État Final Session 3)

## Données Statiques
```python
df_statiques = {
    'arr': ID arrondissement (1-20)
    'microzone_id': ID microzone (1-100)
    'population': Habitants arr
    'prix_m2': Prix m² arrondissement (données réelles 2026)
    'nb_pompiers': Par arr (fictif MVP, réel Phase 2)
}
```

## Données Mobiles (Jour à Jour)
```python
df_mobiles_jour_j = {
    'microzone_id': (1-100)
    'jour': (0-89 pour MVP 90j)
    'incendies': [grave, moyen, bénin]
    'accidents': [grave, moyen, bénin]
    'agressions': [grave, moyen, bénin]
    'fatigue': (0-1, pompiers)
    'congestion': (×factor, routes)
}
```

## Events Majeurs
```python
df_events = {
    'event_id': Identifiant unique
    'type': ['incendie', 'accident', 'agression']
    'arr': Arrondissement
    'jour': Jour déclenchement
    'duration': Jours duree
    'casualties_base': Morts base
    'characteristics': Traffic×2, cancel_sports, kill_pompier (prob)
}
```

## Features Hebdomadaires (StateCalculator)
```python
df_features_hebdo = {
    'arr': (1-20)
    'semaine': (1-4 pour 28j)
    'incendies_benin_moyen': Count
    'incendies_grave': Count
    'accidents_benin_moyen': Count
    'accidents_grave': Count
    'agressions_benin_moyen': Count
    'agressions_grave': Count
}
```

## Labels Mensuels (LabelCalculator)
```python
df_labels_mois = {
    'arr': (1-20)
    'mois': (1-3 pour 90j)
    'score': SUM(morts) + 0.5 × SUM(blesses_graves)
    'seuil_arr': 3.25 × (pop_arr / pop_moyenne)
    'classe': ['normal', 'pre-catastrophe', 'catastrophe']
}
```

## Trois Fonctions Nucléaires

### Fonction 1 : Génération Jour J+1 (7 étapes)
1. Lambda base (prix m², scenario)
2. Lambda saison (modulation hiver/été)
3. Lambda voisins (8 microzones + corrélations)
4. Lambda cachées (fatigue, congestion)
5. Lambda final (produit)
6. Poisson(lambda_final) → totaux
7. Multinomial → [grave, moyen, bénin]

### Fonction 2 : Features Hebdomadaires (6 features)
- Simple COUNT par gravité × type
- Pas Golden Hour, pas calculs complexes
- Input ML training

### Fonction 3 : Labels Mensuels (3 classes)
- Score = morts + 0.5×blessés (events seulement)
- Seuil pondéré population
- Output ML training/prédiction

---

# 🔄 PROCHAINES ÉTAPES

## Session 4 - INTERACTIONS
**Objectif :** Définir flux utilisateur (démarrage → résultats).

**10 Questions posées :**
1. Type interface (script / notebook / Streamlit / CLI)
2. Modes utilisation (Exploration / Entraînement / Prédiction)
3. Paramètres configurables complets
4. Validations & feedback inputs
5. Affichage progression simulation
6. Interruption & sauvegardes
7. Outputs & visualisations (liste complète)
8. Heatmap détails (quoi, comment, interactivité)
9. Mode prédiction & CSV Phase 2
10. Évolutions UI Phase 2/3

**Attendu :** Après Session 4 = workflow utilisateur complet, UI décisions, features finales.

## Session 5 - VALIDATION FINALE BRAINSTORM
**Objectif :** Synthèse finale avant passage MAPPING (Étape 2 BMAD).

**Attendu :** Architecture figée, prêt implémentation.

---

# 📖 GLOSSAIRE TERMES CLÉS

| Terme | Définition |
|-------|-----------|
| **Vecteur** | [grave, moyen, bénin] pour un type incident (incendie, accident, agression) par microzone |
| **Microzone** | ~2km² Paris (100 total, 5 par arr) |
| **Event Majeur** | Incident grave déclenché si ∑grave ≥ 1 par arr |
| **λ (Lambda)** | Paramètre Poisson, "taux moyen incidents" |
| **Montecarlo** | Génération aléatoire jour-à-jour (pas déterministe) |
| **Variables Cachées** | Fatigue pompiers, congestion routes (affectent probabilités) |
| **Golden Hour** | >60min intervention = +30% morts |
| **StateCalculator** | Calcul 6 features hebdo (input ML) |
| **LabelCalculator** | Calcul 3 classes mensuel (output ML) |
| **Catastrophe** | score ≥ seuil_arr (classe ML) |

---

# ✅ POINTS FIGÉS (Ne Plus Changer)

1. **Vecteur [grave, moyen, bénin]** - Structure stable
2. **100 microzones, 5 par arr** - Granularité OK
3. **Poisson + aléatoire jour-à-jour** - Génération acceptée
4. **Features 6 simples** - Remontées facilement
5. **Labels : morts + 0.5×blessés** - Formule validée
6. **RandomForest Classification** - Algo choisi
7. **Saisons MVP** - Obligatoire cohérence
8. **Events positifs rare** - Poisson 60j
9. **Golden Hour simplifié** (30-90min aléatoire)
10. **Cascades empêchées** par aléatoire + indépendance

---

# ⚠️ POINTS ENCORE OUVERTS (Session 4+)

1. **Interface exacte** (script vs Streamlit vs autre)
2. **3-4 features vraiment réalistes** (Session 4 critique)
3. **Heatmap visuels** (couleurs, interactivité)
4. **CSV import Phase 2** (format exact)
5. **Évolutions UI Phase 2/3** (roadmap)

---

**Créé par:** Brainstorm Session 1.1 → 3.3  
**Relais à:** Agent/personne Session 4 INTERACTIONS  
**Date:** 25 Janvier 2026  
**Statut:** ✅ COMPLET, RELAIS PRÊT