# Scripts de Pré-calculs - Epic 1

Ce dossier contient les scripts de pré-calculs nécessaires avant de lancer la simulation.

## Structure

```
scripts/
├── run_precompute.py          # Script unique d'orchestration
├── precompute_distances.py    # Story 1.2 (à implémenter)
├── precompute_microzones.py   # Story 1.2 (à implémenter)
└── precompute_vectors_static.py  # Story 1.3 (à implémenter)
```

## Installation

1. Activer l'environnement Conda :
```bash
conda activate paris_risques
```

2. Installer les dépendances :
```bash
pip install -r requirements-precompute.txt
```

## Utilisation

### Lancement complet

Lancer tous les pré-calculs :
```bash
python scripts/run_precompute.py
```

### Lancement partiel

#### Sauter des blocs

Sauter le calcul des distances :
```bash
python scripts/run_precompute.py --skip-distances
```

Sauter les vecteurs statiques :
```bash
python scripts/run_precompute.py --skip-vectors
```

Sauter plusieurs blocs :
```bash
python scripts/run_precompute.py --skip-distances --skip-microzones
```

#### Lancer uniquement un bloc

Lancer uniquement les distances :
```bash
python scripts/run_precompute.py --only-distances
```

Lancer uniquement les vecteurs statiques :
```bash
python scripts/run_precompute.py --only-vectors
```

### Configuration

Le script utilise le fichier `config/config.yaml` par défaut. Pour utiliser un autre fichier :
```bash
python scripts/run_precompute.py --config config/config-custom.yaml
```

## Arguments disponibles

### Arguments --skip-*

- `--skip-distances` : Sauter le pré-calcul des distances (Story 1.2)
- `--skip-microzones` : Sauter le pré-calcul des microzones (Story 1.2)
- `--skip-vectors` : Sauter le pré-calcul des vecteurs statiques (Story 1.3)
- `--skip-prix-m2` : Sauter le pré-calcul des prix m² (Story 1.3)
- `--skip-congestion` : Sauter le pré-calcul de la congestion statique (Story 1.3)

### Arguments --only-*

- `--only-distances` : Lancer uniquement le pré-calcul des distances
- `--only-microzones` : Lancer uniquement le pré-calcul des microzones
- `--only-vectors` : Lancer uniquement le pré-calcul des vecteurs statiques
- `--only-prix-m2` : Lancer uniquement le pré-calcul des prix m²
- `--only-congestion` : Lancer uniquement le pré-calcul de la congestion statique

**Note:** Les arguments `--only-*` sont mutuellement exclusifs (un seul à la fois).

### Autres arguments

- `--config PATH` : Chemin vers le fichier de configuration (défaut: `config/config.yaml`)

## Configuration dans config.yaml

Vous pouvez également activer/désactiver des blocs dans `config/config.yaml` :

```yaml
precompute:
  enabled:
    distances: true
    microzones: true
    vectors_static: true
    prix_m2: true
    congestion_static: true
```

**Priorité:** Les arguments CLI (`--skip-*`, `--only-*`) ont la priorité sur la configuration YAML.

## Sorties

Tous les fichiers de sortie sont sauvegardés dans `data/source_data/` :

- `distances_caserne_microzone.pkl` (Story 1.2)
- `distances_microzone_hopital.pkl` (Story 1.2)
- `microzones.pkl` ou `microzones.geojson` (Story 1.2)
- `limites_microzone_arrondissement.pkl` (Story 1.2)
- `vecteurs_statiques.pkl` (Story 1.3)
- `prix_m2.pkl` (Story 1.3)
- `congestion_statique.pkl` (Story 1.3)

## Ordre d'exécution

### Après régénération des microzones

Si vous avez régénéré `microzones.pkl` (ex. `--only-distances`), exécuter **dans cet ordre** :

1. **Distances** (crée `microzones.pkl`, limites, distances caserne/hôpital)  
   `python scripts/run_precompute.py --only-distances`

2. **Quartiers sur les microzones** (ajoute la colonne `quartiers_administratifs`)  
   `python scripts/add_quartiers_to_microzones.py`

3. **Vecteurs statiques** (vecteurs, prix m², chômage, délinquance, congestion statique — lit `microzones.pkl`)  
   `python scripts/run_precompute.py --only-vectors`

Sans étape 2, les scripts `update_delinquance_from_ssmsi.py` et `update_prix_m2_from_quartiers.py` échoueront (colonne quartiers manquante).

### Ordre général

- **Story 1.2** (distances) crée les microzones ; **Story 1.3** (vecteurs statiques) les utilise.
- Les vecteurs statiques **dépendent** de `microzones.pkl` (et optionnellement de `add_quartiers_to_microzones` pour les mises à jour délinquance/prix m²).

## Tests

Pour exécuter les tests :
```bash
pytest tests/scripts/
```

## Notes

- Les modules individuels (`precompute_distances.py`, etc.) seront implémentés dans les stories 1.2 et 1.3
- Le script `run_precompute.py` orchestre tous les pré-calculs et peut être utilisé dès maintenant
- Format des pickles : Laissé au choix de l'implémentation (voir stories 1.2 et 1.3)
