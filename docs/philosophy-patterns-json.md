# Philosophie du Format Patterns JSON

**Version** : 1.0  
**Date** : 28 Janvier 2026

---

## Principes Fondamentaux

### 1. Objectif

Les fichiers patterns JSON définissent les **patterns temporels Paris** (4j, 7j, 60j) qui influencent :
- **Régimes cachés** (Stable/Détérioration/Crise)
- **Intensités** λ_base(τ,g)
- **Matrices de modulation** (gravité, croisée, voisins)

### 2. Structure Générale

Tous les fichiers patterns JSON suivent une structure hiérarchique :
- **Niveau global** : Paramètres généraux du pattern
- **Niveau microzone** : Paramètres spécifiques par microzone
- **Niveau type/gravité** : Paramètres par type d'incident et gravité

### 3. Types de Patterns

#### 3.1 Pattern 4j (Court terme)
- **Période** : 4 jours
- **Influence** : Patterns courts (ex: week-end, événements ponctuels)
- **Fichier** : `data/patterns/pattern_4j_{nom}.json`

#### 3.2 Pattern 7j (Hebdomadaire)
- **Période** : 7 jours (semaine)
- **Influence** : Patterns hebdomadaires (ex: lundi vs dimanche)
- **Fichier** : `data/patterns/pattern_7j_{nom}.json`

#### 3.3 Pattern 60j (Long terme)
- **Période** : 60 jours (~2 mois)
- **Influence** : Patterns saisonniers, tendances longues
- **Fichier** : `data/patterns/pattern_60j_{nom}.json`

### 4. Structure Exacte JSON

#### 4.1 Structure Globale
```json
{
  "pattern_type": "4j" | "7j" | "60j",
  "pattern_name": "string",
  "description": "string",
  "version": "1.0",
  "created_at": "2026-01-28T10:30:00Z",
  "microzones": [
    {
      "microzone_id": "mz_001",
      "patterns": {
        "agressions": {
          "benin": { ... },
          "moyen": { ... },
          "grave": { ... }
        },
        "incendies": { ... },
        "accidents": { ... }
      }
    }
  ]
}
```

#### 4.2 Structure par Type/Gravité
```json
{
  "probabilite_base": 0.15,
  "facteurs_modulation": {
    "regime": {
      "stable": 1.0,
      "deterioration": 1.3,
      "crise": 1.8
    },
    "saison": {
      "hiver": 0.9,
      "printemps": 1.2,
      "ete": 1.0,
      "automne": 1.2
    },
    "jour_semaine": {
      "lundi": 1.1,
      "mardi": 1.0,
      "mercredi": 1.0,
      "jeudi": 1.0,
      "vendredi": 1.2,
      "samedi": 1.3,
      "dimanche": 0.8
    }
  },
  "influence_regimes": {
    "stable": 0.95,
    "deterioration": 1.05,
    "crise": 1.15
  },
  "influence_intensites": {
    "multiplicateur": 1.1,
    "offset": 0.0
  }
}
```

### 5. Champs Détaillés

#### 5.1 Niveau Global
- **pattern_type** (string, obligatoire) : "4j", "7j" ou "60j"
- **pattern_name** (string, obligatoire) : Nom du pattern (ex: "weekend_paris")
- **description** (string, optionnel) : Description du pattern
- **version** (string, obligatoire) : Version du format (actuellement "1.0")
- **created_at** (string ISO datetime, obligatoire) : Date de création
- **microzones** (array, obligatoire) : Liste des microzones avec leurs patterns

#### 5.2 Niveau Microzone
- **microzone_id** (string, obligatoire) : ID de la microzone (ex: "mz_001")
- **patterns** (object, obligatoire) : Patterns par type d'incident

#### 5.3 Niveau Type Incident
- **agressions** (object, obligatoire) : Patterns pour agressions
- **incendies** (object, obligatoire) : Patterns pour incendies
- **accidents** (object, obligatoire) : Patterns pour accidents

#### 5.4 Niveau Gravité
- **benin** (object, obligatoire) : Patterns pour incidents bénins
- **moyen** (object, obligatoire) : Patterns pour incidents moyens
- **grave** (object, obligatoire) : Patterns pour incidents graves

#### 5.5 Niveau Pattern Détail
- **probabilite_base** (float, obligatoire) : Probabilité de base (0.0 à 1.0)
- **facteurs_modulation** (object, obligatoire) : Facteurs de modulation
  - **regime** (object) : Multiplicateurs par régime (stable, deterioration, crise)
  - **saison** (object) : Multiplicateurs par saison (hiver, printemps, ete, automne)
  - **jour_semaine** (object, pour pattern 7j) : Multiplicateurs par jour (lundi à dimanche)
  - **jour_mois** (object, pour pattern 60j) : Multiplicateurs par jour du mois (1-31)
- **influence_regimes** (object, optionnel) : Influence sur probabilités régimes
- **influence_intensites** (object, optionnel) : Influence sur intensités λ_base

### 6. Exemples Complets

