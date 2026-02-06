# Fichier de référence – Patterns Paris (4j, 7j, 60j)

**Story 1.4** · **Version** 1.0 · **Date** 29 Janvier 2026

---

## 1. Objectif

Ce document définit le **format exact** des fichiers patterns Paris dans `data/patterns/`.  
Il sert de référence pour :
- **Story 1.3** (vecteurs statiques)
- **Story 2.2.2** (patterns 4j / 7j / 60j)
- **Story 1.4.4** (matrices de corrélation, même vocabulaire types / gravités / régimes)

Voir aussi : `docs/philosophy-patterns-json.md` (philosophie et exemples détaillés).

---

## 2. Emplacement et nommage

| Règle | Description |
|-------|-------------|
| **Dossier** | `data/patterns/` |
| **Convention** | `pattern_{4j|7j|60j}_{nom}.json` ou `pattern_{4j|7j|60j}_example.json` |
| **Exemples** | `pattern_4j_example.json`, `pattern_7j_example.json`, `pattern_60j_example.json` |

---

## 3. Format commun (niveau global)

Tous les patterns partagent la structure racine suivante.

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `pattern_type` | string | oui | `"4j"`, `"7j"` ou `"60j"` |
| `pattern_name` | string | oui | Identifiant lisible (ex. `weekend_paris`) |
| `description` | string | non | Description courte |
| `version` | string | oui | Version du format (ex. `"1.0"`) |
| `created_at` | string | oui | Date ISO 8601 (ex. `2026-01-28T10:30:00Z`) |
| `microzones` | array | oui | Liste d’objets `{ microzone_id, patterns }` |

---

## 4. Niveau microzone

Chaque élément de `microzones` contient :

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `microzone_id` | string | oui | Ex. `mz_001`, `MZ025` |
| `patterns` | object | oui | Clés : `agressions`, `incendies`, `accidents` |

---

## 5. Niveau type d’incident et gravité

Pour chaque type (`agressions`, `incendies`, `accidents`), on trouve trois gravités :  
`benin`, `moyen`, `grave`.  
Cohérent avec `precompute_matrices_correlation` (types, gravités, régimes).

Pour chaque `(type, gravité)` :

| Champ | Type | Obligatoire | Contraintes | Description |
|-------|------|-------------|-------------|-------------|
| `probabilite_base` | float | oui | `0.0 ≤ x ≤ 1.0` | Probabilité de base |
| `facteurs_modulation` | object | oui | — | Voir ci‑dessous |
| `influence_regimes` | object | non | — | Multiplicateurs par régime (4j, 7j) |
| `influence_intensites` | object | non | — | `multiplicateur`, `offset` (surtout 60j) |

### 5.1 `facteurs_modulation`

- **`regime`** (obligatoire) : `stable`, `deterioration`, `crise` (aligné matrices 1.4.4).
- **`saison`** (obligatoire) : `hiver`, `printemps`, `ete`, `automne` — ou `hiver`, `intersaison`, `ete` selon usage.
- **`jour_semaine`** (7j uniquement) : `lundi` … `dimanche`.
- **`jour_mois`** (60j uniquement) : clés `"1"` … `"31"`, valeurs multiplicateurs.

Valeurs : nombres > 0, typiquement dans `[0.5, 2.0]`.

---

## 6. Formats par pattern

### 6.1 Pattern 4j (court terme)

- **Période** : 4 jours.
- **Spécificité** : `facteurs_modulation` = `regime` + `saison` (pas de `jour_semaine` ni `jour_mois`).
- **Optionnel** : `influence_regimes` par régime.

### 6.2 Pattern 7j (hebdomadaire)

- **Période** : 7 jours.
- **Spécificité** : `facteurs_modulation` inclut `jour_semaine` (`lundi` … `dimanche`).
- **Optionnel** : `influence_regimes`.

### 6.3 Pattern 60j (long terme)

- **Période** : 60 jours (~2 mois).
- **Spécificité** : `facteurs_modulation` peut inclure `jour_mois` (clés `"1"` … `"31"`).
- **Optionnel** : `influence_intensites` avec `multiplicateur` et `offset`.

---

## 7. Validation

- **Schéma** : Pydantic (voir `scripts/validate_patterns.py`).
- **Vérifications** : JSON valide, champs obligatoires, types et plages (ex. `probabilite_base` ∈ [0, 1], multiplicateurs > 0).
- **CLI** : `python scripts/validate_patterns.py [--path data/patterns]` et `--validate-patterns` / `--only-validate-patterns` dans `run_precompute`.

---

## 8. Chargement et utilisation

### 8.1 Chargement

Les patterns sont chargés par :
- **Story 1.3** : `VectorsStaticCalculator.load_patterns(patterns_dir)` dans `precompute_vectors_static`.
- Les exemples sont dans `data/patterns/` (`pattern_4j_example.json`, etc.).

### 8.2 Structure utilisée (ex. 1.3)

Pour un pattern chargé (format référence avec `microzones`) :

1. Parcourir `microzones` et, pour chaque `microzone_id`, lire `patterns[type][gravite]`.
2. Utiliser `probabilite_base` (et optionnellement `facteurs_modulation`) pour les calculs.
3. Si une microzone n’a pas d’entrée, utiliser la première microzone du fichier comme défaut, ou des valeurs par défaut définies en dur.

### 8.3 Lien avec les matrices de corrélation (1.4.4)

`precompute_matrices_correlation` utilise les mêmes **types** (`agressions`, `incendies`, `accidents`), **gravités** (`benin`, `moyen`, `grave`) et **régimes** (`stable`, `deterioration`, `crise`). Les patterns peuvent alimenter ou compléter ces données (ex. probabilités de base, facteurs de modulation) dans des stories ultérieures.

---

## 9. Exemples de fichiers

- `data/patterns/pattern_4j_example.json`
- `data/patterns/pattern_7j_example.json`
- `data/patterns/pattern_60j_example.json`

Ils respectent ce référence et sont validés par `validate_patterns` et les tests dans `tests/data/patterns/`.

---

## 10. Résumé des contraintes

| Élément | Contraintes |
|--------|-------------|
| `pattern_type` | `"4j"` \| `"7j"` \| `"60j"` |
| Types d’incident | `agressions`, `incendies`, `accidents` |
| Gravités | `benin`, `moyen`, `grave` |
| Régimes | `stable`, `deterioration`, `crise` |
| `probabilite_base` | `0.0`–`1.0` |
| Multiplicateurs | `> 0` (souvent `0.5`–`2.0`) |

---

**Document de référence** pour Story 1.4. Utilisation par Story 1.3, 2.2.2, 1.4.4.
