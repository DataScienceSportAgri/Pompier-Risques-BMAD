# 📋 SESSION 4.3 - OUTPUTS & VISUALISATIONS
## Échange 4.3 - Interface Streamlit : Outputs, Heatmap, Évolutions

**Date:** 25 Janvier 2026  
**Statut:** ✅ En cours (partiellement complété)  
**Contexte:** Suite Session 4.2 (Validations, Progression, Sauvegardes)

---

# 🎯 OBJECTIF

Définir les outputs complets, les détails de la heatmap (interactivité, filtres), le format CSV Phase 2, et la roadmap des évolutions UI Phase 2/3.

---

# ✅ DÉCISIONS PRISES (Partie 1)

## 7. Outputs & Visualisations Complètes

### Layout Interface Streamlit

```
┌─────────────────────────────────────────────────────────────┐
│  BANDEAU HAUT: Sélections (jours, scénario, variabilité)   │
├──────────┬──────────────────────────────┬───────────────────┤
│          │                              │                   │
│  LISTE   │     CARTE PARIS              │  LISTE           │
│  ÉVÉNTS  │     (Centre)                 │  ARRONDISSEMENTS │
│  &       │     - Événements             │  (Droite)         │
│  INCIDENTS│    - Couleurs changeantes   │  - Petits        │
│  (Gauche)│                              │    rectangles    │
│          │                              │  - Évolution     │
│  Cliquable│                             │    temporelle    │
│  → Détails│                             │                   │
│          │                              │  Cliquable       │
│          │                              │  → Graphiques    │
│          │                              │    détaillés     │
├──────────┴──────────────────────────────┴───────────────────┤
│  BANDEAU BAS: [Lancer] | Jours X/Total | [Stop]             │
└─────────────────────────────────────────────────────────────┘
```

### Statistiques Affichées

**Colonne Gauche - Liste Événements & Incidents:**
- ✅ Liste complète événements majeurs et incidents graves
- ✅ **Cliquable** → Accès aux features de l'événement/incident
- ✅ Affichage des caractéristiques (ce qu'ils ont produit)
- ✅ Codes couleur par type:
  - 🟠 **Orange** → Incendies graves
  - ⚫ **Gris** → Agressions
  - 🟤 **Marron** → Accidents

**Colonne Droite - Liste Arrondissements:**
- ✅ **Petits rectangles** (un par arrondissement)
- ✅ **Évolution temporelle** du nombre d'incidents par type:
  - Incendies
  - Accidents
  - Agressions
- ✅ **Cliquable** → Fenêtre avec graphiques détaillés:
  - Incidents graves
  - Accidents graves
  - Évolution temporelle jour-à-jour
- ✅ **Indicateur catastrophe**:
  - Changement visuel rectangle si seuil catastrophe dépassé
  - Indicateur pré-catastrophe ou catastrophe
  - **Calculé même en mode régression** (pour comparaison)
- ✅ **Fenêtre détaillée**:
  - Permanemment connectée à la simulation
  - Mise à jour en temps réel
  - Graphiques temporels jour-à-jour

**Bandeau Bas:**
- ✅ **Bouton Lancer** (gauche)
- ✅ **Nombre jours / Total** (milieu) - Ex: "Jour 45 / 90"
- ✅ **Bouton Stop** (droite)

---

# 🧠 QUESTIONS REFORMULÉES - MODÈLE PRÉDICTION INCIDENTS

## 📄 RÉFÉRENCE : Modèle Scientifique Complet

**Source:** `.bmad-core/utils/Modèle Prédiction Incidents J+1.pdf`

**Modèle:** Zero-Inflated Poisson avec Régimes Cachés
- **Régimes:** Stable (85% zero), Détérioration (75% zero), Crise (60% zero)
- **Variables cachées:** Long-terme (60 jours), Court-terme (7 jours)
- **Distribution:** Multinomiale conditionnelle sur 9 combinaisons type × gravité
- **Transitions:** Matrices de transition entre régimes modifiées par patterns
- **Littérature:** Zero-Inflated Poisson, Hidden Markov Models, Processus de Hawkes, etc.

**Différence avec Sessions 1-3:** Le modèle scientifique est plus sophistiqué que la version simplifiée discutée (Poisson simple + Multinomial). Il intègre régimes cachés, stress accumulé, et patterns de déclenchement.

---

## 8. Modèle Monte-Carlo & Patterns Paris (Base Nucléaire)

### Contexte
Le modèle de prédiction d'incidents est la **base nucléaire** de la formulation Monte-Carlo pour créer des données d'incidents basées sur la littérature scientifique. Il faut trouver les patterns à Paris sur les 100 microzones pour moduler le lancement des simulations et **intégrer le modèle scientifique complet** (Zero-Inflated Poisson + Régimes Cachés).

### Questions Brainstorming

#### 8.1 Intégration Modèle Scientifique vs Modèle Simplifié MVP

**✅ DÉCISION PRISE : Option B - MVP Modèle Scientifique**

- **Zero-Inflated Poisson + Régimes Cachés** dès le MVP
- Variables cachées (stress 60j, patterns 7j)
- Matrices de transition
- Génération des 3 vecteurs de 3 valeurs par zone dès MVP
- Plus complexe mais plus crédible scientifiquement

**Conséquence:** Temps dev peut augmenter, mais modèle scientifiquement solide dès le départ.

---

#### 8.1.1 Vecteurs Statiques (Nouvelle Proposition)

**Concept:** Vecteurs statiques de même forme que vecteurs mobiles
- **Structure:** 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave) par microzone
- **Rôle:** Influencer la génération des vecteurs mobiles

