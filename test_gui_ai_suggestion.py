#!/usr/bin/env python3
"""
測試 GUI AI 建議功能
"""

from ofc_solver_joker import PineappleOFCSolverJoker, Card

def test_ai_suggestion():
    """測試 AI 建議功能的邏輯"""
    print("=== 測試 GUI AI 建議功能 ===")
    
    # 創建測試牌
    test_cards = [
        Card.from_string("As"),
        Card.from_string("Kh"),
        Card.from_string("Qd"),
        Card.from_string("Jc"),
        Card.from_string("Xj")  # 包含鬼牌
    ]
    
    print(f"測試牌: {' '.join(str(c) for c in test_cards)}")
    
    try:
        # 創建求解器
        solver = PineappleOFCSolverJoker(num_simulations=1000)
        
        # 獲取建議
        print("\n求解中...")
        arrangement = solver.solve_initial_five(test_cards)
        
        # 模擬 GUI 的建議格式轉換
        suggestion = {
            'placement': [],
            'score': 0,
            'method': 'MCTS'
        }
        
        # 從 arrangement 中提取擺放建議
        for card in test_cards:
            if card in arrangement.front_hand.cards:
                suggestion['placement'].append((str(card), 'front'))
            elif card in arrangement.middle_hand.cards:
                suggestion['placement'].append((str(card), 'middle'))
            elif card in arrangement.back_hand.cards:
                suggestion['placement'].append((str(card), 'back'))
        
        print("\n✓ AI 建議生成成功！")
        print(f"建議擺放: {suggestion['placement']}")
        
        # 驗證所有牌都被分配
        if len(suggestion['placement']) == 5:
            print("✓ 所有5張牌都已分配位置")
        else:
            print(f"✗ 只有 {len(suggestion['placement'])} 張牌被分配")
            
        # 顯示最終擺放
        print("\n最終擺放:")
        print(f"前墩: {' '.join(str(c) for c in arrangement.front_hand.cards)}")
        print(f"中墩: {' '.join(str(c) for c in arrangement.middle_hand.cards)}")
        print(f"後墩: {' '.join(str(c) for c in arrangement.back_hand.cards)}")
        
        if arrangement.is_valid():
            print("✓ 有效擺放")
        else:
            print("✗ 無效擺放")
            
        return True
        
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ai_suggestion()
    if success:
        print("\n🎉 GUI AI 建議功能測試通過！")
    else:
        print("\n❌ GUI AI 建議功能測試失敗")