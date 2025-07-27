"""
Hand entity representing a collection of cards in OFC.

This module provides the Hand class which can evaluate poker hands
and determine their type and strength.
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Dict
from collections import Counter

from src.core.domain.card import Card, Rank, Suit
from src.core.domain.card_set import CardSet
from src.core.domain.hand_type import HandType, HandCategory


class Hand:
    """
    Represents a poker hand with evaluation capabilities.
    
    Supports both 3-card (front) and 5-card (middle/back) hands.
    """
    
    __slots__ = ('_cards', '_card_set', '_hand_type', '_is_evaluated')
    
    def __init__(self, cards: List[Card]):
        """
        Initialize hand with list of cards.
        
        Args:
            cards: List of Card objects (3 or 5 cards)
        """
        if len(cards) not in (3, 5):
            raise ValueError(f"Hand must have 3 or 5 cards, got {len(cards)}")
        
        self._cards = sorted(cards, key=lambda c: c.rank_value, reverse=True)
        self._card_set = CardSet.from_cards(cards)
        self._hand_type: Optional[HandType] = None
        self._is_evaluated = False
    
    @property
    def cards(self) -> List[Card]:
        """Get the cards in this hand."""
        return self._cards.copy()
    
    @property
    def size(self) -> int:
        """Get the number of cards."""
        return len(self._cards)
    
    @property
    def is_front_hand(self) -> bool:
        """Check if this is a 3-card front hand."""
        return len(self._cards) == 3
    
    @property
    def hand_type(self) -> HandType:
        """Get the evaluated hand type."""
        if not self._is_evaluated:
            self._evaluate()
        return self._hand_type
    
    def _evaluate(self) -> None:
        """Evaluate the hand type."""
        if self.is_front_hand:
            self._evaluate_three_card()
        else:
            self._evaluate_five_card()
        self._is_evaluated = True
    
    def _evaluate_three_card(self) -> None:
        """Evaluate a 3-card front hand."""
        # Count ranks
        rank_counts = Counter(card.rank_value for card in self._cards if not card.is_joker)
        joker_count = sum(1 for card in self._cards if card.is_joker)
        
        # Get sorted ranks
        sorted_counts = sorted(rank_counts.items(), key=lambda x: (-x[1], -x[0]))
        
        if not sorted_counts:  # All jokers
            # Three jokers = Three Aces
            self._hand_type = HandType(HandCategory.THREE_OF_A_KIND, Rank.ACE.value)
            return
        
        # Check for three of a kind
        if sorted_counts[0][1] + joker_count >= 3:
            self._hand_type = HandType(HandCategory.THREE_OF_A_KIND, sorted_counts[0][0])
            return
        
        # Check for pair
        if sorted_counts[0][1] + joker_count >= 2:
            # Find kicker
            kickers = []
            for rank, count in sorted_counts:
                if rank != sorted_counts[0][0]:
                    kickers.append(rank)
            self._hand_type = HandType(HandCategory.PAIR, sorted_counts[0][0], kickers=kickers)
            return
        
        # High card
        kickers = [rank for rank, _ in sorted_counts]
        self._hand_type = HandType(HandCategory.HIGH_CARD, kickers[0], kickers=kickers)
    
    def _evaluate_five_card(self) -> None:
        """Evaluate a 5-card hand."""
        # Count ranks and suits
        rank_counts = Counter(card.rank_value for card in self._cards if not card.is_joker)
        suit_counts = Counter(card.suit_value for card in self._cards if not card.is_joker)
        joker_count = sum(1 for card in self._cards if card.is_joker)
        
        # Check for flush
        flush_suit = None
        for suit, count in suit_counts.items():
            if count + joker_count >= 5:
                flush_suit = suit
                break
        
        # Check for straight
        is_straight, straight_high = self._check_straight(rank_counts, joker_count)
        
        # Check for straight flush / royal flush
        if flush_suit is not None and is_straight:
            if straight_high == Rank.ACE.value:
                self._hand_type = HandType(HandCategory.ROYAL_FLUSH, Rank.ACE.value)
            else:
                self._hand_type = HandType(HandCategory.STRAIGHT_FLUSH, straight_high)
            return
        
        # Sort rank counts
        sorted_counts = sorted(rank_counts.items(), key=lambda x: (-x[1], -x[0]))
        
        # Check for four of a kind
        if sorted_counts and sorted_counts[0][1] + joker_count >= 4:
            kicker = sorted_counts[1][0] if len(sorted_counts) > 1 else sorted_counts[0][0] - 1
            self._hand_type = HandType(HandCategory.FOUR_OF_A_KIND, sorted_counts[0][0], kickers=[kicker])
            return
        
        # Check for full house
        if len(sorted_counts) >= 2:
            if sorted_counts[0][1] + joker_count >= 3:
                jokers_used = max(0, 3 - sorted_counts[0][1])
                remaining_jokers = joker_count - jokers_used
                if sorted_counts[1][1] + remaining_jokers >= 2:
                    self._hand_type = HandType(HandCategory.FULL_HOUSE, 
                                             sorted_counts[0][0], 
                                             sorted_counts[1][0])
                    return
        
        # Check for flush (already determined)
        if flush_suit is not None:
            # Get all cards of flush suit in descending order
            flush_ranks = sorted([c.rank_value for c in self._cards 
                                if not c.is_joker and c.suit_value == flush_suit], 
                               reverse=True)
            # Fill with jokers as aces
            flush_ranks = [Rank.ACE.value] * min(joker_count, 5 - len(flush_ranks)) + flush_ranks
            self._hand_type = HandType(HandCategory.FLUSH, flush_ranks[0], kickers=flush_ranks[1:])
            return
        
        # Check for straight (already determined)
        if is_straight:
            self._hand_type = HandType(HandCategory.STRAIGHT, straight_high)
            return
        
        # Check for three of a kind
        if sorted_counts and sorted_counts[0][1] + joker_count >= 3:
            kickers = []
            for rank, count in sorted_counts[1:]:
                kickers.append(rank)
            self._hand_type = HandType(HandCategory.THREE_OF_A_KIND, sorted_counts[0][0], kickers=kickers)
            return
        
        # Check for two pair
        if len(sorted_counts) >= 2:
            if sorted_counts[0][1] >= 2 and sorted_counts[1][1] + joker_count >= 2:
                kicker = sorted_counts[2][0] if len(sorted_counts) > 2 else None
                self._hand_type = HandType(HandCategory.TWO_PAIR, 
                                         sorted_counts[0][0], 
                                         sorted_counts[1][0],
                                         kickers=[kicker] if kicker is not None else [])
                return
        
        # Check for pair
        if sorted_counts and sorted_counts[0][1] + joker_count >= 2:
            kickers = []
            for rank, count in sorted_counts[1:]:
                kickers.append(rank)
            self._hand_type = HandType(HandCategory.PAIR, sorted_counts[0][0], kickers=kickers)
            return
        
        # High card
        all_ranks = []
        for rank, count in sorted_counts:
            all_ranks.extend([rank] * count)
        all_ranks.sort(reverse=True)
        # Add jokers as aces
        all_ranks = [Rank.ACE.value] * joker_count + all_ranks
        self._hand_type = HandType(HandCategory.HIGH_CARD, all_ranks[0], kickers=all_ranks[1:])
    
    def _check_straight(self, rank_counts: Counter, joker_count: int) -> Tuple[bool, Optional[int]]:
        """
        Check if cards form a straight.
        
        Returns:
            Tuple of (is_straight, high_card_rank)
        """
        # Get unique ranks
        ranks = sorted(rank_counts.keys())
        
        if not ranks:  # All jokers
            return True, Rank.ACE.value
        
        # Check for ace-low straight (A-2-3-4-5)
        if Rank.ACE.value in ranks:
            low_straight_ranks = [Rank.ACE.value, 0, 1, 2, 3]  # A,2,3,4,5
            gaps = 0
            for r in low_straight_ranks:
                if r not in ranks:
                    gaps += 1
            if gaps <= joker_count:
                return True, 3  # 5-high straight
        
        # Check for regular straights
        for start in range(Rank.ACE.value, -1, -1):
            if start < 3:  # Can't form a valid straight
                break
            
            gaps = 0
            for offset in range(5):
                if start - offset not in ranks:
                    gaps += 1
            
            if gaps <= joker_count:
                return True, start
        
        return False, None
    
    def __lt__(self, other: "Hand") -> bool:
        """Compare hands by strength."""
        return self.hand_type < other.hand_type
    
    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Hand):
            return NotImplemented
        return self.hand_type == other.hand_type
    
    def __str__(self) -> str:
        """String representation."""
        cards_str = " ".join(str(card) for card in self._cards)
        return f"Hand({cards_str}): {self.hand_type}"
    
    @classmethod
    def from_strings(cls, card_strings: List[str]) -> "Hand":
        """Create hand from card string representations."""
        cards = [Card.from_string(s) for s in card_strings]
        return cls(cards)