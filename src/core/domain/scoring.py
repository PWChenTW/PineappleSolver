"""
Scoring system for OFC.

This module implements the complete scoring rules including
basic points, royalties, and special bonuses.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple

from src.core.domain.player_arrangement import PlayerArrangement, RoyaltyPoints
from src.core.domain.hand import Hand


@dataclass
class HandComparison:
    """Result of comparing two hands."""
    winner: int  # 0 for player 1, 1 for player 2, -1 for tie
    player1_hand: Optional[Hand]
    player2_hand: Optional[Hand]


@dataclass
class ScoreResult:
    """Complete scoring result between two players."""
    # Basic points (winning hands)
    front_winner: int  # -1 for tie, 0 for player1, 1 for player2
    middle_winner: int
    back_winner: int
    
    # Scoop bonus
    scoop_winner: Optional[int] = None  # Player who scooped
    
    # Foul
    foul_player: Optional[int] = None  # Player who fouled
    
    # Royalties
    player1_royalties: RoyaltyPoints = None
    player2_royalties: RoyaltyPoints = None
    
    # Net score (from player 1's perspective)
    net_score: int = 0
    
    def __post_init__(self):
        """Calculate net score after initialization."""
        if self.player1_royalties is None:
            self.player1_royalties = RoyaltyPoints()
        if self.player2_royalties is None:
            self.player2_royalties = RoyaltyPoints()
    
    @property
    def player1_score(self) -> int:
        """Total score for player 1."""
        return self.net_score
    
    @property 
    def player2_score(self) -> int:
        """Total score for player 2."""
        return -self.net_score


class ScoringSystem:
    """
    OFC scoring system implementation.
    
    Handles all scoring rules including basic points, royalties,
    scoops, and fouls.
    """
    
    # Foul penalties
    FOUL_PENALTY_HEADS_UP = 6  # Points lost for fouling in heads-up
    FOUL_PENALTY_MULTIPLAYER = 3  # Points lost per opponent in multiplayer
    
    # Scoop bonus
    SCOOP_BONUS = 3  # Extra points for winning all three hands
    
    def score_hands(self, 
                    player1: PlayerArrangement, 
                    player2: PlayerArrangement) -> ScoreResult:
        """
        Score two player arrangements against each other.
        
        Args:
            player1: First player's arrangement
            player2: Second player's arrangement
            
        Returns:
            Complete scoring result
        """
        result = ScoreResult(
            front_winner=-1,
            middle_winner=-1, 
            back_winner=-1
        )
        
        # Check for fouls
        p1_valid, p1_error = player1.is_valid()
        p2_valid, p2_error = player2.is_valid()
        
        if not p1_valid and not p2_valid:
            # Both foul - no scoring
            result.foul_player = -1  # Both fouled
            result.net_score = 0
            return result
        
        if not p1_valid:
            # Player 1 fouls
            result.foul_player = 0
            result.player2_royalties = player2.calculate_royalties()
            # Player 1 loses 6 points + all opponent royalties
            result.net_score = -self.FOUL_PENALTY_HEADS_UP - result.player2_royalties.total
            return result
        
        if not p2_valid:
            # Player 2 fouls  
            result.foul_player = 1
            result.player1_royalties = player1.calculate_royalties()
            # Player 1 wins 6 points + all their royalties
            result.net_score = self.FOUL_PENALTY_HEADS_UP + result.player1_royalties.total
            return result
        
        # Both valid - compare hands
        p1_front = player1.get_front_hand()
        p1_middle = player1.get_middle_hand()
        p1_back = player1.get_back_hand()
        
        p2_front = player2.get_front_hand()
        p2_middle = player2.get_middle_hand()
        p2_back = player2.get_back_hand()
        
        # Compare each hand
        basic_points = 0
        wins = 0
        
        # Front
        if p1_front > p2_front:
            result.front_winner = 0
            basic_points += 1
            wins += 1
        elif p2_front > p1_front:
            result.front_winner = 1
            basic_points -= 1
        
        # Middle
        if p1_middle > p2_middle:
            result.middle_winner = 0
            basic_points += 1
            wins += 1
        elif p2_middle > p1_middle:
            result.middle_winner = 1
            basic_points -= 1
        
        # Back
        if p1_back > p2_back:
            result.back_winner = 0
            basic_points += 1
            wins += 1
        elif p2_back > p1_back:
            result.back_winner = 1
            basic_points -= 1
        
        # Check for scoop
        if wins == 3:
            result.scoop_winner = 0
            basic_points += self.SCOOP_BONUS
        elif wins == 0 and (result.front_winner == 1 or 
                            result.middle_winner == 1 or 
                            result.back_winner == 1):
            # Player 2 scooped
            result.scoop_winner = 1
            basic_points -= self.SCOOP_BONUS
        
        # Calculate royalties
        result.player1_royalties = player1.calculate_royalties()
        result.player2_royalties = player2.calculate_royalties()
        
        # Net score
        royalty_diff = result.player1_royalties.total - result.player2_royalties.total
        result.net_score = basic_points + royalty_diff
        
        return result
    
    def score_against_multiple(self,
                              player: PlayerArrangement,
                              opponents: List[PlayerArrangement]) -> int:
        """
        Score one player against multiple opponents.
        
        Args:
            player: The player's arrangement
            opponents: List of opponent arrangements
            
        Returns:
            Total net score for the player
        """
        total_score = 0
        
        for opponent in opponents:
            result = self.score_hands(player, opponent)
            total_score += result.player1_score
        
        return total_score
    
    def format_score_result(self, result: ScoreResult) -> str:
        """Format a score result for display."""
        lines = []
        
        # Foul handling
        if result.foul_player == 0:
            lines.append("Player 1 FOULED!")
            lines.append(f"Player 2 wins: +{-result.net_score} points")
            return "\n".join(lines)
        elif result.foul_player == 1:
            lines.append("Player 2 FOULED!")
            lines.append(f"Player 1 wins: +{result.net_score} points")
            return "\n".join(lines)
        elif result.foul_player == -1:
            lines.append("Both players FOULED! No scoring.")
            return "\n".join(lines)
        
        # Regular scoring
        lines.append("=== Scoring Summary ===")
        
        # Hand comparisons
        hand_results = []
        if result.front_winner == 0:
            hand_results.append("Front: P1 wins (+1)")
        elif result.front_winner == 1:
            hand_results.append("Front: P2 wins (-1)")
        else:
            hand_results.append("Front: Tie (0)")
        
        if result.middle_winner == 0:
            hand_results.append("Middle: P1 wins (+1)")
        elif result.middle_winner == 1:
            hand_results.append("Middle: P2 wins (-1)")
        else:
            hand_results.append("Middle: Tie (0)")
        
        if result.back_winner == 0:
            hand_results.append("Back: P1 wins (+1)")
        elif result.back_winner == 1:
            hand_results.append("Back: P2 wins (-1)")
        else:
            hand_results.append("Back: Tie (0)")
        
        lines.extend(hand_results)
        
        # Scoop
        if result.scoop_winner == 0:
            lines.append(f"SCOOP! P1 wins all (+{self.SCOOP_BONUS})")
        elif result.scoop_winner == 1:
            lines.append(f"SCOOP! P2 wins all (-{self.SCOOP_BONUS})")
        
        # Royalties
        lines.append("\nRoyalties:")
        p1_roy = result.player1_royalties
        lines.append(f"P1: Front={p1_roy.front}, Middle={p1_roy.middle}, "
                    f"Back={p1_roy.back} (Total=+{p1_roy.total})")
        
        p2_roy = result.player2_royalties
        lines.append(f"P2: Front={p2_roy.front}, Middle={p2_roy.middle}, "
                    f"Back={p2_roy.back} (Total=-{p2_roy.total})")
        
        # Final score
        lines.append(f"\nNet Score: {result.net_score:+d} for Player 1")
        
        return "\n".join(lines)