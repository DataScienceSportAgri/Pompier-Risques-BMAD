# Pompier-Risques-BMAD Brownfield Enhancement PRD

**Version:** v4  
**Date:** 27 Janvier 2026  
**Statut:** Validé

---

# Intro Project Analysis and Context

## Existing Project Overview

### Analysis Source
IDE-based fresh analysis

### Current Project State

Le projet actuel est une **application de visualisation statique** des risques par arrondissement parisien. 

**Fonctionnalités actuelles:**
- Interface Tkinter simple avec contrôles de sélection (type de risque, seuil d'alerte)
- Génération de cartes Folium interactives affichées dans le navigateur
- Visualisation de 3 types de risques: agressions, incendies, accidents de voiture
- Données **hardcodées** dans le code (pas de génération dynamique)
- Statistiques affichées (min, max, moyenne) pour chaque type de risque
- Choroplèthe avec marqueurs pour zones critiques (dépassant le seuil)

**Limitations actuelles:**
- Données statiques et non réalistes
- Pas de simulation temporelle
- Pas de prédiction ou modélisation
- Pas de Machine Learning
- Interface Tkinter (non adaptée pour production web)
- Pas de gestion d'événements dynamiques
- Pas de calculs complexes (Golden Hour, stress pompiers, etc.)

## Available Documentation Analysis

### Available Documentation

- ✅ **Brainstorming Sessions Results**: `docs/brain-storming-session-results.md` - Spécifications techniques complètes (626 lignes)
- ✅ **Contexte Sessions 1-3**: `Contexte-Sessions-1-a-3.md`
- ✅ **Sessions détaillées**: `brainstorming/Session-5-*.md`, `Session-4-*.md`
- ✅ **PDFs de référence**: Modèles mathématiques, schémas projet, échanges
- ❌ **Tech Stack Documentation**: Non documenté (à créer)
- ❌ **Source Tree/Architecture**: Non documenté (à créer)
- ❌ **Coding Standards**: Non documenté
- ❌ **API Documentation**: N/A (pas d'API actuellement)
- ❌ **UX/UI Guidelines**: Non documenté
- ❌ **Technical Debt Documentation**: Non documenté

**Note:** Le document `brain-storming-session-results.md` contient des spécifications techniques très détaillées prêtes pour implémentation, mais il manque la documentation produit (PRD) et architecture.

## Enhancement Scope Definition

### Enhancement Type

- ✅ **New Feature Addition**: Système complet de simulation/prédiction
- ✅ **Major Feature Modification**: Remplacement interface Tkinter par Streamlit
- ✅ **Integration with New Systems**: Intégration Machine Learning (RandomForest + SHAP)
- ✅ **Performance/Scalability Improvements**: Architecture modulaire pour vraies données BSPP (Phase 2)
- ✅ **Technology Stack Upgrade**: Ajout de bibliothèques ML (scikit-learn, SHAP), Streamlit

### Enhancement Description

Transformation de l'application de visualisation statique en **système complet de simulation et prédiction des risques** pour les pompiers de Paris (BSPP). Le système générera des données réalistes jour-à-jour, calculera des features hebdomadaires, entraînera des modèles ML pour prédire les risques, et fournira une interface web interactive (Streamlit) pour visualiser et analyser les résultats.

### Impact Assessment

- ✅ **Major Impact (architectural changes required)**: 
  - Refonte complète de l'architecture (5 niveaux de données)
  - Remplacement Tkinter → Streamlit
  - Ajout de modules ML, Golden Hour, événements modulables
  - Nouvelle structure de dossiers modulaire

## Goals and Background Context

### Goals

- Générer des données réalistes de simulation (remplaçables par vraies données BSPP en Phase 2)
- Implémenter un modèle Zero-Inflated Poisson avec régimes cachés pour prédiction J+1
- Calculer 18 features hebdomadaires par arrondissement
- Entraîner des modèles ML (régression + classification) avec interprétabilité (SHAP)
- Fournir une interface web Streamlit interactive pour visualisation et analyse
- Détecter des patterns dangereux: "Avec ces 4 semaines qui se sont suivies, selon les alentours, on arrive à quelque chose de dangereux"
- Architecture extensible avec plugins/modulateurs sans toucher le cœur

### Background Context

Le projet actuel est un prototype de visualisation avec des données statiques. Les sessions de brainstorming (4 et 5) ont défini un système complet basé sur un modèle mathématique scientifique (Zero-Inflated Poisson + régimes cachés) pour prédire les incidents (accidents, incendies, agressions) à J+1.

**Problème résolu:** Actuellement, il n'y a pas de capacité de prédiction ou de simulation. Le système permettra aux décideurs de la BSPP d'anticiper les risques et de prendre des décisions éclairées basées sur des modèles interprétables.

**Valeur ajoutée:** 
- Simulation réaliste avec données générées (MVP)
- Prédiction basée sur patterns temporels (7 jours court-terme, 60 jours long-terme)
- Explicabilité via SHAP values (critique pour adoption par les pompiers)
- Architecture modulaire permettant remplacement données générées → vraies données BSPP

## Change Log

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|--------|
| Initial PRD | 27 Jan 2026 | v4 | Création PRD brownfield enhancement | PM |
| Peaufinement UI | 27 Jan 2026 | v4 | Réponses session objectifs UI : bloc ML 3×2, layout 2/3 colonnes, bandeau bas, Stop/Reprendre, paramètres verrouillés, prédiction semaine 5+, scripts pré-calc, entraînement après 50 runs. Nouvelles FR21–FR24, mise à jour FR10–FR12, FR18–FR19. Section « Spécifications UI détaillées » ajoutée. | PM |
| Peaufinement UI (2) | 27 Jan 2026 | v4 | Liste chrono + gris quand passé + emojis (flamme, couteau, voiture, rose verte). Rectangles taille fixe, pastel, 3 totaux, pas de clic détail MVP. Carte 100 microzones, délimitation. Inter, pastel, français. Défaut 365 j, auto-save pickle, run complet enregistré. Prédiction 1 run ; **modèles conservés**. Graphiques détail Phase 2, SHAP MVP. FR25–FR28, mise à jour FR10–FR11, FR18, FR20–FR22. §9–11 Spécifications UI. | PM |
| Contraintes techniques | 27 Jan 2026 | v4 | Python 3.12, Conda (paris_risques). Versions fixées, main.py supprimable. Scripts pré-calcul (scripts/), source_data/, structure pickle par run (génération, events, ML, labels). Config YAML, chemins relatifs. Traçabilité JSON par run (détails, patterns). Adjacents en dur, pas de régression linéaire, parallélisation ok, 0,33 s indicatif, multi-OS. Section Recommandations (config, API, 100 microzones, Folium, pytest, coverage). | PM |
| Structure Epic | 27 Jan 2026 | v4 | Deux epics : **Epic 1 Pré-calculs** (1.1–1.3), **Epic 2 Simulation** (blocs 2.1–2.5). Numérotation par blocs. Rollback : revert + pytest. Préalable : clarifier modèle J+1 dans le doc pour tests explicites. Story 2.2.1 vecteurs : sous-étapes vérifiables. IV Tkinter supprimée. Story 2.4.2 Orchestration (main.py, runnable sans UI). 2.4.3 minimal UI Lancer/Stop. 2.4.6 Phase 2 graphiques détaillés. Arrondissements adjacents en dur (2.3.1). | PM |
| Détails Epic & Stories | 27 Jan 2026 | v4 | Epic 1 : **script unique** pré-calculs, **même config** que l’app ; casernes/hôpitaux **fichier internet** ; pickles format implémentation ; vecteurs statiques **sans** distances ; prix m² **internet ou généré**. 2.1.1 : Incident vs PositiveEvent, sous-classes (Fin travaux, etc.). **Ordre 2.2** : 2.2.9 Matrices et 2.2.10 Vecteurs statiques **avant** Golden Hour. Patterns 4j/7j lus → génération patterns futurs, 60j (20+20+20) ; congestion (randomness, accidents ↑, feux ↓), chargement trajets `source_data` explicite. Labels **mensuels** (4 sem), >2 ou >3 morts/mois ; **règle alertes 1–500 morts / 800 j agrégés**. Events : positifs **début de journée**, graves **après** vecteurs ; réduction intensités. 50 runs : **1 affiché** + **49 en calcul seul** ; algos RF, Ridge, LogReg, XGBoost ; **SHAP checkbox**. 2.4.1 avant 2.4.2 ; carte **100 microzones** ; **bouton [Sauvegarder]** export ; **état d’urgence** à l’arrêt. Phase 2 graphiques : morts, blessés, incidence, sommes vecteurs. **DoD** pour toutes stories ; **docs formules + architecture** ; pas d’estimation. | PM |
| Alertes cohérence (final) | 27 Jan 2026 | v4 | **Règle définitive** (par arrondissement, sur **800 jours agrégés**) : **au moins 1 mort**, **moins de 500 morts**. Si 0 mort ou ≥ 500 morts → alerte (message uniquement). Mise à jour NFR5, 2.2.4, 2.5.1, Mitigation. | PM |
| Finalisation | 27 Jan 2026 | v4 | Features ML : 1 central (18, dernière sem.) + 4 voisins (4×18, dernière sem.) = 90. SHAP ref 2.4.4 ; 2.4.4 entraînement (1+49) vs prédiction (1 seul). NFR5 parenthèse fermée. Pas de régression linéaire (Ridge, LogReg, XGBoost). Liste de rectangles arrondissements ; packaging → **propagation directionnelle**. Pré-calculs : **run_precompute.py** orchestre les scripts. **formules.md** (formules, matrices) ; **modele-j1-et-generation.md** (complexité, randomness, patterns). Change log 3×2, modèles conservés, règle 1–500 / 800 j partout. **Statut → Validé**. | PM |

---

# Requirements

## Functional

FR1: Le système doit générer des vecteurs journaliers (3 vecteurs × 3 valeurs: bénin, moyen, grave) par microzone selon le modèle Zero-Inflated Poisson avec régimes cachés (Stable, Détérioration, Crise).

FR2: Le système doit calculer les proportions alcool/nuit par type d'incident via Monte-Carlo journalier, puis agrégation hebdomadaire.

FR3: Le système doit implémenter le calcul Golden Hour (temps trajet caserne→microzone→hôpital) avec prise en compte congestion, stress pompiers, et effet sur casualties si > 60 min.

FR4: Le système doit calculer les morts et blessés graves hebdomadaires par arrondissement. **Morts** : 30 % aléatoire, 70 % Golden Hour (la personne peut mourir malgré le respect de la Golden Hour). **Blessés graves** : 60 % aléatoire, 40 % Golden Hour (la gravité peut être inhérente à l’accident, non seulement à la réponse des pompiers).

FR5: Le système doit calculer 18 features hebdomadaires par arrondissement: 6 sommes incidents (moyen+grave et bénin par type), 6 proportions (alcool et nuit par type), 3 morts hebdo, 3 blessés graves hebdo.

FR6: Le système doit générer des labels (score ou classes) **mensuels** à partir de morts + blessés graves. **Score** : `morts + 0.5 × blessés_graves` (les morts par arrondissement et par mois sont rares à Paris ; les blessés graves, pondérés par 0.5, enrichissent la prédiction). **Seuils** (données Paris) : 1, 2 ou 3 morts/mois selon la zone, ou 4 à 6 blessés graves ; les 18 features servent à prédire ces labels.

FR7: Le système doit entraîner des modèles ML (2 régression, 2 classification) sur **90 features** par arrondissement central : **1 central** (18 features, **dernière semaine**) + **4 voisins** (chacun 18 features, **dernière semaine**) = 18 + 4×18 = **90 features**.

FR8: Le système doit **implémenter** le calcul des SHAP values (code présent en MVP) ; un **bouton (checkbox)** dans l’UI permet de lancer ou non le calcul. Interprétabilité des modèles ML via SHAP.

FR9: Le système doit sauvegarder les modèles avec métadonnées (nom, numéro entraînement, paramètres génération) dans `models/regression/` ou `models/classification/`.

FR10: Le système doit fournir une interface web Streamlit sur **une seule page** : carte Paris (centre, **100 microzones** avec délimitation visible), liste événements/incidents (gauche), colonnes droite selon mode (entraînement: 2 colonnes — rectangles 20 arrondissements; prédiction: 3 colonnes — Prédictions, État arrondissement, Prédiction arrondissement), bandeaux haut/bas.

FR11: Le système doit permettre la sélection de paramètres : **haut gauche** (expander) scénario (pessimiste/moyen/optimiste), variabilité locale (faible/moyen/important) ; **bandeau bas gauche** nombre de jours (**défaut 365**). Lancer possible avec **tous paramètres par défaut**. **Tous paramètres verrouillés** pendant la simulation jusqu'à Stop ; **à l'arrêt, paramètres perdus** (reset).

FR12: Le système doit afficher en temps réel **bandeau bas** : Jours simulés/Total (jour par jour, **avec %**), Run X/50, progression entraînement ML (après 50 runs). Vitesse 1 jour = 0.33s.

FR13: Le système doit générer des événements graves modulables (Accident, Incendie, Agression) avec caractéristiques probabilistes (traffic slowdown, cancel sports, increase bad vectors, kill pompier).

FR14: Le système doit gérer des événements positifs (fin travaux, nouvelle caserne, amélioration matériel) modifiant les matrices de transition en mieux.

FR15: Le système doit détecter les patterns court-terme (7 jours) et long-terme (60 jours) selon les formules définies dans le modèle scientifique.

FR16: Le système doit appliquer les trois matrices de modulation (gravité microzone, types croisés, voisins) dans le calcul des intensités calibrées.

FR17: Le système doit appliquer la règle prix m² (division probabilité agression, diminution probabilités régimes).

FR18: Le système doit permettre **Stop** (arrêt du calcul), affichage du **dernier état de la carte**, **bouton [Reprendre]** pour continuer à partir de l'état sauvegardé. **Sauvegarde automatique** en pickle (dossier dédié, ex. « état d'urgence » / safe state) ; **un run mené à son terme** est enregistré.

FR19: Le système doit fournir **haut droite** un bloc ML (tableau logique **3×2** : 3 colonnes × 2 lignes) : **ligne 1** — radio « Train a model » | « Use a prediction model », radio Régression | Classification, si Use prediction sélection fichier modèle (`models/classification/` ou `models/regression/`) ; **ligne 2** — si Train : choix 2 algorithmes (ex. Random Forest + autre, **Ridge** + autre pour régression ; **LogReg**, **XGBoost** pour classification ; **pas de régression linéaire**), saisie nom modèle après entraînement avec **génération automatique** de noms. Déverrouillage automatique des options selon le choix.

FR20: Le système doit afficher les codes couleur par type/gravité: Feu (Jaune/Orange/Rouge), Accident (Beige/Marron), Agression (Gris), avec priorité affichage: Grave → Feu > Agression > Accident. **Charte visuelle MVP** : police **Inter**, thème **clair**, couleurs **pastel** (claires, pas trop sombres). **Emojis** : flamme (incendie), couteau (agression), voiture (accident, **taille variable** selon gravité), rose verte (événement positif). **Langue** : **français uniquement**.

FR21: **Graphiques détaillés** (clic sur arrondissement → évolution temporelle) : **Phase 2** uniquement ; pas dans le MVP.

FR22: **Mode prédiction** : **un seul run** ; à la fin, **retour à l’état initial** (Paris sans événements, jour 0, défaut jours ex. 365). **Modèle chargé conservé** (pas de reset) ; on peut relancer un run avec le même modèle. À partir de la **semaine 5**, afficher par arrondissement état prédit (n+1) ; **chaque fin de semaine** (après 5e) **+ / −** (régression) ou **match / mismatch** (classification). Pendant une **fraction de seconde**, afficher la **réalité** puis revenir à la prédiction.

FR23: Le système doit **entraîner** les modèles ML **une fois les 50 runs terminés** (pas d'entraînement incrémental pendant les runs).

FR24: Vecteurs statiques, distances et données pré-calculées sont produits par **scripts externes** (l'utilisateur les lance) ; résultats en **pickles** chargés par l'app. Aucun calcul lourd côté UI avant le premier jour.

FR25: **Liste événements (gauche)** : ordre **chronologique** uniquement ; apparition **au fur et à mesure** ; événement **passé** → **gris** ; **pas de filtre** en MVP. Emojis (flamme, couteau, voiture taille variable, rose verte) comme en FR20.

FR26: **Rectangles arrondissements (droite)** : **taille fixe** ; couleurs **pastel** (ex. orange clair feu, vert clair événement) ; **emojis** identiques ; **3 totaux** (agressions, incendies, accidents) **mis à jour en continu**. Pas de mini-courbe ; **clic → fenêtre détails** = Phase 2 uniquement (MVP = pas de fenêtre au clic).

FR27: **Carte** : **100 microzones** avec **délimitation visible** ; événements positifs (**rose verte**), incidents (emojis flamme, couteau, voiture) sur la carte.

FR28: **SHAP** : **implémenté en MVP** (code de calcul disponible) ; **bouton/checkbox** pour lancer le calcul ou non. Interprétabilité des modèles ML.

## Non Functional

NFR1: Le système doit maintenir les performances de chargement des données géospatiales existantes (GeoPandas) sans dégradation.

NFR2: Le système doit générer les données journalières en ≤ 0.33s par jour pour respecter la vitesse d'affichage requise.

NFR3: Le système doit supporter au minimum 50 runs de simulation sans dépassement mémoire significatif.

NFR4: Le système doit sauvegarder les données intermédiaires en pickle pour permettre reprise après interruption.

NFR5: Le système doit valider la cohérence des données (par arrondissement, sur **800 jours agrégés sur plusieurs runs**) : au moins 1 mort, moins de 500 morts ; si 0 mort ou ≥ 500 morts → **alerte (message uniquement, pas d’action automatique)**.

NFR6: Le système doit utiliser des nombres entiers (ints) ou floats raisonnables pour éviter problèmes de scalabilité.

NFR7: Le système doit être modulaire pour permettre remplacement données générées → vraies données BSPP sans refonte majeure.

NFR8: Le système doit maintenir la compatibilité avec les formats de données géospatiales existants (GeoJSON, GeoPandas).

NFR9: Le système doit fournir des métriques ML: MAE, RMSE, R² (régression), Accuracy, Precision, Recall, F1 (classification).

NFR10: Le système doit permettre comparaison entre modèles enregistrés avec paramètres différents.

NFR11: Le système doit gérer les erreurs gracieusement avec messages clairs pour l'utilisateur.

NFR12: Le système doit être testable avec tests unitaires pour vérifier cohérence données et validation patterns.

## Compatibility Requirements

CR1: **Compatibilité données géospatiales**: Le système doit continuer à utiliser GeoPandas et les mêmes formats GeoJSON pour les arrondissements parisiens. Les données géographiques existantes doivent rester compatibles.

CR2: **Point d’entrée** : Un **main.py** existe (orchestration, config, simulation, Streamlit), distinct de l’ancien `main.py` Tkinter. L’ancien peut être **entièrement remplacé** ; pas de préservation de sa structure.

CR3: **Compatibilité bibliothèques Python**: Les bibliothèques existantes (GeoPandas, Pandas, Folium) doivent continuer à fonctionner. Les nouvelles dépendances (Streamlit, scikit-learn, SHAP) ne doivent pas créer de conflits.

CR4: **Compatibilité export cartes**: Si des fonctionnalités d'export de cartes existent ou sont ajoutées, elles doivent rester compatibles avec les formats HTML/Folium existants.

---

# User Interface Enhancement Goals

## Integration with Existing UI

L'interface actuelle Tkinter sera **remplacée** par Streamlit (décision figée Session 4). Cependant, les concepts de visualisation (carte interactive, sélection de risques, statistiques) seront conservés et améliorés dans Streamlit.

**Intégration:**
- Les cartes Folium existantes peuvent être intégrées dans Streamlit via `st.components.v1.html()` ou `folium_static()`
- Les concepts de sélection (type risque, seuil) seront transformés en widgets Streamlit (selectbox, slider)
- Les statistiques seront affichées dans des colonnes Streamlit avec graphiques interactifs

## Modified/New Screens and Views

**Écran unique** – tout sur la même page, autour de la carte Paris. Pas d'écrans séparés ni d'ordre imposé.

- **Colonne gauche:** Liste événements/incidents (toujours visible).
- **Centre:** Carte Paris.
- **Colonne(s) droite:** Selon le mode (entraînement vs prédiction), voir *Spécifications UI détaillées*.
- **Graphiques détaillés:** Clic sur un arrondissement → fenêtre détails (évolution temporelle). **Phase 2** uniquement ; pas dans le MVP.

## UI Consistency Requirements

- **Codes couleur cohérents**: Feu (Jaune/Orange/Rouge), Accident (Beige/Marron), Agression (Gris) - figés Session 4
- **Priorité affichage**: Plus grave → Feu > Agression > Accident
- **Vitesse affichage**: 1 jour = 0.33s (figé Session 4)
- **Layout**: Carte centre, colonnes gauche/droite, bandeaux haut/bas (figé Session 4)
- **Widgets Streamlit**: Utilisation standard (selectbox, slider, button, checkbox, radio) pour cohérence UX
- **Charte visuelle MVP**: Police **Inter**, thème **clair** ; couleurs **pastel**, plutôt claires, pas trop sombres
- **Langue**: **Français uniquement**. **Contexte cible** : app **démo / entretien** pour recruteurs (data scientists).

---

## Spécifications UI détaillées (session de peaufinement)

_Source: réponses session de peaufinement requirements. À utiliser pour implémentation._

### 1. Bloc ML (haut droite) – tableau 3 colonnes × 2 lignes

Layout sans bordures visibles (grille logique uniquement). Déverrouillage automatique des options selon le choix (Train vs Use prediction). Les **18 features** servent à prédire les **labels** ; calcul des labels → prédiction puis **réalité** (comparaison).

**Ligne 1 (première ligne) :**
| Colonne 1 | Colonne 2 | Colonne 3 |
|-----------|-----------|-----------|
| **Train a model** ou **Use a prediction model** (boutons radio) | **Régression** ou **Classification** (boutons radio) | Si *Use prediction* : sélection du fichier modèle enregistré (`models/classification/` ou `models/regression/`) |

**Ligne 2 (seconde ligne) :**
- Si **Train a model** : noms des **2 algorithmes** sélectionnables (ex. Random Forest, **Ridge** pour régression ; **LogReg**, **XGBoost** pour classification ; **pas de régression linéaire**). Saisie du **nom du modèle** après entraînement, avec **génération automatique** de noms.
- Si **Use a prediction model** : lié à la sélection du modèle (fichier) en ligne 1.

### 2. Haut gauche – scénario et variabilité

- **Expander** : type de scénario (pessimiste / moyen / optimiste), variabilité locale (faible / moyen / important), etc., pour alléger l'interface.
- Pas d'ordre imposé entre ces contrôles.

### 3. Layout global (colonne gauche, centre, colonnes droite)

- **Gauche:** Liste **événements / incidents** (toujours visible). Voir § 9 (liste) et § 10 (rectangles).
- **Centre:** Carte Paris avec **100 microzones** (découpage et délimitation visibles sur la carte). Voir § 11 (carte).
- **Droite:** **Liste de rectangles** — un rectangle par arrondissement, chaque nom dans un rectangle.  
  - **Mode entraînement:** **2 colonnes** – (1) **rectangles des 20 arrondissements** (taille fixe, couleurs pastel + emojis, 3 totaux : agressions / incendies / accidents, mis à jour en continu) ; (2) même symbologie (couleurs, emojis). Clic sur rectangle → fenêtre détails (évolution temporelle) : **Phase 2** ; MVP = pas de fenêtre détaillée au clic.  
  - **Mode prédiction:** **3 colonnes** – (1) **Prédictions** ; (2) **État de l'arrondissement** (dernière semaine connue) ; (3) **Prédiction de l'arrondissement** (semaine n+1). Rien avant la semaine 5 ; à partir de la 5e, état prédit. **Un seul run** ; à la fin, **retour à l’état initial** (Paris sans événements, jour 0, défaut 365 j). **Modèle chargé conservé** (pas de reset).

### 4. Bandeau bas – une seule ligne

- **Gauche:** Sélection du **nombre de jours** de simulation. **Valeur par défaut : 365.**
- **Centre / droite:**  
  - **Jours simulés / Total** (jour par jour, **avec %**).  
  - **Run X / 50** (suffisant).  
  - Progression de l'**entraînement ML** (une fois les 50 runs terminés).
- **Boutons:** [Lancer], [Stop], [Reprendre].

### 5. Lancer, paramètres, Stop, Reprendre

- **Lancer:** possible avec **tous les paramètres par défaut** (pré-remplis).
- **Pendant la simulation:** **tous les paramètres sont verrouillés** jusqu'à [Stop].
- **À l'arrêt (Stop):** **tous les paramètres sont perdus** (reset). Affichage du **dernier état de la carte**. **Bouton [Reprendre]** pour continuer la simulation (reprise à partir de l'état sauvegardé).
- **Stop** = arrêt du calcul uniquement ; pas de redémarrage automatique.

### 6. Mode prédiction – dynamique à partir de la semaine 5

- À partir de la **semaine 5** : les arrondissements apparaissent avec **état prédit** (semaine n+1).
- **Chaque fin de semaine** (après la 5e) :  
  - **Régression:** **+** ou **−** selon l'écart entre score prédit et score réel.  
  - **Classification:** **match** ou **mismatch** selon accord prédiction / réalité.
- Affichage **dynamique** chaque week-end. Pendant une **fraction de seconde**, la **réalité** (résultat observé) s'affiche à la place de la prédiction, puis retour à la prédiction.
- L'utilisateur voit : **état de l'arrondissement** sur la dernière semaine connue, et **prédiction** pour la semaine n+1. À la génération, calcul immédiat match/mismatch ou +/−.

### 7. Données pré-calculées, sauvegarde et entraînement

- **Vecteurs statiques, distances, etc.** : **pré-calculés** par des **scripts** (l'utilisateur les lance). Résultats stockés en **pickles** ; l'app les charge. Aucun calcul lourd côté UI avant le premier jour.
- **Entraînement ML:** déclenché **une fois les 50 runs terminés** (pas d'entraînement incrémental pendant les runs).
- **Sauvegarde état:** **Sauvegarde automatique** en pickle ; état stocké dans un **dossier dédié** (ex. « état d’urgence » / « safe state »), **un fichier par état** sauvegardé. Quand un **run est mené à son terme**, l’état est enregistré.

### 8. Mode prédiction, graphiques détaillés, SHAP

- **Mode prédiction:** **Un seul run**. À la fin du run, **retour à l’état initial** : Paris sans événements, **jour 0**, nombre de jours par défaut. **Modèle chargé conservé** (pas de reset) ; on peut relancer un run avec le même modèle.
- **Graphiques détaillés** (clic sur un arrondissement → évolution temporelle) : **Phase 2** uniquement. Souhaitable après SHAP ; pas dans le MVP.
- **SHAP:** **Implémenté en MVP** (code de calcul) ; **bouton/checkbox** pour lancer le calcul ou non.

### 9. Liste événements / incidents (colonne gauche) – MVP

- **Ordre:** **Chronologique** uniquement. Les événements apparaissent **au fur et à mesure** de leur création ; dès qu’un nouvel événement est créé, il s’affiche en bas de liste.
- **Filtres:** **Aucun** pour le MVP.
- **Passé:** Une fois l’événement **passé** (temps écoulé), il devient **gris** ; l’événement suivant apparaît.
- **Emojis** (importants) :  
  - Incendie : **flamme**  
  - Agression : **couteau(x)**  
  - Accident : **voiture(s)** – **taille variable** selon gravité de l’accident  
  - Événement positif : **rose verte** (sur la carte et dans les rectangles).

### 10. Rectangles arrondissements (colonne droite)

- **Taille:** **Fixe** (pas de proportionnalité).
- **Couleurs:** **Pastel**, plutôt claires – ex. **orange clair** pour feu, **vert clair** pour événement positif. Cohérent avec la charte visuelle.
- **Emojis:** Mêmes symboles que dans la liste (flamme, couteau, voiture, rose verte) pour identifier type d’incident vs événement.
- **Contenu (MVP):** **Trois totaux uniquement** – **agressions**, **incendies**, **accidents** – qui se **mettent à jour en continu** (augmentation au fil de la simulation). **Pas** de mini-courbe dans le rectangle.
- **Clic:** Ouvre une **fenêtre** avec détails (évolution temporelle) → **Phase 2** ; MVP = pas de fenêtre au clic.

### 11. Carte Paris et microzones

- **Découpage:** Paris en **100 microzones**. Les **limites** des microzones doivent être **visibles sur la carte** (délimitation).
- **Événements sur la carte:** Événements positifs avec **rose verte** ; incidents avec les mêmes emojis (flamme, couteau, voiture) selon le type.

---

# Technical Constraints and Integration Requirements

_Source: réponses session contraintes techniques + recommandations PM._

## Existing Technology Stack

**Languages**: Python **3.12** (cible). Environnement **Conda** (voir `.cursor-env` : `paris_risques`).

**Frameworks**: 
- Tkinter : **supprimable** ; `main.py` actuel était une première étape, pas à conserver.
- GeoPandas, Pandas, Folium (à conserver). Alternatives carto possibles → *Recommandations*.

**Database**: Aucune. Données en mémoire, sauvegarde pickle.

**Infrastructure**: Application locale ; **pas de déploiement web** pour le MVP.

**Dépendances**: `geopandas`, `pandas`, `folium`, `streamlit`, `scikit-learn`, `shap`, `numpy`. **Versions fixées** (pinned) dans `requirements.txt` pour reproductibilité.

## Integration Approach

**Database**: Pas de BDD. Données en mémoire, pickle pour état. Modulaire pour Phase 2 si besoin.

**API**: Pas d'API pour le MVP. Idées Phase 2 → *Recommandations* (ex. export JSON, jobs longue durée).

**Frontend**: Streamlit remplace Tkinter. Carte (Folium ou alternative) intégrée dans Streamlit.

**Testing**: Tests unitaires (pytest recommandé) pour cohérence données, patterns, Golden Hour, features, labels. CI (GitHub Actions) géré par l'utilisateur.

## Code Organization and Standards

**File Structure Approach**: 
```
Pompier-Risques-BMAD/
├── config/                 # Fichiers config (YAML, cf. Configuration)
├── scripts/                # Pré-calculs (avant runs)
│   ├── run_precompute.py   # Script unique qui orchestre tous les pré-calculs
│   ├── precompute_distances.py
│   └── ...                 # Autres modules (vecteurs statiques, etc.) → pickles dans data/source_data/
├── src/
│   ├── data/               # Génération données, vecteurs
│   ├── golden_hour/
│   ├── events/
│   ├── patterns/
│   ├── ml/
│   └── ui/                 # Streamlit
├── data/
│   ├── source_data/        # Sortie scripts pré-calcul (vecteurs de base, proportions, distances)
│   ├── intermediate/       # Données journalières + ML par run (voir structure par run ci‑dessous)
│   ├── models/             # Modèles ML sauvegardés
│   └── patterns/           # Fichiers patterns (lus au runtime)
├── tests/
└── main.py                 # Coordonne calculs (simulation, UI) ; ne lance pas les pré-calculs
```

**Structure par run (un dossier par run, ex. `data/intermediate/run_042/`)** :  
Plusieurs pickles + JSON de traçabilité, en sous-dossiers :
- **`generation/`** (données journalières) : `vecteurs_base.pkl`, `vecteurs_proportions.pkl`
- **`events/`** : un DataFrame par événement + DataFrame incidents (type, caractéristiques, etc.)
- **`ml/`** : features condensées, features brutes, calculs morts / blessés graves (pickles dédiés)
- **`labels/`** : pickles des labels
- **`trace.json`** (ou à la racine du run) : seed, paramètres, patterns utilisés, détails du run

**Naming Conventions**: 
- Classes: **PascalCase** ; Fichiers / fonctions: **snake_case** ; Constantes: **UPPER_SNAKE_CASE**

**Coding Standards**: 
- Docstrings **homogènes** dans tout le projet (choisir un style, ex. Google ou NumPy, et le tenir).
- Type hints Python 3.12 (recommandé).
- Commentaires pour formules complexes ; gestion d'erreurs (try/except, messages clairs).

**Documentation**: README (installation, démarrage), docstrings fonctions/classes, `docs/architecture.md` (à créer).

## Deployment and Operations

**Build**: 
- `requirements.txt` pour l'app ; **pré-calculs** : deps séparées ou incluses selon besoin (ex. `requirements-precompute.txt` ou section dans README).
- Pas de packaging (wheel/setup.py) pour le MVP.

**Exécution**: 
- **Pré-calculs** : **un fichier orchestration** (ex. `scripts/run_precompute.py`) **lance** les scripts de pré-calcul (`precompute_distances.py`, etc.). Lancés **avant** les runs. Sortie dans `data/source_data/`.
- **App / simulation** : `main.py` **coordonne** tous les calculs (simulation, UI) ; **ne lance pas** les pré-calculs. Point d'entrée Streamlit : `streamlit run src/ui/web_app.py` (ou via `main.py` si encapsulé).
- **Pas de déploiement web** pour le MVP.

**Logging**: Logging Python standard (INFO, WARNING, ERROR). Sauvegarde état pour reprise.

**Configuration**: 
- **Format** : **YAML** (recommandé). **Un seul fichier** (ou jeu de fichiers) partagé entre **pré-calculs** et **application**.
- **Emplacement** : `config/` à la racine. Chemins **relatifs à la racine** du projet.
- Pas de secrets pour le MVP.

**Traçabilité des runs** : 
- **Un fichier JSON par run** (ex. `data/intermediate/run_XXX/trace.json`) : seed, paramètres (scénario, variabilité, durée, etc.), **tous les détails utiles**. **Patterns** lus / utilisés pour la génération **inclus** dans ce JSON.

## Risk Assessment and Mitigation

**Décisions techniques figées** :
- **Arrondissements adjacents** : **définis en dur** dans le code (pas de fichier externe).
- **Algorithmes ML** : **pas de régression linéaire** ; ouverture sur le reste (Random Forest, etc.).
- **50 runs** : **parallélisation autorisée** si réalisable (ex. multiprocessing).
- **0,33 s / jour** : **cible indicative** ; en cas de bug ou charge, dépassement acceptable.
- **OS** : **compatibilité multi-OS** (Windows, Linux, macOS) visée.

**Technical Risks**: 
- Complexité modèle Zero-Inflated Poisson → implémentation par étapes, tests unitaires, validation sur données connues.
- Performance génération → pré-calcul, cache, parallélisation si utile.
- Streamlit + carte (Folium ou alternative) → tests d'intégration précoces ; cf. *Recommandations*.

**Integration Risks**: 
- Dépendances (scikit-learn, SHAP, etc.) → Conda, `requirements.txt` avec versions fixées, env dédié.

**Mitigation**: Tests unitaires composants critiques, validation seuils (≥1 et <500 morts / 800 j **agrégés** par arrondissement), structure modulaire, doc technique, sauvegarde état fréquente.

---

## Recommandations (config, API, carte, tests)

_Recommandations PM / Architect pour les points laissés ouverts._

**Config (YAML vs JSON)**  
- **YAML** recommandé : lisible, commentaires, adapté à la config. JSON plus verbeux. Si tout est généré par code, JSON peut suffire.

**API (Phase 2)**  
- Export des runs (features, labels, métriques) en **JSON** ou **CSV** via endpoint.
- **Jobs asynchrones** pour pré-calculs / entraînement long (ex. Celery, RQ, ou simple script + file watcher).
- **Health check** léger si déploiement web (ex. `/health`).

**100 microzones – sources possibles**  
- **IRIS** (Insee) : découpages statistiques Paris → agrégation pour viser ~100 zones.
- **OpenStreetMap** : découpage par quartiers / polygones ; scripts (ex. `osmnx`, `geopandas`) pour générer GeoJSON.
- **Données Ville de Paris** : découpages existants (îlots, secteurs) à filtrer/agréger.
- **Grille** : découpage géométrique des 20 arrondissements (ex. grid par arrondissement, puis fusion pour ~100).

**Folium vs alternatives**  
- **Garder Folium** en premier choix : bon support GeoPandas, choroplèthes, popups. Intégration Streamlit via `st.folium_static` ou `st.components.v1.html`.
- **Alternatives** si blocage : **Plotly Express** `px.choropleth_mapbox` (vectoriel, fluide) ; **pydeck** (WebGL, gros datasets). Tester tôt l’intégration Streamlit + microzones.

**Carte – affichage**  
- **Microzones** et **arrondissements** affichés ensemble : **couleurs pastel** pour délimiter les arrondissements ; **trait seul** (découpage) pour les microzones, pas de remplissage obligatoire.

**Tests (pytest vs unittest)**  
- **pytest** recommandé : discovery auto, fixtures, plugins (cov, mutpy), syntaxe simple. **unittest** = stdlib, plus verbeux. Pour ce projet, **pytest** est un meilleur compromis.

**Couverture (« coverage »)**  
- **Couverture** = **pourcentage du code exécuté** par les tests (lignes ou branches). Ex. 70 % → 70 % des lignes sont couvertes.  
- Pas d’objectif chiffré imposé pour le MVP ; viser au moins les **chemins critiques** (génération J+1, Golden Hour, features, labels, ML).

---

# Epic and Story Structure

## Epic Approach

**Décision**: **Deux epics**  
- **Epic 1 : Pré-calculs** — Scripts et données fixes (distances, vecteurs statiques, microzones, etc.) produisant les pickles dans `data/source_data/`.  
- **Epic 2 : Système de Simulation et Prédiction** — Génération J+1, Golden Hour, features, labels, ML, UI. Dépend d’Epic 1.

**Rationale** : Les pré-calculs sont un livrable distinct, reproductible et testable ; le reste du système consomme leurs sorties. Numérotation **par blocs** pour Epic 2 (2.1 Infra, 2.2 Génération, 2.3 ML, 2.4 UI, 2.5 Qualité).

**Rollback** : Revert des commits concernés + exécution des tests (pytest). Pas de feature flags imposés.

**Definition of Done** (toutes les stories) : AC satisfaites, IV passées, pytest vert sur les parties concernées, pas de TODO/FIXME résiduels sur le scope de la story. Pas d’estimation (j/h ou t-shirt) dans le PRD.

**Documentation technique** : **Architecture** et **formules** produites **au fil des stories** concernées, pas uniquement en 2.5.2. **Tests** : Réalisés **pendant le développement**, en associant à chaque petite phase le petit test qui correspond.

**Préalable Epic 2** : Clarifier dans un doc (ex. `modele-j1-et-generation.md`) le **modèle J+1** et les **règles de génération** pour **tests explicites**. **Pas bloquant** pour démarrer Epic 2 (ex. 2.1.1) ; utile pour les stories Génération (2.2.x).

---

# Epic 1 : Pré-calculs

**Epic Goal** : Produire toutes les données fixes et pré-calculées (distances, vecteurs statiques, microzones, limites microzone→arrondissement, etc.) et les stocker dans `data/source_data/` pour alimenter Epic 2.

**Livrables** : Un **script unique** orchestrant tous les pré-calculs ; sorties en pickle (format au choix de l’implémentation) dans `data/source_data/`.

---

## Story 1.1 : Infrastructure et script unique de pré-calcul

As a **développeur**,  
I want **un script unique** qui lance **tous** les pré-calculs, **la même config** que l’app, et les dossiers dédiés,  
so that **les pré-calculs sont reproductibles en une commande**.

### Acceptance Criteria

1. Dossiers `scripts/`, `data/source_data/`, `config/` créés. **Un seul script** (ex. `scripts/run_precompute.py`) appelle tous les calculs (distances, vecteurs statiques, microzones, etc.).
2. **Config** : **Un seul fichier** config partagé (ex. `config/*.yaml`) pour pré-calculs et application.
3. **Lancer une partie seulement** : possibilité documentée (README + script) — **argument CLI** (ex. `--skip-distances` pour n’exécuter que 1.3) et/ou **section config** pour activer/désactiver des blocs.
4. `requirements.txt` (ou `requirements-precompute.txt`) avec deps ; README : lancement, sorties, usage des arguments/section.
5. Format des pickles : **laissé au choix de l’implémentation**.

### Integration Verification

IV1: `scripts/` et `data/source_data/` n’écrasent pas `src/`, `docs/`, `brainstorming/`.  
IV2: Imports OK dans l’env Conda. Lancement partiel (argument et/ou section config) documenté et vérifiable.

---

## Story 1.2 : Pré-calcul des distances et 100 microzones (caserne ↔ microzone, microzone ↔ hôpital)

As a **système de simulation**,  
I want **trajets caserne → microzone, microzone → hôpital, et découpage 100 microzones**, pré-calculés et sauvegardés,  
so that **Golden Hour (Epic 2) et la carte (100 microzones) s’appuient sur des données fixes**.

### Acceptance Criteria

1. Sous-partie du script unique : calcul des distances et microzones traversées (caserne → microzone, microzone → hôpital).
2. **100 microzones** : découpage produit et sauvegardé (ex. géométries, centroïdes). Source à définir (IRIS, OSM, etc., cf. recommandations techniques).
3. **Casernes et hôpitaux** : positions à partir d’un **fichier trouvé sur internet** correspondant au mieux à la réalité (casernes pompier Paris, hôpitaux).
4. Sorties dans `data/source_data/` (pickle ; format choisi par l’implémentation). Limites microzone→arrondissement incluses (pour agrégation Epic 2).
5. Vérifications : matrices cohérentes (pas de NaN, dimensions attendues).

### Integration Verification

IV1: Fichiers lisibles par un script Python.  
IV2: Coûts mémoire / temps raisonnables sur machine standard.

---

## Story 1.3 : Pré-calcul vecteurs statiques et prix m²

As a **système de simulation**,  
I want **vecteurs statiques (3×3 par microzone) et prix m²** pré-calculés,  
so that **le moteur J+1 et la règle prix m² (Epic 2) s’appuient sur des données fixes**.

### Acceptance Criteria

1. Sous-partie du script unique : vecteurs statiques (3×3 par microzone) à partir des patterns Paris (`data/patterns/` ou défaut).
2. **Prix m²** : **source trouvée sur internet** ou **génération** à partir de connaissances (ex. par arrondissement / microzone). Intégrée ou produite par script.
3. Sorties dans `data/source_data/` (pickle ; format au choix).
4. **Ordre** : Les vecteurs statiques peuvent être calculés **sans** les distances (Story 1.2) ; pas de dépendance obligatoire 1.3 → 1.2.
5. Vérifications : dimensions et plages cohérentes.

### Integration Verification

IV1: Artefacts chargés sans erreur.  
IV2: Aucun conflit avec `data/intermediate/` (runs Epic 2).

---

# Epic 2 : Système de Simulation et Prédiction des Risques

**Epic Goal** : Mettre en place la génération J+1, Golden Hour, features, labels, ML et l’interface Streamlit (simulation runnable avec ou sans UI, minimal UI Lancer/Stop).

**Integration Requirements** : Compatibilité GeoPandas/Folium, structure modulaire, sauvegarde état. **Simulation exécutable sans UI** (ex. script ou `main.py`) et **UI minimale (Lancer, Stop)** dès que la boucle de simulation est branchée.

**Blocs** : 2.1 Infra · 2.2 Génération · 2.3 ML · 2.4 UI · 2.5 Qualité. Numérotation des stories par bloc (2.1.1, 2.2.1, …).

---

## Bloc 2.1 — Infra

## Story 2.1.1 : Infrastructure de base et structure de projet

As a **développeur**,  
I want **une structure de dossiers modulaire et des classes de base (Vector, Event)**,  
so that **l’implémentation des fonctionnalités complexes peut commencer sur des fondations solides**.

### Acceptance Criteria

1. Structure de dossiers alignée avec les contraintes techniques : `config/`, `scripts/`, `src/data/`, `src/golden_hour/`, `src/events/`, `src/patterns/`, `src/ml/`, `src/ui/`, `data/source_data/`, `data/intermediate/`, `data/models/`, `data/patterns/`, `tests/`.
2. Classe `Vector` (bénin, moyen, grave). **Events** : `Event` ; **Incidents** = opposés aux événements positifs (accident grave, incendie grave, agression grave) ; **PositiveEvent** avec sous-classes concrètes : Fin travaux, Nouvelle caserne, Amélioration matériel, etc.
3. `requirements.txt` avec dépendances (GeoPandas, Pandas, Folium, Streamlit, scikit-learn, SHAP, numpy).
4. README avec installation et démarrage.
5. Tests unitaires de base pour `Vector`.

### Integration Verification

IV1: Imports GeoPandas, Pandas, Folium fonctionnent.  
IV2: La structure n’interfère pas avec `brainstorming/`, `docs/`, etc.

---

## Bloc 2.2 — Génération

**Ordre d’implémentation** : 2.2.1 → 2.2.2 → **2.2.9** → **2.2.10** → 2.2.3 → 2.2.4 → 2.2.5 → 2.2.6 → 2.2.7 → 2.2.8. **Matrices** et **vecteurs statiques** avant Golden Hour.

---

## Story 2.2.1 : Génération vecteurs journaliers (Étape 1)

As a **système de simulation**,  
I want **générer des vecteurs journaliers (3 vecteurs × 3 valeurs) par microzone selon modèle Zero-Inflated Poisson avec régimes cachés**,  
so that **les données de base pour toutes les autres fonctionnalités sont disponibles**.

### Acceptance Criteria (sous-étapes vérifiables par tests explicites)

1. **Modèle et régimes** : Implémentation Zero-Inflated Poisson avec 3 régimes cachés (Stable, Détérioration, Crise). Tests : présence des 3 régimes, transitions possibles.
2. **Vecteurs par microzone** : Génération 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave) par microzone. Tests : dimensions, types.
3. **Matrices de transition** : Matrices de transition entre régimes implémentées (modifiables selon patterns). Tests : sommes lignes = 1, pas de NaN.
4. **Zero-inflation** : Calcul probabilités zero-inflation selon formules Session 4. Tests : valeurs dans [0,1], cohérence avec formules doc.
5. **Intensités calibrées** : Calcul intensités avec facteurs (statique, long-terme, etc.). Tests : positivité, caps éventuels.
6. **Sauvegarde** : Sauvegarde vecteurs journaliers en pickle (structure par run dans `data/intermediate/`). Tests : chargement, cohérence.
7. **Cohérence globale** : Tests unitaires validant probabilités (somme = 1), valeurs positives, pas de NaN, boucle jour-à-jour sans fuite mémoire.

### Integration Verification

IV1: Vecteurs compatibles avec structure GeoPandas / DataFrame utilisée en aval.  
IV2: Génération jour-à-jour en boucle sans fuite mémoire.  
IV3: Performance ≤ 0.33 s/jour (cible indicative).

---

## Story 2.2.2 : Vecteurs alcool/nuit et patterns (Étape 2)

As a **système de simulation**,  
I want **proportions alcool/nuit (Monte-Carlo) et patterns 4j/7j/60j** (lecture + génération),  
so that **les features hebdo incluent ces proportions et les patterns modulent les régimes et matrices**.

### Acceptance Criteria

1. Monte-Carlo journalier proportions alcool/nuit par type (3×2 = 6) ; agrégation hebdomadaire.
2. **Patterns de base** : lecture depuis `data/patterns/` (ex. **4j** ou **7j**). Ces patterns **génèrent** des patterns futurs qui **modifient** les matrices 7j et 60j.
3. **7j** : `Ψ_court(t)` ; si trop d’incidents d’une certaine gravité (ex. ≥4 moyen) → pattern de probabilité légèrement plus élevée.
4. **60j** : structure type **20 jours hausse, 20 jours sous la moyenne, 20 jours re-hausse** pour ajouter chaos / variabilité (ML).
5. Mise à jour matrices de transition selon patterns activés (×3.5 court-terme, Crise si `Φ_long > 15`, etc.).
6. Tests unitaires : proportions [0,1], patterns, modification matrices.

### Integration Verification

IV1: Proportions cohérentes ; patterns modifient les régimes.  
IV2: Lecture depuis `data/patterns/` (format défini) OK.

---

## Story 2.2.3 : Golden Hour — calculs distances et stress (Étape 3)

As a **système de simulation**,  
I want **calculer Golden Hour (temps trajet caserne→microzone→hôpital) avec congestion et stress**,  
so that **morts et blessés graves peuvent être calculés avec réalisme**.

### Acceptance Criteria

1. **Chargement explicite** des trajets pré-calculés depuis `data/source_data/` (produits par Epic 1, Story 1.2). La story **doit** décrire explicitement ce chargement (pickle).
2. **Congestion** par microzone : calcul à partir de **randomness**, **accidents** (↑ congestion), **incendies moyen/grave** (zone bloquée → ↓ congestion). Même principes que vecteurs / proportions : **récurrence microzone, voisins, événements**.
3. `temps_trajet_reel = temps_base × ∏(congestion)` ; `temps_trajet = temps_base × (1 + stress_caserne × 0.1) × ∏(congestion)` ; `temps_total = temps_trajet + temps_traitement + temps_hopital_retour`.
4. Golden Hour : si `temps_total > 60 min` → `casualties × 1.3`. Stress : 30 pompiers/caserne, +0.4 par intervention.
5. Tests unitaires : distances, temps, Golden Hour, stress.

### Integration Verification

IV1: Trajets chargés depuis `data/source_data/` ; Golden Hour **avant** morts/blessés (ordre critique).  
IV2: Performances raisonnables pour toutes microzones.

---

## Story 2.2.4 : Morts et blessés graves hebdomadaires (Étape 4)

As a **système de simulation**,  
I want **calculer morts et blessés graves hebdomadaires par arrondissement** (Golden Hour, agrégation microzones),  
so that **les features hebdo incluent ces données critiques**.

### Acceptance Criteria

1. **Morts** par type (accident, incendie, agression) : **30 % aléatoire, 70 % Golden Hour** (la personne peut mourir malgré le respect de la Golden Hour).
2. **Blessés graves** par type : **60 % aléatoire, 40 % Golden Hour** (gravité pouvant être inhérente à l’accident, pas seulement à la réponse pompiers). Utilisation Golden Hour (2.2.3).
3. **Agrégation microzones → arrondissements** (limites dans pré-calculs Epic 1) ; totaux hebdomadaires.
4. **Alertes** (par arrondissement, sur **800 jours agrégés sur plusieurs runs**) : **au moins 1 mort**, **moins de 500 morts**. Si 0 mort ou ≥ 500 morts → **message d’alerte uniquement** (pas d’action automatique).
5. Tests unitaires : formules, agrégation, seuils.

### Integration Verification

IV1: Golden Hour **avant** cette story ; morts/blessés cohérents avec vecteurs.  
IV2: Agrégation correcte (somme, pas moyenne).

---

## Story 2.2.5 : Features hebdomadaires — StateCalculator (Étape 5)

As a **système de simulation**,  
I want **calculer 18 features hebdomadaires par arrondissement via StateCalculator**,  
so that **les modèles ML peuvent être entraînés sur ces features**.

### Acceptance Criteria

1. Classe `StateCalculator` ; agrégation microzones → arrondissements avec **limites issues des pré-calculs** (Epic 1).
2. Calcul 6 features sommes incidents: (moyen + grave) et bénin par type (3 types × 2 = 6)
3. Calcul 6 features proportions: alcool et nuit par type (3 types × 2 = 6) — utilise agrégation hebdomadaire Story 2.2.2.
4. Calcul 3 features morts hebdomadaires par type (accident, incendie, agression) — utilise Story 2.2.4.
5. Calcul 3 features blessés graves hebdomadaires par type — utilise Story 2.2.4.
6. Total: 18 features par arrondissement par semaine
7. Sauvegarde features en DataFrame avec colonnes claires (arrondissement, semaine, feature_1, ..., feature_18)
8. Tests unitaires validant calculs, agrégation, format DataFrame

### Integration Verification

IV1: Vérifier que toutes dépendances sont disponibles (vecteurs, proportions, morts/blessés)

IV2: Vérifier que les features sont dans format utilisable pour ML (pas de NaN, types numériques)

IV3: Vérifier que l'agrégation hebdomadaire est cohérente (somme pour sommes, moyenne pour proportions?)

---

## Story 2.2.6 : Labels mensuels — LabelCalculator (Étape 6)

As a **système de simulation**,  
I want **calculer labels (score et classes) mensuels** à partir de morts + blessés graves,  
so that **les modèles ML sont entraînés en supervision**.

### Acceptance Criteria

1. Classe `LabelCalculator`. **Agrégation mensuelle** : **exactement 4 semaines** (pas de mois civils). Données Paris : peu de morts/blessés graves par arrondissement et par mois.
2. **Score** : `morts + 0.5 × blessés_graves` (par mois). **Seuils** : **1, 2 ou 3 morts/mois** selon la zone, ou **4 à 6 blessés graves** ; les 18 features prédisent ces labels.
3. **Classes** : Normal / Pre-catastrophique / Catastrophique selon ces seuils (détail dans `modele-j1-et-generation.md` ou implémentation).
4. **Seulement** casualties des événements (éviter double comptage). Sauvegarde labels + features dans DataFrame ML. **Prédiction** puis **réalité** pour comparaison.
5. Tests unitaires : formules, classes, agrégation mensuelle.

### Integration Verification

IV1: Labels alignés avec features (même arrondissement, même période).  
IV2: Pas de double comptage ; classes non ambiguës.

---

## Story 2.2.7 : Événements graves modulables (Accident, Incendie, Agression)

As a **système de simulation**,  
I want **générer événements graves** avec caractéristiques probabilistes,  
so that **la complexité pour le ML est suffisante** (effets locaux, ricochets, patterns).

### Acceptance Criteria

1. Classes `AccidentGrave`, `IncendieGrave`, `AgressionGrave` (héritant de `EventGrave`). Caractéristiques : Traffic slowdown, Cancel sports, Increase bad vectors, Kill pompier (probas et durées selon spec).
2. **Moment de génération** : **juste après** les vecteurs (dans la boucle jour-à-jour). Effets : stress long-terme, pattern court-terme, transitions régimes ; durée 3–10 j ; propagation spatiale (microzone, voisins, gravité décroissante).
3. **Matrices de génération** : les événements peuvent **modifier** les matrices (effets locaux, par ricochet) ; patterns et saisonnalité les modulent aussi.
4. Tests unitaires : caractéristiques, effets temporels/spatiaux.

### Integration Verification

IV1: Événements graves modifient les vecteurs (augmentation) ; probabilités respectées.  
IV2: Propagation spatiale et temporelle conforme.

---

## Story 2.2.8 : Événements positifs et règle prix m²

As a **système de simulation**,  
I want **générer événements positifs** et **appliquer la règle prix m²**,  
so that **travaux, casernes, etc. et corrélations socio-économiques** sont reflétés.

### Acceptance Criteria

1. Événements positifs (Fin travaux, Nouvelle caserne, Amélioration matériel) ; **génération en début de journée** (avant vecteurs).
2. **Effets** : **réduction des intensités** et amélioration des transitions (pas d’« annulation » binaire des négatifs ; modulation).
3. **Prix m²** : `facteur_prix_m2 = prix_m2_microzone / prix_m2_moyen_paris` ; `prob_agression_modulée = prob_agression_base / facteur_prix_m2` ; diminution des probabilités Détérioration/Crise si prix m² élevé. Données depuis pré-calculs (Epic 1).
4. Tests unitaires : effets positifs, modulation agressions et régimes.

### Integration Verification

IV1: Événements positifs réduisent bien les intensités ; règle prix m² appliquée.  
IV2: Données prix m² chargées correctement (depuis `data/source_data/`).

---

## Story 2.2.9 : Trois matrices de modulation (gravité, croisée, voisins)

As a **système de simulation**,  
I want **appliquer trois matrices de modulation (gravité microzone, types croisés, voisins) dans calcul intensités**,  
so that **les corrélations spatiales et temporelles sont prises en compte dans prédiction J+1**.

### Acceptance Criteria

1. Matrice gravité microzone: Même type, même microzone, historique 7 jours avec décroissance exponentielle
2. Matrice types croisés: Autres types, même microzone, corrélations spécifiques (ex: incendie→accidents ×1.3)
3. Matrice voisins: 8 zones alentours (radius 1), pondération grave ×1.0, moyen ×0.5, bénin ×0.2, modulée par variabilité locale
4. Intégration dans formule: `λ_calibrated(τ,g) = λ_base(τ,g) × facteur_statique × facteur_gravité × facteur_croisé × facteur_voisins × facteur_long`
5. Normalisation: `Z(t) = Σ_{τ,g} λ_calibrated(τ,g)`
6. Caps: Min ×0.1, Max ×3.0
7. Tests unitaires validant calculs matrices, intégration formule, normalisation, caps

### Integration Verification

IV1: Vérifier que les trois matrices sont calculées correctement (historique, corrélations, voisins)

IV2: Vérifier que l'intégration dans formule intensités calibrées fonctionne (pas d'erreurs, valeurs cohérentes)

IV3: Vérifier que la normalisation et les caps sont appliqués correctement

---

## Story 2.2.10 : Vecteurs statiques et interface patterns Paris

As a **système de simulation**,  
I want **implémenter vecteurs statiques (3×3 par microzone) comme interface patterns Paris → modèle**,  
so that **les patterns Paris peuvent influencer régimes ET intensités**.

### Acceptance Criteria

1. Vecteurs statiques implémentés: 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave) par microzone
2. Influence sur régimes: Vecteurs statiques modifient probabilités régimes (Stable/Détérioration/Crise)
3. Influence sur intensités: Vecteurs statiques modifient intensités λ_base(τ,g)
4. **Vecteurs statiques** : **chargés depuis `data/source_data/`** (pré-calculés Epic 1, Story 1.3). Interface patterns Paris → modèle (lecture `data/patterns/`, application).
5. Tests unitaires : influence régimes, influence intensités, chargement.

### Integration Verification

IV1: Vecteurs statiques chargés depuis `data/source_data/` ; influence régimes et intensités correcte.  
IV2: Lecture patterns et application OK.

---

## Bloc 2.3 — ML

## Story 2.3.1 : Préparation données ML — fenêtres glissantes

As a **système ML**,  
I want **préparer données ML avec fenêtres glissantes et arrondissements adjacents** (1 central + 4 voisins, **dernière semaine** chacun → **90 features**),  
so that **les modèles peuvent être entraînés sur format correct**.

### Acceptance Criteria

1. **Features ML** : **1 arrondissement central** (18 features, **dernière semaine**) + **4 voisins** (chacun 18 features, **dernière semaine**) = 18 + 4×18 = **90 features**.
2. Arrondissements adjacents **définis en dur** dans le code (cf. contraintes techniques).
3. DataFrame final pour ML : 90 colonnes (features) + 1 colonne label (score ou classe).
4. **Workflow** : **50 runs** au total. **1 run** (affiché à l’écran) + **49 runs** en calcul seul pour générer les données ML — pas de « 5 runs puis 49 ». Central et voisins : **dernière semaine** pour les features.
5. Tests unitaires : fenêtres glissantes, adjacents, format DataFrame.

### Integration Verification

IV1: Vérifier que les fenêtres glissantes sont créées correctement (central + 4 voisins, dernière semaine chacun → 90 features)

IV2: Vérifier que les arrondissements adjacents sont corrects (géographiquement adjacents)

IV3: Vérifier que le DataFrame final est dans format utilisable pour scikit-learn (pas de NaN, types numériques)

---

## Story 2.3.2 : Entraînement modèles ML — régression et classification

As a **système ML**,  
I want **entraîner 4 modèles ML (2 régression, 2 classification) sur données préparées**,  
so that **des prédictions peuvent être faites avec interprétabilité**.

### Acceptance Criteria

1. **2 régression** : **Random Forest**, **Ridge** (ou 2 parmi RF, Ridge, etc. ; pas de régression linéaire simple).
2. **2 classification** : **Logistic Regression**, **XGBoost** (ou 2 parmi LogReg, XGBoost, etc.).
3. Entraînement sur DataFrame final (90 features, labels)
4. Calcul métriques: MAE, RMSE, R² (régression), Accuracy, Precision, Recall, F1 (classification)
5. Hyperparamètres: Phase 2 (valeurs fixes au début)
6. Sauvegarde modèles avec métadonnées: Nom algorithme, numéro entraînement, paramètres génération données
7. Format sauvegarde: `{algo}_{numero_entrainement}_{params}.joblib` dans `models/regression/` ou `models/classification/`
8. Tests unitaires validant entraînement, métriques, sauvegarde

### Integration Verification

IV1: Vérifier que les modèles peuvent être entraînés sans erreur (données valides)

IV2: Vérifier que les métriques sont calculées correctement (comparaison avec valeurs attendues)

IV3: Vérifier que les modèles sauvegardés peuvent être rechargés et utilisés pour prédiction

---

## Story 2.3.3 : SHAP values pour interprétabilité

As a **utilisateur décideur**,  
I want **voir SHAP values pour comprendre importance des 18 features**,  
so that **je peux faire confiance aux prédictions et comprendre les facteurs de risque**.

### Acceptance Criteria

1. **Code SHAP** implémenté en MVP ; calcul pour chaque modèle (régression et classification) ; importance des 18 features (graphiques, summary).
2. **Bouton/checkbox** dans l’UI pour **lancer ou non** le calcul (peut être long).
3. Intégration workflow ML ; sauvegarde optionnelle. Visualisation dans Streamlit (Story 2.4.4).
4. Tests unitaires : calcul SHAP, format, visualisation.

### Integration Verification

IV1: Vérifier que SHAP peut être calculé pour tous modèles (compatibilité)

IV2: Vérifier que les SHAP values sont cohérentes (importance features logique)

IV3: Vérifier que la visualisation SHAP fonctionne dans Streamlit

---

## Bloc 2.4 — UI

## Story 2.4.1 : Interface Streamlit — layout et contrôles de base

As a **utilisateur**,  
I want **une interface web Streamlit avec layout défini (carte centre, colonnes gauche/droite, bandeaux)**,  
so that **je peux interagir avec le système de simulation**.

### Acceptance Criteria

1. Application Streamlit dans `src/ui/web_app.py`.
2. Layout 3 colonnes : liste événements/incidents (gauche), carte Paris (centre), **liste de rectangles** arrondissements (droite — un rectangle par arrondissement, chaque nom dans un rectangle). Bandeaux haut/bas (cf. spécifications UI détaillées).
3. **Carte** : **affichage immédiat des 100 microzones** (données pré-calculées Epic 1).
4. Bandeau haut : expander scénario, variabilité ; bloc ML 3×2 (haut droite). Bandeau bas : nombre de jours (défaut 365), Jours X/Total (avec %), Run X/50, [Lancer], [Stop], [Reprendre].
5. Widgets Streamlit (selectbox, slider, button, radio) ; codes couleur, charte (pastel, Inter, français), emojis (FR20/FR25/FR26).
6. Tests manuels : layout, widgets, carte.

### Integration Verification

IV1: Vérifier que Streamlit peut être lancé (`streamlit run src/ui/web_app.py`)

IV2: Vérifier que la carte Folium s'affiche correctement dans Streamlit

IV3: Vérifier que les widgets fonctionnent (sélections, boutons)

---

## Story 2.4.2 : Orchestration (main.py, config, simulation sans UI)

As a **développeur**,  
I want **brancher `main.py`** (config, simulation, Streamlit) **après** la structure Streamlit (2.4.1),  
so that **la simulation est exécutable avec ou sans UI**.

### Acceptance Criteria

1. **Ordre** : **2.4.1 avant 2.4.2** — d’abord layout Streamlit, puis branchement de `main.py`.
2. `main.py` charge la config (`config/`), lance la boucle de simulation, peut lancer Streamlit. Pas de pré-calculs (Epic 1).
3. **Mode headless** : N jours / N runs sans UI. **Pas d’obligation** de fichiers de sortie supplémentaires (pickles/trace par run suffisent).
4. Tests : pipeline config → simulation OK sans Streamlit.

### Integration Verification

IV1: Headless produit sorties conformes (pickles, trace) si implémenté.  
IV2: `streamlit run ...` lance l’app sans erreur une fois orchestré.

---

## Story 2.4.3 : Simulation et visualisation (Lancer, Stop, minimal UI)

As a **utilisateur**,  
I want **lancer la simulation et voir la progression en temps réel**,  
so that **je peux suivre l’évolution des risques**.

### Acceptance Criteria

1. **UI minimale** : [Lancer] et [Stop] fonctionnels ; progression (Jours X/Total, Run X/50, 1 jour = 0.33 s).
2. **1 run affiché** : **un run** est simulé et affiché à l’écran (0.33 s/jour) ; les **49 autres runs** sont faits **en calcul seul** (sans affichage) pour générer les données ML.
3. [Lancer] démarre ; [Stop] interrompt et sauvegarde l’état (**état d’urgence** / safe state pour inspection : fichiers créés, partie du run).
4. Carte Paris mise à jour en temps réel ; événements (codes couleur) ; priorité Feu > Agression > Accident.
5. Colonne gauche : liste événements/incidents (chronologique, gris quand passé, emojis). Colonne droite : rectangles arrondissements (taille fixe, pastel, 3 totaux, emojis).
6. **Graphiques détaillés** (clic arrondissement → évolution temporelle) : **Phase 2** uniquement ; MVP = pas de fenêtre au clic.
7. Tests manuels : simulation, progression, Lancer/Stop, visualisations.

### Integration Verification

IV1: La simulation se lance et s’exécute correctement (Lancer/Stop, pas d’erreurs).  
IV2: Progression mise à jour en temps réel ; visualisations cohérentes (carte, listes, rectangles).

---

## Story 2.4.4 : Interface Streamlit — ML et modèles sauvegardés

As a **utilisateur**,  
I want **entraîner modèles ML et charger modèles sauvegardés pour prédiction**,  
so that **je peux utiliser le système pour prédictions réelles**.

### Acceptance Criteria

1. Bloc ML 3×2 (layout 2.4.1) **connecté** aux modules ML : Train a model / Use a prediction model, Régression / Classification, 2 algos (RF, Ridge, LogReg, XGBoost).
2. **Bouton/checkbox** pour **calcul SHAP** (lancer ou non) ; code SHAP présent en MVP. Métadonnées modèles (nom, n° entraînement, jours, accuracy).
3. Entraînement depuis interface ; métriques (MAE, RMSE, R² ou Accuracy, Precision, Recall, F1) ; SHAP si coché.
4. **Entraînement** : **1 run** affiché à l’écran (0.33 s/jour) + **49 runs** en calcul seul pour ML. **Prédiction** : **1 run** affiché uniquement, pas de runs en calcul seul.
5. Tests manuels : entraînement, chargement, prédiction, visualisations.

### Integration Verification

IV1: Vérifier que l'entraînement depuis interface fonctionne (pas d'erreurs, modèles sauvegardés)

