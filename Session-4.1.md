# 📋 CONTEXTE RAPIDE - SESSION 4
## Projet BSPP - Simulation & Prédiction Catastrophes Paris

**Date:** 25 Janvier 2026  
**Statut:** Session 4.1 complétée, en cours Session 4.2  
**Objectif:** Définir flux utilisateur et interface Streamlit

---

# 🎯 VISION GLOBALE (30 secondes)

**Projet:** Simulation Monte-Carlo d'incidents urbains Paris (incendies, accidents, agressions) jour-à-jour sur 100 microzones, puis entraînement RandomForest pour prédire "catastrophe" vs "normal" mois suivant par arrondissement.

**Public:** Commandant BSPP, Data Scientist, Manager Opérations, Innovateur Tech  
**Scope MVP:** 90 jours, 100 microzones (5 par arr × 20 arr), données 100% synthétiques, classification 3 classes, temps dev 3-4 jours

---

# 🏗️ ARCHITECTURE DONNÉES (5 niveaux)

## 1. **Data Fixe Géographique**
```python
- arrondissement (1-20)
- microzone_id (1-100, 5 par arr)
- population (habitants arr)
- prix_m2 (données réelles Paris 2026)
- nb_pompiers (par arr, fictif MVP)
- casernes (1 par arr MVP, géolocalisées Phase 2)
- hôpitaux (géolocalisés)
```

## 2. **Data Fixe Non-Géographique**
```python
- variabilité_locale (faible=0.3, moyen=0.5, important=0.7)
- trajets_précalculés (caserne→microzone, microzone→hôpital)
  - distance_km, temps_base_min
  - microzones_traversees (liste)
```

## 3. **Data Mobile Géographique Journalière (Microzones)**
```python
# Par microzone, par jour
- incendies: [grave, moyen, bénin]
- accidents: [grave, moyen, bénin]
- agressions: [grave, moyen, bénin]
- fatigue_pompiers (0-1)
- congestion_routes (×factor)
- état_ralentissement (par microzone jour J)
```

## 4. **Data Mobile Géographique Hebdomadaire (Arrondissements)**
```python
# Features pour ML (6 features simples)
- incendies_benin_moyen (SUM)
- incendies_grave (SUM)
- accidents_benin_moyen (SUM)
- accidents_grave (SUM)
- agressions_benin_moyen (SUM)
- agressions_grave (SUM)
```

## 5. **Data Mobile Géographique Mensuelle (Arrondissements)**
```python
# Labels pour ML (3 classes)
- score = SUM(morts_events) + 0.5 × SUM(blessés_graves_events)
- seuil_arr = 3.25 × (pop_arr / pop_moyenne)
- classe: ['normal', 'pre-catastrophe', 'catastrophe']
```

## 6. **Data Mobile Ponctuelle (Events Majeurs)**
```python
# Déclenchés si ∑grave ≥ 1 par arrondissement
- event_id, type, arr, jour
- duration, casualties_base
- characteristics (probabilistes):
  - Traffic×2 (70% prob, 4j, radius 2)
  - Cancel sports (30% prob, 2j)
  - Increase bad vectors (50% prob, +30%, 5j, radius 3)
  - Kill pompier (5% prob)
```

---

# ⚙️ FONCTION GÉNÉRATION J+1 (7 étapes)

```python
def generer_vecteur_j_plus_1(microzone_id, jour_j, saison, scenario, variabilite):
    # 1. Lambda base (prix m², scenario)
    #    - Quartiers riches (prix_m2 > 12000): λ faible
    #    - Quartiers moyens (8500-12000): λ moyen
    #    - Quartiers pauvres (< 8500): λ élevé
    
    # 2. Lambda saison (hiver +30% incendies, été +20% agressions)
    #    - Hiver: jour 1-80
    #    - Intersaison: jour 81-260
    #    - Été: jour 261+
    
    # 3. Lambda voisins (8 microzones radius 1)
    #    - Pondération: grave×1.0, moyen×0.5, bénin×0.2
    #    - Corrélations croisées (incendie → accidents)
    #    - × variabilité_locale (0.3/0.5/0.7)
    
    # 4. Lambda cachées (fatigue pompiers, congestion routes)
    
    # 5. Lambda final = produit de tous
    
    # 6. Poisson(λ_final) → total incidents
    
    # 7. Multinomial(total, [grave%, moyen%, bénin%]) → [grave, moyen, bénin]
    #    Distribution: ~80% bénin, ~18-19% moyen, ~1-2% grave
    
    return vecteur_incendies, vecteur_accidents, vecteur_agressions
```

**Fréquences visées:**
- Bénin: ~tous les 5 jours/microzone
- Moyen: ~tous les 5-10 jours/microzone
- Grave: ~1 fois par an/microzone (très rare)

