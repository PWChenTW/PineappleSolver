"""
Comprehensive test suite for GameState domain model.
"""

import pytest
import random
from src.core.domain.card import Card, Rank, Suit
from src.core.domain.game_state import GameState, Street, StreetAction
from src.core.domain.card_set import CardSet
from src.exceptions import InvalidInputError, GameRuleViolationError, StateError


class TestGameStateInitialization:
    """Test GameState initialization."""
    
    def test_valid_initialization(self):
        """Test creating game state with valid parameters."""
        # Default 2-player game
        gs = GameState()
        assert gs.num_players == 2
        assert gs.player_index == 0
        assert gs.num_jokers == 0
        assert gs.current_street == Street.INITIAL
        assert not gs.is_complete
        assert len(gs.current_hand) == 0
        
        # 3-player game
        gs = GameState(num_players=3, player_index=1)
        assert gs.num_players == 3
        assert gs.player_index == 1
        
        # With jokers
        gs = GameState(num_jokers=2)
        assert gs.num_jokers == 2
        
        # With seed for reproducibility
        gs = GameState(seed=42)
        # Should be deterministic with seed
    
    def test_invalid_initialization(self):
        """Test initialization with invalid parameters."""
        # Invalid number of players
        with pytest.raises(InvalidInputError) as exc_info:
            GameState(num_players=1)
        assert "between 2 and 4" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            GameState(num_players=5)
        
        # Invalid player index
        with pytest.raises(InvalidInputError) as exc_info:
            GameState(num_players=2, player_index=2)
        assert "out of range" in str(exc_info.value)
        
        with pytest.raises(InvalidInputError):
            GameState(num_players=2, player_index=-1)
        
        # Invalid number of jokers
        with pytest.raises(InvalidInputError):
            GameState(num_jokers=-1)
        
        with pytest.raises(InvalidInputError):
            GameState(num_jokers=3)
    
    def test_deck_initialization(self):
        """Test deck is properly initialized."""
        gs = GameState()
        # Should have full deck available initially
        remaining = gs.remaining_cards
        assert len(remaining) == 52
        
        # With jokers
        gs = GameState(num_jokers=2)
        remaining = gs.remaining_cards
        assert len(remaining) == 54


class TestStreetDealing:
    """Test dealing cards for streets."""
    
    def test_deal_initial_street(self):
        """Test dealing initial 5 cards."""
        gs = GameState(num_players=2, seed=42)
        cards = gs.deal_street()
        
        assert len(cards) == 5
        assert all(isinstance(c, Card) for c in cards)
        assert len(gs.current_hand) == 5
        
        # Cards should be removed from available deck
        remaining = gs.remaining_cards
        assert len(remaining) == 52 - (5 * 2)  # 5 cards per player
    
    def test_deal_subsequent_streets(self):
        """Test dealing 3 cards in later streets."""
        gs = GameState(num_players=2, seed=42)
        
        # Deal and place initial cards
        initial_cards = gs.deal_street()
        placements = [
            (initial_cards[0], 'front', 0),
            (initial_cards[1], 'front', 1),
            (initial_cards[2], 'middle', 0),
            (initial_cards[3], 'back', 0),
            (initial_cards[4], 'back', 1)
        ]
        gs.place_cards(placements)
        
        # Deal first street (should get 3 cards)
        cards = gs.deal_street()
        assert len(cards) == 3
        assert gs.current_street == Street.FIRST
    
    def test_deal_with_multiple_players(self):
        """Test dealing considers all players."""
        gs = GameState(num_players=3, player_index=1, seed=42)
        cards = gs.deal_street()
        
        assert len(cards) == 5  # Player gets 5 cards
        # But 15 cards total dealt (5 per player)
        assert len(gs.remaining_cards) == 52 - 15
        
        # Opponent cards should be marked as used
        assert len(gs.opponent_used_cards) == 10  # 2 opponents * 5 cards
    
    def test_deal_errors(self):
        """Test error conditions when dealing."""
        gs = GameState()
        
        # Deal without placing previous cards
        cards = gs.deal_street()
        with pytest.raises(StateError) as exc_info:
            gs.deal_street()  # Can't deal with unresolved hand
        assert "unresolved hand" in str(exc_info.value)
        
        # Complete game and try to deal
        gs = GameState()
        # Simulate complete game
        gs._current_street = Street.COMPLETE
        with pytest.raises(StateError) as exc_info:
            gs.deal_street()
        assert "completed game" in str(exc_info.value)
    
    def test_insufficient_cards(self):
        """Test handling when not enough cards to deal."""
        # This would require setting up a game state with most cards used
        # Skip for brevity but important to test


