# Révision Saisonnalité - Problèmes Identifiés et Corrections

**Date** : 28 Janvier 2026

## Paramètres Saisonnalité Conformes à la Réalité

Selon `Contexte-Sessions-1-a-3.md` (lignes 151-160) :

```
Été : +20% agressions, -10% incendies
Hiver : +30% incendies, -20% agressions
Intersaison (printemps/automne) : +5-10% accidents (effet léger)
```

**Conversion en multiplicateurs** :
- **Agressions** :
  - Hiver : 0.8 (-20%)
  - Été : 1.2 (+20%)
  - Intersaison : 1.0 (normal)
- **Incendies** :
  - Hiver : 1.3 (+30%)
  - Été : 0.9 (-10%)
  - Intersaison : 1.0 (normal)
- **Accidents** :
  - Hiver : 1.0 (normal)
  - Été : 1.0 (normal)
  - Intersaison : 1.05-1.1 (+5-10%, effet léger)

---

## Problèmes Identifiés

### 1. Fichiers Patterns JSON - Valeurs Incorrectes

**Fichiers à corriger** :
- `data/patterns/pattern_4j_example.json`
- `data/patterns/pattern_7j_example.json`
- `data/patterns/pattern_60j_example.json`

**Valeurs actuelles (incorrectes)** :
- Agressions : hiver 0.9, été 1.0, intersaison 1.1
- Incendies : hiver 1.1, été 1.2, intersaison 1.0
- Accidents : pas de mention spécifique intersaison

**Valeurs correctes** :
- Agressions : hiver 0.8, été 1.2, intersaison 1.0
- Incendies : hiver 1.3, été 0.9, intersaison 1.0
- Accidents : hiver 1.0, été 1.0, intersaison 1.05-1.1

### 2. Story 2.2.1 - Saisonnalité Non Mentionnée

**Problème** : La story de génération de vecteurs (2.2.1) ne mentionne pas explicitement l'application de la saisonnalité aux intensités λ.

**Correction nécessaire** : Ajouter dans Story 2.2.1 :
- Application saisonnalité aux intensités λ_base selon type d'incident
- Facteurs saisonniers : hiver (+30% incendies, -20% agressions), été (+20% agressions, -10% incendies), intersaison (+5-10% accidents)

### 3. Story 1.3 - Saisonnalité Congestion vs Vecteurs

**Problème** : Story 1.3 mentionne saisonnalité pour congestion (intersaison > hiver/été), mais pas pour les vecteurs statiques.

**Clarification** : La saisonnalité doit être appliquée :
- **Aux vecteurs** (génération incidents) : via patterns JSON dans Story 2.2.1
- **À la congestion** : via congestion statique (intersaison > hiver/été)

---

## Corrections à Effectuer

### ✅ Correction 1 : Fichiers Patterns JSON
- [ ] Corriger `pattern_4j_example.json` (agressions, incendies, accidents)
- [ ] Corriger `pattern_7j_example.json` (agressions, incendies, accidents)
- [ ] Corriger `pattern_60j_example.json` (agressions, incendies, accidents)

### ✅ Correction 2 : Story 2.2.1
- [ ] Ajouter mention saisonnalité dans génération vecteurs
- [ ] Ajouter facteurs saisonniers dans calcul intensités λ
- [ ] Ajouter tests validation saisonnalité

### ✅ Correction 3 : Story 1.3
- [ ] Clarifier que saisonnalité congestion ≠ saisonnalité vecteurs
- [ ] Mentionner que saisonnalité vecteurs via patterns JSON

---

## Validation Finale

Après corrections, vérifier :
1. ✅ Patterns JSON ont valeurs correctes (hiver/été/intersaison)
2. ✅ Story 2.2.1 mentionne application saisonnalité aux vecteurs
3. ✅ Story 1.3 distingue saisonnalité congestion vs vecteurs
4. ✅ Toutes les stories cohérentes sur saisonnalité
