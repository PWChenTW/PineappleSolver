#!/usr/bin/env python3
"""
使用簡單包裝器的範例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ofc_solver_simple import SimpleOFCSolver

def main():
    # 創建簡單求解器
    solver = SimpleOFCSolver(num_simulations=2000)
    
    # 使用字串格式的牌
    cards = ["As", "Kh", "Qd", "Jc", "Ts"]
    
    print(f"要擺放的牌: {' '.join(cards)}")
    
    # 求解並獲得擺放字典
    placement = solver.solve_initial_five(cards)
    
    print("\n擺放結果:")
    for card, position in placement.items():
        print(f"  {card} → {position}")
    
    # 分組顯示
    front = [card for card, pos in placement.items() if pos == 'front']
    middle = [card for card, pos in placement.items() if pos == 'middle']
    back = [card for card, pos in placement.items() if pos == 'back']
    
    print(f"\n前墩: {' '.join(front)}")
    print(f"中墩: {' '.join(middle)}")
    print(f"後墩: {' '.join(back)}")


if __name__ == "__main__":
    main()