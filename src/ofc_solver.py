"""
Main OFC Solver class that integrates all components.

This module provides the high-level interface for solving OFC positions.
"""

from typing import List, Optional, Dict, Callable, Tuple
import logging
import time
from dataclasses import dataclass

from src.core.domain import GameState, Card, Street
from src.core.algorithms.ofc_mcts import MCTSEngine, MCTSConfig
from src.core.algorithms.mcts_node import Action
from src.core.algorithms.action_generator import ActionGenerator
from src.core.algorithms.evaluator import StateEvaluator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SolverConfig:
    """Configuration for OFC Solver."""
    
    # Time limit for solving in seconds
    time_limit: float = 300.0  # 5 minutes
    
    # Number of MCTS simulations (if not using time limit)
    num_simulations: Optional[int] = None
    
    # Number of threads for parallel search
    num_threads: int = 4
    
    # MCTS exploration constant
    c_puct: float = 1.4
    
    # Use action generator for move ordering
    use_action_generator: bool = True
    
    # Enable progressive widening
    progressive_widening: bool = True
    
    # Logging level
    log_level: str = 'INFO'


@dataclass
class SolveResult:
    """Result of solving an OFC position."""
    
    # Best action found
    best_action: Action
    
    # Expected score
    expected_score: float
    
    # Number of simulations run
    num_simulations: int
    
    # Time taken in seconds
    time_taken: float
    
    # Top N actions with statistics
    top_actions: List[Tuple[Action, int, float]]  # (action, visits, avg_reward)
    
    # Additional statistics
    statistics: Dict[str, any]


