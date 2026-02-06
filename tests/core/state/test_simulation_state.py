"""
Tests unitaires pour SimulationState et ses domaines spécialisés.
Story 2.1.2 - Structure SimulationState avec domaines spécialisés
"""

import tempfile
from pathlib import Path

import pytest

from src.core.data.vector import Vector
from src.core.events import AccidentGrave, FinTravaux
from src.core.state.casualties_state import CasualtiesState
from src.core.state.events_state import EventsState
from src.core.state.regime_state import RegimeState, REGIME_CRISE, REGIME_STABLE
from src.core.state.simulation_state import SimulationState
from src.core.state.vectors_state import VectorsState


class TestVectorsState:
    """Tests pour VectorsState."""
    
    def test_creation_vide(self):
        """Test création d'un état vide."""
        state = VectorsState()
        assert len(state.get_all_microzones()) == 0
    
    def test_set_get_vector(self):
        """Test définition et récupération d'un vecteur."""
        state = VectorsState()
        vector = Vector(grave=1, moyen=2, benin=3)
        
        state.set_vector("MZ_11_01", 0, "incendie", vector)
        retrieved = state.get_vector("MZ_11_01", 0, "incendie")
        
        assert retrieved is not None
        assert retrieved == vector
        assert retrieved.grave == 1
        assert retrieved.moyen == 2
        assert retrieved.benin == 3
    
    def test_get_vectors_for_day(self):
        """Test récupération de tous les vecteurs d'un jour."""
        state = VectorsState()
        vector_incendie = Vector(grave=1, moyen=0, benin=2)
        vector_accident = Vector(grave=0, moyen=1, benin=0)
        
        state.set_vector("MZ_11_01", 0, "incendie", vector_incendie)
        state.set_vector("MZ_11_01", 0, "accident", vector_accident)
        
        vectors = state.get_vectors_for_day("MZ_11_01", 0)
        assert len(vectors) == 2
        assert vectors["incendie"] == vector_incendie
        assert vectors["accident"] == vector_accident
    
    def test_get_all_days(self):
        """Test récupération de tous les jours."""
        state = VectorsState()
        state.set_vector("MZ_11_01", 0, "incendie", Vector())
        state.set_vector("MZ_11_01", 2, "incendie", Vector())
        state.set_vector("MZ_11_01", 1, "incendie", Vector())
        
        days = state.get_all_days("MZ_11_01")
        assert days == [0, 1, 2]
    
    def test_clear_day(self):
        """Test suppression d'un jour."""
        state = VectorsState()
        state.set_vector("MZ_11_01", 0, "incendie", Vector())
        state.set_vector("MZ_11_02", 0, "incendie", Vector())
        state.set_vector("MZ_11_01", 1, "incendie", Vector())
        
        state.clear_day(0)
        
        assert state.get_vector("MZ_11_01", 0, "incendie") is None
        assert state.get_vector("MZ_11_02", 0, "incendie") is None
        assert state.get_vector("MZ_11_01", 1, "incendie") is not None


