# Système de Matrices de Corrélation et Variables d'État Dynamiques

**Document à l'attention de l'Orchestrator**  
**Story:** 1.4.4 - Matrices de corrélation et patterns dynamiques  
**Date:** 28 Janvier 2026

---

## 📋 Vue d'ensemble

Ce document explique en détail comment le système combine :
1. **Matrices fixes** (règles de transition) qui modulent les probabilités
2. **Variables d'état dynamiques** (trafic, incidents nuit, incidents alcool) qui évoluent jour après jour

Ces deux systèmes s'influencent mutuellement pour créer une simulation réaliste, imprévisible et capable de s'emballer.

---

## 🎯 Architecture : Deux Systèmes Parallèles

### Système 1 : Matrices Fixes (Règles de Transition)

**Rôle :** Moduler les probabilités d'incidents J→J+1

- Matrices intra-type (transitions gravité)
- Matrices inter-type (influence croisée)
- Matrices voisin (contagion spatiale)
- Matrices saisonnalité (effet temporel)

### Système 2 : Variables d'État Dynamiques (Évolution Journalière)

**Rôle :** Variables qui évoluent jour après jour et influencent les probabilités

- **Trafic** : Niveau de congestion (évolue selon incidents, mémoire, aléatoire)
- **Incidents nuit** : Nombre d'incidents par type se produisant la nuit (évolue selon corrélations)
- **Incidents alcool** : Nombre d'incidents par type causés par l'alcool (évolue selon corrélations)

Ces variables utilisent **leurs propres matrices de corrélation** (intra et inter) pour évoluer de manière réaliste.

---

## 🏗️ Architecture Globale Complète

### Flux de Calcul J→J+1 (Vue Complète)

