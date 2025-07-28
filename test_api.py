#!/usr/bin/env python3
"""
Test script for OFC Solver API endpoints.
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
    
    # Sample game state
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
        "remaining_deck": [
            {"rank": "A", "suit": "s"},
            {"rank": "K", "suit": "h"},
            {"rank": "Q", "suit": "d"},
            {"rank": "J", "suit": "c"},
            {"rank": "T", "suit": "s"}
        ],
        "dealer_position": 0
    }
    
    request_data = {
        "game_state": game_state,
        "options": {
            "time_limit": 5.0,
            "threads": 2
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json=request_data,
            headers={"X-API-Key": API_KEY}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Best Move: {json.dumps(data['best_move'], indent=2)}")
            print(f"Evaluation: {data['evaluation']}")
            print(f"Confidence: {data['confidence']}")
            print(f"Computation Time: {data['computation_time']}s")
        else:
            print(f"Error: {response.text}")


async def test_solve_async():
    """Test asynchronous solve endpoint."""
    print("\n=== Testing Asynchronous Solve ===")
    
    # Sample game state (same as above)
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
            }
        ],
        "current_player_index": 0,
        "remaining_deck": [
            {"rank": "A", "suit": "s"},
            {"rank": "K", "suit": "h"}
        ],
        "dealer_position": 0
    }
    
    request_data = {
        "game_state": game_state,
        "async": True,  # Request async processing
        "options": {
            "time_limit": 10.0
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Submit async task
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json=request_data,
            headers={"X-API-Key": API_KEY}
        )
        
        print(f"Submit Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            task_id = data['task_id']
            print(f"Task ID: {task_id}")
            print(f"Status: {data['status']}")
            print(f"Status URL: {data['status_url']}")
            
            # Wait a bit and check status
            await asyncio.sleep(3)
            
            # Check task status
            print("\nChecking task status...")
            status_response = await client.get(
                f"{API_BASE_URL}/api/v1/tasks/{task_id}",
                headers={"X-API-Key": API_KEY}
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Task Status: {status_data['status']}")
                if status_data['status'] == 'completed' and status_data.get('result'):
                    print(f"Result: {json.dumps(status_data['result'], indent=2)}")
            else:
                print(f"Status Error: {status_response.text}")
        else:
            print(f"Error: {response.text}")


async def test_analyze():
    """Test analyze endpoint."""
    print("\n=== Testing Position Analysis ===")
    
    # Game state with some cards placed
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
            }
        ],
        "current_player_index": 0,
        "remaining_deck": [
            {"rank": "T", "suit": "s"},
            {"rank": "8", "suit": "h"}
        ],
        "dealer_position": 0
    }
    
    request_data = {
        "game_state": game_state,
        "options": {
            "depth": 3,
            "include_alternatives": True
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/analyze",
            json=request_data,
            headers={"X-API-Key": API_KEY}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Evaluation: {data['evaluation']}")
            print(f"Hand Strengths: {json.dumps(data['hand_strengths'], indent=2)}")
            print(f"Fantasy Land Probability: {data['fantasy_land_probability']}")
            print(f"Foul Probability: {data['foul_probability']}")
            if data.get('recommendations'):
                print("Recommendations:")
                for rec in data['recommendations']:
                    print(f"  - {rec['reasoning']} (Priority: {rec['priority']})")
        else:
            print(f"Error: {response.text}")


async def test_batch():
    """Test batch processing endpoint."""
    print("\n=== Testing Batch Processing ===")
    
    # Create multiple positions
    positions = []
    for i in range(3):
        game_state = {
            "current_round": i + 1,
            "players": [
                {
                    "player_id": f"player{i}",
                    "top_hand": {"cards": [], "max_size": 3},
                    "middle_hand": {"cards": [], "max_size": 5},
                    "bottom_hand": {"cards": [], "max_size": 5},
                    "in_fantasy_land": False,
                    "next_fantasy_land": False,
                    "is_folded": False
                }
            ],
            "current_player_index": 0,
            "remaining_deck": [
                {"rank": "A", "suit": "s"},
                {"rank": "K", "suit": "h"}
            ],
            "dealer_position": 0
        }
        
        positions.append({
            "id": f"position_{i}",
            "game_state": game_state,
            "options": {
                "time_limit": 5.0
            }
        })
    
    request_data = {
        "positions": positions,
        "batch_options": {
            "priority": "normal"
        }
    }
    
    async with httpx.AsyncClient() as client:
        # Submit batch job
        response = await client.post(
            f"{API_BASE_URL}/api/v1/batch",
            json=request_data,
            headers={"X-API-Key": API_KEY}
        )
        
        print(f"Submit Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            job_id = data['job_id']
            print(f"Job ID: {job_id}")
            print(f"Total Positions: {data['total_positions']}")
            print(f"Status URL: {data['status_url']}")
            
            # Wait a bit and check status
            await asyncio.sleep(5)
            
            # Check batch status
            print("\nChecking batch status...")
            status_response = await client.get(
                f"{API_BASE_URL}/api/v1/batch/{job_id}",
                headers={"X-API-Key": API_KEY}
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Batch Status: {status_data['status']}")
                print(f"Completed: {status_data['completed_positions']}/{status_data['total_positions']}")
                print(f"Failed: {status_data['failed_positions']}")
            else:
                print(f"Status Error: {status_response.text}")
        else:
            print(f"Error: {response.text}")


async def test_validation():
    """Test request validation with various invalid inputs."""
    print("\n=== Testing Request Validation ===")
    
    # Test 1: Invalid game state (too many cards in hand)
    print("\nTest 1: Too many cards in top hand")
    invalid_game_state = {
        "current_round": 1,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {
                    "cards": [
                        {"rank": "A", "suit": "s"},
                        {"rank": "K", "suit": "h"},
                        {"rank": "Q", "suit": "d"},
                        {"rank": "J", "suit": "c"}  # 4 cards, but max is 3
                    ],
                    "max_size": 3
                },
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "remaining_deck": [],
        "dealer_position": 0
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json={"game_state": invalid_game_state},
            headers={"X-API-Key": API_KEY}
        )
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error (expected): {response.text}")
        
        # Test 2: Missing required field
        print("\nTest 2: Missing required field")
        response = await client.post(
            f"{API_BASE_URL}/api/v1/solve",
            json={},  # Missing game_state
            headers={"X-API-Key": API_KEY}
        )
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error (expected): {response.text}")


async def main():
    """Run all tests."""
    print("""
    ╔═══════════════════════════════════════════╗
    ║      OFC Solver API Test Suite            ║
    ╚═══════════════════════════════════════════╝
    """)
    
    try:
        # Check if API is running
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{API_BASE_URL}/")
                if response.status_code != 200:
                    print("❌ API server is not running. Please start it with: python run_api.py")
                    return
            except httpx.ConnectError:
                print("❌ Cannot connect to API server. Please start it with: python run_api.py")
                return
        
        # Run tests
        await test_health_check()
        await test_solve_sync()
        await test_solve_async()
        await test_analyze()
        await test_batch()
        await test_validation()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())