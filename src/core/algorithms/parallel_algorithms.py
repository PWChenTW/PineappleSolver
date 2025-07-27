"""
OFC Solver並行算法實現

包含：
1. 無鎖數據結構
2. 工作竊取算法
3. 負載平衡策略
4. 並行MCTS實現
"""

import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import time
from typing import List, Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass
import numpy as np
from collections import deque
import random
from abc import ABC, abstractmethod


class LockFreeStack:
    """無鎖棧實現
    
    使用Compare-And-Swap (CAS)操作實現無鎖並發
    """
    
    def __init__(self):
        self._head = None
        self._lock = threading.Lock()  # Python沒有原生CAS，使用細粒度鎖模擬
    
    class Node:
        def __init__(self, value, next_node=None):
            self.value = value
            self.next = next_node
    
    def push(self, value):
        """無鎖入棧"""
        new_node = self.Node(value)
        while True:
            # 在真實的無鎖實現中，這裡會使用CAS
            with self._lock:
                new_node.next = self._head
                self._head = new_node
                break
    
    def pop(self):
        """無鎖出棧"""
        while True:
            with self._lock:
                if self._head is None:
                    return None
                value = self._head.value
                self._head = self._head.next
                return value


class LockFreeQueue:
    """無鎖隊列實現
    
    使用Michael & Scott算法
    """
    
    def __init__(self):
        # 初始化哨兵節點
        self._sentinel = self.Node(None)
        self._head = self._sentinel
        self._tail = self._sentinel
        self._head_lock = threading.Lock()
        self._tail_lock = threading.Lock()
    
    class Node:
        def __init__(self, value, next_node=None):
            self.value = value
            self.next = next_node
    
    def enqueue(self, value):
        """無鎖入隊"""
        new_node = self.Node(value)
        
        with self._tail_lock:
            self._tail.next = new_node
            self._tail = new_node
    
    def dequeue(self):
        """無鎖出隊"""
        with self._head_lock:
            if self._head.next is None:
                return None
            
            value = self._head.next.value
            self._head = self._head.next
            return value


@dataclass
class WorkItem:
    """工作項"""
    task_id: int
    func: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    created_time: float = 0.0
    
    def __post_init__(self):
        if self.created_time == 0.0:
            self.created_time = time.time()


class WorkStealingQueue:
    """工作竊取隊列
    
    每個工作線程都有自己的隊列，支持從其他線程竊取任務
    """
    
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        # 每個工作者的私有隊列
        self.queues = [deque() for _ in range(num_workers)]
        self.locks = [threading.Lock() for _ in range(num_workers)]
        
        # 統計信息
        self.stats = {
            'steals': 0,
            'tasks_completed': 0,
            'total_wait_time': 0.0
        }
    
    def push(self, worker_id: int, item: WorkItem):
        """將任務推入指定工作者的隊列"""
        with self.locks[worker_id]:
            self.queues[worker_id].append(item)
    
    def pop(self, worker_id: int) -> Optional[WorkItem]:
        """從自己的隊列取任務，如果為空則嘗試竊取"""
        # 首先嘗試從自己的隊列取
        with self.locks[worker_id]:
            if self.queues[worker_id]:
                return self.queues[worker_id].popleft()
        
        # 嘗試從其他隊列竊取
        return self._steal(worker_id)
    
    def _steal(self, thief_id: int) -> Optional[WorkItem]:
        """竊取任務"""
        # 隨機選擇受害者，避免爭用
        victim_order = list(range(self.num_workers))
        victim_order.remove(thief_id)
        random.shuffle(victim_order)
        
        for victim_id in victim_order:
            with self.locks[victim_id]:
                if len(self.queues[victim_id]) > 1:  # 至少留一個給受害者
                    # 從隊列尾部竊取（LIFO），減少緩存失效
                    self.stats['steals'] += 1
                    return self.queues[victim_id].pop()
        
        return None


