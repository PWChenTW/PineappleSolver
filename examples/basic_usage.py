#!/usr/bin/env python3
"""
OFC Solver 基本使用範例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofc_solver_fixed import OFCMCTSSolver, Card

def main():
    # 創建求解器（可設定模擬次數）
    solver = OFCMCTSSolver(num_simulations=100000)
    
    # 準備要擺放的5張牌
    cards = [
        Card.from_string("As"),  # 黑桃A
        Card.from_string("Kh"),  # 紅心K
        Card.from_string("Qd"),  # 方塊Q
        Card.from_string("Jc"),  # 梅花J
        Card.from_string("Ts")   # 黑桃10
    ]
    
    print("要擺放的牌:", " ".join(str(c) for c in cards))
    print("\n開始求解...")
    
    # 求解最佳擺放位置
    arrangement = solver.solve_initial_five(cards)
    
    # 顯示結果
    print("\n最佳擺放方案:")
    print(f"前墩 (Front): {' '.join(str(c) for c in arrangement.front_hand.cards)}")
    print(f"中墩 (Middle): {' '.join(str(c) for c in arrangement.middle_hand.cards)}")
    print(f"後墩 (Back): {' '.join(str(c) for c in arrangement.back_hand.cards)}")
    
    # 檢查是否有效
    if arrangement.is_valid():
        print("\n✓ 擺放有效（不會犯規）")
    else:
        print("\n✗ 擺放無效（會犯規）")


if __name__ == "__main__":
    main()
