#!/usr/bin/env python3
"""
比較簡單版和完整版求解器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofc_solver_fixed import OFCMCTSSolver, Card
from ofc_solver_full import PineappleOFCSolver, Card as FullCard

def compare_solvers(cards_str):
    """比較兩個求解器的結果"""
    print(f"\n{'='*60}")
    print(f"測試手牌: {' '.join(cards_str)}")
    print(f"{'='*60}")
    
    # 簡單版求解器（只考慮初始5張）
    print("\n[簡單版] 只考慮初始5張牌:")
    simple_solver = OFCMCTSSolver(num_simulations=1000)
    simple_cards = [Card.from_string(c) for c in cards_str]
    simple_result = simple_solver.solve_initial_five(simple_cards)
    
    print(f"前墩: {' '.join(str(c) for c in simple_result.front_hand.cards)}")
    print(f"中墩: {' '.join(str(c) for c in simple_result.middle_hand.cards)}")
    print(f"後墩: {' '.join(str(c) for c in simple_result.back_hand.cards)}")
    
    # 完整版求解器（模擬整個遊戲）
    print("\n[完整版] 模擬完整 Pineapple OFC:")
    full_solver = PineappleOFCSolver(num_simulations=1000)
    full_cards = [FullCard.from_string(c) for c in cards_str]
    full_result = full_solver.solve_initial_five(full_cards)
    
    print(f"前墩: {' '.join(str(c) for c in full_result.front_hand.cards)}")
    print(f"中墩: {' '.join(str(c) for c in full_result.middle_hand.cards)}")
    print(f"後墩: {' '.join(str(c) for c in full_result.back_hand.cards)}")


def main():
    # 測試幾種不同的手牌
    test_hands = [
        ["As", "Ah", "Kd", "Kc", "Qs"],  # 兩對
        ["As", "Ks", "Qs", "Js", "Ts"],  # 同花順潛力
        ["Ac", "Ad", "Ah", "Kc", "Qs"],  # 三條
    ]
    
    for hand in test_hands:
        compare_solvers(hand)


if __name__ == "__main__":
    main()