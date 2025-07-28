#!/usr/bin/env python3
"""
測試 GUI 修復
驗證牌組初始化和基本功能
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 測試導入
try:
    from ofc_solver_joker import create_full_deck, Card
    from ofc_solver_optimized import (
        OptimizedStreetByStreetSolver,
        PineappleState
    )
    print("✅ 成功導入所有必要模組")
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    sys.exit(1)

def test_deck_creation():
    """測試牌組創建"""
    print("\n=== 測試牌組創建 ===")
    
    # 測試不包含鬼牌
    deck = create_full_deck(include_jokers=False)
    print(f"標準牌組大小: {len(deck)} (應該是 52)")
    assert len(deck) == 52, "標準牌組應該有52張牌"
    
    # 測試包含鬼牌
    deck_with_jokers = create_full_deck(include_jokers=True)
    print(f"包含鬼牌的牌組大小: {len(deck_with_jokers)} (應該是 54)")
    assert len(deck_with_jokers) == 54, "包含鬼牌的牌組應該有54張牌"
    
    # 檢查牌的格式
    sample_card = deck[0]
    print(f"樣本牌: {sample_card}")
    assert hasattr(sample_card, 'rank'), "牌應該有 rank 屬性"
    assert hasattr(sample_card, 'suit'), "牌應該有 suit 屬性"
    
    print("✅ 牌組創建測試通過")

def test_solver_initialization():
    """測試求解器初始化"""
    print("\n=== 測試求解器初始化 ===")
    
    try:
        solver = OptimizedStreetByStreetSolver(
            include_jokers=True,
            num_simulations=100
        )
        print("✅ 求解器初始化成功")
        
        # 測試基本屬性
        assert hasattr(solver, 'num_simulations'), "求解器應該有 num_simulations 屬性"
        assert hasattr(solver, 'include_jokers'), "求解器應該有 include_jokers 屬性"
        print(f"  - 模擬次數: {solver.num_simulations}")
        print(f"  - 包含鬼牌: {solver.include_jokers}")
        
    except Exception as e:
        print(f"❌ 求解器初始化失敗: {e}")
        raise

def test_game_state():
    """測試遊戲狀態"""
    print("\n=== 測試遊戲狀態 ===")
    
    try:
        state = PineappleState()
        print("✅ 遊戲狀態創建成功")
        
        # 測試手牌
        assert hasattr(state, 'front_hand'), "狀態應該有前墩"
        assert hasattr(state, 'middle_hand'), "狀態應該有中墩"
        assert hasattr(state, 'back_hand'), "狀態應該有後墩"
        
        # 測試放牌
        test_card = Card(rank='A', suit='s')
        state.place_card(test_card, 'front')
        assert len(state.front_hand.cards) == 1, "前墩應該有1張牌"
        print(f"✅ 成功放置牌到前墩: {test_card}")
        
    except Exception as e:
        print(f"❌ 遊戲狀態測試失敗: {e}")
        raise

def test_deck_operations():
    """測試牌組操作"""
    print("\n=== 測試牌組操作 ===")
    
    deck = create_full_deck(include_jokers=False)
    original_size = len(deck)
    
    # 測試移除牌
    import random
    random.shuffle(deck)
    drawn_cards = []
    for _ in range(5):
        if deck:
            drawn_cards.append(deck.pop())
    
    print(f"抽取了 {len(drawn_cards)} 張牌")
    print(f"剩餘牌數: {len(deck)} (應該是 {original_size - 5})")
    assert len(deck) == original_size - 5, "牌數計算錯誤"
    
    print("✅ 牌組操作測試通過")

def main():
    """運行所有測試"""
    print("開始測試 GUI 相關修復...\n")
    
    try:
        test_deck_creation()
        test_solver_initialization()
        test_game_state()
        test_deck_operations()
        
        print("\n" + "="*50)
        print("✅ 所有 GUI 相關測試通過！")
        print("GUI 應該能正常運行了")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()