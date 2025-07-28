#!/usr/bin/env python3
"""
Fixed test script for OFC Solver API endpoints with proper 2-player game states.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any
import httpx
from datetime import datetime
import uuid

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# API configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "test_key"  # This should match your configured test key


async def test_health_check():
    """Test the health check endpoint."""
    print("\n=== Testing Health Check ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v1/health")
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service Status: {data['status']}")
            print(f"Version: {data['version']}")
            print(f"Components: {json.dumps(data['components'], indent=2)}")
        else:
            print(f"Error: {response.text}")


async def test_solve_sync():
    """Test synchronous solve endpoint."""
    print("\n=== Testing Synchronous Solve ===")
    
    # Sample game state with 2 players
    game_state = {
        "current_round": 1,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            },
            {
                "player_id": "player2",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "drawn_cards": [
            {"rank": "A", "suit": "s"},
            {"rank": "K", "suit": "h"},
            {"rank": "Q", "suit": "d"},
            {"rank": "J", "suit": "c"},
            {"rank": "T", "suit": "s"}
        ],
        "remaining_cards": 47,
        "is_complete": False
    }
    
    request_data = {
        "game_state": game_state,
        "options": {
            "time_limit": 10.0,
            "threads": 2,
            "simulations": 10000
        }
    }
    
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json=request_data,
            headers=headers,
            timeout=20.0
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Best Move: {json.dumps(data['move'], indent=2)}")
            print(f"Evaluation: {data['evaluation']}")
            print(f"Confidence: {data['confidence']}")
            print(f"Computation Time: {data['computation_time_seconds']}s")
        else:
            print(f"Error: {response.text}")


async def test_solve_async():
    """Test asynchronous solve endpoint."""
    print("\n=== Testing Asynchronous Solve ===")
    
    # Same game state with 2 players
    game_state = {
        "current_round": 5,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            },
            {
                "player_id": "player2",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "drawn_cards": [
            {"rank": "9", "suit": "h"}
        ],
        "remaining_cards": 35,
        "is_complete": False
    }
    
    request_data = {
        "game_state": game_state,
        "options": {
            "time_limit": 30.0,
            "threads": 4,
            "async": True
        }
    }
    
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        # Submit task
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json=request_data,
            headers=headers
        )
        
        print(f"Submit Status: {response.status_code}")
        if response.status_code == 202:
            data = response.json()
            task_id = data['task_id']
            print(f"Task ID: {task_id}")
            print(f"Message: {data['message']}")
            
            # Wait a bit and check status
            await asyncio.sleep(2)
            
            status_response = await client.get(
                f"{API_BASE_URL}/api/v1/solve/{task_id}",
                headers=headers
            )
            
            print(f"\nStatus Check: {status_response.status_code}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Task Status: {status_data}")
        else:
            print(f"Error: {response.text}")


async def test_analyze():
    """Test position analysis endpoint."""
    print("\n=== Testing Position Analysis ===")
    
    # Position with some cards already placed - 2 players
    game_state = {
        "current_round": 5,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {
                    "cards": [
                        {"rank": "A", "suit": "s"},
                        {"rank": "A", "suit": "h"}
                    ],
                    "max_size": 3
                },
                "middle_hand": {
                    "cards": [
                        {"rank": "K", "suit": "s"},
                        {"rank": "Q", "suit": "s"},
                        {"rank": "J", "suit": "s"}
                    ],
                    "max_size": 5
                },
                "bottom_hand": {
                    "cards": [
                        {"rank": "9", "suit": "d"},
                        {"rank": "9", "suit": "c"}
                    ],
                    "max_size": 5
                },
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            },
            {
                "player_id": "player2",
                "top_hand": {
                    "cards": [
                        {"rank": "K", "suit": "d"},
                        {"rank": "K", "suit": "c"}
                    ],
                    "max_size": 3
                },
                "middle_hand": {
                    "cards": [
                        {"rank": "T", "suit": "h"},
                        {"rank": "9", "suit": "h"},
                        {"rank": "8", "suit": "h"}
                    ],
                    "max_size": 5
                },
                "bottom_hand": {
                    "cards": [
                        {"rank": "7", "suit": "s"},
                        {"rank": "6", "suit": "s"}
                    ],
                    "max_size": 5
                },
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "drawn_cards": [],
        "remaining_cards": 32,
        "is_complete": False
    }
    
    request_data = {"game_state": game_state}
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/analyze",
            json=request_data,
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Position Strength: {data['position_strength']}")
            print(f"Fantasy Land Probability: {data['fantasy_land_probability']}")
            print(f"Foul Risk: {data['foul_risk']}")
            print(f"Hand Rankings: {json.dumps(data['hand_rankings'], indent=2)}")
            print(f"Recommendations: {json.dumps(data['recommendations'], indent=2)}")
        else:
            print(f"Error: {response.text}")


async def test_batch():
    """Test batch processing endpoint."""
    print("\n=== Testing Batch Processing ===")
    
    # Create 3 different positions - all with 2 players
    positions = []
    for i in range(3):
        positions.append({
            "position_id": f"pos_{i}",
            "game_state": {
                "current_round": 1,
                "players": [
                    {
                        "player_id": f"player{i}_1",
                        "top_hand": {"cards": [], "max_size": 3},
                        "middle_hand": {"cards": [], "max_size": 5},
                        "bottom_hand": {"cards": [], "max_size": 5},
                        "in_fantasy_land": False,
                        "next_fantasy_land": False,
                        "is_folded": False
                    },
                    {
                        "player_id": f"player{i}_2",
                        "top_hand": {"cards": [], "max_size": 3},
                        "middle_hand": {"cards": [], "max_size": 5},
                        "bottom_hand": {"cards": [], "max_size": 5},
                        "in_fantasy_land": False,
                        "next_fantasy_land": False,
                        "is_folded": False
                    }
                ],
                "current_player_index": 0,
                "drawn_cards": [
                    {"rank": ["A", "K", "Q"][i], "suit": "s"},
                    {"rank": ["K", "Q", "J"][i], "suit": "h"},
                    {"rank": ["Q", "J", "T"][i], "suit": "d"},
                    {"rank": ["J", "T", "9"][i], "suit": "c"},
                    {"rank": ["T", "9", "8"][i], "suit": "s"}
                ],
                "remaining_cards": 47,
                "is_complete": False
            },
            "options": {
                "time_limit": 5.0,
                "threads": 2
            }
        })
    
    request_data = {
        "positions": positions,
        "async": False
    }
    
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/batch",
            json=request_data,
            headers=headers,
            timeout=30.0
        )
        
        print(f"Submit Status: {response.status_code}")
        if response.status_code in [200, 202]:
            data = response.json()
            if "results" in data:
                print(f"Batch Results: {len(data['results'])} positions processed")
                for result in data['results']:
                    print(f"\nPosition {result['position_id']}:")
                    print(f"  Status: {result['status']}")
                    if result['status'] == 'completed':
                        print(f"  Best Move: {result['result']['move']['card_placements'][0]}")
                        print(f"  Evaluation: {result['result']['evaluation']}")
            else:
                print(f"Batch ID: {data.get('batch_id')}")
                print(f"Message: {data.get('message')}")
        else:
            print(f"Error: {response.text}")


async def test_validation():
    """Test request validation."""
    print("\n=== Testing Request Validation ===")
    
    # Test 1: Invalid card count in hand (should be max 3 in top)
    print("\nTest 1: Too many cards in top hand")
    invalid_state = {
        "current_round": 1,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {
                    "cards": [
                        {"rank": "A", "suit": "s"},
                        {"rank": "K", "suit": "h"},
                        {"rank": "Q", "suit": "d"},
                        {"rank": "J", "suit": "c"}  # 4 cards - too many!
                    ],
                    "max_size": 3
                },
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            },
            {
                "player_id": "player2",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "drawn_cards": [],
        "remaining_cards": 52,
        "is_complete": False
    }
    
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json={"game_state": invalid_state},
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Error (expected): {response.text}")
    
    # Test 2: Missing required field
    print("\nTest 2: Missing required field")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json={},  # Missing game_state
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Error (expected): {response.text}")


async def test_simplified_input():
    """Test simplified input format."""
    print("\n=== Testing Simplified Input Format ===")
    
    # Using card notation helpers
    from src.api.input_helpers import card, cards, create_game_state
    
    # Create a simple game state
    game_state = create_game_state(
        drawn_cards=cards("As Kh Qd Jc Ts"),
        num_players=2
    )
    
    request_data = {
        "game_state": game_state,
        "options": {
            "time_limit": 5.0
        }
    }
    
    headers = {"X-API-Key": API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json=request_data,
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Simplified input format works!")
            print(f"Best Move: {data['move']['card_placements'][0]}")
        else:
            print(f"Error: {response.text}")


async def main():
    """Run all tests."""
    print("""
    ╔═══════════════════════════════════════════╗
    ║      OFC Solver API Test Suite            ║
    ╚═══════════════════════════════════════════╝
    """)
    
    # Check if API is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/health", timeout=2.0)
            if response.status_code != 200:
                print("❌ API server is not healthy")
                return
    except (httpx.ConnectError, httpx.TimeoutException):
        print("❌ Cannot connect to API server. Please start it with: python run_api.py")
        return
    
    # Run tests
    await test_health_check()
    await test_solve_sync()
    await test_solve_async()
    await test_analyze()
    await test_batch()
    await test_validation()
    await test_simplified_input()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())