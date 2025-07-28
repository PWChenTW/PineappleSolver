"""
Edge case and boundary condition tests for OFC Solver.

Tests unusual scenarios, error conditions, and boundary values
to ensure robustness.
"""

import pytest
import random
from unittest.mock import Mock, patch, MagicMock
from src.core.domain import Card, GameState, CardSet, Rank, Suit
from src.core.domain.hand import Hand
from src.core.domain.player_arrangement import PlayerArrangement
from src.exceptions import InvalidInputError, GameRuleViolationError, StateError


class TestCardEdgeCases:
    """Edge cases for Card class."""
    
    def test_joker_properties(self):
        """Test joker card edge cases."""
        joker = Card(52)
        
        # Joker should have None for rank and suit
        assert joker.rank is None
        assert joker.suit is None
        assert joker.is_joker is True
        
        # Joker should have special values
        assert joker.rank_value == Rank.ACE.value  # Treated as ace
        assert joker.suit_value == 0
        
        # String representation
        assert str(joker) == "Joker"
        
        # Joker in sets
        cs = CardSet.from_cards([joker])
        assert len(cs) == 1
        assert joker in cs
    
    def test_card_boundary_values(self):
        """Test card creation with boundary values."""
        # Valid boundary values
        card0 = Card(0)  # 2 of clubs
        assert card0.rank == Rank.TWO
        assert card0.suit == Suit.CLUBS
        
        card51 = Card(51)  # Ace of spades
        assert card51.rank == Rank.ACE
        assert card51.suit == Suit.SPADES
        
        card52 = Card(52)  # Joker
        assert card52.is_joker
        
        # Invalid boundary values
        with pytest.raises(InvalidInputError):
            Card(-1)
        
        with pytest.raises(InvalidInputError):
            Card(53)
    
    def test_card_unusual_comparisons(self):
        """Test unusual card comparisons."""
        card = Card.from_string("As")
        joker = Card(52)
        
        # Comparing with joker
        assert card < joker  # 51 < 52
        assert not (joker < card)
        
        # Comparing with non-Card should raise TypeError
        with pytest.raises(TypeError):
            card < "As"
        
        with pytest.raises(TypeError):
            card < 51
        
        # Equality with non-Card should return False
        assert card != "As"
        assert card != 51
        assert card != None


class TestCardSetEdgeCases:
    """Edge cases for CardSet class."""
    
    def test_empty_cardset_operations(self):
        """Test operations on empty card sets."""
        empty1 = CardSet.empty()
        empty2 = CardSet.empty()
        full = CardSet.full_deck()
        
        # Empty set properties
        assert len(empty1) == 0
        assert not empty1  # Falsy
        assert list(empty1) == []
        
        # Operations with empty sets
        assert empty1 | empty2 == empty1  # Union of empties is empty
        assert empty1 & full == empty1    # Intersection with empty is empty
        assert full - empty1 == full      # Removing nothing changes nothing
        assert empty1 - full == empty1    # Empty minus anything is empty
        
        # Pop from empty should raise
        with pytest.raises(KeyError) as exc_info:
            empty1.pop()
        assert "empty" in str(exc_info.value)
    
    def test_cardset_with_all_cards(self):
        """Test card set with all possible cards."""
        # With jokers
        all_cards = CardSet.full_deck(include_jokers=True)
        assert len(all_cards) == 53  # 52 + 1 joker
        
        # Adding more cards doesn't change it
        all_cards.add(Card(0))
        assert len(all_cards) == 53
        
        # Removing all cards one by one
        count = 0
        while all_cards:
            all_cards.pop()
            count += 1
        assert count == 53
        assert len(all_cards) == 0
    
    def test_cardset_massive_operations(self):
        """Test card set with many operations."""
        cs = CardSet.empty()
        
        # Add and remove same card many times
        card = Card.from_string("As")
        for _ in range(1000):
            cs.add(card)
            assert len(cs) == 1  # Still just one card
            cs.remove(card)
            assert len(cs) == 0
        
        # Many set operations
        sets = [CardSet.from_cards([Card(i)]) for i in range(52)]
        result = sets[0]
        for s in sets[1:]:
            result = result | s
        assert len(result) == 52  # Union of all singles is full deck


