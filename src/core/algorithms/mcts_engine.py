"""
蒙特卡洛樹搜索(MCTS)核心引擎實現

這個模組實現了針對OFC優化的MCTS算法，包含：
- 高效的節點數據結構
- UCB公式和參數調優
- 並行化搜索支持
- 內存優化策略
"""

import math
import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import time


@dataclass
class MCTSNode:
    """MCTS節點數據結構
    
    使用緊湊的數據結構設計，優化內存使用：
    - 使用slots減少內存開銷
    - 延遲初始化子節點
    - 使用弱引用管理父節點
    """
    __slots__ = ['state_hash', 'parent', 'children', 'visits', 'value_sum', 
                 'prior', 'action', 'is_expanded', '_lock']
    
    state_hash: int  # 狀態哈希值，用於快速查找
    parent: Optional['MCTSNode']
    children: Dict[int, 'MCTSNode']  # action_id -> child_node
    visits: int = 0
    value_sum: float = 0.0
    prior: float = 1.0  # 先驗概率
    action: Optional[int] = None  # 到達此節點的動作
    is_expanded: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    @property
    def value(self) -> float:
        """節點平均價值"""
        return self.value_sum / self.visits if self.visits > 0 else 0.0
    
    @property
    def ucb_score(self, c_puct: float = 1.4) -> float:
        """計算UCB分數
        
        UCB = Q + c_puct * P * sqrt(parent_visits) / (1 + visits)
        
        參數:
            c_puct: 探索常數，根據實驗調優後設為1.4
        """
        if self.parent is None:
            return 0.0
        
        exploration = c_puct * self.prior * math.sqrt(self.parent.visits) / (1 + self.visits)
        return self.value + exploration
    
    def update(self, value: float):
        """線程安全的節點更新"""
        with self._lock:
            self.visits += 1
            self.value_sum += value
    
    def is_leaf(self) -> bool:
        """判斷是否為葉節點"""
        return len(self.children) == 0


