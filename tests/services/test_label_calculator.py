"""
Tests unitaires pour LabelCalculator.
Story 2.2.6 - Labels mensuels
"""

import pytest

from src.core.events.accident_grave import AccidentGrave
from src.core.state.events_state import EventsState
from src.services.label_calculator import (
    CLASSE_CATASTROPHE,
    CLASSE_NORMAL,
    CLASSE_PRE_CATASTROPHE,
    LabelCalculator,
    SEMAINES_PAR_MOIS,
    SEUIL_BLESSES_CATASTROPHE,
    SEUIL_BLESSES_NORMAL,
    SEUIL_BLESSES_PRE_CATASTROPHE,
    SEUIL_MORTS_CATASTROPHE,
    SEUIL_MORTS_NORMAL,
    SEUIL_MORTS_PRE_CATASTROPHE,
)


class TestLabelCalculator:
    """Tests pour LabelCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Calculateur de labels pour les tests."""
        return LabelCalculator()
    
    def test_calculer_score(self, calculator):
        """Test calcul score (morts + 0.5 × blessés_graves)."""
        score = calculator._calculer_score(morts=2, blesses_graves=4)
        
        assert score == 2.0 + 0.5 * 4.0  # 4.0
    
    def test_determiner_classe_normal(self, calculator):
        """Test détermination classe Normal."""
        # 0 morts, 0 blessés → Normal
        classe = calculator._determiner_classe(11, morts=0, blesses_graves=0)
        assert classe == CLASSE_NORMAL
        
        # 1 mort (seuil normal) → Normal
        classe = calculator._determiner_classe(11, morts=SEUIL_MORTS_NORMAL, blesses_graves=0)
        assert classe == CLASSE_NORMAL
        
        # 4 blessés graves (seuil normal) → Normal
        classe = calculator._determiner_classe(11, morts=0, blesses_graves=SEUIL_BLESSES_NORMAL)
        assert classe == CLASSE_NORMAL
    
    def test_determiner_classe_pre_catastrophe(self, calculator):
        """Test détermination classe Pre-catastrophique."""
        # 2 morts (seuil pré-catastrophe) → Pre-catastrophique
        classe = calculator._determiner_classe(11, morts=SEUIL_MORTS_PRE_CATASTROPHE, blesses_graves=0)
        assert classe == CLASSE_PRE_CATASTROPHE
        
        # 5 blessés graves (seuil pré-catastrophe) → Pre-catastrophique
        classe = calculator._determiner_classe(11, morts=0, blesses_graves=SEUIL_BLESSES_PRE_CATASTROPHE)
        assert classe == CLASSE_PRE_CATASTROPHE
    
    def test_determiner_classe_catastrophe(self, calculator):
        """Test détermination classe Catastrophique."""
        # 3 morts (seuil catastrophe) → Catastrophique
        classe = calculator._determiner_classe(11, morts=SEUIL_MORTS_CATASTROPHE, blesses_graves=0)
        assert classe == CLASSE_CATASTROPHE
        
        # 6 blessés graves (seuil catastrophe) → Catastrophique
        classe = calculator._determiner_classe(11, morts=0, blesses_graves=SEUIL_BLESSES_CATASTROPHE)
        assert classe == CLASSE_CATASTROPHE
    
    def test_calculer_casualties_evenements_mois(self, calculator):
        """Test calcul casualties événements pour un mois."""
        events_state = EventsState()
        
        # Ajouter événement grave jour 0 (semaine 1, mois 1)
        event = AccidentGrave(
            event_id="EVT_001",
            jour=0,
            arrondissement=11,
            duration=1,
            casualties_base=2
        )
        events_state.add_event(event)
        
        casualties = calculator._calculer_casualties_evenements_mois(1, events_state)
        
        assert 11 in casualties
        assert casualties[11]['morts'] == 2
        assert casualties[11]['blesses_graves'] == 4  # 2 × 2 (simplification)
    
    def test_calculer_labels_mois(self, calculator):
        """Test calcul labels pour un mois."""
        events_state = EventsState()
        
        # Ajouter événement avec casualties
        event = AccidentGrave(
            event_id="EVT_001",
            jour=0,
            arrondissement=11,
            duration=1,
            casualties_base=2
        )
        events_state.add_event(event)
        
        df = calculator.calculer_labels_mois(1, events_state)
        
        assert len(df) > 0
        assert 'arrondissement' in df.columns
        assert 'mois' in df.columns
        assert 'score' in df.columns
        assert 'classe' in df.columns
        assert 'morts' in df.columns
        assert 'blesses_graves' in df.columns
        
        # Vérifier valeurs
        row = df[df['arrondissement'] == 11].iloc[0]
        assert row['morts'] == 2
        assert row['score'] == 2.0 + 0.5 * 4.0
    
    def test_calculer_labels_multiple_mois(self, calculator):
        """Test calcul labels pour plusieurs mois."""
        events_state = EventsState()
        
        # Ajouter événements pour mois 1 et 2
        event1 = AccidentGrave("EVT_001", 0, 11, 1, 1)
        event2 = AccidentGrave("EVT_002", 28, 11, 1, 1)  # Jour 28 = début mois 2
        
        events_state.add_event(event1)
        events_state.add_event(event2)
        
        df = calculator.calculer_labels_multiple_mois([1, 2], events_state)
        
        assert len(df) > 0
        assert df['mois'].nunique() == 2
    
    def test_agregation_mensuelle_4_semaines(self, calculator):
        """Test que l'agrégation mensuelle utilise exactement 4 semaines."""
        events_state = EventsState()
        
        # Ajouter événements sur 4 semaines (mois 1)
        for jour in range(28):  # 4 semaines
            event = AccidentGrave(f"EVT_{jour}", jour, 11, 1, 1)
            events_state.add_event(event)
        
        casualties = calculator._calculer_casualties_evenements_mois(1, events_state)
        
        # Vérifier que tous les événements sont comptés
        assert 11 in casualties
        # Chaque événement = 1 mort + 2 blessés graves
        assert casualties[11]['morts'] == 28
        assert casualties[11]['blesses_graves'] == 56
    
    def test_filtrage_casualties_evenements_uniquement(self, calculator):
        """Test que seuls les casualties des événements sont comptés."""
        events_state = EventsState()
        
        # Ajouter seulement 1 événement
        event = AccidentGrave("EVT_001", 0, 11, 1, 3)
        events_state.add_event(event)
        
        casualties = calculator._calculer_casualties_evenements_mois(1, events_state)
        
        # Vérifier que seuls les casualties de l'événement sont comptés
        assert 11 in casualties
        assert casualties[11]['morts'] == 3  # Seulement casualties_base de l'événement
        # Pas de double comptage avec vecteurs
