"""
Pré-calcul des matrices de corrélation fixes pour la prédiction J→J+1 (Story 1.4.4).

Ce module calcule toutes les matrices fixes nécessaires pour la génération de vecteurs
journaliers dans la simulation Monte-Carlo d'incidents urbains à Paris.

Matrices calculées :
1. Matrices de corrélation intra-type (3×3)
   - Transitions entre gravités (bénin→bénin, bénin→moyen, etc.)
   - Une matrice par (microzone, type_incident)
   - Basée sur le modèle Zero-Inflated Poisson du PDF

2. Matrices de corrélation inter-type
   - Influence d'un type d'incident sur un autre
   - Exemples : Incendie → Accidents (fumée), Agressions → Accidents (panique)
   - Basée sur les processus de Hawkes

3. Matrices voisin (8 microzones)
   - Identification des 8 microzones les plus proches
   - Calcul des poids d'influence (inverse de la distance)
   - Utilisé pour l'effet d'augmentation (+0.1 si >5 incidents dans voisins)

4. Matrices trafic
   - Engorgement/désengorgement du trafic entre jours
   - Probabilités de transition et facteur de mémoire
   - Impact sur les temps de trajet et la congestion

5. Matrices alcool/nuit
   - Probabilités qu'un incident soit causé par l'alcool ou se produise la nuit
   - 20% accidents avec alcool (base), 30% l'été
   - Génération aléatoire pour déterminer les incidents concernés

6. Matrices saisonnalité
   - Facteurs de modulation par saison (hiver, inter-saison, été)
   - Agressions : +25% été, -15% hiver
   - Incendies : +30% hiver, -10% été
   - Accidents : +10% hiver, -5% été

7. Règles effet d'augmentation (fixes)
   - +0.1 si délinquance voisin > microzone ou si >5 incidents dans 8 voisins, max +0.2

8. Pattern 4j→7j (matrice de transition fixe)
   - Vecteur 7 jours : +0.1 agressions/jour, pic jour 3. Déclencheur : 1 agression 4j consécutifs.

9. Pattern 60j (matrice de transition fixe)
   - Vecteur 60 jours : +0.05 (j1–20), -0.05 (j21–40), +0.1 (j41–60). Déclencheur : 0 agression 7j.

10. Règles patterns : max 3 patterns actifs par microzone.

Fichiers temporaires (data/intermediate/patterns/) : pattern_4j_temp.pkl, pattern_7j_temp.pkl,
pattern_60j_temp.pkl. Ils permettent de générer les patterns (7j, 60j) qui influencent les
probabilités ; le precompute les écrit puis les lit pour produire pattern_*_transition.

Inspiré du modèle de prédiction J+1 (PDF) et des processus de Hawkes pour les corrélations.

Auteur: Story 1.4.4
Date: 28 Janvier 2026
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import geopandas as gpd

logger = logging.getLogger(__name__)


class MatricesCorrelationCalculator:
    """
    Calcule toutes les matrices de corrélation fixes nécessaires pour la prédiction J→J+1.
    
    Basé sur :
    - Modèle Zero-Inflated Poisson du PDF
    - Processus de Hawkes pour corrélations inter-types
    - Littérature criminologique sur near-repeat patterns
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Types d'incidents et gravités
        self.types_incidents = ['agressions', 'incendies', 'accidents']
        self.gravites = ['benin', 'moyen', 'grave']
        
        # Régimes cachés (du PDF)
        self.regimes = ['stable', 'deterioration', 'crise']
        
        # Saisons
        self.saisons = ['hiver', 'intersaison', 'ete']
    
    # ============================================================================
    # 1. MATRICES DE CORRÉLATION INTRA-TYPE
    # ============================================================================
    
    def calculate_matrices_intra_type(self, microzones: gpd.GeoDataFrame) -> Dict:
        """
        Calcule les matrices de corrélation intra-type (3×3) pour chaque type d'incident
        et chaque microzone.
        
        Matrice 3×3 : transitions entre gravités (bénin→bénin, bénin→moyen, etc.)
        
        Returns:
            Dict[microzone_id][type_incident] = matrice 3×3
        """
        logger.info("🔄 Calcul des matrices de corrélation intra-type...")
        
        matrices = {}
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            
            matrices[microzone_id] = {}
            
            for type_incident in self.types_incidents:
                # Matrice de transition 3×3 (bénin, moyen, grave)
                matrice = self._calculate_matrice_intra_type_base(
                    type_incident, arrondissement
                )
                
                matrices[microzone_id][type_incident] = matrice
        
        logger.info(f"✅ Matrices intra-type calculées pour {len(matrices)} microzones")
        return matrices
    
    def _calculate_matrice_intra_type_base(
        self, 
        type_incident: str, 
        arrondissement: int
    ) -> np.ndarray:
        """
        Calcule une matrice de transition intra-type de base (3×3).
        
        Basé sur le modèle Zero-Inflated Poisson du PDF avec probabilités de transition réalistes.
        La matrice modélise les transitions entre gravités J→J+1 pour un type d'incident donné.
        
        Structure :
        - Ligne i : état à J (bénin=0, moyen=1, grave=2)
        - Colonne j : état à J+1 (bénin=0, moyen=1, grave=2)
        - Valeur [i,j] : probabilité de transition de i vers j
        
        Args:
            type_incident: Type d'incident ('agressions', 'incendies', 'accidents')
            arrondissement: Numéro d'arrondissement (1-20)
        
        Returns:
            Matrice numpy 3×3 normalisée (somme de chaque ligne = 1)
        """
        # Matrice de base : tendance à rester dans la même gravité
        # mais possibilité de dégradation ou amélioration
        
        matrice = np.zeros((3, 3))  # [bénin, moyen, grave] × [bénin, moyen, grave]
        
        # Probabilités de transition (basées sur le modèle PDF)
        # Ligne 0 : bénin → [bénin, moyen, grave]
        matrice[0, 0] = 0.85  # Reste bénin (stabilité)
        matrice[0, 1] = 0.12  # Dégradation vers moyen
        matrice[0, 2] = 0.03  # Dégradation vers grave (rare)
        
        # Ligne 1 : moyen → [bénin, moyen, grave]
        matrice[1, 0] = 0.10  # Amélioration vers bénin
        matrice[1, 1] = 0.75  # Reste moyen (stabilité)
        matrice[1, 2] = 0.15  # Dégradation vers grave
        
        # Ligne 2 : grave → [bénin, moyen, grave]
        matrice[2, 0] = 0.05  # Amélioration vers bénin (rare)
        matrice[2, 1] = 0.20  # Amélioration vers moyen
        matrice[2, 2] = 0.75  # Reste grave (persistance)
        
        # Ajustements selon le type d'incident (logique métier)
        if type_incident == 'agressions':
            # Agressions : plus de dégradation possible (escalade de violence)
            matrice[0, 1] *= 1.2
            matrice[0, 2] *= 1.3
            matrice[1, 2] *= 1.1
        elif type_incident == 'incendies':
            # Incendies : moins de dégradation, plus de stabilité (souvent isolés)
            matrice[0, 1] *= 0.8
            matrice[0, 2] *= 0.7
            matrice[1, 2] *= 0.9
        elif type_incident == 'accidents':
            # Accidents : valeurs par défaut (déjà réalistes)
            pass
        
        # Ajustements légers selon l'arrondissement
        if arrondissement in [18, 19, 20]:  # Nord-est (zones à risque)
            # Plus de dégradation possible
            matrice[0, 1] *= 1.1
            matrice[0, 2] *= 1.15
        elif arrondissement in [1, 2, 3, 4, 5, 6, 7, 8]:  # Centre (zones calmes)
            # Moins de dégradation
            matrice[0, 1] *= 0.9
            matrice[0, 2] *= 0.85
        
        # Normaliser chaque ligne pour que la somme = 1
        for i in range(3):
            somme = matrice[i, :].sum()
            if somme > 0:
                matrice[i, :] /= somme
            else:
                # Fallback si somme = 0 (ne devrait pas arriver)
                matrice[i, :] = np.array([0.33, 0.33, 0.34])
        
        return matrice
    
    # ============================================================================
    # 2. MATRICES DE CORRÉLATION INTER-TYPE
    # ============================================================================
    
    def calculate_matrices_inter_type(self, microzones: gpd.GeoDataFrame) -> Dict:
        """
        Calcule les matrices de corrélation inter-type.
        
        Modélise l'influence des autres types d'incidents sur un type donné.
        Basé sur les processus de Hawkes et les corrélations observées :
        - Incendie → Accidents (fumée, routes bloquées)
        - Agressions → Accidents (panique, fuite)
        - Accidents → Incendies (explosions, court-circuits)
        
        Returns:
            Dict[microzone_id][type_cible][type_source] = [influence_bénin, influence_moyen, influence_grave]
        """
        logger.info("🔄 Calcul des matrices de corrélation inter-type...")
        
        matrices = {}
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            
            matrices[microzone_id] = {}
            
            for type_cible in self.types_incidents:
                matrices[microzone_id][type_cible] = {}
                
                for type_source in self.types_incidents:
                    if type_source == type_cible:
                        continue  # Pas d'auto-influence
                    
                    # Calculer l'influence du type_source sur le type_cible
                    influence = self._calculate_influence_inter_type(
                        type_source, type_cible, arrondissement
                    )
                    
                    matrices[microzone_id][type_cible][type_source] = influence
        
        logger.info(f"✅ Matrices inter-type calculées pour {len(matrices)} microzones")
        return matrices
    
    def _calculate_influence_inter_type(
        self,
        type_source: str,
        type_cible: str,
        arrondissement: int
    ) -> List[float]:
        """
        Calcule l'influence d'un type d'incident sur un autre.
        
        Basé sur les processus de Hawkes et les corrélations observées dans la littérature :
        - Incendie → Accidents : fumée réduisant visibilité, routes bloquées
        - Agressions → Accidents : panique, fuite, conduite dangereuse
        - Accidents → Incendies : explosions, court-circuits, fuites
        - Accidents → Agressions : tensions post-accident, disputes
        - Incendie → Agressions : stress, évacuation, tensions
        - Agressions → Incendies : actes volontaires (incendies criminels)
        
        Args:
            type_source: Type d'incident source (qui influence)
            type_cible: Type d'incident cible (qui est influencé)
            arrondissement: Numéro d'arrondissement (1-20)
        
        Returns:
            [influence_bénin, influence_moyen, influence_grave]
            Valeurs entre 0 et 1, représentant l'augmentation de probabilité
        """
        # Valeurs de base (faible influence croisée par défaut)
        influence_base = [0.05, 0.03, 0.01]  # [bénin, moyen, grave]
        
        # Corrélations spécifiques basées sur la logique métier et la littérature
        if type_source == 'incendies' and type_cible == 'accidents':
            # Incendie → Accidents : fumée réduisant visibilité, routes bloquées
            # Impact plus fort sur incidents graves (accidents de la route)
            influence_base = [0.12, 0.08, 0.05]
        
        elif type_source == 'agressions' and type_cible == 'accidents':
            # Agressions → Accidents : panique, fuite, conduite dangereuse
            # Impact modéré, surtout sur incidents moyens/graves
            influence_base = [0.10, 0.06, 0.03]
        
        elif type_source == 'accidents' and type_cible == 'incendies':
            # Accidents → Incendies : explosions, court-circuits, fuites de carburant
            # Impact modéré, surtout sur incidents graves
            influence_base = [0.08, 0.05, 0.02]
        
        elif type_source == 'accidents' and type_cible == 'agressions':
            # Accidents → Agressions : tensions post-accident, disputes
            # Impact faible à modéré
            influence_base = [0.06, 0.04, 0.02]
        
        elif type_source == 'incendies' and type_cible == 'agressions':
            # Incendie → Agressions : stress, évacuation, tensions
            # Impact faible
            influence_base = [0.05, 0.03, 0.01]
        
        elif type_source == 'agressions' and type_cible == 'incendies':
            # Agressions → Incendies : actes volontaires (incendies criminels)
            # Impact faible mais réel
            influence_base = [0.04, 0.02, 0.01]
        
        # Ajustements selon l'arrondissement
        if arrondissement in [18, 19, 20]:  # Nord-est (zones à risque)
            # Corrélations plus fortes dans les zones à risque
            influence_base = [x * 1.2 for x in influence_base]
        elif arrondissement in [1, 2, 3, 4, 5, 6, 7, 8]:  # Centre (zones calmes)
            # Corrélations plus faibles dans les zones calmes
            influence_base = [x * 0.8 for x in influence_base]
        
        # S'assurer que les valeurs restent dans [0, 1]
        influence_base = [min(max(x, 0.0), 1.0) for x in influence_base]
        
        return influence_base
    
    # ============================================================================
    # 3. MATRICES VOISIN (8 microzones)
    # ============================================================================
    
    def calculate_matrices_voisin(self, microzones: gpd.GeoDataFrame) -> Dict:
        """
        Identifie les 8 microzones voisines pour chaque microzone et calcule leur influence.
        
        Returns:
            Dict[microzone_id] = {
                'voisins': [list of 8 microzone_ids],
                'poids_influence': [list of 8 weights],
                'seuil_activation': 5  # Seuil pour effet d'augmentation
            }
        """
        logger.info("🔄 Calcul des matrices voisin (8 microzones)...")
        
        matrices = {}
        
        # Calculer les centroïdes de toutes les microzones
        centroids = {}
        for idx, mz in microzones.iterrows():
            centroids[mz['microzone_id']] = (
                mz.geometry.centroid.x,
                mz.geometry.centroid.y
            )
        
        # Pour chaque microzone, trouver les 8 plus proches
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            center_x, center_y = centroids[microzone_id]
            
            # Calculer distances à toutes les autres microzones
            distances = []
            for other_id, (other_x, other_y) in centroids.items():
                if other_id == microzone_id:
                    continue
                dist = np.sqrt((center_x - other_x)**2 + (center_y - other_y)**2)
                distances.append((other_id, dist))
            
            # Trier par distance et prendre les 8 plus proches
            distances.sort(key=lambda x: x[1])
            voisins = [d[0] for d in distances[:8]]
            distances_voisins = [d[1] for d in distances[:8]]
            
            # Calculer poids d'influence (inverse de la distance, normalisé)
            poids = [1.0 / (d + 0.001) for d in distances_voisins]  # +0.001 pour éviter division par 0
            poids = np.array(poids)
            poids = poids / poids.sum()  # Normaliser
            
            matrices[microzone_id] = {
                'voisins': voisins,
                'poids_influence': poids.tolist(),
                'distances': distances_voisins,
                'seuil_activation': 5  # Seuil pour effet d'augmentation
            }
        
        logger.info(f"✅ Matrices voisin calculées pour {len(matrices)} microzones")
        return matrices
    
    # ============================================================================
    # 4. MATRICE TRAFIC (engorgement/désengorgement)
    # ============================================================================
    
    def calculate_matrice_trafic(self, microzones: gpd.GeoDataFrame) -> Dict:
        """
        Calcule les matrices de transition de trafic entre jours.
        
        Modélise l'engorgement et le désengorgement du trafic :
        - Trafic élevé J → peut engorger J+1 (probabilité d'engorgement)
        - Trafic faible J → peut désengorger J+1 (probabilité de désengorgement)
        - Effet de mémoire (trafic persiste avec un facteur de décroissance)
        
        La matrice permet de calculer le niveau de trafic J+1 en fonction du trafic J :
        trafic_J+1 = trafic_J × facteur_memoire + (engorgement ou désengorgement)
        
        Returns:
            Dict[microzone_id] = {
                'prob_engorgement': float,      # Probabilité d'engorgement si trafic élevé J
                'prob_desengorgement': float,   # Probabilité de désengorgement si trafic faible J
                'facteur_memoire': float,       # Facteur de persistance du trafic (0-1)
                'amplitude_engorgement': float, # Amplitude de l'engorgement si déclenché
                'amplitude_desengorgement': float  # Amplitude du désengorgement si déclenché
            }
        """
        logger.info("🔄 Calcul des matrices trafic...")
        
        matrices = {}
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            
            # Probabilités de base
            prob_engorgement = 0.35  # 35% chance d'engorgement si trafic élevé J
            prob_desengorgement = 0.40  # 40% chance de désengorgement si trafic faible J
            facteur_memoire = 0.60  # 60% de persistance du trafic (décroissance)
            amplitude_engorgement = 0.15  # +15% de trafic si engorgement
            amplitude_desengorgement = -0.12  # -12% de trafic si désengorgement
            
            # Ajustements selon l'arrondissement
            if arrondissement <= 4:  # Centre (1er-4e) : beaucoup de trafic
                prob_engorgement *= 1.3
                facteur_memoire *= 1.2  # Plus de persistance
                amplitude_engorgement *= 1.2
            elif arrondissement in [5, 6, 7, 8]:  # Centre-ouest : trafic modéré
                prob_engorgement *= 1.1
                facteur_memoire *= 1.05
            elif arrondissement >= 16:  # Ouest (16e-20e) : moins de trafic
                prob_engorgement *= 0.8
                prob_desengorgement *= 1.1
                facteur_memoire *= 0.9
            elif arrondissement in [18, 19, 20]:  # Nord-est : trafic variable
                prob_engorgement *= 1.1
                amplitude_engorgement *= 1.1
            
            # S'assurer que les probabilités restent dans [0, 1]
            prob_engorgement = min(max(prob_engorgement, 0.0), 1.0)
            prob_desengorgement = min(max(prob_desengorgement, 0.0), 1.0)
            facteur_memoire = min(max(facteur_memoire, 0.0), 1.0)
            
            matrices[microzone_id] = {
                'prob_engorgement': prob_engorgement,
                'prob_desengorgement': prob_desengorgement,
                'facteur_memoire': facteur_memoire,
                'amplitude_engorgement': amplitude_engorgement,
                'amplitude_desengorgement': amplitude_desengorgement
            }
        
        logger.info(f"✅ Matrices trafic calculées pour {len(matrices)} microzones")
        return matrices
    
    # ============================================================================
    # 5. MATRICES ALCOOL/NUIT
    # ============================================================================
    
    def calculate_matrices_alcool_nuit(self, microzones: gpd.GeoDataFrame) -> Dict:
        """
        Calcule les probabilités qu'un incident soit causé par l'alcool ou se produise la nuit.
        
        Ces matrices permettent de déterminer, parmi les vecteurs ayant au moins une valeur > 0,
        quels incidents ont été causés la nuit ou avec alcool.
        
        Règles (basées sur statistiques réelles) :
        - 20% des accidents avec alcool (base)
        - 30% des accidents avec alcool l'été (20% × 1.5)
        - Probabilités différentes selon le type d'incident
        - Probabilités plus élevées la nuit (22h-6h)
        
        Génération aléatoire :
        - Pour chaque incident généré, tirage aléatoire selon prob_alcool
        - En été, prob_alcool est multipliée par facteur_ete_alcool
        - Pour la nuit, tirage aléatoire selon prob_nuit
        
        Returns:
            Dict[microzone_id][type_incident] = {
                'prob_alcool': float,           # Probabilité base alcool (0-1)
                'prob_nuit': float,             # Probabilité incident la nuit (0-1)
                'facteur_ete_alcool': float,    # Multiplicateur été pour alcool
                'heures_nuit': List[int]         # Heures considérées comme "nuit" [22, 23, 0, 1, 2, 3, 4, 5]
            }
        """
        logger.info("🔄 Calcul des matrices alcool/nuit...")
        
        matrices = {}
        
        # Heures considérées comme "nuit" (22h-5h)
        heures_nuit = [22, 23, 0, 1, 2, 3, 4, 5]
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            
            matrices[microzone_id] = {}
            
            for type_incident in self.types_incidents:
                if type_incident == 'accidents':
                    # Accidents : 20% avec alcool (base), 30% l'été
                    # Source : statistiques sécurité routière
                    prob_alcool = 0.20
                    facteur_ete_alcool = 1.5  # 20% * 1.5 = 30% l'été
                    prob_nuit = 0.35  # Plus d'accidents la nuit (visibilité réduite)
                
                elif type_incident == 'agressions':
                    # Agressions : moins d'alcool directement, mais contexte alcoolisé
                    # Beaucoup plus fréquentes la nuit
                    prob_alcool = 0.15  # Contexte alcoolisé (bars, sorties)
                    facteur_ete_alcool = 1.2  # Légère augmentation l'été
                    prob_nuit = 0.45  # Beaucoup d'agressions la nuit (sorties, bars)
                
                elif type_incident == 'incendies':
                    # Incendies : peu d'alcool directement, répartition jour/nuit équilibrée
                    prob_alcool = 0.05  # Très faible (erreurs, négligence)
                    facteur_ete_alcool = 1.0  # Pas d'augmentation été
                    prob_nuit = 0.40  # Légèrement plus la nuit (chauffage, cuisson)
                
                # Ajustements selon l'arrondissement
                if arrondissement in [18, 19, 20]:  # Nord-est (zones à risque)
                    prob_alcool *= 1.2
                    prob_nuit *= 1.1
                elif arrondissement in [9, 10, 11, 12]:  # Est (zones animées)
                    prob_alcool *= 1.1
                    prob_nuit *= 1.05
                elif arrondissement in [1, 2, 3, 4, 5, 6, 7, 8]:  # Centre (zones calmes)
                    prob_alcool *= 0.9
                    prob_nuit *= 0.95
                elif arrondissement >= 16:  # Ouest (zones résidentielles)
                    prob_alcool *= 0.85
                    prob_nuit *= 0.9
                
                # S'assurer que les probabilités restent dans [0, 1]
                prob_alcool = min(max(prob_alcool, 0.0), 0.5)  # Max 50%
                prob_nuit = min(max(prob_nuit, 0.0), 0.6)  # Max 60%
                
                matrices[microzone_id][type_incident] = {
                    'prob_alcool': prob_alcool,
                    'prob_nuit': prob_nuit,
                    'facteur_ete_alcool': facteur_ete_alcool,
                    'heures_nuit': heures_nuit
                }
        
        logger.info(f"✅ Matrices alcool/nuit calculées pour {len(matrices)} microzones")
        return matrices
    
    # ============================================================================
    # 6. SAISONNALITÉ
    # ============================================================================
    
    def calculate_matrices_saisonnalite(self, microzones: gpd.GeoDataFrame) -> Dict:
        """
        Calcule les facteurs de saisonnalité pour chaque microzone.
        
        Saisons : hiver, inter-saison, été
        Facteurs de modulation selon le type d'incident et la saison.
        
        Basé sur les patterns observés à Paris :
        - Agressions : plus en été (sorties, chaleur, tensions)
        - Incendies : plus en hiver (chauffage, bougies, Noël)
        - Accidents : plus en hiver (routes glissantes, visibilité réduite)
        
        Les facteurs sont appliqués comme multiplicateurs aux probabilités de base.
        
        Returns:
            Dict[microzone_id][type_incident][saison] = facteur_modulation
            facteur_modulation : float (ex: 1.25 = +25% en été pour agressions)
        """
        logger.info("🔄 Calcul des matrices saisonnalité...")
        
        matrices = {}
        
        # Facteurs de base par type et saison (basés sur statistiques réelles Paris)
        facteurs_base = {
            'agressions': {
                'hiver': 0.85,      # -15% en hiver (moins de sorties)
                'intersaison': 1.0, # Référence (printemps/automne)
                'ete': 1.25         # +25% en été (sorties, chaleur, tensions)
            },
            'incendies': {
                'hiver': 1.3,       # +30% en hiver (chauffage, bougies, Noël)
                'intersaison': 1.0, # Référence
                'ete': 0.9          # -10% en été (moins de chauffage)
            },
            'accidents': {
                'hiver': 1.1,       # +10% en hiver (routes glissantes, visibilité)
                'intersaison': 1.0, # Référence
                'ete': 0.95         # -5% en été (meilleures conditions)
            }
        }
        
        for idx, mz in microzones.iterrows():
            microzone_id = mz['microzone_id']
            arrondissement = int(mz['arrondissement'])
            
            matrices[microzone_id] = {}
            
            for type_incident in self.types_incidents:
                matrices[microzone_id][type_incident] = {}
                
                for saison in self.saisons:
                    facteur = facteurs_base[type_incident][saison]
                    
                    # Ajustements selon l'arrondissement
                    if arrondissement in [1, 2, 3, 4, 5, 6, 7, 8]:  # Centre
                        # Moins de variation saisonnière en centre (activité constante)
                        facteur = 1.0 + (facteur - 1.0) * 0.7
                    elif arrondissement in [18, 19, 20]:  # Nord-est
                        # Plus de variation saisonnière dans les zones à risque
                        facteur = 1.0 + (facteur - 1.0) * 1.1
                    
                    # S'assurer que le facteur reste dans une plage raisonnable [0.5, 2.0]
                    facteur = min(max(facteur, 0.5), 2.0)
                    
                    matrices[microzone_id][type_incident][saison] = facteur
        
        logger.info(f"✅ Matrices saisonnalité calculées pour {len(matrices)} microzones")
        return matrices

    # ============================================================================
    # 7. EFFET D'AUGMENTATION (règles fixes – Story 1.4.4 AC4, Epic 4.4)
    # ============================================================================

    def calculate_regles_effet_augmentation(self) -> Dict:
        """
        Règles fixes pour l'effet d'augmentation (+0.1).
        Conditions : délinquance voisin > microzone OU >5 incidents totaux dans 8 voisins.
        Max +0.2. Utilisées avec matrices_voisin (seuil_activation) et données délinquance.
        """
        logger.info("🔄 Calcul des règles effet d'augmentation...")
        regles = {
            "seuil_voisins_incidents": 5,
            "delta_par_condition": 0.1,
            "max_effet": 0.2,
            "conditions": [
                "delinquance_voisin_superieure",
                "voisins_incidents_sup_seuil",
            ],
        }
        logger.info("✅ Règles effet d'augmentation calculées")
        return regles

    # ============================================================================
    # 8. PATTERN 4j→7j (matrice de transition fixe – Story 1.4.4 AC5, Epic 4.5)
    # ============================================================================

    def calculate_pattern_7j_transition(self) -> Dict:
        """
        Matrice de transition fixe 7 jours : +0.1 agressions/jour, pic jour 3.
        Déclencheur : 1 agression 4 jours consécutifs. Story 1.4.4.
        """
        logger.info("🔄 Calcul pattern 7j (transition fixe)...")
        amplitude_base = 0.1
        amplitude_pic = 0.15
        jour_pic = 2  # 0-based : jour 3
        vecteur = [amplitude_base] * 7
        vecteur[jour_pic] = amplitude_pic
        pattern = {
            "type_pattern": "7j",
            "type_incident": "agressions",
            "vecteur_7j": vecteur,
            "amplitude_base": amplitude_base,
            "amplitude_pic": amplitude_pic,
            "jour_pic": jour_pic + 1,
            "trigger": {
                "fenetre_jours": 4,
                "type_incident": "agressions",
                "min_par_jour": 1,
                "consecutifs": True,
            },
        }
        logger.info("✅ Pattern 7j calculé")
        return pattern

    # ============================================================================
    # 9. PATTERN 60j (matrice de transition fixe – Story 1.4.4 AC6, Epic 4.6)
    # ============================================================================

    def calculate_pattern_60j_transition(self) -> Dict:
        """
        Matrice de transition fixe 60 jours : +0.05 (j1–20), -0.05 (j21–40), +0.1 (j41–60).
        Déclencheur : aucune agression pendant 7 jours. Story 1.4.4.
        """
        logger.info("🔄 Calcul pattern 60j (transition fixe)...")
        a1, a2, a3 = 0.05, -0.05, 0.1
        vecteur = [a1] * 20 + [a2] * 20 + [a3] * 20
        pattern = {
            "type_pattern": "60j",
            "type_incident": "agressions",
            "vecteur_60j": vecteur,
            "amplitude_phase1": a1,
            "amplitude_phase2": a2,
            "amplitude_phase3": a3,
            "phase1_jours": (1, 20),
            "phase2_jours": (21, 40),
            "phase3_jours": (41, 60),
            "trigger": {
                "fenetre_jours": 7,
                "type_incident": "agressions",
                "min_total": 0,
            },
        }
        logger.info("✅ Pattern 60j calculé")
        return pattern

    # ============================================================================
    # 10. RÈGLES PATTERNS (limitation, priorité – Story 1.4.4 AC7, Epic 4.7)
    # ============================================================================

    def calculate_regles_patterns(self) -> Dict:
        """Règles fixes : max 3 patterns actifs par microzone."""
        logger.info("🔄 Calcul des règles patterns...")
        regles = {
            "max_patterns_actifs": 3,
            "ordre_priorite": ["7j", "60j"],
        }
        logger.info("✅ Règles patterns calculées")
        return regles


