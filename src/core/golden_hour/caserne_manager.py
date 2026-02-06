"""
Gestionnaire de casernes et suivi du staff.
Story 2.2.3 - Golden Hour
"""

from typing import Dict, List, Optional, Tuple

import numpy as np

# Constantes
STAFF_TOTAL_PAR_CASERNE = 30
SEUIL_MIN_POMPIERS = 3  # Minimum requis pour une intervention
POMPIERS_PAR_INTERVENTION = 4  # Nombre de pompiers par intervention


class CaserneManager:
    """
    Gestionnaire de casernes avec suivi du staff disponible.
    
    Gère :
    - Staff total et disponible par caserne
    - Retrait/remise progressive des pompiers
    - Calcul de la caserne disponible la plus proche
    """
    
    def __init__(
        self,
        caserne_ids: List[str],
        staff_total: Optional[Dict[str, int]] = None,
        seed: Optional[int] = None
    ):
        """
        Initialise le gestionnaire de casernes.
        
        Args:
            caserne_ids: Liste des identifiants de casernes
            staff_total: Staff total par caserne (si None, utilise STAFF_TOTAL_PAR_CASERNE)
            seed: Seed pour reproductibilité
        """
        self.caserne_ids = caserne_ids
        self.rng = np.random.Generator(np.random.PCG64(seed))
        
        # Table permanente staff par caserne
        # Structure : Dict[caserne_id, {'staff_total': int, 'staff_disponible': int, 'interventions_en_cours': List[dict]}]
        self.staff_casernes: Dict[str, Dict] = {}
        
        for caserne_id in caserne_ids:
            staff = staff_total.get(caserne_id, STAFF_TOTAL_PAR_CASERNE) if staff_total else STAFF_TOTAL_PAR_CASERNE
            self.staff_casernes[caserne_id] = {
                'staff_total': staff,
                'staff_disponible': staff,
                'interventions_en_cours': []
            }
    
    def retirer_pompiers(
        self,
        caserne_id: str,
        nb_pompiers: int,
        jour: int,
        duree_retour: int = 1
    ) -> bool:
        """
        Retire des pompiers d'une caserne pour une intervention.
        
        Args:
            caserne_id: Identifiant de la caserne
            nb_pompiers: Nombre de pompiers à retirer
            jour: Jour de l'intervention
            duree_retour: Durée avant retour des pompiers (en jours)
        
        Returns:
            True si retrait réussi, False si staff insuffisant
        """
        if caserne_id not in self.staff_casernes:
            return False
        
        caserne = self.staff_casernes[caserne_id]
        
        # Vérifier disponibilité
        if caserne['staff_disponible'] < nb_pompiers:
            return False
        
        # Retirer les pompiers
        caserne['staff_disponible'] -= nb_pompiers
        
        # Enregistrer l'intervention
        caserne['interventions_en_cours'].append({
            'jour': jour,
            'nb_pompiers': nb_pompiers,
            'duree_retour': duree_retour
        })
        
        return True
    
    def remettre_pompiers(self, jour: int) -> None:
        """
        Remet progressivement les pompiers selon les interventions terminées.
        
        Args:
            jour: Jour actuel
        """
        for caserne_id, caserne in self.staff_casernes.items():
            interventions_terminees = []
            
            for intervention in caserne['interventions_en_cours']:
                jour_retour = intervention['jour'] + intervention['duree_retour']
                
                # Les pompiers reviennent APRÈS duree_retour jours, donc au jour suivant
                # Si duree_retour=1, ils reviennent au jour 2 (jour 0 + 1 + 1)
                if jour > jour_retour:
                    # Remettre les pompiers
                    caserne['staff_disponible'] += intervention['nb_pompiers']
                    # S'assurer qu'on ne dépasse pas le staff total
                    caserne['staff_disponible'] = min(
                        caserne['staff_disponible'],
                        caserne['staff_total']
                    )
                    interventions_terminees.append(intervention)
            
            # Retirer les interventions terminées
            for intervention in interventions_terminees:
                caserne['interventions_en_cours'].remove(intervention)
    
    def get_staff_disponible(self, caserne_id: str) -> int:
        """
        Retourne le staff disponible pour une caserne.
        
        Args:
            caserne_id: Identifiant de la caserne
        
        Returns:
            Nombre de pompiers disponibles
        """
        if caserne_id not in self.staff_casernes:
            return 0
        
        return self.staff_casernes[caserne_id]['staff_disponible']
    
    def trouver_caserne_disponible(
        self,
        microzone_id: str,
        distances_caserne_microzone: Dict[str, Dict[str, float]],
        nb_pompiers_requis: int = POMPIERS_PAR_INTERVENTION
    ) -> Optional[Tuple[str, float]]:
        """
        Trouve la caserne disponible la plus proche pour une microzone.
        
        Args:
            microzone_id: Identifiant de la microzone
            distances_caserne_microzone: Dictionnaire {caserne_id: {microzone_id: distance}}
            nb_pompiers_requis: Nombre de pompiers requis (défaut: POMPIERS_PAR_INTERVENTION)
        
        Returns:
            Tuple (caserne_id, distance) ou None si aucune caserne disponible
        """
        # Trier les casernes par distance
        casernes_proches = []
        
        for caserne_id in self.caserne_ids:
            if caserne_id in distances_caserne_microzone:
                distances = distances_caserne_microzone[caserne_id]
                if microzone_id in distances:
                    distance = distances[microzone_id]
                    staff_disponible = self.get_staff_disponible(caserne_id)
                    casernes_proches.append((caserne_id, distance, staff_disponible))
        
        if not casernes_proches:
            return None
        
        # Trier par distance
        casernes_proches.sort(key=lambda x: x[1])
        
        # Chercher la première caserne avec staff suffisant
        for caserne_id, distance, staff_disponible in casernes_proches:
            if staff_disponible >= nb_pompiers_requis:
                return (caserne_id, distance)
        
        # Si aucune disponible, prendre la plus proche quand même (demande effective)
        # mais avec staff insuffisant
        if casernes_proches:
            caserne_id, distance, _ = casernes_proches[0]
            return (caserne_id, distance)
        
        return None
    
    def get_stress_caserne(self, caserne_id: str) -> float:
        """
        Calcule le stress d'une caserne (nombre d'interventions en cours).
        
        Stress = nombre d'interventions en cours × 0.4
        
        Args:
            caserne_id: Identifiant de la caserne
        
        Returns:
            Facteur de stress (≥ 0.0)
        """
        if caserne_id not in self.staff_casernes:
            return 0.0
        
        nb_interventions = len(self.staff_casernes[caserne_id]['interventions_en_cours'])
        return nb_interventions * 0.4
    
    def to_dict(self) -> Dict:
        """
        Convertit l'état des casernes en dictionnaire (pour sérialisation).
        
        Returns:
            Dictionnaire représentant l'état
        """
        return {
            caserne_id: {
                'staff_total': caserne['staff_total'],
                'staff_disponible': caserne['staff_disponible'],
                'interventions_en_cours': caserne['interventions_en_cours'].copy()
            }
            for caserne_id, caserne in self.staff_casernes.items()
        }
