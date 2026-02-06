# Génération des vecteurs, congestion des routes et incidents alcool / nuit

Ce document décrit comment sont produits, à chaque jour J, les **vecteurs d’incidents** (accidents, agressions, incendies) par microzone, la **congestion des routes**, et le nombre d’incidents **liés à l’alcool** ou **survenus la nuit**.

---

## 1. Génération des vecteurs d’incidents (J)

Pour chaque microzone et chaque type d’incident (accident, agression, incendie), on génère un **vecteur** `(bénin, moyen, grave)` : nombre d’incidents de chaque gravité ce jour-là.

### 1.1 Intensité de base (vecteurs statiques + calibration)

- **Source** : `StaticVectorLoader` charge les vecteurs statiques (`vecteurs_statiques.pkl`) par microzone et par type. Chaque entrée est un triplet (bénin, moyen, grave) normalisé [0, 1].
- **Conversion en intensité** :  
  `λ_base = benin×0.5 + moyen×1.0 + grave×2.0`  
  (facteurs dans `static_vector_loader.py` : `FACTEUR_BENIN`, `FACTEUR_MOYEN`, `FACTEUR_GRAVE`).
- **Recalibration** : pour éviter des niveaux trop hauts partout, les intensités brutes sont **recentrées** par type : la **moyenne** (sur toutes les microzones) est ramenée aux cibles de calibration (`BASE_INTENSITY_ACCIDENT`, `_AGRESSION`, `_INCENDIE` dans `calibration.py`). Les **écarts relatifs** entre microzones sont conservés (zones avec plus d’agressions en statique ont toujours plus d’intensité).
- **Défaut** : si une microzone/type n’a pas de vecteur statique, on utilise les intensités par défaut de calibration (`DEFAULT_INTENSITES_BY_TYPE`).

### 1.2 Modulation de l’intensité (J)

L’intensité de base est ensuite modulée par :

1. **Matrices de modulation** (`MatrixModulator`) :
   - **Gravité** : historique 7 jours (décroissance exponentielle), matrice intra-type.
   - **Types croisés** : effet des autres types (inter-type) et conformité J-1.
   - **Voisins** : effet des incidents chez les voisins (matrices voisin), pondéré par **variabilité locale** (paramètre de run : Faible / Moyenne / Forte → 0.3 / 0.5 / 0.7).
2. **Régime caché** (Stable / Détérioration / Crise) : facteur ×1.0 / ×1.3 / ×2.0 sur l’intensité ; les transitions de régime sont modulées par **prix m²** et par le **scénario** (`proba_crise`).
3. **Saisonnalité** : facteur par type et saison (ex. incendies ×1.3 en hiver).
4. **Événements graves / positifs** : augmentation ou réduction selon les événements actifs.
5. **Scénario** : `facteur_intensite` (Pessimiste > 1, Standard = 1, Optimiste < 1) multiplie l’intensité après calcul.
6. **Prix m²** : modulation de l’intensité (surtout agressions) et des probabilités de régime.
7. **Effets de réduction** : événements positifs actifs réduisent l’intensité par arrondissement.

### 1.3 Modèle Zero-Inflated Poisson (ZIP)

- **Probabilité de zéro** :  
  `p_zero = exp(-α × λ × régime) / (1 + exp(-α × λ × régime))`  
  avec `α = ZERO_INFLATION_ALPHA` (calibration).
- **Tirage** : avec probabilité `p_zero` on obtient 0 incident ; sinon on tire un entier selon une Poisson d’intensité λ.
- **Répartition bénin / moyen / grave** : si le total > 0, on utilise les **probabilités croisées** (matrice 3×3 selon la gravité dominante J-1) pour répartir le total en (bénin, moyen, grave) via une multinomiale.

Résultat : pour chaque (microzone, type), un vecteur `Vector(grave, moyen, bénin)` pour le jour J.

---

## 2. Congestion des routes (J)

La congestion (taux de ralentissement du trafic) par microzone est calculée **après** la génération des vecteurs du jour, dans `CongestionCalculator.calculate_congestion_for_day`.

### 2.1 Entrées

