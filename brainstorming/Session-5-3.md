# 🚀 SESSION 5.3 - VISION FUTURE : Détails d'Implémentation
## Questions Techniques Approfondies - Partie 3

**Date:** 26 Janvier 2026  
**Statut:** 🔄 En cours  
**Objectif:** Clarifier détails techniques d'implémentation, structures de données, et priorités

---

# 🎯 RÉPONSES SESSION 5.3

## 1. PRIORISATION ET ROADMAP

### Q3.1 - Ordre d'Implémentation ✅

**Réponse:** Ordre séquentiel défini

**Ordre d'implémentation:**
1. **Vecteurs journaliers** (les 3 vecteurs de base)
2. **Vecteurs alcool/nuit**
3. **Morts et blessés graves** (calcul hebdomadaire)
4. **Features hebdo** (18 features) - calculées à partir de tout ce qui précède

**Note importante:** Golden Hour est dans l'autre sens - il permet de **calculer** les morts et blessés graves, donc il doit être implémenté avant le calcul des morts/blessés.

**ML:** Fait la transition entre **features hebdo** et **labels** (prédiction semaine suivante)

---

### Q3.1.2 - Composants MVP vs Phase 2 ✅

**Réponse:** Tous les composants sont MVP

**MVP:**
- **Tous les composants** qui ont été donnés sont MVP
- **Phase 2:** Ajustement de paramètres, fine-tuning

**Événements modulables:**
- **Nécessaires dès le début** (pas Phase 2)
- **Raison:** La génération de données doit être complexe dès le départ
- Si génération pas complexe → ML prédira ce qu'on a déjà créé (surapprentissage)
- Complexité dans génération = évite partie scraping (peut prendre beaucoup plus de temps que prévu)

---

## 2. DÉTAILS TECHNIQUES D'IMPLÉMENTATION

### Q3.2 - Structure de Données et Stockage ✅

**Réponse:** DataFrame avec instances de classe Vector

**Structure:**
- **DataFrame** pour stocker les vecteurs journaliers par microzone
- **Classe Vector:** Instance avec 3 valeurs (bénin, moyen, grave)
- **Colonnes DataFrame:** Contiennent instances de Vector
- **Colonne supplémentaire:** Type d'incident ("incendie", "accident", "agression")
- **Avantage:** Permet de faire des calculs vectoriels si nécessaire

**Format sauvegarde:**
- **Pickle** pour données intermédiaires (au début)
- Permet de récupérer DataFrame tel quel

---

### Q3.3 - Calculs Golden Hour - Détails ✅

**Réponse:** Génération positions + calculs distances

**Calcul distances casernes ↔ microzones ↔ hôpitaux:**
1. **Générer ou scraper** positions des casernes
2. **Créer 100 casernes** et **10 hôpitaux**
3. **Calcul distance Pythagore** sur carte de Paris pour avoir tous les calculs
4. **Calculer intersections des microzones** (microzones traversées)
5. **Calculer pourcentages** de microzones traversées par trajet

**Tableau dynamique ralentissement trafic:**
- **Tableau de base** utilisé pour calcul
- **Tableau journalier** des microzones permet, via :
  - Tableau fixe des trajets
  - Tableau des états circulation microzones
- **Calculer temps de trajet** avec stress pompiers

**Stress pompiers:**
- **+0.1 stress** = **10% temps trajet en plus**
- **Chaque intervention pompiers:** +0.4 points de stress
- **Pompiers arrêtés:** +0.4 points de stress
- **Moyenne par caserne:** Stress distribué entre nombre de pompiers par caserne
- **~30 pompiers par caserne** (cohérent)
- **100 casernes × 30 = 3000 pompiers** total (simplification avec SMUR, etc.)

**Formule stress:**
```
temps_trajet = temps_base × (1 + stress_caserne × 0.1)
stress_caserne = moyenne(stress_pompiers) / nb_pompiers_caserne
```

---

### Q3.4 - Patterns et Corrélations ✅

**Réponse:** 2 DataFrames mobiles pour patterns

**Implémentation patterns:**
- **2 DataFrames mobiles:**
  1. **DataFrame patterns 7 jours** (hebdomadaires)
  2. **DataFrame patterns 60 jours** (long-terme)
- **Fonctionnalité:** Implémentent les patterns et les lisent depuis un fichier
- **Référence:** PDF "Modèle Prédiction Incidents J+1.pdf" (formules mathématiques complètes)

**Base mathématique (PDF):**
- **Modèle Zero-Inflated Poisson** pour J → J+1
- **Régimes cachés:** Stable, Détérioration, Crise
- **Patterns court-terme:** 7 jours (détection 4+ événements moyens)
- **Patterns long-terme:** 60 jours (accumulation stress avec décroissance hyperbolique)
- **Intensités calibrées** par régime et gravité
- **Matrices de transition** modifiées selon patterns activés