IV2: Vérifier que le chargement modèles fonctionne (liste fichiers, métadonnées affichées)

IV3: Vérifier que les prédictions avec modèle chargé fonctionnent (format, valeurs cohérentes)

---

## Story 2.4.5 : Sauvegarde / reprise état simulation et export

As a **utilisateur**,  
I want **sauvegarder l’état et exporter des résultats partiels**,  
so that **je peux interrompre, reprendre ou analyser hors ligne**.

### Acceptance Criteria

1. **Bouton [Stop]** : sauvegarde automatique de l’état (**état d’urgence** / safe state) en milieu de run — vecteurs, événements, variables cachées — pour **inspection** (fichiers créés, partie du run).
2. **Bouton dédié [Sauvegarder]** pour export des résultats partiels (features, labels, modèles ML). Formats : CSV (features/labels), joblib (modèles), HTML (cartes).
3. Reprise après interruption : chargement état sauvegardé, reprise depuis point d’arrêt. Pickle dans `data/intermediate/` (ou dossier dédié type `data/safe_state/` pour état d’urgence).
4. Tests unitaires : sauvegarde, chargement, export, reprise.

### Integration Verification

IV1: Sauvegarde et reprise fonctionnent (fichiers créés, format correct).  
IV2: Exports utilisables (CSV, modèles rechargeables).