- **Congestion statique** : niveau de base par microzone (fichier `congestion_statique.pkl`).
- **Vecteurs du jour** : accidents, agressions, incendies par microzone.
- **Événements graves / positifs** du jour.
- **Incidents nuit** : nombre d’incidents nocturnes par microzone et type (`dynamic_state.incidents_nuit`), utilisé pour le facteur « nuit ».

### 2.2 Formule (par microzone)

- **Randomité** : composante aléatoire (pondération 20 % en normal, 70 % en cas d’événement important).
- **Déterministe** :  
  `congestion_base × (accident_effect × fire_effect × aggression_effect × neighbor_effect × recurrence_effect × season_factor) × poids_déterministe`.
- **Effets temporels** : incendies J+1/J+2, agressions graves J+1/J+2/J+3, récurrence, voisins.
- **Facteur nuit** : si la microzone a des **incidents nuit** ce jour, la congestion est divisée (÷3 en moyenne, ÷2.2 en été) pour refléter un trafic nocturne plus fluide.
- **Événements** : les événements graves augmentent la congestion ; les événements positifs la diminuent.
- La valeur finale est bornée (ex. entre 0.1 et 5.0) puis **normalisée** pour être stockée dans `dynamic_state.trafic` sur [0, 1] : `trafic[mz] = min(1.0, congestion / 5.0)`.

La congestion est donc **dérivée des vecteurs et des événements** du jour, plus la base statique et les effets nuit.

---

## 3. Incidents alcool et incidents nuit

Ces grandeurs sont des **variables d’état dynamiques** : elles vivent dans `SimulationState.dynamic_state` et sont censées évoluer de J à J+1 en fonction des vecteurs générés.

### 3.1 Structure (`DynamicState`)

- **`trafic`** : `Dict[microzone_id, float]` — niveau de congestion [0, 1]. **Mis à jour** dans `generate_day` via `CongestionCalculator.calculate_congestion_for_day` puis normalisation.
- **`incidents_nuit`** : `Dict[microzone_id, Dict[type_incident, int]]` — nombre d’incidents **survenus la nuit** par microzone et type (agressions, incendies, accidents).
- **`incidents_alcool`** : `Dict[microzone_id, Dict[type_incident, int]]` — nombre d’incidents **liés à l’alcool** par microzone et type.

### 3.2 Évolution prévue J → J+1

Le module `src.core.evolution` fournit :

- **`evoluer_incidents_nuit_J1`** : met à jour les comptes « nuit » avec mémoire (~65 %), corrélations inter-type et saisonnalité (+20 % été).
- **`evoluer_incidents_alcool_J1`** : idem pour « alcool », avec saisonnalité (+50 % accidents en été).

Les deux prennent en entrée les **vecteurs du jour J** convertis en comptes par type (`incidents_J`), les comptes nuit/alcool précédents, les matrices inter-type et la saison. Ils **ne décomposent pas** explicitement les vecteurs générés en « part alcool » / « part nuit » : ils produisent des **séries temporelles** cohérentes avec le volume d’incidents (mémoire + corrélations).

- **`evoluer_dynamic_state`** appelle ces évolutions et met à jour `state.trafic`, `state.incidents_nuit`, `state.incidents_alcool` en une fois.

**Point d’intégration actuel** : dans le flux de `GenerationService.generate_day`, **seul `trafic`** est mis à jour (via le calculateur de congestion). **`evoluer_dynamic_state` n’est pas appelé** dans ce flux ; il est utilisé dans les tests d’évolution. Donc, en l’état, **`incidents_nuit` et `incidents_alcool` restent à 0** (valeurs initialisées par `ensure_microzones`) sauf si un autre composant les met à jour. Pour que les proportions alcool/nuit reflètent l’évolution J→J+1, il faudrait appeler `evoluer_dynamic_state` après la génération des vecteurs (en lui passant les vecteurs du jour convertis en `incidents_J`).

### 3.3 Utilisation en aval

- **Congestion** : `incidents_nuit` est lu par `CongestionCalculator._calculate_night_congestion_factor` pour réduire la congestion quand il y a des incidents nocturnes.
- **Features ML** : `FeatureCalculator` calcule des proportions alcool et nuit par type (ex. `agressions_alcool`, `agressions_nuit`, etc.) à partir de `dynamic_state.incidents_alcool` et `incidents_nuit` (par microzone puis agrégation arrondissement).
- **Golden Hour / CasualtyCalculator** : peuvent utiliser des indicateurs nuit/alcool par incident pour ajuster temps de trajet ou calcul de morts/blessés graves.

