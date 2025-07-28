#!/usr/bin/env python3
"""
OFC 互動式命令行介面（支持逐街模擬）
"""

import argparse
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from ofc_solver_street import (
    StreetByStreetSolver, StreetState, PineappleState, 
    Card, Street, OpponentTracker
)


class InteractiveOFCSession:
    """互動式 OFC 遊戲會話"""
    
    def __init__(self, num_simulations: int = 10000, include_jokers: bool = True):
        self.solver = StreetByStreetSolver(include_jokers=include_jokers)
        self.num_simulations = num_simulations
        self.game_state = PineappleState()
        self.current_street = Street.INITIAL
        self.history = []
        self.deck_remaining = []
        
    def start_new_game(self, initial_cards: List[Card]):
        """開始新遊戲"""
        print("\n=== 開始新遊戲 ===")
        self.game_state = PineappleState()
        self.current_street = Street.INITIAL
        self.history = []
        
        # 初始化剩餘牌組
        full_deck = self.solver.deck.copy()
        for card in initial_cards:
            full_deck.remove(card)
        self.deck_remaining = full_deck
        
        # 求解初始5張
        result = self.solver.solve_initial_five(initial_cards)
        
        # 記錄歷史
        self.history.append({
            'street': Street.INITIAL.name,
            'cards': [str(c) for c in initial_cards],
            'result': self._serialize_result(result)
        })
        
        # 更新遊戲狀態
        self.game_state = result
        print("\n當前狀態:")
        self._print_current_state()
        
        return result
    
    def simulate_next_street(self, drawn_cards: Optional[List[Card]] = None):
        """模擬下一街"""
        if self.current_street == Street.COMPLETE:
            print("遊戲已完成！")
            return None
            
        # 前進到下一街
        self.current_street = Street(self.current_street.value + 1)
        
        # 如果沒有提供牌，從剩餘牌組隨機抽取
        if drawn_cards is None:
            import random
            if len(self.deck_remaining) < 3:
                print("牌組不足！")
                return None
            random.shuffle(self.deck_remaining)
            drawn_cards = self.deck_remaining[:3]
            self.deck_remaining = self.deck_remaining[3:]
        else:
            # 從牌組中移除提供的牌
            for card in drawn_cards:
                if card in self.deck_remaining:
                    self.deck_remaining.remove(card)
        
        print(f"\n=== 第 {self.current_street.value} 街 ===")
        print(f"抽到: {' '.join(str(c) for c in drawn_cards)}")
        
        # 求解當前街道
        result = self.solver.solve_street(
            self.current_street.value,
            self.game_state,
            drawn_cards
        )
        
        # 記錄歷史
        self.history.append({
            'street': self.current_street.name,
            'cards': [str(c) for c in drawn_cards],
            'result': self._serialize_result(result)
        })
        
        # 更新遊戲狀態
        self.game_state = result['state']
        
        print("\n當前狀態:")
        self._print_current_state()
        
        # 檢查是否完成
        if self.game_state.is_complete():
            self.current_street = Street.COMPLETE
            print("\n遊戲完成！")
            self._print_final_score()
        
        return result
    
    def _print_current_state(self):
        """打印當前狀態"""
        print(f"前墩 ({len(self.game_state.front_hand.cards)}/3): {' '.join(str(c) for c in self.game_state.front_hand.cards)}")
        print(f"中墩 ({len(self.game_state.middle_hand.cards)}/5): {' '.join(str(c) for c in self.game_state.middle_hand.cards)}")
        print(f"後墩 ({len(self.game_state.back_hand.cards)}/5): {' '.join(str(c) for c in self.game_state.back_hand.cards)}")
        if self.game_state.discarded:
            print(f"棄牌: {' '.join(str(c) for c in self.game_state.discarded)}")
        
        if self.game_state.is_valid():
            print("✓ 有效擺放")
        else:
            print("✗ 無效擺放（會犯規）")
            
    def _print_final_score(self):
        """打印最終得分"""
        print("\n=== 最終結果 ===")
        self._print_current_state()
        
        # 計算手牌強度
        evaluator = self.solver.joker_evaluator
        front_eval = evaluator.evaluate(self.game_state.front_hand)
        middle_eval = evaluator.evaluate(self.game_state.middle_hand)
        back_eval = evaluator.evaluate(self.game_state.back_hand)
        
        print(f"\n手牌強度:")
        print(f"前墩: {front_eval['hand_type']} - {front_eval['description']}")
        print(f"中墩: {middle_eval['hand_type']} - {middle_eval['description']}")
        print(f"後墩: {back_eval['hand_type']} - {back_eval['description']}")
        
        if self.game_state.has_fantasy_land():
            print("\n🎉 達到夢幻樂園！")
            
    def save_game(self, filename: str):
        """保存遊戲狀態"""
        save_data = {
            'current_street': self.current_street.name,
            'game_state': self._serialize_state(self.game_state),
            'history': self.history,
            'deck_remaining': [str(c) for c in self.deck_remaining]
        }
        
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        print(f"遊戲已保存到: {filename}")
        
    def load_game(self, filename: str):
        """載入遊戲狀態"""
        with open(filename, 'r') as f:
            save_data = json.load(f)
            
        self.current_street = Street[save_data['current_street']]
        self.history = save_data['history']
        self.deck_remaining = [Card.from_string(c) for c in save_data['deck_remaining']]
        
        # 重建遊戲狀態
        state_data = save_data['game_state']
        self.game_state = PineappleState()
        
        # 恢復手牌
        for pos in ['front', 'middle', 'back']:
            cards = [Card.from_string(c) for c in state_data[pos]]
            for card in cards:
                self.game_state.place_card(card, pos)
                
        # 恢復棄牌
        self.game_state.discarded = [Card.from_string(c) for c in state_data['discarded']]
        
        print(f"遊戲已載入: {filename}")
        self._print_current_state()
        
    def _serialize_state(self, state: PineappleState) -> Dict[str, Any]:
        """序列化遊戲狀態"""
        return {
            'front': [str(c) for c in state.front_hand.cards],
            'middle': [str(c) for c in state.middle_hand.cards],
            'back': [str(c) for c in state.back_hand.cards],
            'discarded': [str(c) for c in state.discarded]
        }
        
    def _serialize_result(self, result: Any) -> Dict[str, Any]:
        """序列化求解結果"""
        if isinstance(result, PineappleState):
            return self._serialize_state(result)
        elif isinstance(result, dict):
            serialized = {}
            for k, v in result.items():
                if k == 'state' and isinstance(v, PineappleState):
                    serialized[k] = self._serialize_state(v)
                elif k == 'placement' and isinstance(v, list):
                    serialized[k] = [(str(card), pos) for card, pos in v]
                else:
                    serialized[k] = v
            return serialized
        return {}


