"""
MCTS Node implementation for OFC Solver.

This module implements the tree node structure for Monte Carlo Tree Search.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass, field
import math
import numpy as np
from itertools import combinations
from collections import Counter

from src.core.domain.game_state import GameState, Street
from src.core.domain.card import Card, Rank
from src.core.domain.hand import Hand
from src.core.domain.hand_type import HandCategory


@dataclass
class Action:
    """Represents an action in OFC."""
    placements: List[Tuple[Card, str, int]]  # (card, position, index)
    discard: Optional[Card] = None
    
    def __hash__(self):
        """Hash for using actions as dict keys."""
        placement_tuple = tuple((c.value, p, i) for c, p, i in self.placements)
        discard_value = self.discard.value if self.discard else -1
        return hash((placement_tuple, discard_value))
    
    def __eq__(self, other):
        """Equality comparison."""
        if not isinstance(other, Action):
            return False
        return (self.placements == other.placements and 
                self.discard == other.discard)


class MCTSNode:
    """
    Node in the MCTS search tree.
    
    Each node represents a game state and tracks visit counts,
    total rewards, and child nodes for each possible action.
    """
    
    __slots__ = (
        'state', 'parent', 'action', 'children', 
        'visit_count', 'total_reward', 'untried_actions',
        'is_terminal', '_ucb_values_cache'
    )
    
    def __init__(self, 
                 state: GameState,
                 parent: Optional[MCTSNode] = None,
                 action: Optional[Action] = None):
        """
        Initialize MCTS node.
        
        Args:
            state: The game state at this node
            parent: Parent node in the tree
            action: Action that led to this state
        """
        self.state = state
        self.parent = parent
        self.action = action
        
        # Statistics
        self.visit_count = 0
        self.total_reward = 0.0
        
        # Children
        self.children: Dict[Action, MCTSNode] = {}
        self.untried_actions: Optional[List[Action]] = None
        
        # Terminal flag
        self.is_terminal = state.is_complete
        
        # Cache for UCB values
        self._ucb_values_cache: Optional[Dict[Action, float]] = None
    
    @property
    def is_fully_expanded(self) -> bool:
        """Check if all actions have been tried."""
        if self.is_terminal:
            return True
        if self.untried_actions is None:
            return False
        return len(self.untried_actions) == 0
    
    @property
    def average_reward(self) -> float:
        """Get average reward for this node."""
        if self.visit_count == 0:
            return 0.0
        return self.total_reward / self.visit_count
    
    def get_untried_actions(self) -> List[Action]:
        """
        Get list of untried actions from this state.
        
        Lazily generates actions on first call.
        """
        if self.untried_actions is None:
            self.untried_actions = self._generate_actions()
        return self.untried_actions
    
    def _generate_actions(self) -> List[Action]:
        """Generate all possible actions from current state."""
        if self.state.is_complete:
            return []
        
        actions = []
        current_hand = self.state.current_hand
        
        if not current_hand:
            # No cards in hand - need to deal
            return []
        
        if self.state.current_street == Street.INITIAL:
            # Initial street - must place all 5 cards
            actions.extend(self._generate_initial_actions(current_hand))
        else:
            # Regular street - place 2, discard 1
            actions.extend(self._generate_regular_actions(current_hand))
        
        return actions
    
    def _generate_initial_actions(self, cards: List[Card]) -> List[Action]:
        """
        Generate actions for initial street (place all 5 cards).
        
        Uses intelligent strategies based on hand strength analysis.
        """
        # Get available positions
        positions = self.state.get_valid_placements()
        
        if len(positions) < 5:
            return []  # Not enough positions
        
        # Group positions by row
        front_positions = [(pos, idx) for pos, idx in positions if pos == 'front']
        middle_positions = [(pos, idx) for pos, idx in positions if pos == 'middle']
        back_positions = [(pos, idx) for pos, idx in positions if pos == 'back']
        
        actions = []
        
        # Analyze card strength
        sorted_cards = sorted(cards, key=lambda c: c.rank_value, reverse=True)
        
        # Count pairs and suits
        rank_counts = Counter(card.rank_value for card in cards if not card.is_joker)
        suit_counts = Counter(card.suit_value for card in cards if not card.is_joker)
        joker_count = sum(1 for card in cards if card.is_joker)
        
        # Identify pairs
        pairs = [(rank, count) for rank, count in rank_counts.items() if count >= 2]
        pairs.sort(key=lambda x: x[0], reverse=True)  # Sort by rank
        
        # Strategy 1: If we have a pair, consider placements that utilize it
        if pairs:
            highest_pair_rank = pairs[0][0]
            pair_cards = [c for c in cards if c.rank_value == highest_pair_rank][:2]
            other_cards = [c for c in cards if c not in pair_cards]
            
            # Option 1: Pair in back (strong position)
            if len(back_positions) >= 2 and len(middle_positions) >= 2 and len(front_positions) >= 1:
                action = self._create_placement_action(
                    pair_cards, back_positions[:2],
                    other_cards[:2], middle_positions[:2],
                    other_cards[2:3], front_positions[:1]
                )
                actions.append(action)
            
            # Option 2: Pair in middle (balanced)
            if len(middle_positions) >= 2 and len(back_positions) >= 2 and len(front_positions) >= 1:
                # Put two highest non-pair cards in back
                sorted_others = sorted(other_cards, key=lambda c: c.rank_value, reverse=True)
                action = self._create_placement_action(
                    sorted_others[:2], back_positions[:2],
                    pair_cards, middle_positions[:2],
                    sorted_others[2:3], front_positions[:1]
                )
                actions.append(action)
            
            # Option 3: Pair in front (aggressive, for high pairs)
            if highest_pair_rank >= Rank.JACK.value and len(front_positions) >= 2:
                if len(back_positions) >= 2 and len(middle_positions) >= 1:
                    sorted_others = sorted(other_cards, key=lambda c: c.rank_value, reverse=True)
                    action = self._create_placement_action(
                        sorted_others[:2], back_positions[:2],
                        sorted_others[2:3], middle_positions[:1],
                        pair_cards, front_positions[:2]
                    )
                    actions.append(action)
        
        # Strategy 2: Flush draw potential
        flush_potential = max(suit_counts.values()) if suit_counts else 0
        if flush_potential + joker_count >= 3:
            # Group cards by suit
            flush_suit = max(suit_counts.items(), key=lambda x: x[1])[0]
            flush_cards = [c for c in cards if not c.is_joker and c.suit_value == flush_suit]
            jokers = [c for c in cards if c.is_joker]
            other_cards = [c for c in cards if c not in flush_cards and c not in jokers]
            
            # Place flush cards together in back or middle
            if len(flush_cards) + len(jokers) >= 3:
                if len(back_positions) >= 3 and len(middle_positions) >= 1 and len(front_positions) >= 1:
                    flush_group = (flush_cards + jokers)[:3]
                    remaining = other_cards + (flush_cards + jokers)[3:]
                    action = self._create_placement_action(
                        flush_group, back_positions[:3],
                        remaining[:1], middle_positions[:1],
                        remaining[1:2], front_positions[:1]
                    )
                    actions.append(action)
        
        # Strategy 3: Straight potential
        straight_potential = self._check_straight_potential(cards)
        if straight_potential:
            # Place connected cards together
            connected_cards = self._get_connected_cards(cards)
            if len(connected_cards) >= 3:
                other_cards = [c for c in cards if c not in connected_cards]
                if len(back_positions) >= 3 and len(middle_positions) >= 1 and len(front_positions) >= 1:
                    action = self._create_placement_action(
                        connected_cards[:3], back_positions[:3],
                        other_cards[:1], middle_positions[:1],
                        other_cards[1:2], front_positions[:1]
                    )
                    actions.append(action)
        
        # Strategy 4: Balanced distribution based on card strength
        # This is the most common approach
        if len(front_positions) >= 2 and len(middle_positions) >= 2 and len(back_positions) >= 1:
            # Standard 2-2-1 distribution
            action = self._create_placement_action(
                sorted_cards[3:5], front_positions[:2],  # Lowest 2 in front
                sorted_cards[1:3], middle_positions[:2],  # Middle 2 in middle
                sorted_cards[0:1], back_positions[:1]     # Highest in back
            )
            actions.append(action)
        
        if len(front_positions) >= 2 and len(middle_positions) >= 1 and len(back_positions) >= 2:
            # Alternative 2-1-2 distribution
            action = self._create_placement_action(
                sorted_cards[3:5], front_positions[:2],  # Lowest 2 in front
                sorted_cards[2:3], middle_positions[:1],  # Middle 1 in middle
                sorted_cards[0:2], back_positions[:2]     # Highest 2 in back
            )
            actions.append(action)
        
        if len(front_positions) >= 1 and len(middle_positions) >= 2 and len(back_positions) >= 2:
            # Alternative 1-2-2 distribution
            action = self._create_placement_action(
                sorted_cards[4:5], front_positions[:1],  # Lowest 1 in front
                sorted_cards[2:4], middle_positions[:2],  # Middle 2 in middle
                sorted_cards[0:2], back_positions[:2]     # Highest 2 in back
            )
            actions.append(action)
        
        # If no specific strategies worked, fall back to simple placement
        if not actions and len(positions) >= 5:
            placements = []
            for i in range(5):
                if i < len(positions) and i < len(cards):
                    placements.append((cards[i], positions[i][0], positions[i][1]))
            if len(placements) == 5:
                actions.append(Action(placements))
        
        return actions
    
    def _create_placement_action(self, 
                                cards1: List[Card], positions1: List[Tuple[str, int]],
                                cards2: List[Card], positions2: List[Tuple[str, int]],
                                cards3: List[Card], positions3: List[Tuple[str, int]]) -> Action:
        """Helper to create a placement action from card groups."""
        placements = []
        
        for card, (pos, idx) in zip(cards1, positions1):
            placements.append((card, pos, idx))
        
        for card, (pos, idx) in zip(cards2, positions2):
            placements.append((card, pos, idx))
        
        for card, (pos, idx) in zip(cards3, positions3):
            placements.append((card, pos, idx))
        
        return Action(placements)
    
    def _check_straight_potential(self, cards: List[Card]) -> bool:
        """Check if cards have straight potential."""
        ranks = sorted([c.rank_value for c in cards if not c.is_joker])
        joker_count = sum(1 for c in cards if c.is_joker)
        
        if not ranks:
            return True  # All jokers can make a straight
        
        # Check for gaps that could be filled
        min_rank = min(ranks)
        max_rank = max(ranks)
        
        # If range is too wide, no straight possible
        if max_rank - min_rank > 4:
            # Check for ace-low straight
            if Rank.ACE.value in ranks and any(r <= 3 for r in ranks):
                return True
            return False
        
        # Count gaps
        gaps = 0
        for r in range(min_rank, max_rank):
            if r not in ranks:
                gaps += 1
        
        return gaps <= joker_count
    
    def _get_connected_cards(self, cards: List[Card]) -> List[Card]:
        """Get cards that are connected (for straight potential)."""
        sorted_cards = sorted(cards, key=lambda c: c.rank_value)
        connected = [sorted_cards[0]]
        
        for i in range(1, len(sorted_cards)):
            if sorted_cards[i].rank_value - sorted_cards[i-1].rank_value <= 2:
                connected.append(sorted_cards[i])
            else:
                # Start new group if better
                if len(connected) < i:
                    connected = [sorted_cards[i]]
        
        return connected
    
    def _generate_regular_actions(self, cards: List[Card]) -> List[Action]:
        """
        Generate actions for regular streets (place 2, discard 1).
        
        This generates all combinations of placing 2 cards and discarding 1.
        """
        if len(cards) != 3:
            return []
        
        positions = self.state.get_valid_placements()
        if len(positions) < 2:
            return []  # Not enough positions
        
        actions = []
        
        # For each card to discard
        for discard_idx in range(3):
            discard_card = cards[discard_idx]
            place_cards = [cards[i] for i in range(3) if i != discard_idx]
            
            # For each way to place the 2 cards
            # Try different position combinations
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    # Place first card in position i, second in position j
                    action1 = Action([
                        (place_cards[0], positions[i][0], positions[i][1]),
                        (place_cards[1], positions[j][0], positions[j][1]),
                    ], discard=discard_card)
                    actions.append(action1)
                    
                    # Also try swapping the cards
                    action2 = Action([
                        (place_cards[1], positions[i][0], positions[i][1]),
                        (place_cards[0], positions[j][0], positions[j][1]),
                    ], discard=discard_card)
                    actions.append(action2)
        
        return actions
    
    def select_child(self, c_puct: float = 1.4) -> MCTSNode:
        """
        Select best child using UCB formula.
        
        Args:
            c_puct: Exploration constant
            
        Returns:
            Best child node according to UCB
        """
        if not self.children:
            raise ValueError("No children to select from")
        
        # Clear cache when selecting (visit counts may have changed)
        self._ucb_values_cache = None
        
        best_value = -float('inf')
        best_child = None
        
        parent_visit_sqrt = math.sqrt(self.visit_count)
        
        for action, child in self.children.items():
            if child.visit_count == 0:
                ucb_value = float('inf')  # Prioritize unvisited nodes
            else:
                exploitation = child.average_reward
                exploration = c_puct * parent_visit_sqrt / (1 + child.visit_count)
                ucb_value = exploitation + exploration
            
            if ucb_value > best_value:
                best_value = ucb_value
                best_child = child
        
        return best_child
    
    def expand(self) -> MCTSNode:
        """
        Expand the node by trying an untried action.
        
        Returns:
            The newly created child node
        """
        if self.is_terminal:
            raise ValueError("Cannot expand terminal node")
        
        untried = self.get_untried_actions()
        if not untried:
            raise ValueError("No untried actions to expand")
        
        # Select a random untried action
        # Could use domain knowledge here to prioritize certain actions
        action = untried.pop()
        
        # Create new state by applying action
        new_state = self.state.copy()
        new_state.place_cards(action.placements, action.discard)
        
        # Create child node
        child = MCTSNode(new_state, parent=self, action=action)
        self.children[action] = child
        
        return child
    
    def update(self, reward: float) -> None:
        """
        Update node statistics with backpropagation.
        
        Args:
            reward: Reward to backpropagate
        """
        self.visit_count += 1
        self.total_reward += reward
        
        # Backpropagate to parent
        if self.parent is not None:
            self.parent.update(reward)
    
    def get_best_action(self) -> Optional[Action]:
        """
        Get the best action based on visit counts.
        
        Returns:
            Action with highest visit count
        """
        if not self.children:
            return None
        
        best_action = None
        best_visits = -1
        
        for action, child in self.children.items():
            if child.visit_count > best_visits:
                best_visits = child.visit_count
                best_action = action
        
        return best_action
    
    def get_action_statistics(self) -> List[Tuple[Action, int, float]]:
        """
        Get statistics for all actions.
        
        Returns:
            List of (action, visit_count, average_reward) tuples
        """
        stats = []
        for action, child in self.children.items():
            stats.append((action, child.visit_count, child.average_reward))
        
        # Sort by visit count
        stats.sort(key=lambda x: x[1], reverse=True)
        return stats
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return len(self.children) == 0
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"MCTSNode(visits={self.visit_count}, "
                f"reward={self.average_reward:.3f}, "
                f"children={len(self.children)}, "
                f"terminal={self.is_terminal})")