---

## 4. Résumé des flux dans `generate_day`

1. **Vecteurs J** : intensités de base (vecteurs statiques + recalibration) → modulation (matrices, régime, saison, événements, scénario, variabilité, prix m², effets réduction) → ZIP → répartition (bénin, moyen, grave) → stockage dans `vectors_state`.
2. **Congestion** : vecteurs J + événements + `incidents_nuit` → `CongestionCalculator.calculate_congestion_for_day` → mise à jour de `dynamic_state.trafic`.
3. **Événements graves / positifs** : génération et enregistrement dans `events_state`.
4. **Incidents nuit / alcool** : prévus pour être mis à jour par `evoluer_dynamic_state(..., incidents_J)` ; non branché dans `generate_day` actuellement, donc restent à 0 tant que ce branchement n’est pas fait.

---

## 5. Règle sur les modifications de probabilités (+0.1 = relatif, pas brut)

**Toute modification de type « +0.1 » (ou +10 %) doit être appliquée en multiplicatif sur la probabilité de base, jamais en additif.**

- **Correct** : `proba_nouvelle = proba_base × (1 + 0.1)`  
  Exemple : proba accidents grave de base 0,4 % → avec +10 % : `0,004 × 1,1 = 0,0044` (0,44 %).
- **Incorrect** : `proba_nouvelle = proba_base + 0.1`  
  Cela donnerait 10,4 %, ce qui n’a pas de sens pour une proba déjà en %.

Dans le code actuel, les effets du type « +10 % » ou « +0.1 » sont bien appliqués en **facteur** sur l’intensité λ ou sur des probabilités (ex. `facteur = 1.0 + 0.1`, puis `λ_new = λ × facteur` ou `proba_new = proba × facteur`). Les **probabilités croisées** (bénin, moyen, grave) pour J+1 viennent **directement de la matrice calibrée** : on choisit la ligne selon la **gravité dominante** J-1 (bénin, moyen ou grave), puis on utilise cette ligne telle quelle ; il n’y a **pas** aujourd’hui d’effet du type « 2 accidents moyens → +0.1 sur la proba accident grave ». Si on ajoute un tel effet, il doit être **multiplicatif** sur la proba de base (ex. proba grave 0,4 % → 0,44 %) :  
`proba_grave_j1 = proba_grave_base × (1 + 0.1)` (puis renormaliser la ligne bénin/moyen/grave), et **jamais** `proba_grave_base + 0.1`.

---

## 6. Régime : valeurs et modifications

Toutes les valeurs numériques liées au **régime** (Stable / Détérioration / Crise) et aux **modulations** associées sont listées ici. Les effets sont **multiplicatifs** (facteurs sur intensité ou sur probabilités), pas additifs sur des probas brutes.

### 6.1 Probabilités initiales des régimes

| Régime        | Constante                    | Valeur |
|---------------|------------------------------|--------|
| Stable        | `PROBA_REGIME_STABLE`        | 0,80   |
| Détérioration | `PROBA_REGIME_DETERIORATION` | 0,15   |
| Crise         | `PROBA_REGIME_CRISE`         | 0,05   |

Fichier : `src/core/generation/regime_manager.py`.

### 6.2 Matrice de transition de régime (par défaut)

Lignes = régime actuel ; colonnes = régime au jour J+1 (Stable, Détérioration, Crise).

| Régime actuel | → Stable | → Détérioration | → Crise |
|---------------|----------|-----------------|---------|
| Stable        | 0,85     | 0,12            | 0,03    |
| Détérioration | 0,20     | 0,70            | 0,10    |
| Crise         | 0,15     | 0,20            | 0,65    |

Fichier : `regime_manager.py` (`_create_default_transition_matrix`).

### 6.3 Facteur d’intensité par régime

| Régime        | Facteur (λ × facteur) |
|---------------|------------------------|
| Stable        | 1,0                   |
| Détérioration | 1,3 (+30 %)           |
| Crise         | 2,0 (+100 %)          |

Fichier : `regime_manager.py` (`get_regime_intensity_factor`).  
Utilisé dans `matrix_modulator.calculer_modulations_dynamiques` (`facteur_regime`) et dans la formule d’intensité calibrée.

