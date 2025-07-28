"""
MCTS implementation with Prometheus metrics integration.
"""

import time
from typing import Dict, Optional, Callable
import threading

from .ofc_mcts import MCTSEngine, MCTSConfig, MCTSResult, MCTSNode
from src.core.domain import GameState
from src.api.prometheus_metrics import (
    record_mcts_metrics,
    mcts_rollout_depth,
    mcts_thread_utilization,
    solver_simulation_rate
)


class PrometheusThreadLocal(threading.local):
    """Thread-local storage for metrics."""
    def __init__(self):
        self.thread_id = None
        self.simulations = 0
        self.last_update = time.time()


class PrometheusMCTSEngine(MCTSEngine):
    """MCTS engine with Prometheus metrics collection."""
    
    def __init__(self, config: Optional[MCTSConfig] = None):
        super().__init__(config)
        self.thread_locals = PrometheusThreadLocal()
        self.metrics_update_interval = 1.0  # Update metrics every second
        self.global_start_time = None
    
    def search(self, 
               initial_state: GameState,
               progress_callback: Optional[Callable[[int, float], None]] = None) -> MCTSResult:
        """Run MCTS search with metrics collection."""
        self.global_start_time = time.time()
        
        # Wrap progress callback to add metrics
        def metrics_progress_callback(simulations: int, elapsed: float):
            # Update simulation rate metric
            if elapsed > 0:
                rate = simulations / elapsed
                solver_simulation_rate.set(rate)
            
            # Call original callback if provided
            if progress_callback:
                progress_callback(simulations, elapsed)
        
        # Run search
        result = super().search(initial_state, metrics_progress_callback)
        
        # Record final MCTS metrics
        record_mcts_metrics(
            nodes_evaluated=self.nodes_evaluated,
            tree_size=len(self.transposition_table) if self.config.use_transposition_table else self.nodes_evaluated
        )
        
        return result
    
    def _run_simulation(self, root: MCTSNode) -> float:
        """Run simulation with metrics collection."""
        # Record simulation start
        rollout_start_depth = 0
        
        # Override to track rollout depth
        node = root
        path = [node]
        
        # Selection phase
        while not node.is_terminal and node.is_fully_expanded and len(node.children) > 0:
            node = node.select_child(self.config.c_puct)
            path.append(node)
        
        # Expansion phase
        if not node.is_terminal and not node.is_fully_expanded:
            if node.get_untried_actions():
                node = node.expand()
                path.append(node)
                self.nodes_evaluated += 1
        
        # Track rollout start depth
        rollout_start_depth = len(path)
        
        # Evaluation/Rollout phase
        if node.is_terminal:
            reward = self.evaluator.evaluate_final_arrangement(node.state.player_arrangement)
        else:
            # Track rollout depth
            rollout_state = node.state.copy()
            rollout_depth = 0
            
            while not rollout_state.is_complete and rollout_depth < self.config.max_rollout_depth:
                if not rollout_state.current_hand:
                    try:
                        rollout_state.deal_street()
                    except ValueError:
                        break
                
                action = self._rollout_policy(rollout_state)
                if action is None:
                    break
                
                try:
                    rollout_state.place_cards(action.placements, action.discard)
                    rollout_depth += 1
                except ValueError:
                    break
            
            # Record rollout depth metric
            mcts_rollout_depth.observe(rollout_depth)
            
            reward = self.evaluator.evaluate_state(rollout_state)
        
        # Backpropagation
        for n in reversed(path):
            n.update(reward)
        
        self.simulations_run += 1
        
        # Update thread-local metrics
        self._update_thread_metrics()
        
        return reward
    
    def _run_simulation_with_virtual_loss(self, root: MCTSNode) -> float:
        """Run simulation with virtual loss and metrics."""
        # Get thread ID
        thread_id = threading.get_ident()
        if self.thread_locals.thread_id != thread_id:
            self.thread_locals.thread_id = thread_id
            self.thread_locals.simulations = 0
            self.thread_locals.last_update = time.time()
        
        # Run simulation
        result = super()._run_simulation_with_virtual_loss(root)
        
        # Update thread metrics
        self.thread_locals.simulations += 1
        self._update_thread_metrics()
        
        return result
    
    def _update_thread_metrics(self):
        """Update thread utilization metrics."""
        current_time = time.time()
        
        # Check if it's time to update metrics
        if current_time - self.thread_locals.last_update >= self.metrics_update_interval:
            # Calculate thread utilization
            elapsed = current_time - self.thread_locals.last_update
            thread_simulations = self.thread_locals.simulations
            
            if elapsed > 0 and self.global_start_time is not None:
                # Calculate this thread's simulation rate
                thread_rate = thread_simulations / elapsed
                
                # Calculate utilization as percentage of expected rate
                total_elapsed = current_time - self.global_start_time
                if total_elapsed > 0:
                    global_rate = self.simulations_run / total_elapsed / self.config.num_threads
                    if global_rate > 0:
                        utilization = min(thread_rate / global_rate * 100, 100)
                    else:
                        utilization = 0
                else:
                    utilization = 0
                
                # Update metric
                thread_id_str = str(self.thread_locals.thread_id)[-4:]  # Last 4 digits
                mcts_thread_utilization.labels(thread_id=thread_id_str).set(utilization)
            
            # Reset counters
            self.thread_locals.simulations = 0
            self.thread_locals.last_update = current_time


# Factory function
def create_prometheus_mcts_engine(config: Optional[MCTSConfig] = None) -> PrometheusMCTSEngine:
    """Create MCTS engine with Prometheus metrics."""
    return PrometheusMCTSEngine(config)