def _get_intermediate_patterns_dir(config: Dict, project_root: Path) -> Path:
    """Retourne data/intermediate/patterns (fichiers temporaires pour génération patterns)."""
    base = config.get("paths", {}).get("data_intermediate", "data/intermediate")
    path = Path(base) / "patterns"
    if not path.is_absolute():
        path = project_root / path
    return path


def _write_temp_pattern_files(
    calculator: "MatricesCorrelationCalculator",
    intermediate_dir: Path,
) -> None:
    """
    Écrit les fichiers temporaires (4j, 7j, 60j) permettant de générer les patterns
    qui influencent les probabilités. Stockés dans data/intermediate/patterns/.
    """
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Fichiers temporaires patterns → {intermediate_dir}")

    pattern_4j_temp = {
        "type_pattern": "4j",
        "type_incident": "agressions",
        "facteurs_modulation": {"regime": {"stable": 1.0, "deterioration": 1.2, "crise": 1.5}, "saison": {"hiver": 0.9, "ete": 1.1, "intersaison": 1.0}},
        "usage": "influence_probabilites_court_terme",
    }
    pattern_7j_temp = {
        "type_pattern": "7j",
        "type_incident": "agressions",
        "amplitude_base": 0.1,
        "amplitude_pic": 0.15,
        "jour_pic": 3,
        "trigger": {"fenetre_jours": 4, "type_incident": "agressions", "min_par_jour": 1, "consecutifs": True},
    }
    pattern_60j_temp = {
        "type_pattern": "60j",
        "type_incident": "agressions",
        "amplitude_phase1": 0.05,
        "amplitude_phase2": -0.05,
        "amplitude_phase3": 0.1,
        "phase1_jours": (1, 20),
        "phase2_jours": (21, 40),
        "phase3_jours": (41, 60),
        "trigger": {"fenetre_jours": 7, "type_incident": "agressions", "min_total": 0},
    }

    for name, data in [
        ("pattern_4j_temp.pkl", pattern_4j_temp),
        ("pattern_7j_temp.pkl", pattern_7j_temp),
        ("pattern_60j_temp.pkl", pattern_60j_temp),
    ]:
        p = intermediate_dir / name
        with open(p, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"   ✅ {name}")


