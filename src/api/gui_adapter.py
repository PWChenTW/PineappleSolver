"""
GUI adapter for handling requests from the web interface.

This module provides compatibility between the GUI's request format
and the API's internal models.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .models import (
    GameState as APIGameState, 
    Card, Rank, Suit, HandCards, PlayerState,
    SolveRequest, SolveOptions
)


class GUICard(BaseModel):
    """Card model from GUI."""
    rank: str
    suit: str


class GUIHandCards(BaseModel):
    """Hand cards from GUI."""
    cards: List[GUICard]
    max_size: int


class GUIPlayerState(BaseModel):
    """Player state from GUI."""
    player_id: str
    top_hand: GUIHandCards
    middle_hand: GUIHandCards
    bottom_hand: GUIHandCards
    in_fantasy_land: bool = False
    next_fantasy_land: bool = False
    is_folded: bool = False


class GUIGameState(BaseModel):
    """Game state from GUI."""
    current_round: int
    players: List[GUIPlayerState]
    current_player_index: int
    drawn_cards: List[GUICard] = Field(default_factory=list)
    remaining_deck: List[GUICard] = Field(default_factory=list)


class GUISolveRequest(BaseModel):
    """Solve request from GUI."""
    game_state: GUIGameState
    options: Optional[Dict[str, Any]] = None


def convert_gui_card(gui_card: GUICard) -> Card:
    """Convert GUI card to API card."""
    # Map rank and suit
    rank_map = {
        '2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, '5': Rank.FIVE,
        '6': Rank.SIX, '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
        'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN, 'K': Rank.KING, 'A': Rank.ACE
    }
    
    suit_map = {
        's': Suit.SPADES, 'h': Suit.HEARTS, 'd': Suit.DIAMONDS, 'c': Suit.CLUBS
    }
    
    return Card(
        rank=rank_map.get(gui_card.rank, Rank.ACE),
        suit=suit_map.get(gui_card.suit, Suit.SPADES)
    )


def convert_gui_request(gui_request: Dict[str, Any]) -> SolveRequest:
    """Convert GUI request to API SolveRequest."""
    # Parse GUI request
    gui_game_state = gui_request['game_state']
    
    # Convert players
    players = []
    for gui_player in gui_game_state['players']:
        # Convert hands
        top_hand = HandCards(
            cards=[convert_gui_card(GUICard(**c)) for c in gui_player['top_hand']['cards']],
            max_size=gui_player['top_hand']['max_size']
        )
        middle_hand = HandCards(
            cards=[convert_gui_card(GUICard(**c)) for c in gui_player['middle_hand']['cards']],
            max_size=gui_player['middle_hand']['max_size']
        )
        bottom_hand = HandCards(
            cards=[convert_gui_card(GUICard(**c)) for c in gui_player['bottom_hand']['cards']],
            max_size=gui_player['bottom_hand']['max_size']
        )
        
        player = PlayerState(
            player_id=gui_player['player_id'],
            top_hand=top_hand,
            middle_hand=middle_hand,
            bottom_hand=bottom_hand,
            in_fantasy_land=gui_player.get('in_fantasy_land', False),
            next_fantasy_land=gui_player.get('next_fantasy_land', False),
            is_folded=gui_player.get('is_folded', False)
        )
        players.append(player)
    
    # Convert drawn cards to remaining deck (for compatibility)
    drawn_cards = [convert_gui_card(GUICard(**c)) for c in gui_game_state.get('drawn_cards', [])]
    remaining_deck = drawn_cards  # Use drawn cards as the cards to be placed
    
    # Create API game state
    api_game_state = APIGameState(
        current_round=gui_game_state['current_round'],
        players=players,
        current_player_index=gui_game_state['current_player_index'],
        remaining_deck=remaining_deck
    )
    
    # Create API game state with drawn_cards attribute for solver adapter
    setattr(api_game_state, 'drawn_cards', drawn_cards)
    
    # Convert options
    options = SolveOptions()
    if gui_request.get('options'):
        gui_options = gui_request['options']
        if 'time_limit' in gui_options:
            options.time_limit = gui_options['time_limit']
        if 'threads' in gui_options:
            options.threads = gui_options['threads']
        if 'simulations' in gui_options:
            options.max_iterations = gui_options['simulations']
    
    return SolveRequest(
        game_state=api_game_state,
        options=options,
        async_mode=False
    )