**Deux points d'influence possibles:**
1. **Probabilités de générer des régimes de crises** (initialisation/modulation régimes)
2. **Obtention pure et dure des incidents** (modulation intensités λ_base)
3. **Les deux** (recommandé par utilisateur)

**Questions de clarification:**
- **Valeurs des vecteurs statiques:** Comment les calculer depuis patterns Paris (prix m², chômage, etc.) ?
- **Normalisation:** Les vecteurs statiques sont-ils des probabilités, des multiplicateurs, ou des intensités de base ?
- **Intégration dans formule:** Où exactement dans l'algorithme scientifique (Étape 1-7) ?
  - Étape 1: Initialisation régimes → vecteurs statiques déterminent probabilités régimes initiaux ?
  - Étape 6: Calcul intensités → vecteurs statiques modulent λ_base ?
  - Les deux ?

#### 8.2 Patterns Socio-Économiques Paris & Initialisation Régimes

**✅ APPROCHE: Vecteurs Statiques comme Interface Patterns → Modèle**

- **Vecteurs statiques** = représentation patterns Paris sous forme exploitable par modèle scientifique
- **Mapping facteurs socio-économiques → vecteurs statiques:**
  - Prix du logement → influence sur vecteurs statiques
  - Taux de chômage → influence sur vecteurs statiques ?
  - Densité de population → influence sur vecteurs statiques ?
  - Revenus médians → influence sur vecteurs statiques ?
  - Autres facteurs (précisez)

**✅ RÈGLE PRIX M² (Décision prise):**

1. **Prix m² → Probabilité création agression:**
   - **Division** de la probabilité de départ de création d'une agression
   - Formule: `prob_agression_modulée = prob_agression_base / facteur_prix_m2`
   - Prix m² élevé → facteur > 1 → probabilité agression diminuée
   - Prix m² faible → facteur < 1 → probabilité agression augmentée

2. **Prix m² → Probabilités régimes (Tension/Crise):**
   - **Diminution** de la probabilité de création d'une situation de tension ou de crise
   - Prix m² élevé → probabilités régimes Détérioration/Crise réduites
   - Prix m² faible → probabilités régimes Détérioration/Crise augmentées

**Questions de clarification:**
- **Formule exacte division agression:**
  - `facteur_prix_m2 = f(prix_m2)` → quelle fonction ? (linéaire, logarithmique, seuils catégoriels ?)
  - Exemple: `facteur = prix_m2 / prix_m2_moyen` ou `facteur = 1 + (prix_m2 - prix_m2_moyen) / prix_m2_moyen` ?
  - Normalisation: plage de valeurs prix m² Paris → facteur dans quelle plage ?

- **Formule diminution probabilités régimes:**
  - Comment modifie-t-on les probabilités régimes initiaux ?
  - Exemple: `P(Crise) = P(Crise)_base × (1 - α × facteur_prix_m2)` ?
  - Ou modification matrice de transition Q_base ?

- **Intégration dans vecteurs statiques:**
  - Les vecteurs statiques reflètent-ils cette influence prix m² ?
  - Ou prix m² appliqué directement dans algorithme (séparément des vecteurs statiques) ?
  
- **Autres facteurs:**
  - Taux de chômage → influence similaire ou différente ?
  - Densité population → impact ?
  - Revenus médians → corrélation avec prix m² ou effet indépendant ?

#### 8.3 Calibration Intensités λ_base selon Patterns Paris

**Dans le modèle scientifique, les intensités λ_base sont calibrées par régime:**

| Régime | Type \ Gravité | Bénin | Moyen | Grave |
|--------|----------------|-------|-------|-------|
| Stable | Accident | 0.0410 | 0.0087 | 0.0011 |
| Stable | Incendie | 0.0246 | 0.0059 | 0.0012 |
| Stable | Agression | 0.0344 | 0.0074 | 0.0021 |

