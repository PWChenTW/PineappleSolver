"""
Comprehensive test suite for Hand domain model.
"""

import pytest
from src.core.domain.card import Card, Rank, Suit
from src.core.domain.hand import Hand
from src.core.domain.hand_type import HandType, HandCategory


class TestHandBasics:
    """Test basic Hand functionality."""
    
    def test_hand_creation_valid(self):
        """Test creating valid hands."""
        # 3-card hand
        cards_3 = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ]
        hand_3 = Hand(cards_3)
        assert hand_3.size == 3
        assert hand_3.is_front_hand
        assert len(hand_3.cards) == 3
        
        # 5-card hand
        cards_5 = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd"),
            Card.from_string("Jc"),
            Card.from_string("Ts")
        ]
        hand_5 = Hand(cards_5)
        assert hand_5.size == 5
        assert not hand_5.is_front_hand
        assert len(hand_5.cards) == 5
    
    def test_hand_creation_invalid(self):
        """Test creating invalid hands."""
        # Wrong number of cards
        with pytest.raises(ValueError) as exc_info:
            Hand([Card.from_string("As")])
        assert "3 or 5 cards" in str(exc_info.value)
        
        with pytest.raises(ValueError):
            Hand([Card.from_string("As"), Card.from_string("Kh")])
        
        with pytest.raises(ValueError):
            Hand([Card.from_string(c) for c in ["As", "Kh", "Qd", "Jc"]])
        
        # Empty hand
        with pytest.raises(ValueError):
            Hand([])
    
    def test_cards_sorted(self):
        """Test that cards are sorted by rank (high to low)."""
        cards = [
            Card.from_string("2s"),
            Card.from_string("As"),
            Card.from_string("Kh")
        ]
        hand = Hand(cards)
        hand_cards = hand.cards
        
        assert hand_cards[0].rank == Rank.ACE
        assert hand_cards[1].rank == Rank.KING
        assert hand_cards[2].rank == Rank.TWO
    
    def test_from_strings(self):
        """Test creating hand from string representations."""
        hand = Hand.from_strings(["As", "Kh", "Qd"])
        assert hand.size == 3
        assert hand.cards[0].rank == Rank.ACE


class TestThreeCardEvaluation:
    """Test 3-card hand evaluation."""
    
    def test_three_of_a_kind(self):
        """Test three of a kind detection."""
        # Natural three of a kind
        hand = Hand.from_strings(["As", "Ah", "Ad"])
        assert hand.hand_type.category == HandCategory.THREE_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.ACE.value
        
        # Different rank
        hand = Hand.from_strings(["7s", "7h", "7d"])
        assert hand.hand_type.category == HandCategory.THREE_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.SEVEN.value
    
    def test_pair(self):
        """Test pair detection."""
        hand = Hand.from_strings(["As", "Ah", "Kd"])
        assert hand.hand_type.category == HandCategory.PAIR
        assert hand.hand_type.primary_rank == Rank.ACE.value
        assert hand.hand_type.kickers == [Rank.KING.value]
        
        # Lower pair with ace kicker
        hand = Hand.from_strings(["Ks", "Kh", "Ad"])
        assert hand.hand_type.category == HandCategory.PAIR
        assert hand.hand_type.primary_rank == Rank.KING.value
        assert hand.hand_type.kickers == [Rank.ACE.value]
    
    def test_high_card(self):
        """Test high card detection."""
        hand = Hand.from_strings(["As", "Kh", "Qd"])
        assert hand.hand_type.category == HandCategory.HIGH_CARD
        assert hand.hand_type.primary_rank == Rank.ACE.value
        assert hand.hand_type.kickers == [Rank.KING.value, Rank.QUEEN.value]
        
        # Different high card
        hand = Hand.from_strings(["9s", "7h", "5d"])
        assert hand.hand_type.category == HandCategory.HIGH_CARD
        assert hand.hand_type.primary_rank == Rank.NINE.value
        assert hand.hand_type.kickers == [Rank.SEVEN.value, Rank.FIVE.value]


