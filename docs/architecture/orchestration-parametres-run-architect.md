# Orchestration projet — Paramètres Scénario et Variabilité locale (Architect)

**Destinataire :** Architect  
**Objectif :** Prendre en compte dans la documentation d’architecture l’implémentation des deux arguments **Scénario** (pessimiste / standard / optimiste) et **Variabilité locale** (faible / moyenne / forte) dans la génération des runs.  
**Références :** PRD FR11, Story 2.4.2 (orchestration main), config `config/config.yaml` (section `scenarios`).

---

## 1. Périmètre implémenté

| Argument           | Valeurs UI / CLI                    | Effet dans le run                                                                 |
|-------------------|-------------------------------------|------------------------------------------------------------------------------------|
| **Scénario**      | Pessimiste, Standard, Optimiste     | `facteur_intensite` et `proba_crise` lus depuis `config.scenarios.<scenario>` ; facteur appliqué aux intensités (VectorGenerator). |
| **Variabilité locale** | Faible, Moyenne, Forte        | Float 0.3 / 0.5 / 0.7 ; passé à `MatrixModulator` et à `VectorGenerator.generate_vectors_for_day` (modulation voisins / matrices). |

Les deux arguments sont **obligatoirement** pris en compte pour chaque run (headless et UI) et **enregistrés** dans `trace.json` par run.

---

## 2. Flux implémenté (à documenter dans le data flow)

### 2.1 Entrées

- **UI Streamlit** : `st.selectbox("Scénario", …)` et `st.selectbox("Variabilité", …)` → valeurs transmises au clic LANCEMENT à `SimulationService.run_one(…, scenario_ui=…, variabilite_ui=…)`.
- **CLI headless** : `main.py --scenario Pessimiste|Standard|Optimiste --variabilite Faible|Moyenne|Forte` → transmis à `SimulationService.run_headless(…, scenario_ui=…, variabilite_ui=…)`.

### 2.2 Résolution des paramètres

- **Composant :** `SimulationService` (module `src/services/simulation_service.py`).
- **Fonction :** `_resolve_run_params(config, scenario_ui, variabilite_ui)`.
- **Mapping UI → config :**
  - Scénario : `Pessimiste` → `pessimiste`, `Standard` → `moyen`, `Optimiste` → `optimiste`.
  - Variabilité : `Faible` → `0.3`, `Moyenne` → `0.5`, `Forte` → `0.7`.
- **Sortie :**  
  `(scenario_config, variabilite_locale, scenario_key, variabilite_label)`  
  avec `scenario_config = {"facteur_intensite": float, "proba_crise": float}` lu depuis `config.scenarios.<scenario_key>`.

### 2.3 Propagation vers la génération

- **SimulationService** crée `GenerationService(…, scenario_config=…, variabilite_locale=…)` pour chaque run (headless ou `run_one`).
- **GenerationService** (`src/core/generation/generation_service.py`) :
  - Construit `MatrixModulator(…, variabilite_locale=variabilite_locale)`.
  - Dans `generate_day`, appelle `VectorGenerator.generate_vectors_for_day(…, variabilite_locale=self.variabilite_locale, facteur_intensite=scenario_config["facteur_intensite"])`.
- **VectorGenerator** (`src/core/generation/vector_generator.py`) :
  - Utilise `variabilite_locale` dans les appels au modulateur / facteur voisins.
  - Applique `intensity *= facteur_intensite` après calcul d’intensité (scénario).

### 2.4 Sortie : trace par run

- **Fichier :** `data/intermediate/run_XXX/trace.json` (créé par `SimulationService` en headless et dans `run_one` si `save_trace=True`).
- **Champs ajoutés (à documenter dans l’architecture) :**

| Champ               | Type   | Description |
|---------------------|--------|-------------|
| `scenario`          | string | Clé config : `pessimiste` \| `moyen` \| `optimiste` |
| `variabilite`       | string | Libellé UI : `Faible` \| `Moyenne` \| `Forte` |
| `variabilite_locale` | number | Valeur utilisée en génération : 0.3 \| 0.5 \| 0.7 |
| `seed`              | number | Seed du run (reproductibilité) |

Les champs déjà présents (`run_id`, `days`, `completed`, `final_day`) restent inchangés.

---

## 3. Fichiers à référencer / à mettre à jour (Architect)

