#!/usr/bin/env python3
"""
OFC Pineapple Street-by-Street Solver
逐街求解器，支持對手追蹤和動態牌堆更新
"""

import random
import math
from typing import List, Dict, Tuple, Optional, Set, Union, Any
from dataclasses import dataclass, field
from collections import defaultdict
import time
from enum import Enum
from abc import ABC, abstractmethod

# Import base components from joker solver
from ofc_solver_joker import (
    Card, Hand, create_full_deck, RANKS, SUITS, RANK_VALUES,
    JokerHandEvaluator
)


class Street(Enum):
    """街道枚舉"""
    INITIAL = 0  # 初始5張牌
    FIRST = 1    # 第一街 (3張抽2張棄1張)
    SECOND = 2   # 第二街
    THIRD = 3    # 第三街
    FOURTH = 4   # 第四街
    COMPLETE = 5 # 完成


@dataclass
class OpponentCard:
    """對手的牌（可能是已知或未知）"""
    card: Optional[Card] = None
    is_known: bool = False
    position: Optional[str] = None  # 'front', 'middle', 'back'
    
    def __str__(self):
        if self.is_known and self.card:
            return str(self.card)
        return "??"


class OpponentTracker:
    """對手追蹤器 - 記錄對手使用的牌"""
    
    def __init__(self):
        self.known_cards: Set[Card] = set()
        self.front_cards: List[OpponentCard] = []
        self.middle_cards: List[OpponentCard] = []
        self.back_cards: List[OpponentCard] = []
        self.discarded_cards: Set[Card] = set()
        
    def add_known_card(self, card: Card, position: str):
        """添加已知的對手牌"""
        self.known_cards.add(card)
        opponent_card = OpponentCard(card=card, is_known=True, position=position)
        
        if position == 'front':
            self.front_cards.append(opponent_card)
        elif position == 'middle':
            self.middle_cards.append(opponent_card)
        elif position == 'back':
            self.back_cards.append(opponent_card)
    
    def add_unknown_cards(self, count: int, positions: List[str]):
        """添加未知的對手牌"""
        for i in range(count):
            pos = positions[i] if i < len(positions) else positions[-1]
            opponent_card = OpponentCard(is_known=False, position=pos)
            
            if pos == 'front':
                self.front_cards.append(opponent_card)
            elif pos == 'middle':
                self.middle_cards.append(opponent_card)
            elif pos == 'back':
                self.back_cards.append(opponent_card)
    
    def get_used_cards(self) -> Set[Card]:
        """獲取所有已使用的牌（包括已知的對手牌）"""
        return self.known_cards.copy()
    
    def get_opponent_state_summary(self) -> Dict[str, Any]:
        """獲取對手狀態摘要"""
        return {
            'front': len(self.front_cards),
            'middle': len(self.middle_cards),
            'back': len(self.back_cards),
            'known_cards': len(self.known_cards),
            'total_cards': len(self.front_cards) + len(self.middle_cards) + len(self.back_cards)
        }


@dataclass
class StreetState:
    """街道狀態 - 包含當前街道的所有信息"""
    street: Street
    player_state: 'PineappleState'
    opponent_tracker: OpponentTracker
    remaining_deck: List[Card]
    street_cards: List[Card] = field(default_factory=list)  # 本街道抽到的牌
    
    def copy(self) -> 'StreetState':
        """深度複製街道狀態"""
        new_state = StreetState(
            street=self.street,
            player_state=self.player_state.copy(),
            opponent_tracker=self.opponent_tracker,  # 對手追蹤器共享
            remaining_deck=self.remaining_deck.copy(),
            street_cards=self.street_cards.copy()
        )
        return new_state