```
┌─────────────────────────────────────────────────────────────┐
│                    JOUR J (État Actuel)                      │
│                                                               │
│  VECTEURS INCIDENTS (3 types × 3 gravités)                  │
│  - Agressions: [grave, moyen, bénin]                        │
│  - Incendies: [grave, moyen, bénin]                         │
│  - Accidents: [grave, moyen, bénin]                         │
│                                                               │
│  VARIABLES D'ÉTAT DYNAMIQUES                                │
│  - Trafic: niveau_congestion (0-1)                          │
│  - Incidents nuit: {agressions: X, incendies: Y, ...}       │
│  - Incidents alcool: {agressions: X, incendies: Y, ...}    │
│                                                               │
│  CONTEXTE                                                    │
│  - Patterns actifs                                           │
│  - Historique 7j et 60j                                      │
│  - Saison actuelle                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         ÉVOLUTION VARIABLES D'ÉTAT (Parallèle)                │
│                                                               │
│  1. Évolution Trafic J→J+1                                   │
│     - Utilise matrice_trafic (probabilités transition)      │
│     - Influencé par incidents J (accidents → engorgement)    │
│     - Aléatoire (engorgement/désengorgement)                 │
│     - Mémoire (facteur persistance)                          │
│                                                               │
│  2. Évolution Incidents Nuit J→J+1                           │
│     - Utilise corrélations intra/inter-type                  │
│     - Influencé par incidents J (plus incidents → plus nuit) │
│     - Aléatoire (probabilités nuit)                          │
│     - Saisonnalité (été = plus de nuit)                      │
│                                                               │
│  3. Évolution Incidents Alcool J→J+1                         │
│     - Utilise corrélations intra/inter-type                  │
│     - Influencé par incidents J (agressions → plus alcool)   │
│     - Aléatoire (probabilités alcool)                         │
│     - Saisonnalité (été = plus d'alcool)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         CALCUL PROBABILITÉS INCIDENTS J+1                     │
│                                                               │
│  1. Probabilité_base (vecteurs statiques)                    │
│     ↓                                                         │
│  2. × Matrice_intra_type (transition gravité)                │
│     ↓                                                         │
│  3. × Matrice_inter_type (influence croisée)                  │
│     ↓                                                         │
│  4. × Matrice_voisin (effet spatial)                          │
│     ↓                                                         │
│  5. × Trafic_J (variable d'état) → impact sur probabilités   │
│     ↓                                                         │
│  6. × Saisonnalité (effet temporel)                           │
│     ↓                                                         │
│  7. × Patterns_dynamiques (emballement)                       │
│     ↓                                                         │
│  8. + Aléatoire (Poisson)                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    JOUR J+1 (Nouvel État)                     │
│                                                               │
│  NOUVEAUX VECTEURS INCIDENTS                                 │
│  - Générés selon probabilités modulées                        │
│                                                               │
│  VARIABLES D'ÉTAT MISES À JOUR                               │
│  - Trafic_J1 (évolué)                                        │
│  - Incidents_nuit_J1 (évolués)                              │
│  - Incidents_alcool_J1 (évolués)                            │
│                                                               │
│  CARACTÉRISTIQUES INCIDENTS                                  │
│  - Pour chaque incident généré :                            │
│    * Déterminer si nuit (selon prob_nuit)                    │
│    * Déterminer si alcool (selon prob_alcool)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Les Matrices Fixes (Règles de Transition)

### 1. Matrices de Corrélation Intra-Type (3×3)

**Rôle :** Modélise les transitions entre gravités pour un type d'incident donné.

**Structure :**
```python
matrice_intra_type[microzone_id][type_incident] = [
    [P(bénin→bénin), P(bénin→moyen), P(bénin→grave)],  # Ligne 0 : état bénin J
    [P(moyen→bénin), P(moyen→moyen), P(moyen→grave)],  # Ligne 1 : état moyen J
    [P(grave→bénin), P(grave→moyen), P(grave→grave)]   # Ligne 2 : état grave J
]
```

**Valeurs de base (exemple agressions) :**
- Bénin → Bénin : 85% (stabilité)
- Bénin → Moyen : 12% (dégradation)
- Bénin → Grave : 3% (dégradation rare)
- Moyen → Grave : 15% (escalade)
- Grave → Grave : 75% (persistance)

**Application :**
```python
# Si J a eu 1 agression grave
prob_grave_J1 = prob_base × matrice_intra_type[2][2]  # 0.75 (persistance)
prob_moyen_J1 = prob_base × matrice_intra_type[2][1]  # 0.20 (amélioration)
prob_benin_J1 = prob_base × matrice_intra_type[2][0]  # 0.05 (amélioration rare)
```

**Effet :** Crée une **mémoire de gravité** - les incidents graves tendent à persister.

---

### 2. Matrices de Corrélation Inter-Type

**Rôle :** Modélise l'influence d'un type d'incident sur un autre (processus de Hawkes).

**Structure :**
```python
matrice_inter_type[microzone_id][type_cible][type_source] = [
    influence_bénin,   # Influence sur incidents bénins
    influence_moyen,   # Influence sur incidents moyens
    influence_grave    # Influence sur incidents graves
]
```

**Corrélations logiques implémentées :**

| Source → Cible | Influence | Logique |
|----------------|-----------|---------|
| Incendie → Accidents | [0.12, 0.08, 0.05] | Fumée réduisant visibilité, routes bloquées |
| Agressions → Accidents | [0.10, 0.06, 0.03] | Panique, fuite, conduite dangereuse |
| Accidents → Incendies | [0.08, 0.05, 0.02] | Explosions, court-circuits, fuites |
| Accidents → Agressions | [0.06, 0.04, 0.02] | Tensions post-accident, disputes |
| Incendie → Agressions | [0.05, 0.03, 0.01] | Stress, évacuation, tensions |
| Agressions → Incendies | [0.04, 0.02, 0.01] | Actes volontaires (incendies criminels) |

**Application :**
```python
# Si J a eu 1 incendie grave
prob_accidents_J1 += prob_base × matrice_inter_type['accidents']['incendies'][2]  # +0.05
prob_agressions_J1 += prob_base × matrice_inter_type['agressions']['incendies'][2]  # +0.01
```

**Effet :** Crée des **cascades d'incidents** - un type d'incident peut déclencher d'autres types.

---

### 3. Matrices Voisin (8 microzones)

**Rôle :** Modélise l'effet de contagion spatiale (near-repeat patterns).

**Structure :**
```python
matrice_voisin[microzone_id] = {
    'voisins': ['MZ002', 'MZ003', ...],  # 8 microzones les plus proches
    'poids_influence': [0.15, 0.12, ...],  # Poids par voisin (inverse distance)
    'seuil_activation': 5  # Seuil pour effet d'augmentation
}
```

**Règles d'activation :**
1. **Effet d'augmentation +0.1** si délinquance voisin > délinquance microzone
2. **Effet d'augmentation +0.1** si total incidents dans 8 voisins > 5

**Application :**
```python
# Calculer influence des voisins
total_incidents_voisins = sum(compter_incidents(voisin) for voisin in voisins)

# Effet d'augmentation
if total_incidents_voisins > 5:
    prob_finale *= 1.1  # +10%

if delinquance_voisin_max > delinquance_microzone:
    prob_finale *= 1.1  # +10% (max +20% total)
