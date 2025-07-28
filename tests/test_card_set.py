"""
Comprehensive test suite for CardSet domain model.
"""

import pytest
from src.core.domain.card import Card, Rank, Suit
from src.core.domain.card_set import CardSet


class TestCardSet:
    """Test suite for CardSet class."""
    
    def test_empty_card_set(self):
        """Test creating and using empty card set."""
        cs = CardSet.empty()
        assert len(cs) == 0
        assert not cs  # Should be falsy when empty
        assert list(cs) == []
        assert cs.bits == 0
    
    def test_from_cards(self):
        """Test creating card set from list of cards."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ]
        cs = CardSet.from_cards(cards)
        
        assert len(cs) == 3
        assert all(card in cs for card in cards)
        assert Card.from_string("Ac") not in cs
    
    def test_full_deck(self):
        """Test creating full deck card set."""
        # Without jokers
        cs = CardSet.full_deck(include_jokers=False)
        assert len(cs) == 52
        
        # Verify all standard cards are present
        for rank in Rank:
            for suit in Suit:
                card = Card.from_rank_suit(rank, suit)
                assert card in cs
        
        # Joker should not be present
        joker = Card(52)
        assert joker not in cs
        
        # With jokers
        cs_with_jokers = CardSet.full_deck(include_jokers=True)
        assert len(cs_with_jokers) == 53
        assert joker in cs_with_jokers
    
    def test_add_remove(self):
        """Test adding and removing cards."""
        cs = CardSet.empty()
        card1 = Card.from_string("As")
        card2 = Card.from_string("Kh")
        
        # Add cards
        cs.add(card1)
        assert card1 in cs
        assert len(cs) == 1
        
        cs.add(card2)
        assert card2 in cs
        assert len(cs) == 2
        
        # Adding same card again should not change size
        cs.add(card1)
        assert len(cs) == 2
        
        # Remove card
        cs.remove(card1)
        assert card1 not in cs
        assert card2 in cs
        assert len(cs) == 1
        
        # Remove last card
        cs.remove(card2)
        assert len(cs) == 0
        assert not cs
    
    def test_discard(self):
        """Test discarding cards (no error if not present)."""
        cs = CardSet.empty()
        card = Card.from_string("As")
        
        # Discard from empty set should not raise error
        cs.discard(card)
        
        # Add and discard
        cs.add(card)
        cs.discard(card)
        assert card not in cs
        
        # Discard again should not raise error
        cs.discard(card)
    
    def test_contains(self):
        """Test membership testing."""
        cs = CardSet.from_cards([
            Card.from_string("As"),
            Card.from_string("Kh")
        ])
        
        assert cs.contains(Card.from_string("As"))
        assert Card.from_string("As") in cs
        assert not cs.contains(Card.from_string("Ac"))
        assert Card.from_string("Ac") not in cs
    
    def test_union(self):
        """Test set union operations."""
        cs1 = CardSet.from_cards([
            Card.from_string("As"),
            Card.from_string("Kh")
        ])
        cs2 = CardSet.from_cards([
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ])
        
        # Union
        union = cs1.union(cs2)
        assert len(union) == 3
        assert Card.from_string("As") in union
        assert Card.from_string("Kh") in union
        assert Card.from_string("Qd") in union
        
        # Using | operator
        union2 = cs1 | cs2
        assert union == union2
        
        # Original sets unchanged
        assert len(cs1) == 2
        assert len(cs2) == 2
    
    def test_intersection(self):
        """Test set intersection operations."""
        cs1 = CardSet.from_cards([
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ])
        cs2 = CardSet.from_cards([
            Card.from_string("Kh"),
            Card.from_string("Qd"),
            Card.from_string("Jc")
        ])
        
        # Intersection
        intersection = cs1.intersection(cs2)
        assert len(intersection) == 2
        assert Card.from_string("Kh") in intersection
        assert Card.from_string("Qd") in intersection
        assert Card.from_string("As") not in intersection
        assert Card.from_string("Jc") not in intersection
        
        # Using & operator
        intersection2 = cs1 & cs2
        assert intersection == intersection2
    
    def test_difference(self):
        """Test set difference operations."""
        cs1 = CardSet.from_cards([
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ])
        cs2 = CardSet.from_cards([
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ])
        
        # Difference
        diff = cs1.difference(cs2)
        assert len(diff) == 1
        assert Card.from_string("As") in diff
        assert Card.from_string("Kh") not in diff
        
        # Using - operator
        diff2 = cs1 - cs2
        assert diff == diff2
    
    def test_symmetric_difference(self):
        """Test symmetric difference operations."""
        cs1 = CardSet.from_cards([
            Card.from_string("As"),
            Card.from_string("Kh")
        ])
        cs2 = CardSet.from_cards([
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ])
        
        # Symmetric difference
        sym_diff = cs1.symmetric_difference(cs2)
        assert len(sym_diff) == 2
        assert Card.from_string("As") in sym_diff
        assert Card.from_string("Qd") in sym_diff
        assert Card.from_string("Kh") not in sym_diff
        
        # Using ^ operator
        sym_diff2 = cs1 ^ cs2
        assert sym_diff == sym_diff2
    
    def test_subset_superset(self):
        """Test subset and superset operations."""
        cs1 = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        cs2 = CardSet.from_cards([Card.from_string("As")])
        cs3 = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh"), Card.from_string("Qd")])
        
        # Subset
        assert cs2.issubset(cs1)  # {As} ⊆ {As, Kh}
        assert cs1.issubset(cs3)  # {As, Kh} ⊆ {As, Kh, Qd}
        assert not cs3.issubset(cs1)  # {As, Kh, Qd} ⊄ {As, Kh}
        assert cs1.issubset(cs1)  # Set is subset of itself
        
        # Superset
        assert cs1.issuperset(cs2)  # {As, Kh} ⊇ {As}
        assert cs3.issuperset(cs1)  # {As, Kh, Qd} ⊇ {As, Kh}
        assert not cs1.issuperset(cs3)  # {As, Kh} ⊉ {As, Kh, Qd}
        assert cs1.issuperset(cs1)  # Set is superset of itself
    
    def test_disjoint(self):
        """Test disjoint set checking."""
        cs1 = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        cs2 = CardSet.from_cards([Card.from_string("Qd"), Card.from_string("Jc")])
        cs3 = CardSet.from_cards([Card.from_string("Kh"), Card.from_string("Tc")])
        
        assert cs1.isdisjoint(cs2)  # No common cards
        assert not cs1.isdisjoint(cs3)  # Kh is common
        assert cs1.isdisjoint(CardSet.empty())  # Empty set is disjoint with any set
    
    def test_copy(self):
        """Test copying card sets."""
        cs1 = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        cs2 = cs1.copy()
        
        # Should be equal but different objects
        assert cs1 == cs2
        assert cs1 is not cs2
        
        # Modifying copy should not affect original
        cs2.add(Card.from_string("Qd"))
        assert len(cs1) == 2
        assert len(cs2) == 3
    
    def test_clear(self):
        """Test clearing card set."""
        cs = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        assert len(cs) == 2
        
        cs.clear()
        assert len(cs) == 0
        assert not cs
        assert cs.bits == 0
    
    def test_iteration(self):
        """Test iterating over card set."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ]
        cs = CardSet.from_cards(cards)
        
        # Iterate and collect
        collected = list(cs)
        assert len(collected) == 3
        assert all(card in cards for card in collected)
        
        # Multiple iterations should work
        collected2 = list(cs)
        assert collected2 == collected
    
    def test_to_list_and_set(self):
        """Test converting to list and set."""
        cards = [
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ]
        cs = CardSet.from_cards(cards)
        
        # To list
        card_list = cs.to_list()
        assert len(card_list) == 3
        assert all(isinstance(card, Card) for card in card_list)
        assert all(card in cards for card in card_list)
        
        # To set
        card_set = cs.to_set()
        assert len(card_set) == 3
        assert isinstance(card_set, set)
        assert all(card in cards for card in card_set)
    
    def test_string_representation(self):
        """Test string representations."""
        cs = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        
        # str() should list cards
        str_repr = str(cs)
        assert "CardSet(" in str_repr
        assert "AS" in str_repr or "KH" in str_repr
        
        # repr() should show bits
        repr_str = repr(cs)
        assert "CardSet(bits=" in repr_str
    
    def test_in_place_operations(self):
        """Test in-place set operations."""
        # Union
        cs1 = CardSet.from_cards([Card.from_string("As")])
        cs1 |= CardSet.from_cards([Card.from_string("Kh")])
        assert len(cs1) == 2
        assert Card.from_string("As") in cs1
        assert Card.from_string("Kh") in cs1
        
        # Intersection
        cs2 = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        cs2 &= CardSet.from_cards([Card.from_string("As")])
        assert len(cs2) == 1
        assert Card.from_string("As") in cs2
        assert Card.from_string("Kh") not in cs2
        
        # Difference
        cs3 = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        cs3 -= CardSet.from_cards([Card.from_string("Kh")])
        assert len(cs3) == 1
        assert Card.from_string("As") in cs3
        
        # Symmetric difference
        cs4 = CardSet.from_cards([Card.from_string("As"), Card.from_string("Kh")])
        cs4 ^= CardSet.from_cards([Card.from_string("Kh"), Card.from_string("Qd")])
        assert len(cs4) == 2
        assert Card.from_string("As") in cs4
        assert Card.from_string("Qd") in cs4
        assert Card.from_string("Kh") not in cs4
    
    def test_pop(self):
        """Test popping cards from set."""
        cs = CardSet.from_cards([
            Card.from_string("As"),
            Card.from_string("Kh"),
            Card.from_string("Qd")
        ])
        
        initial_cards = cs.to_set()
        popped_cards = set()
        
        # Pop all cards
        while cs:
            card = cs.pop()
            assert isinstance(card, Card)
            assert card not in cs  # Should be removed
            popped_cards.add(card)
        
        # All cards should have been popped
        assert popped_cards == initial_cards
        assert len(cs) == 0
        
        # Pop from empty set should raise error
        with pytest.raises(KeyError) as exc_info:
            cs.pop()
        assert "empty" in str(exc_info.value)
    
    def test_edge_cases(self):
        """Test edge cases and special scenarios."""
        # Empty sets
        empty1 = CardSet.empty()
        empty2 = CardSet.empty()
        assert empty1 == empty2
        assert empty1.issubset(empty2)
        assert empty1.issuperset(empty2)
        assert empty1.isdisjoint(empty2)
        
        # Single card operations
        single = CardSet.from_cards([Card.from_string("As")])
        assert len(single) == 1
        assert single.union(empty1) == single
        assert single.intersection(empty1) == empty1
        assert single.difference(empty1) == single
        
        # Joker handling
        joker_set = CardSet.from_cards([Card(52)])  # Joker
        regular_set = CardSet.from_cards([Card.from_string("As")])
        assert joker_set.isdisjoint(regular_set)
        
        # Large number of cards
        many_cards = Card.deck()[:26]  # Half deck
        large_set = CardSet.from_cards(many_cards)
        assert len(large_set) == 26
        
        # Bitwise representation
        ace_spades = CardSet.from_cards([Card.from_string("As")])
        # Ace of spades has value 51, so bit 51 should be set
        assert ace_spades.bits == (1 << 51)