class PineappleState:
    """玩家遊戲狀態"""
    
    def __init__(self):
        self.front_hand = Hand(max_size=3)
        self.middle_hand = Hand(max_size=5)
        self.back_hand = Hand(max_size=5)
        self.discarded: List[Card] = []
    
    def copy(self) -> 'PineappleState':
        new_state = PineappleState()
        new_state.front_hand = self.front_hand.copy()
        new_state.middle_hand = self.middle_hand.copy()
        new_state.back_hand = self.back_hand.copy()
        new_state.discarded = self.discarded.copy()
        return new_state
    
    def get_all_cards(self) -> Set[Card]:
        """獲取所有玩家的牌"""
        all_cards = set()
        all_cards.update(self.front_hand.cards)
        all_cards.update(self.middle_hand.cards)
        all_cards.update(self.back_hand.cards)
        all_cards.update(self.discarded)
        return all_cards
    
    def get_available_positions(self) -> List[str]:
        """獲取可以放牌的位置"""
        positions = []
        if not self.front_hand.is_full():
            positions.append('front')
        if not self.middle_hand.is_full():
            positions.append('middle')
        if not self.back_hand.is_full():
            positions.append('back')
        return positions
    
    def place_card(self, card: Card, position: str) -> bool:
        """放置一張牌"""
        if position == 'front':
            return self.front_hand.add_card(card)
        elif position == 'middle':
            return self.middle_hand.add_card(card)
        elif position == 'back':
            return self.back_hand.add_card(card)
        return False
    
    def is_complete(self) -> bool:
        """檢查是否完成"""
        return (self.front_hand.is_full() and 
                self.middle_hand.is_full() and 
                self.back_hand.is_full())
    
    def is_valid(self) -> bool:
        """檢查是否有效（不犯規）"""
        if not self.is_complete():
            return True
        
        front_rank, _ = self.front_hand.evaluate()
        middle_rank, _ = self.middle_hand.evaluate()
        back_rank, _ = self.back_hand.evaluate()
        
        return back_rank >= middle_rank >= front_rank
    
    def has_fantasy_land(self) -> bool:
        """檢查是否進入夢幻樂園"""
        return self.front_hand.get_fantasy_land_status()


class StreetSolver(ABC):
    """街道求解器基類"""
    
    @abstractmethod
    def solve_street(self, street_state: StreetState) -> Dict[str, Any]:
        """求解單個街道"""
        pass


class InitialStreetSolver(StreetSolver):
    """初始5張牌求解器"""
    
    def __init__(self, num_simulations: int = 5000):
        self.num_simulations = num_simulations
    
    def solve_street(self, street_state: StreetState) -> Dict[str, Any]:
        """求解初始5張牌的擺放"""
        cards = street_state.street_cards
        
        print(f"\n求解初始5張牌: {' '.join(str(c) for c in cards)}")
        
        # 使用MCTS找出最佳擺放
        best_placement = self._find_best_initial_placement(cards, street_state)
        
        # 應用最佳擺放
        for card, position in best_placement:
            street_state.player_state.place_card(card, position)
        
        return {
            'placement': best_placement,
            'fantasy_land': street_state.player_state.has_fantasy_land()
        }
    
    def _find_best_initial_placement(self, cards: List[Card], 
                                   street_state: StreetState) -> List[Tuple[Card, str]]:
        """使用啟發式方法找出最佳初始擺放"""
        # 識別鬼牌和普通牌
        jokers = [c for c in cards if c.is_joker()]
        regular_cards = [c for c in cards if not c.is_joker()]
        
        # 按牌力排序普通牌
        sorted_regular = sorted(regular_cards, 
                              key=lambda c: RANK_VALUES[c.rank], 
                              reverse=True)
        
        placements = []
        
        # 策略：如果有鬼牌，優先用於前墩爭取夢幻樂園
        if jokers:
            # 放一張鬼牌在前墩
            placements.append((jokers[0], 'front'))
            
            # 剩餘的牌
            remaining = sorted_regular + jokers[1:]
            
            # 強牌放後墩
            if len(remaining) >= 2:
                placements.append((remaining[0], 'back'))
                placements.append((remaining[1], 'back'))
            
            # 中等牌放中墩
            if len(remaining) >= 4:
                placements.append((remaining[2], 'middle'))
                placements.append((remaining[3], 'middle'))
        else:
            # 沒有鬼牌的標準擺放
            if len(sorted_regular) >= 5:
                placements.append((sorted_regular[0], 'back'))
                placements.append((sorted_regular[1], 'back'))
                placements.append((sorted_regular[2], 'middle'))
                placements.append((sorted_regular[3], 'middle'))
                placements.append((sorted_regular[4], 'front'))
        
        return placements


