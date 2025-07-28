#!/usr/bin/env python3
"""
OFC 逐街命令行介面（支持連續模擬）
使用現有的優化求解器，支持逐街輸入和求解
"""

import argparse
import json
import os
import random
from typing import List, Dict, Any, Optional, Set
from ofc_solver_joker import PineappleOFCSolverJoker, Card, PineappleStateJoker as PineappleState


class StreetByStreetCLI:
    """逐街命令行介面"""
    
    def __init__(self, num_simulations: int = 1000000):
        self.solver = PineappleOFCSolverJoker(num_simulations=num_simulations)
        self.game_state = None
        self.used_cards = set()  # 已使用的牌（包括玩家的牌）
        self.opponent_cards = set()  # 對手的牌
        self.discarded_cards = set()  # 棄掉的牌
        self.street_number = 0
        self.history = []
        self.deck = self._create_full_deck()  # 完整牌組
        self.auto_deal = True  # 默認自動發牌
        
    def solve_initial(self, cards: List[Card]):
        """求解初始5張牌"""
        print(f"\n=== 初始5張牌 ===")
        print(f"牌: {' '.join(str(c) for c in cards)}")
        
        # 求解
        arrangement = self.solver.solve_initial_five(cards)
        self.game_state = arrangement
        
        # 記錄已使用的牌
        for card in cards:
            self.used_cards.add(str(card))
            self._remove_from_deck(card)
            
        # 顯示結果
        print("\n最佳擺放:")
        print(f"前墩: {' '.join(str(c) for c in arrangement.front_hand.cards)}")
        print(f"中墩: {' '.join(str(c) for c in arrangement.middle_hand.cards)}")
        print(f"後墩: {' '.join(str(c) for c in arrangement.back_hand.cards)}")
        
        if arrangement.is_valid():
            print("✓ 有效擺放")
        else:
            print("✗ 無效擺放（會犯規）")
            
        # 記錄歷史
        self.history.append({
            'street': 0,
            'cards': [str(c) for c in cards],
            'state': self._serialize_state(arrangement)
        })
        
        return arrangement
        
    def solve_next_street(self, drawn_cards: List[Card]):
        """求解下一街（3張牌）"""
        if not self.game_state:
            print("錯誤：請先求解初始5張牌！")
            return None
            
        self.street_number += 1
        print(f"\n=== 第 {self.street_number} 街 ===")
        print(f"抽到: {' '.join(str(c) for c in drawn_cards)}")
        
        # 檢查是否已完成
        total_cards = (len(self.game_state.front_hand.cards) + 
                      len(self.game_state.middle_hand.cards) + 
                      len(self.game_state.back_hand.cards))
        
        if total_cards >= 13:
            print("遊戲已完成！")
            return None
            
        # 建立新的求解器來處理當前狀態
        # 使用 MCTS 來評估所有可能的擺放和棄牌組合
        best_score = float('-inf')
        best_action = None
        
        # 生成所有可能的動作（2張擺放，1張棄牌）
        actions = self._generate_possible_actions(drawn_cards)
        
        print(f"評估 {len(actions)} 種可能的動作...")
        
        for i, (placements, discard) in enumerate(actions):
            if i % 10 == 0:
                print(f"進度: {i}/{len(actions)}")
                
            # 創建臨時狀態
            temp_state = self._copy_state(self.game_state)
            
            # 應用動作
            valid = True
            for card, position in placements:
                if not self._can_place_card(temp_state, position):
                    valid = False
                    break
                self._place_card_in_state(temp_state, card, position)
                
            if not valid or not temp_state.is_valid():
                continue
                
            # 評估狀態
            score = self._evaluate_state(temp_state)
            
            if score > best_score:
                best_score = score
                best_action = (placements, discard)
                
        if best_action:
            placements, discard = best_action
            
            # 應用最佳動作
            for card, position in placements:
                self._place_card_in_state(self.game_state, card, position)
                self.used_cards.add(str(card))
                self._remove_from_deck(card)
                
            self.used_cards.add(str(discard))
            self.discarded_cards.add(str(discard))
            self._remove_from_deck(discard)
            
            print(f"\n最佳動作:")
            for card, position in placements:
                print(f"  {card} → {position}")
            print(f"  棄牌: {discard}")
            
            # 顯示當前狀態
            print("\n當前狀態:")
            print(f"前墩 ({len(self.game_state.front_hand.cards)}/3): {' '.join(str(c) for c in self.game_state.front_hand.cards)}")
            print(f"中墩 ({len(self.game_state.middle_hand.cards)}/5): {' '.join(str(c) for c in self.game_state.middle_hand.cards)}")
            print(f"後墩 ({len(self.game_state.back_hand.cards)}/5): {' '.join(str(c) for c in self.game_state.back_hand.cards)}")
            
            if self.game_state.is_valid():
                print("✓ 有效擺放")
            else:
                print("✗ 無效擺放（會犯規）")
                
            # 記錄歷史
            self.history.append({
                'street': self.street_number,
                'cards': [str(c) for c in drawn_cards],
                'action': {
                    'placements': [(str(c), pos) for c, pos in placements],
                    'discard': str(discard)
                },
                'state': self._serialize_state(self.game_state)
            })
            
            # 檢查是否完成
            total_cards = (len(self.game_state.front_hand.cards) + 
                          len(self.game_state.middle_hand.cards) + 
                          len(self.game_state.back_hand.cards))
            
            if total_cards >= 13:
                print("\n遊戲完成！")
                self._print_final_result()
                
        else:
            print("無法找到有效的動作！")
            
        return self.game_state
        
    def _generate_possible_actions(self, cards: List[Card]):
        """生成所有可能的動作（選2張擺放，1張棄牌）"""
        actions = []
        positions = []
        
        # 檢查可用位置
        if len(self.game_state.front_hand.cards) < 3:
            positions.append('front')
        if len(self.game_state.middle_hand.cards) < 5:
            positions.append('middle')
        if len(self.game_state.back_hand.cards) < 5:
            positions.append('back')
            
        # 生成所有可能的牌和位置組合
        from itertools import combinations, permutations
        
        # 選擇2張牌來擺放
        for two_cards in combinations(cards, 2):
            discard = [c for c in cards if c not in two_cards][0]
            
            # 生成所有可能的位置組合（包括相同位置）
            for pos_combo in [(p1, p2) for p1 in positions for p2 in positions]:
                # 檢查位置是否有空間
                temp_counts = {
                    'front': len(self.game_state.front_hand.cards),
                    'middle': len(self.game_state.middle_hand.cards),
                    'back': len(self.game_state.back_hand.cards)
                }
                
                # 計算每個位置需要的空間
                pos1, pos2 = pos_combo
                temp_counts[pos1] += 1
                if pos1 == pos2:
                    temp_counts[pos2] += 1
                else:
                    temp_counts[pos2] += 1
                    
                # 檢查是否超出限制
                if (temp_counts['front'] > 3 or 
                    temp_counts['middle'] > 5 or 
                    temp_counts['back'] > 5):
                    continue
                    
                # 生成擺放組合
                placements = list(zip(two_cards, pos_combo))
                actions.append((placements, discard))
                
        return actions
        
    def _can_place_card(self, state: PineappleState, position: str) -> bool:
        """檢查是否可以在指定位置放牌"""
        if position == 'front':
            return len(state.front_hand.cards) < 3
        elif position == 'middle':
            return len(state.middle_hand.cards) < 5
        elif position == 'back':
            return len(state.back_hand.cards) < 5
        return False
        
    def _place_card_in_state(self, state: PineappleState, card: Card, position: str):
        """在狀態中放置牌"""
        if position == 'front':
            state.front_hand.cards.append(card)
        elif position == 'middle':
            state.middle_hand.cards.append(card)
        elif position == 'back':
            state.back_hand.cards.append(card)
            
    def _copy_state(self, state: PineappleState) -> PineappleState:
        """複製遊戲狀態"""
        new_state = PineappleState()
        new_state.front_hand.cards = state.front_hand.cards.copy()
        new_state.middle_hand.cards = state.middle_hand.cards.copy()
        new_state.back_hand.cards = state.back_hand.cards.copy()
        return new_state
        
    def _evaluate_state(self, state: PineappleState) -> float:
        """評估狀態的分數"""
        if not state.is_valid():
            return float('-inf')
            
        # 直接評估各手牌
        front_rank, _ = state.front_hand.evaluate()
        middle_rank, _ = state.middle_hand.evaluate()
        back_rank, _ = state.back_hand.evaluate()
        
        # 計算基礎分數
        score = 0
        score += front_rank * 1.5  # 前墩加權
        score += middle_rank * 1.2  # 中墩加權
        score += back_rank * 1.0   # 後墩
        
        # 夢幻樂園加分
        if state.has_fantasy_land():
            score += 1000
            
        return score
        
    def _print_final_result(self):
        """打印最終結果"""
        print("\n=== 最終結果 ===")
        
        rank_names = [
            "高牌", "一對", "兩對", "三條", "順子", 
            "同花", "葫蘆", "四條", "同花順", "皇家同花順"
        ]
        
        front_rank, _ = self.game_state.front_hand.evaluate()
        middle_rank, _ = self.game_state.middle_hand.evaluate()
        back_rank, _ = self.game_state.back_hand.evaluate()
        
        print(f"\n前墩: {' '.join(str(c) for c in self.game_state.front_hand.cards)}")
        print(f"  {rank_names[min(front_rank, 9)]}")
        
        print(f"\n中墩: {' '.join(str(c) for c in self.game_state.middle_hand.cards)}")
        print(f"  {rank_names[min(middle_rank, 9)]}")
        
        print(f"\n後墩: {' '.join(str(c) for c in self.game_state.back_hand.cards)}")
        print(f"  {rank_names[min(back_rank, 9)]}")
        
        if self.game_state.has_fantasy_land():
            print("\n🎉 達到夢幻樂園！")
            
    def save_history(self, filename: str):
        """保存遊戲歷史"""
        with open(filename, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"歷史已保存到: {filename}")
        
    def _serialize_state(self, state: PineappleState) -> Dict[str, Any]:
        """序列化遊戲狀態"""
        return {
            'front': [str(c) for c in state.front_hand.cards],
            'middle': [str(c) for c in state.middle_hand.cards],
            'back': [str(c) for c in state.back_hand.cards]
        }
    
    def _create_full_deck(self) -> List[Card]:
        """創建完整的牌組（包括鬼牌）"""
        deck = []
        # 使用與 ofc_solver_joker 一致的表示方式
        suits = ['s', 'h', 'd', 'c']  # spades, hearts, diamonds, clubs
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        
        for suit in suits:
            for rank in ranks:
                deck.append(Card(rank, suit))
        
        # 添加鬼牌（如果需要）
        # deck.append(Card('X', 'j'))  # Joker
        
        return deck
    
    def _remove_from_deck(self, card: Card):
        """從牌組中移除牌"""
        try:
            self.deck.remove(card)
        except ValueError:
            # 牌可能已經被移除
            pass
    
    def _deal_cards(self, num_cards: int) -> List[Card]:
        """從剩餘牌組中發牌"""
        available_cards = []
        
        for card in self.deck:
            card_str = str(card)
            if (card_str not in self.used_cards and 
                card_str not in self.opponent_cards and
                card_str not in self.discarded_cards):
                available_cards.append(card)
        
        if len(available_cards) < num_cards:
            print(f"警告：只剩 {len(available_cards)} 張可用的牌")
            return None
        
        # 隨機選擇牌
        random.shuffle(available_cards)
        dealt_cards = available_cards[:num_cards]
        
        # 從牌組中移除這些牌
        for card in dealt_cards:
            self._remove_from_deck(card)
        
        return dealt_cards
    
    def get_remaining_cards_count(self) -> int:
        """獲取剩餘可用牌數"""
        count = 0
        for card in self.deck:
            card_str = str(card)
            if (card_str not in self.used_cards and 
                card_str not in self.opponent_cards and
                card_str not in self.discarded_cards):
                count += 1
        return count
    
    def print_game_status(self):
        """打印遊戲狀態"""
        print(f"\n=== 遊戲狀態 ===")
        print(f"已使用的牌: {len(self.used_cards)}")
        print(f"對手的牌: {len(self.opponent_cards)}")
        print(f"棄掉的牌: {len(self.discarded_cards)}")
        print(f"剩餘可用牌: {self.get_remaining_cards_count()}")
        print(f"街道: {self.street_number}/4")


