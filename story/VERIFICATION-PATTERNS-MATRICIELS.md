# Vérification Patterns Matriciels et Aspects Complexes

**Date** : 28 Janvier 2026

## Points à Vérifier

### 1. Triple Pattern Matricielle de Génération

**Exigences** :
- Co-aléatoire et conforme à J-1
- Différents facteurs dans un même incident
- Probabilités croisées (bénin, moyen, grave)
- Même chose avec le nb total des 2 autres types d'incidents
- Changement d'effet sur la génération aléatoire dans J+1

**Vérification** :
- ✅ Story 2.2.9 : Trois matrices (gravité, croisée, voisins) - **PARTIELLEMENT COUVERT**
- ❌ **MANQUE** : Probabilités croisées (bénin, moyen, grave) dans même incident
- ❌ **MANQUE** : Effet nb total des 2 autres types d'incidents sur génération
- ❌ **MANQUE** : Changement d'effet sur génération aléatoire J+1 selon J-1

### 2. Occurrence des 8 Zones Adjacentes

**Exigences** :
- Occurrence des 8 zones adjacentes dans J+1

**Vérification** :
- ✅ Story 2.2.9 : Matrice voisins (8 zones radius 1) - **COUVERT**

### 3. Occurrence des Patterns de Génération (7j et 60j)

**Exigences** :
- Si des patterns sur 4j ou 7j ont été détectés, occurrence des patterns 7j et 60j

**Vérification** :
- ✅ Story 2.2.2 : Patterns 4j/7j/60j - **COUVERT**
- ⚠️ **À CLARIFIER** : Détection patterns 4j/7j et déclenchement patterns 7j/60j

### 4. Occurrence des Saisons

**Exigences** :
- Déjà traité

**Vérification** :
- ✅ **COUVERT** (corrigé précédemment)

### 5. Occurrence des Phénomènes (Crise, Dégradé, Normal)

**Exigences** :
- Créés au hasard en moyenne : 80% normal, 15% dégradé, 5% crise
- Cela pour les vecteurs de base (accidents, incendies, agressions)
- Et pour les variables générées après (nb parmi total de (type en question) d'incidents commis sous alcool et la nuit)

**Vérification** :
- ✅ Story 2.2.1 : Régimes cachés (Stable, Détérioration, Crise) - **PARTIELLEMENT COUVERT**
- ❌ **MANQUE** : Probabilités exactes (80% normal, 15% dégradé, 5% crise)
- ❌ **MANQUE** : Application aux variables alcool/nuit

### 6. Congestion Route - Congestion Nuit

**Exigences** :
- Ajouter congestion nuit pour incidents s'étant produit la nuit
- Carte de congestion beaucoup plus faible (en moyenne divisée par 3 avec effet aléatoire, seulement 2.2 l'été)

**Vérification** :
- ❌ **MANQUE** : Congestion nuit dans Story 2.2.2.5

### 7. Golden Hour Différencié

**Exigences** :
- Si nuit : +congestion nuit
- Si alcool : +5 min
- Jour-(nuit+alcool) = calcul classique

**Vérification** :
- ❌ **MANQUE** : Différenciation nuit/alcool dans Story 2.2.3

### 8. 60% des Valeurs > 0 Sans Alcool Ni Nuit

**Exigences** :
- En moyenne 60% des valeurs supérieur à 0 n'auront ni alcool, ni nuit
- Modifier caractéristique aléatoire pour arriver environ à ce résultat

**Vérification** :
- ❌ **MANQUE** : Contrainte 60% dans Story 2.2.2

---

## Actions Requises

1. **Story 2.2.1** : Ajouter probabilités croisées (bénin, moyen, grave) et effet nb total autres types
2. **Story 2.2.1** : Ajouter probabilités régimes (80% normal, 15% dégradé, 5% crise)
3. **Story 2.2.2** : Ajouter contrainte 60% sans alcool ni nuit
4. **Story 2.2.2** : Application régimes aux variables alcool/nuit
5. **Story 2.2.2.5** : Ajouter congestion nuit (divisée par 3, 2.2 l'été)
6. **Story 2.2.3** : Ajouter différenciation nuit/alcool (+congestion nuit, +5 min alcool)
7. **Story 2.2.9** : Clarifier effet J-1 sur génération aléatoire J+1
