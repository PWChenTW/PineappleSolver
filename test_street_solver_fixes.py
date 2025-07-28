#!/usr/bin/env python3
"""
測試街道求解器的修復
驗證自動發牌和對手牌追蹤功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ofc_cli_street import StreetByStreetCLI
from ofc_solver_joker import Card

def test_auto_deal():
    """測試自動發牌功能"""
    print("=== 測試自動發牌功能 ===")
    
    cli = StreetByStreetCLI(num_simulations=1000)
    
    # 設置一些對手的牌
    opponent_cards = ["As", "Kh", "Qd", "Jc", "10s"]
    for card_str in opponent_cards:
        card = Card.from_string(card_str)
        cli.opponent_cards.add(str(card))
        cli._remove_from_deck(card)
    
    print(f"對手的牌: {', '.join(opponent_cards)}")
    print(f"剩餘可用牌數: {cli.get_remaining_cards_count()}")
    
    # 測試發初始5張牌
    initial_cards = cli._deal_cards(5)
    if initial_cards:
        print(f"發到的初始牌: {', '.join(str(c) for c in initial_cards)}")
        
        # 確認沒有發到對手的牌
        for card in initial_cards:
            assert str(card) not in cli.opponent_cards, f"錯誤：發到了對手的牌 {card}"
        
        # 模擬擺放
        cli.solve_initial(initial_cards)
        
        # 測試發街道牌
        print("\n測試發街道牌...")
        for street in range(1, 5):
            remaining = cli.get_remaining_cards_count()
            print(f"\n第 {street} 街前剩餘牌數: {remaining}")
            
            if remaining >= 3:
                street_cards = cli._deal_cards(3)
                if street_cards:
                    print(f"第 {street} 街發到: {', '.join(str(c) for c in street_cards)}")
                    
                    # 模擬求解
                    cli.solve_next_street(street_cards)
                else:
                    print("無法發牌")
                    break
            else:
                print("牌不夠了")
                break
        
        print("\n✅ 自動發牌功能測試通過！")
    else:
        print("❌ 無法發初始牌")

def test_card_tracking():
    """測試牌追蹤系統"""
    print("\n=== 測試牌追蹤系統 ===")
    
    cli = StreetByStreetCLI(num_simulations=100)
    
    # 初始狀態
    print(f"初始牌組大小: {len(cli.deck)}")
    assert len(cli.deck) == 52, "牌組應該有52張牌"
    
    # 添加對手牌
    opp_cards = ["As", "Ks", "Qs"]
    for card_str in opp_cards:
        card = Card.from_string(card_str)
        cli.opponent_cards.add(str(card))
        cli._remove_from_deck(card)
    
    # 發一些牌
    dealt = cli._deal_cards(5)
    for card in dealt:
        cli.used_cards.add(str(card))
    
    # 棄牌
    discard = Card.from_string("2h")
    cli.discarded_cards.add(str(discard))
    cli._remove_from_deck(discard)
    
    # 打印狀態
    cli.print_game_status()
    
    # 驗證
    total_tracked = len(cli.used_cards) + len(cli.opponent_cards) + len(cli.discarded_cards)
    remaining = cli.get_remaining_cards_count()
    
    print(f"\n追蹤的牌總數: {total_tracked}")
    print(f"剩餘可用牌數: {remaining}")
    print(f"總和應該是52: {total_tracked + remaining}")
    
    assert total_tracked + remaining == 52, "牌數統計錯誤"
    
    print("\n✅ 牌追蹤系統測試通過！")

def test_manual_vs_auto_mode():
    """測試手動和自動模式切換"""
    print("\n=== 測試模式切換 ===")
    
    cli = StreetByStreetCLI()
    
    print(f"默認模式（應該是自動）: {'自動' if cli.auto_deal else '手動'}")
    assert cli.auto_deal == True, "默認應該是自動模式"
    
    # 切換到手動模式
    cli.auto_deal = False
    print(f"切換後模式: {'自動' if cli.auto_deal else '手動'}")
    assert cli.auto_deal == False, "應該切換到手動模式"
    
    print("\n✅ 模式切換測試通過！")

def main():
    """運行所有測試"""
    print("開始測試街道求解器修復...\n")
    
    try:
        test_auto_deal()
        test_card_tracking()
        test_manual_vs_auto_mode()
        
        print("\n" + "="*50)
        print("✅ 所有測試通過！")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()