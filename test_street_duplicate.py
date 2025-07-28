#!/usr/bin/env python3
"""
測試街道 AI 建議重複問題
"""

from ofc_solver_joker import Card, PineappleStateJoker as PineappleState
from ofc_cli_street import StreetByStreetCLI


def test_street_suggestion():
    """測試街道 AI 建議邏輯"""
    print("=== 測試街道 AI 建議 ===")
    
    # 創建測試狀態
    game_state = PineappleState()
    
    # 模擬初始5張牌已擺放
    game_state.front_hand.cards = [Card.from_string("Jc")]
    game_state.middle_hand.cards = [Card.from_string("Kh"), Card.from_string("Qd")]
    game_state.back_hand.cards = [Card.from_string("As"), Card.from_string("Th")]
    
    print("當前狀態:")
    print(f"前墩: {' '.join(str(c) for c in game_state.front_hand.cards)}")
    print(f"中墩: {' '.join(str(c) for c in game_state.middle_hand.cards)}")
    print(f"後墩: {' '.join(str(c) for c in game_state.back_hand.cards)}")
    
    # 第一街的3張牌
    street_cards = [
        Card.from_string("9h"),
        Card.from_string("8s"),
        Card.from_string("7d")
    ]
    
    print(f"\n第一街抽到: {' '.join(str(c) for c in street_cards)}")
    
    # 使用街道求解器
    solver = StreetByStreetCLI(num_simulations=100)
    solver.game_state = game_state
    solver.used_cards = {"Jc", "Kh", "Qd", "As", "Th"}
    
    # 生成所有可能的動作
    actions = solver._generate_possible_actions(street_cards)
    print(f"\n生成了 {len(actions)} 種可能的動作")
    
    # 評估前5個動作
    print("\n評估前5個動作:")
    for i, (placements, discard) in enumerate(actions[:5]):
        print(f"\n動作 {i+1}:")
        print(f"  擺放: {[(str(c), pos) for c, pos in placements]}")
        print(f"  棄牌: {discard}")
        
        # 驗證沒有重複
        placed_cards = [c for c, _ in placements]
        all_cards = placed_cards + [discard]
        
        if len(set(str(c) for c in all_cards)) == 3:
            print("  ✓ 沒有重複牌")
        else:
            print("  ✗ 發現重複牌！")
            
    # 找出最佳動作
    best_score = float('-inf')
    best_action = None
    
    for placements, discard in actions[:20]:
        temp_state = solver._copy_state(game_state)
        
        valid = True
        for card, position in placements:
            if not solver._can_place_card(temp_state, position):
                valid = False
                break
            solver._place_card_in_state(temp_state, card, position)
        
        if not valid or not temp_state.is_valid():
            continue
        
        score = solver._evaluate_state(temp_state)
        
        if score > best_score:
            best_score = score
            best_action = (placements, discard)
    
    if best_action:
        placements, discard = best_action
        print(f"\n最佳動作:")
        print(f"  擺放: {[(str(c), pos) for c, pos in placements]}")
        print(f"  棄牌: {discard}")
        
        # 驗證最終建議沒有重複
        suggestion = {
            'placements': [(str(c), pos) for c, pos in placements],
            'discard': str(discard)
        }
        
        # 檢查所有牌
        all_cards_str = [c for c, _ in suggestion['placements']] + [suggestion['discard']]
        unique_cards = set(all_cards_str)
        
        print(f"\n檢查最終建議:")
        print(f"  所有牌: {all_cards_str}")
        print(f"  唯一牌: {unique_cards}")
        
        if len(all_cards_str) == len(unique_cards):
            print("  ✓ 沒有重複牌，測試通過！")
            return True
        else:
            print("  ✗ 發現重複牌！")
            return False
    
    return False


if __name__ == "__main__":
    success = test_street_suggestion()
    if success:
        print("\n🎉 街道 AI 建議測試通過！")
    else:
        print("\n❌ 街道 AI 建議測試失敗")