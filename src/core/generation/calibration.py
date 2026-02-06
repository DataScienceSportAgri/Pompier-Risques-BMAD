"""
Constantes de calibration pour une génération réaliste (microzone moyenne).
Cibles : ~70 % du temps tous les vecteurs à 0 ; répartition type × gravité selon statistiques cibles.

Interaction avec data/source_data :
- calibration.py ne charge aucun fichier de source_data. Il définit uniquement des constantes
  et get_calibration_cross_probabilities().
- Vecteurs statiques (vecteurs_statiques.pkl) : chargés par StaticVectorLoader, qui utilise
  les cibles de calibration (BASE_INTENSITY_*, DEFAULT_INTENSITES_BY_TYPE) pour RECALIBRER
  la moyenne par type : les intensités brutes sont ramenées à une moyenne = cible, en
  conservant les rapports relatifs entre microzones.
- Matrices (matrices_correlation_intra_type.pkl, inter_type, matrices_voisin.pkl,
  matrices_saisonnalite.pkl) : chargées par _loader, passées à MatrixModulator. Elles
  MODULENT l'intensité λ (facteurs par microzone, type, voisins, saison). Elles ne
  fournissent pas les probabilités croisées (bénin/moyen/grave) : celles-ci viennent
  de get_calibration_cross_probabilities() dans IntensityCalculator. Calibration et
  matrices source_data sont donc indépendantes : les matrices modulent λ, la
  calibration fournit les cibles de moyenne, les probas croisées 3×3 et l’alpha
  zero-inflation.
"""

from typing import Dict, Tuple

import numpy as np

from ..data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)

# ---------------------------------------------------------------------------
# Cibles probabilistes (par jour, microzone moyenne) — pour tests de vérification
# ---------------------------------------------------------------------------
# Probabilité que tous les vecteurs (accident, agression, incendie) soient nuls
TARGET_P_ALL_ZEROS = 0.70

# Par type : proba d'avoir exactement 1 incident de la gravité donnée (bénin, moyen, grave)
# Format: (p_1_benin, p_1_moyen, p_1_grave)
TARGET_PROBA_ACCIDENT = (0.14, 0.024, 0.004)   # 14 %, 2.4 %, 0.4 %
TARGET_PROBA_AGRESSION = (0.09, 0.02, 0.003)   # 9 %, 2 %, 0.3 %
TARGET_PROBA_INCENDIE = (0.06, 0.018, 0.002)  # 6 %, 1.8 %, 0.2 %

# Proba d'au moins un incident par type (somme des trois gravités)
TARGET_P_AT_LEAST_ONE_ACCIDENT = 0.14 + 0.024 + 0.004   # 0.168
TARGET_P_AT_LEAST_ONE_AGRESSION = 0.09 + 0.02 + 0.003   # 0.113
TARGET_P_AT_LEAST_ONE_INCENDIE = 0.06 + 0.018 + 0.002   # 0.08

# Répartition (bénin, moyen, grave) conditionnelle à "exactement 1 incident"
# accident: (14/16.8, 2.4/16.8, 0.4/16.8)
SPLIT_ACCIDENT = (0.14 / 0.168, 0.024 / 0.168, 0.004 / 0.168)
SPLIT_AGRESSION = (0.09 / 0.113, 0.02 / 0.113, 0.003 / 0.113)
SPLIT_INCENDIE = (0.06 / 0.08, 0.018 / 0.08, 0.002 / 0.08)

# ---------------------------------------------------------------------------
# Paramètres de génération pour approcher ces cibles
# ---------------------------------------------------------------------------
# Alpha zero-inflation : p_zero = exp(-alpha * lambda * regime) / (1 + exp(-alpha * lambda * regime))
ZERO_INFLATION_ALPHA = 0.5

