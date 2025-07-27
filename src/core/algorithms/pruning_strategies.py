"""
OFC MCTS剪枝策略實現

包含多種剪枝技術：
1. Alpha-Beta剪枝
2. 基於領域知識的剪枝
3. 動態閾值調整
4. 前向剪枝(Forward Pruning)
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math


@dataclass
class PruningContext:
    """剪枝上下文信息"""
    depth: int  # 當前搜索深度
    time_remaining: float  # 剩餘時間
    nodes_explored: int  # 已探索節點數
    best_score: float  # 當前最佳分數
    alpha: float = -float('inf')  # Alpha值
    beta: float = float('inf')  # Beta值
    
    # OFC特定信息
    cards_placed: int  # 已放置的牌數
    foul_probability: float  # 犯規概率
    current_scores: Dict[str, float]  # 各行當前分數


class PruningStrategy(ABC):
    """剪枝策略基類"""
    
    @abstractmethod
    def should_prune(self, action: int, state, context: PruningContext) -> bool:
        """判斷是否應該剪枝此動作"""
        pass
    
    @abstractmethod
    def update_thresholds(self, context: PruningContext):
        """更新剪枝閾值"""
        pass


class AlphaBetaPruning(PruningStrategy):
    """Alpha-Beta剪枝策略
    
    在MCTS中的應用：
    - 維護每個節點的值邊界
    - 剪掉明顯劣於當前最佳的分支
    """
    
    def __init__(self, window_size: float = 0.1):
        """
        參數:
            window_size: 剪枝窗口大小，越小越激進
        """
        self.window_size = window_size
        self.pruning_stats = {
            'total_pruned': 0,
            'depth_distribution': {}
        }
    
    def should_prune(self, action: int, state, context: PruningContext) -> bool:
        """基於Alpha-Beta邊界判斷是否剪枝"""
        # 獲取動作的預期值
        expected_value = self._estimate_action_value(action, state)
        
        # Alpha剪枝：如果這個動作的最大可能值仍小於alpha
        if expected_value + self.window_size < context.alpha:
            self.pruning_stats['total_pruned'] += 1
            self.pruning_stats['depth_distribution'][context.depth] = \
                self.pruning_stats['depth_distribution'].get(context.depth, 0) + 1
            return True
        
        # Beta剪枝：如果這個動作的最小可能值已大於beta
        if expected_value - self.window_size > context.beta:
            self.pruning_stats['total_pruned'] += 1
            return True
        
        return False
    
    def update_thresholds(self, context: PruningContext):
        """動態調整窗口大小"""
        # 根據時間壓力調整
        if context.time_remaining < 5.0:  # 時間緊張
            self.window_size *= 0.9  # 更激進的剪枝
        elif context.time_remaining > 20.0:  # 時間充裕
            self.window_size *= 1.1  # 更保守的剪枝
        
        # 限制範圍
        self.window_size = max(0.05, min(0.3, self.window_size))
    
    def _estimate_action_value(self, action: int, state) -> float:
        """估計動作的期望值"""
        # 需要根據具體實現
        # 這裡使用簡化的估計
        return 0.0


class DomainKnowledgePruning(PruningStrategy):
    """基於OFC領域知識的剪枝策略
    
    利用OFC特定規則和模式進行剪枝
    """
    
    def __init__(self):
        self.foul_threshold = 0.3  # 犯規概率閾值
        self.pattern_cache = {}  # 緩存已知的壞模式
        
        # 預定義的壞模式
        self.bad_patterns = self._initialize_bad_patterns()
    
    def _initialize_bad_patterns(self) -> Dict[str, Set[Tuple[int, ...]]]:
        """初始化已知的壞牌型模式"""
        return {
            'top': {
                # 頂行放大牌通常是壞選擇（除非已經有對子）
                (12,), (11,), (10,)  # A, K, Q單張
            },
            'middle': {
                # 中行破壞順子/同花的模式
            },
            'bottom': {
                # 底行放小對子通常不好
                (0, 0), (1, 1), (2, 2)  # 22, 33, 44
            }
        }
    
    def should_prune(self, action: int, state, context: PruningContext) -> bool:
        """基於領域知識判斷是否剪枝"""
        # 1. 犯規檢查
        if self._will_cause_foul(action, state):
            return True
        
        # 2. 高犯規概率檢查
        foul_prob = self._estimate_foul_probability(action, state)
        if foul_prob > self.foul_threshold:
            return True
        
        # 3. 壞模式檢查
        if self._matches_bad_pattern(action, state):
            return True
        
        # 4. 基於遊戲階段的檢查
        if self._violates_stage_strategy(action, state, context):
            return True
        
        return False
    
    def update_thresholds(self, context: PruningContext):
        """根據遊戲進程調整閾值"""
        # 遊戲後期降低犯規容忍度
        progress = context.cards_placed / 13.0
        self.foul_threshold = 0.3 * (1 - progress) + 0.1 * progress
    
    def _will_cause_foul(self, action: int, state) -> bool:
        """檢查動作是否會立即導致犯規"""
        # 需要根據OFC規則實現
        # 檢查 top >= middle >= bottom
        return False
    
    def _estimate_foul_probability(self, action: int, state) -> float:
        """估計執行動作後的犯規概率
        
        使用蒙特卡洛模擬或查找表
        """
        # 簡化實現
        return 0.0
    
    def _matches_bad_pattern(self, action: int, state) -> bool:
        """檢查是否匹配已知的壞模式"""
        # 需要具體實現
        return False
    
    def _violates_stage_strategy(self, action: int, state, context: PruningContext) -> bool:
        """檢查是否違反階段性策略"""
        cards_placed = context.cards_placed
        
        # 早期策略（0-5張牌）
        if cards_placed < 5:
            # 避免過早固定牌型
            return False
        
        # 中期策略（6-9張牌）
        elif cards_placed < 10:
            # 應該開始形成牌型
            return False
        
        # 後期策略（10-13張牌）
        else:
            # 專注於避免犯規
            return False


class ProgressivePruning(PruningStrategy):
    """漸進式剪枝策略
    
    根據節點的訪問次數和置信度動態剪枝
    """
    
    def __init__(self, base_threshold: float = 0.1):
        self.base_threshold = base_threshold
        self.confidence_factor = 1.96  # 95%置信區間
        self.visit_threshold = 10  # 最小訪問次數
    
    def should_prune(self, action: int, state, context: PruningContext) -> bool:
        """基於統計置信度的剪枝"""
        node_stats = self._get_node_statistics(action, state)
        
        if node_stats['visits'] < self.visit_threshold:
            return False  # 訪問次數不足，不剪枝
        
        # 計算置信區間
        mean_value = node_stats['value']
        confidence_bound = self._calculate_confidence_bound(node_stats)
        
        # 如果上界仍低於當前最佳值的閾值，則剪枝
        upper_bound = mean_value + confidence_bound
        if upper_bound < context.best_score - self.base_threshold:
            return True
        
        return False
    
    def update_thresholds(self, context: PruningContext):
        """根據搜索進度調整閾值"""
        # 隨著搜索深入，可以更激進
        exploration_ratio = context.nodes_explored / 10000  # 假設目標是10000個節點
        self.base_threshold *= (1 - 0.5 * min(1.0, exploration_ratio))
    
    def _get_node_statistics(self, action: int, state) -> Dict[str, float]:
        """獲取節點統計信息"""
        # 需要從MCTS樹中獲取
        return {
            'visits': 0,
            'value': 0.0,
            'variance': 0.0
        }
    
    def _calculate_confidence_bound(self, stats: Dict[str, float]) -> float:
        """計算置信區間寬度"""
        if stats['visits'] == 0:
            return float('inf')
        
        # Hoeffding bound
        return self.confidence_factor * math.sqrt(stats['variance'] / stats['visits'])


class HybridPruningStrategy(PruningStrategy):
    """混合剪枝策略
    
    結合多種剪枝技術，根據情況選擇最合適的策略
    """
    
    def __init__(self):
        self.strategies = {
            'alpha_beta': AlphaBetaPruning(),
            'domain': DomainKnowledgePruning(),
            'progressive': ProgressivePruning()
        }
        
        # 策略權重
        self.weights = {
            'alpha_beta': 0.3,
            'domain': 0.5,
            'progressive': 0.2
        }
    
    def should_prune(self, action: int, state, context: PruningContext) -> bool:
        """綜合多種策略的剪枝決策"""
        # 加權投票
        prune_score = 0.0
        
        for name, strategy in self.strategies.items():
            if strategy.should_prune(action, state, context):
                prune_score += self.weights[name]
        
        # 如果總分超過閾值，則剪枝
        return prune_score > 0.5
    
    def update_thresholds(self, context: PruningContext):
        """更新所有子策略的閾值"""
        for strategy in self.strategies.values():
            strategy.update_thresholds(context)
        
        # 動態調整權重
        self._adjust_weights(context)
    
    def _adjust_weights(self, context: PruningContext):
        """根據搜索階段調整策略權重"""
        if context.depth < 3:
            # 淺層更依賴領域知識
            self.weights['domain'] = 0.6
            self.weights['alpha_beta'] = 0.3
            self.weights['progressive'] = 0.1
        elif context.depth < 10:
            # 中層平衡各策略
            self.weights['domain'] = 0.4
            self.weights['alpha_beta'] = 0.4
            self.weights['progressive'] = 0.2
        else:
            # 深層更依賴統計剪枝
            self.weights['domain'] = 0.3
            self.weights['alpha_beta'] = 0.3
            self.weights['progressive'] = 0.4


class PruningOrchestrator:
    """剪枝協調器
    
    管理和協調不同的剪枝策略
    """
    
    def __init__(self, strategy: PruningStrategy = None):
        self.strategy = strategy or HybridPruningStrategy()
        self.pruning_history = []
        self.effectiveness_metrics = {
            'total_actions': 0,
            'pruned_actions': 0,
            'pruning_accuracy': 0.0
        }
    
    def filter_actions(self, actions: List[int], state, context: PruningContext) -> List[int]:
        """過濾動作列表，返回未被剪枝的動作"""
        filtered_actions = []
        
        for action in actions:
            self.effectiveness_metrics['total_actions'] += 1
            
            if not self.strategy.should_prune(action, state, context):
                filtered_actions.append(action)
            else:
                self.effectiveness_metrics['pruned_actions'] += 1
                self.pruning_history.append({
                    'action': action,
                    'depth': context.depth,
                    'reason': 'pruned'
                })
        
        # 更新剪枝率
        if self.effectiveness_metrics['total_actions'] > 0:
            self.effectiveness_metrics['pruning_accuracy'] = \
                self.effectiveness_metrics['pruned_actions'] / self.effectiveness_metrics['total_actions']
        
        # 確保至少保留一個動作
        if not filtered_actions and actions:
            # 選擇最有希望的動作
            best_action = self._select_best_fallback(actions, state)
            filtered_actions = [best_action]
        
        return filtered_actions
    
    def adapt_strategy(self, context: PruningContext):
        """根據搜索進展調整策略"""
        self.strategy.update_thresholds(context)
        
        # 如果剪枝率過高或過低，調整策略
        pruning_rate = self.effectiveness_metrics['pruning_accuracy']
        if pruning_rate > 0.8:  # 剪枝過多
            # 放鬆剪枝條件
            pass
        elif pruning_rate < 0.2:  # 剪枝過少
            # 加強剪枝
            pass
    
    def _select_best_fallback(self, actions: List[int], state) -> int:
        """選擇備用動作"""
        # 使用簡單的啟發式評估
        # 實際實現需要根據OFC規則
        return actions[0]
    
    def get_pruning_report(self) -> Dict:
        """獲取剪枝效果報告"""
        return {
            'metrics': self.effectiveness_metrics,
            'history_sample': self.pruning_history[-10:],  # 最近10個剪枝決策
            'strategy_stats': self.strategy.pruning_stats if hasattr(self.strategy, 'pruning_stats') else {}
        }