def _generate_patterns_from_temp(intermediate_dir: Path) -> Tuple[Dict, Dict]:
    """
    Génère les structures pattern 7j et 60j (transition) à partir des fichiers temporaires.
    Ces structures influencent les probabilités en simulation.
    """
    pattern_7j_transition: Dict = {}
    pattern_60j_transition: Dict = {}

    p7 = intermediate_dir / "pattern_7j_temp.pkl"
    if p7.exists():
        with open(p7, "rb") as f:
            t = pickle.load(f)
        v = [t["amplitude_base"]] * 7
        v[t["jour_pic"] - 1] = t["amplitude_pic"]
        pattern_7j_transition = {
            "type_pattern": "7j",
            "type_incident": t["type_incident"],
            "vecteur_7j": v,
            "amplitude_base": t["amplitude_base"],
            "amplitude_pic": t["amplitude_pic"],
            "jour_pic": t["jour_pic"],
            "trigger": t["trigger"],
        }
        logger.info("   ✅ Pattern 7j généré depuis temp")
    else:
        raise FileNotFoundError(f"Fichier temporaire manquant: {p7}")

    p60 = intermediate_dir / "pattern_60j_temp.pkl"
    if p60.exists():
        with open(p60, "rb") as f:
            t = pickle.load(f)
        n1 = t["phase1_jours"][1] - t["phase1_jours"][0] + 1
        n2 = t["phase2_jours"][1] - t["phase2_jours"][0] + 1
        n3 = t["phase3_jours"][1] - t["phase3_jours"][0] + 1
        v = [t["amplitude_phase1"]] * n1 + [t["amplitude_phase2"]] * n2 + [t["amplitude_phase3"]] * n3
        pattern_60j_transition = {
            "type_pattern": "60j",
            "type_incident": t["type_incident"],
            "vecteur_60j": v,
            "amplitude_phase1": t["amplitude_phase1"],
            "amplitude_phase2": t["amplitude_phase2"],
            "amplitude_phase3": t["amplitude_phase3"],
            "phase1_jours": t["phase1_jours"],
            "phase2_jours": t["phase2_jours"],
            "phase3_jours": t["phase3_jours"],
            "trigger": t["trigger"],
        }
        logger.info("   ✅ Pattern 60j généré depuis temp")
    else:
        raise FileNotFoundError(f"Fichier temporaire manquant: {p60}")

    return pattern_7j_transition, pattern_60j_transition