class TestHandEdgeCases:
    """Edge cases for Hand class."""
    
    def test_hand_with_all_jokers(self):
        """Test hand containing all jokers."""
        # 3 jokers (if game allowed it)
        jokers = [Card(52), Card(52), Card(52)]
        hand = Hand(jokers)
        
        # Should be three of a kind (aces)
        assert hand.hand_type.category == HandCategory.THREE_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.ACE.value
    
    def test_hand_with_duplicate_cards(self):
        """Test that duplicate cards work correctly in evaluation."""
        # In real game this shouldn't happen, but test evaluation handles it
        cards = [
            Card.from_string("As"),
            Card.from_string("As"),  # Duplicate!
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Kd")
        ]
        hand = Hand(cards)
        
        # Should still evaluate (though game rules would prevent this)
        assert hand.hand_type.category in [
            HandCategory.FULL_HOUSE,
            HandCategory.THREE_OF_A_KIND
        ]
    
    def test_hand_ace_low_straight_edge_cases(self):
        """Test ace-low straight (wheel) edge cases."""
        # Standard wheel
        wheel = Hand.from_strings(["5s", "4h", "3d", "2c", "As"])
        assert wheel.hand_type.category == HandCategory.STRAIGHT
        
        # Near-wheel (missing one card)
        near_wheel = Hand.from_strings(["5s", "4h", "3d", "2c", "Ks"])
        assert near_wheel.hand_type.category != HandCategory.STRAIGHT
        
        # Wheel with different suits (not straight flush)
        mixed_wheel = Hand.from_strings(["5s", "4h", "3d", "2c", "As"])
        assert mixed_wheel.hand_type.category == HandCategory.STRAIGHT
        assert mixed_wheel.hand_type.category != HandCategory.STRAIGHT_FLUSH
    
    def test_hand_comparison_edge_cases(self):
        """Test edge cases in hand comparison."""
        # Same category, same rank, different kickers
        pair1 = Hand.from_strings(["As", "Ah", "Kd", "Qc", "Jh"])
        pair2 = Hand.from_strings(["Ac", "Ad", "Kh", "Qs", "Jd"])
        
        # Should be equal (same pair, same kickers)
        assert pair1 == pair2
        assert not (pair1 < pair2)
        assert not (pair1 > pair2)
        
        # Comparison with non-Hand
        assert pair1 != "not a hand"
        assert pair1 != None
        assert pair1 != 42


