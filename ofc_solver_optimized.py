#!/usr/bin/env python3
"""
OFC Pineapple Optimized Solver
優化版本：支持隨機初始手牌、100k MCTS 模擬、多線程並行計算、智能剪枝和緩存
"""

import random
import math
import time
import multiprocessing as mp
from multiprocessing import Pool, Manager
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import List, Dict, Tuple, Optional, Set, Union, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
from abc import ABC, abstractmethod
import functools
import pickle
import hashlib
import numpy as np

# Import base components
from ofc_solver_joker import (
    Card, Hand, create_full_deck, RANKS, SUITS, RANK_VALUES,
    JokerHandEvaluator
)
from ofc_solver_street import (
    Street, OpponentCard, OpponentTracker, StreetState, 
    PineappleState, StreetSolver
)


class CacheManager:
    """緩存管理器 - 使用 LRU 緩存策略"""
    
    def __init__(self, max_size: int = 100000):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
        self.hit_count = 0
        self.miss_count = 0
    
    def get_key(self, state: Any) -> str:
        """生成狀態的唯一鍵"""
        # 將狀態序列化為字符串
        state_str = self._serialize_state(state)
        # 使用 MD5 哈希生成短鍵
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def _serialize_state(self, state: Any) -> str:
        """序列化狀態為字符串"""
        if isinstance(state, PineappleState):
            parts = []
            parts.append(f"F:{sorted([str(c) for c in state.front_hand.cards])}")
            parts.append(f"M:{sorted([str(c) for c in state.middle_hand.cards])}")
            parts.append(f"B:{sorted([str(c) for c in state.back_hand.cards])}")
            parts.append(f"D:{sorted([str(c) for c in state.discarded])}")
            return "|".join(parts)
        return str(state)
    
    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        if key in self.cache:
            self.hit_count += 1
            # 更新訪問順序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        self.miss_count += 1
        return None
    
    def put(self, key: str, value: Any):
        """設置緩存值"""
        if len(self.cache) >= self.max_size and key not in self.cache:
            # 移除最舊的緩存項
            if self.access_order:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
        
        self.cache[key] = value
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        return {
            'size': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate
        }


@dataclass
class MCTSNode:
    """MCTS 節點 - 優化版本"""
    state: PineappleState
    parent: Optional['MCTSNode'] = None
    children: Dict[Any, 'MCTSNode'] = field(default_factory=dict)
    visits: int = 0
    total_score: float = 0.0
    action: Optional[Any] = None
    untried_actions: List[Any] = field(default_factory=list)
    is_terminal: bool = False
    cached_uct: Optional[float] = None
    cached_best_child: Optional['MCTSNode'] = None
    
    def uct_value(self, exploration_constant: float = 1.414) -> float:
        """計算 UCT 值 - 帶緩存"""
        if self.visits == 0:
            return float('inf')
        
        if self.cached_uct is None:
            exploitation = self.total_score / self.visits
            exploration = exploration_constant * math.sqrt(
                2 * math.log(self.parent.visits) / self.visits
            )
            self.cached_uct = exploitation + exploration
        
        return self.cached_uct
    
    def best_child(self, exploration_constant: float = 1.414) -> 'MCTSNode':
        """選擇最佳子節點 - 帶緩存"""
        if self.cached_best_child is None or random.random() < 0.1:  # 10% 機率重新計算
            self.cached_best_child = max(
                self.children.values(),
                key=lambda n: n.uct_value(exploration_constant)
            )
        return self.cached_best_child
    
    def update(self, score: float):
        """更新節點統計"""
        self.visits += 1
        self.total_score += score
        # 清除緩存
        self.cached_uct = None
        self.cached_best_child = None


