#!/usr/bin/env python3
"""
調試 GUI 重複牌問題
"""

from ofc_solver_joker import Card


def debug_apply_suggestion():
    """模擬 GUI 應用建議的過程"""
    print("=== 調試 GUI 重複牌問題 ===")
    
    # 模擬街道牌
    street_cards = [
        Card.from_string("9h"),
        Card.from_string("8s"),
        Card.from_string("7d")
    ]
    
    # 模擬 AI 建議
    suggestion = {
        'placements': [('9h', 'front'), ('8s', 'front')],
        'discard': '7d'
    }
    
    print(f"街道牌: {[str(c) for c in street_cards]}")
    print(f"AI 建議: {suggestion}")
    
    # 舊的實現（有問題）
    print("\n=== 舊實現（有問題）===")
    placed_cards_old = []
    for card_str, position in suggestion['placements']:
        for card in street_cards:
            if str(card) == card_str and card not in placed_cards_old:
                print(f"  放置 {card} 到 {position}")
                placed_cards_old.append(card)
                break
    
    # 找棄牌
    for card in street_cards:
        if str(card) == suggestion['discard']:
            print(f"  棄牌: {card}")
            break
    
    print(f"已放置的牌: {[str(c) for c in placed_cards_old]}")
    
    # 新的實現（修復版）
    print("\n=== 新實現（修復版）===")
    placed_cards_new = []
    discard_card = None
    
    # 先找到棄牌
    for card in street_cards:
        if str(card) == suggestion['discard']:
            discard_card = card
            print(f"  找到棄牌: {discard_card}")
            break
    
    # 然後放置其他牌
    for card_str, position in suggestion['placements']:
        for card in street_cards:
            if str(card) == card_str and card not in placed_cards_new and card != discard_card:
                print(f"  放置 {card} 到 {position}")
                placed_cards_new.append(card)
                break
    
    print(f"已放置的牌: {[str(c) for c in placed_cards_new]}")
    print(f"棄牌: {discard_card}")
    
    # 檢查結果
    all_processed = placed_cards_new + ([discard_card] if discard_card else [])
    unique_cards = set(str(c) for c in all_processed)
    
    print(f"\n所有處理的牌: {[str(c) for c in all_processed]}")
    print(f"唯一牌數量: {len(unique_cards)}")
    
    if len(all_processed) == 3 and len(unique_cards) == 3:
        print("✓ 新實現正確，沒有重複！")
    else:
        print("✗ 仍有問題")


if __name__ == "__main__":
    debug_apply_suggestion()