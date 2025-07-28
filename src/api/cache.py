"""
Simple memory-based cache and task manager for development.
Can be replaced with Redis in production.
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading
import uuid


class MemoryCache:
    """In-memory cache implementation that mimics Redis interface."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        with self._lock:
            if key in self._expiry and self._expiry[key] < time.time():
                del self._data[key]
                del self._expiry[key]
                return None
            return self._data.get(key)
    
    def set(self, key: str, value: str, ex: Optional[int] = None):
        """Set key-value pair with optional expiry."""
        with self._lock:
            self._data[key] = value
            if ex:
                self._expiry[key] = time.time() + ex
    
    def setex(self, key: str, seconds: int, value: str):
        """Set key-value pair with expiry in seconds."""
        self.set(key, value, ex=seconds)
    
    def delete(self, key: str):
        """Delete a key."""
        with self._lock:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.get(key) is not None
    
    def expire(self, key: str, seconds: int):
        """Set expiry for a key."""
        with self._lock:
            if key in self._data:
                self._expiry[key] = time.time() + seconds
    
    def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        with self._lock:
            if key not in self._expiry:
                return -1
            ttl = int(self._expiry[key] - time.time())
            return max(0, ttl)
    
    def hset(self, name: str, key: str, value: str):
        """Set hash field."""
        with self._lock:
            if name not in self._data:
                self._data[name] = {}
            self._data[name][key] = value
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field."""
        with self._lock:
            if name in self._data and isinstance(self._data[name], dict):
                return self._data[name].get(key)
            return None
    
    def hgetall(self, name: str) -> Dict[bytes, bytes]:
        """Get all hash fields."""
        with self._lock:
            if name in self._data and isinstance(self._data[name], dict):
                # Return as bytes to match Redis behavior
                return {k.encode(): v.encode() for k, v in self._data[name].items()}
            return {}
    
    def hincrby(self, name: str, key: str, amount: int = 1):
        """Increment hash field by amount."""
        with self._lock:
            if name not in self._data:
                self._data[name] = {}
            current = int(self._data[name].get(key, 0))
            self._data[name][key] = str(current + amount)
    
    def lpush(self, name: str, *values):
        """Push values to the left of list."""
        with self._lock:
            if name not in self._data:
                self._data[name] = []
            for value in reversed(values):
                self._data[name].insert(0, value)
    
    def rpush(self, name: str, *values):
        """Push values to the right of list."""
        with self._lock:
            if name not in self._data:
                self._data[name] = []
            self._data[name].extend(values)
    
    def llen(self, name: str) -> int:
        """Get length of list."""
        with self._lock:
            if name in self._data and isinstance(self._data[name], list):
                return len(self._data[name])
            return 0
    
    def lpop(self, name: str) -> Optional[str]:
        """Pop from left of list."""
        with self._lock:
            if name in self._data and isinstance(self._data[name], list) and self._data[name]:
                return self._data[name].pop(0)
            return None
    
    def zadd(self, name: str, mapping: Dict[str, float]):
        """Add to sorted set."""
        with self._lock:
            if name not in self._data:
                self._data[name] = {}
            self._data[name].update(mapping)
    
    def zremrangebyscore(self, name: str, min_score: float, max_score: float):
        """Remove sorted set members by score range."""
        with self._lock:
            if name in self._data and isinstance(self._data[name], dict):
                to_remove = [k for k, v in self._data[name].items() 
                           if min_score <= v <= max_score]
                for k in to_remove:
                    del self._data[name][k]
    
    def zcount(self, name: str, min_score: float, max_score: float) -> int:
        """Count sorted set members by score range."""
        with self._lock:
            if name in self._data and isinstance(self._data[name], dict):
                return sum(1 for v in self._data[name].values() 
                          if min_score <= v <= max_score)
            return 0
    
    def pipeline(self):
        """Create a pipeline (simplified version)."""
        return MemoryPipeline(self)
    
    def ping(self) -> bool:
        """Ping to check if cache is alive."""
        return True
    
    def close(self):
        """Close cache connection (no-op for memory cache)."""
        pass


class MemoryPipeline:
    """Simplified pipeline for memory cache."""
    
    def __init__(self, cache: MemoryCache):
        self.cache = cache
        self.commands = []
    
    def zremrangebyscore(self, name: str, min_score: float, max_score: float):
        self.commands.append(('zremrangebyscore', name, min_score, max_score))
        return self
    
    def zadd(self, name: str, mapping: Dict[str, float]):
        self.commands.append(('zadd', name, mapping))
        return self
    
    def zcount(self, name: str, min_score: float, max_score: float):
        self.commands.append(('zcount', name, min_score, max_score))
        return self
    
    def expire(self, name: str, seconds: int):
        self.commands.append(('expire', name, seconds))
        return self
    
    def execute(self) -> List[Any]:
        """Execute all commands and return results."""
        results = []
        for cmd in self.commands:
            method_name = cmd[0]
            args = cmd[1:]
            method = getattr(self.cache, method_name)
            result = method(*args)
            results.append(result)
        return results


def get_cache_client() -> MemoryCache:
    """Get cache client instance."""
    # In production, this would return a Redis client
    # For now, return memory cache
    return MemoryCache()


class SimpleTaskQueue:
    """Simple in-memory task queue for development."""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.queue: List[str] = []
        self.lock = threading.Lock()
    
    async def create_task(self, task_type: str, task_data: Dict[str, Any], 
                         priority: str = "normal") -> str:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "type": task_type,
            "data": task_data,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with self.lock:
            self.tasks[task_id] = task
            if priority == "high":
                self.queue.insert(0, task_id)
            else:
                self.queue.append(task_id)
        
        # Start processing in background
        asyncio.create_task(self._process_task(task_id))
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        with self.lock:
            return self.tasks.get(task_id)
    
    async def update_task_status(self, task_id: str, status: str, 
                               result: Optional[Dict[str, Any]] = None,
                               error: Optional[Dict[str, Any]] = None,
                               progress: Optional[int] = None):
        """Update task status."""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task["status"] = status
                task["updated_at"] = datetime.utcnow().isoformat()
                
                if result:
                    task["result"] = result
                if error:
                    task["error"] = error
                if progress is not None:
                    task["progress"] = progress
                
                if status in ["completed", "failed"]:
                    task["completed_at"] = datetime.utcnow().isoformat()
    
    async def _process_task(self, task_id: str):
        """Simulate task processing."""
        # Wait a bit to simulate processing
        await asyncio.sleep(2)
        
        # Update status to processing
        await self.update_task_status(task_id, "processing", progress=50)
        
        # Simulate more processing
        await asyncio.sleep(3)
        
        # Complete the task with a mock result
        result = {
            "best_move": {
                "card_placements": [
                    {"card": {"rank": "A", "suit": "s"}, "hand": "top"}
                ],
                "is_fold": False
            },
            "evaluation": 42.5,
            "confidence": 0.95,
            "statistics": {
                "total_iterations": 50000,
                "nodes_visited": 125000,
                "average_depth": 12.5
            },
            "computation_time": 5.0
        }
        
        await self.update_task_status(task_id, "completed", result=result)