---

# 🔄 BOUCLE SIMULATION

```
Jour 1 → N:
  1. Génération Poisson → vecteurs [grave, moyen, bénin] par microzone
  2. Agrégation arrondissement (∑graves microzones)
  3. Si ∑grave ≥ 1 → Créer N events majeurs (indépendants)
  4. Update variables cachées (fatigue, congestion)
  5. Calcul features hebdo (si semaine complète)
  6. Calcul labels mois (si mois complet)
  7. Heatmap/Stats affichage
```

---

# 📊 POINTS FIGÉS (Sessions 1-3)

## Structure Stable
- ✅ Vecteur [grave, moyen, bénin] par type incident
- ✅ 100 microzones, 5 par arrondissement
- ✅ Poisson + aléatoire jour-à-jour (pas déterministe)
- ✅ Saisons MVP obligatoire (démarrage 1er janvier)
- ✅ Variabilité locale = 3 niveaux (dropdown)
- ✅ Events positifs rares (Poisson 60j Paris-wide, pas rétroaction MVP)
- ✅ Golden Hour simplifié (30-90min aléatoire MVP)

## Formules Validées
- ✅ Labels: `score = morts + 0.5×blessés` (events seulement, évite double comptage)
- ✅ Seuil catastrophe: `3.25 × (pop_arr / pop_moyenne)` (pondération auto)
- ✅ Features hebdo: 6 simples (COUNT par gravité × type)
- ✅ Agrégation arr: ∑graves microzones → N events indépendants

## Contraintes Techniques
- ✅ Pas de caps quotidiens (Poisson j-à-j empêche explosions)
- ✅ Max 10,000 jours accepté, MVP pragmatique 90-365j
- ✅ Pas de cascade infinie (aléatoire + indépendance spatiale + fatigue)
- ✅ RandomForest Classification 3 classes (Scikit-Learn MVP)

---

# 🖥️ SESSION 4.1 - DÉCISIONS INTERFACE

## Interface Choisie
- ✅ **Streamlit** (application web interactive)

## Mode Principal
- ✅ **Mode Prédiction** (le "jeu")
  - Génération Monte Carlo autonome
  - Données aléatoires pour prédiction
  - Génération mensuelle (≥1 mois) avec 4 semaines précédentes comme features
  - Choix modèle ML: **régression OU classification**
  - Comparaison: modèles calculés fonctions internes vs modèles ML entraînés
  - Réutilisation modèles: sauvegarde/chargement pour nouvelles générations

### Flux Entraînement ML (Clarification)

**Pendant le Run:**
- Affichage animé: Carte Paris, carte incidents, arrondissements avec stats
- Compteur jours: "Jour X / Total" (affichage dynamique)
- Compteur runs: "Run 1/50" à droite du compteur jours (rectangle bas)
- Paramètre "nb run": Modifiable par utilisateur (affiché en haut, valeur par défaut)

**Fin des Jours:**
- Affichage dynamique s'arrête (plus d'animation 1/3 seconde)
- Calcul rapide (sans affichage graphique):
  - Suite Monte-Carlo journalière
  - Features hebdomadaires
  - Labels mensuels

**Entraînement:**
- Modèle s'entraîne: Features hebdo → Labels mensuels
- Granularité: Par arrondissement (20 arrondissements)
- Répétition: 50 runs (ou nombre choisi par utilisateur)

**Sauvegarde:**
- Emplacement: `models/regression/` ou `models/classification/`
- Nom: `{algo}_{numero_entrainement}_{params}.joblib`
- Métadonnées: Nom algo, numéro entraînement, paramètres génération données

## Paramètres Configurables
- ✅ Type ML (régression/classification)
- ✅ Durée simulation
- ✅ Scénario (pessimiste/moyen/optimiste)
- ✅ Variabilité locale (faible/moyen/important)
- ⚠️ Nombre de runs: non essentiel MVP

---

# 🖥️ SESSION 4.2 - VALIDATIONS, PROGRESSION & SAUVEGARDES

## 4. Validations & Feedback Inputs
- ✅ **Message d'erreur** si paramètres invalides (nécessaire)
- ❌ Validation proactive des paramètres (pas nécessaire)
- ✅ **Confirmation relance simulation** après 2 ans (warning)
- ❌ Avertissement modèle non entraîné (pas nécessaire, interface gère)

### Interface Modèles ML (Haut droite)
**Ligne supérieure:**
- Checkbox "Train a model"
  - Si coché → Choix type ML (classification/régression)
  - Menu sélection: **2 modèles ML** (sur 4 disponibles, utilisateur voit les 2 plus intelligents)
  - Phase 2: réglage hyperparamètres