class WorkStealingExecutor:
    """工作竊取執行器
    
    實現工作竊取算法的線程池
    """
    
    def __init__(self, num_workers: Optional[int] = None):
        self.num_workers = num_workers or mp.cpu_count()
        self.work_queue = WorkStealingQueue(self.num_workers)
        self.workers = []
        self.running = False
        self.task_counter = 0
        self.results = {}
        self.result_lock = threading.Lock()
    
    def start(self):
        """啟動工作線程"""
        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
    
    def stop(self):
        """停止工作線程"""
        self.running = False
        for worker in self.workers:
            worker.join()
    
    def submit(self, func: Callable, *args, **kwargs) -> int:
        """提交任務"""
        task_id = self.task_counter
        self.task_counter += 1
        
        item = WorkItem(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs
        )
        
        # 選擇負載最少的隊列
        min_load = float('inf')
        best_worker = 0
        for i in range(self.num_workers):
            load = len(self.work_queue.queues[i])
            if load < min_load:
                min_load = load
                best_worker = i
        
        self.work_queue.push(best_worker, item)
        return task_id
    
    def _worker_loop(self, worker_id: int):
        """工作線程主循環"""
        while self.running:
            item = self.work_queue.pop(worker_id)
            
            if item is None:
                time.sleep(0.001)  # 避免忙等待
                continue
            
            # 執行任務
            try:
                result = item.func(*item.args, **item.kwargs)
                
                # 記錄結果
                with self.result_lock:
                    self.results[item.task_id] = result
                
                # 更新統計
                wait_time = time.time() - item.created_time
                self.work_queue.stats['tasks_completed'] += 1
                self.work_queue.stats['total_wait_time'] += wait_time
                
            except Exception as e:
                with self.result_lock:
                    self.results[item.task_id] = e
    
    def get_result(self, task_id: int, timeout: float = None) -> Any:
        """獲取任務結果"""
        start_time = time.time()
        
        while True:
            with self.result_lock:
                if task_id in self.results:
                    result = self.results.pop(task_id)
                    if isinstance(result, Exception):
                        raise result
                    return result
            
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timeout")
            
            time.sleep(0.001)


