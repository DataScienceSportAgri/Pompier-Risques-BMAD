# Résumé de la Réorganisation des Stories

**Date** : 28 Janvier 2026  
**Version** : 2.0

---

## Modifications Majeures Effectuées

### Epic 1 - Pré-calculs

#### Story 1.3 (Modifiée)
- ✅ **Ajout pré-calcul congestion statique de base** : Table de congestion statique (facteurs statiques : saisonnalité, caractéristiques microzone)
- ✅ **Saisonnalité** : Implémentée dès le début dans pré-calculs pour influencer matrices de génération
- ✅ **Format pickle standardisé** : Mentionné pour faciliter chargement/lecture

#### Story 1.4 (Nouvelle)
- ✅ **Fichier de référence patterns Paris** : Document définissant format exact des fichiers patterns JSON

---

### Epic 2 - Bloc 2.1 (Infra)

#### Story 2.1.2 (Nouvelle)
- ✅ **Structure SimulationState** : Création SimulationState avec domaines spécialisés (VectorsState, EventsState, CasualtiesState, RegimeState)

#### Story 2.1.3 (Nouvelle)
- ✅ **Validation config Pydantic** : Schéma Pydantic pour validation configuration YAML

#### Story 2.1.4 (Nouvelle)
- ✅ **Système centralisé chemins** : Convention de nommage et résolution chemins centralisée
- ✅ **Format pickle standardisé** : Structure standardisée pour tous les fichiers pickle

---

### Epic 2 - Bloc 2.2 (Génération)

#### Ordre Réorganisé
**Nouvel ordre** : 2.2.1 (vecteurs) → 2.2.2 (patterns) → **2.2.9** (matrices) → **2.2.10** (vecteurs statiques) → **2.2.2.5** (congestion) → 2.2.3 (Golden Hour) → 2.2.4 (morts/blessés) → 2.2.5 (features) → 2.2.6 (labels) → 2.2.7 (événements graves) → 2.2.8 (événements positifs)

#### Story 2.2.2.5 (Modifiée)
- ✅ **Congestion statique pré-calculée** : Utilisation congestion statique (Story 1.3) comme base
- ✅ **Modifications temps réel** : Événements graves modifient congestion du jour en temps réel
- ✅ **Ordre** : Calculée après vecteurs, avant Golden Hour

#### Story 2.2.3 (Modifiée)
- ✅ **Golden Hour avec tirage au sort** : Pas de multiplication par 1.3, tirage au sort selon probabilité
- ✅ **Système suivi interventions** : Table permanente staff par caserne, retrait/remise progressive
- ✅ **Caserne disponible** : Calcul caserne la plus proche disponible (staff suffisant)
- ✅ **Hôpital le plus proche** : Systématiquement le plus proche

#### Story 2.2.4 (Modifiée)
- ✅ **Vecteurs normaux + événements** : Calcul morts/blessés à partir vecteurs normaux + événements
- ✅ **Golden Hour tirage au sort** : Utilisation tirage au sort selon probabilité (pas ×1.3)

#### Story 2.2.5 (Modifiée)
- ✅ **144 features pour ML** : Clarification structure (1 central dernière semaine + 4 voisins 4 semaines + 1 central 3 semaines précédentes)
- ⚠️ **À clarifier** : Calcul exact pour obtenir 144 (voir QUESTIONS-CLARIFICATIONS.md)

#### Story 2.2.6 (Modifiée)
- ✅ **Mois glissant** : Mois qui se décale à chaque fois qu'on passe un mois
- ✅ **Correspondance features** : 3 semaines des voisins avant la dernière semaine

#### Story 2.2.7 (Modifiée)
- ✅ **Modification congestion temps réel** : Événements graves modifient congestion du jour en temps réel

#### Story 2.2.8 (Modifiée)
- ✅ **Génération après vecteurs** : Événements positifs générés après vecteurs, impact sur J+1

#### Story 2.2.9 (Modifiée)
- ✅ **Modulations dynamiques** : Les trois matrices sont modulées en temps réel par événements, incidents, régimes, patterns

---

### Epic 2 - Bloc 2.3 (ML)

#### Story 2.3.1 (Modifiée)
- ✅ **144 features** : Structure modifiée (1 central dernière semaine + 4 voisins 4 semaines + 1 central 3 semaines précédentes)
- ✅ **DataFrame géant 50 runs** : Concaténation DataFrames (pas d'agrégation statique)
- ✅ **Parallélisation** : 49 runs peuvent être lancés en parallèle
- ⚠️ **À clarifier** : Calcul exact pour obtenir 144 (voir QUESTIONS-CLARIFICATIONS.md)

---

### Epic 2 - Bloc 2.4 (UI)

#### Story 2.4.3 (Modifiée)
- ✅ **Multiprocessing** : 49 runs en parallèle sans bloquer UI Streamlit
- ✅ **Thread séparé** : Mise à jour temps réel via thread séparé
- ✅ **Barre progression 49 runs** : Barre de progression avec pourcentage
- ✅ **Stop dernière itération** : Stop fait la dernière itération journalière puis arrête

#### Story 2.4.5 (Modifiée)
- ✅ **Deux types sauvegarde** : ML finale vs sauvegarde en cours (interruption)
- ✅ **Format pickle standardisé** : Pour les deux types de sauvegarde

---

### Epic 2 - Bloc 2.5 (Qualité)

#### Story 2.5.1 (Modifiée)
- ✅ **Tests validation automatiques** : Exécutés automatiquement après chaque run

#### Story 2.5.3 (Nouvelle)
- ✅ **Tests d'intégration** : Story dédiée pour tests workflow complet

#### Story 2.5.4 (Nouvelle)
- ✅ **Benchmarks automatisés** : Validation performance ≤ 0.33 s/jour

---

## Questions Restantes

Voir `QUESTIONS-CLARIFICATIONS.md` pour les questions nécessitant clarification avec le PO :
1. Structure exacte 144 features
2. Correspondance features/labels
3. Format pickle standardisé (structure exacte)
4. Format patterns JSON (structure exacte)

---

## Stories Créées/Modifiées

### Nouvelles Stories
- 1.4 - Fichier de référence patterns Paris
- 2.1.2 - Structure SimulationState
- 2.1.3 - Validation config Pydantic
- 2.1.4 - Système centralisé chemins
- 2.5.3 - Tests d'intégration
- 2.5.4 - Benchmarks performance

### Stories Modifiées
- 1.3 - Ajout congestion statique
- 2.2.2.5 - Congestion dynamique avec base statique
- 2.2.3 - Golden Hour tirage au sort + suivi interventions
- 2.2.4 - Vecteurs normaux + événements
- 2.2.5 - 144 features
- 2.2.6 - Mois glissant
- 2.2.7 - Modification congestion temps réel
- 2.2.8 - Génération après vecteurs
- 2.2.9 - Modulations dynamiques
- 2.3.1 - 144 features + DataFrame géant
- 2.4.3 - Multiprocessing + thread séparé
- 2.4.5 - Deux types sauvegarde
- 2.5.1 - Tests automatiques

---

**Total** : 6 nouvelles stories + 13 stories modifiées = 19 stories impactées