**✅ APPROCHE: Vecteurs Statiques modulent λ_base**

- **Vecteurs statiques** influencent les intensités λ_base avant normalisation
- **Formule possible:** `λ_base_modulé(τ,g) = λ_base(τ,g) × vecteur_statique(τ,g) × facteurs_autres`

---

#### 8.3.1 Intégration Trois Matrices dans Calcul J+1

**✅ RÈGLE CRITIQUE: Trois types de matrices doivent influencer le calcul J+1**

1. **Matrice Gravité Microzone (même microzone, même type):**
   - Matrice bénin/moyen/grave de la microzone donnée pour J+1
   - Influence: Historique gravité du même type d'incident dans la microzone
   - Exemple: Si microzone a eu beaucoup d'agressions graves récemment → probabilité agression grave J+1 augmentée

2. **Matrice Types Croisés (même microzone, autres types):**
   - Matrice des autres types d'incidents de la même microzone
   - Exemple: Pour calculer accidents J+1 → utiliser matrice agressions + incendies de la microzone
   - Influence: Corrélations croisées (incendie → accidents, agressions → accidents, etc.)

3. **Matrice Voisins (8 zones alentours):**
   - Matrice des 8 microzones voisines (radius 1)
   - Influence: Propagation spatiale, effet de contagion
   - Pondération: grave ×1.0, moyen ×0.5, bénin ×0.2 (Session 3)
   - Modulée par variabilité locale (faible=0.3, moyen=0.5, important=0.7)

**Questions de clarification:**

- **Intégration dans modèle scientifique:**
  - Où dans l'algorithme (Étapes 1-7) ces matrices sont-elles appliquées ?
  - Étape 6 (Calcul intensités) : `λ_calibrated(τ,g) = λ_base(τ,g) × facteur_long × facteur_matrices` ?
  - Ou dans calcul stress long-terme (Étape 2) ?
  - Ou dans détection patterns court-terme (Étape 1) ?

- **Formule combinatoire:**
  - Comment combiner les 3 matrices ?
  - Exemple: `λ_final(τ,g) = λ_base(τ,g) × (1 + α×matrice_gravité + β×matrice_croisée + γ×matrice_voisins)` ?
  - Ou produit: `λ_final = λ_base × matrice_gravité × matrice_croisée × matrice_voisins` ?
  - Pondération relative des 3 matrices ?