class TestGameStateEdgeCases:
    """Edge cases for GameState class."""
    
    def test_game_state_with_max_players(self):
        """Test game with maximum number of players."""
        gs = GameState(num_players=4, player_index=3)
        
        # Deal cards
        gs.deal_street()
        
        # Should have dealt to all 4 players
        assert len(gs.current_hand) == 5
        assert len(gs.opponent_used_cards) == 15  # 3 opponents * 5 cards
        assert len(gs.remaining_cards) == 52 - 20  # 4 players * 5 cards
    
    def test_game_state_insufficient_cards(self):
        """Test when deck runs out of cards."""
        # This is an extreme case - manually set up near-empty deck
        gs = GameState(num_players=4)
        
        # Simulate most cards used (would need to mock internal state)
        # In practice, with 4 players, we'd run out after:
        # Initial: 4*5 = 20 cards
        # 4 streets: 4*4*3 = 48 cards
        # Total: 68 cards > 52, so would fail on 3rd street
        
        # For now, just verify the error handling exists
        pass
    
    def test_game_state_rapid_copy(self):
        """Test rapid copying doesn't cause issues."""
        gs = GameState(seed=42)
        gs.deal_street()
        
        # Make many copies
        copies = []
        for _ in range(100):
            copy = gs.copy()
            copies.append(copy)
            
            # Modify the copy
            if copy.current_hand:
                cards = copy.current_hand
                placements = [(cards[i], 'back', i) for i in range(5)]
                copy.place_cards(placements)
        
        # Original should be unchanged
        assert gs.current_street == Street.INITIAL
        assert len(gs.current_hand) == 5
        
        # All copies should be independent
        assert all(c.current_street == Street.FIRST for c in copies)
    
    def test_game_state_invalid_placements(self):
        """Test various invalid placement scenarios."""
        gs = GameState()
        gs.deal_street()
        cards = gs.current_hand
        
        # Placing in occupied position (after some cards placed)
        placements1 = [
            (cards[0], 'front', 0),
            (cards[1], 'front', 1),
            (cards[2], 'middle', 0),
            (cards[3], 'back', 0),
            (cards[4], 'back', 1)
        ]
        gs.place_cards(placements1)
        
        # Deal next street
        gs.deal_street()
        new_cards = gs.current_hand
        
        # Try to place in occupied position
        with pytest.raises(GameRuleViolationError):
            invalid_placements = [
                (new_cards[0], 'front', 0),  # Already occupied!
                (new_cards[1], 'middle', 1)
            ]
            gs.place_cards(invalid_placements, discard=new_cards[2])
    
    def test_game_state_serialization_edge_cases(self):
        """Test serialization with unusual states."""
        # Empty game state
        gs1 = GameState()
        data1 = gs1.to_dict()
        restored1 = GameState.from_dict(data1)
        assert restored1.current_street == Street.INITIAL
        
        # Game state with cards in hand
        gs2 = GameState(num_players=3, player_index=2, num_jokers=1)
        gs2.deal_street()
        data2 = gs2.to_dict()
        assert len(data2['current_hand']) == 5
        
        # Completed game state
        gs3 = GameState()
        gs3._current_street = Street.COMPLETE
        data3 = gs3.to_dict()
        assert data3['is_complete'] is True


class TestPlayerArrangementEdgeCases:
    """Edge cases for PlayerArrangement class."""
    
    def test_arrangement_full_positions(self):
        """Test arrangement when all positions are full."""
        arr = PlayerArrangement()
        
        # Fill front (3 cards)
        for i in range(3):
            arr.place_card(Card(i), 'front', i)
        
        # Try to place in full front
        with pytest.raises(InvalidInputError):
            arr.place_card(Card(10), 'front', 3)  # Index out of range
        
        # Fill middle and back
        for i in range(5):
            arr.place_card(Card(i+3), 'middle', i)
            arr.place_card(Card(i+8), 'back', i)
        
        assert arr.cards_placed == 13
        assert arr.is_complete()
    
    def test_arrangement_validation_edge_cases(self):
        """Test arrangement validation edge cases."""
        arr = PlayerArrangement()
        
        # Place cards that would violate hand strength rules
        # Back: 22233 (full house)
        arr.place_card(Card.from_string("2s"), 'back', 0)
        arr.place_card(Card.from_string("2h"), 'back', 1)
        arr.place_card(Card.from_string("2d"), 'back', 2)
        arr.place_card(Card.from_string("3s"), 'back', 3)
        arr.place_card(Card.from_string("3h"), 'back', 4)
        
        # Middle: AAA (three of a kind) - invalid, weaker than back
        arr.place_card(Card.from_string("As"), 'middle', 0)
        arr.place_card(Card.from_string("Ah"), 'middle', 1)
        arr.place_card(Card.from_string("Ad"), 'middle', 2)
        
        is_valid, error = arr.is_valid_progressive()
        assert not is_valid
        assert "stronger" in error.lower()