**Ajouts sur cette base:**
1. **Effets des caractéristiques des événements graves** (modulation des intensités)
2. **Calculs proportions journalières nuit/alcool** (Monte-Carlo basé sciences sociales)
3. **Calculs problèmes trafic** (microzone/jour, découlent nombre accidents + hasard)
4. **Modification matrices** en mieux lorsqu'événement positif créé

---

## 3. ÉVÉNEMENTS MODULABLES

### Q3.5 - Implémentation Événements ✅

**Réponse:** Caractéristique de propagation pour commencer

**Pour l'instant (pas les 15 caractéristiques):**
- **Une caractéristique de propagation** qui part d'une microzone
- **Propagation:** Droite, droite, droite, gauche, gauche, gauche, etc. (pattern défini)
- **Nombre de microzones affectées** (progressif)
- **Gravité diminue progressivement** en s'éloignant de la microzone source

**Types de caractéristiques:**
1. **Caractéristique de propagation** (spatiale, diminue avec distance)
2. **Caractéristique d'effet zone globale** (augmente pourcentages globalement)
3. **Caractéristique d'augmentation** (à préciser)

**Structure:**
- Part d'une microzone source
- Se propage selon pattern (droite/gauche)
- Affecte nombre progressif de microzones
- Gravité diminue avec distance

---

## 4. AJOUTS SUR BASE MATHÉMATIQUE

### Q3.6 - Effets Caractéristiques Événements Graves ✅

**Réponse:** Modulation des intensités et matrices

**Intégration:**
- **Sur base du modèle Zero-Inflated Poisson** (PDF)
- **Effets des caractéristiques** des événements graves modulent :
  - Les intensités λ_base(τ,g) par régime
  - Les facteurs long-terme et court-terme
  - Les matrices de transition entre régimes
- **Application:** Lorsqu'événement grave actif → modifier intensités et patterns

---

### Q3.7 - Calculs Proportions Journalières Nuit/Alcool ✅

**Réponse:** Monte-Carlo basé sciences sociales

**Implémentation:**
- **Sur base des vecteurs journaliers** générés par modèle PDF
- **Génération proportions alcool/nuit** via Monte-Carlo hebdomadaire
- **Basé sur études sciences sociales** (comme pour vecteurs de base)
- **Agrégation hebdomadaire** pour features hebdo
- **Corrélations matricielles** entre types d'incidents (incendies nuit → moins accidents)

---

### Q3.8 - Calculs Problèmes Trafic ✅

**Réponse:** Découlent accidents + hasard, effet bénéfique

**Implémentation:**
- **Pour chaque microzone et chaque jour**
- **Calcul problèmes trafic** découlent de :
  - **Nombre d'accidents** dans la microzone
  - **Effet de hasard** (randomité)
- **Effet bénéfique:** Problèmes trafic → **réduisent dangerosité des accidents** (ralentissement = moins graves)
- **Intégration:** Utilisé dans calcul Golden Hour (tableau dynamique ralentissement)

**Formule conceptuelle:**
```
problèmes_trafic_jour = f(nb_accidents_jour, hasard)
dangerosité_accidents = dangerosité_base × (1 - facteur_ralentissement)
```

---

### Q3.9 - Modification Matrices Événements Positifs ✅

**Réponse:** Améliorer matrices lorsqu'événement positif créé

**Implémentation:**
- **Événements positifs** (ex: politique publique, renforts, fin travaux)
- **Modification matrices en mieux:**
  - **Réduire intensités** des incidents
  - **Améliorer transitions** vers régimes moins sévères
  - **Réduire stress long-terme** accumulé
  - **Modifier patterns** (diminuer probabilités incidents)
- **Application:** Lorsqu'événement positif actif → matrices ajustées positivement

---

## 5. RÉSUMÉ ARCHITECTURE TECHNIQUE

### Ordre d'Implémentation Final

1. **Vecteurs journaliers** (3 vecteurs base)
2. **Vecteurs alcool/nuit**
3. **Golden Hour** (calculs distances, stress pompiers)
4. **Morts et blessés graves** (utilise Golden Hour)
5. **Features hebdo** (18 features, utilise tout ce qui précède)
6. **Labels** (score ou classes, utilise morts + blessés)
7. **ML** (transition features hebdo → labels)

### Structure de Données

**Vecteurs:**
- **Classe Vector:** 3 valeurs (bénin, moyen, grave)
- **DataFrame:** Colonnes avec instances Vector + type incident
- **Sauvegarde:** Pickle