def interactive_mode():
    """互動模式"""
    print("=== OFC 逐街模擬器（互動模式）===")
    print("指令:")
    print("  new <5張牌>    - 開始新遊戲")
    print("  next [3張牌]   - 模擬下一街（可選提供牌）")
    print("  save <檔案名>  - 保存遊戲")
    print("  load <檔案名>  - 載入遊戲")
    print("  history        - 顯示歷史記錄")
    print("  quit           - 退出")
    
    session = InteractiveOFCSession(num_simulations=10000)
    
    while True:
        try:
            command = input("\n> ").strip().split()
            if not command:
                continue
                
            cmd = command[0].lower()
            
            if cmd == 'quit':
                break
                
            elif cmd == 'new' and len(command) == 6:
                # 開始新遊戲
                cards = [Card.from_string(c) for c in command[1:6]]
                session.start_new_game(cards)
                
            elif cmd == 'next':
                # 模擬下一街
                if len(command) == 4:
                    cards = [Card.from_string(c) for c in command[1:4]]
                    session.simulate_next_street(cards)
                else:
                    session.simulate_next_street()
                    
            elif cmd == 'save' and len(command) == 2:
                session.save_game(command[1])
                
            elif cmd == 'load' and len(command) == 2:
                session.load_game(command[1])
                
            elif cmd == 'history':
                print("\n=== 遊戲歷史 ===")
                for i, record in enumerate(session.history):
                    print(f"\n{i+1}. {record['street']}: {' '.join(record['cards'])}")
                    
            else:
                print("無效指令！")
                
        except Exception as e:
            print(f"錯誤: {e}")


def main():
    parser = argparse.ArgumentParser(description='OFC 逐街模擬器')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='互動模式')
    parser.add_argument('cards', nargs='*', help='初始5張牌（非互動模式）')
    parser.add_argument('-s', '--simulations', type=int, default=10000,
                        help='MCTS 模擬次數')
    parser.add_argument('--no-jokers', action='store_true',
                        help='不使用鬼牌')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    else:
        if len(args.cards) != 5:
            print("請提供5張初始牌！")
            return
            
        # 單次求解模式
        session = InteractiveOFCSession(
            num_simulations=args.simulations,
            include_jokers=not args.no_jokers
        )
        
        cards = [Card.from_string(c) for c in args.cards]
        session.start_new_game(cards)
        
        # 自動模擬所有街道
        print("\n是否自動模擬剩餘街道？(y/n)")
        if input().lower() == 'y':
            while session.current_street != Street.COMPLETE:
                input("\n按 Enter 繼續下一街...")
                session.simulate_next_street()


if __name__ == "__main__":
    main()