# Pompier-Risques-BMAD Brownfield Enhancement PRD

**Version:** v4  
**Date:** 27 Janvier 2026  
**Statut:** En rédaction

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
| Peaufinement UI | 27 Jan 2026 | v4 | Réponses session objectifs UI : bloc ML 4×2, layout 2/3 colonnes, bandeau bas, Stop/Reprendre, paramètres verrouillés, prédiction semaine 5+, scripts pré-calc, entraînement après 50 runs. Nouvelles FR21–FR24, mise à jour FR10–FR12, FR18–FR19. Section « Spécifications UI détaillées » ajoutée. | PM |
| Peaufinement UI (2) | 27 Jan 2026 | v4 | Liste chrono + gris quand passé + emojis (flamme, couteau, voiture, rose verte). Rectangles taille fixe, pastel, 3 totaux, pas de clic détail MVP. Carte 100 microzones, délimitation. Inter, pastel, français. Défaut 365 j, auto-save pickle, run complet enregistré. Prédiction 1 run + reset. Graphiques détail Phase 2, SHAP MVP. FR25–FR28, mise à jour FR10–FR11, FR18, FR20–FR22. §9–11 Spécifications UI. | PM |

---

# Requirements

## Functional

FR1: Le système doit générer des vecteurs journaliers (3 vecteurs × 3 valeurs: bénin, moyen, grave) par microzone selon le modèle Zero-Inflated Poisson avec régimes cachés (Stable, Détérioration, Crise).

FR2: Le système doit calculer les proportions alcool/nuit par type d'incident via Monte-Carlo journalier, puis agrégation hebdomadaire.

FR3: Le système doit implémenter le calcul Golden Hour (temps trajet caserne→microzone→hôpital) avec prise en compte congestion, stress pompiers, et effet sur casualties si > 60 min.

FR4: Le système doit calculer les morts et blessés graves hebdomadaires par arrondissement en utilisant Golden Hour (30% base aléatoire, 60% après Golden Hour pour morts).

FR5: Le système doit calculer 18 features hebdomadaires par arrondissement: 6 sommes incidents (moyen+grave et bénin par type), 6 proportions (alcool et nuit par type), 3 morts hebdo, 3 blessés graves hebdo.

FR6: Le système doit générer des labels (score ou classes) mensuels à partir de morts + blessés graves, avec formule: `(morts × 0.5 + blessés_graves) / (habitants_arr / 100000) × 3.25`.

FR7: Le système doit entraîner des modèles ML (2 régression, 2 classification) sur fenêtres glissantes de 4 semaines consécutives (18 features × 4 arrondissements = 90 features par arrondissement central).

FR8: Le système doit fournir des SHAP values pour interprétabilité des modèles ML.

FR9: Le système doit sauvegarder les modèles avec métadonnées (nom, numéro entraînement, paramètres génération) dans `models/regression/` ou `models/classification/`.

FR10: Le système doit fournir une interface web Streamlit sur **une seule page** : carte Paris (centre, **100 microzones** avec délimitation visible), liste événements/incidents (gauche), colonnes droite selon mode (entraînement: 2 colonnes — rectangles 20 arrondissements; prédiction: 3 colonnes — Prédictions, État arrondissement, Prédiction arrondissement), bandeaux haut/bas.

FR11: Le système doit permettre la sélection de paramètres : **haut gauche** (expander) scénario (pessimiste/moyen/optimiste), variabilité locale (faible/moyen/important) ; **bandeau bas gauche** nombre de jours (**défaut 365**). Lancer possible avec **tous paramètres par défaut**. **Tous paramètres verrouillés** pendant la simulation jusqu'à Stop ; **à l'arrêt, paramètres perdus** (reset).

FR12: Le système doit afficher en temps réel **bandeau bas** : Jours simulés/Total (jour par jour, optionnellement %), Run X/50, progression entraînement ML (après 50 runs). Vitesse 1 jour = 0.33s.

FR13: Le système doit générer des événements graves modulables (Accident, Incendie, Agression) avec caractéristiques probabilistes (traffic slowdown, cancel sports, increase bad vectors, kill pompier).

FR14: Le système doit gérer des événements positifs (fin travaux, nouvelle caserne, amélioration matériel) modifiant les matrices de transition en mieux.

FR15: Le système doit détecter les patterns court-terme (7 jours) et long-terme (60 jours) selon les formules définies dans le modèle scientifique.

FR16: Le système doit appliquer les trois matrices de modulation (gravité microzone, types croisés, voisins) dans le calcul des intensités calibrées.

FR17: Le système doit appliquer la règle prix m² (division probabilité agression, diminution probabilités régimes).

FR18: Le système doit permettre **Stop** (arrêt du calcul), affichage du **dernier état de la carte**, **bouton [Reprendre]** pour continuer à partir de l'état sauvegardé. **Sauvegarde automatique** en pickle (dossier dédié, ex. « état d'urgence » / safe state) ; **un run mené à son terme** est enregistré.

FR19: Le système doit fournir **haut droite** un bloc ML (tableau logique 4×2) : **ligne 1** — radio « Train a model » | « Use a prediction model », radio Régression | Classification, si Use prediction sélection fichier modèle (`models/classification/` ou `models/regression/`) ; **ligne 2** — si Train : choix 2 algorithmes (ex. Random Forest + autre, Linear regression + autre), saisie nom modèle après entraînement avec **génération automatique** de noms. Déverrouillage automatique des options selon le choix.

