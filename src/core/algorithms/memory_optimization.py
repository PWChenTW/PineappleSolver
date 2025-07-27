"""
OFC Solver內存優化實現

包含：
1. 對象池管理
2. 緊湊數據結構
3. 緩存策略
4. 內存監控和回收
"""

import gc
import weakref
import sys
from typing import TypeVar, Generic, List, Dict, Optional, Any, Callable
from collections import OrderedDict, deque
from dataclasses import dataclass
import numpy as np
import threading
import time
import psutil
import os


T = TypeVar('T')


class ObjectPool(Generic[T]):
    """通用對象池實現
    
    特性：
    - 線程安全
    - 自動擴容和收縮
    - 對象生命週期管理
    """
    
    def __init__(self, 
                 factory: Callable[[], T],
                 reset_func: Callable[[T], None],
                 initial_size: int = 100,
                 max_size: int = 10000):
        """
        參數:
            factory: 創建新對象的工廠函數
            reset_func: 重置對象狀態的函數
            initial_size: 初始池大小
            max_size: 最大池大小
        """
        self.factory = factory
        self.reset_func = reset_func
        self.max_size = max_size
        
        self._pool: deque[T] = deque()
        self._in_use: weakref.WeakSet[T] = weakref.WeakSet()
        self._lock = threading.RLock()
        
        # 統計信息
        self.stats = {
            'created': 0,
            'reused': 0,
            'peak_usage': 0
        }
        
        # 預創建對象
        self._expand_pool(initial_size)
    
    def acquire(self) -> T:
        """獲取對象"""
        with self._lock:
            if self._pool:
                obj = self._pool.popleft()
                self.stats['reused'] += 1
            else:
                obj = self.factory()
                self.stats['created'] += 1
            
            self._in_use.add(obj)
            self.stats['peak_usage'] = max(self.stats['peak_usage'], len(self._in_use))
            
            return obj
    
    def release(self, obj: T):
        """釋放對象回池"""
        with self._lock:
            if obj not in self._in_use:
                return  # 對象不是從池中獲取的
            
            self._in_use.discard(obj)
            
            if len(self._pool) < self.max_size:
                self.reset_func(obj)
                self._pool.append(obj)
            # 否則讓對象被垃圾回收
    
    def _expand_pool(self, size: int):
        """擴展對象池"""
        for _ in range(size):
            obj = self.factory()
            self.reset_func(obj)
            self._pool.append(obj)
            self.stats['created'] += 1
    
    def shrink(self, target_size: Optional[int] = None):
        """收縮對象池"""
        with self._lock:
            if target_size is None:
                target_size = len(self._in_use) * 2  # 保留使用中數量的兩倍
            
            while len(self._pool) > target_size and self._pool:
                self._pool.popleft()
    
    def clear(self):
        """清空對象池"""
        with self._lock:
            self._pool.clear()
            # in_use對象會在釋放時被處理


@dataclass
class CompactGameState:
    """緊湊的遊戲狀態表示
    
    使用位運算和numpy數組最小化內存使用
    """
    # 使用uint8數組存儲牌的位置（0-12表示13個位置，255表示未放置）
    card_positions: np.ndarray  # shape=(52,), dtype=uint8
    
    # 使用位掩碼表示哪些牌已經被放置
    placed_mask: int  # 52位整數
    
    # 當前玩家（0或1）
    current_player: int
    
    # 回合數
    turn: int
    
    def __init__(self):
        self.card_positions = np.full(52, 255, dtype=np.uint8)
        self.placed_mask = 0
        self.current_player = 0
        self.turn = 0
    
    def place_card(self, card_id: int, position: int):
        """放置牌"""
        self.card_positions[card_id] = position
        self.placed_mask |= (1 << card_id)
        self.turn += 1
    
    def is_placed(self, card_id: int) -> bool:
        """檢查牌是否已放置"""
        return bool(self.placed_mask & (1 << card_id))
    
    def get_hand_cards(self, row: int) -> List[int]:
        """獲取某一行的牌"""
        if row == 0:  # top
            positions = range(0, 3)
        elif row == 1:  # middle
            positions = range(3, 8)
        else:  # bottom
            positions = range(8, 13)
        
        cards = []
        for i in range(52):
            if self.card_positions[i] in positions:
                cards.append(i)
        return cards
    
    def copy(self) -> 'CompactGameState':
        """快速複製"""
        new_state = CompactGameState()
        new_state.card_positions = self.card_positions.copy()
        new_state.placed_mask = self.placed_mask
        new_state.current_player = self.current_player
        new_state.turn = self.turn
        return new_state
    
    def hash(self) -> int:
        """計算狀態哈希"""
        # 使用Zobrist hashing會更高效，這裡簡化實現
        return hash((self.card_positions.tobytes(), self.placed_mask, self.current_player))


