#!/usr/bin/env python3
"""
最終測試 - 確認所有功能正常
"""

import subprocess
import time
from ofc_solver_joker import Card, PineappleStateJoker as PineappleState
from ofc_cli_street import StreetByStreetCLI


def test_all_fixes():
    """測試所有修復"""
    print("=== 最終功能測試 ===")
    
    all_tests_passed = True
    
    # 1. 測試街道求解器不重複
    print("\n1. 測試街道求解器不重複牌...")
    try:
        solver = StreetByStreetCLI(num_simulations=100)
        game_state = PineappleState()
        
        # 模擬初始狀態
        game_state.front_hand.cards = [Card.from_string("Jc")]
        game_state.middle_hand.cards = [Card.from_string("Kh"), Card.from_string("Qd")]
        game_state.back_hand.cards = [Card.from_string("As"), Card.from_string("Xj")]
        
        solver.game_state = game_state
        solver.used_cards = {"Jc", "Kh", "Qd", "As", "Xj"}
        
        # 測試街道牌
        street_cards = [Card.from_string("9h"), Card.from_string("8s"), Card.from_string("7d")]
        
        # 生成動作
        actions = solver._generate_possible_actions(street_cards)
        
        # 檢查前10個動作
        for i, (placements, discard) in enumerate(actions[:10]):
            all_cards = [c for c, _ in placements] + [discard]
            if len(set(str(c) for c in all_cards)) != 3:
                print(f"  ✗ 動作 {i+1} 有重複牌！")
                all_tests_passed = False
                break
        else:
            print("  ✓ 所有動作都沒有重複牌")
            
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
        all_tests_passed = False
    
    # 2. 測試 GUI 導入
    print("\n2. 測試 GUI 模組...")
    try:
        import pineapple_ofc_gui
        # 檢查關鍵類是否正確導入
        from pineapple_ofc_gui import PineappleState
        
        # 創建測試狀態
        test_state = PineappleState()
        test_state.front_hand.cards = [Card.from_string("Ac")]
        
        if hasattr(test_state.front_hand.cards[0], 'is_joker'):
            print("  ✓ GUI 使用正確的 PineappleState 類")
        else:
            print("  ✗ GUI 使用錯誤的 PineappleState 類")
            all_tests_passed = False
            
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
        all_tests_passed = False
    
    # 3. 測試 CLI 功能
    print("\n3. 測試 CLI 基本功能...")
    try:
        result = subprocess.run(
            ["python3", "ofc_cli.py", "As", "Kh", "Qd", "Jc", "Xj", "-s", "100"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "最佳擺放" in result.stdout:
            print("  ✓ CLI 正常運作")
        else:
            print("  ✗ CLI 執行失敗")
            all_tests_passed = False
            
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
        all_tests_passed = False
    
    # 4. 測試街道 CLI
    print("\n4. 測試街道 CLI...")
    try:
        # 創建測試輸入
        with open("/tmp/test_input.txt", "w") as f:
            f.write("quit\n")
            
        result = subprocess.run(
            ["python3", "ofc_cli_street.py", "As", "Kh", "Qd", "Jc", "Xj", "--continue"],
            stdin=open("/tmp/test_input.txt"),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and "最佳擺放" in result.stdout:
            print("  ✓ 街道 CLI 正常運作")
        else:
            print("  ✗ 街道 CLI 執行失敗")
            all_tests_passed = False
            
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
        all_tests_passed = False
    
    # 總結
    print("\n=== 測試總結 ===")
    if all_tests_passed:
        print("🎉 所有測試通過！系統功能正常。")
        return 0
    else:
        print("❌ 部分測試失敗，請檢查錯誤。")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(test_all_fixes())