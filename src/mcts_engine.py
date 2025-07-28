"""
MCTS 引擎實現（帶結構化日誌）

這是一個示例實現，展示如何在 MCTS 搜索中使用結構化日誌
"""

import time
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import random
import math

from .logging_config import (
    get_mcts_logger,
    get_performance_logger,
    LogContext
)


@dataclass
class MCTSNode:
    """MCTS 節點"""
    state: Any
    parent: Optional['MCTSNode']
    action: Optional[Any]
    visits: int = 0
    total_reward: float = 0.0
    children: List['MCTSNode'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    @property
    def avg_reward(self) -> float:
        """平均獎勵"""
        return self.total_reward / self.visits if self.visits > 0 else 0.0
    
    @property
    def uct_value(self, c: float = 1.414) -> float:
        """UCT 值計算"""
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.avg_reward
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration


class MCTSEngine:
    """MCTS 搜索引擎"""
    
    def __init__(self, 
                 threads: int = 4,
                 c_param: float = 1.414,
                 max_simulations: int = 100000):
        self.threads = threads
        self.c_param = c_param
        self.max_simulations = max_simulations
        
        # 獲取日誌器
        self.logger = get_mcts_logger()
        self.perf_logger = get_performance_logger("mcts_engine")
        
        # 線程安全鎖
        self.lock = threading.Lock()
        
        # 記錄初始化
        self.logger.info(
            "MCTS Engine initialized",
            extra={
                'component': 'mcts_engine',
                'context': {
                    'threads': threads,
                    'c_param': c_param,
                    'max_simulations': max_simulations
                }
            }
        )
    
    def search(self, root_state: Any, time_limit: float = 30.0) -> MCTSNode:
        """
        執行 MCTS 搜索
        
        Args:
            root_state: 根節點狀態
            time_limit: 時間限制（秒）
            
        Returns:
            根節點
        """
        request_id = str(random.randint(1000, 9999))
        
        with LogContext(self.logger, request_id=request_id,
                       operation="mcts_search") as log_ctx:
            
            # 記錄搜索開始
            log_ctx.log("info", "Starting MCTS search",
                       time_limit=time_limit)
            
            # 創建根節點
            root = MCTSNode(state=root_state, parent=None, action=None)
            
            # 使用性能日誌記錄搜索時間
            @self.perf_logger.log_timing("mcts_search")
            def _search():
                return self._parallel_search(root, time_limit, log_ctx)
            
            # 執行搜索
            _search()
            
            # 記錄搜索完成
            log_ctx.log("info", "MCTS search completed",
                       total_simulations=root.visits,
                       avg_reward=root.avg_reward)
            
            return root
    
    def _parallel_search(self, root: MCTSNode, time_limit: float,
                        log_ctx: LogContext) -> None:
        """並行搜索實現"""
        start_time = time.time()
        stop_event = threading.Event()
        
        # 創建工作線程
        threads = []
        for i in range(self.threads):
            thread = threading.Thread(
                target=self._worker_thread,
                args=(root, stop_event, log_ctx, i)
            )
            threads.append(thread)
            thread.start()
        
        # 監控進度
        last_log_time = start_time
        last_simulations = 0
        
        while time.time() - start_time < time_limit:
            time.sleep(0.5)
            
            # 定期記錄進度
            current_time = time.time()
            if current_time - last_log_time >= 2.0:  # 每2秒記錄一次
                with self.lock:
                    current_simulations = root.visits
                
                simulations_per_second = (current_simulations - last_simulations) / 2.0
                
                log_ctx.log("debug", "MCTS progress update",
                           simulations=current_simulations,
                           simulations_per_second=simulations_per_second,
                           elapsed_time=current_time - start_time)
                
                last_log_time = current_time
                last_simulations = current_simulations
        
        # 停止工作線程
        stop_event.set()
        for thread in threads:
            thread.join()
    
    def _worker_thread(self, root: MCTSNode, stop_event: threading.Event,
                      log_ctx: LogContext, thread_id: int) -> None:
        """工作線程"""
        simulations = 0
        errors = 0
        
        log_ctx.log("debug", f"Worker thread {thread_id} started")
        
        try:
            while not stop_event.is_set() and root.visits < self.max_simulations:
                try:
                    # 執行一次模擬
                    self._run_simulation(root)
                    simulations += 1
                    
                    # 每1000次模擬記錄一次
                    if simulations % 1000 == 0:
                        log_ctx.log("debug", f"Thread {thread_id} progress",
                                   thread_simulations=simulations,
                                   thread_errors=errors)
                        
                except Exception as e:
                    errors += 1
                    if errors % 10 == 0:  # 每10個錯誤記錄一次
                        log_ctx.log("warning", f"Thread {thread_id} simulation error",
                                   error_count=errors,
                                   last_error=str(e))
        
        finally:
            log_ctx.log("debug", f"Worker thread {thread_id} stopped",
                       total_simulations=simulations,
                       total_errors=errors)
    
    def _run_simulation(self, root: MCTSNode) -> float:
        """運行一次 MCTS 模擬"""
        # 選擇
        node = self._select(root)
        
        # 擴展
        if not self._is_terminal(node.state):
            node = self._expand(node)
        
        # 模擬
        reward = self._simulate(node.state)
        
        # 回傳
        self._backpropagate(node, reward)
        
        return reward
    
    def _select(self, node: MCTSNode) -> MCTSNode:
        """選擇階段：使用 UCT 選擇最佳子節點"""
        while node.children:
            # 選擇 UCT 值最大的子節點
            best_child = max(node.children, 
                           key=lambda n: n.uct_value(self.c_param))
            node = best_child
        return node
    
    def _expand(self, node: MCTSNode) -> MCTSNode:
        """擴展階段：添加新的子節點"""
        # 獲取可能的動作（這裡簡化為隨機生成）
        possible_actions = self._get_possible_actions(node.state)
        
        if possible_actions:
            action = random.choice(possible_actions)
            new_state = self._apply_action(node.state, action)
            
            with self.lock:
                child = MCTSNode(
                    state=new_state,
                    parent=node,
                    action=action
                )
                node.children.append(child)
            
            return child
        
        return node
    
    def _simulate(self, state: Any) -> float:
        """模擬階段：隨機模擬到終局"""
        # 簡化實現：返回隨機獎勵
        return random.uniform(-10, 50)
    
    def _backpropagate(self, node: MCTSNode, reward: float) -> None:
        """回傳階段：更新路徑上所有節點的統計信息"""
        while node is not None:
            with self.lock:
                node.visits += 1
                node.total_reward += reward
            node = node.parent
    
    def _is_terminal(self, state: Any) -> bool:
        """檢查是否為終局狀態"""
        # 簡化實現
        return random.random() < 0.1
    
    def _get_possible_actions(self, state: Any) -> List[Any]:
        """獲取可能的動作"""
        # 簡化實現
        return ['action1', 'action2', 'action3']
    
    def _apply_action(self, state: Any, action: Any) -> Any:
        """應用動作到狀態"""
        # 簡化實現
        return f"{state}_{action}"
    
    def get_best_action(self, root: MCTSNode) -> Any:
        """獲取最佳動作"""
        if not root.children:
            return None
        
        # 選擇訪問次數最多的子節點
        best_child = max(root.children, key=lambda n: n.visits)
        
        self.logger.info(
            "Best action selected",
            extra={
                'component': 'mcts_engine',
                'context': {
                    'action': best_child.action,
                    'visits': best_child.visits,
                    'avg_reward': best_child.avg_reward
                }
            }
        )
        
        return best_child.action
    
    def get_top_actions(self, root: MCTSNode, n: int = 5) -> List[Dict[str, Any]]:
        """獲取前 N 個最佳動作"""
        if not root.children:
            return []
        
        # 按訪問次數排序
        sorted_children = sorted(root.children, key=lambda n: n.visits, reverse=True)
        
        top_actions = []
        for i, child in enumerate(sorted_children[:n]):
            top_actions.append({
                'rank': i + 1,
                'action': child.action,
                'visits': child.visits,
                'avg_reward': child.avg_reward,
                'confidence': child.visits / root.visits if root.visits > 0 else 0
            })
        
        self.logger.debug(
            f"Top {n} actions retrieved",
            extra={
                'component': 'mcts_engine',
                'context': {
                    'top_actions': top_actions
                }
            }
        )
        
        return top_actions