class DrawStreetSolver(StreetSolver):
    """抽牌街道求解器（第1-4街）"""
    
    def __init__(self, num_simulations: int = 3000):
        self.num_simulations = num_simulations
    
    def solve_street(self, street_state: StreetState) -> Dict[str, Any]:
        """求解抽3張擺2張棄1張"""
        cards = street_state.street_cards
        
        print(f"\n街道 {street_state.street.name}: 抽到 {' '.join(str(c) for c in cards)}")
        
        # 生成所有可能的動作
        actions = self._generate_actions(cards, street_state.player_state)
        
        # 評估每個動作
        best_action = self._evaluate_actions(actions, street_state)
        
        # 應用最佳動作
        placements, discard = best_action
        for card, position in placements:
            street_state.player_state.place_card(card, position)
        street_state.player_state.discarded.append(discard)
        
        print(f"擺放: {[(str(c), pos) for c, pos in placements]}")
        print(f"棄牌: {discard}")
        
        return {
            'placements': placements,
            'discard': discard
        }
    
    def _generate_actions(self, cards: List[Card], 
                         player_state: PineappleState) -> List[Tuple[List[Tuple[Card, str]], Card]]:
        """生成所有可能的動作"""
        actions = []
        positions = player_state.get_available_positions()
        
        # 對每張可能棄掉的牌
        for discard_idx in range(3):
            cards_to_place = [cards[i] for i in range(3) if i != discard_idx]
            card_to_discard = cards[discard_idx]
            
            # 生成所有可能的擺放組合
            for pos1 in positions:
                for pos2 in positions:
                    placement = [
                        (cards_to_place[0], pos1),
                        (cards_to_place[1], pos2)
                    ]
                    actions.append((placement, card_to_discard))
        
        return actions
    
    def _evaluate_actions(self, actions: List[Tuple[List[Tuple[Card, str]], Card]], 
                         street_state: StreetState) -> Tuple[List[Tuple[Card, str]], Card]:
        """評估動作並返回最佳動作"""
        best_score = -float('inf')
        best_action = None
        
        for placement, discard in actions:
            # 創建臨時狀態
            temp_state = street_state.player_state.copy()
            
            # 應用動作
            valid = True
            for card, position in placement:
                if not temp_state.place_card(card, position):
                    valid = False
                    break
            
            if not valid:
                continue
            
            # 評估這個狀態
            score = self._evaluate_state(temp_state, discard)
            
            if score > best_score:
                best_score = score
                best_action = (placement, discard)
        
        return best_action
    
    def _evaluate_state(self, state: PineappleState, discard: Card) -> float:
        """評估遊戲狀態"""
        score = 0.0
        
        # 評估各手牌強度
        front_rank, _ = state.front_hand.evaluate()
        middle_rank, _ = state.middle_hand.evaluate()
        back_rank, _ = state.back_hand.evaluate()
        
        # 基礎分數
        score += front_rank * 0.2
        score += middle_rank * 0.3
        score += back_rank * 0.5
        
        # 夢幻樂園獎勵
        if state.has_fantasy_land():
            score += 5.0
        
        # 棄牌懲罰（不要棄掉好牌）
        if discard.is_joker():
            score -= 10.0  # 絕不棄鬼牌
        else:
            score -= RANK_VALUES[discard.rank] * 0.1
        
        # 位置平衡獎勵
        positions_left = len(state.get_available_positions())
        if positions_left > 0:
            score += positions_left * 0.2
        
        return score