class OFCSolver:
    """
    Main solver class for Open Face Chinese Poker.
    
    Integrates MCTS search with domain-specific optimizations
    to find optimal plays.
    """
    
    def __init__(self, config: Optional[SolverConfig] = None):
        """
        Initialize OFC Solver.
        
        Args:
            config: Solver configuration
        """
        self.config = config or SolverConfig()
        
        # Set logging level
        logging.getLogger().setLevel(getattr(logging, self.config.log_level))
        
        # Initialize components
        self.action_generator = ActionGenerator() if self.config.use_action_generator else None
        self.evaluator = StateEvaluator()
        
        # Create MCTS config
        self.mcts_config = MCTSConfig(
            time_limit=self.config.time_limit,
            num_simulations=self.config.num_simulations,
            c_puct=self.config.c_puct,
            num_threads=self.config.num_threads,
            progressive_widening=self.config.progressive_widening
        )
    
    def solve(self, 
              game_state: GameState,
              progress_callback: Optional[Callable[[int, float, str], None]] = None) -> SolveResult:
        """
        Solve the current OFC position.
        
        Args:
            game_state: Current game state to solve
            progress_callback: Optional callback for progress updates
                              Called with (simulations, elapsed_time, status_message)
        
        Returns:
            SolveResult with best action and statistics
        """
        logger.info(f"Starting to solve position at street {game_state.current_street.name}")
        logger.info(f"Cards placed: {game_state.player_arrangement.cards_placed}/13")
        
        start_time = time.time()
        
        # Check if we need to deal cards first
        if not game_state.current_hand and not game_state.is_complete:
            logger.info("Dealing cards for current street")
            game_state.deal_street()
        
        # Special handling for action generation
        if self.config.use_action_generator:
            # Inject custom action generator into MCTS
            original_generate = self._inject_action_generator(game_state)
        
        # Create MCTS engine
        mcts_engine = MCTSEngine(self.mcts_config)
        
        # Define internal progress callback
        def mcts_progress(sims: int, elapsed: float):
            if progress_callback:
                status = f"Running MCTS: {sims} simulations"
                progress_callback(sims, elapsed, status)
        
        # Run MCTS search
        best_action = mcts_engine.search(game_state, mcts_progress)
        
        # Get statistics from root node
        # This is a bit hacky - would be better to return root from search
        stats = mcts_engine.get_statistics()
        
        # Calculate time taken
        time_taken = time.time() - start_time
        
        # Create result
        result = SolveResult(
            best_action=best_action,
            expected_score=0.0,  # TODO: Get from root node
            num_simulations=stats['simulations'],
            time_taken=time_taken,
            top_actions=[],  # TODO: Get from root node
            statistics=stats
        )
        
        logger.info(f"Solving complete. Time: {time_taken:.2f}s, "
                   f"Simulations: {result.num_simulations}")
        
        return result
    
    def solve_game(self,
                   initial_state: Optional[GameState] = None,
                   progress_callback: Optional[Callable[[str], None]] = None) -> List[SolveResult]:
        """
        Solve a complete game from start to finish.
        
        Args:
            initial_state: Starting state (or None for new game)
            progress_callback: Optional callback for status updates
            
        Returns:
            List of SolveResults for each decision point
        """
        if initial_state is None:
            initial_state = GameState(num_players=2, player_index=0)
        
        game_state = initial_state.copy()
        results = []
        
        while not game_state.is_complete:
            # Update progress
            if progress_callback:
                progress_callback(f"Solving street {game_state.current_street.name}")
            
            # Deal cards if needed
            if not game_state.current_hand:
                game_state.deal_street()
                logger.info(f"Dealt cards: {' '.join(str(c) for c in game_state.current_hand)}")
            
            # Solve current position
            result = self.solve(game_state)
            results.append(result)
            
            # Apply best action
            if result.best_action:
                game_state.place_cards(result.best_action.placements, 
                                     result.best_action.discard)
                
                logger.info("Action applied:")
                for card, pos, idx in result.best_action.placements:
                    logger.info(f"  Place {card} at {pos}[{idx}]")
                if result.best_action.discard:
                    logger.info(f"  Discard {result.best_action.discard}")
            else:
                logger.error("No action found!")
                break
        
        # Final evaluation
        if game_state.is_complete:
            final_score = self.evaluator.evaluate_final_arrangement(
                game_state.player_arrangement
            )
            logger.info(f"Game complete! Expected score: {final_score:.2f}")
            
            if progress_callback:
                progress_callback(f"Game complete! Final score: {final_score:.2f}")
        
        return results
    
    def _inject_action_generator(self, game_state: GameState):
        """
        Inject custom action generator into MCTS node.
        
        This is a bit of a hack but avoids modifying the MCTS implementation.
        """
        from src.core.algorithms.mcts_node import MCTSNode
        
        # Save original method
        original_generate = MCTSNode._generate_actions
        
        # Store action generator reference
        action_gen = self.action_generator
        
        # Create wrapper that uses our action generator
        def custom_generate(node_self):
            # Use our action generator
            actions = action_gen.generate_actions(node_self.state)
            return actions
        
        # Monkey patch
        MCTSNode._generate_actions = custom_generate
        
        return original_generate
    
    def analyze_position(self, game_state: GameState) -> Dict[str, any]:
        """
        Analyze a position without full search.
        
        Provides quick evaluation and statistics.
        """
        analysis = {
            'street': game_state.current_street.name,
            'cards_placed': game_state.player_arrangement.cards_placed,
            'current_hand': [str(c) for c in game_state.current_hand],
            'is_valid': True,
            'foul_risk': 0.0,
            'expected_score': 0.0,
            'royalties': None
        }
        
        # Check validity
        if game_state.player_arrangement.cards_placed > 0:
            is_valid, error = game_state.player_arrangement.is_valid_progressive()
            analysis['is_valid'] = is_valid
            if not is_valid:
                analysis['error'] = error
        
        # Evaluate position
        if not game_state.is_complete:
            score = self.evaluator.evaluate_state(game_state)
            analysis['expected_score'] = score
            
            # Calculate foul risk
            foul_risk = self.evaluator._evaluate_foul_risk(
                game_state.player_arrangement, game_state
            )
            analysis['foul_risk'] = foul_risk
        else:
            # Complete game
            final_score = self.evaluator.evaluate_final_arrangement(
                game_state.player_arrangement
            )
            analysis['expected_score'] = final_score
            
            royalties = game_state.player_arrangement.calculate_royalties()
            analysis['royalties'] = {
                'front': royalties.front,
                'middle': royalties.middle,
                'back': royalties.back,
                'total': royalties.total
            }
        
        return analysis


def create_solver(time_limit: float = 300.0,
                  num_threads: int = 4,
                  use_action_generator: bool = True) -> OFCSolver:
    """
    Convenience function to create a solver with common settings.
    
    Args:
        time_limit: Time limit in seconds
        num_threads: Number of threads for parallel search
        use_action_generator: Whether to use intelligent action generation
        
    Returns:
        Configured OFC solver
    """
    config = SolverConfig(
        time_limit=time_limit,
        num_threads=num_threads,
        use_action_generator=use_action_generator
    )
    return OFCSolver(config)