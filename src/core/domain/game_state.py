"""
Game state management for OFC Solver.

This module manages the complete game state including deck, streets,
and player arrangements.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass
from enum import IntEnum
import random

from src.core.domain.card import Card
from src.core.domain.card_set import CardSet
from src.core.domain.player_arrangement import PlayerArrangement


class Street(IntEnum):
    """Game streets in Pineapple OFC."""
    INITIAL = 0  # 5 cards, place all
    FIRST = 1    # 3 cards, place 2, discard 1
    SECOND = 2   # 3 cards, place 2, discard 1
    THIRD = 3    # 3 cards, place 2, discard 1
    FOURTH = 4   # 3 cards, place 2, discard 1
    COMPLETE = 5 # Game complete


@dataclass
class StreetAction:
    """Action taken in a street."""
    street: Street
    cards_dealt: List[Card]
    cards_placed: List[Tuple[Card, str, int]]  # (card, position, index)
    card_discarded: Optional[Card] = None


class GameState:
    """
    Complete game state for OFC.
    
    Tracks the deck, current street, player arrangement,
    and all actions taken.
    """
    
    def __init__(self, 
                 num_players: int = 2,
                 player_index: int = 0,
                 num_jokers: int = 0,
                 seed: Optional[int] = None):
        """
        Initialize game state.
        
        Args:
            num_players: Number of players in the game
            player_index: Index of the player we're solving for
            num_jokers: Number of jokers in the deck
            seed: Random seed for reproducibility
        """
        self.num_players = num_players
        self.player_index = player_index
        self.num_jokers = num_jokers
        
        # Initialize deck
        self._deck = Card.deck(num_jokers)
        self._remaining_deck = CardSet.from_cards(self._deck)
        
        # Initialize RNG
        self._rng = random.Random(seed)
        if seed is not None:
            self._rng.shuffle(self._deck)
        
        # Game state
        self._current_street = Street.INITIAL
        self._player_arrangement = PlayerArrangement()
        self._opponent_used_cards = CardSet.empty()
        self._actions: List[StreetAction] = []
        
        # Cards currently in hand (dealt but not yet placed)
        self._current_hand: List[Card] = []
    
    @property
    def current_street(self) -> Street:
        """Get current street."""
        return self._current_street
    
    @property
    def player_arrangement(self) -> PlayerArrangement:
        """Get player's arrangement."""
        return self._player_arrangement
    
    @property
    def opponent_used_cards(self) -> CardSet:
        """Get cards used by opponents."""
        return self._opponent_used_cards.copy()
    
    @property
    def remaining_cards(self) -> CardSet:
        """Get cards remaining in deck."""
        used = self._player_arrangement.used_cards | self._opponent_used_cards
        return self._remaining_deck - used
    
    @property
    def current_hand(self) -> List[Card]:
        """Get cards currently in hand."""
        return self._current_hand.copy()
    
    @property
    def is_complete(self) -> bool:
        """Check if game is complete."""
        return self._current_street == Street.COMPLETE
    
    def deal_street(self) -> List[Card]:
        """
        Deal cards for the current street.
        
        Returns:
            List of cards dealt
        """
        if self._current_street == Street.COMPLETE:
            raise ValueError("Game already complete")
        
        if self._current_hand:
            raise ValueError("Current hand not yet resolved")
        
        # Determine number of cards to deal
        if self._current_street == Street.INITIAL:
            num_cards = 5
        else:
            num_cards = 3
        
        # Get available cards
        available = self.remaining_cards.to_list()
        if len(available) < num_cards * self.num_players:
            raise ValueError("Not enough cards remaining")
        
        # Shuffle and deal
        self._rng.shuffle(available)
        
        # Deal to all players
        all_dealt = []
        for i in range(self.num_players):
            player_cards = available[i*num_cards:(i+1)*num_cards]
            all_dealt.extend(player_cards)
            
            if i == self.player_index:
                self._current_hand = player_cards
            else:
                # Mark opponent cards as used
                for card in player_cards:
                    self._opponent_used_cards.add(card)
        
        return self._current_hand
    
    def get_valid_placements(self) -> List[Tuple[str, int]]:
        """
        Get all valid placement positions.
        
        Returns:
            List of (position, index) tuples
        """
        positions = []
        
        # Check front positions
        for i, card in enumerate(self._player_arrangement.front_cards):
            if card is None:
                positions.append(('front', i))
        
        # Check middle positions
        for i, card in enumerate(self._player_arrangement.middle_cards):
            if card is None:
                positions.append(('middle', i))
        
        # Check back positions
        for i, card in enumerate(self._player_arrangement.back_cards):
            if card is None:
                positions.append(('back', i))
        
        return positions
    
    def place_cards(self, 
                    placements: List[Tuple[Card, str, int]], 
                    discard: Optional[Card] = None) -> None:
        """
        Place cards and advance to next street.
        
        Args:
            placements: List of (card, position, index) tuples
            discard: Card to discard (for streets 1-4)
        """
        # Validate street requirements
        if self._current_street == Street.INITIAL:
            if len(placements) != 5 or discard is not None:
                raise ValueError("Initial street requires placing all 5 cards")
        else:
            if len(placements) != 2 or discard is None:
                raise ValueError("Streets 1-4 require placing 2 cards and discarding 1")
        
        # Validate cards are from current hand
        placed_cards = {p[0] for p in placements}
        if discard:
            placed_cards.add(discard)
        
        hand_set = set(self._current_hand)
        if placed_cards != hand_set:
            raise ValueError("Invalid cards - must use exactly the dealt cards")
        
        # Place cards
        for card, position, index in placements:
            self._player_arrangement.place_card(card, position, index)
        
        # Record action
        action = StreetAction(
            street=self._current_street,
            cards_dealt=self._current_hand.copy(),
            cards_placed=placements,
            card_discarded=discard
        )
        self._actions.append(action)
        
        # Clear current hand
        self._current_hand = []
        
        # Advance street
        if self._current_street == Street.FOURTH:
            self._current_street = Street.COMPLETE
        else:
            self._current_street = Street(self._current_street + 1)
    
    def simulate_opponent_actions(self, cards_used: List[Card]) -> None:
        """
        Simulate opponent using cards (for single-player optimization).
        
        Args:
            cards_used: Cards used by opponent this street
        """
        for card in cards_used:
            if card not in self.remaining_cards:
                raise ValueError(f"Card {card} not available")
            self._opponent_used_cards.add(card)
    
    def undo_last_action(self) -> Optional[StreetAction]:
        """
        Undo the last action and return to previous state.
        
        Returns:
            The undone action, or None if no actions to undo
        """
        if not self._actions:
            return None
        
        action = self._actions.pop()
        
        # Remove placed cards
        for card, position, index in action.cards_placed:
            self._player_arrangement.remove_card(position, index)
        
        # Restore current hand
        self._current_hand = action.cards_dealt
        
        # Revert street
        self._current_street = action.street
        
        return action
    
    def copy(self) -> "GameState":
        """Create a deep copy of the game state."""
        # This is a simplified copy - full implementation would deep copy all state
        new_state = GameState(
            num_players=self.num_players,
            player_index=self.player_index,
            num_jokers=self.num_jokers
        )
        
        # Copy arrangement
        for pos in ['front', 'middle', 'back']:
            if pos == 'front':
                cards = self._player_arrangement.front_cards
            elif pos == 'middle':
                cards = self._player_arrangement.middle_cards
            else:
                cards = self._player_arrangement.back_cards
            
            for i, card in enumerate(cards):
                if card is not None:
                    new_state._player_arrangement.place_card(card, pos, i)
        
        # Copy other state
        new_state._current_street = self._current_street
        new_state._opponent_used_cards = self._opponent_used_cards.copy()
        new_state._current_hand = self._current_hand.copy()
        new_state._actions = self._actions.copy()
        
        return new_state
    
    def __str__(self) -> str:
        """String representation of game state."""
        lines = [
            f"=== OFC Game State ===",
            f"Street: {self._current_street.name}",
            f"Cards placed: {self._player_arrangement.cards_placed}/13",
            f"Current hand: {' '.join(str(c) for c in self._current_hand)}",
            f"\nArrangement:",
            str(self._player_arrangement)
        ]
        
        if self._player_arrangement.is_complete:
            is_valid, error = self._player_arrangement.is_valid()
            if is_valid:
                royalties = self._player_arrangement.calculate_royalties()
                lines.append(f"\nRoyalties: Front={royalties.front}, "
                           f"Middle={royalties.middle}, Back={royalties.back} "
                           f"(Total={royalties.total})")
                
                if self._player_arrangement.qualifies_for_fantasyland():
                    lines.append("Qualifies for FANTASYLAND!")
            else:
                lines.append(f"\nFOUL: {error}")
        
        return "\n".join(lines)