#!/usr/bin/env python3
"""
測試數據生成腳本
生成用於 GUI 測試的測試數據和場景
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any

def generate_test_game_states():
    """生成測試用的遊戲狀態"""
    test_states = []
    
    # 1. 初始狀態
    test_states.append({
        "name": "initial_state",
        "description": "遊戲初始狀態",
        "timestamp": datetime.now().isoformat(),
        "game_state": {
            "front": [],
            "middle": [],
            "back": [],
            "discarded": []
        },
        "current_street": 0,
        "settings": {
            "num_simulations": 10000,
            "include_jokers": True
        }
    })
    
    # 2. 部分完成狀態
    test_states.append({
        "name": "partial_game",
        "description": "部分完成的遊戲",
        "timestamp": datetime.now().isoformat(),
        "game_state": {
            "front": ["Ah", "Kh", "Qh"],
            "middle": ["Jh", "10h", "9h", "8h"],
            "back": ["7h", "6h", "5h"],
            "discarded": ["2c", "3d"]
        },
        "current_street": 3,
        "settings": {
            "num_simulations": 25000,
            "include_jokers": True
        }
    })
    
    # 3. Fantasy Land 狀態
    test_states.append({
        "name": "fantasy_land",
        "description": "達到 Fantasy Land 的狀態",
        "timestamp": datetime.now().isoformat(),
        "game_state": {
            "front": ["Qh", "Qd", "Kh"],
            "middle": ["Ah", "Ad", "Ac", "Kd", "Kc"],
            "back": ["Jh", "Jd", "Jc", "10h", "10d"],
            "discarded": []
        },
        "current_street": 5,
        "settings": {
            "num_simulations": 50000,
            "include_jokers": False
        }
    })
    
    # 4. 犯規狀態
    test_states.append({
        "name": "foul_state",
        "description": "犯規的遊戲狀態",
        "timestamp": datetime.now().isoformat(),
        "game_state": {
            "front": ["Ah", "Ad", "Ac"],  # 三條在前墩
            "middle": ["Kh", "Kd", "Qh", "Qd", "Jh"],  # 兩對在中墩
            "back": ["10h", "9h", "8h", "7h", "6h"],  # 順子在後墩
            "discarded": []
        },
        "current_street": 5,
        "settings": {
            "num_simulations": 10000,
            "include_jokers": False
        }
    })
    
    # 5. 包含鬼牌的狀態
    test_states.append({
        "name": "with_jokers",
        "description": "包含鬼牌的遊戲",
        "timestamp": datetime.now().isoformat(),
        "game_state": {
            "front": ["Xj", "Ah", "Kh"],  # 鬼牌在前墩
            "middle": ["Qh", "Qd", "Qc", "Jh", "Jd"],
            "back": ["10h", "10d", "10c", "9h", "9d"],
            "discarded": ["2c"]
        },
        "current_street": 4,
        "settings": {
            "num_simulations": 25000,
            "include_jokers": True
        }
    })
    
    return test_states

def generate_test_scenarios():
    """生成測試場景"""
    scenarios = []
    
    # 1. 快速遊戲場景
    scenarios.append({
        "name": "quick_game",
        "description": "快速完成一局遊戲",
        "steps": [
            {"action": "new_game"},
            {"action": "deal_initial"},
            {"action": "get_ai_suggestion"},
            {"action": "apply_suggestion"},
            {"action": "draw_street", "street": 1},
            {"action": "get_ai_suggestion"},
            {"action": "apply_suggestion"},
            {"action": "draw_street", "street": 2},
            {"action": "get_ai_suggestion"},
            {"action": "apply_suggestion"},
            {"action": "draw_street", "street": 3},
            {"action": "get_ai_suggestion"},
            {"action": "apply_suggestion"},
            {"action": "draw_street", "street": 4},
            {"action": "get_ai_suggestion"},
            {"action": "apply_suggestion"},
            {"action": "check_result"}
        ]
    })
    
    # 2. 手動放置場景
    scenarios.append({
        "name": "manual_placement",
        "description": "測試手動放置功能",
        "steps": [
            {"action": "new_game"},
            {"action": "deal_initial"},
            {"action": "select_card", "index": 0},
            {"action": "select_position", "position": "front"},
            {"action": "place_card"},
            {"action": "select_card", "index": 0},
            {"action": "select_position", "position": "middle"},
            {"action": "place_card"},
            {"action": "select_card", "index": 0},
            {"action": "select_position", "position": "back"},
            {"action": "place_card"},
            {"action": "verify_placement", "expected": {
                "front": 1,
                "middle": 1,
                "back": 1
            }}
        ]
    })
    
    # 3. 設置調整場景
    scenarios.append({
        "name": "settings_adjustment",
        "description": "測試設置調整",
        "steps": [
            {"action": "new_game"},
            {"action": "adjust_simulations", "value": 50000},
            {"action": "toggle_jokers", "enabled": False},
            {"action": "toggle_ai_thinking", "enabled": True},
            {"action": "deal_initial"},
            {"action": "get_ai_suggestion"},
            {"action": "verify_settings", "expected": {
                "simulations": 50000,
                "jokers": False,
                "ai_thinking": True
            }}
        ]
    })
    
    # 4. 保存載入場景
    scenarios.append({
        "name": "save_load",
        "description": "測試保存和載入功能",
        "steps": [
            {"action": "new_game"},
            {"action": "deal_initial"},
            {"action": "get_ai_suggestion"},
            {"action": "apply_suggestion"},
            {"action": "save_game"},
            {"action": "new_game"},
            {"action": "load_game", "file": "test_save.json"},
            {"action": "verify_state", "expected": {
                "cards_placed": 5,
                "current_street": 1
            }}
        ]
    })
    
    # 5. 錯誤處理場景
    scenarios.append({
        "name": "error_handling",
        "description": "測試錯誤處理",
        "steps": [
            {"action": "new_game"},
            {"action": "place_card"},  # 嘗試在沒有牌的情況下放置
            {"action": "verify_error"},
            {"action": "deal_initial"},
            {"action": "draw_street", "street": 1},  # 嘗試在初始階段抽街
            {"action": "verify_no_error"}
        ]
    })
    
    return scenarios

def generate_performance_test_data():
    """生成性能測試數據"""
    return {
        "load_test": {
            "concurrent_users": [1, 5, 10, 20],
            "test_duration": 300,  # 5 minutes
            "actions_per_user": 50
        },
        "stress_test": {
            "max_users": 50,
            "ramp_up_time": 60,  # 1 minute
            "sustained_duration": 600  # 10 minutes
        },
        "spike_test": {
            "normal_users": 10,
            "spike_users": 100,
            "spike_duration": 30  # 30 seconds
        },
        "endurance_test": {
            "users": 10,
            "duration": 3600  # 1 hour
        },
        "benchmarks": {
            "page_load_time": 3000,  # 3 seconds
            "ai_suggestion_time": 10000,  # 10 seconds
            "card_placement_time": 500,  # 0.5 seconds
            "save_game_time": 1000  # 1 second
        }
    }

def save_test_data():
    """保存所有測試數據"""
    # 確保測試數據目錄存在
    test_data_dir = "test_data"
    os.makedirs(test_data_dir, exist_ok=True)
    
    # 保存遊戲狀態
    game_states = generate_test_game_states()
    with open(os.path.join(test_data_dir, "test_game_states.json"), 'w') as f:
        json.dump(game_states, f, indent=2)
    print(f"Generated {len(game_states)} test game states")
    
    # 保存測試場景
    scenarios = generate_test_scenarios()
    with open(os.path.join(test_data_dir, "test_scenarios.json"), 'w') as f:
        json.dump(scenarios, f, indent=2)
    print(f"Generated {len(scenarios)} test scenarios")
    
    # 保存性能測試數據
    perf_data = generate_performance_test_data()
    with open(os.path.join(test_data_dir, "performance_test_data.json"), 'w') as f:
        json.dump(perf_data, f, indent=2)
    print("Generated performance test data")
    
    # 生成測試報告模板
    report_template = {
        "test_suite": "Pineapple OFC GUI Tests",
        "test_date": datetime.now().isoformat(),
        "environment": {
            "browser": "chrome",
            "headless": True,
            "platform": "linux"
        },
        "results": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration": 0
        },
        "test_cases": []
    }
    
    with open(os.path.join(test_data_dir, "report_template.json"), 'w') as f:
        json.dump(report_template, f, indent=2)
    print("Generated report template")

if __name__ == "__main__":
    save_test_data()
    print("\nTest data generation complete!")
    print("Files saved in 'test_data' directory")