class TestFiveCardEvaluation:
    """Test 5-card hand evaluation."""
    
    def test_royal_flush(self):
        """Test royal flush detection."""
        hand = Hand.from_strings(["As", "Ks", "Qs", "Js", "Ts"])
        assert hand.hand_type.category == HandCategory.ROYAL_FLUSH
        assert hand.hand_type.primary_rank == Rank.ACE.value
    
    def test_straight_flush(self):
        """Test straight flush detection."""
        # High straight flush
        hand = Hand.from_strings(["Kh", "Qh", "Jh", "Th", "9h"])
        assert hand.hand_type.category == HandCategory.STRAIGHT_FLUSH
        assert hand.hand_type.primary_rank == Rank.KING.value
        
        # Low straight flush (5-high)
        hand = Hand.from_strings(["5d", "4d", "3d", "2d", "Ad"])
        assert hand.hand_type.category == HandCategory.STRAIGHT_FLUSH
        assert hand.hand_type.primary_rank == Rank.FIVE.value - 2  # 5-high straight
    
    def test_four_of_a_kind(self):
        """Test four of a kind detection."""
        hand = Hand.from_strings(["As", "Ah", "Ad", "Ac", "Kh"])
        assert hand.hand_type.category == HandCategory.FOUR_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.ACE.value
        assert hand.hand_type.kickers == [Rank.KING.value]
        
        # Different rank
        hand = Hand.from_strings(["7s", "7h", "7d", "7c", "2h"])
        assert hand.hand_type.category == HandCategory.FOUR_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.SEVEN.value
        assert hand.hand_type.kickers == [Rank.TWO.value]
    
    def test_full_house(self):
        """Test full house detection."""
        hand = Hand.from_strings(["As", "Ah", "Ad", "Kc", "Kh"])
        assert hand.hand_type.category == HandCategory.FULL_HOUSE
        assert hand.hand_type.primary_rank == Rank.ACE.value
        assert hand.hand_type.secondary_rank == Rank.KING.value
        
        # Reverse (KKK AA)
        hand = Hand.from_strings(["Ks", "Kh", "Kd", "Ac", "Ah"])
        assert hand.hand_type.category == HandCategory.FULL_HOUSE
        assert hand.hand_type.primary_rank == Rank.KING.value
        assert hand.hand_type.secondary_rank == Rank.ACE.value
    
    def test_flush(self):
        """Test flush detection."""
        hand = Hand.from_strings(["As", "Ks", "Qs", "7s", "2s"])
        assert hand.hand_type.category == HandCategory.FLUSH
        assert hand.hand_type.primary_rank == Rank.ACE.value
        expected_kickers = [Rank.KING.value, Rank.QUEEN.value, Rank.SEVEN.value, Rank.TWO.value]
        assert hand.hand_type.kickers == expected_kickers
        
        # Different suit
        hand = Hand.from_strings(["Jh", "9h", "7h", "5h", "3h"])
        assert hand.hand_type.category == HandCategory.FLUSH
        assert hand.hand_type.primary_rank == Rank.JACK.value
    
    def test_straight(self):
        """Test straight detection."""
        # Ace-high straight
        hand = Hand.from_strings(["As", "Kh", "Qd", "Jc", "Ts"])
        assert hand.hand_type.category == HandCategory.STRAIGHT
        assert hand.hand_type.primary_rank == Rank.ACE.value
        
        # Middle straight
        hand = Hand.from_strings(["9s", "8h", "7d", "6c", "5s"])
        assert hand.hand_type.category == HandCategory.STRAIGHT
        assert hand.hand_type.primary_rank == Rank.NINE.value
        
        # Ace-low straight (wheel)
        hand = Hand.from_strings(["5s", "4h", "3d", "2c", "As"])
        assert hand.hand_type.category == HandCategory.STRAIGHT
        assert hand.hand_type.primary_rank == Rank.FIVE.value - 2  # 5-high
    
    def test_three_of_a_kind_five_card(self):
        """Test three of a kind in 5-card hand."""
        hand = Hand.from_strings(["As", "Ah", "Ad", "Kc", "Qh"])
        assert hand.hand_type.category == HandCategory.THREE_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.ACE.value
        assert hand.hand_type.kickers == [Rank.KING.value, Rank.QUEEN.value]
    
    def test_two_pair(self):
        """Test two pair detection."""
        hand = Hand.from_strings(["As", "Ah", "Kd", "Kc", "Qh"])
        assert hand.hand_type.category == HandCategory.TWO_PAIR
        assert hand.hand_type.primary_rank == Rank.ACE.value
        assert hand.hand_type.secondary_rank == Rank.KING.value
        assert hand.hand_type.kickers == [Rank.QUEEN.value]
        
        # Lower two pair
        hand = Hand.from_strings(["7s", "7h", "5d", "5c", "Ah"])
        assert hand.hand_type.category == HandCategory.TWO_PAIR
        assert hand.hand_type.primary_rank == Rank.SEVEN.value
        assert hand.hand_type.secondary_rank == Rank.FIVE.value
        assert hand.hand_type.kickers == [Rank.ACE.value]
    
    def test_pair_five_card(self):
        """Test pair in 5-card hand."""
        hand = Hand.from_strings(["As", "Ah", "Kd", "Qc", "Jh"])
        assert hand.hand_type.category == HandCategory.PAIR
        assert hand.hand_type.primary_rank == Rank.ACE.value
        assert hand.hand_type.kickers == [Rank.KING.value, Rank.QUEEN.value, Rank.JACK.value]
    
    def test_high_card_five_card(self):
        """Test high card in 5-card hand."""
        hand = Hand.from_strings(["As", "Kh", "Qd", "Jc", "9h"])
        assert hand.hand_type.category == HandCategory.HIGH_CARD
        assert hand.hand_type.primary_rank == Rank.ACE.value
        expected_kickers = [Rank.KING.value, Rank.QUEEN.value, Rank.JACK.value, Rank.NINE.value]
        assert hand.hand_type.kickers == expected_kickers