```

**Effet :** Crée une **contagion spatiale** - les zones à risque affectent leurs voisines.

---

### 4. Matrices Saisonnalité

**Rôle :** Modélise les variations saisonnières des probabilités d'incidents.

**Structure :**
```python
matrices_saisonnalite[microzone_id][type_incident][saison] = facteur_modulation
```

**Facteurs par type et saison :**

| Type | Hiver | Inter-saison | Été |
|------|-------|--------------|-----|
| Agressions | 0.85 (-15%) | 1.0 (référence) | 1.25 (+25%) |
| Incendies | 1.3 (+30%) | 1.0 (référence) | 0.9 (-10%) |
| Accidents | 1.1 (+10%) | 1.0 (référence) | 0.95 (-5%) |

**Application :**
```python
prob_finale *= matrices_saisonnalite[microzone_id][type_incident][saison_actuelle]
```

**Effet :** Crée des **patterns saisonniers reconnaissables**.

---

## 🔄 Variables d'État Dynamiques (Évolution Journalière)

Ces variables évoluent jour après jour selon leurs propres règles de corrélation, tout en influençant les probabilités d'incidents.

### 1. Trafic (Niveau de Congestion)

**Nature :** Variable continue évoluant jour après jour (0.0 = fluide, 1.0 = très engorgé)

**Évolution J→J+1 :**

```python
def evoluer_trafic_J1(microzone_id, trafic_J, incidents_J, jour, saison):
    """
    Évolue le niveau de trafic J→J+1 selon :
    - Trafic J (mémoire)
    - Incidents J (accidents → engorgement)
    - Matrices de transition trafic
    - Aléatoire
    """
    trafic_data = matrices_trafic[microzone_id]
    
    # 1. MÉMOIRE (persistance)
    trafic_base = trafic_J × trafic_data['facteur_memoire']  # 60% de persistance
    
    # 2. INFLUENCE INCIDENTS (accidents → engorgement)
    accidents_J = compter_incidents_J('accidents')
    influence_accidents = accidents_J × 0.05  # Chaque accident +5% trafic
    
    # 3. ENGORGEMENT/DÉSENGORGEMENT (aléatoire)
    if trafic_J > 0.7:  # Trafic élevé
        if random() < trafic_data['prob_engorgement']:  # 35%
            trafic_J1 = trafic_base + trafic_data['amplitude_engorgement'] + influence_accidents
        else:
            trafic_J1 = trafic_base + influence_accidents
    elif trafic_J < 0.3:  # Trafic faible
        if random() < trafic_data['prob_desengorgement']:  # 40%
            trafic_J1 = trafic_base + trafic_data['amplitude_desengorgement']
        else:
            trafic_J1 = trafic_base
    else:  # Trafic moyen
        trafic_J1 = trafic_base + influence_accidents
    
    # 4. CLAMP [0, 1]
    trafic_J1 = min(max(trafic_J1, 0.0), 1.0)
    
    return trafic_J1
```

**Influence sur probabilités d'incidents :**
```python
# Trafic élevé → plus d'accidents (routes bloquées, stress)
if trafic_J > 0.7:
    prob_accidents *= 1.15  # +15%
    prob_agressions *= 1.05  # +5% (stress)
```

**Corrélations :**
- **Intra-type trafic** : Trafic élevé J → tendance à rester élevé J+1 (mémoire)
- **Inter-type trafic** : Accidents → engorgement trafic → plus d'accidents (boucle)

---

### 2. Incidents Nuit (Par Type)

**Nature :** Nombre d'incidents par type se produisant la nuit (22h-5h), évoluant jour après jour.

**Évolution J→J+1 :**

```python
def evoluer_incidents_nuit_J1(microzone_id, type_incident, incidents_nuit_J, incidents_J, saison):
    """
    Évolue le nombre d'incidents nuit J→J+1 selon :
    - Incidents nuit J (mémoire)
    - Incidents J (plus incidents → plus nuit)
    - Corrélations inter-type (agressions → accidents nuit)
    - Saisonnalité (été = plus de nuit)
    - Aléatoire
    """
    prob_nuit_data = matrices_alcool_nuit[microzone_id][type_incident]
    
    # 1. BASE : Proportion d'incidents J qui sont la nuit
    total_incidents_J = sum(incidents_J[type_incident])  # [grave, moyen, bénin]
    
    if total_incidents_J > 0:
        # Calculer proportion nuit actuelle
        proportion_nuit_J = incidents_nuit_J / total_incidents_J
    else:
        proportion_nuit_J = prob_nuit_data['prob_nuit']  # Probabilité de base
    
    # 2. MÉMOIRE (persistance de la proportion)
    proportion_nuit_base = proportion_nuit_J × 0.7  # 70% de persistance
    
    # 3. INFLUENCE INTER-TYPE (agressions → accidents nuit)
    influence_inter = 0.0
    for autre_type in ['agressions', 'incendies', 'accidents']:
        if autre_type != type_incident:
            incidents_autre_type = sum(incidents_J[autre_type])
            # Corrélation : agressions → plus d'accidents la nuit
            if autre_type == 'agressions' and type_incident == 'accidents':
                influence_inter += incidents_autre_type × 0.08
            elif autre_type == 'accidents' and type_incident == 'agressions':
                influence_inter += incidents_autre_type × 0.05
    
    # 4. SAISONNALITÉ (été = plus de nuit)
    facteur_saison = 1.0
    if saison == 'ete':
        facteur_saison = 1.2  # +20% en été
    elif saison == 'hiver':
        facteur_saison = 0.9  # -10% en hiver
    
    # 5. ALCÉATOIRE (variabilité)
    variation_aleatoire = random.uniform(-0.1, 0.1)
    
    # 6. CALCUL FINAL
    proportion_nuit_J1 = (proportion_nuit_base + influence_inter) × facteur_saison + variation_aleatoire
    proportion_nuit_J1 = min(max(proportion_nuit_J1, 0.0), 0.6)  # Max 60%
    
    # 7. APPLIQUER AUX INCIDENTS GÉNÉRÉS J+1
    total_incidents_J1 = nombre_incidents_generes_J1[type_incident]
    incidents_nuit_J1 = int(total_incidents_J1 × proportion_nuit_J1)
    
    return incidents_nuit_J1