class ParallelMCTS:
    """並行MCTS實現
    
    使用多種並行化策略：
    1. Leaf Parallelization: 並行評估多個葉節點
    2. Root Parallelization: 多個MCTS樹並行搜索
    3. Tree Parallelization: 單樹多線程更新
    """
    
    def __init__(self, num_threads: int = 4, strategy: str = "tree"):
        """
        參數:
            num_threads: 線程數
            strategy: 並行策略 ("leaf", "root", "tree")
        """
        self.num_threads = num_threads
        self.strategy = strategy
        self.executor = WorkStealingExecutor(num_threads)
        self.executor.start()
        
        # Virtual Loss用於tree parallelization
        self.virtual_loss = 1.0
        
        # 統計信息
        self.stats = {
            'simulations': 0,
            'parallel_efficiency': 0.0
        }
    
    def search(self, root_state, num_simulations: int) -> Dict[int, float]:
        """執行並行搜索"""
        if self.strategy == "leaf":
            return self._leaf_parallel_search(root_state, num_simulations)
        elif self.strategy == "root":
            return self._root_parallel_search(root_state, num_simulations)
        else:  # tree
            return self._tree_parallel_search(root_state, num_simulations)
    
    def _leaf_parallel_search(self, root_state, num_simulations: int) -> Dict[int, float]:
        """葉節點並行化
        
        批量收集葉節點，並行評估
        """
        root = self._create_root_node(root_state)
        
        batch_size = min(self.num_threads * 4, 100)
        num_batches = num_simulations // batch_size
        
        for _ in range(num_batches):
            # 收集葉節點
            leaves = []
            for _ in range(batch_size):
                path, leaf = self._select_leaf(root, root_state.copy())
                leaves.append((path, leaf))
            
            # 並行評估
            task_ids = []
            for path, leaf in leaves:
                task_id = self.executor.submit(self._evaluate_leaf, leaf)
                task_ids.append((task_id, path))
            
            # 收集結果並反向傳播
            for task_id, path in task_ids:
                value = self.executor.get_result(task_id)
                self._backpropagate(path, value)
        
        return self._get_action_probs(root)
    
    def _root_parallel_search(self, root_state, num_simulations: int) -> Dict[int, float]:
        """根並行化
        
        創建多個獨立的MCTS樹並行搜索
        """
        simulations_per_tree = num_simulations // self.num_threads
        
        # 啟動並行搜索
        task_ids = []
        for _ in range(self.num_threads):
            task_id = self.executor.submit(
                self._single_tree_search,
                root_state.copy(),
                simulations_per_tree
            )
            task_ids.append(task_id)
        
        # 收集結果
        all_action_probs = []
        for task_id in task_ids:
            action_probs = self.executor.get_result(task_id)
            all_action_probs.append(action_probs)
        
        # 合併結果
        return self._merge_action_probs(all_action_probs)
    
    def _tree_parallel_search(self, root_state, num_simulations: int) -> Dict[int, float]:
        """樹並行化
        
        多線程共享單個MCTS樹，使用Virtual Loss避免衝突
        """
        root = self._create_root_node(root_state)
        
        # 創建共享的樹結構
        tree_lock = threading.RLock()
        
        def worker_func():
            local_simulations = 0
            while self.stats['simulations'] < num_simulations:
                # 選擇路徑（需要鎖）
                with tree_lock:
                    if self.stats['simulations'] >= num_simulations:
                        break
                    
                    path, leaf, state = self._select_with_virtual_loss(root, root_state.copy())
                    self.stats['simulations'] += 1
                
                # 評估（不需要鎖）
                value = self._simulate_playout(state)
                
                # 反向傳播（需要鎖）
                with tree_lock:
                    self._backpropagate_with_virtual_loss(path, value)
                
                local_simulations += 1
            
            return local_simulations
        
        # 啟動工作線程
        task_ids = []
        for _ in range(self.num_threads):
            task_id = self.executor.submit(worker_func)
            task_ids.append(task_id)
        
        # 等待完成
        total_sims = 0
        for task_id in task_ids:
            sims = self.executor.get_result(task_id)
            total_sims += sims
        
        # 計算並行效率
        self.stats['parallel_efficiency'] = total_sims / (num_simulations * self.num_threads)
        
        return self._get_action_probs(root)
    
    def _select_with_virtual_loss(self, node, state) -> Tuple[List, Any, Any]:
        """帶虛擬損失的選擇
        
        在選擇路徑時臨時增加訪問次數，避免多線程選擇相同路徑
        """
        path = []
        
        while not node.is_leaf():
            # 應用虛擬損失
            node.visits += self.virtual_loss
            node.value_sum -= self.virtual_loss
            
            action, child = self._select_best_child(node)
            path.append((node, action))
            node = child
            state = self._apply_action(state, action)
        
        return path, node, state
    
    def _backpropagate_with_virtual_loss(self, path: List, value: float):
        """帶虛擬損失的反向傳播
        
        移除虛擬損失並更新真實值
        """
        for node, _ in path:
            # 移除虛擬損失
            node.visits -= self.virtual_loss
            node.value_sum += self.virtual_loss
            
            # 更新真實值
            node.update(value)
            value = -value  # 對手視角
    
    def _merge_action_probs(self, all_probs: List[Dict[int, float]]) -> Dict[int, float]:
        """合併多個MCTS樹的結果"""
        merged = {}
        action_counts = {}
        
        for probs in all_probs:
            for action, prob in probs.items():
                if action not in merged:
                    merged[action] = 0.0
                    action_counts[action] = 0
                merged[action] += prob
                action_counts[action] += 1
        
        # 平均化
        for action in merged:
            merged[action] /= action_counts[action]
        
        return merged
    
    # 以下為輔助方法的占位實現
    def _create_root_node(self, state):
        """創建根節點"""
        pass
    
    def _select_leaf(self, root, state):
        """選擇葉節點"""
        pass
    
    def _evaluate_leaf(self, leaf):
        """評估葉節點"""
        pass
    
    def _backpropagate(self, path, value):
        """反向傳播"""
        pass
    
    def _get_action_probs(self, root):
        """獲取動作概率分布"""
        pass
    
    def _single_tree_search(self, state, num_simulations):
        """單樹搜索"""
        pass
    
    def _select_best_child(self, node):
        """選擇最佳子節點"""
        pass
    
    def _apply_action(self, state, action):
        """應用動作"""
        pass
    
    def _simulate_playout(self, state):
        """模擬對局"""
        pass


