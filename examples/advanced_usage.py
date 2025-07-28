#!/usr/bin/env python3
"""
OFC Solver 進階使用範例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofc_solver_fixed import OFCMCTSSolver, Card

def analyze_hand(cards_str):
    """分析一手牌的最佳擺放"""
    # 將字串轉換為牌
    cards = [Card.from_string(c) for c in cards_str]
    
    print(f"\n分析手牌: {' '.join(cards_str)}")
    print("-" * 50)
    
    # 嘗試不同的模擬次數
    for num_sims in [100, 1000, 5000]:
        solver = OFCMCTSSolver(num_simulations=num_sims)
        
        print(f"\n使用 {num_sims} 次模擬:")
        arrangement = solver.solve_initial_five(cards)
        
        print(f"  前墩: {' '.join(str(c) for c in arrangement.front_hand.cards)}")
        print(f"  中墩: {' '.join(str(c) for c in arrangement.middle_hand.cards)}")
        print(f"  後墩: {' '.join(str(c) for c in arrangement.back_hand.cards)}")


def main():
    # 測試不同類型的手牌
    test_hands = [
        # 對子
        ["As", "Ah", "Kd", "Qc", "Js"],
        
        # 兩對
        ["As", "Ah", "Kd", "Kc", "Qs"],
        
        # 三條
        ["As", "Ah", "Ad", "Kc", "Qs"],
        
        # 順子潛力
        ["As", "Kd", "Qh", "Jc", "Ts"],
        
        # 同花潛力
        ["As", "Ks", "Qs", "Js", "9h"],
        
        # 小牌
        ["2s", "3h", "4d", "5c", "7s"]
    ]
    
    for hand in test_hands:
        analyze_hand(hand)


if __name__ == "__main__":
    main()