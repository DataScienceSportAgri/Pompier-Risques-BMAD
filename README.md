# Système de Simulation et Prédiction des Risques - Pompiers de Paris

Système de simulation et prédiction des problématiques d'urgence (incendies, accidents, agressions) auxquels les pompiers de Paris pourraient faire face.

## Installation

### Prérequis

- Python 3.12
- Conda (recommandé)

### Environnement Conda

```bash
# Créer l'environnement conda
conda create -n paris_risques python=3.12
conda activate paris_risques

# Installer les dépendances
pip install -r requirements.txt
```

### Installation des dépendances

```bash
pip install -r requirements.txt
```

## Structure du Projet

```
src/
├── core/
│   ├── data/          # Classes de base (Vector, constantes)
│   ├── events/        # Hiérarchie d'événements (Event, EventGrave, PositiveEvent)
│   ├── state/         # État de simulation (SimulationState)
│   ├── patterns/      # Détection et gestion de patterns
│   ├── probability/   # Calculs de probabilités
│   └── evolution/     # Évolution des variables d'état
├── services/          # Services applicatifs
├── adapters/          # Adaptateurs (UI, données externes)
data/
├── source_data/       # Données sources (pickle)
├── intermediate/      # Données intermédiaires
├── patterns/          # Patterns de référence
└── models/            # Modèles ML entraînés
tests/                 # Tests unitaires et d'intégration
scripts/               # Scripts de pré-calcul et utilitaires
config/                # Configuration (config.yaml)
```

## Démarrage

### Pré-calculs (Epic 1)

Les données pré-calculées doivent être générées en premier :

```bash
# Exécuter les scripts de pré-calcul
python scripts/precompute_matrices_correlation.py
# ... autres scripts de pré-calcul
```

### Simulation (Epic 2)

```bash
# Lancer la simulation
python scripts/run_simulation.py
```

### Interface Utilisateur (Streamlit)

```bash
streamlit run src/ui/app.py
```

## Classes Principales

### Vector

Représente un vecteur d'incidents par niveau de gravité : `[grave, moyen, bénin]`

```python
from src.core.data.vector import Vector

# Créer un vecteur
vecteur = Vector(grave=1, moyen=2, benin=5)
print(vecteur)  # [1, 2, 5]

# Depuis une liste
vecteur = Vector.from_list([1, 2, 5])
```

### Events

Hiérarchie d'événements :

- **Event** : Classe de base abstraite
- **EventGrave** : Événements graves (incidents)
  - `AccidentGrave`
  - `IncendieGrave`
  - `AgressionGrave`
- **PositiveEvent** : Événements positifs (améliorations)
  - `FinTravaux`
  - `NouvelleCaserne`
  - `AmeliorationMateriel`

```python
from src.core.events import AccidentGrave, FinTravaux

# Créer un accident grave
accident = AccidentGrave(
    event_id="ACC_001",
    jour=5,
    arrondissement=11,
    duration=4,
    casualties_base=2,
    characteristics={"traffic_slowdown": 0.7}
)

# Créer un événement positif
fin_travaux = FinTravaux(
    event_id="FT_001",
    jour=10,
    arrondissement=11,
    impact_reduction=0.1
)
```

## Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=src tests/

# Tests spécifiques
pytest tests/core/data/test_vector.py
```

## Documentation

- Architecture : `docs/architecture.md`
- PRD : `docs/prd.md`
- Stories : `story/`

## Auteur

Développé dans le cadre du projet BMAD pour la simulation des risques pompiers de Paris.