```

**Influence sur probabilités d'incidents :**
```python
# Plus d'incidents nuit J → plus d'incidents nuit J+1 (effet boule de neige)
if incidents_nuit_J > seuil:
    prob_incidents_J1 *= 1.1  # +10% (tendance à se reproduire la nuit)
```

**Corrélations :**
- **Intra-type nuit** : Beaucoup d'incidents nuit J → tendance à rester élevé J+1
- **Inter-type nuit** : Agressions nuit → accidents nuit (sorties, bars)

---

### 3. Incidents Alcool (Par Type)

**Nature :** Nombre d'incidents par type causés par l'alcool, évoluant jour après jour.

**Évolution J→J+1 :**

```python
def evoluer_incidents_alcool_J1(microzone_id, type_incident, incidents_alcool_J, incidents_J, saison):
    """
    Évolue le nombre d'incidents alcool J→J+1 selon :
    - Incidents alcool J (mémoire)
    - Incidents J (plus incidents → plus alcool possible)
    - Corrélations inter-type (agressions → accidents alcool)
    - Saisonnalité (été = plus d'alcool, 20% → 30% pour accidents)
    - Aléatoire
    """
    prob_alcool_data = matrices_alcool_nuit[microzone_id][type_incident]
    
    # 1. BASE : Proportion d'incidents J qui sont avec alcool
    total_incidents_J = sum(incidents_J[type_incident])
    
    if total_incidents_J > 0:
        proportion_alcool_J = incidents_alcool_J / total_incidents_J
    else:
        proportion_alcool_J = prob_alcool_data['prob_alcool']  # Probabilité de base
    
    # 2. MÉMOIRE (persistance)
    proportion_alcool_base = proportion_alcool_J × 0.65  # 65% de persistance
    
    # 3. INFLUENCE INTER-TYPE (agressions → accidents alcool)
    influence_inter = 0.0
    for autre_type in ['agressions', 'incendies', 'accidents']:
        if autre_type != type_incident:
            incidents_autre_type = sum(incidents_J[autre_type])
            # Corrélation : agressions → plus d'accidents avec alcool
            if autre_type == 'agressions' and type_incident == 'accidents':
                influence_inter += incidents_autre_type × 0.06
            elif autre_type == 'accidents' and type_incident == 'agressions':
                influence_inter += incidents_autre_type × 0.04
    
    # 4. SAISONNALITÉ (été = plus d'alcool)
    facteur_saison = 1.0
    if saison == 'ete':
        facteur_saison = prob_alcool_data['facteur_ete_alcool']  # 1.5 pour accidents (20% → 30%)
    elif saison == 'hiver':
        facteur_saison = 0.9  # -10% en hiver
    
    # 5. ALCÉATOIRE (variabilité)
    variation_aleatoire = random.uniform(-0.05, 0.05)
    
    # 6. CALCUL FINAL
    proportion_alcool_J1 = (proportion_alcool_base + influence_inter) × facteur_saison + variation_aleatoire
    proportion_alcool_J1 = min(max(proportion_alcool_J1, 0.0), 0.5)  # Max 50%
    
    # 7. APPLIQUER AUX INCIDENTS GÉNÉRÉS J+1
    total_incidents_J1 = nombre_incidents_generes_J1[type_incident]
    incidents_alcool_J1 = int(total_incidents_J1 × proportion_alcool_J1)
    
    return incidents_alcool_J1
```

**Influence sur probabilités d'incidents :**
```python
# Plus d'incidents alcool J → plus d'incidents alcool J+1 (effet boule de neige)
if incidents_alcool_J > seuil:
    prob_incidents_J1 *= 1.08  # +8% (tendance à se reproduire avec alcool)
