"""
MCTS implementation for OFC Solver.

This module implements the Monte Carlo Tree Search algorithm optimized
for Open Face Chinese Poker.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Set, Callable
from dataclasses import dataclass
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

from src.core.domain import GameState, Street, Card
from src.core.algorithms.mcts_node import MCTSNode, Action
from src.core.algorithms.evaluator import StateEvaluator


logger = logging.getLogger(__name__)


@dataclass
class MCTSConfig:
    """Configuration for MCTS search."""
    
    # Time limit in seconds
    time_limit: float = 300.0  # 5 minutes default
    
    # Number of simulations (if not using time limit)
    num_simulations: Optional[int] = None
    
    # Exploration constant
    c_puct: float = 1.4
    
    # Number of threads for parallel search
    num_threads: int = 1
    
    # Enable transposition table
    use_transposition_table: bool = True
    
    # Maximum depth for rollouts
    max_rollout_depth: int = 20
    
    # Batch size for leaf parallelization
    leaf_batch_size: int = 8
    
    # Virtual loss for parallel MCTS
    virtual_loss: float = 1.0
    
    # Enable progressive widening
    progressive_widening: bool = True
    
    # Progressive widening constant
    pw_constant: float = 1.5
    
    # Minimum visits before expanding new action
    pw_threshold: int = 10


@dataclass
class MCTSResult:
    """Result from MCTS search containing action and root node."""
    best_action: Action
    root_node: MCTSNode


class MCTSEngine:
    """
    Monte Carlo Tree Search engine for OFC.
    
    Implements MCTS with domain-specific optimizations for
    Open Face Chinese Poker.
    """
    
    def __init__(self, config: Optional[MCTSConfig] = None):
        """
        Initialize MCTS engine.
        
        Args:
            config: Search configuration
        """
        self.config = config or MCTSConfig()
        self.evaluator = StateEvaluator()
        
        # Statistics
        self.nodes_evaluated = 0
        self.simulations_run = 0
        
        # Transposition table
        self.transposition_table: Dict[str, MCTSNode] = {}
    
    def search(self, 
               initial_state: GameState,
               progress_callback: Optional[Callable[[int, float], None]] = None) -> MCTSResult:
        """
        Run MCTS search from initial state.
        
        Args:
            initial_state: Starting game state
            progress_callback: Optional callback for progress updates
            
        Returns:
            MCTSResult containing best action and root node
        """
        logger.info(f"Starting MCTS search with config: {self.config}")
        
        # Reset statistics
        self.nodes_evaluated = 0
        self.simulations_run = 0
        self.transposition_table.clear()
        
        # Create root node
        root = MCTSNode(initial_state)
        
        # Run search
        if self.config.num_threads > 1:
            best_action = self._parallel_search(root, progress_callback)
        else:
            best_action = self._sequential_search(root, progress_callback)
        
        # Log final statistics
        logger.info(f"Search complete. Simulations: {self.simulations_run}, "
                   f"Nodes: {self.nodes_evaluated}")
        
        if root.children:
            stats = root.get_action_statistics()
            logger.info("Top actions:")
            for i, (action, visits, reward) in enumerate(stats[:5]):
                logger.info(f"  {i+1}. Visits: {visits}, Avg reward: {reward:.3f}")
        
        return MCTSResult(best_action=best_action, root_node=root)
    
    def _sequential_search(self, 
                          root: MCTSNode,
                          progress_callback: Optional[Callable[[int, float], None]]) -> Action:
        """Run sequential MCTS search."""
        start_time = time.time()
        
        while not self._should_stop(start_time):
            # Run one simulation
            self._run_simulation(root)
            
            # Progress callback
            if progress_callback and self.simulations_run % 100 == 0:
                elapsed = time.time() - start_time
                progress_callback(self.simulations_run, elapsed)
        
        return root.get_best_action()
    
    def _parallel_search(self,
                        root: MCTSNode,
                        progress_callback: Optional[Callable[[int, float], None]]) -> Action:
        """Run parallel MCTS search using root parallelization."""
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.config.num_threads) as executor:
            # Create thread-local roots
            thread_roots = [root]  # Share the root for virtual loss
            
            # Submit initial batch of simulations
            futures = []
            for _ in range(self.config.num_threads * 2):
                future = executor.submit(self._run_simulation_with_virtual_loss, root)
                futures.append(future)
            
            completed = 0
            while not self._should_stop(start_time):
                # Wait for some simulations to complete
                done = []
                pending = []
                
                # Check which futures are done
                for future in futures:
                    if future.done():
                        done.append(future)
                    else:
                        pending.append(future)
                
                # Process completed simulations
                for future in done:
                    try:
                        future.result()
                        completed += 1
                        
                        # Submit new simulation
                        new_future = executor.submit(self._run_simulation_with_virtual_loss, root)
                        pending.append(new_future)
                        
                    except Exception as e:
                        logger.error(f"Simulation error: {e}")
                
                # If no futures completed, wait a bit
                if not done:
                    time.sleep(0.01)
                
                futures = pending
                
                # Progress callback
                if progress_callback and completed % 100 == 0:
                    elapsed = time.time() - start_time
                    progress_callback(self.simulations_run, elapsed)
            
            # Cancel remaining futures
            for future in futures:
                future.cancel()
        
        return root.get_best_action()
    
    def _should_stop(self, start_time: float) -> bool:
        """Check if search should stop."""
        if self.config.num_simulations is not None:
            return self.simulations_run >= self.config.num_simulations
        else:
            elapsed = time.time() - start_time
            return elapsed >= self.config.time_limit
    
    def _run_simulation(self, root: MCTSNode) -> float:
        """
        Run one MCTS simulation.
        
        Phases:
        1. Selection - traverse tree using UCB
        2. Expansion - add new node
        3. Rollout - simulate to end
        4. Backpropagation - update statistics
        """
        node = root
        
        # Selection phase
        path = [node]
        while not node.is_terminal and node.is_fully_expanded and len(node.children) > 0:
            node = node.select_child(self.config.c_puct)
            path.append(node)
        
        # Expansion phase
        if not node.is_terminal and not node.is_fully_expanded:
            # Check for progressive widening
            if self.config.progressive_widening:
                allowed_actions = self._get_allowed_actions(node)
                if allowed_actions:
                    node.untried_actions = allowed_actions
            
            if node.get_untried_actions():
                node = node.expand()
                path.append(node)
                self.nodes_evaluated += 1
        
        # Evaluation/Rollout phase
        if node.is_terminal:
            # Terminal node - evaluate final state
            reward = self.evaluator.evaluate_final_arrangement(node.state.player_arrangement)
        else:
            # Non-terminal - use rollout or neural network evaluation
            reward = self._rollout(node.state)
        
        # Backpropagation phase
        for n in reversed(path):
            n.update(reward)
        
        self.simulations_run += 1
        return reward
    
    def _run_simulation_with_virtual_loss(self, root: MCTSNode) -> float:
        """Run simulation with virtual loss for parallel MCTS."""
        node = root
        
        # Apply virtual loss during selection
        path = [node]
        virtual_visits = []
        
        while not node.is_terminal and node.is_fully_expanded and len(node.children) > 0:
            # Apply virtual loss
            node.visit_count += self.config.virtual_loss
            virtual_visits.append(node)
            
            node = node.select_child(self.config.c_puct)
            path.append(node)
        
        # Run rest of simulation
        if not node.is_terminal and not node.is_fully_expanded:
            if node.get_untried_actions():
                node = node.expand()
                path.append(node)
                self.nodes_evaluated += 1
        
        # Evaluation
        if node.is_terminal:
            reward = self.evaluator.evaluate_final_arrangement(node.state.player_arrangement)
        else:
            reward = self._rollout(node.state)
        
        # Remove virtual loss and do real update
        for n in virtual_visits:
            n.visit_count -= self.config.virtual_loss
        
        for n in reversed(path):
            n.update(reward)
        
        self.simulations_run += 1
        return reward
    
    def _rollout(self, state: GameState) -> float:
        """
        Perform rollout from current state to terminal state.
        
        Uses simple heuristic policy for speed.
        """
        # Make a copy to avoid modifying original
        sim_state = state.copy()
        
        depth = 0
        while not sim_state.is_complete and depth < self.config.max_rollout_depth:
            # Deal cards if needed
            if not sim_state.current_hand:
                try:
                    sim_state.deal_street()
                except ValueError:
                    # Not enough cards - shouldn't happen
                    break
            
            # Use simple heuristic to choose action
            action = self._rollout_policy(sim_state)
            if action is None:
                break
            
            try:
                sim_state.place_cards(action.placements, action.discard)
            except ValueError:
                # Invalid action - shouldn't happen with good policy
                break
            
            depth += 1
        
        # Evaluate final or partial state
        return self.evaluator.evaluate_state(sim_state)
    
    def _rollout_policy(self, state: GameState) -> Optional[Action]:
        """
        Simple rollout policy for fast simulation.
        
        Uses heuristics to make reasonable but fast decisions.
        """
        current_hand = state.current_hand
        if not current_hand:
            return None
        
        positions = state.get_valid_placements()
        if not positions:
            return None
        
        if state.current_street == Street.INITIAL:
            # Initial placement - use simple heuristic
            # Place high cards in back, medium in middle, low in front
            sorted_cards = sorted(current_hand, key=lambda c: c.rank_value, reverse=True)
            
            # Simple distribution: 2 front, 2 middle, 1 back
            if len(positions) >= 5:
                placements = []
                pos_idx = 0
                
                # Place lowest 2 in front
                for i in range(2):
                    if pos_idx < len(positions):
                        pos = positions[pos_idx]
                        if pos[0] == 'front':
                            placements.append((sorted_cards[-(i+1)], pos[0], pos[1]))
                            pos_idx += 1
                
                # Place middle 2 in middle
                for i in range(2):
                    if pos_idx < len(positions):
                        pos = positions[pos_idx]
                        if pos[0] == 'middle':
                            placements.append((sorted_cards[2+i], pos[0], pos[1]))
                            pos_idx += 1
                
                # Place highest in back
                if pos_idx < len(positions):
                    pos = positions[pos_idx]
                    if pos[0] == 'back':
                        placements.append((sorted_cards[0], pos[0], pos[1]))
                
                if len(placements) == 5:
                    return Action(placements)
            
            # Fallback - just place in order
            placements = []
            for i in range(5):
                if i < len(positions) and i < len(current_hand):
                    placements.append((current_hand[i], positions[i][0], positions[i][1]))
            return Action(placements) if len(placements) == 5 else None
        
        else:
            # Regular street - place 2, discard 1
            # Simple heuristic: keep higher cards, place in back positions
            sorted_cards = sorted(current_hand, key=lambda c: c.rank_value, reverse=True)
            
            # Keep 2 highest, discard lowest
            keep_cards = sorted_cards[:2]
            discard = sorted_cards[-1]
            
            # Place in available positions (prefer back)
            back_positions = [p for p in positions if p[0] == 'back']
            middle_positions = [p for p in positions if p[0] == 'middle']
            front_positions = [p for p in positions if p[0] == 'front']
            
            preferred_positions = back_positions + middle_positions + front_positions
            
            if len(preferred_positions) >= 2:
                placements = [
                    (keep_cards[0], preferred_positions[0][0], preferred_positions[0][1]),
                    (keep_cards[1], preferred_positions[1][0], preferred_positions[1][1])
                ]
                return Action(placements, discard)
        
        return None
    
    def _get_allowed_actions(self, node: MCTSNode) -> List[Action]:
        """
        Get allowed actions for progressive widening.
        
        Returns subset of actions based on visit count.
        """
        all_actions = node.get_untried_actions()
        
        if not self.config.progressive_widening:
            return all_actions
        
        # Calculate how many actions to allow
        max_actions = int(self.config.pw_constant * math.pow(node.visit_count, 0.5))
        max_actions = max(1, min(max_actions, len(all_actions)))
        
        # For now, just take first N actions
        # Could use domain knowledge to prioritize
        return all_actions[:max_actions]
    
    def get_statistics(self) -> Dict[str, any]:
        """Get search statistics."""
        return {
            'simulations': self.simulations_run,
            'nodes_evaluated': self.nodes_evaluated,
            'transposition_table_size': len(self.transposition_table),
            'config': self.config
        }