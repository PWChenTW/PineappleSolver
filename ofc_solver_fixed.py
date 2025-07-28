#!/usr/bin/env python3
"""
Fixed OFC Poker Solver with MCTS
Corrects the PlayerArrangement attribute naming issue.
"""

import random
import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from itertools import combinations


# Card representation
RANKS = '23456789TJQKA'
SUITS = 'cdhs'
RANK_VALUES = {r: i for i, r in enumerate(RANKS, 2)}


@dataclass
class Card:
    """Represents a playing card."""
    rank: str
    suit: str
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __lt__(self, other):
        return RANK_VALUES[self.rank] < RANK_VALUES[other.rank]
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """Create a Card from string like 'As' or 'Td'."""
        return cls(rank=card_str[0], suit=card_str[1])


@dataclass
class Hand:
    """Represents a poker hand (front, middle, or back)."""
    cards: List[Card] = field(default_factory=list)
    max_size: int = 5
    
    def is_full(self) -> bool:
        return len(self.cards) >= self.max_size
    
    def add_card(self, card: Card) -> bool:
        """Add a card if hand is not full."""
        if not self.is_full():
            self.cards.append(card)
            return True
        return False
    
    def get_rank_counts(self) -> Dict[str, int]:
        """Get count of each rank in hand."""
        counts = defaultdict(int)
        for card in self.cards:
            counts[card.rank] += 1
        return dict(counts)
    
    def get_suit_counts(self) -> Dict[str, int]:
        """Get count of each suit in hand."""
        counts = defaultdict(int)
        for card in self.cards:
            counts[card.suit] += 1
        return dict(counts)
    
    def evaluate(self) -> Tuple[int, List[int]]:
        """Evaluate the poker hand and return (hand_type, tiebreakers)."""
        if not self.cards:
            return (0, [])
        
        sorted_cards = sorted(self.cards, reverse=True)
        ranks = [card.rank for card in sorted_cards]
        suits = [card.suit for card in sorted_cards]
        rank_counts = self.get_rank_counts()
        suit_counts = self.get_suit_counts()
        
        # Check for flush
        is_flush = any(count >= 5 for count in suit_counts.values())
        
        # Check for straight
        is_straight = False
        straight_high = 0
        
        if len(self.cards) >= 5:
            # Convert to rank values for checking
            rank_values = sorted([RANK_VALUES[card.rank] for card in self.cards], reverse=True)
            
            # Check for regular straight
            for i in range(len(rank_values) - 4):
                if rank_values[i] - rank_values[i+4] == 4:
                    is_straight = True
                    straight_high = rank_values[i]
                    break
            
            # Check for A-5 straight
            if set([14, 2, 3, 4, 5]).issubset(set(rank_values)):
                is_straight = True
                straight_high = 5
        
        # Get counts for different ranks
        count_values = sorted(rank_counts.values(), reverse=True)
        rank_by_count = sorted(rank_counts.items(), key=lambda x: (-x[1], -RANK_VALUES[x[0]]))
        
        # Determine hand type
        if is_straight and is_flush:
            return (8, [straight_high])  # Straight flush
        elif count_values[:1] == [4]:
            return (7, [RANK_VALUES[rank_by_count[0][0]]])  # Four of a kind
        elif count_values[:2] == [3, 2]:
            return (6, [RANK_VALUES[rank_by_count[0][0]], RANK_VALUES[rank_by_count[1][0]]])  # Full house
        elif is_flush:
            return (5, [RANK_VALUES[card.rank] for card in sorted_cards])  # Flush
        elif is_straight:
            return (4, [straight_high])  # Straight
        elif count_values[:1] == [3]:
            return (3, [RANK_VALUES[rank_by_count[0][0]]])  # Three of a kind
        elif count_values[:2] == [2, 2]:
            return (2, [RANK_VALUES[rank_by_count[0][0]], RANK_VALUES[rank_by_count[1][0]]])  # Two pair
        elif count_values[:1] == [2]:
            return (1, [RANK_VALUES[rank_by_count[0][0]]])  # One pair
        else:
            return (0, [RANK_VALUES[card.rank] for card in sorted_cards])  # High card
    
    def __str__(self):
        return ' '.join(str(card) for card in self.cards)


