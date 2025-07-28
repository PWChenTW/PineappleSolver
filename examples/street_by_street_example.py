#!/usr/bin/env python3
"""
逐街求解器使用示例
展示如何使用街道求解器進行完整的 OFC Pineapple 遊戲
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ofc_solver_street import (
    StreetByStreetSolver, Street, OpponentTracker,
    Card, PineappleState, StreetState,
    InitialStreetSolver, DrawStreetSolver
)
from ofc_solver_joker import create_full_deck
import random


class InteractiveOFCGame:
    """交互式 OFC 遊戲"""
    
    def __init__(self, include_jokers: bool = True):
        self.solver = StreetByStreetSolver(include_jokers=include_jokers)
        self.player_state = PineappleState()
        self.opponent_tracker = OpponentTracker()
        self.deck = []
        self.include_jokers = include_jokers
        
    def start_new_game(self):
        """開始新遊戲"""
        print("\n" + "="*60)
        print("開始新的 OFC Pineapple 遊戲")
        print("="*60)
        
        # 初始化牌堆
        self.deck = create_full_deck(include_jokers=self.include_jokers)
        random.shuffle(self.deck)
        
        # 重置狀態
        self.player_state = PineappleState()
        self.opponent_tracker = OpponentTracker()
        
        # 開始遊戲
        self.play_initial_street()
        
        # 繼續後續街道
        for street_num in range(1, 5):
            if not self.play_draw_street(street_num):
                break
        
        # 顯示最終結果
        self.show_final_results()
    
    def play_initial_street(self):
        """玩初始街道"""
        print("\n--- 初始街道（5張牌）---")
        
        # 玩家抽5張
        player_cards = [self.deck.pop() for _ in range(5)]
        print(f"你抽到: {' '.join(str(c) for c in player_cards)}")
        
        # 創建街道狀態
        street_state = StreetState(
            street=Street.INITIAL,
            player_state=self.player_state,
            opponent_tracker=self.opponent_tracker,
            remaining_deck=self.deck.copy(),
            street_cards=player_cards
        )
        
        # 使用求解器
        result = self.solver.initial_solver.solve_street(street_state)
        
        # 顯示結果
        print("\n建議擺放:")
        for card, position in result['placement']:
            print(f"  {card} → {position}")
        
        if result.get('fantasy_land'):
            print("\n✨ 這個擺放可以進入夢幻樂園！")
        
        # 讓用戶確認或修改
        if self.ask_user_confirmation("接受這個擺放嗎？"):
            # 已經在求解器中應用了
            pass
        else:
            # 讓用戶手動擺放
            self.manual_initial_placement(player_cards)
        
        # 對手擺放
        self.simulate_opponent_initial()
        
        # 顯示當前狀態
        self.show_current_state()
    
    def play_draw_street(self, street_num: int) -> bool:
        """玩抽牌街道"""
        street_name = ['', '第一', '第二', '第三', '第四'][street_num]
        print(f"\n--- {street_name}街（抽3張，擺2張，棄1張）---")
        
        # 檢查牌堆
        if len(self.deck) < 6:  # 玩家3張 + 對手3張
            print("牌堆不足，遊戲結束！")
            return False
        
        # 玩家抽3張
        player_cards = [self.deck.pop() for _ in range(3)]
        print(f"你抽到: {' '.join(str(c) for c in player_cards)}")
        
        # 創建街道狀態
        street_state = StreetState(
            street=Street(street_num),
            player_state=self.player_state,
            opponent_tracker=self.opponent_tracker,
            remaining_deck=self.deck.copy(),
            street_cards=player_cards
        )
        
        # 使用求解器
        result = self.solver.draw_solver.solve_street(street_state)
        
        # 顯示結果
        print("\n建議動作:")
        for card, position in result['placements']:
            print(f"  擺放: {card} → {position}")
        print(f"  棄牌: {result['discard']}")
        
        # 讓用戶確認
        if self.ask_user_confirmation("接受這個動作嗎？"):
            # 已經在求解器中應用了
            pass
        else:
            # 讓用戶手動選擇
            self.manual_draw_placement(player_cards)
        
        # 對手行動
        self.simulate_opponent_draw()
        
        # 顯示當前狀態
        self.show_current_state()
        
        return True
    
    def manual_initial_placement(self, cards: List[Card]):
        """手動初始擺放"""
        print("\n手動擺放模式:")
        # 重置狀態
        self.player_state = PineappleState()
        
        cards_left = cards.copy()
        while cards_left:
            print(f"\n剩餘牌: {' '.join(str(c) for c in cards_left)}")
            print("可用位置:", self.player_state.get_available_positions())
            
            # 選擇牌
            card_idx = self.get_user_choice("選擇要擺放的牌（輸入序號）:", len(cards_left))
            card = cards_left.pop(card_idx)
            
            # 選擇位置
            positions = self.player_state.get_available_positions()
            pos_idx = self.get_user_choice(f"將 {card} 擺放到（0=front, 1=middle, 2=back）:", 3)
            position = ['front', 'middle', 'back'][pos_idx]
            
            if position in positions:
                self.player_state.place_card(card, position)
                print(f"已將 {card} 擺放到 {position}")
            else:
                print("該位置已滿！")
                cards_left.append(card)
    
    def manual_draw_placement(self, cards: List[Card]):
        """手動抽牌擺放"""
        print("\n手動擺放模式:")
        
        # 選擇棄牌
        print(f"抽到的牌: {' '.join(str(c) for c in cards)}")
        discard_idx = self.get_user_choice("選擇要棄掉的牌（輸入序號）:", 3)
        
        cards_to_place = []
        discard = None
        for i, card in enumerate(cards):
            if i == discard_idx:
                discard = card
                self.player_state.discarded.append(card)
            else:
                cards_to_place.append(card)
        
        print(f"\n棄掉: {discard}")
        
        # 擺放剩餘2張
        for card in cards_to_place:
            positions = self.player_state.get_available_positions()
            print(f"\n要擺放: {card}")
            print("可用位置:", positions)
            
            pos_idx = self.get_user_choice("選擇位置（0=front, 1=middle, 2=back）:", 3)
            position = ['front', 'middle', 'back'][pos_idx]
            
            if position in positions:
                self.player_state.place_card(card, position)
                print(f"已將 {card} 擺放到 {position}")
            else:
                print("該位置已滿！請重新選擇")
                # 簡化處理，隨機選一個可用位置
                if positions:
                    position = random.choice(positions)
                    self.player_state.place_card(card, position)
                    print(f"自動將 {card} 擺放到 {position}")
    
    def simulate_opponent_initial(self):
        """模擬對手初始擺放"""
        if len(self.deck) < 5:
            return
        
        print("\n對手擺放初始5張牌...")
        opponent_cards = [self.deck.pop() for _ in range(5)]
        
        # 簡單策略
        positions = ['back', 'back', 'middle', 'middle', 'front']
        for card, pos in zip(opponent_cards, positions):
            self.opponent_tracker.add_known_card(card, pos)
    
    def simulate_opponent_draw(self):
        """模擬對手抽牌"""
        if len(self.deck) < 3:
            return
        
        print("\n對手抽3張牌...")
        opponent_cards = [self.deck.pop() for _ in range(3)]
        
        # 隨機選2張擺放
        random.shuffle(opponent_cards)
        cards_to_place = opponent_cards[:2]
        
        # 獲取對手可用位置
        summary = self.opponent_tracker.get_opponent_state_summary()
        positions = []
        
        if summary['back'] < 5:
            positions.extend(['back'] * (5 - summary['back']))
        if summary['middle'] < 5:
            positions.extend(['middle'] * (5 - summary['middle']))
        if summary['front'] < 3:
            positions.extend(['front'] * (3 - summary['front']))
        
        # 擺放
        for card in cards_to_place[:2]:
            if positions:
                pos = positions.pop(0)
                self.opponent_tracker.add_known_card(card, pos)
    
    def show_current_state(self):
        """顯示當前遊戲狀態"""
        print("\n" + "-"*40)
        print("當前遊戲狀態:")
        print("-"*40)
        
        # 玩家狀態
        print("你的牌:")
        print(f"  前墩({len(self.player_state.front_hand.cards)}/3): {' '.join(str(c) for c in self.player_state.front_hand.cards)}")
        print(f"  中墩({len(self.player_state.middle_hand.cards)}/5): {' '.join(str(c) for c in self.player_state.middle_hand.cards)}")
        print(f"  後墩({len(self.player_state.back_hand.cards)}/5): {' '.join(str(c) for c in self.player_state.back_hand.cards)}")
        
        if self.player_state.discarded:
            print(f"  棄牌: {' '.join(str(c) for c in self.player_state.discarded)}")
        
        # 對手狀態
        summary = self.opponent_tracker.get_opponent_state_summary()
        print(f"\n對手的牌:")
        print(f"  前墩: {summary['front']}/3 張")
        print(f"  中墩: {summary['middle']}/5 張")
        print(f"  後墩: {summary['back']}/5 張")
        
        print(f"\n牌堆剩餘: {len(self.deck)} 張")
        print("-"*40)
    
    def show_final_results(self):
        """顯示最終結果"""
        print("\n" + "="*60)
        print("遊戲結束 - 最終結果")
        print("="*60)
        
        # 玩家結果
        print("\n你的最終牌型:")
        print(f"前墩: {' '.join(str(c) for c in self.player_state.front_hand.cards)}")
        front_rank, _ = self.player_state.front_hand.evaluate()
        print(f"  牌力: {self.get_hand_name(front_rank)}")
        
        print(f"\n中墩: {' '.join(str(c) for c in self.player_state.middle_hand.cards)}")
        middle_rank, _ = self.player_state.middle_hand.evaluate()
        print(f"  牌力: {self.get_hand_name(middle_rank)}")
        
        print(f"\n後墩: {' '.join(str(c) for c in self.player_state.back_hand.cards)}")
        back_rank, _ = self.player_state.back_hand.evaluate()
        print(f"  牌力: {self.get_hand_name(back_rank)}")
        
        # 檢查有效性
        if self.player_state.is_valid():
            print("\n✓ 有效擺放！")
            if self.player_state.has_fantasy_land():
                print("✨ 恭喜進入夢幻樂園！")
        else:
            print("\n✗ 無效擺放（犯規）")
        
        # 對手信息
        summary = self.opponent_tracker.get_opponent_state_summary()
        print(f"\n對手使用了 {summary['known_cards']} 張已知牌")
    
    def get_hand_name(self, rank: int) -> str:
        """獲取牌型名稱"""
        names = ["高牌", "一對", "兩對", "三條", "順子", "同花", "葫蘆", "四條", "同花順"]
        return names[rank] if rank < len(names) else "未知"
    
    def ask_user_confirmation(self, prompt: str) -> bool:
        """詢問用戶確認"""
        response = input(f"\n{prompt} (y/n): ").lower()
        return response == 'y'
    
    def get_user_choice(self, prompt: str, max_choice: int) -> int:
        """獲取用戶選擇"""
        while True:
            try:
                choice = int(input(f"{prompt} (0-{max_choice-1}): "))
                if 0 <= choice < max_choice:
                    return choice
                print("無效選擇，請重試")
            except ValueError:
                print("請輸入數字")


def main():
    """主函數"""
    print("歡迎來到 OFC Pineapple 逐街求解器！")
    print("本程序將幫助你做出最佳決策")
    
    # 詢問是否包含鬼牌
    include_jokers = input("\n是否包含鬼牌？(y/n): ").lower() == 'y'
    
    # 創建遊戲
    game = InteractiveOFCGame(include_jokers=include_jokers)
    
    while True:
        # 開始新遊戲
        game.start_new_game()
        
        # 詢問是否繼續
        if not game.ask_user_confirmation("再來一局？"):
            break
    
    print("\n感謝遊玩！再見！")


if __name__ == "__main__":
    main()