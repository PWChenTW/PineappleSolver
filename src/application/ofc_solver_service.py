"""
OFC Solver Application Service.

This module provides the main service layer that coordinates between
the API layer and the domain layer, handling all business logic.
"""

import time
from typing import List, Dict, Optional, Tuple
import logging

from src.api.dto import (
    GameStateDTO, SolveRequestDTO, SolveResultDTO,
    PlacementDTO, ActionStatDTO, InitialPlacementRequestDTO
)
from src.core.domain import (
    GameState, Card, Rank, Suit, Street,
    PlayerArrangement
)
from src.core.algorithms import MCTSEngine, MCTSConfig, Action
from src.exceptions import InvalidInputError, GameRuleViolationError
from src.logging_config import get_solver_logger, LogContext

logger = get_solver_logger()


class OFCSolverService:
    """
    Main application service for OFC solving.
    
    This service handles:
    - DTO to domain model conversion
    - MCTS algorithm coordination
    - Result transformation
    - Error handling and logging
    """
    
    def __init__(self,
                 threads: int = 4,
                 default_time_limit: float = 30.0,
                 default_simulations_limit: Optional[int] = None):
        """
        Initialize the solver service.
        
        Args:
            threads: Number of threads for parallel MCTS
            default_time_limit: Default time limit for search
            default_simulations_limit: Default simulations limit
        """
        self.threads = threads
        self.default_time_limit = default_time_limit
        self.default_simulations_limit = default_simulations_limit
        
        # Initialize MCTS engine with default config
        self.mcts_config = MCTSConfig(
            time_limit=default_time_limit,
            num_simulations=default_simulations_limit,
            num_threads=threads,
            c_puct=1.4,
            use_transposition_table=True,
            progressive_widening=True
        )
        self.mcts_engine = MCTSEngine(self.mcts_config)
        
        logger.info(
            "OFC Solver Service initialized",
            extra={
                'component': 'solver_service',
                'context': {
                    'threads': threads,
                    'default_time_limit': default_time_limit
                }
            }
        )
    
    def solve_position(self, request: SolveRequestDTO) -> SolveResultDTO:
        """
        Solve an OFC position.
        
        Args:
            request: Solve request with game state and options
            
        Returns:
            SolveResultDTO with best placement and statistics
        """
        with LogContext(logger, operation="solve_position") as log_ctx:
            try:
                # Convert DTO to domain model
                game_state = self._dto_to_domain_state(request.game_state)
                
                # Update config if custom limits provided
                if request.time_limit is not None:
                    self.mcts_config.time_limit = request.time_limit
                if request.simulations_limit is not None:
                    self.mcts_config.num_simulations = request.simulations_limit
                
                # Run MCTS search
                start_time = time.time()
                mcts_result = self.mcts_engine.search(game_state)
                elapsed_time = time.time() - start_time
                
                # Convert result to DTO
                result_dto = self._create_result_dto(
                    mcts_result.best_action,
                    mcts_result.root_node,
                    elapsed_time
                )
                
                log_ctx.log("info", "Position solved successfully",
                           simulations=result_dto.simulations_count,
                           time_taken=elapsed_time)
                
                return result_dto
                
            except Exception as e:
                log_ctx.log("error", f"Failed to solve position: {str(e)}",
                           error_type=type(e).__name__)
                raise
    
    def solve_initial_placement(self, request: InitialPlacementRequestDTO) -> SolveResultDTO:
        """
        Solve initial 5-card placement.
        
        Args:
            request: Initial placement request
            
        Returns:
            SolveResultDTO with optimal placement
        """
        with LogContext(logger, operation="solve_initial_placement") as log_ctx:
            try:
                # Validate request
                request.validate()
                
                # Create initial game state properly
                game_state = self._create_initial_game_state(request.cards)
                
                # Update config if custom time limit provided
                if request.time_limit is not None:
                    self.mcts_config.time_limit = request.time_limit
                
                # Run MCTS search
                start_time = time.time()
                mcts_result = self.mcts_engine.search(game_state)
                elapsed_time = time.time() - start_time
                
                # Convert result to DTO
                result_dto = self._create_result_dto(
                    mcts_result.best_action,
                    mcts_result.root_node,
                    elapsed_time
                )
                
                log_ctx.log("info", "Initial placement solved",
                           cards=request.cards,
                           simulations=result_dto.simulations_count)
                
                return result_dto
                
            except Exception as e:
                log_ctx.log("error", f"Failed to solve initial placement: {str(e)}",
                           error_type=type(e).__name__)
                raise
    
    def _dto_to_domain_state(self, dto: GameStateDTO) -> GameState:
        """Convert GameStateDTO to domain GameState."""
        # Create new game state
        game_state = GameState(num_players=2, player_index=0)
        
        # Convert and set current hand
        current_cards = [self._parse_card(card_str) for card_str in dto.current_cards]
        
        # Handle street and hand setup
        if dto.current_street:
            street = Street[dto.current_street.upper()]
        else:
            # Infer street from card counts
            total_cards = (len(dto.front_hand) + len(dto.middle_hand) + 
                          len(dto.back_hand) + len(dto.current_cards))
            street = self._infer_street(total_cards)
        
        # For initial street with cards in hand, we need special handling
        if street == Street.INITIAL and current_cards:
            # Create a fresh game state and manually set the hand
            # This is a workaround for the domain model's constraints
            game_state._current_street = Street.INITIAL
            game_state._current_hand = current_cards
        else:
            # Place existing cards first
            self._place_existing_cards(game_state, dto)
            
            # Then set current hand if any
            if current_cards:
                game_state._current_hand = current_cards
                game_state._current_street = street
        
        return game_state
    
    def _create_initial_game_state(self, card_strings: List[str]) -> GameState:
        """Create game state for initial 5-card placement."""
        # Convert card strings to domain cards
        cards = [self._parse_card(card_str) for card_str in card_strings]
        
        # Create game state
        game_state = GameState(num_players=2, player_index=0)
        
        # Set up initial state manually
        # This is necessary because GameState doesn't expose a clean way
        # to set up an initial hand without going through deal_street()
        game_state._current_street = Street.INITIAL
        game_state._current_hand = cards
        
        return game_state
    
    def _place_existing_cards(self, game_state: GameState, dto: GameStateDTO):
        """Place already placed cards into game state."""
        # This would need to be implemented based on how the domain model
        # allows setting up partial game states
        pass
    
    def _parse_card(self, card_str: str) -> Card:
        """Parse card string to domain Card."""
        if len(card_str) != 2:
            raise InvalidInputError(f"Invalid card string: {card_str}")
        
        rank_char = card_str[0]
        suit_char = card_str[1]
        
        # Map rank
        rank_map = {
            '2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, '5': Rank.FIVE,
            '6': Rank.SIX, '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
            'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN, 
            'K': Rank.KING, 'A': Rank.ACE
        }
        
        # Map suit
        suit_map = {
            's': Suit.SPADES, 'h': Suit.HEARTS,
            'd': Suit.DIAMONDS, 'c': Suit.CLUBS
        }
        
        if rank_char not in rank_map:
            raise InvalidInputError(f"Invalid rank: {rank_char}")
        if suit_char not in suit_map:
            raise InvalidInputError(f"Invalid suit: {suit_char}")
        
        return Card(rank=rank_map[rank_char], suit=suit_map[suit_char])
    
    def _infer_street(self, total_cards: int) -> Street:
        """Infer current street from total cards."""
        if total_cards <= 5:
            return Street.INITIAL
        elif total_cards <= 8:
            return Street.FIRST
        elif total_cards <= 10:
            return Street.SECOND
        elif total_cards <= 12:
            return Street.THIRD
        elif total_cards <= 13:
            return Street.FOURTH
        else:
            return Street.COMPLETE
    
    def _create_result_dto(self, 
                          best_action: Action,
                          root_node,
                          elapsed_time: float) -> SolveResultDTO:
        """Create SolveResultDTO from MCTS result."""
        # Convert placements
        placements = []
        for card, position, index in best_action.placements:
            card_str = f"{card.rank.value}{card.suit.value}"
            placements.append(PlacementDTO(
                card=card_str,
                position=position,
                index=index
            ))
        
        # Convert discard if any
        discard = None
        if best_action.discard:
            discard = f"{best_action.discard.rank.value}{best_action.discard.suit.value}"
        
        # Calculate statistics
        expected_score = root_node.total_reward / max(root_node.visit_count, 1)
        confidence = min(root_node.visit_count / 10000.0, 0.99)
        
        # Get top actions
        action_stats = root_node.get_action_statistics()
        top_actions = []
        
        for action, visits, avg_reward in action_stats[:5]:
            if action.placements:
                # Use first placement as representative
                card, position, index = action.placements[0]
                card_str = f"{card.rank.value}{card.suit.value}"
                
                top_actions.append(ActionStatDTO(
                    placement=PlacementDTO(card=card_str, position=position, index=index),
                    visits=visits,
                    average_reward=avg_reward,
                    confidence=visits / max(root_node.visit_count, 1)
                ))
        
        return SolveResultDTO(
            best_placements=placements,
            discard=discard,
            expected_score=expected_score,
            confidence=confidence,
            simulations_count=self.mcts_engine.simulations_run,
            time_taken=elapsed_time,
            top_actions=top_actions
        )
    
    def update_config(self, **kwargs):
        """Update solver configuration."""
        if 'threads' in kwargs:
            self.mcts_config.num_threads = kwargs['threads']
        if 'time_limit' in kwargs:
            self.mcts_config.time_limit = kwargs['time_limit']
        if 'simulations_limit' in kwargs:
            self.mcts_config.num_simulations = kwargs['simulations_limit']
        if 'exploration_constant' in kwargs:
            self.mcts_config.c_puct = kwargs['exploration_constant']
        
        # Recreate engine with new config
        self.mcts_engine = MCTSEngine(self.mcts_config)