class TestHandComparison:
    """Test hand comparison operations."""
    
    def test_hand_comparison_different_categories(self):
        """Test comparing hands of different categories."""
        royal_flush = Hand.from_strings(["As", "Ks", "Qs", "Js", "Ts"])
        straight = Hand.from_strings(["9s", "8h", "7d", "6c", "5s"])
        pair = Hand.from_strings(["As", "Ah", "Kd", "Qc", "Jh"])
        
        assert royal_flush > straight
        assert straight > pair
        assert not (pair > straight)
        assert pair < royal_flush
    
    def test_hand_comparison_same_category(self):
        """Test comparing hands of same category."""
        # Pairs
        aces = Hand.from_strings(["As", "Ah", "Kd", "Qc", "Jh"])
        kings = Hand.from_strings(["Ks", "Kh", "Ad", "Qc", "Jh"])
        assert aces > kings
        
        # Straights
        high_straight = Hand.from_strings(["As", "Kh", "Qd", "Jc", "Ts"])
        low_straight = Hand.from_strings(["9s", "8h", "7d", "6c", "5s"])
        assert high_straight > low_straight
    
    def test_hand_equality(self):
        """Test hand equality."""
        hand1 = Hand.from_strings(["As", "Ah", "Kd", "Qc", "Jh"])
        hand2 = Hand.from_strings(["Ac", "Ad", "Kh", "Qs", "Jd"])
        hand3 = Hand.from_strings(["Ks", "Kh", "Ad", "Qc", "Jh"])
        
        assert hand1 == hand2  # Same hand type and ranks
        assert hand1 != hand3  # Different primary rank
        assert hand1 != "not a hand"  # Different type
    
    def test_three_card_comparison(self):
        """Test comparing 3-card hands."""
        trips = Hand.from_strings(["As", "Ah", "Ad"])
        pair = Hand.from_strings(["Ks", "Kh", "Qd"])
        high = Hand.from_strings(["As", "Kh", "Qd"])
        
        assert trips > pair
        assert pair > high
        assert trips > high


class TestSpecialCases:
    """Test special cases and edge conditions."""
    
    def test_joker_handling(self):
        """Test hands with jokers."""
        # Joker in 3-card hand (should make three of a kind with aces)
        joker = Card(52)
        hand = Hand([joker, Card.from_string("As"), Card.from_string("Ah")])
        assert hand.hand_type.category == HandCategory.THREE_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.ACE.value
        
        # All jokers (3-card)
        hand = Hand([Card(52), Card(52), Card(52)])
        assert hand.hand_type.category == HandCategory.THREE_OF_A_KIND
        assert hand.hand_type.primary_rank == Rank.ACE.value
    
    def test_unsorted_input(self):
        """Test that unsorted input is handled correctly."""
        # Cards given in random order
        cards = [
            Card.from_string("7h"),
            Card.from_string("As"),
            Card.from_string("2c"),
            Card.from_string("Kd"),
            Card.from_string("Qh")
        ]
        hand = Hand(cards)
        
        # Should be sorted internally
        sorted_cards = hand.cards
        assert sorted_cards[0].rank == Rank.ACE
        assert sorted_cards[1].rank == Rank.KING
        assert sorted_cards[2].rank == Rank.QUEEN
        assert sorted_cards[3].rank == Rank.SEVEN
        assert sorted_cards[4].rank == Rank.TWO
    
    def test_string_representation(self):
        """Test string representation of hands."""
        hand = Hand.from_strings(["As", "Kh", "Qd"])
        str_repr = str(hand)
        
        assert "Hand(" in str_repr
        assert "AS" in str_repr
        assert "KH" in str_repr
        assert "QD" in str_repr
        assert str(hand.hand_type) in str_repr
    
    def test_immutability(self):
        """Test that hands are effectively immutable."""
        original_cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ]
        hand = Hand(original_cards)
        
        # Getting cards returns a copy
        retrieved_cards = hand.cards
        retrieved_cards.append(Card.from_string("Jc"))
        
        # Original hand should be unchanged
        assert hand.size == 3
        assert len(hand.cards) == 3