class ParallelMCTS:
    """並行 MCTS 實現"""
    
    def __init__(self, num_simulations: int = 100000, 
                 num_processes: int = None,
                 cache_manager: Optional[CacheManager] = None):
        self.num_simulations = num_simulations
        self.num_processes = num_processes or mp.cpu_count()
        self.cache_manager = cache_manager or CacheManager()
        self.evaluator = JokerHandEvaluator()
    
    def search(self, initial_state: PineappleState, 
               available_cards: List[Card],
               time_limit: float = 5.0) -> Dict[str, Any]:
        """執行並行 MCTS 搜索"""
        start_time = time.time()
        
        # 檢查緩存
        cache_key = self.cache_manager.get_key(initial_state)
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        # 初始化根節點
        root = MCTSNode(state=initial_state.copy())
        root.untried_actions = self._get_possible_actions(initial_state, available_cards)
        
        # 並行執行模擬
        simulations_per_process = self.num_simulations // self.num_processes
        remaining_simulations = self.num_simulations % self.num_processes
        
        # 使用進程池執行並行搜索
        with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
            futures = []
            
            for i in range(self.num_processes):
                sims = simulations_per_process
                if i < remaining_simulations:
                    sims += 1
                
                future = executor.submit(
                    self._run_simulations_batch,
                    root, sims, available_cards, time_limit - (time.time() - start_time)
                )
                futures.append(future)
            
            # 收集結果並合併
            batch_results = []
            for future in futures:
                if time.time() - start_time >= time_limit:
                    break
                try:
                    result = future.result(timeout=time_limit - (time.time() - start_time))
                    batch_results.append(result)
                except:
                    pass
        
        # 合併結果
        final_result = self._merge_results(batch_results)
        
        # 緩存結果
        self.cache_manager.put(cache_key, final_result)
        
        # 統計信息
        elapsed_time = time.time() - start_time
        actual_simulations = sum(r.get('simulations', 0) for r in batch_results)
        
        final_result['stats'] = {
            'total_simulations': actual_simulations,
            'time_elapsed': elapsed_time,
            'simulations_per_second': actual_simulations / elapsed_time if elapsed_time > 0 else 0,
            'cache_stats': self.cache_manager.get_stats()
        }
        
        return final_result
    
    def _run_simulations_batch(self, root: MCTSNode, 
                              num_simulations: int,
                              available_cards: List[Card],
                              time_limit: float) -> Dict[str, Any]:
        """運行一批模擬"""
        start_time = time.time()
        action_scores = defaultdict(float)
        action_visits = defaultdict(int)
        
        for _ in range(num_simulations):
            if time.time() - start_time >= time_limit:
                break
            
            # 執行單次 MCTS 迭代
            node = self._select(root)
            
            if not node.is_terminal and node.untried_actions:
                node = self._expand(node, available_cards)
            
            score = self._simulate(node.state, available_cards)
            self._backpropagate(node, score)
            
            # 記錄根節點的動作統計
            for action, child in root.children.items():
                action_scores[action] += child.total_score
                action_visits[action] += child.visits
        
        # 返回批次結果
        return {
            'action_scores': dict(action_scores),
            'action_visits': dict(action_visits),
            'simulations': sum(action_visits.values())
        }
    
    def _select(self, node: MCTSNode) -> MCTSNode:
        """選擇階段 - 使用 UCT"""
        while node.children and not node.is_terminal:
            if node.untried_actions:
                return node
            node = node.best_child()
        return node
    
    def _expand(self, node: MCTSNode, available_cards: List[Card]) -> MCTSNode:
        """擴展階段"""
        action = node.untried_actions.pop(random.randrange(len(node.untried_actions)))
        
        # 應用動作創建新狀態
        new_state = node.state.copy()
        self._apply_action(new_state, action)
        
        # 創建子節點
        child = MCTSNode(
            state=new_state,
            parent=node,
            action=action
        )
        
        # 檢查是否終止
        if new_state.is_complete():
            child.is_terminal = True
        else:
            child.untried_actions = self._get_possible_actions(new_state, available_cards)
        
        node.children[action] = child
        return child
    
    def _simulate(self, state: PineappleState, available_cards: List[Card]) -> float:
        """模擬階段 - 使用啟發式快速模擬"""
        sim_state = state.copy()
        
        # 快速隨機完成遊戲
        while not sim_state.is_complete():
            actions = self._get_possible_actions(sim_state, available_cards)
            if not actions:
                break
            
            # 使用啟發式選擇動作（而不是完全隨機）
            action = self._heuristic_action_selection(sim_state, actions)
            self._apply_action(sim_state, action)
        
        # 評估最終狀態
        return self._evaluate_final_state(sim_state)
    
    def _backpropagate(self, node: MCTSNode, score: float):
        """回傳階段"""
        while node is not None:
            node.update(score)
            node = node.parent
    
    def _merge_results(self, batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合併多個批次的結果"""
        merged_scores = defaultdict(float)
        merged_visits = defaultdict(int)
        
        for result in batch_results:
            for action, score in result.get('action_scores', {}).items():
                merged_scores[action] += score
            for action, visits in result.get('action_visits', {}).items():
                merged_visits[action] += visits
        
        # 找出最佳動作
        best_action = None
        best_avg_score = -float('inf')
        
        for action in merged_scores:
            if merged_visits[action] > 0:
                avg_score = merged_scores[action] / merged_visits[action]
                if avg_score > best_avg_score:
                    best_avg_score = avg_score
                    best_action = action
        
        return {
            'best_action': best_action,
            'action_scores': dict(merged_scores),
            'action_visits': dict(merged_visits),
            'best_score': best_avg_score
        }
    
    def _get_possible_actions(self, state: PineappleState, 
                            available_cards: List[Card]) -> List[Any]:
        """獲取可能的動作 - 智能剪枝"""
        actions = []
        positions = state.get_available_positions()
        
        # 剪枝策略：限制考慮的牌數
        cards_to_consider = available_cards[:10]  # 只考慮前10張牌
        
        for card in cards_to_consider:
            for position in positions:
                # 剪枝：跳過明顯不合理的擺放
                if self._is_reasonable_placement(state, card, position):
                    actions.append((card, position))
        
        return actions
    
    def _is_reasonable_placement(self, state: PineappleState, 
                               card: Card, position: str) -> bool:
        """判斷擺放是否合理 - 用於剪枝"""
        # 鬼牌優先放前墩
        if card.is_joker() and position == 'back':
            return False
        
        # 小牌不放後墩
        if not card.is_joker() and position == 'back' and RANK_VALUES[card.rank] < 10:
            return len(state.back_hand.cards) >= 3  # 除非後墩快滿了
        
        return True
    
    def _heuristic_action_selection(self, state: PineappleState, 
                                  actions: List[Any]) -> Any:
        """啟發式動作選擇"""
        # 評分每個動作
        action_scores = []
        
        for action in actions:
            card, position = action
            score = 0.0
            
            # 鬼牌優先放前墩
            if card.is_joker() and position == 'front':
                score += 10.0
            
            # 大牌優先放後墩
            if not card.is_joker():
                if position == 'back':
                    score += RANK_VALUES[card.rank] * 0.3
                elif position == 'middle':
                    score += RANK_VALUES[card.rank] * 0.2
                else:
                    score += RANK_VALUES[card.rank] * 0.1
            
            action_scores.append((action, score))
        
        # 使用輪盤賭選擇（帶權重的隨機）
        total_score = sum(s for _, s in action_scores)
        if total_score <= 0:
            return random.choice(actions)
        
        r = random.uniform(0, total_score)
        cumsum = 0
        for action, score in action_scores:
            cumsum += score
            if cumsum >= r:
                return action
        
        return action_scores[-1][0]
    
    def _apply_action(self, state: PineappleState, action: Any):
        """應用動作到狀態"""
        card, position = action
        state.place_card(card, position)
    
    def _evaluate_final_state(self, state: PineappleState) -> float:
        """評估最終狀態"""
        if not state.is_valid():
            return -100.0  # 犯規懲罰
        
        score = 0.0
        
        # 評估各手牌
        front_rank, front_score = state.front_hand.evaluate()
        middle_rank, middle_score = state.middle_hand.evaluate()
        back_rank, back_score = state.back_hand.evaluate()
        
        # 基礎分數
        score += front_score * 0.3
        score += middle_score * 0.3
        score += back_score * 0.4
        
        # 夢幻樂園獎勵
        if state.has_fantasy_land():
            score += 20.0
        
        # 特殊牌型獎勵
        score += self._calculate_royalties(state)
        
        return score
    
    def _calculate_royalties(self, state: PineappleState) -> float:
        """計算特殊牌型獎勵"""
        royalties = 0.0
        
        # 前墩獎勵
        front_rank, _ = state.front_hand.evaluate()
        if front_rank >= 8:  # 三條或更好
            royalties += (front_rank - 7) * 2
        
        # 中墩獎勵
        middle_rank, _ = state.middle_hand.evaluate()
        if middle_rank >= 6:  # 順子或更好
            royalties += (middle_rank - 5) * 1
        
        # 後墩獎勵
        back_rank, _ = state.back_hand.evaluate()
        if back_rank >= 7:  # 葫蘆或更好
            royalties += (back_rank - 6) * 1.5
        
        return royalties


class OptimizedStreetByStreetSolver:
    """優化版逐街求解器"""
    
    def __init__(self, include_jokers: bool = True, 
                 num_simulations: int = 100000):
        self.include_jokers = include_jokers
        self.num_simulations = num_simulations
        self.cache_manager = CacheManager()
        self.mcts = ParallelMCTS(
            num_simulations=num_simulations,
            cache_manager=self.cache_manager
        )
        self.full_deck = create_full_deck(include_jokers=include_jokers)
    
    def deal_random_initial(self) -> List[Card]:
        """隨機發5張初始手牌"""
        deck = self.full_deck.copy()
        random.shuffle(deck)
        return [deck.pop() for _ in range(5)]
    
    def solve_game(self, initial_five_cards: Optional[List[Card]] = None,
                   use_mcts_for_initial: bool = True) -> Dict[str, Any]:
        """求解完整遊戲"""
        start_time = time.time()
        
        # 初始化
        player_state = PineappleState()
        opponent_tracker = OpponentTracker()
        
        # 處理初始手牌
        if initial_five_cards is None:
            initial_five_cards = self.deal_random_initial()
            print(f"隨機發牌: {' '.join(str(c) for c in initial_five_cards)}")
        
        # 創建剩餘牌堆
        deck = self.full_deck.copy()
        for card in initial_five_cards:
            deck.remove(card)
        
        remaining_deck = deck.copy()
        random.shuffle(remaining_deck)
        
        # 結果記錄
        results = {
            'initial_cards': [str(c) for c in initial_five_cards],
            'streets': [],
            'final_state': None,
            'performance': {}
        }
        
        # 第0街：初始5張牌
        print("\n=== 初始擺放階段 ===")
        
        if use_mcts_for_initial:
            # 使用 MCTS 求解初始擺放
            initial_result = self._solve_initial_with_mcts(
                initial_five_cards, player_state, remaining_deck
            )
        else:
            # 使用啟發式方法
            initial_result = self._solve_initial_heuristic(
                initial_five_cards, player_state
            )
        
        results['streets'].append({
            'street': 'INITIAL',
            'result': initial_result
        })
        
        # 後續街道處理（簡化版）
        for street_num in range(1, 5):
            print(f"\n=== 第{street_num}街 ===")
            
            if len(remaining_deck) < 3:
                break
            
            street_cards = [remaining_deck.pop() for _ in range(3)]
            street_result = self._solve_draw_street(
                street_cards, player_state, remaining_deck
            )
            
            results['streets'].append({
                'street': f'STREET_{street_num}',
                'result': street_result
            })
        
        # 最終結果
        results['final_state'] = self._get_final_state_summary(player_state)
        results['performance'] = {
            'total_time': time.time() - start_time,
            'cache_stats': self.cache_manager.get_stats(),
            'simulations_total': self.num_simulations * len(results['streets'])
        }
        
        print("\n=== 最終結果 ===")
        self._print_final_result(player_state)
        print(f"\n性能統計:")
        print(f"- 總時間: {results['performance']['total_time']:.2f}秒")
        print(f"- 緩存命中率: {results['performance']['cache_stats']['hit_rate']:.2%}")
        
        return results
    
    def _solve_initial_with_mcts(self, cards: List[Card], 
                                player_state: PineappleState,
                                remaining_deck: List[Card]) -> Dict[str, Any]:
        """使用 MCTS 求解初始5張牌"""
        print(f"使用 MCTS ({self.num_simulations:,} 次模擬) 求解初始擺放...")
        
        # 生成所有可能的初始擺放
        all_placements = self._generate_initial_placements(cards)
        
        if not all_placements:
            # 如果沒有生成擺放，使用默認啟發式
            return self._solve_initial_heuristic(cards, player_state)
        
        best_placement = None
        best_score = -float('inf')
        
        # 評估每種擺放
        for placement in all_placements[:100]:  # 限制評估數量
            temp_state = player_state.copy()
            
            # 應用擺放
            for card, position in placement:
                temp_state.place_card(card, position)
            
            # 使用 MCTS 評估這個起始狀態
            mcts_result = self.mcts.search(
                temp_state, 
                remaining_deck[:20],  # 只考慮接下來的20張牌
                time_limit=0.05  # 每個擺放 50ms
            )
            
            score = mcts_result.get('best_score', 0)
            
            if score > best_score:
                best_score = score
                best_placement = placement
        
        # 檢查是否找到擺放
        if best_placement is None:
            # 如果沒有找到有效擺放，使用啟發式方法
            return self._solve_initial_heuristic(cards, player_state)
        
        # 應用最佳擺放
        for card, position in best_placement:
            player_state.place_card(card, position)
        
        print(f"最佳擺放: {[(str(c), pos) for c, pos in best_placement]}")
        print(f"預期分數: {best_score:.2f}")
        
        return {
            'placement': [(str(c), pos) for c, pos in best_placement],
            'score': best_score,
            'method': 'MCTS'
        }
    
    def _solve_initial_heuristic(self, cards: List[Card], 
                               player_state: PineappleState) -> Dict[str, Any]:
        """使用啟發式方法求解初始5張牌"""
        # 識別特殊牌
        jokers = [c for c in cards if c.is_joker()]
        regular_cards = [c for c in cards if not c.is_joker()]
        
        # 排序普通牌
        sorted_regular = sorted(regular_cards, 
                              key=lambda c: RANK_VALUES[c.rank], 
                              reverse=True)
        
        placement = []
        
        # 優化的啟發式策略
        if jokers:
            # 有鬼牌：優先爭取夢幻樂園
            placement.append((jokers[0], 'front'))
            
            if len(jokers) > 1:
                # 第二張鬼牌放中墩
                placement.append((jokers[1], 'middle'))
                
            # 剩餘的牌
            remaining = sorted_regular
            
            # 大牌放後墩
            for i in range(min(2, len(remaining))):
                placement.append((remaining[i], 'back'))
            
            # 中等牌放中墩
            for i in range(2, min(4, len(remaining))):
                placement.append((remaining[i], 'middle'))
            
            # 剩餘放前墩
            for i in range(4, len(remaining)):
                placement.append((remaining[i], 'front'))
        else:
            # 無鬼牌：標準分配
            if len(sorted_regular) >= 5:
                placement = [
                    (sorted_regular[0], 'back'),
                    (sorted_regular[1], 'back'),
                    (sorted_regular[2], 'middle'),
                    (sorted_regular[3], 'middle'),
                    (sorted_regular[4], 'front')
                ]
        
        # 應用擺放
        for card, position in placement:
            player_state.place_card(card, position)
        
        return {
            'placement': [(str(c), pos) for c, pos in placement],
            'method': 'heuristic'
        }
    
    def _generate_initial_placements(self, cards: List[Card]) -> List[List[Tuple[Card, str]]]:
        """生成所有可能的初始擺放組合"""
        # 這是一個簡化版本，實際可以生成更多組合
        placements = []
        
        # 生成一些合理的擺放模式
        patterns = [
            ['back', 'back', 'middle', 'middle', 'front'],
            ['back', 'middle', 'middle', 'front', 'back'],
            ['middle', 'back', 'back', 'middle', 'front'],
            ['front', 'middle', 'middle', 'back', 'back'],
        ]
        
        for pattern in patterns:
            placement = list(zip(cards, pattern))
            placements.append(placement)
        
        return placements
    
    def _solve_draw_street(self, cards: List[Card], 
                          player_state: PineappleState,
                          remaining_deck: List[Card]) -> Dict[str, Any]:
        """求解抽牌街道"""
        print(f"抽到: {' '.join(str(c) for c in cards)}")
        
        # 生成所有可能的動作（2張擺放+1張棄牌）
        actions = []
        positions = player_state.get_available_positions()
        
        for discard_idx in range(3):
            cards_to_place = [cards[i] for i in range(3) if i != discard_idx]
            card_to_discard = cards[discard_idx]
            
            for pos1 in positions:
                for pos2 in positions:
                    action = {
                        'placements': [(cards_to_place[0], pos1), 
                                     (cards_to_place[1], pos2)],
                        'discard': card_to_discard
                    }
                    actions.append(action)
        
        # 快速評估每個動作
        best_action = None
        best_score = -float('inf')
        
        for action in actions:
            temp_state = player_state.copy()
            
            # 應用動作
            valid = True
            for card, position in action['placements']:
                if not temp_state.place_card(card, position):
                    valid = False
                    break
            
            if not valid:
                continue
            
            # 快速評估
            score = self._quick_evaluate_state(temp_state, action['discard'])
            
            if score > best_score:
                best_score = score
                best_action = action
        
        # 應用最佳動作
        if best_action:
            for card, position in best_action['placements']:
                player_state.place_card(card, position)
            player_state.discarded.append(best_action['discard'])
            
            print(f"擺放: {[(str(c), pos) for c, pos in best_action['placements']]}")
            print(f"棄牌: {best_action['discard']}")
        
        return {
            'placements': [(str(c), pos) for c, pos in best_action['placements']] if best_action else [],
            'discard': str(best_action['discard']) if best_action else None
        }
    
    def _quick_evaluate_state(self, state: PineappleState, discard: Card) -> float:
        """快速評估狀態"""
        score = 0.0
        
        # 手牌強度
        front_rank, _ = state.front_hand.evaluate()
        middle_rank, _ = state.middle_hand.evaluate()
        back_rank, _ = state.back_hand.evaluate()
        
        score += front_rank * 1.0
        score += middle_rank * 2.0
        score += back_rank * 3.0
        
        # 夢幻樂園
        if state.has_fantasy_land():
            score += 10.0
        
        # 棄牌懲罰
        if discard.is_joker():
            score -= 20.0
        else:
            score -= RANK_VALUES[discard.rank] * 0.1
        
        return score
    
    def _get_final_state_summary(self, player_state: PineappleState) -> Dict[str, Any]:
        """獲取最終狀態摘要"""
        return {
            'front': [str(c) for c in player_state.front_hand.cards],
            'middle': [str(c) for c in player_state.middle_hand.cards],
            'back': [str(c) for c in player_state.back_hand.cards],
            'discarded': [str(c) for c in player_state.discarded],
            'is_valid': player_state.is_valid(),
            'fantasy_land': player_state.has_fantasy_land()
        }
    
    def _print_final_result(self, player_state: PineappleState):
        """打印最終結果"""
        print(f"前墩: {' '.join(str(c) for c in player_state.front_hand.cards)}")
        print(f"中墩: {' '.join(str(c) for c in player_state.middle_hand.cards)}")
        print(f"後墩: {' '.join(str(c) for c in player_state.back_hand.cards)}")
        print(f"棄牌: {' '.join(str(c) for c in player_state.discarded)}")
        
        if player_state.is_valid():
            print("✓ 有效擺放")
            if player_state.has_fantasy_land():
                print("✨ 進入夢幻樂園!")
        else:
            print("✗ 無效擺放（犯規）")


def performance_test():
    """性能測試"""
    print("=== OFC Solver 性能測試 ===\n")
    
    # 測試不同模擬次數的性能
    simulation_counts = [1000, 10000, 50000, 100000]
    
    for num_sims in simulation_counts:
        print(f"\n--- 測試 {num_sims:,} 次模擬 ---")
        
        solver = OptimizedStreetByStreetSolver(
            include_jokers=True,
            num_simulations=num_sims
        )
        
        # 測試3輪
        total_time = 0
        for i in range(3):
            start = time.time()
            
            # 隨機初始手牌
            initial_cards = solver.deal_random_initial()
            
            # 只測試初始擺放的 MCTS
            player_state = PineappleState()
            remaining_deck = solver.full_deck.copy()
            for card in initial_cards:
                remaining_deck.remove(card)
            
            result = solver._solve_initial_with_mcts(
                initial_cards, player_state, remaining_deck
            )
            
            elapsed = time.time() - start
            total_time += elapsed
            
            print(f"  輪 {i+1}: {elapsed:.3f}秒")
        
        avg_time = total_time / 3
        print(f"  平均時間: {avg_time:.3f}秒")
        print(f"  模擬速度: {num_sims/avg_time:,.0f} 次/秒")


def main():
    """主測試函數"""
    # 創建優化求解器
    solver = OptimizedStreetByStreetSolver(
        include_jokers=True,
        num_simulations=100000
    )
    
    print("=== 測試1：隨機初始手牌 ===")
    # 測試隨機發牌功能
    for i in range(3):
        print(f"\n第 {i+1} 次發牌:")
        cards = solver.deal_random_initial()
        print(f"發到: {' '.join(str(c) for c in cards)}")
    
    print("\n\n=== 測試2：完整遊戲求解 ===")
    # 測試完整遊戲
    result = solver.solve_game(use_mcts_for_initial=True)
    
    print("\n\n=== 測試3：性能基準測試 ===")
    performance_test()


if __name__ == "__main__":
    main()