**Ligne inférieure:**
- Bouton rond (radio) "Use a prediction model" (un seul sélectionnable)
  - Choix classification OU régression
  - Chargement modèle depuis fichiers:
    - `models/classification/` (fichiers modèles classification)
    - `models/regression/` (fichiers modèles régression)
  - Chaque modèle sauvegardé contient:
    - Nom modèle ML utilisé
    - Numéro entraînement
    - Nombre jours d'entraînement
    - Accuracy au moment entraînement

## 5. Affichage Progression Simulation
- ⚠️ Barre de progression: pas super utile
- ✅ **Jours simulés / Total** (affichage important)
- ⚠️ Indicateur temps restant: pour plus tard
- ✅ **Pop-up événements majeurs** (incidents graves + events majeurs)
- ✅ **Icônes sur carte** pour incidents graves et événements
  - Type (accident, feu, agression)
  - Microzone concernée
  - Type événement, type incident, conséquences
- ✅ **Colonne gauche**: liste événements/incidents qui s'ajoutent pendant simulation
  - Utilisateur peut analyser cette colonne
  - Caractéristiques des éléments
- ✅ **Vitesse simulation**: 1 jour = 1/3 seconde (0.33s)
  - Carte change en temps réel avec événements
  - Jours évoluent visuellement
- ✅ **Codes couleur carte**:
  - **Feu**: jaune (bénin), orange (moyen), rouge (grave)
  - **Accident**: beige clair (bénin), marron clair (moyen), marron foncé (grave)
  - **Agression**: gris clair (bénin), gris moyen (moyen), gris très foncé (grave)
- ✅ **Priorité affichage carte**:
  - Vecteur avec nombre le plus élevé
  - Priorité au plus grave
  - Si même niveau gravité: **Feu > Agression > Accident**
- ✅ **Carte découpage**: 100 microzones
  - Chercher carte existante (arrondissements découpés en ~100 microzones)
  - Si n'existe pas: créer nous-mêmes

## 6. Interruption & Sauvegardes
- ✅ **Interrompre simulation** (possible)
- ✅ **Sauvegarder état** (vecteurs, événements, variables cachées)
- ✅ **Export résultats partiels** (dans frame pause)

---

# ⚠️ POINTS ENCORE OUVERTS (Session 4.3)

## Session 4.3 (À venir)
- ❓ Outputs & visualisations complètes (détails)
- ❓ Heatmap détails (interactivité, filtres)
- ❓ Mode prédiction & CSV Phase 2 (format exact)
- ❓ Évolutions UI Phase 2/3 (roadmap)

## Features Hebdo Finales
- ⚠️ Session 3 a défini 6 features simples
- ⚠️ Session 4 doit valider 3-4 features **vraiment réalistes** et utilisables

---

# 🔗 LIENS ARCHITECTURE (Schéma PDF)

```
Data Fixe Géographique
  ↓ (Initialise)
Data Mobile Journalière (Monte-Carlo)
  ↓ (Génère)
Data Mobile Hebdomadaire (Features)
  ↓ (Permet de calculer)
Data Mobile Mensuelle (Labels)
  ↓ (Permet de prédire)

Data Fixe Non-Géographique
  ↓ (Modifie)
Data Mobile Journalière

Events Majeurs
  ↓ (Apparaît régulièrement et aléatoirement)
Data Mobile Journalière
  ↓ (Influence)
Variables Cachées (fatigue, congestion)
  ↓ (Influence)
Fonction Génération J+1

Casernes/Hôpitaux
  ↓ (Utilise)
Trajets Précalculés
  ↓ (Calcul Golden Hour + aléatoire)
Casualties Events
```

---

# 📖 GLOSSAIRE RAPIDE

| Terme | Définition |
|-------|-----------|
| **Vecteur** | [grave, moyen, bénin] pour un type incident par microzone |
| **Microzone** | ~2km² Paris (100 total, 5 par arr) |
| **Event Majeur** | Incident grave déclenché si ∑grave ≥ 1 par arr |
| **λ (Lambda)** | Paramètre Poisson, "taux moyen incidents" |
| **Montecarlo** | Génération aléatoire jour-à-jour (pas déterministe) |
| **Variables Cachées** | Fatigue pompiers, congestion routes (affectent probabilités) |
| **Golden Hour** | >60min intervention = +30% morts (simplifié MVP: 30-90min aléatoire) |
| **StateCalculator** | Calcul 6 features hebdo (input ML) |
| **LabelCalculator** | Calcul 3 classes mensuel (output ML) |
| **Catastrophe** | score ≥ seuil_arr (classe ML) |

---

**Créé:** 25 Janvier 2026  
**Pour:** Session 4.2 & 4.3  
**Base:** Sessions 1-3 + Échange 4.1 + Schémas PDF
