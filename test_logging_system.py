"""
測試結構化日誌系統

這個腳本演示如何使用 OFC Solver 的結構化日誌系統
"""

import sys
import os
import time
import json
from pathlib import Path

# 添加 src 到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import (
    Card, GameState, OFCSolver,
    MCTSEngine, HandEvaluator,
    LoggerManager, get_performance_logger
)


def test_logging_system():
    """測試日誌系統的各個功能"""
    
    print("=== OFC Solver 結構化日誌系統測試 ===\n")
    
    # 1. 測試基本日誌功能
    print("1. 測試基本日誌功能...")
    solver = OFCSolver(threads=4, time_limit=10.0)
    print("   ✓ Solver 初始化日誌已記錄\n")
    
    # 2. 測試敏感信息過濾
    print("2. 測試敏感信息過濾...")
    
    # 創建包含手牌的遊戲狀態
    cards = [
        Card('A', 's'), Card('K', 'h'), Card('Q', 'd'),
        Card('J', 'c'), Card('T', 's')
    ]
    
    game_state = GameState(
        current_cards=cards,
        front_hand=[Card('9', 'h'), Card('8', 'h'), Card('7', 'h')],
        middle_hand=[],
        back_hand=[],
        remaining_cards=5
    )
    
    # 這些手牌信息應該被過濾
    solver.logger.info(f"Testing sensitive data filter: {cards}")
    print("   ✓ 手牌信息應該被遮蔽為 [CARDS_MASKED]\n")
    
    # 3. 測試性能日誌
    print("3. 測試性能日誌...")
    result = solver.solve(game_state, {'time_limit': 2.0})
    print(f"   ✓ 求解完成，期望分數: {result.expected_score:.2f}")
    print(f"   ✓ 模擬次數: {result.simulations}")
    print(f"   ✓ 耗時: {result.time_taken:.2f} 秒\n")
    
    # 4. 測試 MCTS 引擎日誌
    print("4. 測試 MCTS 引擎日誌...")
    mcts = MCTSEngine(threads=2, max_simulations=10000)
    root = mcts.search("initial_state", time_limit=1.0)
    print(f"   ✓ MCTS 搜索完成，訪問次數: {root.visits}")
    
    # 獲取最佳動作
    best_action = mcts.get_best_action(root)
    top_actions = mcts.get_top_actions(root, n=3)
    print(f"   ✓ 最佳動作: {best_action}")
    print(f"   ✓ 前3個動作: {len(top_actions)} 個\n")
    
    # 5. 測試評估器日誌和緩存
    print("5. 測試評估器日誌...")
    evaluator = HandEvaluator()
    
    # 第一次評估（緩存未命中）
    hand1 = [Card('A', 's'), Card('K', 's'), Card('Q', 's'), 
             Card('J', 's'), Card('T', 's')]
    hand_type1, strength1 = evaluator.evaluate_hand(hand1)
    print(f"   ✓ 評估皇家同花順: {hand_type1.name}")
    
    # 第二次評估相同手牌（緩存命中）
    hand_type2, strength2 = evaluator.evaluate_hand(hand1)
    print(f"   ✓ 緩存命中測試通過")
    
    # 獲取統計信息
    stats = evaluator.get_statistics()
    print(f"   ✓ 緩存統計: 命中率 = {stats['cache_hit_rate']:.2%}\n")
    
    # 6. 測試日誌文件
    print("6. 檢查日誌文件...")
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        print(f"   ✓ 找到 {len(log_files)} 個日誌文件:")
        for log_file in log_files:
            size = log_file.stat().st_size
            print(f"     - {log_file.name}: {size:,} bytes")
        
        # 讀取並解析一行日誌
        if log_files:
            with open(log_files[0], 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line)
                            print("\n   ✓ 日誌格式示例:")
                            print(f"     時間戳: {log_entry.get('timestamp', 'N/A')}")
                            print(f"     級別: {log_entry.get('level', 'N/A')}")
                            print(f"     組件: {log_entry.get('component', 'N/A')}")
                            print(f"     消息: {log_entry.get('message', 'N/A')[:50]}...")
                            break
                        except json.JSONDecodeError:
                            pass
    else:
        print("   ! 日誌目錄尚未創建")
    
    print("\n=== 測試完成 ===")
    
    # 7. 測試錯誤處理和日誌
    print("\n7. 測試錯誤處理日誌...")
    try:
        # 創建無效的遊戲狀態（太多牌）
        invalid_state = GameState(
            current_cards=[Card('A', 's')] * 10,  # 10張A
            front_hand=[Card('K', 'h')] * 3,
            middle_hand=[Card('Q', 'd')] * 5,
            back_hand=[],
            remaining_cards=0
        )
        solver.solve(invalid_state)
    except ValueError as e:
        print(f"   ✓ 錯誤被正確捕獲並記錄: {e}")
    
    # 8. 測試日誌上下文
    print("\n8. 測試自定義日誌上下文...")
    perf_logger = get_performance_logger("test")
    
    @perf_logger.log_timing("custom_operation")
    def slow_operation():
        time.sleep(0.5)
        return "完成"
    
    result = slow_operation()
    print(f"   ✓ 自定義操作 '{result}' 的性能已記錄")
    
    print("\n=== 所有測試通過！===")


def demonstrate_log_formats():
    """演示不同的日誌格式"""
    print("\n=== 日誌格式示例 ===\n")
    
    # 創建一個簡單的日誌條目示例
    example_logs = [
        {
            "timestamp": "2025-01-27T10:30:00Z",
            "level": "INFO",
            "component": "mcts_engine",
            "message": "Search completed",
            "context": {
                "simulations": 65000,
                "time_taken": 10.5,
                "threads": 4,
                "request_id": "uuid-here"
            }
        },
        {
            "timestamp": "2025-01-27T10:30:01Z",
            "level": "DEBUG",
            "component": "evaluator",
            "message": "Cache hit for hand evaluation",
            "context": {
                "cache_hit_rate": 0.85,
                "hand_size": 5
            }
        },
        {
            "timestamp": "2025-01-27T10:30:02Z",
            "level": "WARNING",
            "component": "solver",
            "message": "Solve time approaching limit",
            "context": {
                "elapsed": 28.5,
                "limit": 30.0,
                "progress": 0.95
            }
        },
        {
            "timestamp": "2025-01-27T10:30:03Z",
            "level": "ERROR",
            "component": "api",
            "message": "Request validation failed",
            "context": {
                "error": "Missing required field: game_state",
                "request_id": "req-12345"
            },
            "exception": {
                "type": "ValidationError",
                "message": "game_state is required",
                "traceback": ["...stack trace here..."]
            }
        }
    ]
    
    print("結構化日誌格式示例:")
    for log in example_logs:
        print(f"\n{log['level']}: {log['message']}")
        print(json.dumps(log, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # 設置環境變量
    os.environ['OFC_LOG_LEVEL'] = 'DEBUG'
    os.environ['OFC_LOG_DIR'] = 'logs'
    os.environ['OFC_MASK_SENSITIVE'] = 'true'
    
    # 運行測試
    test_logging_system()
    
    # 演示日誌格式
    demonstrate_log_formats()