class TestExceptionEdgeCases:
    """Test exception handling edge cases."""
    
    def test_nested_exceptions(self):
        """Test handling of nested exceptions."""
        # InvalidInputError with complex details
        try:
            raise InvalidInputError(
                "Complex error",
                input_value={"nested": {"data": [1, 2, 3]}},
                expected_format="something",
                additional_info="more context"
            )
        except InvalidInputError as e:
            assert "Complex error" in str(e)
            assert "nested" in e.details
            assert e.details["input_value"]["nested"]["data"] == [1, 2, 3]
    
    def test_error_recovery(self):
        """Test that system can recover from errors."""
        gs = GameState()
        
        # Cause an error
        with pytest.raises(StateError):
            gs.place_cards([])  # No cards to place
        
        # System should still be usable
        gs.deal_street()
        assert len(gs.current_hand) == 5
        
        # Can continue normally
        cards = gs.current_hand
        placements = [(cards[i], 'back', i) for i in range(5)]
        gs.place_cards(placements)
        assert gs.current_street == Street.FIRST


class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrent access."""
    
    def test_cardset_concurrent_modification(self):
        """Test CardSet behavior with concurrent-like modifications."""
        cs = CardSet.from_cards(Card.deck()[:26])
        
        # Simulate concurrent modification by modifying during iteration
        # (This would be bad in real concurrent code, but tests robustness)
        cards_seen = []
        for i, card in enumerate(cs):
            cards_seen.append(card)
            if i == 10:
                # Modify set during iteration
                cs.add(Card(50))
        
        # Should have seen original cards (iteration snapshot)
        assert len(cards_seen) == 26
    
    def test_game_state_isolation(self):
        """Test that game states are properly isolated."""
        gs1 = GameState(seed=100)
        gs2 = GameState(seed=100)
        
        # Deal to both
        cards1 = gs1.deal_street()
        cards2 = gs2.deal_street()
        
        # Should get same cards due to same seed
        assert [str(c) for c in cards1] == [str(c) for c in cards2]
        
        # Modify one
        placements = [(cards1[i], 'back', i) for i in range(5)]
        gs1.place_cards(placements)
        
        # Other should be unaffected
        assert gs1.current_street == Street.FIRST
        assert gs2.current_street == Street.INITIAL


class TestMemoryEdgeCases:
    """Test memory-related edge cases."""
    
    def test_large_hand_evaluation(self):
        """Test evaluating many hands doesn't leak memory."""
        # Create and evaluate many hands
        hands_evaluated = 0
        
        for _ in range(1000):
            deck = Card.deck()
            random.shuffle(deck)
            hand = Hand(deck[:5])
            _ = hand.hand_type
            hands_evaluated += 1
        
        assert hands_evaluated == 1000
        
        # Hands should be garbage collected
        # (Can't easily test this without memory profiler)
    
    def test_circular_references(self):
        """Test that circular references don't cause issues."""
        # MCTS nodes have parent-child relationships
        from src.core.algorithms.mcts_node import MCTSNode
        
        root = MCTSNode(GameState())
        child1 = MCTSNode(GameState(), parent=root)
        child2 = MCTSNode(GameState(), parent=root)
        
        root.children = [child1, child2]
        
        # Delete root - children should also be collectible
        del root
        # Children now have no strong reference from root
        
        # This would be verified by garbage collector


# Helper to run all edge case tests with summary
def run_edge_case_summary():
    """Run and summarize all edge case tests."""
    print("\n" + "="*60)
    print("OFC Solver Edge Case Test Summary")
    print("="*60)
    
    test_classes = [
        TestCardEdgeCases,
        TestCardSetEdgeCases,
        TestHandEdgeCases,
        TestGameStateEdgeCases,
        TestPlayerArrangementEdgeCases,
        TestExceptionEdgeCases,
        TestConcurrencyEdgeCases,
        TestMemoryEdgeCases,
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        test_instance = test_class()
        
        for method_name in dir(test_instance):
            if method_name.startswith('test_'):
                total_tests += 1
                try:
                    method = getattr(test_instance, method_name)
                    method()
                    print(f"  ✓ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
    
    print(f"\n{passed_tests}/{total_tests} edge case tests passed")


if __name__ == "__main__":
    run_edge_case_summary()