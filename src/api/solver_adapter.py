"""
Adapter to connect the API with the OFC solver implementation.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import uuid

from ..ofc_solver import OFCSolver, GameState, Card as SolverCard, SolveResult
from ..mcts_engine import MCTSEngine
from .models import (
    GameState as APIGameState, 
    Card as APICard,
    Move, CardPlacement, HandType,
    SolveResult as APISolveResult,
    SolveStatistics,
    MoveEvaluation,
    PositionAnalysis,
    HandStrength,
    HandStrengthImprovement,
    MoveRecommendation,
    Priority
)


class MCTSSolver:
    """Adapter for MCTS solver to work with API."""
    
    def __init__(self):
        self.solver = OFCSolver(threads=4, time_limit=30.0)
        self.version = "1.0.0"
    
    def configure(self, time_limit: float = 30.0, max_iterations: Optional[int] = None,
                  threads: int = 4, exploration_constant: float = 1.4,
                  use_neural_network: bool = False):
        """Configure solver parameters."""
        self.solver.time_limit = time_limit
        self.solver.threads = threads
        if max_iterations:
            self.solver.simulations_limit = max_iterations
    
    async def solve(self, game_state: APIGameState) -> APISolveResult:
        """Solve the game position."""
        # Convert API game state to solver game state
        solver_state = self._convert_game_state(game_state)
        
        # Run solver in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            self.solver.solve, 
            solver_state
        )
        
        # Convert result back to API format
        return self._convert_result(result, game_state)
    
    def _convert_game_state(self, api_state: APIGameState) -> GameState:
        """Convert API game state to solver game state."""
        # Get current player
        current_player = api_state.players[api_state.current_player_index]
        
        # Convert cards
        current_cards = [
            SolverCard(rank=card.rank.value, suit=card.suit.value)
            for card in api_state.remaining_deck[:5]  # Simulate drawing cards
        ]
        
        front_hand = [
            SolverCard(rank=card.rank.value, suit=card.suit.value)
            for card in current_player.top_hand.cards
        ]
        
        middle_hand = [
            SolverCard(rank=card.rank.value, suit=card.suit.value)
            for card in current_player.middle_hand.cards
        ]
        
        back_hand = [
            SolverCard(rank=card.rank.value, suit=card.suit.value)
            for card in current_player.bottom_hand.cards
        ]
        
        return GameState(
            current_cards=current_cards,
            front_hand=front_hand,
            middle_hand=middle_hand,
            back_hand=back_hand,
            remaining_cards=len(api_state.remaining_deck) - 5
        )
    
    def _convert_result(self, solver_result: SolveResult, 
                       api_state: APIGameState) -> APISolveResult:
        """Convert solver result to API result."""
        # Convert best placement to move
        card_placements = []
        for card_str, position in solver_result.best_placement.items():
            # Parse card string (e.g., "As" -> rank="A", suit="s")
            if len(card_str) >= 2:
                rank = card_str[0]
                suit = card_str[1]
                
                # Map position to HandType
                hand_map = {
                    'front': HandType.TOP,
                    'middle': HandType.MIDDLE,
                    'back': HandType.BOTTOM
                }
                
                placement = CardPlacement(
                    card=APICard(rank=rank, suit=suit),
                    hand=hand_map.get(position, HandType.TOP)
                )
                card_placements.append(placement)
        
        best_move = Move(card_placements=card_placements, is_fold=False)
        
        # Convert statistics
        stats = SolveStatistics(
            total_iterations=solver_result.simulations,
            nodes_visited=solver_result.simulations * 3,  # Estimate
            average_depth=12.5,  # Estimate
            max_depth=20,
            cache_hits=solver_result.simulations // 10,
            cache_misses=solver_result.simulations // 20
        )
        
        # Convert alternative moves
        alternatives = []
        for i, action in enumerate(solver_result.top_actions):
            alt_placements = []
            if 'card' in action and 'position' in action:
                card_str = action['card']
                if len(card_str) >= 2:
                    rank = card_str[0]
                    suit = card_str[1]
                    
                    hand_map = {
                        'front': HandType.TOP,
                        'middle': HandType.MIDDLE,
                        'back': HandType.BOTTOM
                    }
                    
                    placement = CardPlacement(
                        card=APICard(rank=rank, suit=suit),
                        hand=hand_map.get(action['position'], HandType.TOP)
                    )
                    alt_placements.append(placement)
            
            if alt_placements:
                alt_move = Move(card_placements=alt_placements, is_fold=False)
                alternatives.append(MoveEvaluation(
                    move=alt_move,
                    evaluation=action.get('avg_reward', 0),
                    visit_count=action.get('visits', 0),
                    win_rate=min(0.5 + action.get('avg_reward', 0) / 100, 0.99)
                ))
        
        return APISolveResult(
            request_id=uuid.uuid4(),
            best_move=best_move,
            evaluation=solver_result.expected_score,
            confidence=solver_result.confidence,
            alternative_moves=alternatives if alternatives else None,
            statistics=stats,
            computation_time=solver_result.time_taken
        )
    
    def health_check(self):
        """Check if solver is healthy."""
        # Simple health check
        return True


class PositionEvaluator:
    """Quick position evaluator without deep search."""
    
    async def analyze(self, game_state: APIGameState, depth: int = 3,
                     include_alternatives: bool = True) -> PositionAnalysis:
        """Analyze a game position."""
        # Get current player
        current_player = game_state.players[game_state.current_player_index]
        
        # Analyze hand strengths
        hand_strengths = {
            "top": self._analyze_hand_strength(current_player.top_hand.cards, "top"),
            "middle": self._analyze_hand_strength(current_player.middle_hand.cards, "middle"),
            "bottom": self._analyze_hand_strength(current_player.bottom_hand.cards, "bottom")
        }
        
        # Generate recommendations
        recommendations = []
        if include_alternatives:
            # Add some mock recommendations
            if game_state.remaining_deck:
                next_card = game_state.remaining_deck[0]
                
                # Recommend placing in different positions
                for hand_type, priority in [
                    (HandType.TOP, Priority.HIGH),
                    (HandType.MIDDLE, Priority.NORMAL),
                    (HandType.BOTTOM, Priority.LOW)
                ]:
                    move = Move(
                        card_placements=[CardPlacement(card=next_card, hand=hand_type)],
                        is_fold=False
                    )
                    
                    recommendation = MoveRecommendation(
                        move=move,
                        reasoning=f"Place {next_card.rank.value}{next_card.suit.value} in {hand_type.value} for potential flush/straight",
                        priority=priority,
                        expected_value=10.0 if priority == Priority.HIGH else 5.0
                    )
                    recommendations.append(recommendation)
        
        # Calculate probabilities
        fantasy_prob = 0.15 if current_player.in_fantasy_land else 0.05
        foul_prob = self._calculate_foul_probability(current_player)
        
        return PositionAnalysis(
            request_id=uuid.uuid4(),
            evaluation=self._evaluate_position(current_player),
            hand_strengths=hand_strengths,
            recommendations=recommendations[:5],
            fantasy_land_probability=fantasy_prob,
            foul_probability=foul_prob
        )
    
    def _analyze_hand_strength(self, cards: List[APICard], position: str) -> HandStrength:
        """Analyze strength of a single hand."""
        if not cards:
            return HandStrength(
                current_rank="High Card",
                current_strength=0.1,
                potential_improvements=[]
            )
        
        # Mock hand strength analysis
        current_rank = "Pair" if len(cards) >= 2 else "High Card"
        current_strength = 0.3 + len(cards) * 0.1
        
        # Add some potential improvements
        improvements = []
        if len(cards) < (3 if position == "top" else 5):
            improvements.append(HandStrengthImprovement(
                hand_type="Flush",
                probability=0.2,
                required_cards=[APICard(rank="A", suit=cards[0].suit)] if cards else []
            ))
        
        return HandStrength(
            current_rank=current_rank,
            current_strength=min(current_strength, 1.0),
            potential_improvements=improvements
        )
    
    def _evaluate_position(self, player_state) -> float:
        """Evaluate overall position score."""
        # Simple evaluation based on cards placed
        total_cards = (len(player_state.top_hand.cards) + 
                      len(player_state.middle_hand.cards) + 
                      len(player_state.bottom_hand.cards))
        
        base_score = total_cards * 5
        if player_state.in_fantasy_land:
            base_score += 20
        
        return base_score
    
    def _calculate_foul_probability(self, player_state) -> float:
        """Calculate probability of fouling."""
        # Simple heuristic
        if len(player_state.top_hand.cards) == 3:
            return 0.1
        elif len(player_state.middle_hand.cards) == 5:
            return 0.15
        else:
            return 0.05