# Intensités de base totale (lambda) par type pour une microzone "moyenne"
# (régime Stable, autres facteurs ~1) pour obtenir P(N>=1) ≈ cible
BASE_INTENSITY_ACCIDENT = 0.35
BASE_INTENSITY_AGRESSION = 0.25
BASE_INTENSITY_INCENDIE = 0.15

# Vecteurs (bénin, moyen, grave) × facteurs (0.5, 1.0, 2.0) pour obtenir ces intensités totales
# Intensité totale = benin*0.5 + moyen*1.0 + grave*2.0
DEFAULT_INTENSITES_BY_TYPE: Dict[str, Tuple[float, float, float]] = {
    INCIDENT_TYPE_ACCIDENT: (0.26, 0.14, 0.04),   # -> 0.13+0.14+0.08 = 0.35
    INCIDENT_TYPE_AGRESSION: (0.20, 0.08, 0.035), # -> 0.10+0.08+0.07 = 0.25
    INCIDENT_TYPE_INCENDIE: (0.10, 0.06, 0.02),   # -> 0.05+0.06+0.04 = 0.15
}

# Probabilités croisées (ligne "dominante bénin J-1") : (prob bénin, prob moyen, prob grave) J+1
# Pour coller aux répartitions cibles quand N=1
CROSS_PROB_ROW_BENIN_ACCIDENT = np.array([SPLIT_ACCIDENT[0], SPLIT_ACCIDENT[1], SPLIT_ACCIDENT[2]])
CROSS_PROB_ROW_BENIN_AGRESSION = np.array([SPLIT_AGRESSION[0], SPLIT_AGRESSION[1], SPLIT_AGRESSION[2]])
CROSS_PROB_ROW_BENIN_INCENDIE = np.array([SPLIT_INCENDIE[0], SPLIT_INCENDIE[1], SPLIT_INCENDIE[2]])

def get_calibration_cross_probabilities() -> Dict[str, np.ndarray]:
    """
    Retourne les matrices 3x3 de probabilités croisées calibrées (réaliste).
    Ligne 0 (J-1 bénin) = répartition cible ; lignes 1 et 2 = persistance modérée.
    Pour l'accident : persistance "grave" réduite (lignes 1 et 2) pour éviter
    une fréquence empirique trop élevée d'accidents graves.
    """
    def make_matrix(row0: np.ndarray, row1=None, row2=None) -> np.ndarray:
        row0 = np.asarray(row0, dtype=float)
        row0 = row0 / row0.sum()
        if row1 is None:
            row1 = np.array([0.2, 0.6, 0.2])
        if row2 is None:
            row2 = np.array([0.1, 0.2, 0.7])
        row1 = np.asarray(row1, dtype=float) / np.sum(row1)
        row2 = np.asarray(row2, dtype=float) / np.sum(row2)
        return np.array([row0, row1, row2])

    # Accident : moins de persistance "grave" (évite runs grave → grave), poids légèrement réduits
    row1_accident = np.array([0.37, 0.61, 0.02])
    row2_accident = np.array([0.42, 0.535, 0.045])

    # Agression : moins de persistance "grave" pour obtenir un peu moins d'agressions graves
    row1_agression = np.array([0.38, 0.55, 0.07])
    row2_agression = np.array([0.42, 0.48, 0.10])

    # Incendie : moins de persistance "grave" pour en avoir légèrement moins
    row1_incendie = np.array([0.40, 0.54, 0.06])
    row2_incendie = np.array([0.45, 0.48, 0.07])

    return {
        INCIDENT_TYPE_ACCIDENT: make_matrix(
            CROSS_PROB_ROW_BENIN_ACCIDENT, row1_accident, row2_accident
        ),
        INCIDENT_TYPE_AGRESSION: make_matrix(
            CROSS_PROB_ROW_BENIN_AGRESSION, row1_agression, row2_agression
        ),
        INCIDENT_TYPE_INCENDIE: make_matrix(
            CROSS_PROB_ROW_BENIN_INCENDIE, row1_incendie, row2_incendie
        ),
    }
