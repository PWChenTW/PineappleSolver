#!/usr/bin/env python3
"""
Simple test for OFC Solver to diagnose issues.
"""

import sys
sys.path.append('.')

from src.core.domain import GameState, Card
from src.core.algorithms.mcts_node import MCTSNode
from src.core.algorithms.evaluator import StateEvaluator


def test_basic_mcts_node():
    """Test basic MCTS node functionality."""
    print("=== Testing MCTS Node ===")
    
    # Create game state
    game = GameState(num_players=2, player_index=0, seed=42)
    initial_cards = game.deal_street()
    print(f"Dealt cards: {' '.join(str(c) for c in initial_cards)}")
    
    # Create root node
    root = MCTSNode(game)
    print(f"Root node: {root}")
    
    # Get untried actions
    actions = root.get_untried_actions()
    print(f"Number of untried actions: {len(actions)}")
    
    if actions:
        print(f"First action: {len(actions[0].placements)} placements")
        for card, pos, idx in actions[0].placements[:3]:
            print(f"  - Place {card} at {pos}[{idx}]")
    
    # Test expansion
    if actions:
        print("\nExpanding node...")
        child = root.expand()
        print(f"Child node: {child}")
        print(f"Child state cards placed: {child.state.player_arrangement.cards_placed}")


def test_evaluator():
    """Test state evaluator."""
    print("\n\n=== Testing Evaluator ===")
    
    evaluator = StateEvaluator()
    
    # Test empty state
    game = GameState(num_players=2, player_index=0)
    score = evaluator.evaluate_state(game)
    print(f"Empty state score: {score:.2f}")
    
    # Test with some cards
    game.deal_street()
    score = evaluator.evaluate_state(game)
    print(f"With dealt cards score: {score:.2f}")


def test_action_generation():
    """Test action generation."""
    print("\n\n=== Testing Action Generation ===")
    
    from src.core.algorithms.action_generator import ActionGenerator
    
    gen = ActionGenerator()
    
    # Test initial street
    game = GameState(num_players=2, player_index=0, seed=123)
    cards = game.deal_street()
    print(f"Initial cards: {' '.join(str(c) for c in cards)}")
    
    actions = gen.generate_actions(game)
    print(f"Generated {len(actions)} actions")
    
    if actions:
        print("\nFirst few actions:")
        for i, action in enumerate(actions[:3]):
            print(f"\nAction {i+1}:")
            for card, pos, idx in action.placements:
                print(f"  Place {card} at {pos}[{idx}]")


def test_simple_search():
    """Test simple MCTS search."""
    print("\n\n=== Testing Simple Search ===")
    
    from src.core.algorithms.ofc_mcts import MCTSEngine, MCTSConfig
    
    # Create simple config
    config = MCTSConfig(
        num_simulations=10,  # Very few for testing
        num_threads=1,
        progressive_widening=False  # Disable for simplicity
    )
    
    engine = MCTSEngine(config)
    
    # Create game
    game = GameState(num_players=2, player_index=0, seed=456)
    game.deal_street()
    
    print(f"Running {config.num_simulations} simulations...")
    
    try:
        best_action = engine.search(game)
        print("Search completed!")
        
        if best_action:
            print("\nBest action found:")
            for card, pos, idx in best_action.placements:
                print(f"  Place {card} at {pos}[{idx}]")
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    test_basic_mcts_node()
    test_evaluator()
    test_action_generation()
    test_simple_search()


if __name__ == "__main__":
    main()