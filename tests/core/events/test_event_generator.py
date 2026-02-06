"""
Tests unitaires pour EventGenerator.
Story 2.2.7 - Événements graves modulables
"""

import pytest

from src.core.data.constants import (
    INCIDENT_TYPE_ACCIDENT,
    INCIDENT_TYPE_AGRESSION,
    INCIDENT_TYPE_INCENDIE,
)
from src.core.data.vector import Vector
from src.core.events.event_generator import (
    DUREE_MAX_EVENT,
    DUREE_MIN_EVENT,
    EventGenerator,
    PROB_CANCEL_SPORTS,
    PROB_INCREASE_BAD_VECTORS,
    PROB_KILL_POMPIER,
    PROB_TRAFFIC_SLOWDOWN,
)
from src.core.generation.congestion_calculator import CongestionCalculator
from src.core.state.events_state import EventsState
from src.core.state.vectors_state import VectorsState


class TestEventGenerator:
    """Tests pour EventGenerator."""
    
    @pytest.fixture
    def limites_microzone_arrondissement(self):
        """Limites microzone → arrondissement pour les tests."""
        return {
            "MZ_11_01": 11,
            "MZ_11_02": 11,
            "MZ_12_01": 12
        }
    
    @pytest.fixture
    def event_generator(self, limites_microzone_arrondissement):
        """Générateur d'événements pour les tests."""
        return EventGenerator(
            limites_microzone_arrondissement=limites_microzone_arrondissement,
            seed=42
        )
    
    def test_generer_caracteristiques(self, event_generator):
        """Test génération caractéristiques probabilistes."""
        characteristics = event_generator._generer_caracteristiques()
        
        # Vérifier que les caractéristiques sont générées selon probabilités
        assert isinstance(characteristics, dict)
        
        # Vérifier plages de probabilités (sur plusieurs tirages)
        traffic_count = 0
        cancel_count = 0
        increase_count = 0
        kill_count = 0
        
        for _ in range(100):
            chars = event_generator._generer_caracteristiques()
            if 'traffic_slowdown' in chars:
                traffic_count += 1
            if 'cancel_sports' in chars:
                cancel_count += 1
            if 'increase_bad_vectors' in chars:
                increase_count += 1
            if 'kill_pompier' in chars:
                kill_count += 1
        
        # Vérifier que les probabilités sont approximativement respectées
        assert 50 <= traffic_count <= 90  # ~70%
        assert 10 <= cancel_count <= 50  # ~30%
        assert 30 <= increase_count <= 70  # ~50%
        assert 0 <= kill_count <= 15  # ~5%
    
    def test_generer_duree(self, event_generator):
        """Test génération durée (3-10 jours)."""
        durees = [event_generator._generer_duree() for _ in range(100)]
        
        assert all(DUREE_MIN_EVENT <= d <= DUREE_MAX_EVENT for d in durees)
        assert min(durees) >= DUREE_MIN_EVENT
        assert max(durees) <= DUREE_MAX_EVENT
    
    def test_calculer_casualties_base(self, event_generator):
        """Test calcul casualties_base."""
        vector = Vector(grave=2, moyen=1, benin=0)
        
        casualties = event_generator._calculer_casualties_base(
            INCIDENT_TYPE_ACCIDENT, vector
        )
        
        assert casualties == 2  # Nombre d'incidents graves
    
    def test_generer_evenements_graves(self, event_generator):
        """Test génération événements graves depuis vecteurs."""
        vectors = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(1, 0, 0),  # 1 grave
                INCIDENT_TYPE_INCENDIE: Vector(2, 0, 0)  # 2 graves
            }
        }
        
        events_state = EventsState()
        
        evenements = event_generator.generer_evenements_graves(
            0, vectors, events_state
        )
        
        # Devrait générer 3 événements (1 accident + 2 incendies)
        assert len(evenements) == 3
        
        # Vérifier que les événements sont dans events_state
        events_jour = events_state.get_grave_events_for_day(0)
        assert len(events_jour) == 3
    
    def test_generer_evenements_graves_pas_grave(self, event_generator):
        """Test qu'aucun événement n'est généré si pas d'incident grave."""
        vectors = {
            "MZ_11_01": {
                INCIDENT_TYPE_ACCIDENT: Vector(0, 1, 2)  # Pas de grave
            }
        }
        
        events_state = EventsState()
        
        evenements = event_generator.generer_evenements_graves(
            0, vectors, events_state
        )
        
        assert len(evenements) == 0
    
    def test_appliquer_effets_congestion_temps_reel(self, event_generator):
        """Test application effets congestion temps réel."""
        # Créer calculateur de congestion
        congestion_statique = {"MZ_11_01": 0.5, "MZ_12_01": 0.6}
        congestion_calculator = CongestionCalculator(
            congestion_statique=congestion_statique,
            microzone_ids=["MZ_11_01", "MZ_12_01"],
            seed=42
        )
        
        # Calculer congestion initiale
        vectors = {"MZ_11_01": {INCIDENT_TYPE_ACCIDENT: Vector(0, 0, 0)}}
        congestion_calculator.calculate_congestion_for_day(0, vectors)
        
        congestion_initiale = congestion_calculator.get_congestion("MZ_11_01", 0)
        
        # Créer événement avec traffic_slowdown
        from src.core.events.accident_grave import AccidentGrave
        event = AccidentGrave(
            event_id="EVT_001",
            jour=0,
            arrondissement=11,
            duration=4,
            casualties_base=1,
            characteristics={'traffic_slowdown': 2.0, 'traffic_slowdown_radius': 2}
        )
        
        # Appliquer effets
        event_generator.appliquer_effets_congestion_temps_reel(
            0, [event], congestion_calculator
        )
        
        # Vérifier que la congestion a été modifiée
        congestion_modifiee = congestion_calculator.get_congestion("MZ_11_01", 0)
        assert congestion_modifiee is not None
        assert congestion_modifiee > congestion_initiale
    
    def test_get_effets_vecteurs_actifs(self, event_generator):
        """Test récupération effets actifs sur vecteurs."""
        events_state = EventsState()
        
        # Créer événement avec increase_bad_vectors
        from src.core.events.accident_grave import AccidentGrave
        event = AccidentGrave(
            event_id="EVT_001",
            jour=0,
            arrondissement=11,
            duration=5,
            casualties_base=1,
            characteristics={
                'increase_bad_vectors': 0.3,
                'increase_bad_vectors_duration': 3,
                'increase_bad_vectors_radius': 2
            }
        )
        
        events_state.add_event(event)
        
        # Récupérer effets actifs jour 1
        effets = event_generator.get_effets_vecteurs_actifs(1, events_state)
        
        # Vérifier que les effets sont présents
        assert "MZ_11_01" in effets or len(effets) > 0
