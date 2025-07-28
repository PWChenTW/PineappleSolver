#!/usr/bin/env python3
"""
Test script to verify API and MCTS integration.
"""

import requests
import json
import time
import sys

API_URL = "http://localhost:8000"
API_KEY = "test_key"


def test_health_check():
    """Test API health check."""
    print("Testing API health check...")
    try:
        response = requests.get(f"{API_URL}/api/v1/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            data = response.json()
            print(f"   Version: {data['version']}")
            print(f"   Status: {data['status']}")
            print(f"   Components: {', '.join(data['components'].keys())}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False


def test_initial_placement():
    """Test solving initial 5-card placement."""
    print("\nTesting initial 5-card placement...")
    
    # Create test request in GUI format
    request_data = {
        "game_state": {
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
            "remaining_deck": []
        },
        "options": {
            "time_limit": 5,
            "threads": 2,
            "simulations": 10000
        }
    }
    
    cards = request_data['game_state']['drawn_cards']
    cards_str = ', '.join(f"{c['rank']}{c['suit']}" for c in cards)
    print(f"Cards to place: {cards_str}")
    
    try:
        # Send request
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        response = requests.post(
            f"{API_URL}/api/v1/solve",
            json=request_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Solve completed successfully!")
            
            # Display results
            if 'best_move' in result and result['best_move']['card_placements']:
                print("\nBest placement:")
                for placement in result['best_move']['card_placements']:
                    card = placement['card']
                    hand = placement['hand']
                    print(f"  {card['rank']}{card['suit']} → {hand}")
                
                print(f"\nExpected score: {result.get('evaluation', 0):.2f}")
                print(f"Confidence: {result.get('confidence', 0):.2%}")
                print(f"Computation time: {result.get('computation_time', 0):.2f}s")
                
                # Check statistics
                if 'statistics' in result:
                    stats = result['statistics']
                    print(f"Total iterations: {stats.get('total_iterations', 0):,}")
            else:
                print("❌ No placements returned!")
                print(f"Response: {json.dumps(result, indent=2)}")
                return False
            
            return True
        else:
            print(f"❌ Solve failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_api_format():
    """Test with standard API format."""
    print("\nTesting standard API format...")
    
    request_data = {
        "game_state": {
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
                {"rank": "9", "suit": "h"},
                {"rank": "8", "suit": "d"},
                {"rank": "7", "suit": "c"},
                {"rank": "6", "suit": "s"},
                {"rank": "5", "suit": "h"}
            ]
        },
        "options": {
            "time_limit": 3,
            "threads": 1
        }
    }
    
    try:
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        response = requests.post(
            f"{API_URL}/api/v1/solve",
            json=request_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Standard API format works!")
            return True
        else:
            print(f"❌ API format failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """Run all tests."""
    print("OFC Solver API Integration Test")
    print("=" * 50)
    
    # Check if API is running
    if not test_health_check():
        print("\n❌ API is not running. Please start it with: python run_api.py")
        sys.exit(1)
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    if test_initial_placement():
        tests_passed += 1
    
    if test_api_format():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n✅ All tests passed! MCTS integration is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()