```

**Corrélations :**
- **Intra-type alcool** : Beaucoup d'incidents alcool J → tendance à rester élevé J+1
- **Inter-type alcool** : Agressions alcool → accidents alcool (conduite en état d'ivresse)

---

## 🔗 Interactions Entre Systèmes

### Comment les Variables d'État Influencent les Probabilités

```python
# 1. TRAFIC → PROBABILITÉS INCIDENTS
if trafic_J > 0.7:  # Trafic élevé
    prob_accidents *= 1.15  # +15% (routes bloquées, stress)
    prob_agressions *= 1.05  # +5% (stress, tensions)

# 2. INCIDENTS NUIT → PROBABILITÉS INCIDENTS
if incidents_nuit_J[type_incident] > seuil:
    prob_incidents_J1 *= 1.1  # +10% (tendance à se reproduire la nuit)

# 3. INCIDENTS ALCOOL → PROBABILITÉS INCIDENTS
if incidents_alcool_J[type_incident] > seuil:
    prob_incidents_J1 *= 1.08  # +8% (tendance à se reproduire avec alcool)
```

### Comment les Incidents Influencent les Variables d'État

```python
# 1. INCIDENTS → TRAFIC
accidents_J = compter_incidents_J('accidents')
trafic_J1 += accidents_J × 0.05  # Chaque accident +5% trafic

# 2. INCIDENTS → INCIDENTS NUIT
# Plus d'incidents J → plus de chances qu'ils soient la nuit
proportion_nuit_J1 = f(incidents_J, incidents_nuit_J, corrélations)

# 3. INCIDENTS → INCIDENTS ALCOOL
# Plus d'incidents J → plus de chances qu'ils soient avec alcool
proportion_alcool_J1 = f(incidents_J, incidents_alcool_J, corrélations, saison)
```

---

## 📐 Formule Mathématique Complète

### Étape 1 : Évolution des Variables d'État J→J+1

```python
def evoluer_variables_etat_J1(microzone_id, etat_J, jour, saison):
    """
    Évolue toutes les variables d'état en parallèle.
    """
    # 1. ÉVOLUTION TRAFIC
    trafic_J1 = evoluer_trafic_J1(
        microzone_id, 
        etat_J['trafic'], 
        etat_J['incidents'], 
        jour, 
        saison
    )
    
    # 2. ÉVOLUTION INCIDENTS NUIT
    incidents_nuit_J1 = {}
    for type_incident in ['agressions', 'incendies', 'accidents']:
        incidents_nuit_J1[type_incident] = evoluer_incidents_nuit_J1(
            microzone_id,
            type_incident,
            etat_J['incidents_nuit'][type_incident],
            etat_J['incidents'],
            saison
        )
    
    # 3. ÉVOLUTION INCIDENTS ALCOOL
    incidents_alcool_J1 = {}
    for type_incident in ['agressions', 'incendies', 'accidents']:
        incidents_alcool_J1[type_incident] = evoluer_incidents_alcool_J1(
            microzone_id,
            type_incident,
            etat_J['incidents_alcool'][type_incident],
            etat_J['incidents'],
            saison
        )
    
    return {
        'trafic': trafic_J1,
        'incidents_nuit': incidents_nuit_J1,
        'incidents_alcool': incidents_alcool_J1
    }
