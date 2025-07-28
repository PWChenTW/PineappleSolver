#!/usr/bin/env python3
"""
直接測試 OFC Solver（不通過 API）
"""

import sys
sys.path.insert(0, '.')

from src.ofc_solver import create_solver, GameState, Card

def test_initial_five_cards():
    """測試初始5張牌求解"""
    print("=== 直接測試 OFC Solver ===\n")
    
    # 創建求解器
    solver = create_solver(
        threads=2,
        time_limit=2.0,
        simulations_limit=10000
    )
    
    # 創建初始5張牌
    cards = [
        Card("A", "s"),  # A♠
        Card("K", "h"),  # K♥
        Card("Q", "d"),  # Q♦  
        Card("J", "c"),  # J♣
        Card("T", "s")   # T♠
    ]
    
    # 創建遊戲狀態（初始狀態，所有墩位都是空的）
    game_state = GameState(
        current_cards=cards,
        front_hand=[],
        middle_hand=[],
        back_hand=[],
        remaining_cards=47  # 52 - 5
    )
    
    print(f"要擺放的牌: {', '.join(str(c) for c in cards)}")
    print("開始求解...\n")
    
    try:
        # 求解
        result = solver.solve(game_state)
        
        print("🎯 求解結果:")
        print(f"最佳擺放: {result.best_placement}")
        print(f"期望分數: {result.expected_score:.2f}")
        print(f"置信度: {result.confidence:.2%}")
        print(f"模擬次數: {result.simulations:,}")
        print(f"計算時間: {result.time_taken:.2f}秒")
        
        if result.top_actions:
            print("\n前幾個選擇:")
            for i, action in enumerate(result.top_actions[:3]):
                print(f"  {i+1}. {action}")
                
        return True
        
    except Exception as e:
        print(f"❌ 求解失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_initial_five_cards()
    print("\n" + "="*50)
    print(f"測試{'成功' if success else '失敗'}！")
    
    if not success:
        print("\n可能的問題：")
        print("1. GameState 格式不兼容")
        print("2. MCTS 整合未正確實現")
        print("3. 需要檢查 ofc_solver_integration.py")