@dataclass
class PlayerArrangement:
    """Represents a player's complete OFC arrangement."""
    front_hand: Hand = field(default_factory=lambda: Hand(max_size=3))  # Note: front_hand, not front
    middle_hand: Hand = field(default_factory=lambda: Hand(max_size=5))  # Note: middle_hand, not middle
    back_hand: Hand = field(default_factory=lambda: Hand(max_size=5))    # Note: back_hand, not back
    
    def add_card_to_hand(self, card: Card, hand_position: str) -> bool:
        """Add a card to specified hand."""
        hand_map = {
            'front': self.front_hand,
            'middle': self.middle_hand,
            'back': self.back_hand
        }
        hand = hand_map.get(hand_position)
        if hand and not hand.is_full():
            return hand.add_card(card)
        return False
    
    def is_valid(self) -> bool:
        """Check if arrangement follows OFC rules (back >= middle >= front)."""
        if not self.all_hands_full():
            return True  # Incomplete arrangements are considered valid
        
        front_rank, _ = self.front_hand.evaluate()
        middle_rank, _ = self.middle_hand.evaluate()
        back_rank, _ = self.back_hand.evaluate()
        
        # Special case: if ranks are equal, need to check high cards
        if back_rank < middle_rank or middle_rank < front_rank:
            return False
        
        return True
    
    def all_hands_full(self) -> bool:
        """Check if all hands are full."""
        return (self.front_hand.is_full() and 
                self.middle_hand.is_full() and 
                self.back_hand.is_full())
    
    def get_available_positions(self) -> List[str]:
        """Get list of positions that can accept more cards."""
        positions = []
        if not self.front_hand.is_full():
            positions.append('front')
        if not self.middle_hand.is_full():
            positions.append('middle')
        if not self.back_hand.is_full():
            positions.append('back')
        return positions
    
    def copy(self) -> 'PlayerArrangement':
        """Create a deep copy of the arrangement."""
        new_arrangement = PlayerArrangement()
        new_arrangement.front_hand.cards = self.front_hand.cards.copy()
        new_arrangement.middle_hand.cards = self.middle_hand.cards.copy()
        new_arrangement.back_hand.cards = self.back_hand.cards.copy()
        return new_arrangement
    
    def __str__(self):
        return f"Front: {self.front_hand}\nMiddle: {self.middle_hand}\nBack: {self.back_hand}"


class MCTSNode:
    """Node in the MCTS tree."""
    
    def __init__(self, state: PlayerArrangement, parent=None, action=None, 
                 remaining_cards=None):
        self.state = state
        self.parent = parent
        self.action = action  # (card, position)
        self.remaining_cards = remaining_cards or []
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.untried_actions = None
        self._setup_untried_actions()
    
    def _setup_untried_actions(self):
        """Initialize untried actions for this node."""
        if self.state.all_hands_full() or not self.remaining_cards:
            self.untried_actions = []
            return
        
        self.untried_actions = []
        available_positions = self.state.get_available_positions()
        
        # Always try placing any of the remaining cards in any available position
        for card in self.remaining_cards:
            for position in available_positions:
                self.untried_actions.append((card, position))
    
    def select_child(self, c=1.4):
        """Select child using UCB1 formula."""
        if not self.children:
            return None
        
        # If parent has no visits, select randomly
        if self.visits == 0:
            return random.choice(self.children)
        
        # UCB1 formula with protection against division by zero
        def ucb_score(node):
            if node.visits == 0:
                return float('inf')
            exploitation = node.wins / node.visits
            exploration = c * math.sqrt(2 * math.log(self.visits) / node.visits)
            return exploitation + exploration
        
        return max(self.children, key=ucb_score)
    
    def add_child(self, action):
        """Add a child node for the given action."""
        card, position = action
        new_state = self.state.copy()
        new_state.add_card_to_hand(card, position)
        
        # Remove used card from remaining cards
        new_remaining = [c for c in self.remaining_cards if c != card]
        
        child = MCTSNode(new_state, parent=self, action=action, 
                        remaining_cards=new_remaining)
        self.children.append(child)
        return child
    
    def update(self, result):
        """Update node statistics."""
        self.visits += 1
        self.wins += result


