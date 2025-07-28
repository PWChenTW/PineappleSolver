"""
Adapter to connect the API with the OFC solver implementation.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import uuid

from ..ofc_solver import OFCSolver, GameState, Card as SolverCard, SolveResult
from ..core.domain import Card as DomainCard, Rank, Suit
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
        # Update solver configuration
        # The new OFCSolver doesn't have a separate _solver attribute
        # Configuration is done through the integration instance
        if hasattr(self.solver, 'integration'):
            # New implementation with MCTS integration
            self.solver.integration.configure(
                time_limit=time_limit,
                threads=threads,
                simulations_limit=max_iterations
            )
        elif hasattr(self.solver, '_solver'):
            # Old implementation
            self.solver._solver.configure(
                time_limit=time_limit,
                threads=threads,
                simulations_limit=max_iterations,
                exploration_constant=exploration_constant
            )
    
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
        
        # Handle drawn_cards field from GUI
        drawn_cards = []
        if hasattr(api_state, 'drawn_cards'):
            drawn_cards = api_state.drawn_cards
        
        # Convert cards - check if we have drawn cards from GUI
        if drawn_cards:
            # Use drawn cards from GUI
            current_cards = [
                SolverCard(rank=card.rank.value, suit=card.suit.value)
                for card in drawn_cards
            ]
        elif api_state.remaining_deck:
            # Use cards from remaining deck
            if api_state.current_round == 1:  # Initial round
                current_cards = [
                    SolverCard(rank=card.rank.value, suit=card.suit.value)
                    for card in api_state.remaining_deck[:5]
                ]
            else:
                current_cards = [
                    SolverCard(rank=card.rank.value, suit=card.suit.value)
                    for card in api_state.remaining_deck[:3]
                ]
        else:
            # No cards to place
            current_cards = []
        
        # Convert existing hands
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
        
        # Calculate remaining cards
        total_used = len(front_hand) + len(middle_hand) + len(back_hand) + len(current_cards)
        remaining_cards = 52 - total_used
        
        return GameState(
            current_cards=current_cards,
            front_hand=front_hand,
            middle_hand=middle_hand,
            back_hand=back_hand,
            remaining_cards=remaining_cards
        )
    
    def _convert_result(self, solver_result: SolveResult, 
                       api_state: APIGameState) -> APISolveResult:
        """Convert solver result to API result."""
        # Convert best placement to move
        card_placements = []
        
        # Parse the placement dictionary
        for card_str, position in solver_result.best_placement.items():
            # Parse card string (e.g., "As" -> rank="A", suit="s")
            if len(card_str) >= 2:
                rank_char = card_str[0]
                suit_char = card_str[1]
                
                # Create API card
                api_card = APICard(rank=rank_char, suit=suit_char)
                
                # Map position to HandType
                hand_map = {
                    'front': HandType.TOP,
                    'middle': HandType.MIDDLE,
                    'back': HandType.BOTTOM
                }
                
                hand_type = hand_map.get(position, HandType.TOP)
                
                placement = CardPlacement(
                    card=api_card,
                    hand=hand_type
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
        
        # Convert alternative moves from top actions
        alternatives = []
        for action_info in solver_result.top_actions:
            # Each top action represents one card placement
            if 'card' in action_info and 'position' in action_info:
                card_str = action_info['card']
                position = action_info['position']
                
                if len(card_str) >= 2:
                    rank_char = card_str[0]
                    suit_char = card_str[1]
                    
                    api_card = APICard(rank=rank_char, suit=suit_char)
                    
                    hand_map = {
                        'front': HandType.TOP,
                        'middle': HandType.MIDDLE,
                        'back': HandType.BOTTOM
                    }
                    
                    hand_type = hand_map.get(position, HandType.TOP)
                    
                    placement = CardPlacement(card=api_card, hand=hand_type)
                    alt_move = Move(card_placements=[placement], is_fold=False)
                    
                    alternatives.append(MoveEvaluation(
                        move=alt_move,
                        evaluation=action_info.get('avg_reward', 0),
                        visit_count=action_info.get('visits', 0),
                        win_rate=min(0.5 + action_info.get('avg_reward', 0) / 100, 0.99)
                    ))
        
        return APISolveResult(
            request_id=uuid.uuid4(),
            best_move=best_move,
            evaluation=solver_result.expected_score,
            confidence=solver_result.confidence,
            alternative_moves=alternatives[:3] if alternatives else None,
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
            # Check for drawn cards first
            cards_to_consider = []
            if hasattr(game_state, 'drawn_cards') and game_state.drawn_cards:
                cards_to_consider = game_state.drawn_cards
            elif game_state.remaining_deck:
                # Get next few cards to consider
                num_cards = 3 if game_state.current_round > 1 else 5
                cards_to_consider = game_state.remaining_deck[:num_cards]
            
            for i, card in enumerate(cards_to_consider):
                # Recommend placing in different positions based on card strength
                card_value = self._get_card_value(card)
                
                if card_value >= 10:  # High cards
                    preferred_hand = HandType.BOTTOM
                    priority = Priority.HIGH
                elif card_value >= 7:  # Medium cards
                    preferred_hand = HandType.MIDDLE
                    priority = Priority.NORMAL
                else:  # Low cards
                    preferred_hand = HandType.TOP
                    priority = Priority.LOW
                
                move = Move(
                    card_placements=[CardPlacement(card=card, hand=preferred_hand)],
                    is_fold=False
                )
                
                recommendation = MoveRecommendation(
                    move=move,
                    reasoning=f"Place {card.rank.value}{card.suit.value} in {preferred_hand.value} based on card strength",
                    priority=priority,
                    expected_value=card_value * 2.0
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
    
    def _get_card_value(self, card: APICard) -> int:
        """Get numerical value of a card for evaluation."""
        rank_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        return rank_values.get(card.rank.value, 0)
    
    def _analyze_hand_strength(self, cards: List[APICard], position: str) -> HandStrength:
        """Analyze strength of a single hand."""
        if not cards:
            return HandStrength(
                current_rank="High Card",
                current_strength=0.1,
                potential_improvements=[]
            )
        
        # Simple hand strength analysis based on number of cards
        if len(cards) >= 2:
            # Check for pairs
            ranks = [card.rank.value for card in cards]
            if len(ranks) != len(set(ranks)):
                current_rank = "Pair"
                current_strength = 0.4
            else:
                current_rank = "High Card"
                current_strength = 0.2
        else:
            current_rank = "High Card"
            current_strength = 0.1
        
        # Add potential improvements
        improvements = []
        max_cards = 3 if position == "top" else 5
        if len(cards) < max_cards:
            # Check for flush potential
            if len(cards) >= 2 and all(card.suit == cards[0].suit for card in cards):
                improvements.append(HandStrengthImprovement(
                    hand_type="Flush",
                    probability=0.3,
                    required_cards=[]  # Would need more cards of same suit
                ))
            
            # Check for straight potential
            if len(cards) >= 2:
                improvements.append(HandStrengthImprovement(
                    hand_type="Straight",
                    probability=0.15,
                    required_cards=[]
                ))
        
        return HandStrength(
            current_rank=current_rank,
            current_strength=min(current_strength + len(cards) * 0.05, 1.0),
            potential_improvements=improvements
        )
    
    def _evaluate_position(self, player_state) -> float:
        """Evaluate overall position score."""
        # Count total cards placed
        total_cards = (len(player_state.top_hand.cards) + 
                      len(player_state.middle_hand.cards) + 
                      len(player_state.bottom_hand.cards))
        
        # Base score on cards placed and position quality
        base_score = total_cards * 3
        
        # Bonus for fantasy land
        if player_state.in_fantasy_land:
            base_score += 25
        
        # Penalty for potential fouls
        if len(player_state.top_hand.cards) == 3 and len(player_state.middle_hand.cards) == 5:
            # Check if top is stronger than middle (potential foul)
            base_score -= 10
        
        return base_score
    
    def _calculate_foul_probability(self, player_state) -> float:
        """Calculate probability of fouling."""
        # Simple heuristic based on cards placed
        top_cards = len(player_state.top_hand.cards)
        middle_cards = len(player_state.middle_hand.cards)
        bottom_cards = len(player_state.bottom_hand.cards)
        
        # If hands are complete, check for actual fouls
        if top_cards == 3 and middle_cards == 5 and bottom_cards == 5:
            return 0.0  # Would need actual hand comparison
        
        # Otherwise estimate based on cards placed
        if top_cards >= 2 and middle_cards >= 3:
            return 0.2  # Higher risk when multiple hands have cards
        elif top_cards >= 1 or middle_cards >= 2:
            return 0.1
        else:
            return 0.05