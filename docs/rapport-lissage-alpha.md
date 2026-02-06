# Rapport Dev : effet réel du paramètre `vecteurs_statiques.lissage_alpha`

**Contexte** : `config/config.yaml` lignes 37-38 — paramètre `lissage_alpha: 0.01`.  
**Question** : ce paramètre semble ne rien changer aux simulations. Analyse de son effet réel.

---

## 1. Chaîne d’utilisation du paramètre

| Étape | Fichier | Rôle |
|-------|---------|------|
| Config | `config/config.yaml` | `vecteurs_statiques.lissage_alpha: 0.01` |
| Validation | `src/core/config/config_validator.py` | `VecteursStatiquesConfig.lissage_alpha` (default 0.7, `ge=0`, `le=1`) |
| Simulation | `src/services/simulation_service.py` | `run_headless`, `run_one`, `advance_one_day` lisent la config et passent `lissage_alpha` au `GenerationService` |
| Génération | `src/core/generation/generation_service.py` | Crée `StaticVectorLoader(lissage_alpha=lissage_alpha)` et utilise `get_base_intensities_dict()` + `calculer_probabilites_regimes()` |
| Lissage | `src/core/generation/static_vector_loader.py` | Si `lissage_alpha < 1.0`, applique `_appliquer_lissage(alpha)` aux vecteurs statiques chargés |

Conclusion : **le paramètre est bien lu et propagé** jusqu’au chargeur de vecteurs statiques. Aucun chemin ne l’ignore (fallback 0.7 uniquement si `config.vecteurs_statiques` est absent).

---

## 2. Effet algorithmique du lissage

Dans `StaticVectorLoader` :

- **Formule** : `v_lissé = α × v_brut + (1 − α) × moyenne_par_type_gravité`
- **α = 1.0** : pas de lissage, disparité spatiale maximale.
- **α = 0.01** : lissage très fort → vecteurs quasi uniformes (1 % brut, 99 % moyenne) → peu de variation entre microzones.

Ensuite, `get_base_intensities_dict()` :

1. Calcule des intensités « brutes » à partir des vecteurs (déjà lissés) : `raw[mz][type]`.
2. **Recalibration** : pour chaque type, impose que la **moyenne** sur les microzones soit égale à la cible de calibration :
   - `intensities[mz][type] = (raw[mz][type] / mean_raw) × target`

Conséquences :

- La **moyenne** (et donc le niveau global d’intensité par type) est **fixée par la cible**, indépendamment de `lissage_alpha`.
- Ce qui change avec `lissage_alpha` est **uniquement la répartition spatiale** :
  - **α faible (ex. 0.01)** : `raw` quasi identique partout → intensités quasi identiques partout → répartition très uniforme.
  - **α = 1.0** : `raw` variable → différences nettes entre microzones (zones « chaudes » vs « calmes »).

Le paramètre influe aussi sur **calculer_probabilites_regimes** (probabilités initiales Stable / Dégradation / Crise) : avec α faible, tous les facteurs régime sont proches de 1 → mêmes probas pour toutes les microzones ; avec α = 1.0, certaines zones ont facteur &gt; 1.5 ou &lt; 0.7 → régimes plus différenciés.

---

## 3. Pourquoi l’effet peut sembler absent

1. **Métriques observées**  
   Si vous regardez surtout des **totaux** (nombre total d’incidents par run, par type, par jour), ils restent stables : la recalibration fixe la moyenne, donc le niveau global. **L’effet de `lissage_alpha` est sur la variance spatiale, pas sur le total.**

2. **Bruit dominant**  
   Variabilité locale, réaléatoirisation des matrices, régimes, etc. ajoutent beaucoup de variance. La part due aux **seules** intensités de base lissées peut être noyée si on ne compare pas explicitement des indicateurs **spatiaux** (écart-type entre microzones, disparité arrondissements, cartes).

