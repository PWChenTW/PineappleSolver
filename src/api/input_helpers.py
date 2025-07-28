"""
Helper functions to simplify API input creation.

These utilities make it easier to create game states and requests
without dealing with the full complexity of the data models.
"""

from typing import List, Dict, Any, Union, Optional
from .models import (
    Card, Rank, Suit, GameState, PlayerState, HandCards,
    SolveRequest, AnalyzeRequest, SolveOptions, AnalyzeOptions
)


def card(notation: str) -> Dict[str, str]:
    """
    Convert string notation to card dictionary.
    
    Examples:
        card("As") -> {"rank": "A", "suit": "s"}
        card("Kh") -> {"rank": "K", "suit": "h"}
        card("Td") -> {"rank": "T", "suit": "d"}
        card("9c") -> {"rank": "9", "suit": "c"}
    
    Args:
        notation: Two-character string (rank + suit)
        
    Returns:
        Card dictionary
    """
    if len(notation) != 2:
        raise ValueError(f"Invalid card notation: {notation}. Expected 2 characters.")
    
    rank = notation[0].upper()
    suit = notation[1].lower()
    
    # Validate rank
    valid_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    if rank not in valid_ranks:
        raise ValueError(f"Invalid rank: {rank}. Valid ranks: {valid_ranks}")
    
    # Validate suit
    valid_suits = ['s', 'h', 'd', 'c']
    if suit not in valid_suits:
        raise ValueError(f"Invalid suit: {suit}. Valid suits: {valid_suits}")
    
    return {"rank": rank, "suit": suit}


def cards(notations: Union[str, List[str]]) -> List[Dict[str, str]]:
    """
    Convert multiple card notations to list of card dictionaries.
    
    Examples:
        cards("As Kh Qd") -> [{"rank": "A", "suit": "s"}, ...]
        cards(["As", "Kh", "Qd"]) -> [{"rank": "A", "suit": "s"}, ...]
        cards("AsKhQd") -> [{"rank": "A", "suit": "s"}, ...]  # No spaces
    
    Args:
        notations: Space-separated string or list of card notations
        
    Returns:
        List of card dictionaries
    """
    if isinstance(notations, str):
        # Handle both space-separated and continuous notation
        if ' ' in notations:
            notations = notations.split()
        else:
            # Split every 2 characters
            notations = [notations[i:i+2] for i in range(0, len(notations), 2)]
    
    return [card(n) for n in notations]


def create_player(
    player_id: str = "player1",
    top: Union[str, List[str]] = "",
    middle: Union[str, List[str]] = "",
    bottom: Union[str, List[str]] = "",
    in_fantasy: bool = False
) -> Dict[str, Any]:
    """
    Create a player state with simplified input.
    
    Examples:
        create_player("me", top="Ks Kh", middle="9s 8s 7s")
        create_player("opponent", bottom="As Ad Ac")
    
    Args:
        player_id: Player identifier
        top: Cards in top hand (max 3)
        middle: Cards in middle hand (max 5)
        bottom: Cards in bottom hand (max 5)
        in_fantasy: Whether player is in fantasy land
        
    Returns:
        Player state dictionary
    """
    return {
        "player_id": player_id,
        "top_hand": {
            "cards": cards(top) if top else [],
            "max_size": 3
        },
        "middle_hand": {
            "cards": cards(middle) if middle else [],
            "max_size": 5
        },
        "bottom_hand": {
            "cards": cards(bottom) if bottom else [],
            "max_size": 5
        },
        "in_fantasy_land": in_fantasy,
        "next_fantasy_land": False,
        "is_folded": False
    }


