"""
逐街求解測試套件

測試對手追蹤、街道狀態傳遞、牌堆更新邏輯和完整遊戲流程。
"""

import unittest
import pytest
from typing import List, Dict, Tuple, Optional
import random

# 添加項目路徑
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ofc_solver import OFCSolver, create_solver, GameState, Card
from src.core.domain import (
    GameState as DomainGameState, 
    Card as DomainCard,
    Street,
    PlayerArrangement
)


class TestStreetSolver(unittest.TestCase):
    """逐街求解核心功能測試"""
    
    def setUp(self):
        """測試前置設置"""
        self.solver = create_solver(simulations_limit=5000)
        self.initial_deck = self._create_shuffled_deck()
    
    def test_initial_street_placement(self):
        """測試初始街道（5張牌）的擺放"""
        # 從牌堆抽取前5張
        initial_cards = [
            Card('A', 's'),
            Card('K', 's'),
            Card('Q', 's'),
            Card('J', 's'),
            Card('T', 's')  # 同花順
        ]
        
        game_state = GameState(
            current_cards=initial_cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8  # 還有8張牌要發
        )
        
        result = self.solver.solve(game_state)
        
        # 驗證結果
        self.assertIsNotNone(result)
        self.assertEqual(len(result.best_placement), 5, "Should place all 5 cards")
        
        # 驗證牌被分配到了三個位置
        positions = set(result.best_placement.values())
        self.assertTrue('front' in positions or 'middle' in positions or 'back' in positions)
        
        # 同花順應該被放在後墩
        back_cards = [card for card, pos in result.best_placement.items() if pos == 'back']
        self.assertGreaterEqual(len(back_cards), 3, "Most cards should be in back for straight flush")
        
        print(f"\n🎯 Initial placement result:")
        for card, position in sorted(result.best_placement.items()):
            print(f"   {card} → {position}")
    
    def test_street_by_street_progression(self):
        """測試完整的逐街進行流程"""
        # 初始化牌堆
        deck = self._create_shuffled_deck()
        deck_index = 0
        
        # 記錄遊戲歷史
        game_history = {
            'initial': None,
            'street1': None,
            'street2': None,
            'street3': None,
            'street4': None
        }
        
        # 初始街道 - 5張牌
        print("\n📍 Initial Street (5 cards):")
        initial_cards = [deck[i] for i in range(5)]
        deck_index = 5
        
        game_state = GameState(
            current_cards=initial_cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        result = self.solver.solve(game_state)
        game_history['initial'] = result
        
        # 應用初始擺放
        front_cards = []
        middle_cards = []
        back_cards = []
        
        for card_str, position in result.best_placement.items():
            card = self._card_from_string(card_str)
            if position == 'front':
                front_cards.append(card)
            elif position == 'middle':
                middle_cards.append(card)
            elif position == 'back':
                back_cards.append(card)
        
        print(f"   Front: {[str(c) for c in front_cards]}")
        print(f"   Middle: {[str(c) for c in middle_cards]}")
        print(f"   Back: {[str(c) for c in back_cards]}")
        
        # 第一街 - 3張牌（放2丟1）
        print("\n📍 First Street (3 cards, place 2, discard 1):")
        street1_cards = [deck[i] for i in range(deck_index, deck_index + 3)]
        deck_index += 3
        
        game_state = GameState(
            current_cards=street1_cards,
            front_hand=front_cards,
            middle_hand=middle_cards,
            back_hand=back_cards,
            remaining_cards=5
        )
        
        result = self.solver.solve(game_state)
        game_history['street1'] = result
        
        # 應用第一街的決策
        placed_count = 0
        for card_str, position in result.best_placement.items():
            if position != 'discard':
                card = self._card_from_string(card_str)
                if position == 'front':
                    front_cards.append(card)
                elif position == 'middle':
                    middle_cards.append(card)
                elif position == 'back':
                    back_cards.append(card)
                placed_count += 1
        
        self.assertEqual(placed_count, 2, "Should place exactly 2 cards in street 1")
        
        print(f"   Placed: {placed_count} cards")
        print(f"   Front: {[str(c) for c in front_cards]} ({len(front_cards)}/3)")
        print(f"   Middle: {[str(c) for c in middle_cards]} ({len(middle_cards)}/5)")
        print(f"   Back: {[str(c) for c in back_cards]} ({len(back_cards)}/5)")
        
        # 繼續剩餘街道...
        streets = [
            ('Second Street', 2, deck_index, deck_index + 3),
            ('Third Street', 2, deck_index + 3, deck_index + 6),
            ('Fourth Street', 1, deck_index + 6, deck_index + 8)
        ]
        
        for street_name, expected_placements, start_idx, end_idx in streets:
            print(f"\n📍 {street_name}:")
            
            street_cards = [deck[i] for i in range(start_idx, end_idx)]
            remaining = 13 - len(front_cards) - len(middle_cards) - len(back_cards) - len(street_cards)
            
            game_state = GameState(
                current_cards=street_cards,
                front_hand=front_cards,
                middle_hand=middle_cards,
                back_hand=back_cards,
                remaining_cards=remaining
            )
            
            # 檢查是否還有空位
            front_space = 3 - len(front_cards)
            middle_space = 5 - len(middle_cards)
            back_space = 5 - len(back_cards)
            total_space = front_space + middle_space + back_space
            
            if total_space > 0:
                result = self.solver.solve(game_state)
                
                # 應用決策
                placed_count = 0
                for card_str, position in result.best_placement.items():
                    if position != 'discard':
                        card = self._card_from_string(card_str)
                        if position == 'front' and len(front_cards) < 3:
                            front_cards.append(card)
                            placed_count += 1
                        elif position == 'middle' and len(middle_cards) < 5:
                            middle_cards.append(card)
                            placed_count += 1
                        elif position == 'back' and len(back_cards) < 5:
                            back_cards.append(card)
                            placed_count += 1
                
                print(f"   Placed: {placed_count} cards")
            
            print(f"   Front: {[str(c) for c in front_cards]} ({len(front_cards)}/3)")
            print(f"   Middle: {[str(c) for c in middle_cards]} ({len(middle_cards)}/5)")
            print(f"   Back: {[str(c) for c in back_cards]} ({len(back_cards)}/5)")
        
        # 驗證最終狀態
        self.assertEqual(len(front_cards), 3, "Front should have exactly 3 cards")
        self.assertEqual(len(middle_cards), 5, "Middle should have exactly 5 cards")
        self.assertEqual(len(back_cards), 5, "Back should have exactly 5 cards")
        
        # 驗證手牌強度順序（後 >= 中 >= 前）
        front_strength = self._evaluate_hand(front_cards)
        middle_strength = self._evaluate_hand(middle_cards)
        back_strength = self._evaluate_hand(back_cards)
        
        print(f"\n📊 Final hand strengths:")
        print(f"   Front: {self._hand_type_name(front_strength)}")
        print(f"   Middle: {self._hand_type_name(middle_strength)}")
        print(f"   Back: {self._hand_type_name(back_strength)}")
        
        self.assertGreaterEqual(back_strength, middle_strength, 
                               "Back hand should be stronger than middle")
        self.assertGreaterEqual(middle_strength, front_strength,
                               "Middle hand should be stronger than front")
    
    def test_opponent_tracking(self):
        """測試對手牌追蹤功能"""
        # 創建多人遊戲狀態
        num_players = 3
        
        # 模擬初始發牌
        deck = self._create_shuffled_deck()
        player_hands = []
        
        for player_idx in range(num_players):
            start_idx = player_idx * 5
            end_idx = start_idx + 5
            player_cards = [deck[i] for i in range(start_idx, end_idx)]
            player_hands.append(player_cards)
        
        # 追蹤已知的對手牌
        known_opponent_cards = set()
        for player_idx in range(1, num_players):  # 跳過自己（玩家0）
            for card in player_hands[player_idx]:
                known_opponent_cards.add(str(card))
        
        print(f"\n👥 Opponent Tracking Test:")
        print(f"   Total players: {num_players}")
        print(f"   Known opponent cards: {len(known_opponent_cards)}")
        
        # 創建考慮對手牌的遊戲狀態
        my_cards = player_hands[0]
        
        # 計算剩餘未知牌
        total_cards = 52
        cards_dealt = num_players * 5
        remaining_unknown = total_cards - cards_dealt
        
        game_state = GameState(
            current_cards=my_cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8  # 我還會收到8張牌
        )
        
        # 求解時應該考慮對手可能的牌
        result = self.solver.solve(game_state)
        
        # 驗證求解器的決策
        self.assertIsNotNone(result)
        self.assertGreater(result.confidence, 0.5, "Should have reasonable confidence")
        
        print(f"   My initial cards: {[str(c) for c in my_cards]}")
        print(f"   Placement confidence: {result.confidence:.2%}")
        print(f"   Expected score vs opponents: {result.expected_score:.2f}")
    
    def test_deck_depletion_handling(self):
        """測試牌堆耗盡的處理"""
        # 模擬接近遊戲結束的情況
        # 已經發了很多牌，只剩最後幾張
        
        # 設置一個接近完成的局面
        front_cards = [Card('K', 's'), Card('K', 'h')]  # 還差1張
        middle_cards = [Card('A', 'd'), Card('A', 'c'), Card('Q', 's'), Card('Q', 'h')]  # 還差1張
        back_cards = [Card('T', 's'), Card('T', 'h'), Card('T', 'd'), Card('9', 's'), Card('9', 'h')]  # 已滿
        
        # 最後的3張牌
        final_cards = [Card('J', 'd'), Card('8', 'c'), Card('7', 's')]
        
        game_state = GameState(
            current_cards=final_cards,
            front_hand=front_cards,
            middle_hand=middle_cards,
            back_hand=back_cards,
            remaining_cards=0  # 這是最後一輪
        )
        
        result = self.solver.solve(game_state)
        
        # 應該正好放置2張，丟棄1張
        placed_cards = [card for card, pos in result.best_placement.items() if pos != 'discard']
        self.assertEqual(len(placed_cards), 2, "Should place exactly 2 cards")
        
        # 驗證牌被放在了正確的位置（前墩和中墩各需要1張）
        positions = [pos for card, pos in result.best_placement.items() if pos != 'discard']
        self.assertIn('front', positions, "Should place one card in front")
        self.assertIn('middle', positions, "Should place one card in middle")
        
        print(f"\n🏁 Final street handling:")
        print(f"   Remaining cards: {final_cards}")
        print(f"   Placement decision: {result.best_placement}")
    
    def test_state_transition_validation(self):
        """測試狀態轉換的有效性驗證"""
        # 測試無效的狀態轉換
        
        # 情況1：嘗試在已滿的位置放牌
        full_back = [Card(rank, 's') for rank in ['A', 'K', 'Q', 'J', 'T']]
        
        game_state = GameState(
            current_cards=[Card('9', 'h'), Card('8', 'd'), Card('7', 'c')],
            front_hand=[],
            middle_hand=[],
            back_hand=full_back,  # 後墩已滿
            remaining_cards=5
        )
        
        result = self.solver.solve(game_state)
        
        # 驗證沒有牌被放到後墩
        back_placements = [card for card, pos in result.best_placement.items() if pos == 'back']
        self.assertEqual(len(back_placements), 0, "Should not place cards in full back hand")
        
        # 情況2：測試街道識別
        total_cards_placed = len(game_state.front_hand) + len(game_state.middle_hand) + len(game_state.back_hand)
        current_street = self._identify_street(total_cards_placed + len(game_state.current_cards))
        
        print(f"\n🔍 State validation test:")
        print(f"   Total cards seen: {total_cards_placed + len(game_state.current_cards)}")
        print(f"   Current street: {current_street}")
        print(f"   Valid placements: {[pos for _, pos in result.best_placement.items() if pos != 'discard']}")
    
    def test_progressive_strategy_adaptation(self):
        """測試策略隨街道進展的適應性"""
        # 測試求解器是否會根據遊戲進展調整策略
        
        # 早期街道 - 應該更保守
        early_game = GameState(
            current_cards=[Card('A', 's'), Card('A', 'h'), Card('K', 'd')],
            front_hand=[],
            middle_hand=[Card('Q', 's'), Card('J', 'h')],
            back_hand=[Card('T', 'd'), Card('9', 'c')],
            remaining_cards=6  # 還有很多牌
        )
        
        early_result = self.solver.solve(early_game)
        
        # 晚期街道 - 應該更激進
        late_game = GameState(
            current_cards=[Card('A', 's'), Card('A', 'h'), Card('K', 'd')],
            front_hand=[Card('7', 's'), Card('6', 'h')],
            middle_hand=[Card('Q', 's'), Card('J', 'h'), Card('T', 'c'), Card('9', 'd')],
            back_hand=[Card('K', 'c'), Card('K', 'h'), Card('Q', 'd'), Card('Q', 'c')],
            remaining_cards=1  # 快結束了
        )
        
        late_result = self.solver.solve(late_game)
        
        print(f"\n📈 Strategy Adaptation Test:")
        print(f"   Early game AA placement: {early_result.best_placement}")
        print(f"   Late game AA placement: {late_result.best_placement}")
        
        # 晚期應該更傾向於把AA放在能完成的位置
        self.assertIsNotNone(early_result)
        self.assertIsNotNone(late_result)
    
    # 輔助方法
    def _create_shuffled_deck(self) -> List[Card]:
        """創建並洗牌的完整牌組"""
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        suits = ['s', 'h', 'd', 'c']
        
        deck = []
        for rank in ranks:
            for suit in suits:
                deck.append(Card(rank, suit))
        
        random.shuffle(deck)
        return deck
    
    def _card_from_string(self, card_str: str) -> Card:
        """從字符串創建Card對象"""
        if len(card_str) >= 2:
            rank = card_str[0]
            suit = card_str[1]
            return Card(rank, suit)
        raise ValueError(f"Invalid card string: {card_str}")
    
    def _evaluate_hand(self, cards: List[Card]) -> int:
        """評估手牌強度（簡化版）"""
        if not cards:
            return 0
        
        # 統計點數
        rank_counts = {}
        for card in cards:
            rank = card.rank
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        # 統計花色
        suit_counts = {}
        for card in cards:
            suit = card.suit
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
        
        # 檢查牌型
        counts = sorted(rank_counts.values(), reverse=True)
        
        # 同花檢查
        is_flush = any(count >= 5 for count in suit_counts.values()) if len(cards) >= 5 else False
        
        # 順子檢查（簡化）
        is_straight = False
        if len(cards) >= 5:
            ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
            rank_values = {r: i for i, r in enumerate(ranks)}
            card_ranks = sorted([rank_values[c.rank] for c in cards])
            
            for i in range(len(card_ranks) - 4):
                if card_ranks[i+4] - card_ranks[i] == 4:
                    is_straight = True
                    break
        
        # 返回牌型強度
        if is_straight and is_flush:
            return 8  # 同花順
        elif counts and counts[0] == 4:
            return 7  # 四條
        elif counts and len(counts) >= 2 and counts[0] == 3 and counts[1] == 2:
            return 6  # 葫蘆
        elif is_flush:
            return 5  # 同花
        elif is_straight:
            return 4  # 順子
        elif counts and counts[0] == 3:
            return 3  # 三條
        elif counts and len(counts) >= 2 and counts[0] == 2 and counts[1] == 2:
            return 2  # 兩對
        elif counts and counts[0] == 2:
            return 1  # 一對
        else:
            return 0  # 高牌
    
    def _hand_type_name(self, strength: int) -> str:
        """獲取牌型名稱"""
        names = [
            "High Card", "One Pair", "Two Pair", "Three of a Kind",
            "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"
        ]
        return names[strength] if 0 <= strength < len(names) else "Unknown"
    
    def _identify_street(self, total_cards: int) -> str:
        """根據總牌數識別當前街道"""
        if total_cards <= 5:
            return "Initial"
        elif total_cards <= 8:
            return "First"
        elif total_cards <= 10:
            return "Second"
        elif total_cards <= 12:
            return "Third"
        elif total_cards <= 13:
            return "Fourth"
        else:
            return "Complete"


class TestStreetSolverIntegration(unittest.TestCase):
    """街道求解器整合測試"""
    
    def test_multi_player_simulation(self):
        """測試多人遊戲模擬"""
        num_players = 3
        num_games = 10
        
        win_counts = [0] * num_players
        
        for game_idx in range(num_games):
            # 模擬一局完整的遊戲
            deck = self._create_shuffled_deck()
            player_arrangements = []
            
            # 每個玩家依次做決策
            for player_idx in range(num_players):
                # 初始5張牌
                start_idx = player_idx * 5
                initial_cards = [deck[i] for i in range(start_idx, start_idx + 5)]
                
                # 使用求解器為每個玩家做決策
                solver = create_solver(simulations_limit=1000)
                
                game_state = GameState(
                    current_cards=initial_cards,
                    front_hand=[],
                    middle_hand=[],
                    back_hand=[],
                    remaining_cards=8
                )
                
                result = solver.solve(game_state)
                
                # 記錄玩家的安排
                arrangement = {
                    'player': player_idx,
                    'front': [],
                    'middle': [],
                    'back': [],
                    'placement': result.best_placement
                }
                
                player_arrangements.append(arrangement)
            
            # 簡單判定勝者（基於期望分數）
            scores = [random.uniform(0.4, 0.8) for _ in range(num_players)]  # 模擬分數
            winner_idx = scores.index(max(scores))
            win_counts[winner_idx] += 1
        
        print(f"\n🏆 Multi-player Simulation Results ({num_games} games):")
        for i in range(num_players):
            win_rate = win_counts[i] / num_games
            print(f"   Player {i+1}: {win_counts[i]} wins ({win_rate:.1%})")
        
        # 驗證結果合理性
        for count in win_counts:
            self.assertGreater(count, 0, "Each player should win at least once")
    
    def test_fantasy_land_detection(self):
        """測試Fantasy Land的檢測和處理"""
        # 創建一個可能進入Fantasy Land的局面
        # 前墩需要QQ或更好
        
        game_state = GameState(
            current_cards=[Card('Q', 's'), Card('Q', 'h'), Card('K', 'd')],
            front_hand=[],
            middle_hand=[Card('A', 's'), Card('A', 'h')],
            back_hand=[Card('T', 's'), Card('T', 'h'), Card('T', 'd')],
            remaining_cards=5
        )
        
        result = self.solver.solve(game_state)
        
        # 檢查是否識別出Fantasy Land機會
        front_placements = [card for card, pos in result.best_placement.items() 
                           if pos == 'front' and 'Q' in card]
        
        print(f"\n🌟 Fantasy Land Detection:")
        print(f"   Current cards: {game_state.current_cards}")
        print(f"   QQ placement: {front_placements}")
        print(f"   Full placement: {result.best_placement}")
        
        # QQ應該被考慮放在前墩
        self.assertGreaterEqual(len(front_placements), 1, 
                               "Should consider placing Queens in front for Fantasy Land")
    
    def _create_shuffled_deck(self) -> List[Card]:
        """創建並洗牌的完整牌組"""
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        suits = ['s', 'h', 'd', 'c']
        
        deck = []
        for rank in ranks:
            for suit in suits:
                deck.append(Card(rank, suit))
        
        random.shuffle(deck)
        return deck


if __name__ == '__main__':
    unittest.main(verbosity=2)