3. **Valeur 0.01**  
   Avec α = 0.01, le lissage est déjà très fort ; passer à 0.7 ou 1.0 change beaucoup la disparité, mais 0.01 vs 0.5 peut donner des différences moins visibles sur des métriques globales.

4. **Pas de bug identifié**  
   Le code utilise bien `lissage_alpha` de la config à chaque création de `GenerationService` ; il n’y a pas de cache qui figerait un ancien alpha.

---

## 4. Recommandations pour « voir » l’effet

- **Métriques à comparer** (pour deux runs identiques, même seed, en ne changeant que `lissage_alpha`) :
  - Écart-type (ou coefficient de variation) des **intensités de base** par type entre microzones.
  - Écart-type du **nombre d’incidents par microzone** (ou par arrondissement) sur la durée du run.
  - Cartes ou heatmaps : avec α = 0.01 la carte devrait être plus uniforme qu’avec α = 1.0.
- **Test côte à côte** :  
  - Run A : `lissage_alpha: 0.01`  
  - Run B : `lissage_alpha: 1.0`  
  Comparer distribution par microzone/arrondissement (histogrammes, écarts-types), pas seulement les totaux.

---

## 5. Synthèse

| Question | Réponse |
|----------|--------|
| Le paramètre est-il utilisé ? | Oui, de la config jusqu’à `StaticVectorLoader` et `GenerationService`. |
| Modifie-t-il le niveau global d’incidents ? | Non, à cause de la recalibration (moyenne = cible). |
| Modifie-t-il la simulation ? | Oui : **répartition spatiale** des intensités de base et **probabilités initiales des régimes** par microzone. |
| Pourquoi ça peut sembler ne rien changer ? | Effet visible surtout sur **disparité spatiale** et **régimes** ; totaux et métriques globales peu sensibles ; autre variabilité peut masquer l’effet. |

**Conclusion** : `lissage_alpha` a un effet réel mais **ciblé** : il réduit ou augmente la **disparité entre microzones** (et la différenciation des régimes), pas le niveau moyen. Pour le constater, il faut comparer des indicateurs spatiaux (variance entre zones, cartes) entre deux valeurs d’alpha (par ex. 0.01 vs 1.0), pas seulement les totaux de la simulation.

---

## 6. Complément : 7e arrondissement sans événements (cause réelle)

**Problème signalé** : aucun événement n'apparaît dans le 7e arrondissement malgré un lissage à 0,01.

**Cause identifiée** : ce n'est **pas** un problème de lissage ni de vecteurs statiques. Les microzones du 7e (MZ031–MZ035) ont des valeurs dans `vecteurs_statiques.pkl` du même ordre que les autres (sommes ~67–69). La cause est le **format des identifiants** : les clés sont `MZ001`…`MZ100` (sans underscore), alors que le **fallback** d'arrondissement utilisait `microzone_id.split("_")[1]` (format `MZ_11_01`). Pour `MZ031`, cela échouait → fallback à **arrondissement 1**. Si le fichier `limites_microzone_arrondissement.pkl` n'était pas chargé (chemin, exception), **toutes** les microzones étaient attribuées à l'arrondissement 1, donc le 7e (et les autres) affichaient 0 événement.

**Correction appliquée** :
- Fallback de parsing étendu au format **MZxxx** (ex. MZ031 → 7) : 5 microzones par arrondissement (MZ001–005→1, MZ031–035→7).
- Modifications dans : `web_app.py` (`microzone_to_arrondissement`), `simulation_service.py` (`_parse_arr`), `realaléatoirisation_state.py` (`_parse_arrondissement_from_microzone_id`), `generation_service.py` (fallback `_microzone_to_arrondissement_fallback`), `vector_generator.py` (utilisation de `limites_microzone_arrondissement` pour les effets réduction).

Avec ces changements, le 7e (et tous les arrondissements) reçoit bien les événements de ses microzones, avec ou sans fichier limites.