def create_game_state(
    round_num: int = 1,
    players: Optional[List[Dict[str, Any]]] = None,
    current_player: int = 0,
    deck: Union[str, List[str]] = "",
    dealer: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a game state with simplified input.
    
    Examples:
        # Simple single player
        create_game_state(deck="As Kh Qd Jc Ts")
        
        # Two players mid-game
        create_game_state(
            round_num=5,
            players=[
                create_player("me", top="Ks Kh", middle="9s 8s 7s"),
                create_player("opponent", top="As", bottom="Qd Qc")
            ],
            deck="6s 5s 4h"
        )
    
    Args:
        round_num: Current round (1-17)
        players: List of player states (default: one empty player)
        current_player: Index of current player
        deck: Remaining cards in deck
        dealer: Dealer position (default: 0)
        
    Returns:
        Game state dictionary
    """
    if players is None:
        players = [create_player()]
    
    return {
        "current_round": round_num,
        "players": players,
        "current_player_index": current_player,
        "remaining_deck": cards(deck) if deck else [],
        "dealer_position": dealer if dealer is not None else 0
    }


def quick_solve_request(
    game_state: Optional[Dict[str, Any]] = None,
    deck: Optional[Union[str, List[str]]] = None,
    time_limit: float = 5.0,
    async_mode: bool = False
) -> Dict[str, Any]:
    """
    Create a solve request with minimal input.
    
    Examples:
        # Simplest case - just provide the deck
        quick_solve_request(deck="As Kh Qd Jc Ts")
        
        # With custom game state
        quick_solve_request(
            game_state=create_game_state(round_num=5, ...),
            time_limit=10.0
        )
        
        # Async processing
        quick_solve_request(deck="As Kh Qd", async_mode=True)
    
    Args:
        game_state: Complete game state (if not provided, creates default)
        deck: Shortcut to create game state with just deck cards
        time_limit: Solving time limit in seconds
        async_mode: Whether to process asynchronously
        
    Returns:
        Solve request dictionary
    """
    if game_state is None:
        if deck is None:
            raise ValueError("Either game_state or deck must be provided")
        game_state = create_game_state(deck=deck)
    
    return {
        "game_state": game_state,
        "options": {
            "time_limit": time_limit
        },
        "async": async_mode
    }


def quick_analyze_request(
    game_state: Optional[Dict[str, Any]] = None,
    top: str = "",
    middle: str = "",
    bottom: str = "",
    deck: Union[str, List[str]] = "",
    depth: int = 3
) -> Dict[str, Any]:
    """
    Create an analyze request with minimal input.
    
    Examples:
        # Analyze with current hands
        quick_analyze_request(
            top="Ks Kh",
            middle="9s 8s 7s",
            bottom="As Ad",
            deck="6s Kd"
        )
    
    Args:
        game_state: Complete game state (if provided, other args ignored)
        top: Cards in top hand
        middle: Cards in middle hand
        bottom: Cards in bottom hand
        deck: Remaining cards
        depth: Analysis depth
        
    Returns:
        Analyze request dictionary
    """
    if game_state is None:
        player = create_player("player1", top=top, middle=middle, bottom=bottom)
        # Calculate round based on cards placed
        cards_placed = (
            len(player["top_hand"]["cards"]) +
            len(player["middle_hand"]["cards"]) +
            len(player["bottom_hand"]["cards"])
        )
        round_num = cards_placed // 5 + 1  # Rough estimate
        
        game_state = create_game_state(
            round_num=round_num,
            players=[player],
            deck=deck
        )
    
    return {
        "game_state": game_state,
        "options": {
            "depth": depth,
            "include_alternatives": True
        }
    }


# Validation endpoint helpers
def validate_game_state(game_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a game state before sending to API.
    
    Returns a dictionary with validation results:
    {
        "valid": bool,
        "errors": List[str],
        "warnings": List[str],
        "suggestions": List[str]
    }
    """
    errors = []
    warnings = []
    suggestions = []
    
    # Check basic structure
    if "players" not in game_state:
        errors.append("Missing 'players' field")
    elif not game_state["players"]:
        errors.append("No players in game state")
    else:
        # Check each player
        for i, player in enumerate(game_state["players"]):
            # Check hand sizes
            for hand_name, max_size in [("top_hand", 3), ("middle_hand", 5), ("bottom_hand", 5)]:
                if hand_name in player:
                    hand = player[hand_name]
                    if "cards" in hand and len(hand["cards"]) > max_size:
                        errors.append(f"Player {i} {hand_name} has too many cards ({len(hand['cards'])} > {max_size})")
    
    # Check round number
    if "current_round" in game_state:
        if game_state["current_round"] < 1 or game_state["current_round"] > 17:
            errors.append(f"Invalid round number: {game_state['current_round']} (must be 1-17)")
    
    # Check deck
    if "remaining_deck" in game_state:
        deck_cards = game_state["remaining_deck"]
        if len(deck_cards) > 52:
            errors.append(f"Too many cards in deck: {len(deck_cards)}")
        
        # Check for duplicates
        card_set = set()
        for card in deck_cards:
            card_str = f"{card.get('rank', '?')}{card.get('suit', '?')}"
            if card_str in card_set:
                errors.append(f"Duplicate card in deck: {card_str}")
            card_set.add(card_str)
    
    # Suggestions
    if not errors:
        if "current_round" in game_state and game_state["current_round"] == 1:
            if not game_state.get("remaining_deck"):
                suggestions.append("Add cards to remaining_deck to solve for initial placement")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions
    }


# Export commonly used functions for easy access
__all__ = [
    'card',
    'cards',
    'create_player',
    'create_game_state',
    'quick_solve_request',
    'quick_analyze_request',
    'validate_game_state'
]