class StreetByStreetSolver:
    """逐街求解器主類"""
    
    def __init__(self, include_jokers: bool = True):
        self.include_jokers = include_jokers
        self.initial_solver = InitialStreetSolver()
        self.draw_solver = DrawStreetSolver()
        
    def solve_game(self, initial_five_cards: Optional[List[Card]] = None) -> Dict[str, Any]:
        """求解完整遊戲"""
        # 初始化
        player_state = PineappleState()
        opponent_tracker = OpponentTracker()
        
        # 創建牌堆
        deck = create_full_deck(include_jokers=self.include_jokers)
        
        # 如果提供了初始5張牌，從牌堆中移除
        if initial_five_cards:
            for card in initial_five_cards:
                deck.remove(card)
        else:
            # 隨機抽5張
            random.shuffle(deck)
            initial_five_cards = [deck.pop() for _ in range(5)]
        
        remaining_deck = deck.copy()
        random.shuffle(remaining_deck)
        
        # 結果記錄
        results = {
            'streets': [],
            'final_state': None,
            'opponent_state': None
        }
        
        # 第0街：初始5張牌
        print("\n=== 初始擺放階段 ===")
        street_state = StreetState(
            street=Street.INITIAL,
            player_state=player_state,
            opponent_tracker=opponent_tracker,
            remaining_deck=remaining_deck,
            street_cards=initial_five_cards
        )
        
        initial_result = self.initial_solver.solve_street(street_state)
        results['streets'].append({
            'street': Street.INITIAL.name,
            'result': initial_result
        })
        
        # 對手隨機擺5張
        self._simulate_opponent_initial(opponent_tracker, remaining_deck)
        
        # 第1-4街：抽3擺2棄1
        for street_num in range(1, 5):
            print(f"\n=== 第{street_num}街 ===")
            
            # 玩家抽3張
            if len(remaining_deck) < 3:
                print("牌堆不足！")
                break
            
            street_cards = [remaining_deck.pop() for _ in range(3)]
            
            street_state = StreetState(
                street=Street(street_num),
                player_state=player_state,
                opponent_tracker=opponent_tracker,
                remaining_deck=remaining_deck,
                street_cards=street_cards
            )
            
            draw_result = self.draw_solver.solve_street(street_state)
            results['streets'].append({
                'street': Street(street_num).name,
                'result': draw_result
            })
            
            # 對手隨機擺2張
            self._simulate_opponent_draw(opponent_tracker, remaining_deck)
        
        # 最終結果
        results['final_state'] = self._get_final_state_summary(player_state)
        results['opponent_state'] = opponent_tracker.get_opponent_state_summary()
        
        print("\n=== 最終結果 ===")
        self._print_final_result(player_state)
        
        return results
    
    def _simulate_opponent_initial(self, opponent_tracker: OpponentTracker, 
                                 remaining_deck: List[Card]):
        """模擬對手初始5張牌擺放"""
        if len(remaining_deck) < 5:
            return
        
        # 對手抽5張
        opponent_cards = [remaining_deck.pop() for _ in range(5)]
        
        # 簡單策略：2張放後墩，2張放中墩，1張放前墩
        positions = ['back', 'back', 'middle', 'middle', 'front']
        
        for card, pos in zip(opponent_cards, positions):
            opponent_tracker.add_known_card(card, pos)
        
        print(f"對手擺放了5張牌")
    
    def _simulate_opponent_draw(self, opponent_tracker: OpponentTracker, 
                              remaining_deck: List[Card]):
        """模擬對手抽牌街道"""
        if len(remaining_deck) < 3:
            return
        
        # 對手抽3張
        opponent_cards = [remaining_deck.pop() for _ in range(3)]
        
        # 隨機選2張擺放
        random.shuffle(opponent_cards)
        cards_to_place = opponent_cards[:2]
        
        # 簡單策略：優先填滿後墩和中墩
        opponent_summary = opponent_tracker.get_opponent_state_summary()
        positions = []
        
        if opponent_summary['back'] < 5:
            positions.append('back')
        if opponent_summary['middle'] < 5:
            positions.append('middle')
        if opponent_summary['front'] < 3:
            positions.append('front')
        
        # 擺放2張牌
        for i, card in enumerate(cards_to_place):
            if i < len(positions):
                opponent_tracker.add_known_card(card, positions[i])
            else:
                # 隨機選位置
                pos = random.choice(['front', 'middle', 'back'])
                opponent_tracker.add_known_card(card, pos)
        
        print(f"對手擺放了2張牌，棄掉1張")
    
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


def main():
    """測試逐街求解器"""
    solver = StreetByStreetSolver(include_jokers=True)
    
    # 測試1：指定初始5張牌
    print("=== 測試1：指定初始5張牌 ===")
    initial_cards = [
        Card.from_string("As"),
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Kc"),
        Card.joker()
    ]
    
    result1 = solver.solve_game(initial_cards)
    
    # 測試2：隨機初始5張牌
    print("\n\n=== 測試2：隨機初始5張牌 ===")
    result2 = solver.solve_game()
    
    # 輸出統計
    print("\n=== 遊戲統計 ===")
    print(f"總街道數: {len(result2['streets'])}")
    print(f"最終狀態: {'有效' if result2['final_state']['is_valid'] else '犯規'}")
    print(f"夢幻樂園: {'是' if result2['final_state']['fantasy_land'] else '否'}")


if __name__ == "__main__":
    main()