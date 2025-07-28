#!/usr/bin/env python3
"""
OFC Solver - 初始5張牌求解範例
展示如何使用 API 求解第一條街的初始擺放
"""

import requests
import json
from typing import List, Dict

def solve_initial_five_cards(cards: List[Dict[str, str]], 
                           time_limit: float = 10.0,
                           threads: int = 4) -> Dict:
    """
    求解初始5張牌的最佳擺放策略
    
    Args:
        cards: 5張牌的列表，格式如 [{"rank": "A", "suit": "s"}, ...]
        time_limit: 求解時間限制（秒）
        threads: 使用的線程數
    
    Returns:
        API 響應結果
    """
    
    # API 端點
    api_url = "http://localhost:8000/api/v1/solve"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "test_key"
    }
    
    # 構建遊戲狀態 - 初始狀態所有墩位都是空的
    game_state = {
        "current_round": 1,
        "players": [
            {
                "player_id": "player1",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            },
            {
                "player_id": "player2",
                "top_hand": {"cards": [], "max_size": 3},
                "middle_hand": {"cards": [], "max_size": 5},
                "bottom_hand": {"cards": [], "max_size": 5},
                "in_fantasy_land": False,
                "next_fantasy_land": False,
                "is_folded": False
            }
        ],
        "current_player_index": 0,
        "drawn_cards": cards,
        "remaining_deck": []  # 初始求解不需要剩餘牌庫
    }
    
    # 求解選項
    options = {
        "time_limit": time_limit,
        "threads": threads
    }
    
    # 發送請求
    request_data = {
        "game_state": game_state,
        "options": options
    }
    
    try:
        response = requests.post(api_url, json=request_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 請求失敗: {e}")
        if hasattr(e.response, 'text'):
            print(f"錯誤詳情: {e.response.text}")
        return None


def print_result(result: Dict):
    """打印求解結果"""
    if not result:
        return
    
    # 調試: 打印原始響應
    print("\n[DEBUG] 原始響應:")
    print(json.dumps(result, indent=2))
    
    print("\n🎯 最佳擺放策略:")
    print("-" * 40)
    
    # 獲取最佳動作
    best_move = result.get('best_move') or result.get('move')
    if best_move and not best_move.get('is_fold', False):
        placements = best_move.get('card_placements', [])
        if not placements:
            print("  [警告] 沒有找到卡牌擺放信息")
        else:
            for placement in placements:
                card = placement['card']
                hand = placement['hand']
                
                # 將花色符號轉換為中文
                suit_symbols = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
                card_str = f"{card['rank']}{suit_symbols.get(card['suit'], card['suit'])}"
                
                # 將位置轉換為中文
                hand_names = {'top': '前墩', 'middle': '中墩', 'bottom': '後墩'}
                hand_name = hand_names.get(hand, hand)
                
                print(f"  {card_str} → {hand_name}")
    else:
        print("  建議棄牌")
    
    print("\n📊 評估信息:")
    print(f"  期望分數: {result.get('evaluation', 0):.2f}")
    print(f"  置信度: {result.get('confidence', 0):.2%}")
    print(f"  計算時間: {result.get('computation_time', 0):.2f}秒")
    
    # 打印統計信息
    if 'statistics' in result:
        stats = result['statistics']
        print(f"\n📈 統計信息:")
        print(f"  總模擬次數: {stats.get('total_iterations', 0):,}")
        print(f"  訪問節點數: {stats.get('nodes_visited', 0):,}")


def main():
    """主函數"""
    print("=== OFC Solver 初始5張牌求解範例 ===\n")
    
    # 範例1: 一手好牌
    print("範例1: 一手好牌（對子 + 同花）")
    cards_1 = [
        {"rank": "A", "suit": "s"},  # A♠
        {"rank": "A", "suit": "h"},  # A♥ - 對子
        {"rank": "K", "suit": "s"},  # K♠ - 同花
        {"rank": "Q", "suit": "s"},  # Q♠ - 同花
        {"rank": "J", "suit": "d"}   # J♦
    ]
    result_1 = solve_initial_five_cards(cards_1, time_limit=10.0)
    print_result(result_1)
    
    print("\n" + "="*50 + "\n")
    
    # 範例2: 順子潛力
    print("範例2: 順子潛力牌")
    cards_2 = [
        {"rank": "9", "suit": "h"},   # 9♥
        {"rank": "8", "suit": "d"},   # 8♦
        {"rank": "7", "suit": "s"},   # 7♠
        {"rank": "6", "suit": "c"},   # 6♣
        {"rank": "4", "suit": "h"}    # 4♥
    ]
    result_2 = solve_initial_five_cards(cards_2, time_limit=10.0)
    print_result(result_2)
    
    print("\n" + "="*50 + "\n")
    
    # 範例3: 散牌
    print("範例3: 散牌（高牌）")
    cards_3 = [
        {"rank": "A", "suit": "d"},   # A♦
        {"rank": "K", "suit": "c"},   # K♣
        {"rank": "J", "suit": "h"},   # J♥
        {"rank": "7", "suit": "s"},   # 7♠
        {"rank": "3", "suit": "d"}    # 3♦
    ]
    result_3 = solve_initial_five_cards(cards_3, time_limit=10.0)
    print_result(result_3)


if __name__ == "__main__":
    # 檢查 API 是否運行
    try:
        health_check = requests.get("http://localhost:8000/api/v1/health")
        if health_check.status_code != 200:
            print("❌ 錯誤: API 服務器未運行")
            print("請先運行: python run_api.py")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ 錯誤: 無法連接到 API 服務器")
        print("請先運行: python run_api.py")
        exit(1)
    
    main()