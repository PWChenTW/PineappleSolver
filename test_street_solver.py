#!/usr/bin/env python3
"""
測試逐街求解器的高級功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from ofc_solver_street import (
    StreetByStreetSolver, Street, OpponentTracker, 
    Card, PineappleState, StreetState,
    InitialStreetSolver, DrawStreetSolver
)
import json


def test_opponent_tracking():
    """測試對手追蹤功能"""
    print("=== 測試對手追蹤器 ===")
    
    tracker = OpponentTracker()
    
    # 模擬對手擺放一些牌
    tracker.add_known_card(Card.from_string("As"), "back")
    tracker.add_known_card(Card.from_string("Ah"), "back")
    tracker.add_known_card(Card.from_string("Kd"), "middle")
    
    # 添加一些未知牌
    tracker.add_unknown_cards(2, ["middle", "front"])
    
    # 獲取狀態
    summary = tracker.get_opponent_state_summary()
    print(f"對手狀態: {json.dumps(summary, indent=2)}")
    
    # 獲取已用牌
    used_cards = tracker.get_used_cards()
    print(f"已知對手用牌: {[str(c) for c in used_cards]}")
    print()


def test_street_by_street_solving():
    """測試逐街求解"""
    print("=== 測試逐街求解 ===")
    
    solver = StreetByStreetSolver(include_jokers=True)
    
    # 準備一手特殊的初始牌
    initial_cards = [
        Card.from_string("Qs"),
        Card.from_string("Qh"),
        Card.joker(),  # 鬼牌幫助進入夢幻樂園
        Card.from_string("5d"),
        Card.from_string("3c")
    ]
    
    print(f"初始5張牌: {' '.join(str(c) for c in initial_cards)}")
    
    # 求解整個遊戲
    result = solver.solve_game(initial_cards)
    
    # 分析結果
    print("\n=== 詳細結果分析 ===")
    for street_result in result['streets']:
        print(f"\n{street_result['street']}:")
        print(f"  結果: {street_result['result']}")
    
    print(f"\n最終玩家狀態:")
    final_state = result['final_state']
    print(f"  前墩: {final_state['front']}")
    print(f"  中墩: {final_state['middle']}")
    print(f"  後墩: {final_state['back']}")
    print(f"  棄牌: {final_state['discarded']}")
    print(f"  有效: {final_state['is_valid']}")
    print(f"  夢幻樂園: {final_state['fantasy_land']}")
    
    print(f"\n最終對手狀態:")
    print(f"  {result['opponent_state']}")


def test_custom_street_solving():
    """測試自定義街道求解"""
    print("\n=== 測試自定義街道求解 ===")
    
    # 創建一個已經擺了一些牌的狀態
    player_state = PineappleState()
    
    # 模擬已經擺好初始5張
    player_state.place_card(Card.from_string("As"), "back")
    player_state.place_card(Card.from_string("Ah"), "back")
    player_state.place_card(Card.from_string("Kd"), "middle")
    player_state.place_card(Card.from_string("Kc"), "middle")
    player_state.place_card(Card.joker(), "front")
    
    print("當前狀態:")
    print(f"  前墩: {[str(c) for c in player_state.front_hand.cards]}")
    print(f"  中墩: {[str(c) for c in player_state.middle_hand.cards]}")
    print(f"  後墩: {[str(c) for c in player_state.back_hand.cards]}")
    
    # 創建對手追蹤器
    opponent_tracker = OpponentTracker()
    
    # 創建剩餘牌堆（移除已用牌）
    from ofc_solver_joker import create_full_deck
    deck = create_full_deck(include_jokers=True)
    used_cards = player_state.get_all_cards()
    remaining_deck = [c for c in deck if c not in used_cards]
    
    # 模擬第一街抽牌
    import random
    random.shuffle(remaining_deck)
    street_cards = [remaining_deck.pop() for _ in range(3)]
    
    print(f"\n第一街抽到: {' '.join(str(c) for c in street_cards)}")
    
    # 創建街道狀態
    street_state = StreetState(
        street=Street.FIRST,
        player_state=player_state,
        opponent_tracker=opponent_tracker,
        remaining_deck=remaining_deck,
        street_cards=street_cards
    )
    
    # 使用求解器求解這一街
    draw_solver = DrawStreetSolver()
    result = draw_solver.solve_street(street_state)
    
    print(f"\n求解結果:")
    print(f"  擺放: {[(str(c), pos) for c, pos in result['placements']]}")
    print(f"  棄牌: {result['discard']}")
    
    # 顯示更新後的狀態
    print(f"\n更新後狀態:")
    print(f"  前墩: {[str(c) for c in player_state.front_hand.cards]}")
    print(f"  中墩: {[str(c) for c in player_state.middle_hand.cards]}")
    print(f"  後墩: {[str(c) for c in player_state.back_hand.cards]}")
    print(f"  棄牌: {[str(c) for c in player_state.discarded]}")


def test_performance_comparison():
    """性能比較測試"""
    print("\n=== 性能比較測試 ===")
    
    import time
    
    # 測試不同模擬次數的性能
    simulation_counts = [1000, 3000, 5000]
    
    for sim_count in simulation_counts:
        solver = StreetByStreetSolver(include_jokers=True)
        solver.initial_solver.num_simulations = sim_count
        solver.draw_solver.num_simulations = sim_count // 2
        
        start_time = time.time()
        
        # 運行一次完整遊戲
        result = solver.solve_game()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n模擬次數: {sim_count}")
        print(f"  總時間: {elapsed_time:.2f}秒")
        print(f"  最終有效: {result['final_state']['is_valid']}")
        print(f"  夢幻樂園: {result['final_state']['fantasy_land']}")


def test_joker_strategy():
    """測試鬼牌策略"""
    print("\n=== 測試鬼牌策略 ===")
    
    # 測試有2張鬼牌的情況
    solver = StreetByStreetSolver(include_jokers=True)
    
    initial_cards = [
        Card.joker(),
        Card.joker(),
        Card.from_string("Ks"),
        Card.from_string("Td"),
        Card.from_string("5c")
    ]
    
    print(f"初始牌（2張鬼牌）: {' '.join(str(c) for c in initial_cards)}")
    
    result = solver.solve_game(initial_cards)
    
    final_state = result['final_state']
    print(f"\n最終擺放:")
    print(f"  前墩: {final_state['front']} - 夢幻樂園: {final_state['fantasy_land']}")
    print(f"  中墩: {final_state['middle']}")
    print(f"  後墩: {final_state['back']}")
    
    # 統計鬼牌位置
    joker_positions = []
    for pos, cards in [('front', final_state['front']), 
                      ('middle', final_state['middle']), 
                      ('back', final_state['back'])]:
        for card_str in cards:
            if 'X' in card_str:  # 鬼牌
                joker_positions.append(pos)
    
    print(f"\n鬼牌最終位置: {joker_positions}")


def main():
    """運行所有測試"""
    print("OFC 逐街求解器測試套件")
    print("=" * 50)
    
    # 運行各項測試
    test_opponent_tracking()
    test_street_by_street_solving()
    test_custom_street_solving()
    test_joker_strategy()
    
    # 性能測試（可選）
    print("\n是否運行性能測試？(y/n): ", end='')
    if input().lower() == 'y':
        test_performance_comparison()
    
    print("\n測試完成！")


if __name__ == "__main__":
    main()