class LRUCache(Generic[T]):
    """最近最少使用緩存
    
    特性：
    - O(1)的get和put操作
    - 自動過期策略
    - 內存限制
    """
    
    def __init__(self, max_size: int = 10000, ttl: Optional[float] = None):
        """
        參數:
            max_size: 最大緩存項數
            ttl: 緩存項存活時間（秒），None表示不過期
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[Any, Tuple[T, float]] = OrderedDict()
        self._lock = threading.RLock()
        
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get(self, key: Any) -> Optional[T]:
        """獲取緩存項"""
        with self._lock:
            if key not in self.cache:
                self.stats['misses'] += 1
                return None
            
            value, timestamp = self.cache[key]
            
            # 檢查是否過期
            if self.ttl and time.time() - timestamp > self.ttl:
                del self.cache[key]
                self.stats['misses'] += 1
                return None
            
            # 移到末尾（最近使用）
            self.cache.move_to_end(key)
            self.stats['hits'] += 1
            return value
    
    def put(self, key: Any, value: T):
        """放入緩存項"""
        with self._lock:
            # 如果已存在，先刪除
            if key in self.cache:
                del self.cache[key]
            
            # 檢查容量
            while len(self.cache) >= self.max_size:
                # 移除最老的項
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evictions'] += 1
            
            self.cache[key] = (value, time.time())
    
    def clear(self):
        """清空緩存"""
        with self._lock:
            self.cache.clear()
    
    @property
    def hit_rate(self) -> float:
        """計算命中率"""
        total = self.stats['hits'] + self.stats['misses']
        return self.stats['hits'] / total if total > 0 else 0.0


class MemoryManager:
    """內存管理器
    
    監控和管理系統內存使用
    """
    
    def __init__(self, target_memory_mb: int = 1024):
        """
        參數:
            target_memory_mb: 目標內存使用量（MB）
        """
        self.target_memory_mb = target_memory_mb
        self.process = psutil.Process(os.getpid())
        self._callbacks: List[Callable] = []
        self._monitoring = False
        self._monitor_thread = None
    
    def register_callback(self, callback: Callable):
        """註冊內存壓力回調"""
        self._callbacks.append(callback)
    
    def start_monitoring(self, interval: float = 1.0):
        """開始監控內存"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止監控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
    
    def _monitor_loop(self, interval: float):
        """監控循環"""
        while self._monitoring:
            memory_mb = self.get_memory_usage()
            
            if memory_mb > self.target_memory_mb:
                # 觸發內存壓力回調
                for callback in self._callbacks:
                    try:
                        callback()
                    except Exception as e:
                        print(f"Memory callback error: {e}")
                
                # 強制垃圾回收
                gc.collect()
            
            time.sleep(interval)
    
    def get_memory_usage(self) -> float:
        """獲取當前內存使用量（MB）"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_memory_info(self) -> Dict[str, float]:
        """獲取詳細內存信息"""
        info = self.process.memory_info()
        return {
            'rss_mb': info.rss / 1024 / 1024,
            'vms_mb': info.vms / 1024 / 1024,
            'percent': self.process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }


class CacheStrategy:
    """緩存策略實現
    
    結合多級緩存和智能預取
    """
    
    def __init__(self):
        # L1緩存：最熱數據
        self.l1_cache = LRUCache[Any](max_size=1000, ttl=60)
        
        # L2緩存：次熱數據
        self.l2_cache = LRUCache[Any](max_size=10000, ttl=300)
        
        # L3緩存：冷數據（可選持久化）
        self.l3_cache = LRUCache[Any](max_size=100000, ttl=3600)
        
        # 預取隊列
        self.prefetch_queue = deque(maxlen=100)
        self._prefetch_thread = None
        self._prefetching = False
    
    def get(self, key: Any) -> Optional[Any]:
        """多級緩存查詢"""
        # L1查詢
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # L2查詢
        value = self.l2_cache.get(key)
        if value is not None:
            # 提升到L1
            self.l1_cache.put(key, value)
            return value
        
        # L3查詢
        value = self.l3_cache.get(key)
        if value is not None:
            # 提升到L2
            self.l2_cache.put(key, value)
            return value
        
        return None
    
    def put(self, key: Any, value: Any, level: int = 1):
        """放入指定級別的緩存"""
        if level == 1:
            self.l1_cache.put(key, value)
        elif level == 2:
            self.l2_cache.put(key, value)
        else:
            self.l3_cache.put(key, value)
    
    def prefetch(self, keys: List[Any]):
        """預取數據"""
        self.prefetch_queue.extend(keys)
        if not self._prefetching:
            self._start_prefetching()
    
    def _start_prefetching(self):
        """開始預取線程"""
        self._prefetching = True
        self._prefetch_thread = threading.Thread(
            target=self._prefetch_worker,
            daemon=True
        )
        self._prefetch_thread.start()
    
    def _prefetch_worker(self):
        """預取工作線程"""
        while self._prefetching and self.prefetch_queue:
            try:
                key = self.prefetch_queue.popleft()
                # 這裡應該實現實際的數據加載邏輯
                # 暫時跳過
            except IndexError:
                break
        
        self._prefetching = False
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """獲取緩存統計"""
        return {
            'l1': {
                'hit_rate': self.l1_cache.hit_rate,
                'size': len(self.l1_cache.cache)
            },
            'l2': {
                'hit_rate': self.l2_cache.hit_rate,
                'size': len(self.l2_cache.cache)
            },
            'l3': {
                'hit_rate': self.l3_cache.hit_rate,
                'size': len(self.l3_cache.cache)
            }
        }


# 全局內存管理實例
memory_manager = MemoryManager()

# 節點對象池
node_pool = ObjectPool(
    factory=lambda: MCTSNode(0, None, {}, 0),
    reset_func=lambda node: node.__init__(0, None, {}, 0),
    initial_size=1000,
    max_size=100000
)

# 狀態對象池
state_pool = ObjectPool(
    factory=CompactGameState,
    reset_func=lambda state: state.__init__(),
    initial_size=500,
    max_size=50000
)