```

### Étape 2 : Calcul Probabilités Incidents J+1

```python
def calculer_probabilite_incidents_J1(microzone_id, type_incident, etat_J, variables_etat_J1, jour, saison):
    """
    Calcule la probabilité d'incidents J+1 en appliquant toutes les matrices
    et en tenant compte des variables d'état.
    """
    
    # 1. PROBABILITÉ DE BASE
    prob_base = vecteurs_statiques[microzone_id][type_incident]
    
    # 2. MATRICE INTRA-TYPE (transition gravité)
    gravite_J = determiner_gravite_dominante(etat_J['incidents'][type_incident])
    prob_intra = prob_base
    for gravite_J1 in ['benin', 'moyen', 'grave']:
        transition = matrices_intra_type[microzone_id][type_incident][gravite_J][gravite_J1]
        prob_intra *= transition
    
    # 3. MATRICE INTER-TYPE (influence croisée)
    prob_inter = prob_intra
    for autre_type in ['agressions', 'incendies', 'accidents']:
        if autre_type != type_incident:
            incidents_autre_type = sum(etat_J['incidents'][autre_type])
            influence = matrices_inter_type[microzone_id][type_incident][autre_type]
            prob_inter += prob_base * influence * incidents_autre_type
    
    # 4. MATRICE VOISIN (effet spatial)
    prob_voisin = prob_inter
    voisins_data = matrices_voisin[microzone_id]
    total_incidents_voisins = sum(
        sum(etat_J['incidents'][type]) 
        for voisin in voisins_data['voisins']
        for type in ['agressions', 'incendies', 'accidents']
    )
    
    if total_incidents_voisins > voisins_data['seuil_activation']:
        prob_voisin *= 1.1  # +10%
    
    # 5. VARIABLE D'ÉTAT : TRAFIC (influence sur probabilités)
    prob_trafic = prob_voisin
    if variables_etat_J1['trafic'] > 0.7:  # Trafic élevé
        prob_trafic *= 1.15  # +15% accidents
        if type_incident == 'agressions':
            prob_trafic *= 1.05  # +5% agressions (stress)
    
    # 6. VARIABLE D'ÉTAT : INCIDENTS NUIT (influence sur probabilités)
    prob_nuit = prob_trafic
    if variables_etat_J1['incidents_nuit'][type_incident] > seuil_nuit:
        prob_nuit *= 1.1  # +10% (tendance à se reproduire la nuit)
    
    # 7. VARIABLE D'ÉTAT : INCIDENTS ALCOOL (influence sur probabilités)
    prob_alcool = prob_nuit
    if variables_etat_J1['incidents_alcool'][type_incident] > seuil_alcool:
        prob_alcool *= 1.08  # +8% (tendance à se reproduire avec alcool)
    
    # 8. SAISONNALITÉ
    prob_saison = prob_alcool
    facteur_saison = matrices_saisonnalite[microzone_id][type_incident][saison]
    prob_saison *= facteur_saison
    
    # 9. PATTERNS DYNAMIQUES (emballement)
    prob_pattern = prob_saison
    patterns_actifs = patterns_actifs_par_microzone[microzone_id]
    for pattern in patterns_actifs:
        if pattern['type'] == '7j' and pattern['type_incident'] == type_incident:
            jour_pattern = jour - pattern['jour_debut']
            if jour_pattern == 2:  # Pic au jour 3
                amplitude = pattern['amplitude_pic']
            else:
                amplitude = pattern['amplitude_base']
            prob_pattern *= (1 + amplitude)
    
    # 10. TIRAGE ALÉATOIRE FINAL (Poisson)
    lambda_final = prob_pattern
    nombre_incidents = np.random.poisson(lambda_final)
    
    # 11. RÉPARTITION GRAVITÉ (Multinomial)
    if nombre_incidents > 0:
        prob_gravites = [
            matrices_intra_type[microzone_id][type_incident][gravite_J][0],  # bénin
            matrices_intra_type[microzone_id][type_incident][gravite_J][1],  # moyen
            matrices_intra_type[microzone_id][type_incident][gravite_J][2]   # grave
        ]
        repartition = np.random.multinomial(nombre_incidents, prob_gravites)
        
        # 12. DÉTERMINER CARACTÉRISTIQUES (nuit, alcool)
        incidents_nuit = 0
        incidents_alcool = 0
        
        for i in range(nombre_incidents):
            # Déterminer si nuit
            heure = random.randint(0, 23)
            if heure in [22, 23, 0, 1, 2, 3, 4, 5]:
                prob_nuit_actuelle = matrices_alcool_nuit[microzone_id][type_incident]['prob_nuit']
                if random() < prob_nuit_actuelle:
                    incidents_nuit += 1
            
            # Déterminer si alcool
            prob_alcool_actuelle = matrices_alcool_nuit[microzone_id][type_incident]['prob_alcool']
            if saison == 'ete':
                prob_alcool_actuelle *= matrices_alcool_nuit[microzone_id][type_incident]['facteur_ete_alcool']
            if random() < prob_alcool_actuelle:
                incidents_alcool += 1
        
        return {
            'vecteur': {'benin': repartition[0], 'moyen': repartition[1], 'grave': repartition[2]},
            'nuit': incidents_nuit,
            'alcool': incidents_alcool
        }
    else:
        return {
            'vecteur': {'benin': 0, 'moyen': 0, 'grave': 0},
            'nuit': 0,
            'alcool': 0
        }
```

---

## 🔄 Exemple Complet : Évolution Parallèle

### Jour J (État Initial)

```
Microzone MZ009 (La Chapelle, arr 19)

VECTEURS INCIDENTS :
- Agressions: [grave: 1, moyen: 0, bénin: 0]
- Incendies: [grave: 0, moyen: 0, bénin: 0]
- Accidents: [grave: 0, moyen: 1, bénin: 0]

