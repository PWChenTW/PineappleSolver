#!/usr/bin/env python3
"""
Basic test script for OFC game engine.

Tests the core functionality of the game engine.
"""

import sys
sys.path.append('.')

from src.core.domain import (
    Card, Rank, Suit, Hand, PlayerArrangement,
    GameState, Street, ScoringSystem
)


def test_card_creation():
    """Test card creation and representation."""
    print("=== Testing Card Creation ===")
    
    # Create cards
    ace_spades = Card.from_rank_suit(Rank.ACE, Suit.SPADES)
    two_hearts = Card.from_string("2h")
    king_clubs = Card.from_string("Kc")
    
    print(f"Ace of Spades: {ace_spades}")
    print(f"Two of Hearts: {two_hearts}")
    print(f"King of Clubs: {king_clubs}")
    
    # Test comparison
    print(f"\nAce > King: {ace_spades > king_clubs}")
    print(f"King > Two: {king_clubs > two_hearts}")
    print()


def test_hand_evaluation():
    """Test hand evaluation."""
    print("=== Testing Hand Evaluation ===")
    
    # Test flush
    flush_cards = [
        Card.from_string("As"),
        Card.from_string("Ks"),
        Card.from_string("Qs"),
        Card.from_string("Js"),
        Card.from_string("9s")
    ]
    flush_hand = Hand(flush_cards)
    print(f"Flush: {flush_hand}")
    
    # Test full house
    fh_cards = [
        Card.from_string("Kh"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.from_string("2s"),
        Card.from_string("2h")
    ]
    fh_hand = Hand(fh_cards)
    print(f"Full House: {fh_hand}")
    
    # Test straight
    straight_cards = [
        Card.from_string("9h"),
        Card.from_string("8d"),
        Card.from_string("7c"),
        Card.from_string("6s"),
        Card.from_string("5h")
    ]
    straight_hand = Hand(straight_cards)
    print(f"Straight: {straight_hand}")
    
    # Test comparison
    print(f"\nFull House > Flush: {fh_hand > flush_hand}")
    print(f"Flush > Straight: {flush_hand > straight_hand}")
    
    # Test 3-card hand
    trips_cards = [
        Card.from_string("Qh"),
        Card.from_string("Qd"),
        Card.from_string("Qc")
    ]
    trips_hand = Hand(trips_cards)
    print(f"\n3-card trips: {trips_hand}")
    print()


def test_game_flow():
    """Test basic game flow."""
    print("=== Testing Game Flow ===")
    
    # Create game
    game = GameState(num_players=2, player_index=0, seed=42)
    
    # Deal initial street
    print(f"Current street: {game.current_street.name}")
    initial_cards = game.deal_street()
    print(f"Dealt cards: {' '.join(str(c) for c in initial_cards)}")
    
    # Place initial 5 cards
    placements = [
        (initial_cards[0], 'front', 0),   # First card to front
        (initial_cards[1], 'front', 1),   # Second card to front
        (initial_cards[2], 'middle', 0),  # Third to middle
        (initial_cards[3], 'back', 0),    # Fourth to back
        (initial_cards[4], 'back', 1),    # Fifth to back
    ]
    
    game.place_cards(placements)
    print(f"\nAfter placing initial cards:")
    print(game.player_arrangement)
    
    # Deal and play street 1
    print(f"\n\nCurrent street: {game.current_street.name}")
    street1_cards = game.deal_street()
    print(f"Dealt cards: {' '.join(str(c) for c in street1_cards)}")
    
    # Place 2, discard 1
    placements = [
        (street1_cards[0], 'middle', 1),
        (street1_cards[1], 'back', 2),
    ]
    game.place_cards(placements, discard=street1_cards[2])
    
    print(f"\nAfter street 1:")
    print(game.player_arrangement)
    print()


def test_scoring():
    """Test scoring system."""
    print("=== Testing Scoring System ===")
    
    # Create two complete arrangements
    p1 = PlayerArrangement()
    p2 = PlayerArrangement()
    
    # Player 1: Strong back (flush), medium middle (straight), weak front (pair)
    # Front: 88x
    p1.place_card(Card.from_string("8h"), 'front', 0)
    p1.place_card(Card.from_string("8d"), 'front', 1)
    p1.place_card(Card.from_string("2c"), 'front', 2)
    
    # Middle: 9-high straight
    p1.place_card(Card.from_string("9s"), 'middle', 0)
    p1.place_card(Card.from_string("8s"), 'middle', 1)
    p1.place_card(Card.from_string("7h"), 'middle', 2)
    p1.place_card(Card.from_string("6d"), 'middle', 3)
    p1.place_card(Card.from_string("5c"), 'middle', 4)
    
    # Back: King-high flush
    p1.place_card(Card.from_string("Kc"), 'back', 0)
    p1.place_card(Card.from_string("Jc"), 'back', 1)
    p1.place_card(Card.from_string("9c"), 'back', 2)
    p1.place_card(Card.from_string("7c"), 'back', 3)
    p1.place_card(Card.from_string("3c"), 'back', 4)
    
    # Player 2: QQ in front (fantasyland!), trips in middle, straight in back
    # Front: QQx
    p2.place_card(Card.from_string("Qh"), 'front', 0)
    p2.place_card(Card.from_string("Qd"), 'front', 1)
    p2.place_card(Card.from_string("4c"), 'front', 2)
    
    # Middle: Trip 4s
    p2.place_card(Card.from_string("4h"), 'middle', 0)
    p2.place_card(Card.from_string("4d"), 'middle', 1)
    p2.place_card(Card.from_string("4s"), 'middle', 2)
    p2.place_card(Card.from_string("Ah"), 'middle', 3)
    p2.place_card(Card.from_string("Kd"), 'middle', 4)
    
    # Back: Ace-high straight
    p2.place_card(Card.from_string("As"), 'back', 0)
    p2.place_card(Card.from_string("Ks"), 'back', 1)
    p2.place_card(Card.from_string("Qs"), 'back', 2)
    p2.place_card(Card.from_string("Js"), 'back', 3)
    p2.place_card(Card.from_string("Th"), 'back', 4)
    
    print("Player 1:")
    print(p1)
    is_valid, error = p1.is_valid()
    print(f"Valid: {is_valid}")
    if is_valid:
        royalties = p1.calculate_royalties()
        print(f"Royalties: F={royalties.front} M={royalties.middle} B={royalties.back}")
    
    print("\nPlayer 2:")
    print(p2)
    is_valid, error = p2.is_valid()
    print(f"Valid: {is_valid}")
    if is_valid:
        royalties = p2.calculate_royalties()
        print(f"Royalties: F={royalties.front} M={royalties.middle} B={royalties.back}")
        print(f"Fantasyland: {p2.qualifies_for_fantasyland()}")
    
    # Score the hands
    scoring = ScoringSystem()
    result = scoring.score_hands(p1, p2)
    print(f"\n{scoring.format_score_result(result)}")


def main():
    """Run all tests."""
    test_card_creation()
    test_hand_evaluation()
    test_game_flow()
    test_scoring()
    
    print("\n=== All tests completed! ===")


if __name__ == "__main__":
    main()