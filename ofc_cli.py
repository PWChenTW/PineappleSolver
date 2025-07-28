#!/usr/bin/env python3
"""
OFC Solver 命令行介面（支持鬼牌）
"""

import argparse
from ofc_solver_joker import PineappleOFCSolverJoker, Card


def main():
    parser = argparse.ArgumentParser(description='OFC 初始五張牌求解器')
    parser.add_argument('cards', nargs=5, help='五張牌，格式如: As Kh Qd Jc Ts')
    parser.add_argument('-s', '--simulations', type=int, default=1000,
                        help='MCTS 模擬次數 (預設: 1000)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='顯示詳細輸出')
    
    args = parser.parse_args()
    
    # 創建求解器（支持鬼牌）
    solver = PineappleOFCSolverJoker(num_simulations=args.simulations)
    
    # 轉換牌
    try:
        cards = [Card.from_string(c) for c in args.cards]
    except Exception as e:
        print(f"錯誤: 無效的牌格式 - {e}")
        print("牌的格式應為: 等級(2-9,T,J,Q,K,A,X) + 花色(s,h,d,c,j)")
        print("例如: As = 黑桃A, Kh = 紅心K, Xj = 鬼牌")
        return
    
    if args.verbose:
        print(f"輸入的牌: {' '.join(args.cards)}")
        print(f"使用 {args.simulations} 次 MCTS 模擬")
        print("-" * 40)
    
    # 求解
    arrangement = solver.solve_initial_five(cards)
    
    # 輸出結果
    print("\n最佳擺放:")
    print(f"前墩: {' '.join(str(c) for c in arrangement.front_hand.cards)}")
    print(f"中墩: {' '.join(str(c) for c in arrangement.middle_hand.cards)}")
    print(f"後墩: {' '.join(str(c) for c in arrangement.back_hand.cards)}")
    
    if arrangement.is_valid():
        print("\n✓ 有效擺放")
    else:
        print("\n✗ 無效擺放（會犯規）")


if __name__ == "__main__":
    main()