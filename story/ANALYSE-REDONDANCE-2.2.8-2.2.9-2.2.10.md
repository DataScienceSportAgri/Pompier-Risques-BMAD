# Analyse de Redondance : Stories 2.2.8, 2.2.9, 2.2.10 vs Phase 1

**Date :** 29 Janvier 2026  
**Auteur :** Analyse comparative  
**Objectif :** Clarifier si les stories 2.2.8, 2.2.9, 2.2.10 sont redondantes avec la fin de la Story 1, ou s'il s'agit de l'implémentation réelle des concepts testés en Phase 1.

---

## 🎯 Résumé Exécutif

**Conclusion :** Il y a **partiellement redondance conceptuelle**, mais les stories 2.2.8, 2.2.9, 2.2.10 représentent **l'implémentation complète et intégrée** dans le moteur de simulation, alors que la Phase 1 a créé les **données pré-calculées** et les **composants de base**.

### Distinction Clé

- **Phase 1 (Epic 1)** : Pré-calculs et composants de base (données + fonctions isolées)
- **Phase 2 (Epic 2)** : Intégration complète dans le moteur de simulation avec toutes les interactions

---

## 📊 Analyse Détaillée par Story

### Story 2.2.8 : Événements positifs et règle prix m²

#### Ce qui a été fait en Phase 1
- **Story 1.3** : Pré-calcul du prix m² → `data/source_data/prix_m2.pkl`
- **Story 1.3** : Pré-calcul des vecteurs statiques → `data/source_data/vecteurs_statiques.pkl`

#### Ce qui reste à faire (Story 2.2.8)
- ✅ **Implémentation événements positifs** : Fin travaux, Nouvelle caserne, Amélioration matériel
- ✅ **Génération événements positifs** : Début de journée, avant vecteurs (impact sur vecteurs J+1)
- ✅ **Effets événements positifs** : Réduction intensités, amélioration transitions
- ✅ **Application règle prix m²** : `prob_agression_modulée = prob_agression_base / facteur_prix_m2`
- ✅ **Diminution probabilités régimes** : Si prix m² élevé → diminution Détérioration/Crise

#### Verdict : **NON REDONDANT**
- Phase 1 : Données pré-calculées (prix m², vecteurs statiques)
- Story 2.2.8 : **Utilisation** de ces données dans le moteur de simulation + événements positifs (nouveau concept)

---

### Story 2.2.9 : Trois matrices de modulation (gravité, croisée, voisins)

#### Ce qui a été fait en Phase 1
- **Story 1.4.4.1** : Pré-calcul des matrices fixes → `matrices_correlation_intra_type.pkl`, `matrices_correlation_inter_type.pkl`, `matrices_voisin.pkl`
- **Story 1.4.4.3** : Application des matrices fixes dans `calculer_probabilite_incidents_J1()` → fonctions `apply_intra_type`, `apply_inter_type`, `apply_voisin`

#### Ce qui reste à faire (Story 2.2.9)
- ✅ **Matrice gravité microzone** : Même type, même microzone, historique 7 jours avec décroissance exponentielle
- ✅ **Matrice types croisés** : Autres types, même microzone, corrélations spécifiques
- ✅ **Matrice voisins** : 8 zones alentours (radius 1), pondération grave×1.0, moyen×0.5, bénin×0.2
- ✅ **Modulations dynamiques** : Les trois matrices sont modulées en temps réel par :
  - Événements (graves/positifs)
  - Incidents (accidents, incendies, agressions)
  - Régimes (Stable/Détérioration/Crise)
  - Patterns (4j, 7j, 60j)
- ✅ **Intégration dans formule** : `λ_calibrated = λ_base × facteur_statique × facteur_gravité × facteur_croisé × facteur_voisins × facteur_long`
- ✅ **Normalisation** : `Z(t) = Σ_{τ,g} λ_calibrated(τ,g)`
- ✅ **Caps** : Min ×0.1, Max ×3.0

#### Verdict : **PARTIELLEMENT REDONDANT, MAIS EXTENSION IMPORTANTE**

**Redondance :**
- Les concepts de base (intra-type, inter-type, voisin) sont déjà implémentés dans 1.4.4.3

**Différences clés (Story 2.2.9 apporte) :**
1. **Modulations dynamiques** : Les matrices sont modulées en temps réel par événements, incidents, régimes, patterns (pas dans 1.4.4.3)
2. **Formule complète** : Intégration dans `λ_calibrated` avec tous les facteurs (statique, gravité, croisé, voisins, long terme)
3. **Normalisation et caps** : Contrôles de cohérence (pas dans 1.4.4.3)
4. **Historique 7 jours** : Matrice gravité utilise historique 7 jours avec décroissance exponentielle (plus sophistiqué que 1.4.4.3)

**Recommandation :**
- **Option A** : Fusionner 2.2.9 avec 1.4.4.3 (étendre 1.4.4.3 pour inclure modulations dynamiques, normalisation, caps)
- **Option B** : Garder 2.2.9 comme story séparée mais clarifier qu'elle **étend** 1.4.4.3 avec les modulations dynamiques

---

### Story 2.2.10 : Vecteurs statiques et interface patterns Paris

#### Ce qui a été fait en Phase 1
- **Story 1.3** : Pré-calcul des vecteurs statiques → `data/source_data/vecteurs_statiques.pkl`
- **Story 1.3** : Interface patterns Paris → lecture depuis `data/patterns/` (pattern_4j, pattern_7j, pattern_60j)
- **Story 1.4.4.6** : Application des patterns dans le calcul des probabilités

