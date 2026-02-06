"""
Tests unitaires pour PositiveEventGenerator.
Story 2.2.8 - Événements positifs et règle prix m²
"""

import pytest

from src.core.events.positive_event_generator import (
    LAMBDA_POSITIVE_EVENTS,
    PositiveEventGenerator,
    PROB_AMELIORATION_MATERIEL,
    PROB_FIN_TRAVAUX,
    PROB_NOUVELLE_CASERNE,
)
from src.core.state.events_state import EventsState


class TestPositiveEventGenerator:
    """Tests pour PositiveEventGenerator."""
    
    @pytest.fixture
    def limites_microzone_arrondissement(self):
        """Limites microzone → arrondissement pour les tests."""
        return {
            "MZ_11_01": 11,
            "MZ_11_02": 11,
            "MZ_12_01": 12
        }
    
    @pytest.fixture
    def arrondissements(self):
        """Arrondissements pour les tests."""
        return [11, 12]
    
    @pytest.fixture
    def positive_event_generator(self, limites_microzone_arrondissement, arrondissements):
        """Générateur d'événements positifs pour les tests."""
        return PositiveEventGenerator(
            limites_microzone_arrondissement=limites_microzone_arrondissement,
            arrondissements=arrondissements,
            seed=42
        )
    
    def test_choisir_type_event(self, positive_event_generator):
        """Test choix type événement selon probabilités."""
        types = [positive_event_generator._choisir_type_event() for _ in range(100)]
        
        fin_travaux_count = types.count("fin_travaux")
        nouvelle_caserne_count = types.count("nouvelle_caserne")
        amelioration_count = types.count("amelioration_materiel")
        
        # Vérifier que les probabilités sont approximativement respectées
        assert 20 <= fin_travaux_count <= 60  # ~40%
        assert 20 <= nouvelle_caserne_count <= 50  # ~35%
        assert 15 <= amelioration_count <= 40  # ~25%
    
    def test_generer_evenements_positifs(self, positive_event_generator):
        """Test génération événements positifs."""
        events_state = EventsState()
        
        evenements = positive_event_generator.generer_evenements_positifs(
            0, events_state
        )
        
        # Vérifier que les événements sont générés (probabilité faible mais possible)
        assert isinstance(evenements, list)
        
        # Vérifier que les événements sont dans events_state
        events_jour = events_state.get_positive_events_for_day(0)
        assert len(events_jour) == len(evenements)
    
    def test_get_effets_reduction_actifs(self, positive_event_generator):
        """Test récupération effets réduction actifs."""
        events_state = EventsState()
        
        # Créer événement positif jour 0
        from src.core.events.fin_travaux import FinTravaux
        event = FinTravaux(
            event_id="POS_001",
            jour=0,
            arrondissement=11,
            impact_reduction=0.1
        )
        events_state.add_event(event)
        
        # Récupérer effets jour 1 (jour suivant)
        effets = positive_event_generator.get_effets_reduction_actifs(1, events_state)
        
        # Vérifier que les effets sont présents
        assert 11 in effets
        assert effets[11] == 0.1  # 10% réduction


class TestPrixM2Modulator:
    """Tests pour PrixM2Modulator."""
    
    @pytest.fixture
    def prix_m2_data(self):
        """Données prix m² pour les tests."""
        return {
            "MZ_11_01": 8000.0,  # Quartier riche
            "MZ_11_02": 5000.0,  # Quartier moyen
            "MZ_12_01": 3000.0  # Quartier moins riche
        }
    
    @pytest.fixture
    def prix_m2_modulator(self, prix_m2_data):
        """Modulateur prix m² pour les tests."""
        from src.core.events.prix_m2_modulator import PrixM2Modulator
        return PrixM2Modulator(prix_m2_data=prix_m2_data)
    
    def test_get_facteur_prix_m2(self, prix_m2_modulator):
        """Test calcul facteur prix m²."""
        # Prix moyen = (8000 + 5000 + 3000) / 3 = 5333.33
        facteur_riche = prix_m2_modulator.get_facteur_prix_m2("MZ_11_01")
        facteur_moyen = prix_m2_modulator.get_facteur_prix_m2("MZ_11_02")
        facteur_pauvre = prix_m2_modulator.get_facteur_prix_m2("MZ_12_01")
        
        assert facteur_riche > 1.0  # Quartier riche
        assert abs(facteur_moyen - 1.0) < 0.5  # Quartier moyen
        assert facteur_pauvre < 1.0  # Quartier moins riche
    
    def test_moduler_probabilite_agression(self, prix_m2_modulator):
        """Test modulation probabilité agression."""
        prob_base = 0.5
        
        prob_riche = prix_m2_modulator.moduler_probabilite_agression("MZ_11_01", prob_base)
        prob_pauvre = prix_m2_modulator.moduler_probabilite_agression("MZ_12_01", prob_base)
        
        # Quartier riche : probabilité réduite
        assert prob_riche < prob_base
        
        # Quartier moins riche : probabilité augmentée
        assert prob_pauvre > prob_base
    
    def test_moduler_probabilites_regimes(self, prix_m2_modulator):
        """Test modulation probabilités régimes."""
        prob_deterioration = 0.15
        prob_crise = 0.05
        
        # Quartier riche (facteur > 1.2)
        prob_det_riche, prob_crise_riche = prix_m2_modulator.moduler_probabilites_regimes(
            "MZ_11_01", prob_deterioration, prob_crise
        )
        
        # Vérifier diminution pour quartier riche
        assert prob_det_riche < prob_deterioration
        assert prob_crise_riche < prob_crise
        
        # Quartier moins riche (facteur < 1.2)
        prob_det_pauvre, prob_crise_pauvre = prix_m2_modulator.moduler_probabilites_regimes(
            "MZ_12_01", prob_deterioration, prob_crise
        )
        
        # Vérifier pas de modification pour quartier moins riche
        assert prob_det_pauvre == prob_deterioration
        assert prob_crise_pauvre == prob_crise
    
    def test_moduler_intensite(self, prix_m2_modulator):
        """Test modulation intensité."""
        from src.core.data.constants import INCIDENT_TYPE_AGRESSION, INCIDENT_TYPE_INCENDIE
        
        intensite_base = 2.0
        
        # Pour agressions, intensité modulée selon prix m²
        intensite_agression_riche = prix_m2_modulator.moduler_intensite(
            "MZ_11_01", INCIDENT_TYPE_AGRESSION, intensite_base
        )
        assert intensite_agression_riche < intensite_base  # Quartier riche = moins d'agressions
        
        # Pour autres types, pas de modulation
        intensite_incendie = prix_m2_modulator.moduler_intensite(
            "MZ_11_01", INCIDENT_TYPE_INCENDIE, intensite_base
        )
        assert intensite_incendie == intensite_base