FR20: Le système doit afficher les codes couleur par type/gravité: Feu (Jaune/Orange/Rouge), Accident (Beige/Marron), Agression (Gris), avec priorité affichage: Grave → Feu > Agression > Accident. **Charte visuelle MVP** : police **Inter**, thème **clair**, couleurs **pastel** (claires, pas trop sombres). **Emojis** : flamme (incendie), couteau (agression), voiture (accident, **taille variable** selon gravité), rose verte (événement positif). **Langue** : **français uniquement**.

FR21: **Graphiques détaillés** (clic sur arrondissement → évolution temporelle) : **Phase 2** uniquement ; pas dans le MVP.

FR22: **Mode prédiction** : **un seul run** ; à la fin, **retour à l'état initial** (Paris sans événements, jour 0, défaut jours ex. 365). À partir de la **semaine 5**, afficher par arrondissement état prédit (n+1) ; **chaque fin de semaine** (après 5e) afficher **+ / −** (régression) ou **match / mismatch** (classification). Pendant une **fraction de seconde**, afficher la **réalité** puis revenir à la prédiction.

FR23: Le système doit **entraîner** les modèles ML **une fois les 50 runs terminés** (pas d'entraînement incrémental pendant les runs).

FR24: Vecteurs statiques, distances et données pré-calculées sont produits par **scripts externes** (l'utilisateur les lance) ; résultats en **pickles** chargés par l'app. Aucun calcul lourd côté UI avant le premier jour.

FR25: **Liste événements (gauche)** : ordre **chronologique** uniquement ; apparition **au fur et à mesure** ; événement **passé** → **gris** ; **pas de filtre** en MVP. Emojis (flamme, couteau, voiture taille variable, rose verte) comme en FR20.

FR26: **Rectangles arrondissements (droite)** : **taille fixe** ; couleurs **pastel** (ex. orange clair feu, vert clair événement) ; **emojis** identiques ; **3 totaux** (agressions, incendies, accidents) **mis à jour en continu**. Pas de mini-courbe ; **clic → fenêtre détails** = Phase 2 uniquement (MVP = pas de fenêtre au clic).

FR27: **Carte** : **100 microzones** avec **délimitation visible** ; événements positifs (**rose verte**), incidents (emojis flamme, couteau, voiture) sur la carte.

FR28: **SHAP** : **obligatoire en MVP** pour interprétabilité des modèles ML.

## Non Functional

NFR1: Le système doit maintenir les performances de chargement des données géospatiales existantes (GeoPandas) sans dégradation.

NFR2: Le système doit générer les données journalières en ≤ 0.33s par jour pour respecter la vitesse d'affichage requise.

NFR3: Le système doit supporter au minimum 50 runs de simulation sans dépassement mémoire significatif.

NFR4: Le système doit sauvegarder les données intermédiaires en pickle pour permettre reprise après interruption.

NFR5: Le système doit valider la cohérence des données: si 0 morts ou < 2 morts sur arrondissement sur 400 jours → alerte, si > 200 morts → alerte.

NFR6: Le système doit utiliser des nombres entiers (ints) ou floats raisonnables pour éviter problèmes de scalabilité.

NFR7: Le système doit être modulaire pour permettre remplacement données générées → vraies données BSPP sans refonte majeure.

NFR8: Le système doit maintenir la compatibilité avec les formats de données géospatiales existants (GeoJSON, GeoPandas).

NFR9: Le système doit fournir des métriques ML: MAE, RMSE, R² (régression), Accuracy, Precision, Recall, F1 (classification).

NFR10: Le système doit permettre comparaison entre modèles enregistrés avec paramètres différents.

NFR11: Le système doit gérer les erreurs gracieusement avec messages clairs pour l'utilisateur.

NFR12: Le système doit être testable avec tests unitaires pour vérifier cohérence données et validation patterns.

## Compatibility Requirements

CR1: **Compatibilité données géospatiales**: Le système doit continuer à utiliser GeoPandas et les mêmes formats GeoJSON pour les arrondissements parisiens. Les données géographiques existantes doivent rester compatibles.

CR2: **Compatibilité structure fichiers**: La structure de base du projet (main.py comme point d'entrée possible) doit être préservée, même si Streamlit devient l'interface principale.

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

### 1. Bloc ML (haut droite) – tableau 4 colonnes × 2 lignes

Layout sans bordures visibles (grille logique uniquement). Déverrouillage automatique des options selon le choix (Train vs Use prediction).

**Ligne 1 (première ligne) :**
| Colonne 1 | Colonne 2 | Colonne 3 | Colonne 4 |
|-----------|-----------|-----------|-----------|
| **Train a model** ou **Use a prediction model** (boutons radio) | **Régression** ou **Classification** (boutons radio) | Si *Use prediction* : sélection du fichier modèle enregistré (`models/classification/` ou `models/regression/`) | (à définir si besoin) |

**Ligne 2 (seconde ligne) :**
- Si **Train a model** : noms des **2 algorithmes** sélectionnables (ex. Random Forest + un autre pour classification ; Linear regression + un autre pour régression). Saisie du **nom du modèle** après entraînement, avec **génération automatique** de noms.
- Si **Use a prediction model** : lié à la sélection du modèle (fichier) en ligne 1.

### 2. Haut gauche – scénario et variabilité

- **Expander** : type de scénario (pessimiste / moyen / optimiste), variabilité locale (faible / moyen / important), etc., pour alléger l'interface.
- Pas d'ordre imposé entre ces contrôles.

### 3. Layout global (colonne gauche, centre, colonnes droite)

- **Gauche:** Liste **événements / incidents** (toujours visible). Voir § 9 (liste) et § 10 (rectangles).
- **Centre:** Carte Paris avec **100 microzones** (découpage et délimitation visibles sur la carte). Voir § 11 (carte).
- **Droite:**  
  - **Mode entraînement:** **2 colonnes** – (1) **rectangles des 20 arrondissements** (taille fixe, couleurs pastel + emojis, 3 totaux : agressions / incendies / accidents, mis à jour en continu) ; (2) même symbologie (couleurs, emojis). Clic sur rectangle → fenêtre détails (évolution temporelle) : **Phase 2** ; MVP = pas de fenêtre détaillée au clic.  
  - **Mode prédiction:** **3 colonnes** – (1) **Prédictions** ; (2) **État de l'arrondissement** (dernière semaine connue) ; (3) **Prédiction de l'arrondissement** (semaine n+1). Rien affiché avant la semaine 5 ; à partir de la semaine 5, les arrondissements apparaissent avec état prédit. **Un seul run** en mode prédiction ; à la fin, **retour à l’état initial** : Paris sans événements, affichage réinitialisé, jour 0, nombre de jours par défaut (ex. 365).

### 4. Bandeau bas – une seule ligne

- **Gauche:** Sélection du **nombre de jours** de simulation. **Valeur par défaut : 365.**
- **Centre / droite:**  
  - **Jours simulés / Total** (jour par jour), éventuellement **%** à droite.  
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

- **Mode prédiction:** **Un seul run**. À la fin du run, **retour à l’état initial** : Paris sans événements (tous événements/accidents retirés de l’affichage), **jour 0**, nombre de jours par défaut (ex. 365).
- **Graphiques détaillés** (clic sur un arrondissement → évolution temporelle) : **Phase 2** uniquement. Souhaitable après SHAP ; pas dans le MVP.
- **SHAP:** **Obligatoire en MVP** – à inclure dès la première version.

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

## Existing Technology Stack

**Languages**: Python (version à déterminer, probablement 3.8+)

**Frameworks**: 
- Tkinter (interface actuelle, à remplacer)
- GeoPandas (données géospatiales, à conserver)
- Pandas (manipulation données, à conserver)
- Folium (cartes interactives, à conserver/integrer dans Streamlit)

**Database**: Aucune base de données actuellement (données en mémoire, fichiers pickle pour sauvegarde)

**Infrastructure**: Application desktop locale (pas de déploiement serveur actuellement)

**External Dependencies**:
- `geopandas`: Chargement données arrondissements Paris
- `pandas`: Manipulation données risques
- `folium`: Génération cartes HTML
- `tkinter`: Interface actuelle (standard library)

**Nouvelles dépendances requises:**
- `streamlit`: Interface web
- `scikit-learn`: Modèles ML (RandomForest, autres à définir)
- `shap`: Interprétabilité modèles
- `numpy`: Calculs numériques (probablement déjà utilisé indirectement)
- `pickle`: Sauvegarde données intermédiaires (standard library)

## Integration Approach

**Database Integration Strategy**: Pas de base de données. Données en mémoire avec sauvegarde pickle pour état de simulation. Structure modulaire pour permettre ajout BDD en Phase 2 si nécessaire.

**API Integration Strategy**: Pas d'API actuellement. Streamlit gère l'interface utilisateur directement. Architecture modulaire pour permettre ajout API REST en Phase 2 si nécessaire.

**Frontend Integration Strategy**: Remplacement complet Tkinter → Streamlit. Les composants Folium seront intégrés dans Streamlit via `st.components.v1.html()` ou `folium_static()`. Les widgets Tkinter seront remplacés par widgets Streamlit équivalents.

**Testing Integration Strategy**: Tests unitaires Python (pytest recommandé) pour valider:
- Cohérence données (seuils morts: 0-2 ou >200)
- Validation patterns (pas de packaging)
- Calculs Golden Hour
- Features hebdomadaires
- Labels

## Code Organization and Standards

**File Structure Approach**: 
```
Pompier-Risques-BMAD/
├── src/
│   ├── data/          # Génération données, vecteurs
│   ├── golden_hour/   # Calculs Golden Hour
│   ├── events/        # Événements modulables
│   ├── patterns/      # Patterns 7j et 60j
│   ├── ml/            # Machine Learning
│   └── ui/            # Interface Streamlit
├── data/
│   ├── intermediate/   # Pickle données intermédiaires
│   ├── models/        # Modèles ML sauvegardés
│   └── patterns/      # Fichiers patterns (CSV/JSON/YAML)
├── tests/             # Tests unitaires
└── main.py            # Point d'entrée possible (à adapter)
```

**Naming Conventions**: 
- Classes: PascalCase (`Vector`, `StateCalculator`, `EventGrave`)
- Fonctions: snake_case (`calculate_golden_hour`, `generate_daily_vectors`)
- Fichiers: snake_case (`daily_data.py`, `weekly_features.py`)
- Constantes: UPPER_SNAKE_CASE (`MAX_STRESS`, `GOLDEN_HOUR_THRESHOLD`)

**Coding Standards**: 
- Docstrings Python (Google style ou NumPy style)
- Type hints Python 3.8+ (optionnel mais recommandé)
- Commentaires pour formules mathématiques complexes
- Gestion d'erreurs avec try/except et messages clairs

**Documentation Standards**: 
- README.md avec instructions installation/démarrage
- Docstrings pour toutes fonctions/classes publiques
- Commentaires pour algorithmes complexes (modèle Zero-Inflated Poisson, Golden Hour)
- Documentation architecture dans `docs/architecture.md` (à créer)

## Deployment and Operations

**Build Process Integration**: 
- Pas de build process actuellement (Python script direct)
- `requirements.txt` à créer pour dépendances
- Pas de packaging (wheel/setup.py) nécessaire pour MVP

**Deployment Strategy**: 
- Application locale Streamlit (`streamlit run src/ui/web_app.py`)
- Pas de déploiement serveur pour MVP
- Phase 2: Possible déploiement Streamlit Cloud ou serveur dédié

**Monitoring and Logging**: 
- Logging Python standard pour debug (niveaux INFO, WARNING, ERROR)
- Pas de monitoring externe pour MVP
- Sauvegarde état simulation pour reprise après erreur

**Configuration Management**: 
- Fichier de configuration YAML/JSON pour paramètres (scénarios, variabilité, etc.)
- Variables d'environnement optionnelles pour chemins fichiers
- Pas de secrets management nécessaire pour MVP (données générées)

## Risk Assessment and Mitigation

**Technical Risks**: 
- **Complexité modèle mathématique**: Le modèle Zero-Inflated Poisson avec régimes cachés est complexe. Risque d'erreurs d'implémentation.
  - *Mitigation*: Implémentation étape par étape selon ordre défini (7 étapes), tests unitaires pour chaque composant, validation avec données de test connues.

- **Performance génération données**: Génération jour-à-jour avec calculs complexes (Golden Hour, patterns) peut être lent.
  - *Mitigation*: Optimisation calculs (pré-calcul distances, cache), profiling avec cProfile, parallélisation si nécessaire (calculs vecteurs vs proportions).

- **Compatibilité Streamlit + Folium**: Intégration cartes Folium dans Streamlit peut avoir limitations.
  - *Mitigation*: Tests d'intégration dès le début, alternatives (plotly, leaflet) si nécessaire.

**Integration Risks**: 
- **Remplacement Tkinter → Streamlit**: Perte de fonctionnalités existantes si migration incomplète.
  - *Mitigation*: Liste exhaustive fonctionnalités Tkinter actuelles, migration progressive, tests de régression.

- **Dépendances nouvelles**: Ajout scikit-learn, SHAP peut créer conflits avec versions existantes.
  - *Mitigation*: Environnement virtuel Python, `requirements.txt` avec versions spécifiques, tests installation propre.

**Deployment Risks**: 
- **Pas de déploiement actuellement**: Risque faible pour MVP (local).
  - *Mitigation*: Documentation claire installation, README avec troubleshooting.

**Mitigation Strategies**: 
- Tests unitaires dès le début pour chaque composant critique
- Validation continue avec seuils définis (morts: 0-2 ou >200)
- Architecture modulaire pour faciliter debug et maintenance
- Documentation technique détaillée (formules, algorithmes)
- Sauvegarde fréquente état simulation pour reprise après erreur

---

# Epic and Story Structure

## Epic Approach

**Epic Structure Decision**: Un seul epic principal "Système de Simulation et Prédiction des Risques" car l'enhancement est cohérent et toutes les fonctionnalités sont interdépendantes. L'ordre d'implémentation est critique (7 étapes définies) et doit être respecté pour éviter problèmes de dépendances.

**Rationale**: 
- Toutes les fonctionnalités font partie du même système de simulation/prédiction
- L'ordre d'implémentation est défini et séquentiel (vecteurs → Golden Hour → features → labels → ML → UI)
- Un seul epic permet meilleure visibilité et coordination
- Les stories seront organisées selon les 7 étapes + UI + ML

---

# Epic 1: Système de Simulation et Prédiction des Risques

**Epic Goal**: Transformer l'application de visualisation statique en système complet de simulation et prédiction des risques avec génération de données réalistes, modèles ML interprétables, et interface web Streamlit interactive.

**Integration Requirements**: 
- Préserver compatibilité données géospatiales GeoPandas/Folium
- Architecture modulaire permettant remplacement données générées → vraies données BSPP
- Structure de dossiers claire séparant données, calculs, ML, UI
- Sauvegarde état simulation pour reprise après interruption

---

## Story 1.1: Infrastructure de Base et Structure de Projet

As a **développeur**,  
I want **une structure de dossiers modulaire et des classes de base (Vector, Event)**,  
so that **l'implémentation des fonctionnalités complexes peut commencer sur des fondations solides**.

### Acceptance Criteria

1. Structure de dossiers créée: `src/data/`, `src/golden_hour/`, `src/events/`, `src/patterns/`, `src/ml/`, `src/ui/`, `data/intermediate/`, `data/models/`, `data/patterns/`, `tests/`
2. Classe `Vector` implémentée avec 3 valeurs (bénin, moyen, grave) et méthodes appropriées
3. Classes de base `Event`, `Incident`, `PositiveEvent` implémentées avec structure hiérarchique
4. Fichier `requirements.txt` créé avec toutes dépendances (GeoPandas, Pandas, Folium, Streamlit, scikit-learn, SHAP, numpy)
5. README.md créé avec instructions installation et démarrage
6. Tests unitaires de base pour classe `Vector` (création, accès valeurs, opérations)

### Integration Verification

IV1: Vérifier que l'application Tkinter existante (`main.py`) peut toujours être exécutée sans erreur (même si non utilisée après)

IV2: Vérifier que les imports GeoPandas, Pandas, Folium fonctionnent toujours

IV3: Vérifier que la structure de dossiers n'interfère pas avec fichiers existants (brainstorming/, docs/, etc.)

---

## Story 1.2: Génération Vecteurs Journaliers (Étape 1)

As a **système de simulation**,  
I want **générer des vecteurs journaliers (3 vecteurs × 3 valeurs) par microzone selon modèle Zero-Inflated Poisson avec régimes cachés**,  
so that **les données de base pour toutes les autres fonctionnalités sont disponibles**.

### Acceptance Criteria

1. Implémentation modèle Zero-Inflated Poisson avec 3 régimes cachés (Stable, Détérioration, Crise)
2. Génération vecteurs journaliers par microzone: 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave)
3. Matrices de transition entre régimes implémentées (modifiables selon patterns)
4. Calcul probabilités zero-inflation selon formules Session 4
5. Calcul intensités calibrées avec facteurs (statique, long-terme, etc.)
6. Sauvegarde vecteurs journaliers en pickle dans `data/intermediate/`
7. Tests unitaires validant cohérence probabilités (somme = 1), valeurs positives, pas de NaN

### Integration Verification

IV1: Vérifier que les vecteurs générés sont compatibles avec structure DataFrame existante (GeoPandas)

IV2: Vérifier que la génération jour-à-jour peut être appelée en boucle sans fuite mémoire

IV3: Vérifier que les performances permettent génération en ≤ 0.33s par jour (objectif)

---

## Story 1.3: Vecteurs Alcool/Nuit et Patterns (Étape 2)

As a **système de simulation**,  
I want **générer proportions alcool/nuit via Monte-Carlo journalier et détecter patterns 7j/60j**,  
so that **les features hebdomadaires peuvent inclure ces proportions et les patterns modulent les régimes**.

### Acceptance Criteria

1. Génération Monte-Carlo journalière proportions alcool/nuit par type incident (3 types × 2 proportions = 6)
2. Agrégation hebdomadaire des proportions (moyenne ou autre méthode définie)
3. Détection pattern court-terme (7 jours): `Ψ_court(t) = Σ_{s=t-6}^{t} Σ_{τ∈T} I_s^(τ, Moyen)` activé si ≥ 4
4. Calcul variable cachée long-terme (60 jours): `Φ_long(t) = Σ_{ℓ=1}^{60} β_ℓ × Ψ_pondéré(t-ℓ)` avec décroissance hyperbolique
5. DataFrames mobiles pour patterns 7j et 60j (lecture depuis fichiers `data/patterns/`)
6. Mise à jour matrices de transition selon patterns activés (×3.5 si pattern court-terme, probabilité Crise si `Φ_long > 15`)
7. Tests unitaires validant détection patterns, calculs `Ψ_court` et `Φ_long`, modification matrices

### Integration Verification

IV1: Vérifier que les proportions générées sont dans [0,1] et cohérentes

IV2: Vérifier que les patterns modifient bien les régimes (tests avec patterns connus)

IV3: Vérifier que les DataFrames patterns peuvent être lus depuis fichiers (CSV/JSON/YAML)

---

## Story 1.4: Golden Hour - Calculs Distances et Stress (Étape 3)

As a **système de simulation**,  
I want **calculer Golden Hour (temps trajet caserne→microzone→hôpital) avec congestion et stress pompiers**,  
so that **les morts et blessés graves peuvent être calculés avec réalisme**.

### Acceptance Criteria

1. Pré-calcul trajets caserne → microzone (distances, microzones traversées) - données fixes
2. Pré-calcul trajets microzone → hôpital (distances, microzones traversées) - données fixes
3. Calcul temps trajet réel avec congestion: `temps_trajet_reel = temps_base × ∏(congestion_microzone_traversee)`
4. Calcul temps trajet avec stress pompiers: `temps_trajet = temps_base × (1 + stress_caserne × 0.1) × ∏(congestion)`
5. Calcul temps total: `temps_total = temps_trajet + temps_traitement + temps_hopital_retour`
6. Détection Golden Hour: si `temps_total > 60 min → casualties × 1.3`
7. Gestion stress pompiers: 30 pompiers/caserne, +0.4 stress par intervention, moyenne par caserne
8. Tests unitaires validant calculs distances, temps, Golden Hour, stress

### Integration Verification

IV1: Vérifier que les données fixes (trajets) peuvent être pré-calculées et sauvegardées (pickle ou CSV)

IV2: Vérifier que le calcul Golden Hour est appelé **avant** calcul morts/blessés (ordre critique)

IV3: Vérifier que les performances permettent calcul Golden Hour en temps raisonnable pour toutes microzones

---

## Story 1.5: Morts et Blessés Graves Hebdomadaires (Étape 4)

As a **système de simulation**,  
I want **calculer morts et blessés graves hebdomadaires par arrondissement en utilisant Golden Hour**,  
so that **les features hebdomadaires incluent ces données critiques**.

### Acceptance Criteria

1. Calcul morts hebdomadaires par type (accident, incendie, agression) avec formule: 30% base aléatoire + 60% après Golden Hour
2. Calcul blessés graves hebdomadaires par type avec formule: plus randomité, moins importance durée trajet, plus importance sévérité
3. Utilisation résultats Golden Hour (Story 1.4) pour modulation casualties
4. Agrégation microzones → arrondissements pour totaux hebdomadaires
5. Validation cohérence: si 0 morts ou < 2 morts sur arrondissement sur 400 jours → alerte, si > 200 morts → alerte
6. Tests unitaires validant formules, agrégation, validation seuils

### Integration Verification

IV1: Vérifier que Golden Hour est calculé **avant** cette story (dépendance critique)

IV2: Vérifier que les morts/blessés sont cohérents avec vecteurs journaliers générés (pas de déconnexion)

IV3: Vérifier que l'agrégation microzones → arrondissements est correcte (somme, pas moyenne)

---

## Story 1.6: Features Hebdomadaires - StateCalculator (Étape 5)

As a **système de simulation**,  
I want **calculer 18 features hebdomadaires par arrondissement via StateCalculator**,  
so that **les modèles ML peuvent être entraînés sur ces features**.

### Acceptance Criteria

1. Classe `StateCalculator` implémentée pour agrégation microzones → arrondissements
2. Calcul 6 features sommes incidents: (moyen + grave) et bénin par type (3 types × 2 = 6)
3. Calcul 6 features proportions: alcool et nuit par type (3 types × 2 = 6) - utilise agrégation hebdomadaire Story 1.3
4. Calcul 3 features morts hebdomadaires: par type (accident, incendie, agression) - utilise Story 1.5
5. Calcul 3 features blessés graves hebdomadaires: par type - utilise Story 1.5
6. Total: 18 features par arrondissement par semaine
7. Sauvegarde features en DataFrame avec colonnes claires (arrondissement, semaine, feature_1, ..., feature_18)
8. Tests unitaires validant calculs, agrégation, format DataFrame

### Integration Verification

IV1: Vérifier que toutes dépendances sont disponibles (vecteurs, proportions, morts/blessés)

IV2: Vérifier que les features sont dans format utilisable pour ML (pas de NaN, types numériques)

IV3: Vérifier que l'agrégation hebdomadaire est cohérente (somme pour sommes, moyenne pour proportions?)

---

## Story 1.7: Labels Mensuels - LabelCalculator (Étape 6)

As a **système de simulation**,  
I want **calculer labels (score ou classes) mensuels à partir de morts + blessés graves**,  
so that **les modèles ML peuvent être entraînés en supervision**.

### Acceptance Criteria

1. Classe `LabelCalculator` implémentée pour calcul labels
2. Calcul score: `(morts × 0.5 + blessés_graves) / (habitants_arr / 100000) × 3.25`
3. Calcul classes (3): Normal (≤ 3.25), Pre-catastrophique (> 4.2), Catastrophique (> 4.8 × 0.5 blessés graves)
4. Utilisation SEULEMENT casualties des événements (évite double comptage)
5. Agrégation mensuelle (4 semaines) pour labels
6. Sauvegarde labels avec features dans DataFrame final pour ML
7. Tests unitaires validant formules, classes, agrégation mensuelle

### Integration Verification

IV1: Vérifier que les labels sont alignés avec features (même arrondissement, même période)

IV2: Vérifier que le calcul évite double comptage (utilise seulement casualties événements)

IV3: Vérifier que les classes sont bien définies et non ambiguës

---

## Story 1.8: Événements Graves Modulables avec Caractéristiques

As a **système de simulation**,  
I want **générer événements graves (Accident, Incendie, Agression) avec caractéristiques probabilistes**,  
so that **la complexité nécessaire pour éviter que ML comprenne trop facilement est présente**.

### Acceptance Criteria

1. Classes événements graves implémentées: `AccidentGrave`, `IncendieGrave`, `AgressionGrave` héritant de `EventGrave`
2. Caractéristiques probabilistes: Traffic slowdown (70% prob, ×2 temps, 4j, radius 2), Cancel sports (30% prob, 2j), Increase bad vectors (50% prob, +30%, 5j, radius 3), Kill pompier (5% prob)
3. Influence ligne temporelle: Augmente stress long-terme, pattern court-terme, force transitions régimes
4. Durée d'effet: 3-10 jours (aléatoire)
5. Propagation spatiale: Part d'une microzone, pattern droite/gauche, gravité diminue avec distance
6. Tests unitaires validant génération caractéristiques, effets temporels/spatiaux, durée

### Integration Verification

IV1: Vérifier que les événements graves modifient bien les vecteurs journaliers (augmentation)

IV2: Vérifier que les caractéristiques probabilistes sont appliquées correctement (probabilités respectées)

IV3: Vérifier que les effets se propagent spatialement et temporellement comme défini

---

## Story 1.9: Événements Positifs et Règle Prix m²

As a **système de simulation**,  
I want **générer événements positifs et appliquer règle prix m² pour modulation agressions**,  
so that **le système reflète la réalité (travaux, nouvelles casernes) et corrélations socio-économiques**.

### Acceptance Criteria

1. Événements positifs implémentés: Fin travaux, nouvelle caserne, amélioration matériel
2. Effets événements positifs: Modification matrices transition en mieux (réduction intensités, amélioration transitions)
3. Règle prix m²: Division probabilité agression: `prob_agression_modulée = prob_agression_base / facteur_prix_m2`
4. Règle prix m²: Diminution probabilités régimes (Prix m² élevé → probabilités Détérioration/Crise réduites)
5. Facteur prix m²: `facteur_prix_m2 = prix_m2_microzone / prix_m2_moyen_paris`
6. Données prix m² par microzone (statiques, à définir/charger)
7. Tests unitaires validant effets événements positifs, modulation agressions, diminution régimes

### Integration Verification

IV1: Vérifier que les événements positifs annulent bien événements négatifs (si défini)

IV2: Vérifier que la règle prix m² modifie bien probabilités agressions et régimes

IV3: Vérifier que les données prix m² sont chargées correctement (format, valeurs)

---

## Story 1.10: Trois Matrices de Modulation (Gravité, Croisée, Voisins)

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

## Story 1.11: Vecteurs Statiques et Interface Patterns Paris

As a **système de simulation**,  
I want **implémenter vecteurs statiques (3×3 par microzone) comme interface patterns Paris → modèle**,  
so that **les patterns Paris peuvent influencer régimes ET intensités**.

### Acceptance Criteria

1. Vecteurs statiques implémentés: 3 vecteurs (agressions, incendies, accidents) × 3 valeurs (bénin, moyen, grave) par microzone
2. Influence sur régimes: Vecteurs statiques modifient probabilités régimes (Stable/Détérioration/Crise)
3. Influence sur intensités: Vecteurs statiques modifient intensités λ_base(τ,g)
4. Interface patterns Paris → modèle: Lecture depuis fichiers patterns, application aux vecteurs statiques
5. Données patterns Paris par microzone (statiques, à définir/charger)
6. Tests unitaires validant influence régimes, influence intensités, lecture patterns

### Integration Verification

IV1: Vérifier que les vecteurs statiques sont chargés correctement (format, valeurs par microzone)

IV2: Vérifier que l'influence sur régimes et intensités est appliquée correctement

IV3: Vérifier que l'interface patterns Paris fonctionne (lecture fichiers, application)

---

## Story 1.12: Préparation Données ML - Fenêtres Glissantes

As a **système ML**,  
I want **préparer données ML avec fenêtres glissantes (4 semaines consécutives) et arrondissements adjacents**,  
so that **les modèles peuvent être entraînés sur format correct**.

### Acceptance Criteria

1. Fenêtres glissantes implémentées: 4 semaines consécutives par arrondissement
2. Arrondissements adjacents: Arrondissement central + 4 autour = 5 × 18 features = 90 features
3. Tableau statique arrondissements adjacents créé (format à définir: CSV, JSON, dict Python)
4. DataFrame final pour ML: 90 colonnes (features) + 1 colonne label (score ou classe)
5. Workflow: 2 parties - Run qui crée tout (features hebdo + labels), puis 5 runs puis 49 runs supplémentaires
6. Limitation: Seulement 4 semaines précédentes de l'arrondissement (pas toutes semaines, pas tout Paris)
7. Tests unitaires validant fenêtres glissantes, arrondissements adjacents, format DataFrame

### Integration Verification

IV1: Vérifier que les fenêtres glissantes sont créées correctement (4 semaines consécutives)

IV2: Vérifier que les arrondissements adjacents sont corrects (géographiquement adjacents)

IV3: Vérifier que le DataFrame final est dans format utilisable pour scikit-learn (pas de NaN, types numériques)

---

## Story 1.13: Entraînement Modèles ML - Régression et Classification

As a **système ML**,  
I want **entraîner 4 modèles ML (2 régression, 2 classification) sur données préparées**,  
so that **des prédictions peuvent être faites avec interprétabilité**.

### Acceptance Criteria

1. 2 modèles régression implémentés (algorithmes à définir, RandomForest probable)
2. 2 modèles classification implémentés (algorithmes à définir)
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

## Story 1.14: SHAP Values pour Interprétabilité

As a **utilisateur décideur**,  
I want **voir SHAP values pour comprendre importance des 18 features**,  
so that **je peux faire confiance aux prédictions et comprendre les facteurs de risque**.

### Acceptance Criteria

1. Calcul SHAP values pour chaque modèle entraîné (régression et classification)
2. Importance des 18 features affichée (graphiques SHAP, summary plots)
3. Intégration SHAP dans workflow ML (calcul après entraînement)
4. Sauvegarde SHAP values avec modèles (optionnel, peut être recalculé)
5. Visualisation SHAP dans interface Streamlit (Story 1.16)
6. Tests unitaires validant calcul SHAP, format valeurs, visualisation

### Integration Verification

IV1: Vérifier que SHAP peut être calculé pour tous modèles (compatibilité)

IV2: Vérifier que les SHAP values sont cohérentes (importance features logique)

IV3: Vérifier que la visualisation SHAP fonctionne dans Streamlit

---

## Story 1.15: Interface Streamlit - Layout et Contrôles de Base

As a **utilisateur**,  
I want **une interface web Streamlit avec layout défini (carte centre, colonnes gauche/droite, bandeaux)**,  
so that **je peux interagir avec le système de simulation**.

### Acceptance Criteria

1. Application Streamlit créée dans `src/ui/web_app.py`
2. Layout 3 colonnes: Liste événements/incidents (gauche), Carte Paris (centre), Liste arrondissements (droite)
3. Bandeau haut: Sélections (jours, scénario, variabilité, type ML, nombre runs)
4. Bandeau bas: [Lancer], Jours X/Total, Run 1/50, [Stop]
5. Widgets Streamlit: selectbox (scénario, variabilité, type ML), slider (jours, runs), button (Lancer, Stop)
6. Intégration carte Folium dans Streamlit (via `st.components.v1.html()` ou `folium_static()`)
7. Codes couleur: Feu (Jaune/Orange/Rouge), Accident (Beige/Marron), Agression (Gris)
8. Tests manuels validant layout, widgets, intégration carte

### Integration Verification

IV1: Vérifier que Streamlit peut être lancé (`streamlit run src/ui/web_app.py`)

IV2: Vérifier que la carte Folium s'affiche correctement dans Streamlit

IV3: Vérifier que les widgets fonctionnent (sélections, boutons)

---

## Story 1.16: Interface Streamlit - Simulation et Visualisation

As a **utilisateur**,  
I want **lancer simulation et voir progression en temps réel avec visualisations**,  
so that **je peux suivre l'évolution des risques et analyser les résultats**.

### Acceptance Criteria

1. Bouton [Lancer] démarre simulation avec paramètres sélectionnés
2. Progression affichée: Jours simulés/Total, Run X/50, avec vitesse 1 jour = 0.33s
3. Carte Paris mise à jour en temps réel: Événements affichés avec codes couleur, couleurs changeantes selon gravité
4. Colonne gauche: Liste événements/incidents cliquable → détails (popup/modal)
5. Colonne droite: Rectangles arrondissements avec évolution temporelle, cliquable → graphiques détaillés (popup/modal)
6. Priorité affichage: Plus grave → Feu > Agression > Accident
7. Bouton [Stop] interrompt simulation et sauvegarde état
8. Tests manuels validant simulation, progression, visualisations, interactions

### Integration Verification

IV1: Vérifier que la simulation peut être lancée et s'exécute correctement (pas d'erreurs)

IV2: Vérifier que la progression est mise à jour en temps réel (Streamlit rerun)

IV3: Vérifier que les visualisations sont correctes (carte, graphiques, codes couleur)

---

## Story 1.17: Interface Streamlit - ML et Modèles Sauvegardés

As a **utilisateur**,  
I want **entraîner modèles ML et charger modèles sauvegardés pour prédiction**,  
so that **je peux utiliser le système pour prédictions réelles**.

### Acceptance Criteria

1. Ligne supérieure: Checkbox "Train a model" → choix type ML → sélection 2 modèles (sur 4)
2. Ligne inférieure: Bouton radio "Use a prediction model" → chargement depuis `models/classification/` ou `models/regression/`
3. Métadonnées modèles affichées: Nom, numéro entraînement, jours, accuracy
4. Entraînement modèles depuis interface (bouton "Entraîner" après sélection)
5. Affichage métriques après entraînement (MAE, RMSE, R² ou Accuracy, Precision, Recall, F1)
6. Affichage SHAP values après entraînement (graphiques)
7. Utilisation modèle chargé pour prédiction sur nouvelles données
8. Tests manuels validant entraînement, chargement, prédiction, visualisations

### Integration Verification

IV1: Vérifier que l'entraînement depuis interface fonctionne (pas d'erreurs, modèles sauvegardés)