**Golden Hour:**
- **Tableaux pré-calculés:** Distances casernes/hôpitaux/microzones
- **Tableau dynamique:** États circulation microzones (journalier)
- **Calcul temps:** Temps_base × (1 + stress × 0.1)

**Stress Pompiers:**
- **30 pompiers par caserne** (3000 total)
- **+0.4 stress** par intervention ou pompiers arrêtés
- **Moyenne par caserne** pour calcul temps trajet

### Patterns (7 et 60 jours)

**DataFrames mobiles:**
- **DataFrame patterns 7 jours:** Patterns hebdomadaires
- **DataFrame patterns 60 jours:** Patterns long-terme
- **Lecture depuis fichier:** Patterns définis et lus automatiquement
- **Base mathématique:** Modèle Zero-Inflated Poisson avec régimes cachés (PDF)

### Ajouts sur Base Mathématique

**1. Effets événements graves:**
- Modulation intensités λ_base(τ,g)
- Modification facteurs long/court-terme
- Ajustement matrices de transition

**2. Proportions nuit/alcool:**
- Monte-Carlo journalier (sciences sociales)
- Agrégation hebdomadaire
- Corrélations matricielles

**3. Problèmes trafic:**
- Calcul microzone/jour
- Découlent accidents + hasard
- Effet bénéfique sur dangerosité accidents

**4. Événements positifs:**
- Modification matrices en mieux
- Réduction intensités
- Amélioration transitions régimes

### Événements Modulables (MVP)

**Caractéristique de propagation:**
- Part d'une microzone source
- Pattern de propagation (droite/gauche alterné)
- Nombre microzones affectées progressif
- Gravité diminue avec distance
- Effet zone globale possible
- Caractéristiques d'augmentation

---

## 6. CORRÉLATIONS ET EFFETS TEMPORELS

### Q3.10 - Gestion Corrélations entre Types d'Incidents ✅

**Réponse:** Matrices de corrélation, facteurs multiplicatifs

**Implémentation:**
- **Matrices de corrélation** entre types d'incidents
- **Facteurs multiplicatifs** pour moduler les intensités
- **Exemple:** Plus d'incendies la nuit → moins d'accidents (réveil, concentration)
- **Intégration:** Dans calcul des vecteurs journaliers (modèle PDF)

---

### Q3.11 - Effets Temporels (Agressions, Patterns) ✅

**Réponse:** Déjà vu et implémenté

**Effets temporels:**
- **Agressions jour suivant:** Diminuent jour même, augmentent jour suivant
- **Patterns 3 jours → 1 semaine:** Si proportions > 60% d'agressions pendant 3 jours → augmentation probabilité agressions pendant 1 semaine suivante (même zone + zones adjacentes)
- **Intégration:** Dans patterns 7 jours et 60 jours (DataFrames mobiles)

---

## 7. STRUCTURE ÉVÉNEMENTS

### Q3.12 - Structure Classe de Base Événements ✅

**Réponse:** Hiérarchie de classes avec héritage

**Structure:**
```
Event (classe de base)
├── Incident (sous-classe)
│   ├── Accident
│   ├── Agression
│   └── Incendie
└── PositiveEvent (sous-classe)
```

**Caractéristiques:**
- **Caractéristiques peuvent être créées aléatoirement ou non**
- **Caractéristiques peuvent avoir effet sur randomité** création caractéristiques dans autres événements
- **Complexité nécessaire:** Pour éviter que ML comprenne trop facilement le modèle
- **Réalisme:** Doit être réaliste (difficile mais nécessaire)

**Retour à la normale:**
- **Peut être simplement un événement positif**
- **Caractéristique:** Annuler tous événements négatifs pour 10 jours sur tout Paris

---

### Q3.13 - Types de Caractéristiques ✅

**Réponse:** 3 types de caractéristiques

**1. Augmentation accidents bénins/moyens:**
- Augmente nombre accidents bénins/moyens dans microzones suivantes
- Génère effets dans toutes zones adjacentes

**2. Deuxième caractéristique:**
- (À préciser)

**3. Réduction embouteillages:**
- Baisse embouteillages (zone si dangereuse que gens ne viennent plus en voiture)
- Devient positif sur nombre d'accidents (moins de voitures = moins d'accidents)

---

## 8. MACHINE LEARNING

### Q3.14 - Fenêtres Glissantes Efficaces ✅

**Réponse:** Tableau avec 18 features × 4 semaines + arrondissements adjacents

**Structure:**
- **18 features × 4 semaines = 72 colonnes** (pour un arrondissement)
- **Chaque semaine on ajoute la suivante**
- **Pour arrondissements:** Prendre arrondissement central + **4 arrondissements autour**
- **Tableau statique:** Dit pour chaque arrondissement quels sont les 4 autour
- **Base arrondissement + 4 autour = 5 × 18 = 90 features** pour trouver label