---

## Story 2.4.6 *(Phase 2)* : Graphiques détaillés par arrondissement

As a **utilisateur**,  
I want **voir graphiques détaillés (morts, blessés, incidence, vecteurs) au clic sur un arrondissement**,  
so that **j’analyse finement les risques par zone**.

### Acceptance Criteria

1. Clic sur rectangle arrondissement → **fenêtre** (ou expander) avec graphiques.
2. **Contenu** : **nombre de morts**, **nombre de blessés**, **incidence** (évolution des incidents), **évolution des sommes de vecteurs** dans l’arrondissement ; **Phase 2** inclut aussi **évolution des 18 features** et **courbes par type** d’incident.
3. Intégration fluide avec le layout Streamlit (hors carte, selon specs UI).

### Integration Verification

IV1: Ouverture/fermeture sans erreur ; pas de régression Lancer/Stop.  
IV2: Données correspondent à l’arrondissement sélectionné.

**Scope** : Phase 2 uniquement ; hors MVP.

---

## Bloc 2.5 — Qualité

## Story 2.5.1 : Validation et tests de cohérence

As a **développeur/QA**,  
I want **valider cohérence données et patterns avec tests automatisés**,  
so that **le système génère des données réalistes et cohérentes**.

### Acceptance Criteria

1. Tests validation cohérence données (par arrondissement, sur **800 jours agrégés sur plusieurs runs**) : **au moins 1 mort**, **moins de 500 morts**. Si 0 mort ou ≥ 500 morts → **alerte (message uniquement, pas d’action automatique)**.
2. Tests validation patterns : vérifier qu’il n’y a pas de **propagation directionnelle** indésirable — un effet d’événement peut se propager dans une direction (bas, gauche, droite) et modifier pendant quelques jours les matrices de création de vecteurs (proportions alcool/nuit ou vecteurs des 3 types d’incidents).
3. Tests unitaires pour chaque composant critique: Vecteurs, Golden Hour, Features, Labels, ML
4. Tests d'intégration: Workflow complet simulation → features → labels → ML
5. Suivi graphiques: Nombre de morts, évolution temporelle, validation visuelle
6. Documentation tests: README tests, commentaires, exemples
7. Couverture tests: Au minimum composants critiques (vecteurs, Golden Hour, features, ML)