IV2: Vérifier que le chargement modèles fonctionne (liste fichiers, métadonnées affichées)

IV3: Vérifier que les prédictions avec modèle chargé fonctionnent (format, valeurs cohérentes)

---

## Story 1.18: Sauvegarde/Reprise État Simulation et Export

As a **utilisateur**,  
I want **sauvegarder état simulation et exporter résultats partiels**,  
so that **je peux interrompre et reprendre, ou analyser résultats hors ligne**.

### Acceptance Criteria

1. Sauvegarde état simulation: Vecteurs, événements, variables cachées (stress, patterns, régimes)
2. Format sauvegarde: Pickle dans `data/intermediate/` avec timestamp
3. Reprise après interruption: Chargement état sauvegardé, reprise simulation depuis point sauvegarde
4. Export résultats partiels: DataFrame features, DataFrame labels, modèles ML
5. Export formats: CSV (features/labels), joblib (modèles), HTML (cartes)
6. Bouton [Stop] sauvegarde automatiquement état avant interruption
7. Tests unitaires validant sauvegarde, chargement, export, reprise

### Integration Verification

IV1: Vérifier que la sauvegarde fonctionne (fichiers créés, format correct)

IV2: Vérifier que la reprise fonctionne (chargement, continuation simulation)

IV3: Vérifier que les exports sont utilisables (CSV lisible, modèles rechargeables)