class LoadBalancer:
    """負載平衡器
    
    動態調整任務分配策略
    """
    
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.worker_loads = [0.0] * num_workers
        self.worker_speeds = [1.0] * num_workers  # 相對處理速度
        self.task_history = deque(maxlen=1000)
        
        # 負載平衡策略
        self.strategies = {
            'round_robin': self._round_robin,
            'least_loaded': self._least_loaded,
            'weighted': self._weighted_distribution,
            'adaptive': self._adaptive_distribution
        }
        self.current_strategy = 'adaptive'
        self.next_worker = 0
    
    def assign_task(self, task_size: float = 1.0) -> int:
        """分配任務到工作者"""
        strategy_func = self.strategies[self.current_strategy]
        worker_id = strategy_func(task_size)
        
        # 更新負載
        self.worker_loads[worker_id] += task_size
        
        # 記錄歷史
        self.task_history.append({
            'worker_id': worker_id,
            'task_size': task_size,
            'timestamp': time.time()
        })
        
        return worker_id
    
    def complete_task(self, worker_id: int, task_size: float, duration: float):
        """任務完成回調"""
        # 更新負載
        self.worker_loads[worker_id] -= task_size
        
        # 更新處理速度估計
        if task_size > 0:
            speed = task_size / duration
            # 指數移動平均
            alpha = 0.1
            self.worker_speeds[worker_id] = (
                alpha * speed + (1 - alpha) * self.worker_speeds[worker_id]
            )
    
    def _round_robin(self, task_size: float) -> int:
        """輪詢分配"""
        worker_id = self.next_worker
        self.next_worker = (self.next_worker + 1) % self.num_workers
        return worker_id
    
    def _least_loaded(self, task_size: float) -> int:
        """最小負載優先"""
        return min(range(self.num_workers), key=lambda i: self.worker_loads[i])
    
    def _weighted_distribution(self, task_size: float) -> int:
        """基於處理速度的加權分配"""
        # 計算每個工作者的權重（速度/負載）
        weights = []
        for i in range(self.num_workers):
            load = max(0.1, self.worker_loads[i])  # 避免除零
            weight = self.worker_speeds[i] / load
            weights.append(weight)
        
        # 基於權重選擇
        total_weight = sum(weights)
        if total_weight == 0:
            return 0
        
        probabilities = [w / total_weight for w in weights]
        return np.random.choice(self.num_workers, p=probabilities)
    
    def _adaptive_distribution(self, task_size: float) -> int:
        """自適應分配策略"""
        # 對於大任務，使用最快的空閒工作者
        if task_size > 5.0:
            # 找到負載低且速度快的工作者
            candidates = [
                i for i in range(self.num_workers)
                if self.worker_loads[i] < 2.0
            ]
            if candidates:
                return max(candidates, key=lambda i: self.worker_speeds[i])
        
        # 對於小任務，使用最小負載策略
        return self._least_loaded(task_size)
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取負載平衡統計"""
        return {
            'worker_loads': self.worker_loads.copy(),
            'worker_speeds': self.worker_speeds.copy(),
            'load_variance': np.var(self.worker_loads),
            'speed_variance': np.var(self.worker_speeds),
            'current_strategy': self.current_strategy
        }