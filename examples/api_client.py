"""
Example client for OFC Solver API.

This module demonstrates how to interact with the OFC Solver API
using Python requests library.
"""

import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class OFCSolverClient:
    """Client for OFC Solver API."""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API (e.g., https://api.ofcsolver.com)
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                # Retry the request
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Error response: {e.response.text}")
            raise
    
    def solve(
        self,
        game_state: Dict[str, Any],
        time_limit: float = 30,
        threads: int = 4,
        async_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Solve an OFC position.
        
        Args:
            game_state: Current game state
            time_limit: Time limit for solving in seconds
            threads: Number of threads to use
            async_mode: Whether to use async processing
            
        Returns:
            Solution result or async task info
        """
        data = {
            "game_state": game_state,
            "options": {
                "time_limit": time_limit,
                "threads": threads
            },
            "async": async_mode
        }
        
        return self._make_request("POST", "/api/v1/solve", data=data)
    
    def analyze(
        self,
        game_state: Dict[str, Any],
        depth: int = 3,
        include_alternatives: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze an OFC position without deep search.
        
        Args:
            game_state: Current game state
            depth: Analysis depth
            include_alternatives: Whether to include alternative moves
            
        Returns:
            Position analysis
        """
        data = {
            "game_state": game_state,
            "options": {
                "depth": depth,
                "include_alternatives": include_alternatives
            }
        }
        
        return self._make_request("POST", "/api/v1/analyze", data=data)
    
    def batch_solve(
        self,
        positions: List[Dict[str, Any]],
        priority: str = "normal",
        notification_webhook: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit multiple positions for batch solving.
        
        Args:
            positions: List of positions to solve
            priority: Job priority (low, normal, high)
            notification_webhook: Optional webhook for completion notification
            
        Returns:
            Batch job info
        """
        batch_positions = []
        for i, pos in enumerate(positions):
            batch_positions.append({
                "id": f"pos_{i}",
                "game_state": pos["game_state"],
                "options": pos.get("options", {})
            })
        
        data = {
            "positions": batch_positions,
            "batch_options": {
                "priority": priority
            }
        }
        
        if notification_webhook:
            data["batch_options"]["notification_webhook"] = notification_webhook
        
        return self._make_request("POST", "/api/v1/batch", data=data)
    
    def get_batch_status(self, job_id: str) -> Dict[str, Any]:
        """Get batch job status."""
        return self._make_request("GET", f"/api/v1/batch/{job_id}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get async task status."""
        return self._make_request("GET", f"/api/v1/tasks/{task_id}")
    
    def wait_for_task(self, task_id: str, poll_interval: int = 2) -> Dict[str, Any]:
        """
        Wait for async task to complete.
        
        Args:
            task_id: Task ID to wait for
            poll_interval: Polling interval in seconds
            
        Returns:
            Task result
        """
        while True:
            status = self.get_task_status(task_id)
            
            if status["status"] == "completed":
                return status["result"]
            elif status["status"] == "failed":
                raise Exception(f"Task failed: {status.get('error', 'Unknown error')}")
            
            print(f"Task {task_id} status: {status['status']}"
                  f" (progress: {status.get('progress', 0)}%)")
            time.sleep(poll_interval)
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._make_request("GET", "/api/v1/health")


# Example usage
def main():
    """Example usage of the OFC Solver client."""
    # Initialize client
    client = OFCSolverClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    # Check health
    print("Checking API health...")
    health = client.health_check()
    print(f"API Status: {health['status']}")
    print(f"Version: {health['version']}")
    
    # Example game state
    game_state = {
        "current_round": 5,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {
                    "cards": [
                        {"rank": "K", "suit": "h"},
                        {"rank": "K", "suit": "d"}
                    ],
                    "max_size": 3
                },
                "middle_hand": {
                    "cards": [
                        {"rank": "9", "suit": "s"},
                        {"rank": "9", "suit": "c"},
                        {"rank": "8", "suit": "h"}
                    ],
                    "max_size": 5
                },
                "bottom_hand": {
                    "cards": [
                        {"rank": "A", "suit": "s"},
                        {"rank": "A", "suit": "c"},
                        {"rank": "Q", "suit": "s"},
                        {"rank": "Q", "suit": "c"}
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
                        {"rank": "J", "suit": "h"},
                        {"rank": "J", "suit": "d"}
                    ],
                    "max_size": 3
                },
                "middle_hand": {
                    "cards": [
                        {"rank": "T", "suit": "s"},
                        {"rank": "T", "suit": "c"},
                        {"rank": "7", "suit": "h"}
                    ],
                    "max_size": 5
                },
                "bottom_hand": {
                    "cards": [
                        {"rank": "K", "suit": "s"},
                        {"rank": "K", "suit": "c"},
                        {"rank": "J", "suit": "s"},
                        {"rank": "J", "suit": "c"}
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
            {"rank": "2", "suit": "h"},
            {"rank": "3", "suit": "d"},
            {"rank": "4", "suit": "s"},
            # ... more cards
        ],
        "dealer_position": 0
    }
    
    # Quick analysis
    print("\nAnalyzing position...")
    analysis = client.analyze(game_state)
    print(f"Evaluation: {analysis['evaluation']}")
    print(f"Fantasy Land Probability: {analysis['fantasy_land_probability']:.2%}")
    print(f"Foul Probability: {analysis['foul_probability']:.2%}")
    
    print("\nRecommendations:")
    for rec in analysis['recommendations'][:3]:
        print(f"- {rec['reasoning']} (Priority: {rec['priority']})")
    
    # Solve position (sync)
    print("\nSolving position...")
    start_time = time.time()
    result = client.solve(game_state, time_limit=10, threads=4)
    solve_time = time.time() - start_time
    
    print(f"Best move found in {solve_time:.2f} seconds:")
    print(f"Evaluation: {result['evaluation']}")
    print(f"Confidence: {result['confidence']:.2%}")
    
    print("\nCard placements:")
    for placement in result['best_move']['card_placements']:
        card = placement['card']
        hand = placement['hand']
        print(f"- {card['rank']}{card['suit']} → {hand}")
    
    print(f"\nStatistics:")
    stats = result['statistics']
    print(f"- Iterations: {stats['total_iterations']:,}")
    print(f"- Nodes visited: {stats['nodes_visited']:,}")
    print(f"- Average depth: {stats['average_depth']:.1f}")
    
    # Async solve example
    print("\nStarting async solve...")
    async_result = client.solve(game_state, time_limit=60, async_mode=True)
    task_id = async_result['task_id']
    print(f"Task ID: {task_id}")
    print(f"Status URL: {async_result['status_url']}")
    
    # Wait for completion
    print("\nWaiting for task completion...")
    final_result = client.wait_for_task(task_id)
    print(f"Async solve completed!")
    print(f"Evaluation: {final_result['evaluation']}")
    
    # Batch solve example
    print("\nSubmitting batch job...")
    positions = [
        {"game_state": game_state, "options": {"time_limit": 10}},
        {"game_state": game_state, "options": {"time_limit": 20}},
    ]
    
    batch_job = client.batch_solve(positions, priority="high")
    job_id = batch_job['job_id']
    print(f"Batch job ID: {job_id}")
    
    # Check batch status
    print("\nChecking batch status...")
    while True:
        status = client.get_batch_status(job_id)
        print(f"Status: {status['status']}")
        print(f"Completed: {status['completed_positions']}/{status['total_positions']}")
        
        if status['status'] == 'completed':
            print("\nBatch results:")
            for result in status['results']:
                print(f"- Position {result['position_id']}: {result['status']}")
            break
        
        time.sleep(2)


if __name__ == "__main__":
    main()