### Integration Verification

IV1: Vérifier que les tests de validation détectent bien problèmes (tests avec données invalides)

IV2: Vérifier que les tests d'intégration passent (workflow complet)

IV3: Vérifier que la couverture tests est suffisante (composants critiques testés)

---

## Story 2.5.2 : Documentation technique et utilisateur

As a **développeur/utilisateur**,  
I want **documentation technique et guide utilisateur**,  
so that **le système est maintenable et utilisable**.

### Acceptance Criteria

1. **README.md** : installation, démarrage, structure projet, dépendances.
2. **`docs/architecture.md`** : structure, composants, flux données ; **niveaux d’intégration** — microzone, voisins, inter-type, même type, incidents, proportions, **congestion routière**, **saisonnalité**, **lecture de patterns** générant des patterns futurs, **effets positifs/négatifs** sur les matrices de génération.
3. **`docs/formules.md`** : **formules mathématiques** et **matrices** (Zero-Inflated Poisson, Golden Hour, features, labels, modulations).
4. **`docs/modele-j1-et-generation.md`** : **explication d’ensemble** de la complexité — randomness, patterns réels, ce qui est prédictible ; règles de génération pour tests explicites.
5. Guide utilisateur : interface Streamlit, paramètres, interprétation des résultats. Docstrings et commentaires pour algorithmes complexes. Documentation patterns (format fichiers) et modèles ML (sauvegarde, métadonnées).

### Integration Verification

IV1: Documentation complète et à jour.  
IV2: Instructions claires et exemples utilisables.

---

**Fin du PRD**