- **Matrice Gravité Microzone:**
  - Historique sur combien de jours ? (J, J-1, J-2, ... J-N ?)
  - Décroissance temporelle (plus récent = plus d'influence) ?
  - Structure: Vecteur [grave, moyen, bénin] du jour J ou agrégation historique ?

- **Matrice Types Croisés:**
  - Pour accidents J+1 → utiliser agressions + incendies de la microzone
  - Pour incendies J+1 → utiliser accidents + agressions ?
  - Pour agressions J+1 → utiliser accidents + incendies ?
  - Historique sur combien de jours ?
  - Pondération par type (ex: incendie → accidents plus fort que agressions → accidents) ?

- **Matrice Voisins (8 zones):**
  - Comment agréger les 8 microzones voisines ?
  - Moyenne pondérée (grave×1.0, moyen×0.5, bénin×0.2) ?
  - Par type d'incident (agressions voisins → agressions microzone) ou tous types confondus ?
  - Historique sur combien de jours pour chaque voisin ?
  - Modulée par variabilité locale (0.3/0.5/0.7) → comment exactement ?

- **Normalisation:**
  - Après application des 3 matrices, faut-il renormaliser Z(t) ?
  - Comment garantir probabilités cibles (82% bénin, 16% moyen, 2% grave) ?

---

#### 8.3.2 Pistes d'Implémentation Réalistes

**📋 PROPOSITION 1 : Structure Données & Stockage**

```python
# Structure efficace pour 100 microzones × N jours
class MicrozoneData:
    def __init__(self, microzone_id):
        self.id = microzone_id
        # Vecteurs mobiles jour-à-jour (accès rapide J, J-1, ..., J-60)
        self.histoire_vecteurs = {
            'incendies': deque(maxlen=60),  # [grave, moyen, bénin] par jour
            'accidents': deque(maxlen=60),
            'agressions': deque(maxlen=60)
        }
        # Vecteurs statiques (calculés une fois au début)
        self.vecteurs_statiques = {
            'incendies': [0.0, 0.0, 0.0],  # [grave, moyen, bénin]
            'accidents': [0.0, 0.0, 0.0],
            'agressions': [0.0, 0.0, 0.0]
        }
        # Régime actuel
        self.regime_actuel = 'Stable'  # 'Stable', 'Détérioration', 'Crise'
        # Variables cachées
        self.stress_long_terme = 0.0
        self.pattern_court_terme = 0  # Nombre événements moyens sur 7j

# Structure globale
simulation_data = {
    microzone_id: MicrozoneData(microzone_id) 
    for microzone_id in range(1, 101)
}
```

**📋 PROPOSITION 2 : Calcul Matrice Gravité Microzone**

```python
def calcul_matrice_gravite(microzone_id, type_incident, jour_j, fenetre=7):
    """
    Matrice gravité: historique même type, même microzone
    Influence décroissante (plus récent = plus important)
    """
    hist = simulation_data[microzone_id].histoire_vecteurs[type_incident]
    
    if len(hist) < fenetre:
        fenetre = len(hist)
    
    # Agrégation pondérée (décroissance exponentielle)
    poids_total = 0.0
    vecteur_agrege = [0.0, 0.0, 0.0]  # [grave, moyen, bénin]
    
    for i in range(fenetre):
        jour_relatif = fenetre - i - 1  # 0 = plus récent
        poids = np.exp(-0.1 * jour_relatif)  # Décroissance exponentielle
        vecteur_jour = hist[-(i+1)]  # Plus récent en premier
        
        for g in range(3):  # grave, moyen, bénin
            vecteur_agrege[g] += poids * vecteur_jour[g]
        poids_total += poids
    
    # Normalisation
    if poids_total > 0:
        vecteur_agrege = [v / poids_total for v in vecteur_agrege]
    
    # Conversion en facteur multiplicateur (évite explosion)
    facteur_gravite = 1.0 + 0.2 * (vecteur_agrege[0] * 1.0 + vecteur_agrege[1] * 0.5)
    # Grave compte ×1.0, moyen ×0.5, bénin ignoré
    
    return facteur_gravite, vecteur_agrege
```

**📋 PROPOSITION 3 : Calcul Matrice Types Croisés**

```python
def calcul_matrice_types_croises(microzone_id, type_cible, jour_j, fenetre=7):
    """
    Matrice types croisés: autres types même microzone
    Corrélations: incendie → accidents, agressions → accidents, etc.
    """
    types_autres = {
        'accidents': ['incendies', 'agressions'],
        'incendies': ['accidents', 'agressions'],
        'agressions': ['accidents', 'incendies']
    }
    
    types_a_considerer = types_autres[type_cible]
    facteur_croise = 1.0
    
    # Corrélations spécifiques (basées sur littérature)
    correlations = {
        'incendies': {'accidents': 1.3, 'agressions': 1.1},  # Incendie → accidents fort
        'agressions': {'accidents': 1.2, 'incendies': 1.0},   # Agressions → accidents moyen
        'accidents': {'incendies': 1.1, 'agressions': 1.0}   # Accidents → autres faibles
    }
    
    for type_autre in types_a_considerer:
        hist = simulation_data[microzone_id].histoire_vecteurs[type_autre]
        
        if len(hist) < fenetre:
            continue
        
        # Agrégation récente (7 derniers jours)
        total_recent = 0.0
        for i in range(min(fenetre, len(hist))):
            vecteur = hist[-(i+1)]
            total_recent += sum(vecteur)  # Tous niveaux de gravité
        
        # Facteur selon corrélation
        corr = correlations.get(type_autre, {}).get(type_cible, 1.0)
        facteur_croise *= (1.0 + 0.1 * corr * total_recent / fenetre)
    
    return min(facteur_croise, 2.0)  # Cap à ×2 pour éviter explosion
```

**📋 PROPOSITION 4 : Calcul Matrice Voisins**

```python
def calcul_matrice_voisins(microzone_id, type_incident, jour_j, variabilite_locale=0.5):
    """
    Matrice voisins: 8 microzones radius 1
    Pondération: grave×1.0, moyen×0.5, bénin×0.2
    Modulée par variabilité locale
    """
    # Trouver 8 voisins (structure géographique précalculée)
    voisins = trouver_voisins_radius_1(microzone_id)  # Liste de 8 IDs
    
    facteur_voisins = 1.0
    poids_total = 0.0
    
    for voisin_id in voisins:
        hist = simulation_data[voisin_id].histoire_vecteurs[type_incident]
        
        if len(hist) == 0:
            continue
        
        # Vecteur le plus récent du voisin
        vecteur_voisin = hist[-1]  # [grave, moyen, bénin]
        
        # Pondération par gravité
        influence_voisin = (
            vecteur_voisin[0] * 1.0 +  # Grave
            vecteur_voisin[1] * 0.5 +  # Moyen
            vecteur_voisin[2] * 0.2    # Bénin
        )
        
        facteur_voisins += variabilite_locale * 0.1 * influence_voisin
        poids_total += 1.0
    
    # Normalisation par nombre de voisins
    if len(voisins) > 0:
        facteur_voisins = 1.0 + (facteur_voisins - 1.0) / len(voisins)
    
    return min(facteur_voisins, 1.5)  # Cap à ×1.5 pour éviter explosion
```

**📋 PROPOSITION 5 : Intégration dans Modèle Scientifique (Étape 6)**

```python
def calcul_intensites_calibrees(microzone_id, type_incident, gravite, jour_j, 
                                 regime, variabilite_locale):
    """
    Étape 6 du modèle scientifique: Calcul intensités calibrées
    Intègre les 3 matrices + vecteurs statiques + prix m²
    """
    # 1. Intensité de base selon régime (du PDF)
    lambda_base = INTENSITES_BASE[regime][type_incident][gravite]
    # Exemple: INTENSITES_BASE['Stable']['Agression']['Bénin'] = 0.0344
    
    # 2. Vecteur statique (patterns Paris)
    vecteur_stat = simulation_data[microzone_id].vecteurs_statiques[type_incident]
    facteur_statique = 1.0 + 0.3 * vecteur_stat[GRAVITE_INDEX[gravite]]
    
    # 3. Prix m² (division agressions)
    prix_m2 = get_prix_m2(microzone_id)
    prix_m2_moyen = 10000.0  # Paris moyenne
    if type_incident == 'agressions':
        facteur_prix_m2 = prix_m2 / prix_m2_moyen
        lambda_base = lambda_base / max(facteur_prix_m2, 0.5)  # Division, min 0.5
    
    # 4. Matrice gravité (même type, même microzone)
    facteur_gravite, _ = calcul_matrice_gravite(microzone_id, type_incident, jour_j)
    
    # 5. Matrice types croisés (autres types, même microzone)
    facteur_croise = calcul_matrice_types_croises(microzone_id, type_incident, jour_j)
    
    # 6. Matrice voisins (8 zones alentours)
    facteur_voisins = calcul_matrice_voisins(microzone_id, type_incident, jour_j, 
                                             variabilite_locale)
    
    # 7. Facteur long-terme (stress 60j) - du modèle scientifique
    stress = simulation_data[microzone_id].stress_long_terme
    kappa_s = SENSIBILITE_REGIME[regime]  # 0.10, 0.40, 0.80
    facteur_long = 1.0 + kappa_s * stress
    
    # 8. Combinaison (multiplicative avec caps)
    lambda_calibre = (
        lambda_base *
        facteur_statique *
        facteur_gravite *
        facteur_croise *
        facteur_voisins *
        facteur_long
    )
    
    # Caps pour éviter explosions
    lambda_calibre = min(lambda_calibre, lambda_base * 3.0)  # Max ×3
    lambda_calibre = max(lambda_calibre, lambda_base * 0.1)   # Min ×0.1
    
    return lambda_calibre
```

**📋 PROPOSITION 6 : Normalisation Z(t) et Probabilités Finales**

```python
def calcul_probabilites_j_plus_1(microzone_id, jour_j, regime, variabilite_locale):
    """
    Étape 7: Probabilités finales J+1 avec normalisation Z(t)
    """
    # Calculer toutes les intensités calibrées (9 combinaisons type × gravité)
    intensites = {}
    for type_inc in ['incendies', 'accidents', 'agressions']:
        for gravite in ['bénin', 'moyen', 'grave']:
            key = (type_inc, gravite)
            intensites[key] = calcul_intensites_calibrees(
                microzone_id, type_inc, gravite, jour_j, regime, variabilite_locale
            )
    
    # Normalisation Z(t)
    Z_t = sum(intensites.values())
    
    # Probabilités conditionnelles (si incident)
    probas_conditionnelles = {
        key: intensite / Z_t 
        for key, intensite in intensites.items()
    }
    
    # Probabilité zero-inflation (Étape 5)
    stress = simulation_data[microzone_id].stress_long_terme
    pattern_court = simulation_data[microzone_id].pattern_court_terme
    
    p0_base = PROB_ZERO_INFLATION[regime]  # 0.85, 0.75, 0.60
    p0 = p0_base * np.exp(-0.05 * stress) * np.exp(-0.10 * pattern_court)
    
    # Probabilités finales (Étape 7)
    probas_finales = {
        'rien': p0
    }
    
    for key, prob_cond in probas_conditionnelles.items():
        probas_finales[key] = (1.0 - p0) * prob_cond
    
    # Vérification normalisation
    assert abs(sum(probas_finales.values()) - 1.0) < 1e-6
    
    return probas_finales
```

**📋 PROPOSITION 7 : Optimisation Performance**

```python
# Précalculs pour éviter recalculs
class CacheCalculs:
    def __init__(self):
        self.cache_voisins = {}  # {(microzone_id, type): facteur}
        self.cache_gravite = {}  # {(microzone_id, type, jour): facteur}
        self.cache_croise = {}   # {(microzone_id, type, jour): facteur}
        self.jour_cache = -1
    
    def invalidate(self, jour_j):
        """Invalider cache si nouveau jour"""
        if jour_j != self.jour_cache:
            self.cache_voisins.clear()
            self.cache_gravite.clear()
            self.cache_croise.clear()
            self.jour_cache = jour_j

cache = CacheCalculs()

# Utilisation dans boucle principale
def boucle_simulation(jour_j):
    cache.invalidate(jour_j)
    
    for microzone_id in range(1, 101):
        # Calculs avec cache
        regime = simulation_data[microzone_id].regime_actuel
        probas = calcul_probabilites_j_plus_1(microzone_id, jour_j, regime, variabilite)
        
        # Génération aléatoire selon probabilités
        vecteur = generer_vecteur_selon_probas(probas)
        
        # Mise à jour historique
        simulation_data[microzone_id].histoire_vecteurs['incendies'].append(vecteur['incendies'])
        # ...
```

**📋 PROPOSITION 8 : Gestion Événements Graves (Classes)**

```python
from abc import ABC, abstractmethod

class EventGrave(ABC):
    """Classe parent événement grave"""
    def __init__(self, microzone_id, jour, casualties_base):
        self.microzone_id = microzone_id
        self.jour = jour
        self.casualties_base = casualties_base
        self.duration = self.calculer_duration()
        self.characteristics = self.generer_characteristics()
    
    @abstractmethod
    def calculer_duration(self):
        """Durée spécifique par type"""
        pass
    
    @abstractmethod
    def generer_characteristics(self):
        """Caractéristiques probabilistes"""
        pass
    
    def influencer_ligne_temporelle(self, simulation_data):
        """Influence sur génération J+1"""
        # Augmenter stress long-terme
        simulation_data[self.microzone_id].stress_long_terme += 0.5
        
        # Augmenter pattern court-terme
        simulation_data[self.microzone_id].pattern_court_terme += 1
        
        # Forcer transition régime si nécessaire
        if simulation_data[self.microzone_id].stress_long_terme > 15:
            simulation_data[self.microzone_id].regime_actuel = 'Crise'

class AccidentGrave(EventGrave):
    def calculer_duration(self):
        return np.random.choice([3, 4, 5], p=[0.4, 0.4, 0.2])
    
    def generer_characteristics(self):
        return {
            'traffic_slowdown': np.random.random() < 0.7,  # 70% prob
            'cancel_sports': np.random.random() < 0.2,     # 20% prob
            'increase_bad_vectors': np.random.random() < 0.5,  # 50% prob
            'kill_pompier': np.random.random() < 0.05  # 5% prob
        }

class IncendieGrave(EventGrave):
    def calculer_duration(self):
        return np.random.choice([4, 5, 6], p=[0.3, 0.5, 0.2])
    
    def generer_characteristics(self):
        return {
            'traffic_slowdown': np.random.random() < 0.8,  # 80% prob (plus fort)
            'cancel_sports': np.random.random() < 0.1,
            'increase_bad_vectors': np.random.random() < 0.6,
            'kill_pompier': np.random.random() < 0.08  # 8% prob (plus dangereux)
        }

class AgressionGrave(EventGrave):
    def calculer_duration(self):
        return np.random.choice([2, 3], p=[0.6, 0.4])
    
    def generer_characteristics(self):
        return {
            'traffic_slowdown': np.random.random() < 0.5,
            'cancel_sports': np.random.random() < 0.4,  # 40% prob (plus fort)
            'increase_bad_vectors': np.random.random() < 0.7,  # 70% prob (plus fort)
            'kill_pompier': np.random.random() < 0.02
        }
```

**✅ RÉSUMÉ IMPLÉMENTATION:**

1. **Structure données:** `MicrozoneData` avec `deque` pour historique (maxlen=60)
2. **Matrice gravité:** Décroissance exponentielle sur 7 jours
3. **Matrice croisée:** Corrélations spécifiques par type, fenêtre 7 jours
4. **Matrice voisins:** Pondération grave×1.0, moyen×0.5, bénin×0.2, modulée variabilité
5. **Intégration:** Étape 6 modèle scientifique, combinaison multiplicative avec caps
6. **Normalisation:** Z(t) garantit probabilités cibles
7. **Performance:** Cache pour éviter recalculs
8. **Événements graves:** Classes avec héritabilité, influence ligne temporelle

Ces pistes sont prêtes pour l'implémentation technique.

#### 8.4 Paramètres Utilisateur & Impact Modèle Scientifique

- **Scénario (pessimiste/moyen/optimiste)** → Comment impacte-t-il le modèle ?
  - Modifie probabilités zero-inflation par régime ?
  - Modifie intensités λ_base ?
  - Modifie matrices de transition entre régimes ?
  - Autre impact (précisez)

- **Variabilité locale** → Impact sur le modèle scientifique ?
  - Influence sur transitions entre régimes ?
  - Impact sur détection patterns court-terme (7 jours) ?
  - Impact sur accumulation stress long-terme (60 jours) ?

#### 8.5 Variables Cachées & Patterns Paris

- **Stress long-terme (60 jours):** Comment les patterns Paris influencent-ils l'accumulation ?
  - Vecteurs statiques → pondération différente du stress ?
  - Seuil basculement Crise (15) → ajusté selon contexte local (microzones sensibles) ?

- **Patterns court-terme (7 jours):** Détection déclencheur (≥4 événements moyens) → modulée par patterns ?
  - Seuil différent selon microzone (basé sur vecteurs statiques) ?
  - Impact multiplicateur transitions (×3.5) → variable selon contexte local ?

---

#### 8.6 Classes Événements Graves & Héritabilité

**✅ CONCEPT: Classes événements graves avec héritabilité**

- **Classes:** AccidentGrave, IncendieGrave, AgressionGrave
- **Héritabilité:** Caractéristiques communes + spécificités par type
- **Capacité d'influence:** Ligne temporelle, arrondissements, microzones

**Questions de clarification:**

1. **Structure classe événement grave:**
   - Attributs communs (hérités) : durée, casualties_base, characteristics probabilistes ?
   - Attributs spécifiques par type : quelles différences Accident vs Incendie vs Agression ?
   - Exemple structure Python souhaitée ?

2. **Héritabilité:**
   - Classe parent `EventGrave` avec méthodes communes ?
   - Classes enfants `AccidentGrave(EventGrave)`, `IncendieGrave(EventGrave)`, `AgressionGrave(EventGrave)` ?
   - Ou composition (événement contient caractéristiques type) ?

3. **Influence sur ligne temporelle:**
   - Comment événements graves modifient-ils génération J+1 ?
   - Impact sur régimes cachés (transitions forcées) ?
   - Impact sur variables cachées (stress, patterns) ?
   - Impact sur intensités λ (multiplicateurs temporaires) ?

4. **Influence sur arrondissements/microzones:**
   - Rayon d'impact spatial (radius) ?
   - Propagation aux microzones voisines ?
   - Caractéristiques probabilistes (Traffic×2, Cancel sports, Increase bad vectors, Kill pompier) → comment appliquées ?

5. **Gestion technique:**
   - Stockage événements graves (liste, dictionnaire, DataFrame) ?
   - Accès aux variables depuis génération J+1 ?
   - Performance (100 microzones, événements multiples) ?

---

## 9. Validation Modèle & CSV Phase 2 (Données Réelles)

### Contexte
Phase 2 : remplacer données synthétiques par vraies données BSPP. Le modèle doit être compatible et validable.

### Questions Brainstorming

#### 9.1 Format CSV Phase 2 & Compatibilité Modèle Scientifique

- **Format exact CSV** pour import données réelles BSPP ?
  - Colonnes minimales requises (type, gravité, date, microzone, etc.)
  - Format dates/timestamps
  - Identifiants microzones/arrondissements
  - Structure compatible modèle Zero-Inflated Poisson + Régimes

- **Mapping CSV → Structure Modèle Scientifique** :
  - Colonnes CSV → indicateurs binaires I_t^(τ,g) (type × gravité)
  - Colonnes CSV → historique H_t (pour calcul stress, patterns)
  - Colonnes CSV → features hebdo (pour ML)
  - Colonnes CSV → labels mensuels (pour ML)
  - **Régimes cachés:** Comment inférer depuis données réelles ? (Phase 2)

- **Compatibilité avec modèle scientifique:**
  - Données réelles permettent-elles de calculer stress long-terme (60j) ?
  - Détection patterns court-terme (7j) possible avec vraies données ?
  - Inférence régimes cachés depuis historique réel ?

#### 9.2 Validation & Calibration Modèle Scientifique

- **Validation modèle Zero-Inflated Poisson:**
  - Vérifier probabilités zero-inflation (80% baseline) vs données réelles
  - Validation distribution multinomiale conditionnelle (82% bénin, 16% moyen, 2% grave)
  - Tests statistiques (Kolmogorov-Smirnov, Chi², tests zero-inflation)

- **Calibration régimes cachés:**
  - Inférence régimes (Stable/Détérioration/Crise) depuis données réelles
  - Validation matrices de transition Q_base vs transitions observées
  - Calibration seuils (stress >15 → Crise, pattern ≥4 événements/7j)

- **Calibration intensités λ_base:**
  - Ajustement λ_base par régime selon données réelles BSPP
  - Validation patterns socio-économiques (prix m², chômage, etc.)
  - Ajustement facteurs long-terme (κ_s) et court-terme selon contexte Paris

- **Validation variables cachées:**
  - Stress long-terme (60j): cohérence avec accumulation observée ?
  - Patterns court-terme (7j): détection déclencheur validée ?
  - Décroissance hyperbolique (β_ℓ) cohérente avec données ?

#### 9.3 Gestion Données Réelles
- **Données manquantes/incomplètes** :
  - Stratégie (interpolation, valeurs par défaut, exclusion)
  - Impact sur génération
  - Alertes utilisateur

- **Cohérence temporelle** :
  - Gaps temporels dans données
  - Extrapolation si nécessaire
  - Validation continuité

---

## 10. Évolutions Modèle & Architecture (Phase 2/3)

### Contexte
Le modèle doit évoluer pour intégrer plus de complexité, vraies données, et améliorations basées sur retours utilisateurs.

### Questions Brainstorming

#### 10.1 Roadmap Modèle Scientifique Phase 2

- **Migration vers modèle complet** (si MVP simplifié):
  - Implémentation Zero-Inflated Poisson
  - Intégration régimes cachés (Stable/Détérioration/Crise)
  - Variables cachées long/court-terme
  - Matrices de transition dynamiques

- **Améliorations modèle scientifique:**
  - Patterns supplémentaires (météo, événements spéciaux) → impact sur régimes ?
  - Processus de Hawkes (cross-excitation) → déjà dans modèle scientifique ?
  - Boucles rétroactives (events positifs) → transitions vers régimes meilleurs ?
  - Near-repeat patterns spatiaux → intégration dans détection patterns ?

- **Intégration vraies données BSPP:**
  - Workflow import/validation
  - Calibration automatique intensités λ_base
  - Inférence régimes depuis historique réel
  - Comparaison synthétique vs réel (métriques, visualisations)

#### 10.2 Évolutions Architecture
- **Nouvelles fonctionnalités** nécessitant changements modèle :
  - Prédictions multi-mois
  - Scénarios "what-if" (changements patterns)
  - Analyse sensibilité (quels patterns impactent le plus)
  - Optimisation ressources (casernes, pompiers)

#### 10.3 Validation Scientifique Continue
- **Comment maintenir** la crédibilité scientifique du modèle ?
  - Documentation sources littérature
  - Validation périodique avec données réelles
  - Peer review (si possible)
  - Métriques qualité modèle

---

# 🎯 OBJECTIF BRAINSTORMING

**Préparer Session 5** en ayant clarifié :
1. ✅ **Option B choisie** : MVP avec modèle scientifique complet (Zero-Inflated Poisson + Régimes Cachés)
2. ✅ **Vecteurs statiques** : Interface patterns Paris → modèle scientifique (3×3 valeurs par microzone)
3. ⏳ **Intégration technique** : Comment gérer génération et accès aux variables
4. ⏳ **Classes événements graves** : Héritabilité, caractéristiques, influence ligne temporelle
5. ⏳ **Mapping patterns → vecteurs statiques** : Formule facteurs socio-économiques → 3×3 valeurs
6. ⏳ **Modulation λ_base** : Formule exacte vecteurs statiques × intensités calibrées
7. ⏳ **Compatibilité Phase 2** : CSV, validation, calibration

**Décisions prises:**
- ✅ Modèle scientifique dès MVP
- ✅ Vecteurs statiques comme interface patterns → modèle
- ✅ Vecteurs statiques influencent régimes ET intensités (les deux)
- ✅ **Prix m²:**
  - Divise probabilité création agression
  - Diminue probabilités régimes Tension/Crise
- ✅ **Trois matrices dans calcul J+1:**
  - Matrice gravité microzone (même type, même microzone)
  - Matrice types croisés (autres types, même microzone)
  - Matrice voisins (8 zones alentours)

**Questions en suspens:**
- ⏳ Formule calcul vecteurs statiques depuis patterns Paris
- ⏳ Formule intégration vecteurs statiques dans algorithme scientifique
- ⏳ Structure classes événements graves (héritabilité)
- ⏳ Gestion technique accès variables (performance, stockage)

**Même si cela ne change rien à l'interface utilisateur**, ces décisions impactent :
- La **crédibilité** du modèle
- La **facilité d'intégration** vraies données Phase 2
- La **maintenabilité** et évolutivité
- La **validation scientifique** du projet
- La **performance** et architecture technique

---

# 📝 NOTES

*Échange 4.3 en cours - Questions 8, 9, 10 à compléter*

---

**Créé:** 25 Janvier 2026  
**Statut:** ⏳ En attente  
**Précédent:** Session 4.2  
**Prochaine étape:** Session 5 (Validation Finale Brainstorm)
