"""
Tests unitaires pour Zero-Inflated Poisson.
Story 2.2.1 - Génération vecteurs journaliers
"""

import numpy as np
import pytest

from src.core.generation.zero_inflated_poisson import (
    calculate_zero_inflation_probability,
    sample_multinomial_counts,
    sample_zero_inflated_poisson,
)


class TestZeroInflationProbability:
    """Tests pour calculate_zero_inflation_probability."""
    
    def test_zero_inflation_probability_range(self):
        """Test que la probabilité est dans [0, 1]."""
        for intensity in [0.0, 0.5, 1.0, 2.0, 5.0, 10.0]:
            for regime_factor in [1.0, 1.3, 2.0]:
                prob = calculate_zero_inflation_probability(intensity, regime_factor)
                assert 0.0 <= prob <= 1.0
    
    def test_zero_inflation_decreases_with_intensity(self):
        """Test que la probabilité de zero-inflation diminue avec l'intensité."""
        prob_low = calculate_zero_inflation_probability(0.1, 1.0)
        prob_high = calculate_zero_inflation_probability(5.0, 1.0)
        
        assert prob_low > prob_high
    
    def test_zero_inflation_decreases_with_regime_factor(self):
        """Test que la probabilité de zero-inflation diminue avec le facteur régime.
        
        Quand le facteur régime augmente, l'intensité ajustée augmente,
        donc la probabilité de zero-inflation diminue (moins de zéros attendus).
        """
        prob_stable = calculate_zero_inflation_probability(1.0, 1.0)
        prob_crise = calculate_zero_inflation_probability(1.0, 2.0)
        
        # Avec un facteur régime plus élevé, l'intensité ajustée est plus grande,
        # donc la probabilité de zero-inflation est plus faible
        assert prob_crise < prob_stable


class TestSampleZeroInflatedPoisson:
    """Tests pour sample_zero_inflated_poisson."""
    
    def test_sample_non_negative(self):
        """Test que l'échantillon est ≥ 0."""
        rng = np.random.Generator(np.random.PCG64(42))
        
        for _ in range(100):
            count = sample_zero_inflated_poisson(1.0, 0.3, rng)
            assert count >= 0
    
    def test_sample_zero_inflation(self):
        """Test que zero-inflation fonctionne."""
        rng = np.random.Generator(np.random.PCG64(42))
        
        # Avec probabilité de zero-inflation = 1.0, toujours 0
        count = sample_zero_inflated_poisson(10.0, 1.0, rng)
        assert count == 0
    
    def test_sample_poisson_when_no_zero_inflation(self):
        """Test que sans zero-inflation, on échantillonne depuis Poisson."""
        rng = np.random.Generator(np.random.PCG64(42))
        
        # Avec probabilité de zero-inflation = 0.0, toujours Poisson
        counts = [sample_zero_inflated_poisson(2.0, 0.0, rng) for _ in range(1000)]
        
        # La moyenne devrait être proche de 2.0
        mean_count = np.mean(counts)
        assert 1.5 <= mean_count <= 2.5


class TestSampleMultinomialCounts:
    """Tests pour sample_multinomial_counts."""
    
    def test_sample_multinomial_counts_sum(self):
        """Test que la somme des comptes = total_count."""
        rng = np.random.Generator(np.random.PCG64(42))
        
        for total in [0, 1, 5, 10, 100]:
            counts = sample_multinomial_counts(
                total,
                (0.33, 0.33, 0.34),
                rng
            )
            assert sum(counts) == total
    
    def test_sample_multinomial_counts_non_negative(self):
        """Test que tous les comptes sont ≥ 0."""
        rng = np.random.Generator(np.random.PCG64(42))
        
        counts = sample_multinomial_counts(10, (0.5, 0.3, 0.2), rng)
        
        assert counts[0] >= 0
        assert counts[1] >= 0
        assert counts[2] >= 0
    
    def test_sample_multinomial_counts_zero_total(self):
        """Test que total_count = 0 retourne (0, 0, 0)."""
        rng = np.random.Generator(np.random.PCG64(42))
        
        counts = sample_multinomial_counts(0, (0.5, 0.3, 0.2), rng)
        
        assert counts == (0, 0, 0)
    
    def test_sample_multinomial_counts_normalized_probs(self):
        """Test que les probabilités sont normalisées."""
        rng = np.random.Generator(np.random.PCG64(42))
        
        # Probabilités qui ne somment pas à 1
        counts = sample_multinomial_counts(10, (0.5, 0.3, 0.1), rng)
        
        assert sum(counts) == 10
