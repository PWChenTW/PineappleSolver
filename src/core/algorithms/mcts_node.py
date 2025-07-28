"""
MCTS node implementation for OFC Solver.

This module implements the node structure for Monte Carlo Tree Search
optimized for Open Face Chinese Poker.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import math

from src.core.domain import GameState, Card, Street
from src.core.algorithms.evaluator import StateEvaluator


@dataclass(frozen=True)
class Action:
    """
    Represents an action in OFC.
    
    For initial street: place all 5 cards
    For other streets: place 2 cards, discard 1
    """
    placements: List[Tuple[Card, str, int]]  # (card, position, index)
    discard: Optional[Card] = None
    
    def __hash__(self):
        """Make action hashable for use as dict key."""
        placement_tuple = tuple((str(c), pos, idx) for c, pos, idx in self.placements)
        discard_str = str(self.discard) if self.discard else None
        return hash((placement_tuple, discard_str))
    
    def __repr__(self):
        """String representation for debugging."""
        placements_str = ", ".join(f"{c}→{pos}[{idx}]" for c, pos, idx in self.placements)
        if self.discard:
            return f"Action(place=[{placements_str}], discard={self.discard})"
        return f"Action(place=[{placements_str}])"


class MCTSNode:
    """
    Node in the MCTS tree.
    
    Represents a game state and tracks statistics for UCB selection.
    """
    
    def __init__(self, state: GameState, parent: Optional['MCTSNode'] = None, 
                 parent_action: Optional[Action] = None):
        """
        Initialize MCTS node.
        
        Args:
            state: Game state at this node
            parent: Parent node
            parent_action: Action that led to this state
        """
        self.state = state
        self.parent = parent
        self.parent_action = parent_action
        
        # Statistics
        self.visit_count = 0
        self.total_reward = 0.0
        
        # Children
        self.children: Dict[Action, MCTSNode] = {}
        self.untried_actions: Optional[List[Action]] = None
        
        # Cached evaluations
        self._is_terminal: Optional[bool] = None
        self._is_fully_expanded: Optional[bool] = None
    
    @property
    def average_reward(self) -> float:
        """Get average reward (win rate)."""
        if self.visit_count == 0:
            return 0.0
        return self.total_reward / self.visit_count
    
    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        if self._is_terminal is None:
            self._is_terminal = self.state.is_complete
        return self._is_terminal
    
    @property
    def is_fully_expanded(self) -> bool:
        """Check if all actions have been tried."""
        if self._is_fully_expanded is None:
            if self.untried_actions is None:
                self.untried_actions = self._get_legal_actions()
            self._is_fully_expanded = len(self.untried_actions) == 0
        return self._is_fully_expanded
    
    def get_untried_actions(self) -> List[Action]:
        """Get list of untried actions."""
        if self.untried_actions is None:
            self.untried_actions = self._get_legal_actions()
        return self.untried_actions
    
    def _get_legal_actions(self) -> List[Action]:
        """
        Generate all legal actions from current state.
        
        Returns:
            List of legal actions
        """
        if self.is_terminal:
            return []
        
        # Get current hand
        current_hand = self.state.current_hand
        if not current_hand:
            return []
        
        # Get valid placement positions
        positions = self.state.get_valid_placements()
        if not positions:
            return []
        
        actions = []
        
        if self.state.current_street == Street.INITIAL:
            # Initial placement - need to place all 5 cards
            actions.extend(self._generate_initial_placements(current_hand, positions))
        else:
            # Regular street - place 2, discard 1
            actions.extend(self._generate_regular_placements(current_hand, positions))
        
        return actions
    
    def _generate_initial_placements(self, cards: List[Card], 
                                   positions: List[Tuple[str, int]]) -> List[Action]:
        """
        Generate initial placement actions with strategic templates.
        
        Uses heuristics to limit the number of actions to evaluate.
        """
        if len(cards) != 5 or len(positions) < 5:
            return []
        
        actions = []
        
        # Sort cards by strength for easier strategy implementation
        sorted_cards = sorted(cards, key=lambda c: c.rank_value, reverse=True)
        
        # Get position groups
        front_positions = [(pos, idx) for pos, idx in positions if pos == 'front']
        middle_positions = [(pos, idx) for pos, idx in positions if pos == 'middle']
        back_positions = [(pos, idx) for pos, idx in positions if pos == 'back']
        
        # Strategy 1: Pair/trips priority placement
        rank_counts = {}
        for card in cards:
            rank = card.rank_value
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        pairs = [(rank, cards) for rank, count in rank_counts.items() if count >= 2]
        if pairs:
            # Place pair in back, distribute rest
            pair_rank = pairs[0][0]
            pair_cards = [c for c in cards if c.rank_value == pair_rank][:2]
            other_cards = [c for c in cards if c not in pair_cards]
            
            if len(back_positions) >= 2 and len(middle_positions) >= 2 and len(front_positions) >= 1:
                action = self._create_placement_action(
                    pair_cards, back_positions[:2],
                    other_cards[:2], middle_positions[:2],
                    other_cards[2:3], front_positions[:1]
                )
                actions.append(action)
        
        # Consider suited cards
        suit_counts = {}
        joker_count = 0
        for card in cards:
            if card.is_joker:
                joker_count += 1
            else:
                suit = card.suit_value
                suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
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
                sorted_cards[4:5], front_positions[:1],  # Lowest in front
                sorted_cards[2:4], middle_positions[:2],  # Middle 2 in middle
                sorted_cards[0:2], back_positions[:2]     # Highest 2 in back
            )
            actions.append(action)
        
        # Ensure we have at least one action (fallback to arbitrary valid placement)
        if not actions and len(positions) >= 5:
            placements = []
            for i, card in enumerate(cards):
                if i < len(positions):
                    pos, idx = positions[i]
                    placements.append((card, pos, idx))
            if len(placements) == 5:
                actions.append(Action(placements))
        
        # Remove duplicate actions
        unique_actions = []
        seen = set()
        for action in actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        return unique_actions
    
    def _create_placement_action(self, cards1: List[Card], positions1: List[Tuple[str, int]],
                                cards2: List[Card], positions2: List[Tuple[str, int]],
                                cards3: List[Card], positions3: List[Tuple[str, int]]) -> Action:
        """Helper to create placement action from card groups."""
        placements = []
        
        for cards, positions in [(cards1, positions1), (cards2, positions2), (cards3, positions3)]:
            for i, card in enumerate(cards):
                if i < len(positions):
                    pos, idx = positions[i]
                    placements.append((card, pos, idx))
        
        return Action(placements)
    
    def _check_straight_potential(self, cards: List[Card]) -> bool:
        """Check if cards have straight potential."""
        ranks = sorted([c.rank_value for c in cards if not c.is_joker])
        joker_count = sum(1 for c in cards if c.is_joker)
        
        if len(ranks) + joker_count < 3:
            return False
        
        # Check for connected cards
        for i in range(len(ranks) - 1):
            gap = ranks[i+1] - ranks[i]
            if gap > joker_count + 1:
                return False
        
        return True
    
    def _get_connected_cards(self, cards: List[Card]) -> List[Card]:
        """Get cards that could form a straight."""
        sorted_cards = sorted([c for c in cards if not c.is_joker], 
                            key=lambda c: c.rank_value)
        jokers = [c for c in cards if c.is_joker]
        
        if len(sorted_cards) < 2:
            return sorted_cards + jokers
        
        # Find the longest connected sequence
        connected = [sorted_cards[0]]
        available_jokers = len(jokers)
        
        for i in range(1, len(sorted_cards)):
            gap = sorted_cards[i].rank_value - sorted_cards[i-1].rank_value - 1
            if gap <= available_jokers:
                connected.append(sorted_cards[i])
                available_jokers -= gap
            else:
                # Start new sequence if current is shorter
                if len(connected) + len(jokers) < 3:
                    connected = [sorted_cards[i]]
                    available_jokers = len(jokers)
        
        # Add jokers to the connected cards
        return connected + jokers[:available_jokers]
    
    def _generate_regular_placements(self, cards: List[Card], 
                                    positions: List[Tuple[str, int]]) -> List[Action]:
        """
        Generate placement actions for regular streets.
        
        Place 2 cards and discard 1.
        """
        if len(cards) != 3 or len(positions) < 2:
            return []
        
        actions = []
        
        # Generate all combinations of 2 cards to place
        from itertools import combinations
        for cards_to_place in combinations(cards, 2):
            discard = [c for c in cards if c not in cards_to_place][0]
            
            # Generate different position combinations
            for pos_combo in combinations(positions, 2):
                # Try both orderings
                placements1 = [
                    (cards_to_place[0], pos_combo[0][0], pos_combo[0][1]),
                    (cards_to_place[1], pos_combo[1][0], pos_combo[1][1])
                ]
                actions.append(Action(placements1, discard))
                
                # Only add reverse if positions are different
                if pos_combo[0] != pos_combo[1]:
                    placements2 = [
                        (cards_to_place[0], pos_combo[1][0], pos_combo[1][1]),
                        (cards_to_place[1], pos_combo[0][0], pos_combo[0][1])
                    ]
                    actions.append(Action(placements2, discard))
        
        # Remove duplicates
        unique_actions = []
        seen = set()
        for action in actions:
            if action not in seen:
                seen.add(action)
                unique_actions.append(action)
        
        # Limit number of actions for performance (can be tuned)
        max_actions = 50  # Reasonable limit for regular streets
        if len(unique_actions) > max_actions:
            # Prioritize actions based on heuristics
            # For now, just take first N actions
            unique_actions = unique_actions[:max_actions]
        
        return unique_actions
    
    def select_child(self, c_puct: float) -> 'MCTSNode':
        """
        Select child using UCB1 formula.
        
        Args:
            c_puct: Exploration constant
            
        Returns:
            Selected child node
        """
        best_score = -float('inf')
        best_child = None
        
        for child in self.children.values():
            # UCB1 formula
            exploitation = child.average_reward
            exploration = c_puct * math.sqrt(math.log(self.visit_count) / child.visit_count)
            score = exploitation + exploration
            
            if score > best_score:
                best_score = score
                best_child = child
        
        return best_child
    
    def expand(self) -> 'MCTSNode':
        """
        Expand node by adding a new child.
        
        Returns:
            Newly created child node
        """
        if not self.untried_actions:
            raise ValueError("No untried actions to expand")
        
        # Take first untried action
        action = self.untried_actions.pop(0)
        
        # Create new state by applying action
        new_state = self.state.copy()
        new_state.place_cards(action.placements, action.discard)
        
        # Create child node
        child = MCTSNode(new_state, parent=self, parent_action=action)
        self.children[action] = child
        
        return child
    
    def update(self, reward: float) -> None:
        """
        Update node statistics with backpropagation.
        
        Args:
            reward: Reward from simulation
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
    
    def get_action_win_rate(self, action: Action) -> float:
        """
        Get win rate for a specific action.
        
        Args:
            action: Action to get win rate for
            
        Returns:
            Win rate (average reward) for the action
        """
        if action in self.children:
            return self.children[action].average_reward
        return 0.0
    
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