#### Ce qui reste à faire (Story 2.2.10)
- ✅ **Chargement vecteurs statiques** : Depuis `data/source_data/` (pré-calculés Epic 1, Story 1.3)
- ✅ **Structure vecteurs statiques** : 3×3 par microzone (3 types × 3 gravités)
- ✅ **Influence sur régimes** : Modification probabilités régimes (Stable/Détérioration/Crise)
- ✅ **Influence sur intensités** : Modification `λ_base(τ,g)`
- ✅ **Interface patterns Paris** : Lecture `data/patterns/`, application

#### Verdict : **REDONDANT AVEC 1.4.4.6**

**Redondance :**
- Les vecteurs statiques sont déjà pré-calculés (Story 1.3)
- Les patterns sont déjà appliqués dans le calcul des probabilités (Story 1.4.4.6)
- L'interface patterns Paris est déjà implémentée (Story 1.3)

**Différences potentielles :**
- Story 2.2.10 mentionne "influence sur régimes" et "influence sur intensités" → mais ces concepts sont déjà dans 1.4.4.6 (application patterns)

**Recommandation :**
- ✅ **CLARIFIÉE** : Story 2.2.10 a un rôle unique :
  - Utilisation des vecteurs statiques pour calculer les **intensités de base** λ_base(τ,g) (point de départ)
  - Influence des vecteurs statiques sur les **probabilités des régimes cachés** (Stable/Détérioration/Crise)
- **Distinction** : 1.3 = pré-calcul (données), 2.2.10 = utilisation (intensités de base + régimes), 1.4.4.6 = patterns dynamiques (après modulations)

---

## 🔄 Vue d'Ensemble : Flux de Données

### Phase 1 (Epic 1) : Pré-calculs
```
Données brutes
    ↓
Scripts de pré-calcul
    ↓
Pickle files dans data/source_data/
    ├── prix_m2.pkl
    ├── vecteurs_statiques.pkl
    ├── matrices_correlation_intra_type.pkl
    ├── matrices_correlation_inter_type.pkl
    ├── matrices_voisin.pkl
    └── ...
```

### Phase 2 (Epic 2) : Simulation
```
Chargement données pré-calculées
    ↓
Moteur de simulation
    ├── Story 1.4.4.3 : Application matrices fixes
    ├── Story 1.4.4.4 : Intégration variables d'état
    ├── Story 1.4.4.6 : Application patterns
    ├── Story 2.2.8 : Événements positifs + prix m²
    ├── Story 2.2.9 : Modulations dynamiques matrices
    └── Story 2.2.10 : Intensités de base + régimes (depuis vecteurs statiques)
```

---

## ✅ Recommandations

### 1. Story 2.2.8 : **GARDER** (non redondant)
- Utilise les données pré-calculées (prix m², vecteurs statiques)
- Ajoute les événements positifs (nouveau concept)
- Application de la règle prix m² dans le moteur de simulation

### 2. Story 2.2.9 : **CLARIFIER OU FUSIONNER**
- **Option A (Recommandée)** : Fusionner avec 1.4.4.3
  - Étendre `calculer_probabilite_incidents_J1()` pour inclure :
    - Modulations dynamiques (événements, incidents, régimes, patterns)
    - Normalisation `Z(t)`
    - Caps (Min ×0.1, Max ×3.0)
    - Historique 7 jours pour matrice gravité
- **Option B** : Garder séparée mais clarifier qu'elle **étend** 1.4.4.3

### 3. Story 2.2.10 : **CLARIFIÉE** ✅
- **Rôle unique identifié** :
  - Utilisation des vecteurs statiques comme **point de départ** pour calculer les intensités de base λ_base(τ,g)
  - Influence des vecteurs statiques sur les **probabilités des régimes cachés** (Stable/Détérioration/Crise)
- **Distinction claire** :
  - Story 1.3 : **Pré-calcul** des vecteurs statiques (données)
  - Story 2.2.10 : **Utilisation** des vecteurs statiques dans le moteur (intensités de base + régimes)
  - Story 1.4.4.6 : Application des **patterns dynamiques** sur probabilités déjà modulées
  - Story 2.2.10 : Fournit les **intensités de base** utilisées **avant** les modulations (matrices, variables, patterns)
- **Verdict** : **NON REDONDANT** - Rôle unique et nécessaire

---

## 📋 Actions Proposées

1. ✅ **Story 2.2.10 clarifiée** : Rôle unique identifié (intensités de base + régimes)
2. **Valider avec l'équipe** : Les recommandations pour Story 2.2.9
3. **Fusionner 2.2.9 avec 1.4.4.3** (optionnel) : Étendre l'application des matrices avec modulations dynamiques
4. **Mettre à jour la documentation** : Clarifier le flux Phase 1 → Phase 2

---

## 🔍 Questions pour Clarification

1. **Story 2.2.9** : Les "modulations dynamiques" sont-elles vraiment différentes de l'application des matrices dans 1.4.4.3, ou est-ce une extension naturelle ?
2. ✅ **Story 2.2.10** : **CLARIFIÉE** - Rôle unique identifié (intensités de base + régimes)
3. **Ordre d'implémentation** : Les stories 2.2.8, 2.2.9, 2.2.10 doivent-elles être implémentées **après** 1.4.4.3, 1.4.4.4, 1.4.4.6, ou en parallèle ?

---

**Document créé le :** 29 Janvier 2026  
**Version :** 1.0