def main():
    parser = argparse.ArgumentParser(description='OFC 逐街求解器')
    parser.add_argument('cards', nargs='*', help='初始5張牌（可選，留空則自動發牌）')
    parser.add_argument('-s', '--simulations', type=int, default=10000,
                        help='MCTS 模擬次數')
    parser.add_argument('--continue', dest='continue_game', action='store_true',
                        help='繼續遊戲（等待輸入後續街道）')
    parser.add_argument('--save-history', help='保存遊戲歷史到文件')
    parser.add_argument('--manual', action='store_true',
                        help='手動輸入所有牌（不自動發牌）')
    parser.add_argument('--opponent-cards', nargs='*', help='對手的牌（用於追蹤）')
    
    args = parser.parse_args()
    
    # 創建 CLI
    cli = StreetByStreetCLI(num_simulations=args.simulations)
    
    # 設置模式
    if args.manual:
        cli.auto_deal = False
    
    # 處理對手的牌
    if args.opponent_cards:
        try:
            for card_str in args.opponent_cards:
                card = Card.from_string(card_str)
                cli.opponent_cards.add(str(card))
                cli._remove_from_deck(card)
            print(f"已記錄對手的 {len(cli.opponent_cards)} 張牌")
        except Exception as e:
            print(f"錯誤: 對手牌格式無效 - {e}")
            return
    
    # 處理初始牌
    if args.cards and len(args.cards) > 0:
        # 手動輸入的牌
        if len(args.cards) != 5:
            print("錯誤: 初始必須輸入5張牌，或留空自動發牌")
            return
        try:
            initial_cards = [Card.from_string(c) for c in args.cards]
            # 檢查牌是否已被使用
            for card in initial_cards:
                if str(card) in cli.opponent_cards:
                    print(f"錯誤: {card} 已被對手使用！")
                    return
        except Exception as e:
            print(f"錯誤: 無效的牌格式 - {e}")
            return
    else:
        # 自動發牌
        print("自動發初始5張牌...")
        initial_cards = cli._deal_cards(5)
        if not initial_cards:
            print("錯誤: 無法發牌，可能沒有足夠的牌！")
            return
    
    cli.solve_initial(initial_cards)
    
    # 如果啟用繼續模式
    if args.continue_game:
        print("\n繼續模式已啟用。輸入3張牌來模擬下一街，或輸入 'quit' 退出。")
        
        while True:
            try:
                # 檢查是否還有牌可發
                total_cards = (len(cli.game_state.front_hand.cards) + 
                              len(cli.game_state.middle_hand.cards) + 
                              len(cli.game_state.back_hand.cards))
                if total_cards >= 13:
                    break
                
                if cli.auto_deal:
                    # 自動發牌模式
                    input(f"\n按 Enter 發第 {cli.street_number + 1} 街的牌...")
                    street_cards = cli._deal_cards(3)
                    if not street_cards:
                        print("牌堆已空！")
                        break
                    print(f"發到: {' '.join(str(c) for c in street_cards)}")
                else:
                    # 手動輸入模式
                    user_input = input(f"\n第 {cli.street_number + 1} 街 (3張牌，或 'auto' 切換到自動模式): ").strip()
                    
                    if user_input.lower() == 'quit':
                        break
                    elif user_input.lower() == 'auto':
                        cli.auto_deal = True
                        print("已切換到自動發牌模式")
                        continue
                        
                    cards_str = user_input.split()
                    if len(cards_str) != 3:
                        print("請輸入3張牌！")
                        continue
                        
                    # 解析牌
                    street_cards = [Card.from_string(c) for c in cards_str]
                    
                    # 檢查是否已使用
                    for card in street_cards:
                        if str(card) in cli.used_cards or str(card) in cli.opponent_cards:
                            print(f"錯誤: {card} 已經使用過！")
                            continue
                
                # 更新對手牌（可選）
                opp_input = input("輸入對手這輪的牌（可選，直接按 Enter 跳過）: ").strip()
                if opp_input:
                    try:
                        opp_cards = [Card.from_string(c) for c in opp_input.split()]
                        for card in opp_cards:
                            cli.opponent_cards.add(str(card))
                            cli._remove_from_deck(card)
                        print(f"已記錄對手的牌: {' '.join(str(c) for c in opp_cards)}")
                    except Exception as e:
                        print(f"警告: 對手牌格式錯誤 - {e}")
                
                # 求解下一街
                result = cli.solve_next_street(street_cards)
                
                if not result:
                    break
                    
            except Exception as e:
                print(f"錯誤: {e}")
                
    # 保存歷史
    if args.save_history:
        cli.save_history(args.save_history)


if __name__ == "__main__":
    main()