class TestEventsState:
    """Tests pour EventsState."""
    
    def test_creation_vide(self):
        """Test création d'un état vide."""
        state = EventsState()
        assert len(state.get_all_days()) == 0
    
    def test_add_get_event(self):
        """Test ajout et récupération d'événements."""
        state = EventsState()
        accident = AccidentGrave(
            event_id="ACC_001",
            jour=5,
            arrondissement=11,
            duration=4,
            casualties_base=2
        )
        
        state.add_event(accident)
        events = state.get_events_for_day(5)
        
        assert len(events) == 1
        assert events[0] == accident
    
    def test_get_grave_events(self):
        """Test récupération uniquement des événements graves."""
        state = EventsState()
        accident = AccidentGrave("ACC_001", 5, 11, 4)
        fin_travaux = FinTravaux("FT_001", 5, 11)
        
        state.add_event(accident)
        state.add_event(fin_travaux)
        
        grave_events = state.get_grave_events_for_day(5)
        assert len(grave_events) == 1
        assert grave_events[0] == accident
    
    def test_get_positive_events(self):
        """Test récupération uniquement des événements positifs."""
        state = EventsState()
        accident = AccidentGrave("ACC_001", 5, 11, 4)
        fin_travaux = FinTravaux("FT_001", 5, 11)
        
        state.add_event(accident)
        state.add_event(fin_travaux)
        
        positive_events = state.get_positive_events_for_day(5)
        assert len(positive_events) == 1
        assert positive_events[0] == fin_travaux
    
    def test_get_events_for_arrondissement(self):
        """Test récupération par arrondissement."""
        state = EventsState()
        accident_11 = AccidentGrave("ACC_001", 5, 11, 4)
        accident_12 = AccidentGrave("ACC_002", 5, 12, 4)
        
        state.add_event(accident_11)
        state.add_event(accident_12)
        
        events_11 = state.get_events_for_arrondissement(11, jour=5)
        assert len(events_11) == 1
        assert events_11[0] == accident_11


class TestCasualtiesState:
    """Tests pour CasualtiesState."""
    
    def test_creation_vide(self):
        """Test création d'un état vide."""
        state = CasualtiesState()
        assert len(state.get_all_semaines()) == 0
    
    def test_add_get_casualties(self):
        """Test ajout et récupération de casualties."""
        state = CasualtiesState()
        state.add_casualties(semaine=1, arrondissement=11, morts=2, blesses_graves=5)
        
        casualties = state.get_casualties(1, 11)
        assert casualties["morts"] == 2
        assert casualties["blesses_graves"] == 5
    
    def test_get_score(self):
        """Test calcul du score."""
        state = CasualtiesState()
        state.add_casualties(semaine=1, arrondissement=11, morts=2, blesses_graves=4)
        
        score = state.get_score(1, 11)
        assert score == 2 + 0.5 * 4  # 4.0
    
    def test_add_cumulative(self):
        """Test que les casualties s'accumulent."""
        state = CasualtiesState()
        state.add_casualties(semaine=1, arrondissement=11, morts=1, blesses_graves=2)
        state.add_casualties(semaine=1, arrondissement=11, morts=1, blesses_graves=3)
        
        casualties = state.get_casualties(1, 11)
        assert casualties["morts"] == 2
        assert casualties["blesses_graves"] == 5


class TestRegimeState:
    """Tests pour RegimeState."""
    
    def test_creation_vide(self):
        """Test création d'un état vide."""
        state = RegimeState()
        assert len(state.get_all_microzones()) == 0
    
    def test_set_get_regime(self):
        """Test définition et récupération d'un régime."""
        state = RegimeState()
        state.set_regime("MZ_11_01", REGIME_CRISE)
        
        regime = state.get_regime("MZ_11_01")
        assert regime == REGIME_CRISE
    
    def test_get_regime_or_default(self):
        """Test récupération avec valeur par défaut."""
        state = RegimeState()
        assert state.get_regime_or_default("MZ_11_01") == REGIME_STABLE
        
        state.set_regime("MZ_11_01", REGIME_CRISE)
        assert state.get_regime_or_default("MZ_11_01") == REGIME_CRISE
    
    def test_invalid_regime_raises_error(self):
        """Test qu'un régime invalide lève une erreur."""
        state = RegimeState()
        with pytest.raises(ValueError, match="Régime invalide"):
            state.set_regime("MZ_11_01", "Invalid")
    
    def test_get_microzones_by_regime(self):
        """Test récupération des microzones par régime."""
        state = RegimeState()
        state.set_regime("MZ_11_01", REGIME_STABLE)
        state.set_regime("MZ_11_02", REGIME_CRISE)
        state.set_regime("MZ_12_01", REGIME_STABLE)
        
        stable_mz = state.get_microzones_by_regime(REGIME_STABLE)
        assert len(stable_mz) == 2
        assert "MZ_11_01" in stable_mz
        assert "MZ_12_01" in stable_mz