| Fichier | Action recommandée |
|---------|--------------------|
| `docs/architecture/dataflow.md` | Ajouter une section (ou sous-section) **« Paramètres de run : Scénario et Variabilité locale »** décrivant le flux : UI/CLI → `_resolve_run_params` → `GenerationService` → `VectorGenerator` / `MatrixModulator` → trace. Option : diagramme de séquence ou schéma de données simplifié. |
| `docs/architecture/index.md`   | Ajouter une entrée pointant vers cette section (ex. « Paramètres de run et trace (scénario, variabilité) — voir dataflow.md »). |
| Schéma / convention de `trace.json` | Si un document décrit le format des traces (ex. `docs/philosophy-patterns-json.md` ou équivalent), y ajouter les champs `scenario`, `variabilite`, `variabilite_locale`, `seed`. |

---

## 4. Fichiers de code concernés (référence)

- `src/services/simulation_service.py` : `_resolve_run_params`, `SCENARIO_UI_TO_CONFIG`, `VARIABILITE_UI_TO_FLOAT` ; `run_headless` / `run_one` (signatures et écriture trace).
- `src/core/generation/generation_service.py` : `__init__(scenario_config, variabilite_locale)` ; `generate_day` (passation à `generate_vectors_for_day`).
- `src/core/generation/vector_generator.py` : `generate_vectors_for_day(…, variabilite_locale, facteur_intensite)` ; application `intensity *= facteur_intensite`.
- `src/core/generation/matrix_modulator.py` : utilisation de `variabilite_locale` (déjà documentée ailleurs si besoin).
- `src/ui/web_app.py` : lecture Scénario / Variabilité et passage à `run_one` au LANCEMENT.
- `main.py` : arguments `--scenario` et `--variabilite` pour le mode headless.
- `config/config.yaml` : section `scenarios` (pessimiste, moyen, optimiste) avec `facteur_intensite`, `proba_crise`, `variabilite_locale` (ce dernier n’est pas utilisé comme source unique ; la variabilité du run vient du choix UI/CLI).

---

## 5. Checklist Architect

- [x] Lire ce fichier et les références PRD FR11 / Story 2.4.2.
- [x] Mettre à jour `docs/architecture/dataflow.md` avec le flux « Paramètres de run (Scénario, Variabilité locale) » (§ 1.1).
- [x] Mettre à jour `docs/architecture/index.md` pour pointer vers cette section.
- [x] Mettre à jour la convention de trace : `docs/naming-conventions.md` § Trace (champs scenario, variabilite, variabilite_locale, seed).
- [x] VectorGenerator : paramètre facteur_intensite et application intensity *= facteur_intensite après calcul d'intensité.
- [ ] Valider la cohérence avec la Strategy Pattern « Scénarios » décrite ailleurs dans l’architecture (scénarios pessimiste/moyen/optimiste).

---

*Document d’orchestration projet — implémentation Scénario et Variabilité locale — à usage Architect.*

## 6. Proposition réorganisation légère (post-Story 2.4.2)

**État actuel (déjà en place) :**  
`_resolve_run_params`, CLI `--scenario` / `--variabilite`, `GenerationService(scenario_config, variabilite_locale)`, `MatrixModulator(variabilite_locale)`, trace.json avec scenario/variabilite/variabilite_locale/seed, UI selectboxes Scénario/Variabilité.

**Correction appliquée (fonctionnalité « oubliée ») :**  
- **VectorGenerator.generate_vectors_for_day** : ajout du paramètre `facteur_intensite: float = 1.0` et application `intensity *= facteur_intensite` après le calcul d'intensité (avant modulation prix m² et effets réduction). Ainsi le scénario modifie bien les intensités en génération.

**Documentation mise à jour :**  
- `dataflow.md` : section 1.1 « Paramètres de run : Scénario et Variabilité locale ».  
- `index.md` : entrée « Paramètres de run et trace » → dataflow § 1.1.  
- `naming-conventions.md` : champs trace scenario, variabilite, variabilite_locale, seed.

**Réorganisation du code :** Aucune. Les fichiers concernés restent ceux listés en § 4 ; le flux UI → run_one(scenario_ui, variabilite_ui) est prévu côté service ; lorsque l'UI branchera le LANCEMENT sur `SimulationService.run_one(…, scenario_ui=scenario, variabilite_ui=variabilite)` (story 2.4.3 ou équivalent), il suffira de transmettre les valeurs des selectboxes.

---

*Document d'orchestration projet — implémentation Scénario et Variabilité locale — à usage Architect.*
