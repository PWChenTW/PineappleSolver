"""
MCTS Node implementation for OFC Solver.

This module implements the tree node structure for Monte Carlo Tree Search.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple, Set
from dataclasses import dataclass, field
import math
import numpy as np

from src.core.domain.game_state import GameState, Street
from src.core.domain.card import Card


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
        
        For now, using a simplified approach - can be optimized later.
        """
        # Get available positions
        positions = self.state.get_valid_placements()
        
        if len(positions) < 5:
            return []  # Not enough positions
        
        # For initial implementation, try a few reasonable distributions
        # This is where domain knowledge helps reduce the search space
        actions = []
        
        # Common patterns for initial placement:
        # 1. 2 front, 2 middle, 1 back
        # 2. 2 front, 1 middle, 2 back
        # 3. 1 front, 2 middle, 2 back
        
        # For now, just generate one simple action
        # TODO: Implement smarter initial placement generation
        if len(positions) >= 5:
            action = Action([
                (cards[0], positions[0][0], positions[0][1]),
                (cards[1], positions[1][0], positions[1][1]),
                (cards[2], positions[2][0], positions[2][1]),
                (cards[3], positions[3][0], positions[3][1]),
                (cards[4], positions[4][0], positions[4][1]),
            ])
            actions.append(action)
        
        return actions
    
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