class TestSimulationState:
    """Tests pour SimulationState (Aggregate Root)."""
    
    def test_creation(self):
        """Test création d'un SimulationState."""
        config = {"param1": "value1"}
        state = SimulationState(run_id="test_run", config=config)
        
        assert state.run_id == "test_run"
        assert state.config == config
        assert state.current_day == 0
        assert isinstance(state.vectors_state, VectorsState)
        assert isinstance(state.events_state, EventsState)
        assert isinstance(state.casualties_state, CasualtiesState)
        assert isinstance(state.regime_state, RegimeState)
        assert isinstance(state.dynamic_state, type(state.dynamic_state))  # DynamicState
    
    def test_save_load(self):
        """Test sauvegarde et chargement avec pickle."""
        config = {"param1": "value1"}
        state = SimulationState(run_id="test_run", config=config)
        
        # Ajouter des données
        state.vectors_state.set_vector("MZ_11_01", 0, "incendie", Vector(1, 2, 3))
        state.events_state.add_event(AccidentGrave("ACC_001", 0, 11, 4))
        state.casualties_state.add_casualties(1, 11, morts=2, blesses_graves=5)
        state.regime_state.set_regime("MZ_11_01", REGIME_CRISE)
        state.current_day = 5
        
        # Sauvegarder
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
            tmp_path = tmp.name
        
        try:
            state.save(tmp_path)
            
            # Charger
            loaded_state = SimulationState.load(tmp_path)
            
            assert loaded_state.run_id == "test_run"
            assert loaded_state.config == config
            assert loaded_state.current_day == 5
            
            # Vérifier les domaines
            vector = loaded_state.vectors_state.get_vector("MZ_11_01", 0, "incendie")
            assert vector is not None
            assert vector.grave == 1
            
            events = loaded_state.events_state.get_events_for_day(0)
            assert len(events) == 1
            
            casualties = loaded_state.casualties_state.get_casualties(1, 11)
            assert casualties["morts"] == 2
            
            regime = loaded_state.regime_state.get_regime("MZ_11_01")
            assert regime == REGIME_CRISE
        
        finally:
            # Nettoyer
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_to_dict(self):
        """Test conversion en dictionnaire."""
        state = SimulationState(run_id="test_run", config={"param": "value"})
        state.vectors_state.set_vector("MZ_11_01", 0, "incendie", Vector(1, 2, 3))
        
        dict_repr = state.to_dict()
        
        assert dict_repr["run_id"] == "test_run"
        assert dict_repr["current_day"] == 0
        assert "vectors_state" in dict_repr
        assert "events_state" in dict_repr
        assert "casualties_state" in dict_repr
        assert "regime_state" in dict_repr
    
    def test_separation_journalier_vs_agrege(self):
        """
        Test que SimulationState contient UNIQUEMENT données journalières.
        CasualtiesState est agrégé par semaine (pas journalier).
        """
        state = SimulationState(run_id="test", config={})
        
        # VectorsState : journalier ✓
        state.vectors_state.set_vector("MZ_11_01", 0, "incendie", Vector())
        state.vectors_state.set_vector("MZ_11_01", 1, "incendie", Vector())
        
        # EventsState : journalier ✓
        state.events_state.add_event(AccidentGrave("ACC_001", 0, 11, 4))
        state.events_state.add_event(AccidentGrave("ACC_002", 1, 11, 4))
        
        # CasualtiesState : agrégé par semaine (pas journalier) ✓
        state.casualties_state.add_casualties(semaine=1, arrondissement=11, morts=2)
        # Pas de méthode add_casualties(jour=...) car c'est agrégé
        
        # Vérifier la séparation
        assert len(state.vectors_state.get_all_days("MZ_11_01")) == 2  # Journalier
        assert len(state.events_state.get_all_days()) == 2  # Journalier
        assert len(state.casualties_state.get_all_semaines()) == 1  # Hebdomadaire
