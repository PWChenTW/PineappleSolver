"""
Player arrangement representing the three hands in OFC.

This module defines how cards are arranged in front, middle, and back hands,
and validates the arrangement according to OFC rules.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from src.core.domain.card import Card
from src.core.domain.card_set import CardSet
from src.core.domain.hand import Hand
from src.core.domain.hand_type import HandCategory


@dataclass
class RoyaltyPoints:
    """Royalty points for each hand."""
    front: int = 0
    middle: int = 0
    back: int = 0
    
    @property
    def total(self) -> int:
        """Get total royalty points."""
        return self.front + self.middle + self.back


class PlayerArrangement:
    """
    Represents a player's card arrangement in OFC.
    
    Manages the placement of cards in three hands and validates
    the arrangement according to OFC rules.
    """
    
    def __init__(self):
        """Initialize empty arrangement."""
        self._front_cards: List[Optional[Card]] = [None] * 3
        self._middle_cards: List[Optional[Card]] = [None] * 5
        self._back_cards: List[Optional[Card]] = [None] * 5
        self._used_cards = CardSet.empty()
    
    def place_card(self, card: Card, position: str, index: int) -> None:
        """
        Place a card in a specific position.
        
        Args:
            card: The card to place
            position: 'front', 'middle', or 'back'
            index: Position within the hand (0-based)
        
        Raises:
            ValueError: If position is invalid or already occupied
        """
        if card in self._used_cards:
            raise ValueError(f"Card {card} already used")
        
        if position == 'front':
            if not (0 <= index < 3):
                raise ValueError(f"Invalid front index: {index}")
            if self._front_cards[index] is not None:
                raise ValueError(f"Front position {index} already occupied")
            self._front_cards[index] = card
        
        elif position == 'middle':
            if not (0 <= index < 5):
                raise ValueError(f"Invalid middle index: {index}")
            if self._middle_cards[index] is not None:
                raise ValueError(f"Middle position {index} already occupied")
            self._middle_cards[index] = card
        
        elif position == 'back':
            if not (0 <= index < 5):
                raise ValueError(f"Invalid back index: {index}")
            if self._back_cards[index] is not None:
                raise ValueError(f"Back position {index} already occupied")
            self._back_cards[index] = card
        
        else:
            raise ValueError(f"Invalid position: {position}")
        
        self._used_cards.add(card)
    
    def remove_card(self, position: str, index: int) -> Optional[Card]:
        """
        Remove a card from a position.
        
        Args:
            position: 'front', 'middle', or 'back'
            index: Position within the hand
            
        Returns:
            The removed card, or None if position was empty
        """
        card = None
        
        if position == 'front':
            card = self._front_cards[index]
            self._front_cards[index] = None
        elif position == 'middle':
            card = self._middle_cards[index]
            self._middle_cards[index] = None
        elif position == 'back':
            card = self._back_cards[index]
            self._back_cards[index] = None
        
        if card is not None:
            self._used_cards.remove(card)
        
        return card
    
    @property
    def front_cards(self) -> List[Optional[Card]]:
        """Get front hand cards (including None for empty spots)."""
        return self._front_cards.copy()
    
    @property
    def middle_cards(self) -> List[Optional[Card]]:
        """Get middle hand cards (including None for empty spots)."""
        return self._middle_cards.copy()
    
    @property
    def back_cards(self) -> List[Optional[Card]]:
        """Get back hand cards (including None for empty spots)."""
        return self._back_cards.copy()
    
    @property
    def used_cards(self) -> CardSet:
        """Get set of all used cards."""
        return self._used_cards.copy()
    
    @property
    def cards_placed(self) -> int:
        """Get total number of cards placed."""
        return len(self._used_cards)
    
    @property
    def is_complete(self) -> bool:
        """Check if all 13 positions are filled."""
        return self.cards_placed == 13
    
    def get_front_hand(self) -> Optional[Hand]:
        """Get the front hand if complete."""
        cards = [c for c in self._front_cards if c is not None]
        if len(cards) == 3:
            return Hand(cards)
        return None
    
    def get_middle_hand(self) -> Optional[Hand]:
        """Get the middle hand if complete."""
        cards = [c for c in self._middle_cards if c is not None]
        if len(cards) == 5:
            return Hand(cards)
        return None
    
    def get_back_hand(self) -> Optional[Hand]:
        """Get the back hand if complete."""
        cards = [c for c in self._back_cards if c is not None]
        if len(cards) == 5:
            return Hand(cards)
        return None
    
    def is_valid_progressive(self) -> Tuple[bool, Optional[str]]:
        """
        Check if current arrangement is valid (no fouls).
        
        Returns partial hands for progressive checking during play.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get whatever cards we have in each position
        front_cards = [c for c in self._front_cards if c is not None]
        middle_cards = [c for c in self._middle_cards if c is not None]
        back_cards = [c for c in self._back_cards if c is not None]
        
        # Can't validate until we have at least 2 cards in positions to compare
        if len(front_cards) < 2 or len(middle_cards) < 2 or len(back_cards) < 2:
            return True, None  # Too early to determine
        
        # For partial validation, we check what we can
        # This is complex as we need to consider potential completions
        # For now, return True until hands are complete
        if not self.is_complete:
            return True, None
        
        return self.is_valid()
    
    def is_valid(self) -> Tuple[bool, Optional[str]]:
        """
        Check if the arrangement follows OFC rules (back >= middle >= front).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_complete:
            return False, "Arrangement not complete"
        
        front = self.get_front_hand()
        middle = self.get_middle_hand()
        back = self.get_back_hand()
        
        if front is None or middle is None or back is None:
            return False, "Hands not properly formed"
        
        # Check back >= middle
        if back < middle:
            return False, "Back hand must be stronger than or equal to middle hand"
        
        # Check middle >= front
        # Special case: front hand uses different comparison
        if not self._compare_hands_ofc(middle, front):
            return False, "Middle hand must be stronger than or equal to front hand"
        
        return True, None
    
    def _compare_hands_ofc(self, five_card: Hand, three_card: Hand) -> bool:
        """
        Compare a 5-card hand with a 3-card hand using OFC rules.
        
        In OFC, any 5-card hand category beats any 3-card category except:
        - Three of a kind (3-card) beats two pair or less (5-card)
        """
        five_type = five_card.hand_type
        three_type = three_card.hand_type
        
        # Three of a kind in front beats two pair or less in middle
        if (three_type.category == HandCategory.THREE_OF_A_KIND and 
            five_type.category <= HandCategory.TWO_PAIR):
            return False
        
        # Otherwise, any 5-card hand beats any 3-card hand
        return True
    
    def calculate_royalties(self) -> RoyaltyPoints:
        """Calculate royalty points for the current arrangement."""
        if not self.is_complete:
            return RoyaltyPoints()
        
        points = RoyaltyPoints()
        
        # Front hand royalties
        front = self.get_front_hand()
        if front:
            front_type = front.hand_type
            if front_type.category == HandCategory.PAIR:
                # Pairs 66-AA get royalties
                pair_rank = front_type.primary_rank
                if pair_rank >= 4:  # 6 or higher
                    points.front = pair_rank - 3  # 66=1, 77=2, ..., AA=9
            elif front_type.category == HandCategory.THREE_OF_A_KIND:
                # Trips get 10-22 points (222=10, ..., AAA=22)
                points.front = 10 + front_type.primary_rank
        
        # Middle hand royalties
        middle = self.get_middle_hand()
        if middle:
            middle_type = middle.hand_type
            royalty_map = {
                HandCategory.THREE_OF_A_KIND: 2,
                HandCategory.STRAIGHT: 4,
                HandCategory.FLUSH: 8,
                HandCategory.FULL_HOUSE: 12,
                HandCategory.FOUR_OF_A_KIND: 20,
                HandCategory.STRAIGHT_FLUSH: 30,
                HandCategory.ROYAL_FLUSH: 50
            }
            points.middle = royalty_map.get(middle_type.category, 0)
        
        # Back hand royalties
        back = self.get_back_hand()
        if back:
            back_type = back.hand_type
            royalty_map = {
                HandCategory.STRAIGHT: 2,
                HandCategory.FLUSH: 4,
                HandCategory.FULL_HOUSE: 6,
                HandCategory.FOUR_OF_A_KIND: 10,
                HandCategory.STRAIGHT_FLUSH: 15,
                HandCategory.ROYAL_FLUSH: 25
            }
            points.back = royalty_map.get(back_type.category, 0)
        
        return points
    
    def qualifies_for_fantasyland(self) -> bool:
        """Check if arrangement qualifies for Fantasyland (QQ+ in front)."""
        front = self.get_front_hand()
        if not front:
            return False
        
        front_type = front.hand_type
        
        # Three of a kind always qualifies
        if front_type.category == HandCategory.THREE_OF_A_KIND:
            return True
        
        # Pair of queens or better
        if front_type.category == HandCategory.PAIR:
            return front_type.primary_rank >= 10  # Q=10, K=11, A=12
        
        return False
    
    def __str__(self) -> str:
        """String representation of arrangement."""
        lines = []
        
        # Front
        front_str = " ".join(str(c) if c else "__" for c in self._front_cards)
        lines.append(f"Front:  {front_str}")
        
        # Middle  
        middle_str = " ".join(str(c) if c else "__" for c in self._middle_cards)
        lines.append(f"Middle: {middle_str}")
        
        # Back
        back_str = " ".join(str(c) if c else "__" for c in self._back_cards)
        lines.append(f"Back:   {back_str}")
        
        return "\n".join(lines)