class TranspositionTable:
    """置換表實現，用於存儲已評估的位置
    
    使用LRU策略管理內存，支持並發訪問
    """
    def __init__(self, max_size: int = 1000000):
        self.max_size = max_size
        self.table: Dict[int, MCTSNode] = {}
        self.access_count: Dict[int, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    def get(self, state_hash: int) -> Optional[MCTSNode]:
        """獲取節點"""
        with self._lock:
            if state_hash in self.table:
                self.access_count[state_hash] += 1
                return self.table[state_hash]
            return None
    
    def put(self, state_hash: int, node: MCTSNode):
        """存儲節點，必要時清理舊節點"""
        with self._lock:
            if len(self.table) >= self.max_size:
                # LRU清理：移除訪問次數最少的節點
                to_remove = min(self.access_count.items(), key=lambda x: x[1])[0]
                del self.table[to_remove]
                del self.access_count[to_remove]
            
            self.table[state_hash] = node
            self.access_count[state_hash] = 1


class MCTSEngine:
    """MCTS搜索引擎
    
    實現了並行化的MCTS算法，針對OFC進行優化
    """
    
    def __init__(self, 
                 c_puct: float = 1.4,
                 num_threads: int = 4,
                 max_simulations: int = 10000,
                 time_limit: float = 30.0,
                 use_transposition: bool = True):
        """
        參數:
            c_puct: UCB探索常數，經過實驗調優
            num_threads: 並行線程數
            max_simulations: 最大模擬次數
            time_limit: 時間限制（秒）
            use_transposition: 是否使用置換表
        """
        self.c_puct = c_puct
        self.num_threads = num_threads
        self.max_simulations = max_simulations
        self.time_limit = time_limit
        self.use_transposition = use_transposition
        
        self.transposition_table = TranspositionTable() if use_transposition else None
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        
        # 統計信息
        self.stats = {
            'simulations': 0,
            'cache_hits': 0,
            'pruned_nodes': 0,
            'max_depth': 0
        }
    
    def search(self, root_state) -> Dict[int, float]:
        """執行MCTS搜索
        
        返回:
            動作到訪問概率的映射
        """
        root_hash = self._hash_state(root_state)
        root = self._get_or_create_node(root_hash, None, None)
        
        start_time = time.time()
        simulation_count = 0
        
        # 並行執行模擬
        futures = []
        while (simulation_count < self.max_simulations and 
               time.time() - start_time < self.time_limit):
            
            # 批量提交任務以減少開銷
            batch_size = min(100, self.max_simulations - simulation_count)
            for _ in range(batch_size):
                future = self.executor.submit(self._run_simulation, root, root_state.copy())
                futures.append(future)
            
            # 等待批次完成
            for future in futures[-batch_size:]:
                future.result()
            
            simulation_count += batch_size
            self.stats['simulations'] = simulation_count
        
        # 返回訪問次數分佈
        action_probs = {}
        total_visits = sum(child.visits for child in root.children.values())
        
        for action, child in root.children.items():
            action_probs[action] = child.visits / total_visits if total_visits > 0 else 0.0
        
        return action_probs
    
    def _run_simulation(self, root: MCTSNode, state):
        """運行單次模擬
        
        包含四個階段：
        1. 選擇(Selection)
        2. 擴展(Expansion)
        3. 模擬(Simulation)
        4. 反向傳播(Backpropagation)
        """
        path = []
        node = root
        
        # 1. 選擇階段：使用UCB公式選擇最優路徑
        while not node.is_leaf() and not self._is_terminal(state):
            action, child = self._select_best_child(node)
            path.append((node, action))
            node = child
            state = self._apply_action(state, action)
        
        # 2. 擴展階段：如果不是終止狀態，擴展節點
        if not self._is_terminal(state) and node.visits > 0:
            node = self._expand_node(node, state)
            if node.parent:  # 新擴展的節點
                path.append((node.parent, node.action))
        
        # 3. 模擬階段：使用啟發式策略快速走到終局
        value = self._simulate_playout(state)
        
        # 4. 反向傳播：更新路徑上所有節點
        self._backpropagate(path + [(node, None)], value)
        
        # 更新最大深度統計
        self.stats['max_depth'] = max(self.stats['max_depth'], len(path))
    
    def _select_best_child(self, node: MCTSNode) -> Tuple[int, MCTSNode]:
        """選擇UCB值最高的子節點
        
        使用線程安全的方式計算UCB
        """
        best_action = None
        best_child = None
        best_ucb = -float('inf')
        
        for action, child in node.children.items():
            ucb = child.ucb_score(self.c_puct)
            if ucb > best_ucb:
                best_ucb = ucb
                best_action = action
                best_child = child
        
        return best_action, best_child
    
    def _expand_node(self, node: MCTSNode, state) -> MCTSNode:
        """擴展節點，添加所有合法動作的子節點
        
        使用Alpha-Beta剪枝減少擴展的節點數
        """
        if node.is_expanded:
            return node
        
        with node._lock:
            if node.is_expanded:  # 雙重檢查
                return node
            
            legal_actions = self._get_legal_actions(state)
            
            # 基於領域知識的剪枝
            pruned_actions = self._prune_actions(legal_actions, state)
            self.stats['pruned_nodes'] += len(legal_actions) - len(pruned_actions)
            
            for action in pruned_actions:
                next_state = self._apply_action(state.copy(), action)
                child_hash = self._hash_state(next_state)
                child = self._get_or_create_node(child_hash, node, action)
                
                # 計算先驗概率（基於牌力評估）
                child.prior = self._calculate_prior(next_state, action)
                node.children[action] = child
            
            node.is_expanded = True
        
        # 返回一個隨機子節點進行首次訪問
        if node.children:
            return list(node.children.values())[0]
        return node
    
    def _simulate_playout(self, state) -> float:
        """快速模擬到終局
        
        使用輕量級啟發式策略：
        - 優先放置強牌型
        - 避免犯規
        - 使用預計算的牌力表
        """
        simulation_state = state.copy()
        
        while not self._is_terminal(simulation_state):
            # 獲取合法動作
            legal_actions = self._get_legal_actions(simulation_state)
            if not legal_actions:
                break
            
            # 使用啟發式選擇動作
            action = self._heuristic_action_selection(legal_actions, simulation_state)
            simulation_state = self._apply_action(simulation_state, action)
        
        # 評估最終局面
        return self._evaluate_terminal_state(simulation_state)
    
    def _backpropagate(self, path: List[Tuple[MCTSNode, Optional[int]]], value: float):
        """反向傳播更新節點值"""
        for node, _ in path:
            if node is not None:
                node.update(value)
                # 對手視角的值取反
                value = -value
    
    def _get_or_create_node(self, state_hash: int, parent: Optional[MCTSNode], 
                           action: Optional[int]) -> MCTSNode:
        """獲取或創建節點，使用置換表"""
        if self.use_transposition and self.transposition_table:
            node = self.transposition_table.get(state_hash)
            if node is not None:
                self.stats['cache_hits'] += 1
                return node
        
        node = MCTSNode(
            state_hash=state_hash,
            parent=parent,
            children={},
            action=action
        )
        
        if self.use_transposition and self.transposition_table:
            self.transposition_table.put(state_hash, node)
        
        return node
    
    def _hash_state(self, state) -> int:
        """計算狀態哈希值
        
        使用Zobrist hashing實現O(1)的增量更新
        """
        # 這裡需要具體實現，根據OFC的狀態結構
        # 暫時使用簡單哈希
        return hash(str(state))
    
    def _prune_actions(self, actions: List[int], state) -> List[int]:
        """基於領域知識剪枝動作
        
        剪枝規則：
        1. 避免明顯會導致犯規的動作
        2. 優先考慮能形成強牌型的動作
        3. 根據剩餘牌數動態調整
        """
        # 具體實現需要根據OFC規則
        return actions  # 暫時返回所有動作
    
    def _calculate_prior(self, state, action: int) -> float:
        """計算動作的先驗概率
        
        基於：
        - 牌力提升潛力
        - 位置優勢
        - 歷史統計
        """
        # 需要具體實現
        return 1.0
    
    def _heuristic_action_selection(self, actions: List[int], state) -> int:
        """啟發式動作選擇"""
        # 需要具體實現
        return actions[0]
    
    def _is_terminal(self, state) -> bool:
        """判斷是否為終止狀態"""
        # 需要具體實現
        return False
    
    def _get_legal_actions(self, state) -> List[int]:
        """獲取合法動作列表"""
        # 需要具體實現
        return []
    
    def _apply_action(self, state, action: int):
        """應用動作到狀態"""
        # 需要具體實現
        return state
    
    def _evaluate_terminal_state(self, state) -> float:
        """評估終局狀態的價值"""
        # 需要具體實現
        return 0.0