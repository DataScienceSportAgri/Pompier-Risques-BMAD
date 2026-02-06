# Questions et Clarifications Nécessaires

Ce document liste les questions restantes et points à clarifier pour finaliser les stories avant le développement.

## Questions Critiques

### 1. Structure 144 features (Story 2.3.1) ✅ RÉSOLU

**Réponse** : Structure exacte clarifiée :
- 1 central dernière semaine : 18 features
- 1 central 3 semaines précédentes : 3 × 18 = 54 features
- 4 voisins dernière semaine : 4 × 18 = 72 features
- **Total** : 18 + 54 + 72 = **144 features** ✓

---

### 2. Correspondance features/labels (Story 2.2.6)

**Question** : Comment aligner les 144 features (4 semaines voisins) avec les labels mensuels (4 semaines) ?

L'utilisateur a dit : "3 semaines des voisins avant la dernière semaine" et "la dernière semaine n'est pas prise en compte pour les voisins dans le label mensuel".

**Clarification nécessaire** :
- Les 4 semaines des voisins sont-elles les 4 semaines avant le mois du label ?
- La dernière semaine du mois est-elle incluse dans les features du central mais pas dans les features des voisins ?

---

### 3. Ordre événements positifs (Story 2.2.8)

**Question** : Impact sur vecteurs J+1

L'utilisateur a confirmé que les événements positifs sont générés **après** les vecteurs et ont un impact sur **J+1**.

**Clarification nécessaire** :
- Les événements positifs modifient-ils les intensités pour le jour suivant (J+1) ?
- Ou modifient-ils les matrices de transition pour J+1 ?

---

### 4. Format pickle standardisé (Story 2.1.4) ✅ RÉSOLU

**Réponse** : Philosophie définie dans `docs/philosophy-pickle-format.md` :
- Structure : `{'data': ..., 'metadata': {...}}`
- Métadonnées obligatoires : version, created_at, type, description
- Métadonnées optionnelles : run_id, schema_version, config_hash
- Voir document complet pour détails

---

### 5. Patterns Paris (Story 1.4) ✅ RÉSOLU

**Réponse** : Philosophie définie dans `docs/philosophy-patterns-json.md` :
- Structure hiérarchique : global → microzone → type → gravité
- Champs obligatoires : pattern_type, pattern_name, version, created_at, microzones
- Exemples complets : `data/patterns/pattern_4j_example.json`, `pattern_7j_example.json`
- Voir document complet pour détails

---

## Points Validés

✅ Congestion statique pré-calculée (Story 1.3)  
✅ SimulationState avec domaines spécialisés (Story 2.1.2)  
✅ Ordre : Vecteurs → Matrices → Congestion → Golden Hour  
✅ Événements graves modifient congestion temps réel  
✅ Événements positifs après vecteurs, impact J+1  
✅ Golden Hour avec tirage au sort (pas ×1.3)  
✅ Système suivi interventions par caserne  
✅ Mois glissant pour labels  
✅ 50 runs parallélisables  
✅ DataFrame géant 50 runs (pas agrégation statique)  
✅ Validation config Pydantic  
✅ Tests intégration dédiés  
✅ Benchmarks automatisés  
✅ Format pickle standardisé  
✅ Thread séparé pour UI temps réel  
✅ Stop fait dernière itération  
✅ Tests validation cohérence automatiques après chaque run  

---

## Actions Requises

1. ✅ **Clarifier structure 144 features** avec PO → **RÉSOLU**
2. ✅ **Finaliser format pickle standardisé** (structure exacte) → **RÉSOLU** (voir `docs/philosophy-pickle-format.md`)
3. ✅ **Finaliser format patterns JSON** (structure exacte) → **RÉSOLU** (voir `docs/philosophy-patterns-json.md`)
4. **Valider ordre final** des stories avec équipe

---

**Date de création** : 28 Janvier 2026  
**Dernière mise à jour** : 28 Janvier 2026  
**Statut** : Toutes les questions critiques résolues ✓
