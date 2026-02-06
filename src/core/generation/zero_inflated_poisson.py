"""
Modèle Zero-Inflated Poisson pour génération de vecteurs.
Story 2.2.1 - Génération vecteurs journaliers
"""

from typing import Tuple

import numpy as np

from .calibration import ZERO_INFLATION_ALPHA


def calculate_zero_inflation_probability(
    intensity: float,
    regime_factor: float = 1.0
) -> float:
    """
    Calcule la probabilité de zero-inflation selon les formules Session 4.
    
    Formule : p_zero = exp(-α * λ * regime_factor) / (1 + exp(-α * λ * regime_factor))
    où α est un paramètre de calibration (calibration réaliste).
    
    Args:
        intensity: Intensité λ
        regime_factor: Facteur du régime (1.0, 1.3, 2.0)
    
    Returns:
        Probabilité de zero-inflation dans [0, 1]
    """
    alpha = ZERO_INFLATION_ALPHA
    
    # Calcul de la probabilité
    adjusted_intensity = intensity * regime_factor
    exp_term = np.exp(-alpha * adjusted_intensity)
    p_zero = exp_term / (1.0 + exp_term)
    
    # Clamp dans [0, 1]
    return float(np.clip(p_zero, 0.0, 1.0))


def sample_zero_inflated_poisson(
    intensity: float,
    zero_inflation_prob: float,
    rng: np.random.Generator
) -> int:
    """
    Échantillonne depuis une distribution Zero-Inflated Poisson.
    
    Args:
        intensity: Intensité λ de la distribution Poisson
        zero_inflation_prob: Probabilité de zero-inflation
        rng: Générateur aléatoire NumPy
    
    Returns:
        Nombre d'incidents (≥ 0)
    """
    # Décider si on est dans le cas "zero-inflated"
    if rng.random() < zero_inflation_prob:
        return 0
    
    # Sinon, échantillonner depuis Poisson
    return rng.poisson(intensity)


def sample_multinomial_counts(
    total_count: int,
    probabilities: Tuple[float, float, float],
    rng: np.random.Generator
) -> Tuple[int, int, int]:
    """
    Échantillonne les comptes (bénin, moyen, grave) depuis une multinomiale.
    
    Args:
        total_count: Nombre total d'incidents
        probabilities: Probabilités (prob_bénin, prob_moyen, prob_grave)
        rng: Générateur aléatoire NumPy
    
    Returns:
        Tuple (count_bénin, count_moyen, count_grave)
    """
    if total_count == 0:
        return (0, 0, 0)
    
    # Normaliser les probabilités
    probs = np.array(probabilities)
    probs = probs / np.sum(probs)
    
    # Échantillonner depuis multinomiale
    counts = rng.multinomial(total_count, probs)
    
    return (int(counts[0]), int(counts[1]), int(counts[2]))