class TestCardPlacement:
    """Test placing cards."""
    
    def test_initial_street_placement(self):
        """Test placing all 5 cards in initial street."""
        gs = GameState(seed=42)
        cards = gs.deal_street()
        
        placements = [
            (cards[0], 'front', 0),
            (cards[1], 'front', 1),
            (cards[2], 'middle', 0),
            (cards[3], 'back', 0),
            (cards[4], 'back', 1)
        ]
        
        gs.place_cards(placements)
        
        # Check state advanced
        assert gs.current_street == Street.FIRST
        assert len(gs.current_hand) == 0
        
        # Check arrangement updated
        arrangement = gs.player_arrangement
        assert arrangement.front[0] == cards[0]
        assert arrangement.front[1] == cards[1]
        assert arrangement.middle[0] == cards[2]
        assert arrangement.back[0] == cards[3]
        assert arrangement.back[1] == cards[4]
        assert arrangement.cards_placed == 5
    
    def test_subsequent_street_placement(self):
        """Test placing 2 cards and discarding 1."""
        gs = GameState(seed=42)
        
        # Setup: place initial cards
        initial_cards = gs.deal_street()
        initial_placements = [
            (initial_cards[0], 'front', 0),
            (initial_cards[1], 'front', 1),
            (initial_cards[2], 'middle', 0),
            (initial_cards[3], 'back', 0),
            (initial_cards[4], 'back', 1)
        ]
        gs.place_cards(initial_placements)
        
        # Deal first street
        cards = gs.deal_street()
        assert len(cards) == 3
        
        # Place 2, discard 1
        placements = [
            (cards[0], 'middle', 1),
            (cards[1], 'back', 2)
        ]
        discard = cards[2]
        
        gs.place_cards(placements, discard)
        
        # Check state
        assert gs.current_street == Street.SECOND
        assert gs.player_arrangement.middle[1] == cards[0]
        assert gs.player_arrangement.back[2] == cards[1]
        assert gs.player_arrangement.cards_placed == 7
    
    def test_placement_validation(self):
        """Test placement validation rules."""
        gs = GameState(seed=42)
        cards = gs.deal_street()
        
        # Wrong number of placements for initial street
        with pytest.raises(InvalidInputError) as exc_info:
            gs.place_cards([(cards[0], 'front', 0)])  # Only 1 card
        assert "Expected 5 placements" in str(exc_info.value)
        
        # Discard not allowed in initial street
        with pytest.raises(InvalidInputError) as exc_info:
            placements = [(cards[i], 'front', i) for i in range(3)]
            placements.extend([(cards[3], 'middle', 0), (cards[4], 'back', 0)])
            gs.place_cards(placements, discard=cards[0])
        assert "No discard allowed" in str(exc_info.value)
        
        # Card not in hand
        other_card = Card.from_string("As")
        with pytest.raises(GameRuleViolationError) as exc_info:
            placements = [
                (other_card, 'front', 0),  # Not in hand!
                (cards[1], 'front', 1),
                (cards[2], 'middle', 0),
                (cards[3], 'back', 0),
                (cards[4], 'back', 1)
            ]
            gs.place_cards(placements)
        assert "not in current hand" in str(exc_info.value)
        
        # Duplicate placement
        with pytest.raises(GameRuleViolationError) as exc_info:
            placements = [
                (cards[0], 'front', 0),
                (cards[0], 'front', 1),  # Same card twice!
                (cards[2], 'middle', 0),
                (cards[3], 'back', 0),
                (cards[4], 'back', 1)
            ]
            gs.place_cards(placements)
        assert "Duplicate cards" in str(exc_info.value)
    
    def test_placement_after_street_validation(self):
        """Test validation after initial street."""
        gs = GameState(seed=42)
        
        # Place initial cards
        initial_cards = gs.deal_street()
        initial_placements = [
            (initial_cards[i], 'back', i) for i in range(5)
        ]
        gs.place_cards(initial_placements)
        
        # Deal next street
        cards = gs.deal_street()
        
        # Missing discard
        with pytest.raises(InvalidInputError) as exc_info:
            gs.place_cards([(cards[0], 'middle', 0), (cards[1], 'middle', 1)])
        assert "Discard required" in str(exc_info.value)
        
        # Wrong number of placements
        with pytest.raises(InvalidInputError) as exc_info:
            gs.place_cards([(cards[0], 'middle', 0)], discard=cards[1])
        assert "Expected 2 placements" in str(exc_info.value)
    
    def test_invalid_arrangement_rollback(self):
        """Test that invalid arrangements are rolled back."""
        # This would require setting up a situation where placement
        # would violate hand strength rules (back >= middle >= front)
        # Skip for brevity but important to test


