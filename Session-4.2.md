# 📋 SESSION 4.2 - VALIDATIONS, PROGRESSION & SAUVEGARDES
## Échange 4.2 - Interface Streamlit : Validations, Affichage, Sauvegardes

**Date:** 25 Janvier 2026  
**Statut:** ✅ Complété  
**Contexte:** Suite Session 4.1 (Interface & Modes)

---

# 🎯 RÉSUMÉ EXÉCUTIF

Définition des mécanismes de validation, d'affichage de progression et de sauvegarde pour l'interface Streamlit. Interface modèles ML structurée, affichage temps réel avec codes couleur, vitesse simulation fixée, sauvegardes état et modèles.

---

# ✅ DÉCISIONS PRISES

## 4. Validations & Feedback Inputs

### Validations Minimales
- ✅ **Message d'erreur** si paramètres invalides (nécessaire)
- ❌ Validation proactive des paramètres (pas nécessaire)
- ✅ **Confirmation relance simulation** après 2 ans (warning affiché)
- ❌ Avertissement modèle non entraîné (pas nécessaire, interface gère automatiquement)

### Interface Modèles ML (Position: Haut droite)

**Ligne Supérieure - Mode Entraînement:**
```
[☐ Train a model]
  └─ Si coché:
     ├─ Choix type ML: [Classification] [Régression]
     └─ Menu sélection: 2 modèles ML (sur 4 disponibles)
        - Utilisateur voit les 2 plus intelligents
        - Phase 2: réglage hyperparamètres
```

**Ligne Inférieure - Mode Prédiction:**
```
(○) Use a prediction model
  └─ Choix: [Classification] OU [Régression]
     └─ Chargement depuis fichiers:
        - models/classification/ (fichiers modèles classification)
        - models/regression/ (fichiers modèles régression)
```

**Métadonnées Modèles Sauvegardés:**
Chaque modèle contient:
- Nom modèle ML utilisé (ex: RandomForest, XGBoost)
- Numéro entraînement (ID unique)
- Nombre jours d'entraînement
- Accuracy au moment entraînement

---

## 5. Affichage Progression Simulation

### Affichage Essentiel
- ✅ **Jours simulés / Total** (ex: "Jour 45 / 90") - **IMPORTANT**
- ⚠️ Barre de progression: pas super utile MVP
- ⚠️ Indicateur temps restant: pour plus tard (Phase 2)

### Notifications Événements
- ✅ **Pop-up événements majeurs** (incidents graves + events majeurs)
- ✅ **Icônes sur carte** pour incidents graves et événements
  - Type incident (accident, feu, agression)
  - Microzone concernée
  - Type événement, type incident, conséquences

### Colonne Gauche - Liste Événements
- ✅ **Colonne gauche**: liste événements/incidents qui s'ajoutent pendant simulation
  - Utilisateur peut analyser cette colonne
  - Caractéristiques des éléments affichées
  - Historique complet de la simulation

### Vitesse Simulation
- ✅ **1 jour = 1/3 seconde** (0.33s par jour)
  - Carte change en temps réel avec événements
  - Jours évoluent visuellement
  - Animation fluide des microzones

### Codes Couleur Carte

**Feu (Incendies):**
- 🟡 Jaune → Bénin
- 🟠 Orange → Moyen
- 🔴 Rouge → Grave

**Accident:**
- 🟤 Beige clair → Bénin
- 🟤 Marron clair → Moyen
- 🟤 Marron foncé → Grave

**Agression:**
- ⚪ Gris clair → Bénin
- ⚫ Gris moyen → Moyen
- ⬛ Gris très foncé → Grave

### Priorité Affichage Carte
1. **Vecteur avec nombre le plus élevé** (plus grave)
2. Si même niveau gravité: **Feu > Agression > Accident**

### Carte Découpage
- ✅ **100 microzones** visibles sur carte
- Chercher carte existante (arrondissements découpés en ~100 microzones)
- Si n'existe pas: créer nous-mêmes

---

## 6. Interruption & Sauvegardes

### Fonctionnalités
- ✅ **Interrompre simulation** (bouton pause/stop)
- ✅ **Sauvegarder état complet**:
  - Vecteurs jour-à-jour
  - Événements majeurs
  - Variables cachées (fatigue, congestion)
  - Jour actuel
- ✅ **Export résultats partiels** (dans frame pause)
  - CSV données générées jusqu'à interruption
  - État simulation (reprise possible)

### Sauvegarde Modèles ML
- ✅ **Sauvegarde automatique** modèles entraînés
- Format: joblib/pickle
- Emplacement: `models/classification/` ou `models/regression/`
- Métadonnées incluses (nom, numéro, jours, accuracy)

---

# 📊 RÉSUMÉ MANUSCRIT (6 lignes)

1. **Validations inputs minimales** : message d'erreur si paramètres invalides, confirmation relance après 2 ans (warning). Interface modèles ML en haut droite : ligne supérieure checkbox "Train a model" avec choix type ML (classification/régression) et sélection 2 modèles parmi 4 (les plus intelligents), ligne inférieure bouton radio "Use a prediction model" avec chargement depuis fichiers `models/classification/` ou `models/regression/` contenant nom modèle, numéro entraînement, jours d'entraînement, accuracy.

2. **Affichage progression simplifié** : jours simulés/total (important), pas de barre de progression ni temps restant MVP. Pop-up + icônes carte pour événements majeurs et incidents graves (type, microzone, conséquences). Colonne gauche liste événements/incidents s'ajoutant pendant simulation avec caractéristiques analysables.

3. **Vitesse simulation 1 jour = 1/3 seconde** : carte mise à jour en temps réel, jours évoluent visuellement, codes couleur par type incident (feu: jaune/orange/rouge, accident: beige/marron clair/foncé, agression: gris clair/moyen/foncé) selon gravité vecteur, priorité affichage: plus grave d'abord, puis si égalité Feu > Agression > Accident.

4. **Carte découpage 100 microzones** : chercher carte existante arrondissements découpés, sinon créer nous-mêmes. Affichage microzones avec codes couleur selon incidents en cours, icônes événements majeurs positionnées géographiquement.

5. **Interruption & sauvegardes** : possibilité interrompre simulation, sauvegarder état complet (vecteurs, événements, variables cachées), export résultats partiels dans frame pause. Modèles ML sauvegardés automatiquement avec métadonnées (nom, numéro, jours, accuracy).

6. **Session 4.2 fixe interface Streamlit complète** : validations minimales, progression temps réel avec pop-ups et colonne événements, vitesse 0.33s/jour, codes couleur par type/gravité, priorité affichage, sauvegardes état et modèles. Report Session 4.3 : outputs/visualisations détaillées, heatmap interactivité, format CSV Phase 2, roadmap évolutions UI.

---

# 🔗 LIENS AVEC SESSIONS PRÉCÉDENTES

## Depuis Session 3
- ✅ Vitesse simulation compatible avec durée max 10,000 jours
- ✅ Codes couleur reflètent structure vecteur [grave, moyen, bénin]
- ✅ Priorité affichage respecte logique agrégation arrondissement

## Vers Session 4.3
- ⚠️ Outputs & visualisations complètes à définir
- ⚠️ Heatmap détails (interactivité, filtres)
- ⚠️ Format CSV Phase 2 exact
- ⚠️ Roadmap évolutions UI Phase 2/3

---

**Créé:** 25 Janvier 2026  
**Statut:** ✅ Complété  
**Prochaine étape:** Session 4.3 (Outputs & Visualisations)