---

## Story 1.19: Validation et Tests de Cohérence

As a **développeur/QA**,  
I want **valider cohérence données et patterns avec tests automatisés**,  
so that **le système génère des données réalistes et cohérentes**.

### Acceptance Criteria

1. Tests validation cohérence données: Si 0 morts ou < 2 morts sur arrondissement sur 400 jours → alerte, si > 200 morts → alerte
2. Tests validation patterns: Vérifier qu'il n'y a pas de packaging (regroupement dans une direction)
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

## Story 1.20: Documentation Technique et Utilisateur

As a **développeur/utilisateur**,  
I want **documentation technique complète et guide utilisateur**,  
so that **le système peut être maintenu et utilisé efficacement**.

### Acceptance Criteria

1. README.md mis à jour: Installation, démarrage, structure projet, dépendances
2. Documentation architecture: `docs/architecture.md` avec structure, composants, flux données
3. Documentation formules mathématiques: Modèle Zero-Inflated Poisson, Golden Hour, features, labels (dans code ou docs/)
4. Guide utilisateur: Instructions interface Streamlit, paramètres, interprétation résultats
5. Docstrings Python: Toutes fonctions/classes publiques avec descriptions, paramètres, retours
6. Commentaires code: Algorithmes complexes (formules, calculs) expliqués
7. Documentation patterns: Format fichiers patterns (CSV/JSON/YAML), exemples
8. Documentation modèles ML: Format sauvegarde, métadonnées, utilisation

### Integration Verification

IV1: Vérifier que la documentation est complète (tous composants documentés)

IV2: Vérifier que la documentation est à jour (correspond au code)

IV3: Vérifier que la documentation est utilisable (instructions claires, exemples)

---

**Fin du PRD**