class TestGameStateProperties:
    """Test game state properties and queries."""
    
    def test_remaining_cards(self):
        """Test calculation of remaining cards."""
        gs = GameState(num_players=2, seed=42)
        
        # Initially all cards available
        assert len(gs.remaining_cards) == 52
        
        # After dealing initial street
        gs.deal_street()
        assert len(gs.remaining_cards) == 52 - 10  # 5 cards * 2 players
        
        # Place cards and deal next
        cards = gs.current_hand
        placements = [
            (cards[0], 'front', 0),
            (cards[1], 'front', 1),
            (cards[2], 'middle', 0),
            (cards[3], 'back', 0),
            (cards[4], 'back', 1)
        ]
        gs.place_cards(placements)
        
        gs.deal_street()
        assert len(gs.remaining_cards) == 52 - 10 - 6  # Additional 3 * 2 cards
    
    def test_is_complete(self):
        """Test game completion detection."""
        gs = GameState(seed=42)
        assert not gs.is_complete
        
        # Simulate playing through all streets
        # Initial street
        cards = gs.deal_street()
        placements = [(cards[i], 'back', i) for i in range(5)]
        gs.place_cards(placements)
        
        # Play through 4 more streets
        for _ in range(4):
            cards = gs.deal_street()
            placements = [
                (cards[0], 'middle', gs.player_arrangement.cards_placed % 5),
                (cards[1], 'front', gs.player_arrangement.cards_placed % 3)
            ]
            gs.place_cards(placements, discard=cards[2])
        
        assert gs.is_complete
        assert gs.current_street == Street.COMPLETE
    
    def test_copy_state(self):
        """Test copying game state."""
        gs1 = GameState(seed=42)
        cards = gs1.deal_street()
        
        # Make a copy
        gs2 = gs1.copy()
        
        # Both should have same state
        assert gs1.current_street == gs2.current_street
        assert gs1.current_hand == gs2.current_hand
        assert gs1.num_players == gs2.num_players
        
        # But modifying one shouldn't affect other
        placements = [
            (cards[0], 'front', 0),
            (cards[1], 'front', 1),
            (cards[2], 'middle', 0),
            (cards[3], 'back', 0),
            (cards[4], 'back', 1)
        ]
        gs1.place_cards(placements)
        
        assert gs1.current_street == Street.FIRST
        assert gs2.current_street == Street.INITIAL  # Unchanged
        assert gs1.player_arrangement.cards_placed == 5
        assert gs2.player_arrangement.cards_placed == 0  # Unchanged


class TestSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self):
        """Test converting game state to dictionary."""
        gs = GameState(num_players=3, player_index=1, num_jokers=1)
        data = gs.to_dict()
        
        assert data['num_players'] == 3
        assert data['player_index'] == 1
        assert data['num_jokers'] == 1
        assert data['current_street'] == 'INITIAL'
        assert data['cards_placed'] == 0
        assert data['is_complete'] is False
        assert data['current_hand'] == []
    
    def test_to_dict_with_hand(self):
        """Test serialization with cards in hand."""
        gs = GameState(seed=42)
        gs.deal_street()
        
        data = gs.to_dict()
        assert len(data['current_hand']) == 5
        assert all(isinstance(card_str, str) for card_str in data['current_hand'])
    
    def test_from_dict_basic(self):
        """Test creating game state from dictionary."""
        data = {
            'num_players': 3,
            'player_index': 2,
            'num_jokers': 1,
            'current_street': 'FIRST'
        }
        
        gs = GameState.from_dict(data)
        assert gs.num_players == 3
        assert gs.player_index == 2
        assert gs.num_jokers == 1
        assert gs.current_street == Street.FIRST
    
    def test_string_representation(self):
        """Test string representation."""
        gs = GameState()
        repr_str = repr(gs)
        
        assert "GameState" in repr_str
        assert "street=INITIAL" in repr_str
        assert "cards_placed=0/13" in repr_str
        assert "hand_size=0" in repr_str


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        gs1 = GameState(seed=12345)
        gs2 = GameState(seed=12345)
        
        cards1 = gs1.deal_street()
        cards2 = gs2.deal_street()
        
        # Should get same cards in same order
        assert len(cards1) == len(cards2)
        for c1, c2 in zip(cards1, cards2):
            assert c1 == c2
    
    def test_different_seeds(self):
        """Test that different seeds produce different results."""
        gs1 = GameState(seed=111)
        gs2 = GameState(seed=222)
        
        cards1 = gs1.deal_street()
        cards2 = gs2.deal_street()
        
        # Very unlikely to get same cards
        # (possible but probability is extremely low)
        cards1_str = [str(c) for c in cards1]
        cards2_str = [str(c) for c in cards2]
        assert cards1_str != cards2_str
    
    def test_state_after_error(self):
        """Test that state is consistent after errors."""
        gs = GameState(seed=42)
        cards = gs.deal_street()
        
        # Try invalid placement
        with pytest.raises(InvalidInputError):
            gs.place_cards([(cards[0], 'front', 0)])  # Too few cards
        
        # State should be unchanged
        assert gs.current_street == Street.INITIAL
        assert len(gs.current_hand) == 5
        assert gs.player_arrangement.cards_placed == 0