VARIABLES D'ÉTAT :
- Trafic: 0.45 (modéré)
- Incidents nuit: {agressions: 1, incendies: 0, accidents: 0}
- Incidents alcool: {agressions: 0, incendies: 0, accidents: 0}
```

### Étape 1 : Évolution Variables d'État J→J+1

```python
# TRAFIC
trafic_J = 0.45
accidents_J = 1
trafic_J1 = 0.45 × 0.60 (mémoire) + 1 × 0.05 (influence accidents) = 0.32
# Légère baisse (trafic modéré, peu d'accidents)

# INCIDENTS NUIT
incidents_nuit_J = {'agressions': 1, 'incendies': 0, 'accidents': 0}
total_agressions_J = 1
proportion_nuit_J = 1.0  # 100% des agressions étaient la nuit
proportion_nuit_J1 = 1.0 × 0.7 (mémoire) × 1.2 (été) = 0.84
# Reste élevé (mémoire forte)

# INCIDENTS ALCOOL
incidents_alcool_J = {'agressions': 0, 'incendies': 0, 'accidents': 0}
proportion_alcool_J = 0.15 (base agressions)
proportion_alcool_J1 = 0.15 × 0.65 (mémoire) × 1.2 (été) = 0.117
# Légère augmentation (été)
```

### Étape 2 : Calcul Probabilités Incidents J+1

```python
# AGRESSIONS
prob_base = 0.05
prob_intra = prob_base × 0.75 (grave→grave) = 0.0375
prob_inter = prob_intra + 0 (pas d'influence autres types) = 0.0375
prob_voisin = prob_inter × 1.1 (voisins affectés) = 0.04125
prob_trafic = prob_voisin × 1.0 (trafic modéré) = 0.04125
prob_nuit = prob_trafic × 1.1 (beaucoup nuit J) = 0.045375
prob_alcool = prob_nuit × 1.0 (peu d'alcool) = 0.045375
prob_saison = prob_alcool × 1.25 (été) = 0.0567
prob_pattern = prob_saison × 1.0 (pas de pattern) = 0.0567

# Tirage Poisson
nombre_agressions = np.random.poisson(0.0567)  # ≈ 0-1
```

### Jour J+1 (Nouvel État)

```
VECTEURS INCIDENTS :
- Agressions: [grave: 0, moyen: 0, bénin: 1]  # Tirage aléatoire
- Incendies: [grave: 0, moyen: 0, bénin: 0]
- Accidents: [grave: 0, moyen: 0, bénin: 0]

VARIABLES D'ÉTAT (ÉVOLUÉES) :
- Trafic: 0.32 (légère baisse)
- Incidents nuit: {agressions: 1, incendies: 0, accidents: 0}  # 1 agression bénin, 100% nuit
- Incidents alcool: {agressions: 0, incendies: 0, accidents: 0}  # Pas d'alcool
```

---

## 🎲 Caractéristiques du Système

### 1. Évolution Parallèle mais Influencée

**Variables d'état évoluent en parallèle :**
- Trafic évolue selon ses propres règles
- Incidents nuit évoluent selon leurs propres règles
- Incidents alcool évoluent selon leurs propres règles

**Mais elles s'influencent mutuellement :**
- Incidents → Trafic (accidents engorgent)
- Trafic → Incidents (trafic élevé → plus d'accidents)
- Incidents nuit → Probabilités (tendance à se reproduire)
- Incidents alcool → Probabilités (tendance à se reproduire)

### 2. Corrélations Scientifiques

**Basées sur la littérature :**
- **Near-repeat patterns** : Incidents tendent à se reproduire dans la même zone
- **Temporal clustering** : Incidents nuit tendent à se reproduire la nuit
- **Alcohol-related incidents** : Corrélations entre agressions et accidents avec alcool
- **Traffic congestion** : Accidents → engorgement → plus d'accidents (boucle)

### 3. Mémoire et Persistance

**Chaque variable a sa propre mémoire :**
- Trafic : 60% de persistance
- Incidents nuit : 70% de persistance
- Incidents alcool : 65% de persistance

**Résultat :** Les états persistent mais évoluent progressivement.

### 4. Potentiel d'Emballement

**Boucles de rétroaction :**
- Accidents → Trafic élevé → Plus d'accidents → Trafic encore plus élevé
- Agressions nuit → Plus d'agressions nuit → Pattern déclenché → Emballement
- Agressions alcool → Accidents alcool → Plus d'agressions alcool

**Limites naturelles :**
- Mémoires décroissantes (60-70%)
- Aléatoire à chaque étape
- Patterns se terminent après leur durée

---

## 📁 Fichiers de Données

### Matrices Fixes (Pré-calculées)

| Fichier | Contenu | Structure |
|---------|---------|-----------|
| `matrices_correlation_intra_type.pkl` | Matrices 3×3 par (microzone, type) | `Dict[mz_id][type] = np.array(3×3)` |
| `matrices_correlation_inter_type.pkl` | Influences croisées | `Dict[mz_id][type_cible][type_source] = [bénin, moyen, grave]` |
| `matrices_voisin.pkl` | 8 voisins par microzone | `Dict[mz_id] = {'voisins': [...], 'poids': [...], 'seuil': 5}` |
| `matrices_trafic.pkl` | **Règles de transition trafic** | `Dict[mz_id] = {'prob_engorgement': ..., 'facteur_memoire': ...}` |
| `matrices_alcool_nuit.pkl` | **Probabilités de base alcool/nuit** | `Dict[mz_id][type] = {'prob_alcool': ..., 'prob_nuit': ...}` |
| `matrices_saisonnalite.pkl` | Facteurs saisonniers | `Dict[mz_id][type][saison] = facteur` |

### Variables d'État (Runtime - Évoluent chaque jour)

**Stockées dans l'état de simulation :**
```python
etat_simulation[jour][microzone_id] = {
    'vecteurs_incidents': {
        'agressions': [grave, moyen, bénin],
        'incendies': [grave, moyen, bénin],
        'accidents': [grave, moyen, bénin]
    },
    'variables_etat': {
        'trafic': float,  # 0.0 - 1.0
        'incidents_nuit': {
            'agressions': int,
            'incendies': int,
            'accidents': int
        },
        'incidents_alcool': {
            'agressions': int,
            'incendies': int,
            'accidents': int
        }
    }
}
```

---

## 🔧 Utilisation par l'Orchestrator

### Algorithme Complet J→J+1

```python
def generer_jour_J1(microzone_id, etat_J, jour, saison):
    """
    Génère l'état complet J+1 pour une microzone.
    """
    # ÉTAPE 1 : Évoluer variables d'état (en parallèle)
    variables_etat_J1 = evoluer_variables_etat_J1(
        microzone_id, etat_J, jour, saison
    )
    
    # ÉTAPE 2 : Calculer probabilités incidents J+1
    nouveaux_vecteurs = {}
    nouveaux_incidents_nuit = {}
    nouveaux_incidents_alcool = {}
    
    for type_incident in ['agressions', 'incendies', 'accidents']:
        resultat = calculer_probabilite_incidents_J1(
            microzone_id,
            type_incident,
            etat_J,
            variables_etat_J1,
            jour,
            saison
        )
        
        nouveaux_vecteurs[type_incident] = resultat['vecteur']
        nouveaux_incidents_nuit[type_incident] = resultat['nuit']
        nouveaux_incidents_alcool[type_incident] = resultat['alcool']
    
    # ÉTAPE 3 : Construire nouvel état
    etat_J1 = {
        'vecteurs_incidents': nouveaux_vecteurs,
        'variables_etat': {
            'trafic': variables_etat_J1['trafic'],
            'incidents_nuit': nouveaux_incidents_nuit,
            'incidents_alcool': nouveaux_incidents_alcool
        }
    }
    
    return etat_J1
```

---

## 🎯 Points Clés pour l'Orchestrator

1. **Deux systèmes parallèles** :
   - Matrices fixes (règles de transition) → modulent probabilités
   - Variables d'état (évoluent jour après jour) → influencent probabilités

2. **Évolution des variables d'état** :
   - Utilisent leurs propres corrélations (intra et inter)
   - Sont influencées par les incidents
   - Influencent à leur tour les probabilités d'incidents
   - Utilisent de l'aléatoire pour la variabilité

3. **Ordre d'exécution** :
   - D'abord : Évoluer variables d'état J→J+1
   - Ensuite : Calculer probabilités incidents J+1 (en utilisant variables d'état J1)
   - Enfin : Générer incidents J+1 et déterminer leurs caractéristiques (nuit, alcool)

4. **Boucles de rétroaction** :
   - Incidents → Variables d'état → Probabilités → Incidents
   - Crée des dynamiques réalistes et potentiellement emballantes

5. **Mémoire du système** :
   - Chaque variable a sa propre mémoire (60-70% de persistance)
   - Les états persistent mais évoluent progressivement

---

## 📚 Références Scientifiques

Les corrélations implémentées sont basées sur :

- **Near-repeat patterns** : Littérature criminologique montrant que les incidents tendent à se reproduire dans les mêmes zones et aux mêmes heures
- **Temporal clustering** : Les incidents nocturnes créent des clusters temporels
- **Alcohol-related incidents** : Corrélations observées entre agressions et accidents avec alcool (conduite en état d'ivresse, violences)
- **Traffic congestion feedback** : Accidents → engorgement → stress → plus d'accidents (boucle de rétroaction)

---

**Document créé le :** 28 Janvier 2026  
**Dernière mise à jour :** 28 Janvier 2026  
**Version :** 2.0 (Révision : Variables d'état dynamiques)