class OFCMCTSSolver:
    """MCTS solver for Open Face Chinese Poker."""
    
    def __init__(self, num_simulations=1000, num_processes=None):
        self.num_simulations = num_simulations
        self.num_processes = num_processes or mp.cpu_count()
    
    def solve_initial_five(self, cards: List[Card]) -> PlayerArrangement:
        """Find optimal placement for initial 5 cards."""
        print(f"\nSolving initial 5 cards placement:")
        print(f"Cards: {' '.join(str(c) for c in cards)}")
        
        # For initial placement, we only consider the 5 cards given
        root = MCTSNode(PlayerArrangement(), remaining_cards=cards)
        
        print(f"\nRunning MCTS with {self.num_simulations} simulations...")
        
        self.debug_count = 0  # Initialize debug counter
        
        for i in range(self.num_simulations):
            self._run_simulation(root)
            
            if (i + 1) % 100 == 0:
                print(f"Progress: {i+1}/{self.num_simulations} simulations", end='\r')
        
        print(f"\nCompleted {self.num_simulations} simulations")
        
        # Debug: print tree stats
        total_nodes = self._count_nodes(root)
        complete_nodes = self._count_complete_nodes(root, len(cards))
        print(f"Tree stats: {total_nodes} total nodes, {complete_nodes} complete initial placements")
        
        # Find best initial placement
        best_arrangement = self._extract_best_initial_placement(root, cards)
        
        return best_arrangement
    
    def _run_simulation(self, node: MCTSNode) -> float:
        """Run a single MCTS simulation."""
        # Selection
        path = [node]
        
        # Traverse tree using UCB until we find unexpanded node
        while node.untried_actions == [] and node.children:
            node = node.select_child()
            if node is None:
                break
            path.append(node)
        
        # Expansion - add new child if there are untried actions
        if node and node.untried_actions:
            action = random.choice(node.untried_actions)
            node.untried_actions.remove(action)
            node = node.add_child(action)
            path.append(node)
            
            # Debug first few expansions
            if self.debug_count < 5:
                self.debug_count += 1
                total_placed = (len(node.state.front_hand.cards) + 
                               len(node.state.middle_hand.cards) + 
                               len(node.state.back_hand.cards))
                print(f"Debug: Expanded node {self.debug_count}, placed {total_placed} cards, {len(node.untried_actions)} untried actions remain")
        
        # Simulation - play out randomly from this node
        if node:
            result = self._simulate_random_playout(node)
        else:
            result = 0.0
        
        # Backpropagation - update all nodes in path
        for n in path:
            if n:
                n.update(result)
        
        return result
    
    def _simulate_random_playout(self, node: MCTSNode) -> float:
        """Simulate a random playout from the given node."""
        state = node.state.copy()
        remaining = node.remaining_cards.copy()
        
        # Complete the arrangement randomly
        while not state.all_hands_full() and remaining:
            card = remaining[0]
            remaining = remaining[1:]
            
            positions = state.get_available_positions()
            if positions:
                position = random.choice(positions)
                state.add_card_to_hand(card, position)
        
        # Evaluate the final arrangement
        if not state.is_valid():
            return 0.0
        
        # Simple scoring based on hand strengths
        score = 0.0
        front_rank, _ = state.front_hand.evaluate()
        middle_rank, _ = state.middle_hand.evaluate()
        back_rank, _ = state.back_hand.evaluate()
        
        # Award points for strong hands
        score += front_rank * 1  # Front hand worth less
        score += middle_rank * 2  # Middle hand worth more
        score += back_rank * 3    # Back hand worth most
        
        # Normalize to [0, 1]
        max_score = 8 * (1 + 2 + 3)  # Maximum possible score
        return score / max_score
    
    def _extract_best_initial_placement(self, root: MCTSNode, initial_cards: List[Card]) -> PlayerArrangement:
        """Extract the best placement from MCTS tree."""
        # Follow best path through tree
        best_arrangement = PlayerArrangement()
        current = root
        placed_count = 0
        
        while current.children and placed_count < len(initial_cards):
            # Get visited children
            visited_children = [c for c in current.children if c.visits > 0]
            if not visited_children:
                break
            
            # Select child with best win rate
            best_child = max(visited_children, key=lambda n: n.wins / n.visits)
            
            # Apply the action
            if best_child.action:
                card, position = best_child.action
                best_arrangement.add_card_to_hand(card, position)
                placed_count += 1
                
                if self.debug_count < 10:  # Show first few placements
                    print(f"MCTS chose: {card} → {position} (win rate: {best_child.wins/best_child.visits:.3f})")
            
            current = best_child
        
        # Check if we placed all cards
        total_placed = (len(best_arrangement.front_hand.cards) + 
                       len(best_arrangement.middle_hand.cards) + 
                       len(best_arrangement.back_hand.cards))
        
        if total_placed == len(initial_cards):
            print(f"\nMCTS found complete placement")
            return best_arrangement
        else:
            # Use heuristics for any remaining cards
            print(f"\nMCTS placed {total_placed}/{len(initial_cards)} cards, using heuristics for remainder")
            
            # Get cards that were placed
            placed_cards = (best_arrangement.front_hand.cards + 
                          best_arrangement.middle_hand.cards + 
                          best_arrangement.back_hand.cards)
            
            # Find remaining cards
            remaining = []
            for card in initial_cards:
                is_placed = any(pc.rank == card.rank and pc.suit == card.suit for pc in placed_cards)
                if not is_placed:
                    remaining.append(card)
            
            # Place remaining cards using heuristics
            if remaining:
                heuristic_placement = self._heuristic_initial_placement(remaining)
                
                # Merge heuristic placement into best_arrangement
                for card in heuristic_placement.front_hand.cards:
                    if not best_arrangement.front_hand.is_full():
                        best_arrangement.front_hand.add_card(card)
                
                for card in heuristic_placement.middle_hand.cards:
                    if not best_arrangement.middle_hand.is_full():
                        best_arrangement.middle_hand.add_card(card)
                
                for card in heuristic_placement.back_hand.cards:
                    if not best_arrangement.back_hand.is_full():
                        best_arrangement.back_hand.add_card(card)
            
            return best_arrangement
    
    def _heuristic_initial_placement(self, cards: List[Card]) -> PlayerArrangement:
        """Place initial 5 cards using simple heuristics."""
        arrangement = PlayerArrangement()
        sorted_cards = sorted(cards, reverse=True)
        
        # Look for pairs, trips, etc.
        rank_counts = defaultdict(int)
        for card in cards:
            rank_counts[card.rank] += 1
        
        # Place high pairs in back, medium pairs in middle
        placed_cards = set()
        
        # First, handle special combinations
        for rank, count in sorted(rank_counts.items(), key=lambda x: -RANK_VALUES[x[0]]):
            if count >= 2 and len(placed_cards) < 5:
                cards_of_rank = [c for c in cards if c.rank == rank and c not in placed_cards]
                
                if count >= 3:
                    # Place trips in back
                    for c in cards_of_rank[:3]:
                        arrangement.back_hand.add_card(c)
                        placed_cards.add(c)
                elif not arrangement.back_hand.cards:
                    # Place first pair in back
                    for c in cards_of_rank[:2]:
                        arrangement.back_hand.add_card(c)
                        placed_cards.add(c)
                elif not arrangement.middle_hand.cards:
                    # Place second pair in middle
                    for c in cards_of_rank[:2]:
                        arrangement.middle_hand.add_card(c)
                        placed_cards.add(c)
        
        # Place remaining cards
        remaining = [c for c in sorted_cards if c not in placed_cards]
        for card in remaining:
            if len(arrangement.back_hand.cards) < 2:
                arrangement.back_hand.add_card(card)
            elif len(arrangement.middle_hand.cards) < 2:
                arrangement.middle_hand.add_card(card)
            else:
                arrangement.front_hand.add_card(card)
        
        return arrangement
    
    def _count_nodes(self, node: MCTSNode) -> int:
        """Count total nodes in the tree."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def _count_complete_nodes(self, node: MCTSNode, target_cards: int) -> int:
        """Count nodes with complete initial placements."""
        total_placed = (len(node.state.front_hand.cards) + 
                       len(node.state.middle_hand.cards) + 
                       len(node.state.back_hand.cards))
        
        count = 1 if total_placed == target_cards else 0
        
        for child in node.children:
            count += self._count_complete_nodes(child, target_cards)
        
        return count


def main():
    """Main function to demonstrate the solver."""
    print("=== OFC MCTS Solver (Fixed) ===")
    
    # Test with initial 5 cards
    test_cards = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.from_string("Qs")
    ]
    
    solver = OFCMCTSSolver(num_simulations=1000)
    
    start_time = time.time()
    best_arrangement = solver.solve_initial_five(test_cards)
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*40}")
    print("BEST ARRANGEMENT:")
    print(f"{'='*40}")
    print(best_arrangement)
    print(f"\nTime taken: {elapsed_time:.2f} seconds")
    
    # Verify validity
    if best_arrangement.is_valid():
        print("✓ Arrangement is valid")
    else:
        print("✗ Arrangement is INVALID!")
    
    # Show hand evaluations
    print("\nHand Evaluations:")
    front_rank, _ = best_arrangement.front_hand.evaluate()
    middle_rank, _ = best_arrangement.middle_hand.evaluate()
    back_rank, _ = best_arrangement.back_hand.evaluate()
    
    hand_names = ["High Card", "Pair", "Two Pair", "Three of a Kind", 
                  "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]
    
    print(f"Front: {hand_names[front_rank]}")
    print(f"Middle: {hand_names[middle_rank]}")
    print(f"Back: {hand_names[back_rank]}")


if __name__ == "__main__":
    main()