**Workflow:**
- **Au début:** Pas de prédiction tant qu'il n'y a pas 5 semaines
- **Deux parties:**
  1. **Run qui crée tout:** Features hebdo + labels (colonnes, pour chaque nouvelle semaine on multiplie tout)
  2. **5 runs puis 49 runs supplémentaires**
- **Chargement:** Temps avec entraînement ML à la fin, icône "finished"
- **Entraînement:** Sur grand DataFrame final avec 18 features × 4 arrondissements pour 1 arrondissement
- **Combinaisons:** Même données remises, mais on prend seulement les 4 semaines précédentes de l'arrondissement
- **Limitation:** On ne prend pas toutes les semaines précédentes, pas tout Paris
- **Avantage:** Limite features mais laisse assez pour prédiction possible

---

### Q3.15 - Hyperparamètres ✅

**Réponse:** Phase 2, valeurs fixes au début

- **Hyperparamètres:** Phase 2 (ajustement plus tard)
- **Valeurs fixes** au début pour MVP

---

### Q3.16 - Ratio Normal pour Normaliser Score ✅

**Réponse:** À déterminer lors partie technique, se rapprocher de réalité

**Seuils pour 3 classes:**
- **Normal:** 3.25 morts par semaine pour 100,000 habitants
- **Pre-catastrophique:** > 4.2 morts (formule: morts + 0.5 × blessés graves)
- **Catastrophique:** > 4.8 morts × 0.5 blessés graves
- **Calcul:** En relation avec nombre total d'habitants de l'arrondissement

**Formule:**
```
score = (morts + 0.5 × blessés_graves) / (habitants_arr / 100000) × 3.25
```

---

### Q3.17 - Métriques ML ✅

**Réponse:** Seulement à la fin, mais suivi live possible

**Métriques:**
- **Métriques ML:** Seulement à la fin de l'entraînement
- **Suivi live:** On peut suivre nombre de morts, blessés graves par arrondissements en live (intéressant)

---

## 9. INTERFACE UTILISATEUR

### Q3.18 - Interface Web App ✅

**Réponse:** Web app simple, Tkinter/Folium étaient tests

**Interface:**
- **Web app simple** (Tkinter et Folium étaient juste tests de départ)
- **Update 2.5 secondes:** Chaque jour dure 1/3 seconde, donc 7 × 1/3 = 2.5 secondes
- **Fonctionnalités:**
  - **Modèles enregistrés** (trained models)
  - **Choix algos:** 2 régression, 2 classification = **4 algos total**
  - **Pré-cachés** selon décision régression/classification
  - **Change calculs labels** selon algo choisi

---

## 10. TESTS ET VALIDATION

### Q3.19 - Tests Unitaires ✅

**Réponse:** Vérifier cohérence des données

**Tests:**
- **Vérifier données:** Si 0 morts ou < 2 morts sur arrondissement sur 400 jours → problème
- **Si > 200 morts** → problème
- **Cohérence données:** Vérifier soi-même en regardant les données

---

### Q3.20 - Validation Patterns et Corrélations ✅

**Réponse:** Vérifier qu'il n'y a pas de packaging

**Validation:**
- **Vérifier qu'il n'y a pas de packaging** (regroupement dans une direction)
- **Suivre graphiques** nombre de morts, etc.
- **Pas de packaging** dans un sens ou l'autre
- **Test de performance:** Voir plus tard (ML, génération de données d'abord)

---

### Q3.21 - Gestion Modèle qui Performe Mal ✅

**Réponse:** Voir plus tard

- Re-entraînement, ajustements → à voir plus tard

---

## 11. PERFORMANCE ET OPTIMISATION

### Q3.22 - Optimisation Nécessaire ✅

**Réponse:** Parallélisation possible mais pas vraiment voulu

**Options:**
1. **Faire tous les runs puis ML à la fin**
2. **Commencer à entraîner sur nouvelles données générées** (parallélisation possible mais pas vraiment voulu)

**Parallélisation:**
- **Calculs vecteurs vs calculs proportions:** Pourraient être parallélisés (dépendants l'un de l'autre)
- **Python:** Limites de parallélisation, mais possible

---

### Q3.23 - Scalabilité ✅

**Réponse:** Architecture modulaire, nombres entiers/floats

**Scalabilité:**
- **Reste nombres entiers (ints) ou floats** → pas énormes
- **Architecture modulaire** pour mettre vraies données (Phase 2)
- **Réponse à question 3:** Architecture modulaire surtout pour mettre vraies données

---

**Créé:** 26 Janvier 2026  
**Statut:** ✅ Complété  
**Prochaine étape:** Implémentation selon spécifications