def precompute_matrices_correlation(config: Dict, output_dir: Path) -> bool:
    """
    Fonction principale de pré-calcul des matrices de corrélation.
    
    Returns:
        True si succès, False sinon
    """
    try:
        project_root = Path(__file__).resolve().parent.parent
        
        # 1. Charger les microzones
        logger.info("📂 Chargement des microzones...")
        microzones_file = output_dir / "microzones.pkl"
        if not microzones_file.exists():
            logger.error(f"❌ Fichier microzones introuvable: {microzones_file}")
            return False
        
        with open(microzones_file, 'rb') as f:
            microzones = pickle.load(f)
        
        logger.info(f"✅ {len(microzones)} microzones chargées")
        
        # 2. Créer le calculateur
        calculator = MatricesCorrelationCalculator(config)
        
        # 3. Fichiers temporaires patterns (4j, 7j, 60j) pour génération
        intermediate_dir = _get_intermediate_patterns_dir(config, project_root)
        _write_temp_pattern_files(calculator, intermediate_dir)
        
        # 4. Générer patterns (transition) depuis temp → influencent les probabilités
        logger.info("🔄 Génération des patterns depuis fichiers temporaires...")
        pattern_7j_transition, pattern_60j_transition = _generate_patterns_from_temp(intermediate_dir)
        
        # 5. Calculer toutes les matrices
        logger.info("🔄 Calcul de toutes les matrices de corrélation...")
        
        matrices_intra_type = calculator.calculate_matrices_intra_type(microzones)
        matrices_inter_type = calculator.calculate_matrices_inter_type(microzones)
        matrices_voisin = calculator.calculate_matrices_voisin(microzones)
        matrices_trafic = calculator.calculate_matrice_trafic(microzones)
        matrices_alcool_nuit = calculator.calculate_matrices_alcool_nuit(microzones)
        matrices_saisonnalite = calculator.calculate_matrices_saisonnalite(microzones)
        regles_effet_augmentation = calculator.calculate_regles_effet_augmentation()
        regles_patterns = calculator.calculate_regles_patterns()
        
        # 4. Sauvegarder toutes les matrices et structures fixes
        logger.info("💾 Sauvegarde des matrices...")
        
        matrices_files = {
            'matrices_correlation_intra_type.pkl': matrices_intra_type,
            'matrices_correlation_inter_type.pkl': matrices_inter_type,
            'matrices_voisin.pkl': matrices_voisin,
            'matrices_trafic.pkl': matrices_trafic,
            'matrices_alcool_nuit.pkl': matrices_alcool_nuit,
            'matrices_saisonnalite.pkl': matrices_saisonnalite,
            'regles_effet_augmentation.pkl': regles_effet_augmentation,
            'pattern_7j_transition.pkl': pattern_7j_transition,
            'pattern_60j_transition.pkl': pattern_60j_transition,
            'regles_patterns.pkl': regles_patterns,
        }
        
        for filename, data in matrices_files.items():
            filepath = output_dir / filename
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"✅ {filename} sauvegardé")
        
        # 5. Vérifications
        logger.info("🔍 Vérifications...")
        
        # Vérifier que toutes les microzones ont des matrices
        assert len(matrices_intra_type) == len(microzones), \
            f"Nombre de microzones incorrect dans matrices_intra_type"
        assert len(matrices_voisin) == len(microzones), \
            f"Nombre de microzones incorrect dans matrices_voisin"
        
        # Vérifier structure matrices intra-type
        for mz_id, types in matrices_intra_type.items():
            for type_incident, matrice in types.items():
                assert matrice.shape == (3, 3), \
                    f"Matrice intra-type {mz_id}/{type_incident} doit être 3×3"
                # Vérifier normalisation (somme de chaque ligne ≈ 1)
                for i in range(3):
                    assert abs(matrice[i, :].sum() - 1.0) < 0.01, \
                        f"Ligne {i} de {mz_id}/{type_incident} doit sommer à 1"
        
        # Vérifier matrices voisin (8 voisins)
        for mz_id, data in matrices_voisin.items():
            assert len(data['voisins']) == 8, \
                f"Microzone {mz_id} doit avoir 8 voisins"
            assert len(data['poids_influence']) == 8, \
                f"Microzone {mz_id} doit avoir 8 poids"
            assert abs(sum(data['poids_influence']) - 1.0) < 0.01, \
                f"Poids voisins {mz_id} doivent sommer à 1"
        
        # Vérifier structures fixes (effet augmentation, patterns, regles)
        assert regles_effet_augmentation['seuil_voisins_incidents'] == 5
        assert regles_effet_augmentation['max_effet'] == 0.2
        assert len(pattern_7j_transition['vecteur_7j']) == 7
        assert pattern_7j_transition['jour_pic'] == 3
        assert len(pattern_60j_transition['vecteur_60j']) == 60
        assert pattern_60j_transition['amplitude_phase1'] == 0.05
        assert pattern_60j_transition['amplitude_phase2'] == -0.05
        assert pattern_60j_transition['amplitude_phase3'] == 0.1
        assert regles_patterns['max_patterns_actifs'] == 3
        
        logger.info("✅ Toutes les vérifications passées")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur pré-calcul matrices corrélation: {e}", exc_info=True)
        return False