#### 6.1 Pattern 4j - Exemple
```json
{
  "pattern_type": "4j",
  "pattern_name": "weekend_paris",
  "description": "Pattern week-end pour Paris (vendredi-dimanche)",
  "version": "1.0",
  "created_at": "2026-01-28T10:30:00Z",
  "microzones": [
    {
      "microzone_id": "mz_001",
      "patterns": {
        "agressions": {
          "benin": {
            "probabilite_base": 0.10,
            "facteurs_modulation": {
              "regime": {
                "stable": 1.0,
                "deterioration": 1.2,
                "crise": 1.5
              },
              "saison": {
                "hiver": 0.9,
                "printemps": 1.1,
                "ete": 1.0,
                "automne": 1.1
              }
            },
            "influence_regimes": {
              "stable": 0.98,
              "deterioration": 1.02,
              "crise": 1.05
            }
          },
          "moyen": { ... },
          "grave": { ... }
        },
        "incendies": { ... },
        "accidents": { ... }
      }
    }
  ]
}
```

#### 6.2 Pattern 7j - Exemple
```json
{
  "pattern_type": "7j",
  "pattern_name": "hebdomadaire_paris",
  "description": "Pattern hebdomadaire pour Paris",
  "version": "1.0",
  "created_at": "2026-01-28T10:30:00Z",
  "microzones": [
    {
      "microzone_id": "mz_001",
      "patterns": {
        "agressions": {
          "benin": {
            "probabilite_base": 0.12,
            "facteurs_modulation": {
              "regime": {
                "stable": 1.0,
                "deterioration": 1.3,
                "crise": 1.8
              },
              "saison": {
                "hiver": 0.9,
                "printemps": 1.2,
                "ete": 1.0,
                "automne": 1.2
              },
              "jour_semaine": {
                "lundi": 1.1,
                "mardi": 1.0,
                "mercredi": 1.0,
                "jeudi": 1.0,
                "vendredi": 1.2,
                "samedi": 1.3,
                "dimanche": 0.8
              }
            }
          },
          "moyen": { ... },
          "grave": { ... }
        },
        "incendies": { ... },
        "accidents": { ... }
      }
    }
  ]
}
```

#### 6.3 Pattern 60j - Exemple
```json
{
  "pattern_type": "60j",
  "pattern_name": "saisonnier_paris",
  "description": "Pattern saisonnier pour Paris (2 mois)",
  "version": "1.0",
  "created_at": "2026-01-28T10:30:00Z",
  "microzones": [
    {
      "microzone_id": "mz_001",
      "patterns": {
        "agressions": {
          "benin": {
            "probabilite_base": 0.15,
            "facteurs_modulation": {
              "regime": {
                "stable": 1.0,
                "deterioration": 1.3,
                "crise": 1.8
              },
              "saison": {
                "hiver": 0.9,
                "printemps": 1.2,
                "ete": 1.0,
                "automne": 1.2
              },
              "jour_mois": {
                "1": 1.0,
                "15": 1.1,
                "30": 0.95
              }
            },
            "influence_intensites": {
              "multiplicateur": 1.1,
              "offset": 0.0
            }
          },
          "moyen": { ... },
          "grave": { ... }
        },
        "incendies": { ... },
        "accidents": { ... }
      }
    }
  ]
}
```

### 7. Validation

#### 7.1 Schéma JSON Schema
Un schéma JSON Schema sera créé pour valider automatiquement les fichiers patterns.

#### 7.2 Vérifications
- Structure JSON valide
- Champs obligatoires présents
- Types de valeurs corrects (float pour probabilités, string pour IDs)
- Plages de valeurs cohérentes (probabilités entre 0.0 et 1.0, multiplicateurs > 0)
- IDs microzones valides (mz_001 à mz_100)

### 8. Utilisation

#### 8.1 Chargement
```python
from src.core.patterns.pattern_loader import load_pattern

# Chargement pattern 4j
pattern_4j = load_pattern("data/patterns/pattern_4j_weekend_paris.json")

# Accès aux données
prob_base = pattern_4j['microzones'][0]['patterns']['agressions']['benin']['probabilite_base']
facteur_regime = pattern_4j['microzones'][0]['patterns']['agressions']['benin']['facteurs_modulation']['regime']['stable']
```

#### 8.2 Application
Les patterns sont utilisés dans :
- **Story 1.3** : Calcul vecteurs statiques
- **Story 2.2.2** : Modulation régimes et intensités
- **Story 2.2.9** : Modulation matrices

### 9. Convention de Nommage

```
data/patterns/
├── pattern_4j_{nom}.json    # Patterns 4 jours
├── pattern_7j_{nom}.json    # Patterns 7 jours
└── pattern_60j_{nom}.json   # Patterns 60 jours
```

Exemples :
- `pattern_4j_weekend_paris.json`
- `pattern_7j_hebdomadaire_paris.json`
- `pattern_60j_saisonnier_paris.json`

---

## Migration et Évolution

### Changements de Version
- **Version 1.0** : Format initial
- **Futures versions** : Ajout de champs, modification structure (avec migration)

### Compatibilité
- Lecture rétroactive : Support des anciennes versions (si nécessaire)
- Migration automatique : Conversion vers version actuelle au chargement

---

**Document de référence** : À utiliser par Story 1.3, Story 1.4, Story 2.2.2, Story 2.2.9, Story 2.2.10.
