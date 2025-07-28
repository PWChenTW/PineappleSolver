#!/usr/bin/env python3
"""
Quick start example for OFC Solver API.

Shows simplified input formats and common use cases.
"""

import httpx
import asyncio
import json

# API configuration
API_URL = "http://localhost:8000"
API_KEY = "test_key"  # Replace with your actual API key


async def example_simple_solve():
    """Example: Simple solve with minimal input."""
    print("=== Simple Solve Example ===\n")
    
    # Simplified game state - just the essentials
    game_state = {
        "current_round": 1,
        "players": [
            {
                "player_id": "me",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5}
            }
        ],
        "current_player_index": 0,
        "remaining_deck": [
            {"rank": "A", "suit": "s"},  # Ace of spades
            {"rank": "K", "suit": "h"},  # King of hearts
            {"rank": "Q", "suit": "d"},  # Queen of diamonds
            {"rank": "J", "suit": "c"},  # Jack of clubs
            {"rank": "T", "suit": "s"}   # Ten of spades
        ]
    }
    
    request = {
        "game_state": game_state,
        "options": {
            "time_limit": 5  # 5 seconds to find best move
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/v1/solve",
            json=request,
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Best move found in {result['computation_time']:.2f} seconds:")
            for placement in result['best_move']['card_placements']:
                card = placement['card']
                hand = placement['hand']
                print(f"  Place {card['rank']}{card['suit']} in {hand}")
            print(f"\nExpected score: {result['evaluation']:.2f}")
            print(f"Confidence: {result['confidence']:.2%}")
        else:
            print(f"Error: {response.text}")


async def example_mid_game_analysis():
    """Example: Analyze a mid-game position."""
    print("\n=== Mid-Game Analysis Example ===\n")
    
    # Mid-game state with some cards already placed
    game_state = {
        "current_round": 7,
        "players": [
            {
                "player_id": "me",
                "top_hand": {
                    "cards": [
                        {"rank": "K", "suit": "s"},
                        {"rank": "K", "suit": "h"}
                    ],
                    "max_size": 3
                },
                "middle_hand": {
                    "cards": [
                        {"rank": "9", "suit": "s"},
                        {"rank": "8", "suit": "s"},
                        {"rank": "7", "suit": "s"}
                    ],
                    "max_size": 5
                },
                "bottom_hand": {
                    "cards": [
                        {"rank": "A", "suit": "d"},
                        {"rank": "A", "suit": "c"}
                    ],
                    "max_size": 5
                }
            }
        ],
        "current_player_index": 0,
        "remaining_deck": [
            {"rank": "6", "suit": "s"},  # Could complete straight flush!
            {"rank": "K", "suit": "d"}   # Could make trips in top
        ]
    }
    
    request = {
        "game_state": game_state,
        "options": {
            "include_alternatives": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/v1/analyze",
            json=request,
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Position Analysis:")
            print(f"  Overall evaluation: {result['evaluation']:.2f}")
            print(f"  Fantasy land chance: {result['fantasy_land_probability']:.1%}")
            print(f"  Foul risk: {result['foul_probability']:.1%}")
            
            print("\nHand strengths:")
            for hand, strength in result['hand_strengths'].items():
                print(f"  {hand}: {strength['current_rank']} "
                      f"(strength: {strength['current_strength']:.2f})")
            
            print("\nRecommendations:")
            for i, rec in enumerate(result['recommendations'][:3], 1):
                print(f"  {i}. {rec['reasoning']}")
        else:
            print(f"Error: {response.text}")


async def example_async_solve():
    """Example: Async solve for longer computations."""
    print("\n=== Async Solve Example ===\n")
    
    # Complex position that needs more computation time
    game_state = {
        "current_round": 10,
        "players": [
            {
                "player_id": "me",
                "top_hand": {
                    "cards": [{"rank": "Q", "suit": "s"}],
                    "max_size": 3
                },
                "middle_hand": {
                    "cards": [
                        {"rank": "J", "suit": "h"},
                        {"rank": "T", "suit": "h"},
                        {"rank": "9", "suit": "h"}
                    ],
                    "max_size": 5
                },
                "bottom_hand": {
                    "cards": [
                        {"rank": "A", "suit": "s"},
                        {"rank": "K", "suit": "s"},
                        {"rank": "J", "suit": "s"}
                    ],
                    "max_size": 5
                }
            }
        ],
        "current_player_index": 0,
        "remaining_deck": [
            {"rank": "Q", "suit": "h"},
            {"rank": "8", "suit": "h"},
            {"rank": "T", "suit": "s"}
        ]
    }
    
    request = {
        "game_state": game_state,
        "async": True,  # Request async processing
        "options": {
            "time_limit": 30,  # Give it more time
            "threads": 4       # Use more threads
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Submit async task
        response = await client.post(
            f"{API_URL}/api/v1/solve",
            json=request,
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code == 200:
            task_info = response.json()
            task_id = task_info['task_id']
            print(f"Task submitted: {task_id}")
            print("Processing... ", end="", flush=True)
            
            # Poll for result
            for i in range(10):  # Try for up to 10 seconds
                await asyncio.sleep(1)
                print(".", end="", flush=True)
                
                status_response = await client.get(
                    f"{API_URL}/api/v1/tasks/{task_id}",
                    headers={"X-API-Key": API_KEY}
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    if status['status'] == 'completed':
                        print(" Done!")
                        result = status['result']
                        print(f"\nBest move:")
                        for placement in result['best_move']['card_placements']:
                            card = placement['card']
                            hand = placement['hand']
                            print(f"  Place {card['rank']}{card['suit']} in {hand}")
                        break
                    elif status['status'] == 'failed':
                        print(" Failed!")
                        print(f"Error: {status.get('error', 'Unknown error')}")
                        break
            else:
                print(" Timeout!")
        else:
            print(f"Error: {response.text}")


async def example_card_shortcuts():
    """Example: Using card notation shortcuts."""
    print("\n=== Card Notation Examples ===\n")
    
    print("Standard card notation:")
    print("  Ranks: 2-9, T (ten), J (jack), Q (queen), K (king), A (ace)")
    print("  Suits: s (spades ♠), h (hearts ♥), d (diamonds ♦), c (clubs ♣)")
    print("\nExamples:")
    print("  As = Ace of spades")
    print("  Kh = King of hearts")
    print("  Td = Ten of diamonds")
    print("  9c = Nine of clubs")
    
    # You can also create a helper function for easier card creation
    def card(notation):
        """Convert string notation to card object. E.g., 'As' -> {'rank': 'A', 'suit': 's'}"""
        if len(notation) == 2:
            return {"rank": notation[0], "suit": notation[1]}
        raise ValueError(f"Invalid card notation: {notation}")
    
    # Example usage
    game_state = {
        "current_round": 1,
        "players": [{
            "player_id": "me",
            "top_hand": {"cards": [], "max_size": 3},
            "middle_hand": {"cards": [], "max_size": 5},
            "bottom_hand": {"cards": [], "max_size": 5}
        }],
        "current_player_index": 0,
        "remaining_deck": [
            card("As"), card("Ks"), card("Qs"), card("Js"), card("Ts")
        ]
    }
    
    print("\nCreated royal flush cards:", game_state["remaining_deck"])


async def main():
    """Run all examples."""
    print("""
    ╔═══════════════════════════════════════════╗
    ║     OFC Solver API - Quick Start          ║
    ╚═══════════════════════════════════════════╝
    
    Make sure the API server is running:
    $ python run_api.py
    
    """)
    
    # Check if API is available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/api/v1/health")
            if response.status_code != 200:
                print("❌ API server is not healthy")
                return
    except httpx.ConnectError:
        print("❌ Cannot connect to API server at", API_URL)
        print("Please start the server with: python run_api.py")
        return
    
    # Run examples
    await example_simple_solve()
    await example_mid_game_analysis()
    await example_async_solve()
    await example_card_shortcuts()
    
    print("\n✅ All examples completed!")
    print("\nFor more details, see the API documentation at:")
    print(f"  {API_URL}/docs")


if __name__ == "__main__":
    asyncio.run(main())