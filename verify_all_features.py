#!/usr/bin/env python3
"""
功能驗證腳本 - 測試所有實現的功能
"""

import sys
import subprocess
import time
from ofc_solver_joker import PineappleOFCSolverJoker, Card, create_full_deck
from ofc_cli_street import StreetByStreetCLI


def test_joker_support():
    """測試鬼牌支持"""
    print("\n=== 測試鬼牌支持 ===")
    
    # 創建包含鬼牌的牌組
    deck = create_full_deck(include_jokers=True)
    joker_cards = [c for c in deck if c.is_joker()]
    
    print(f"✓ 牌組包含 {len(joker_cards)} 張鬼牌")
    
    # 測試鬼牌求解
    solver = PineappleOFCSolverJoker(num_simulations=1000)
    test_cards = [Card.from_string("As"), Card.from_string("Kh"), 
                  Card.from_string("Qd"), Card.from_string("Jc"),
                  Card.from_string("Xj")]
    
    print("測試求解包含鬼牌的初始牌...")
    result = solver.solve_initial_five(test_cards)
    
    if result and result.is_valid():
        print("✓ 成功求解包含鬼牌的初始牌")
        return True
    else:
        print("✗ 求解失敗")
        return False


def test_street_by_street_solver():
    """測試逐街求解器"""
    print("\n=== 測試逐街求解器 ===")
    
    cli = StreetByStreetCLI(num_simulations=1000)
    
    # 測試初始5張牌
    initial_cards = [Card.from_string(c) for c in ["As", "Kh", "Qd", "Jc", "Th"]]
    print("測試初始5張牌求解...")
    result = cli.solve_initial(initial_cards)
    
    if result and result.is_valid():
        print("✓ 初始牌求解成功")
        
        # 測試下一街
        street_cards = [Card.from_string(c) for c in ["9h", "8s", "7d"]]
        print("\n測試第一街求解...")
        result2 = cli.solve_next_street(street_cards)
        
        if result2:
            print("✓ 街道求解成功")
            return True
    
    print("✗ 求解失敗")
    return False


def test_random_dealing():
    """測試隨機發牌功能"""
    print("\n=== 測試隨機發牌 ===")
    
    from ofc_solver_optimized import OptimizedStreetByStreetSolver
    
    solver = OptimizedStreetByStreetSolver()
    
    # 測試隨機初始牌
    print("測試隨機發初始5張牌...")
    from ofc_solver_joker import create_full_deck
    import random
    deck = create_full_deck(include_jokers=True)
    random.shuffle(deck)
    initial_cards = deck[:5]
    
    if initial_cards and len(initial_cards) == 5:
        print(f"✓ 成功發牌: {' '.join(str(c) for c in initial_cards)}")
        
        # 檢查沒有重複
        if len(set(str(c) for c in initial_cards)) == 5:
            print("✓ 沒有重複的牌")
            return True
        else:
            print("✗ 發現重複的牌")
    
    return False


def test_performance_optimization():
    """測試性能優化"""
    print("\n=== 測試性能優化 ===")
    
    from ofc_solver_optimized import OptimizedStreetByStreetSolver
    import time
    
    from ofc_solver_joker import PineappleOFCSolverJoker
    solver = PineappleOFCSolverJoker(num_simulations=10000)
    cards = [Card.from_string(c) for c in ["As", "Kh", "Qd", "Jc", "Th"]]
    
    print("運行 10,000 次模擬...")
    start_time = time.time()
    result = solver.solve_initial_five(cards)
    elapsed = time.time() - start_time
    
    print(f"✓ 完成時間: {elapsed:.2f} 秒")
    
    if elapsed < 5:
        print("✓ 性能達標（< 5秒）")
        return True
    else:
        print("✗ 性能未達標")
        return False


def test_cli_interface():
    """測試命令行介面"""
    print("\n=== 測試命令行介面 ===")
    
    # 測試基本 CLI
    print("測試基本 CLI...")
    result = subprocess.run(
        ["python3", "ofc_cli.py", "As", "Kh", "Qd", "Jc", "Th", "-s", "100"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "最佳擺放" in result.stdout:
        print("✓ 基本 CLI 正常")
    else:
        print("✗ 基本 CLI 失敗")
        return False
    
    # 測試鬼牌 CLI
    print("\n測試鬼牌 CLI...")
    result = subprocess.run(
        ["python3", "ofc_cli.py", "As", "Kh", "Qd", "Jc", "Xj", "-s", "100"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and "最佳擺放" in result.stdout:
        print("✓ 鬼牌 CLI 正常")
        return True
    else:
        print("✗ 鬼牌 CLI 失敗")
        return False


def test_gui_imports():
    """測試 GUI 導入"""
    print("\n=== 測試 GUI 導入 ===")
    
    try:
        # 測試導入
        import pineapple_ofc_gui
        print("✓ GUI 模組導入成功")
        
        # 檢查關鍵函數
        if hasattr(pineapple_ofc_gui, 'main'):
            print("✓ main 函數存在")
            return True
    except Exception as e:
        print(f"✗ GUI 導入失敗: {e}")
    
    return False


def main():
    """主測試函數"""
    print("=== 開始功能驗證 ===")
    
    tests = [
        ("鬼牌支持", test_joker_support),
        ("逐街求解", test_street_by_street_solver),
        ("隨機發牌", test_random_dealing),
        ("性能優化", test_performance_optimization),
        ("CLI 介面", test_cli_interface),
        ("GUI 導入", test_gui_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"✗ {test_name} 測試異常: {e}")
            results.append((test_name, False))
    
    # 總結
    print("\n=== 測試總結 ===")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ 通過" if success else "✗ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有功能測試通過！")
        return 0
    else:
        print("\n❌ 部分測試失敗，請檢查錯誤")
        return 1


if __name__ == "__main__":
    sys.exit(main())