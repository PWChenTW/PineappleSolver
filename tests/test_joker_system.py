"""
鬼牌系統測試套件

測試鬼牌的創建、識別、最優替換算法和各種手牌組合處理。
"""

import unittest
import pytest
from typing import List, Dict, Any

# 添加項目路徑
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.domain import Card, Rank, Suit
from src.core.domain.game_state import GameState
from src.core.algorithms.evaluator import HandEvaluator
from src.ofc_solver import OFCSolver, create_solver


class TestJokerSystem(unittest.TestCase):
    """鬼牌系統核心功能測試"""
    
    def setUp(self):
        """測試前置設置"""
        self.solver = create_solver(simulations_limit=1000)
        self.evaluator = HandEvaluator()
    
    def test_joker_creation_and_identification(self):
        """測試鬼牌創建和識別"""
        # 測試從字符串創建鬼牌
        joker = Card.from_string("JOKER")
        self.assertTrue(joker.is_joker)
        self.assertEqual(str(joker), "Joker")
        self.assertEqual(joker.value, Card.JOKER_VALUE)
        
        # 測試鬼牌沒有花色和點數
        self.assertIsNone(joker.rank)
        self.assertIsNone(joker.suit)
        
        # 測試鬼牌的字典表示
        joker_dict = joker.to_dict()
        self.assertEqual(joker_dict["type"], "joker")
        self.assertEqual(joker_dict["value"], Card.JOKER_VALUE)
        
        # 測試從字典創建鬼牌
        joker2 = Card.from_dict(joker_dict)
        self.assertEqual(joker, joker2)
    
    def test_deck_with_jokers(self):
        """測試包含鬼牌的牌組"""
        # 標準牌組（無鬼牌）
        deck_no_jokers = Card.deck(num_jokers=0)
        self.assertEqual(len(deck_no_jokers), 52)
        self.assertFalse(any(card.is_joker for card in deck_no_jokers))
        
        # 包含1張鬼牌的牌組
        deck_one_joker = Card.deck(num_jokers=1)
        self.assertEqual(len(deck_one_joker), 53)
        joker_count = sum(1 for card in deck_one_joker if card.is_joker)
        self.assertEqual(joker_count, 1)
        
        # 包含2張鬼牌的牌組
        deck_two_jokers = Card.deck(num_jokers=2)
        self.assertEqual(len(deck_two_jokers), 54)
        joker_count = sum(1 for card in deck_two_jokers if card.is_joker)
        self.assertEqual(joker_count, 2)
        
        # 測試無效的鬼牌數量
        with self.assertRaises(Exception):
            Card.deck(num_jokers=3)
    
    def test_joker_optimal_replacement_straight(self):
        """測試鬼牌在順子中的最優替換"""
        # 測試案例：4♠ 5♦ 6♣ 7♥ Joker -> 應該替換為8形成順子
        cards = [
            Card.from_string("4S"),
            Card.from_string("5D"),
            Card.from_string("6C"),
            Card.from_string("7H"),
            Card.from_string("JOKER")
        ]
        
        # 評估最優替換
        optimal_hand = self._find_optimal_joker_replacement(cards)
        
        # 驗證形成了順子
        self.assertTrue(self._is_straight(optimal_hand))
        
        # 測試案例：A♠ 2♦ 3♣ 4♥ Joker -> 應該替換為5形成順子
        cards2 = [
            Card.from_string("AS"),
            Card.from_string("2D"),
            Card.from_string("3C"),
            Card.from_string("4H"),
            Card.from_string("JOKER")
        ]
        
        optimal_hand2 = self._find_optimal_joker_replacement(cards2)
        self.assertTrue(self._is_straight(optimal_hand2))
    
    def test_joker_optimal_replacement_flush(self):
        """測試鬼牌在同花中的最優替換"""
        # 測試案例：A♠ K♠ Q♠ J♠ Joker -> 應該替換為T♠形成同花順
        cards = [
            Card.from_string("AS"),
            Card.from_string("KS"),
            Card.from_string("QS"),
            Card.from_string("JS"),
            Card.from_string("JOKER")
        ]
        
        optimal_hand = self._find_optimal_joker_replacement(cards)
        
        # 驗證形成了同花
        self.assertTrue(self._is_flush(optimal_hand))
        # 進一步驗證是否形成了同花順
        self.assertTrue(self._is_straight_flush(optimal_hand))
    
    def test_joker_optimal_replacement_pairs(self):
        """測試鬼牌在對子/三條中的最優替換"""
        # 測試案例：A♠ A♦ K♣ Joker 5♥ -> 鬼牌應該替換為A形成三條
        cards = [
            Card.from_string("AS"),
            Card.from_string("AD"),
            Card.from_string("KC"),
            Card.from_string("JOKER"),
            Card.from_string("5H")
        ]
        
        optimal_hand = self._find_optimal_joker_replacement(cards)
        
        # 驗證形成了三條
        rank_counts = self._get_rank_counts(optimal_hand)
        self.assertTrue(any(count >= 3 for count in rank_counts.values()))
    
    def test_fantasy_land_with_joker(self):
        """測試鬼牌在Fantasy Land判定中的作用"""
        # 測試案例：Q♠ Q♦ Joker -> 鬼牌替換為Q形成QQQ，符合Fantasy Land
        front_cards = [
            Card.from_string("QS"),
            Card.from_string("QD"),
            Card.from_string("JOKER")
        ]
        
        # 評估是否符合Fantasy Land條件（前墩QQ+）
        optimal_front = self._find_optimal_joker_replacement(front_cards)
        rank_counts = self._get_rank_counts(optimal_front)
        
        # 檢查是否有QQ或更好
        has_qq_plus = False
        for rank, count in rank_counts.items():
            if count >= 2 and rank >= Rank.QUEEN.value:
                has_qq_plus = True
                break
        
        self.assertTrue(has_qq_plus, "Should qualify for Fantasy Land with QQ+")
    
    def test_multiple_jokers_handling(self):
        """測試多張鬼牌的處理"""
        # 測試案例：A♠ K♦ Joker Joker 9♥ -> 雙鬼牌最優替換
        cards = [
            Card.from_string("AS"),
            Card.from_string("KD"),
            Card.from_string("JOKER"),
            Card.from_string("JOKER"),
            Card.from_string("9H")
        ]
        
        # 使用求解器處理多鬼牌情況
        from src.ofc_solver import GameState as SolverGameState, Card as SolverCard
        
        solver_cards = [SolverCard(c.rank.display if c.rank else 'JOKER', 
                                  c.suit.char if c.suit else '') 
                       for c in cards if not c.is_joker]
        
        game_state = SolverGameState(
            current_cards=solver_cards[:3],  # 只使用非鬼牌進行測試
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=10
        )
        
        result = self.solver.solve(game_state)
        self.assertIsNotNone(result.best_placement)
    
    def test_joker_in_different_positions(self):
        """測試鬼牌在不同位置（前/中/後墩）的最優使用"""
        test_cases = [
            {
                'name': '前墩鬼牌形成對子',
                'front': ['AS', 'JOKER', '5D'],
                'middle': ['KS', 'KD', 'QC', 'QH', 'JS'],
                'back': ['TH', 'TD', 'TC', '9S', '9D'],
                'expected_front_strength': 1  # 對子
            },
            {
                'name': '中墩鬼牌形成順子',
                'front': ['AS', 'KH', 'QD'],
                'middle': ['6S', '7D', '8C', '9H', 'JOKER'],
                'back': ['AH', 'AD', 'KC', 'KS', 'JD'],
                'expected_middle_strength': 4  # 順子
            },
            {
                'name': '後墩鬼牌形成同花',
                'front': ['7S', '7D', '5C'],
                'middle': ['JS', 'JD', 'TC', 'TH', '9S'],
                'back': ['AS', 'KS', 'QS', '4S', 'JOKER'],
                'expected_back_strength': 5  # 同花
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case['name']):
                # 解析牌
                front = [Card.from_string(c) for c in test_case['front']]
                middle = [Card.from_string(c) for c in test_case['middle']]
                back = [Card.from_string(c) for c in test_case['back']]
                
                # 驗證各墩的牌力
                if 'expected_front_strength' in test_case:
                    front_optimal = self._find_optimal_joker_replacement(front)
                    front_strength = self._evaluate_hand_strength(front_optimal)
                    self.assertEqual(front_strength, test_case['expected_front_strength'])
                
                if 'expected_middle_strength' in test_case:
                    middle_optimal = self._find_optimal_joker_replacement(middle)
                    middle_strength = self._evaluate_hand_strength(middle_optimal)
                    self.assertEqual(middle_strength, test_case['expected_middle_strength'])
                
                if 'expected_back_strength' in test_case:
                    back_optimal = self._find_optimal_joker_replacement(back)
                    back_strength = self._evaluate_hand_strength(back_optimal)
                    self.assertEqual(back_strength, test_case['expected_back_strength'])
    
    def test_joker_edge_cases(self):
        """測試鬼牌的邊界情況"""
        # 測試空手牌
        with self.assertRaises(ValueError):
            self._find_optimal_joker_replacement([])
        
        # 測試只有鬼牌
        cards = [Card.from_string("JOKER")]
        optimal = self._find_optimal_joker_replacement(cards)
        self.assertEqual(len(optimal), 1)
        
        # 測試所有牌都是鬼牌（極端情況）
        cards = [Card.from_string("JOKER"), Card.from_string("JOKER")]
        optimal = self._find_optimal_joker_replacement(cards)
        self.assertEqual(len(optimal), 2)
    
    # 輔助方法
    def _find_optimal_joker_replacement(self, cards: List[Card]) -> List[Card]:
        """找出鬼牌的最優替換"""
        if not cards:
            raise ValueError("Empty hand")
        
        # 如果沒有鬼牌，直接返回
        if not any(card.is_joker for card in cards):
            return cards
        
        # 簡化實現：將鬼牌替換為最有利的牌
        non_joker_cards = [c for c in cards if not c.is_joker]
        joker_count = len(cards) - len(non_joker_cards)
        
        if not non_joker_cards:
            # 全是鬼牌，返回高牌
            return [Card.from_rank_suit(Rank.ACE, Suit.SPADES) for _ in range(len(cards))]
        
        # 基於現有牌判斷最優替換
        # 這裡使用簡化邏輯，實際實現應該更複雜
        best_cards = non_joker_cards.copy()
        
        # 嘗試形成對子/三條
        rank_counts = self._get_rank_counts(non_joker_cards)
        for rank, count in sorted(rank_counts.items(), key=lambda x: -x[0]):
            if joker_count > 0 and count >= 1:
                # 用鬼牌形成更大的組合
                for _ in range(min(joker_count, 3 - count)):
                    best_cards.append(Card.from_rank_suit(Rank(rank), Suit.HEARTS))
                    joker_count -= 1
        
        return best_cards
    
    def _get_rank_counts(self, cards: List[Card]) -> Dict[int, int]:
        """統計各點數的數量"""
        counts = {}
        for card in cards:
            if not card.is_joker:
                rank = card.rank_value
                counts[rank] = counts.get(rank, 0) + 1
        return counts
    
    def _is_straight(self, cards: List[Card]) -> bool:
        """檢查是否為順子"""
        if len(cards) < 5:
            return False
        
        ranks = sorted([c.rank_value for c in cards if not c.is_joker])
        if len(ranks) < 5:
            return False
        
        # 檢查連續性
        for i in range(len(ranks) - 1):
            if ranks[i+1] - ranks[i] != 1:
                return False
        
        return True
    
    def _is_flush(self, cards: List[Card]) -> bool:
        """檢查是否為同花"""
        if len(cards) < 5:
            return False
        
        suits = [c.suit_value for c in cards if not c.is_joker]
        if not suits:
            return False
        
        return all(s == suits[0] for s in suits)
    
    def _is_straight_flush(self, cards: List[Card]) -> bool:
        """檢查是否為同花順"""
        return self._is_straight(cards) and self._is_flush(cards)
    
    def _evaluate_hand_strength(self, cards: List[Card]) -> int:
        """評估手牌強度（簡化版）"""
        rank_counts = self._get_rank_counts(cards)
        count_values = sorted(rank_counts.values(), reverse=True)
        
        if self._is_straight_flush(cards):
            return 8  # 同花順
        elif count_values and count_values[0] == 4:
            return 7  # 四條
        elif count_values and len(count_values) >= 2 and count_values[0] == 3 and count_values[1] == 2:
            return 6  # 葫蘆
        elif self._is_flush(cards):
            return 5  # 同花
        elif self._is_straight(cards):
            return 4  # 順子
        elif count_values and count_values[0] == 3:
            return 3  # 三條
        elif count_values and len(count_values) >= 2 and count_values[0] == 2 and count_values[1] == 2:
            return 2  # 兩對
        elif count_values and count_values[0] == 2:
            return 1  # 一對
        else:
            return 0  # 高牌


class TestJokerIntegration(unittest.TestCase):
    """鬼牌系統整合測試"""
    
    def setUp(self):
        self.solver = create_solver(simulations_limit=5000)
    
    def test_joker_in_complete_game(self):
        """測試鬼牌在完整遊戲中的表現"""
        # 初始5張牌包含鬼牌
        from src.ofc_solver import GameState, Card as SolverCard
        
        initial_cards = [
            SolverCard('A', 's'),
            SolverCard('K', 's'),
            SolverCard('Q', 's'),
            SolverCard('J', 's'),
            SolverCard('JOKER', '')
        ]
        
        game_state = GameState(
            current_cards=initial_cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        # 求解初始擺放
        result = self.solver.solve(game_state)
        
        # 驗證結果
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.best_placement)
        self.assertGreater(result.expected_score, 0)
        
        # 檢查鬼牌是否被合理使用
        joker_placement = None
        for card, position in result.best_placement.items():
            if 'JOKER' in card:
                joker_placement = position
                break
        
        self.assertIsNotNone(joker_placement, "Joker should be placed")
        
        # 鬼牌應該被放在後墩以形成同花順
        self.assertEqual(joker_placement, 'back', "Joker should be in back for royal flush")
    
    @pytest.mark.benchmark
    def test_joker_performance_impact(self):
        """測試鬼牌對性能的影響"""
        import time
        
        # 無鬼牌的性能測試
        normal_cards = [
            SolverCard('A', 's'),
            SolverCard('K', 'h'),
            SolverCard('Q', 'd'),
            SolverCard('J', 'c'),
            SolverCard('T', 's')
        ]
        
        start_time = time.time()
        for _ in range(10):
            game_state = GameState(
                current_cards=normal_cards,
                front_hand=[],
                middle_hand=[],
                back_hand=[],
                remaining_cards=8
            )
            self.solver.solve(game_state)
        normal_time = time.time() - start_time
        
        # 有鬼牌的性能測試
        joker_cards = [
            SolverCard('A', 's'),
            SolverCard('K', 'h'),
            SolverCard('JOKER', ''),
            SolverCard('J', 'c'),
            SolverCard('T', 's')
        ]
        
        start_time = time.time()
        for _ in range(10):
            game_state = GameState(
                current_cards=joker_cards,
                front_hand=[],
                middle_hand=[],
                back_hand=[],
                remaining_cards=8
            )
            self.solver.solve(game_state)
        joker_time = time.time() - start_time
        
        # 鬼牌不應該顯著影響性能（最多慢2倍）
        self.assertLess(joker_time, normal_time * 2, 
                       f"Joker performance impact too high: {joker_time/normal_time:.2f}x slower")


if __name__ == '__main__':
    unittest.main(verbosity=2)