### 6.4 Modulation par le scénario (proba_crise)

- **Référence** : `PROBA_CRISE_REF = 0.10` (config « moyen »).
- **Règle** : la probabilité de transition vers Crise (colonne Crise) est multipliée par `proba_crise / PROBA_CRISE_REF`, puis la ligne est renormalisée.
- **Config** (ex. `config.yaml`) : `scenarios.moyen.proba_crise: 0.10`, `pessimiste: 0.15`, `optimiste: 0.05`.

Fichier : `vector_generator.py` (transition de régime, après éventuelle modulation prix m²).

### 6.5 Modulation par le prix m² (transitions de régime)

- **Seuil** : `facteur_prix_m2 > 1.2` (quartier riche).
- **Si quartier riche** :  
  - `prob_deterioration_mod = prob_deterioration × 0.8`  
  - `prob_crise_mod = prob_crise × 0.7`  
- **Sinon** : pas de changement.

Fichier : `src/core/events/prix_m2_modulator.py` (`moduler_probabilites_regimes`).

### 6.6 Probabilités initiales selon les vecteurs statiques (StaticVectorLoader)

- **Facteur** : `facteur = somme_vecteurs_statiques / (moyenne_globale × 3 × 3)`.
- **Si facteur > 1,5** (zone à risque) : Stable 0,6, Détérioration 0,25, Crise 0,15.
- **Si facteur < 0,7** (zone calme) : Stable 0,9, Détérioration 0,08, Crise 0,02.
- **Sinon** (zone moyenne) : Stable 0,80, Détérioration 0,15, Crise 0,05.  
Les trois probas sont ensuite normalisées (somme = 1).

Fichier : `static_vector_loader.py` (`calculer_probabilites_regimes`).

### 6.7 Autres effets « 0.1 » (multiplicatifs dans le code)

| Où              | Effet                    | Application dans le code |
|-----------------|--------------------------|---------------------------|
| Voisins         | +10 % si seuil dépassé   | `facteur = 1.0 + (0.1 × variabilite_locale)` sur l’intensité (MatrixModulator). |
| Conformité J-1  | +10 % par incident J-1   | `facteur_conformite = 1.0 + (total_j_minus_1 × 0.1)` puis `facteur *= facteur_conformite` (facteur croisé). |
| Patterns        | +10 % par pattern actif  | `facteur_patterns *= 1.1` (modulations dynamiques). |
| Trafic > 0,7    | +15 % agressions/accidents| `f *= 1.0 + 0.15` (variables_etat). |
| Incidents nuit > 2 | +10 % tous types     | `f *= 1.0 + 0.10` (variables_etat). |
| Incidents alcool > 2 | +8 % tous types  | `f *= 1.0 + 0.08` (variables_etat). |

Dans `variables_etat_applicator.py`, le facteur `f` est appliqué **multiplicativement** aux trois probabilités (bénin, moyen, grave) : `(prob[0]*f, prob[1]*f, prob[2]*f)`. Donc un « +10 % » augmente bien chaque proba de base de 10 % en relatif (ex. 0,4 % → 0,44 %), pas en additif.

---

## 7. Fichiers principaux

| Rôle | Fichier |
|------|---------|
| Vecteurs statiques + recalibration | `src/core/generation/static_vector_loader.py` |
| Constantes de calibration | `src/core/generation/calibration.py` |
| Intensité + matrices | `src/core/generation/intensity_calculator.py`, `matrix_modulator.py` |
| Régime (transition, facteurs) | `src/core/generation/regime_manager.py` |
| Prix m² (régimes + intensité) | `src/core/events/prix_m2_modulator.py` |
| Variables d’état (trafic, nuit, alcool → facteurs) | `src/core/probability/variables_etat_applicator.py` |
| Génération ZIP + répartition | `src/core/generation/vector_generator.py`, `zero_inflated_poisson.py` |
| Orchestration jour J | `src/core/generation/generation_service.py` (`generate_day`) |
| Congestion | `src/core/generation/congestion_calculator.py` |
| Évolution trafic / nuit / alcool | `src/core/evolution/__init__.py`, `nuit_evolution.py`, `alcool_evolution.py` |
| État dynamique | `src/core/state/dynamic_state.py` |
