"""
OFC Solver 結構化日誌系統使用示例

這個文件展示如何在實際應用中使用日誌系統
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加 src 到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import (
    Card, GameState, OFCSolver,
    get_api_logger, LogContext,
    get_performance_logger
)


# 模擬 API 處理函數
async def handle_solve_request(request_data: dict) -> dict:
    """處理求解請求（模擬 API 端點）"""
    
    # 獲取 API 日誌器
    api_logger = get_api_logger()
    perf_logger = get_performance_logger("api")
    
    # 創建請求上下文
    request_id = request_data.get('request_id', 'unknown')
    client_ip = request_data.get('client_ip', 'unknown')
    
    with LogContext(api_logger, 
                   request_id=request_id,
                   client_ip=client_ip,
                   endpoint="/api/v1/solve") as log_ctx:
        
        # 記錄請求接收
        log_ctx.log("info", "Received solve request",
                   method="POST",
                   user_agent=request_data.get('user_agent', 'unknown'))
        
        try:
            # 驗證請求
            if 'game_state' not in request_data:
                log_ctx.log("warning", "Invalid request: missing game_state")
                return {
                    'success': False,
                    'error': 'Missing required field: game_state',
                    'request_id': request_id
                }
            
            # 解析遊戲狀態
            game_data = request_data['game_state']
            current_cards = [
                Card(c['rank'], c['suit']) 
                for c in game_data.get('current_cards', [])
            ]
            
            game_state = GameState(
                current_cards=current_cards,
                front_hand=[],
                middle_hand=[],
                back_hand=[],
                remaining_cards=game_data.get('remaining_cards', 52)
            )
            
            # 記錄開始求解
            log_ctx.log("info", "Starting solve operation",
                       cards_count=len(current_cards),
                       remaining_cards=game_state.remaining_cards)
            
            # 創建求解器並求解
            solver = OFCSolver(
                threads=request_data.get('threads', 4),
                time_limit=request_data.get('time_limit', 30.0)
            )
            
            # 使用性能日誌包裝求解過程
            @perf_logger.log_timing("api_solve_request")
            async def solve_with_timing():
                # 模擬異步操作
                await asyncio.sleep(0.1)
                return solver.solve(game_state)
            
            result = await solve_with_timing()
            
            # 構建響應
            response = {
                'success': True,
                'request_id': request_id,
                'result': {
                    'best_placement': result.best_placement,
                    'expected_score': result.expected_score,
                    'confidence': result.confidence,
                    'simulations': result.simulations,
                    'time_taken': result.time_taken,
                    'top_actions': result.top_actions[:3]  # 只返回前3個
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            # 記錄成功響應
            log_ctx.log("info", "Request completed successfully",
                       expected_score=result.expected_score,
                       simulations=result.simulations,
                       response_time=result.time_taken)
            
            return response
            
        except Exception as e:
            # 記錄錯誤
            log_ctx.log("error", f"Request failed: {str(e)}",
                       error_type=type(e).__name__)
            
            return {
                'success': False,
                'error': 'Internal server error',
                'request_id': request_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }


async def simulate_concurrent_requests():
    """模擬併發請求"""
    print("=== 模擬併發 API 請求 ===\n")
    
    # 創建多個請求
    requests = []
    for i in range(5):
        request = {
            'request_id': f'req-{i+1:03d}',
            'client_ip': f'192.168.1.{100+i}',
            'user_agent': 'OFC-Client/1.0',
            'game_state': {
                'current_cards': [
                    {'rank': 'A', 'suit': 's'},
                    {'rank': 'K', 'suit': 'h'},
                    {'rank': 'Q', 'suit': 'd'}
                ],
                'remaining_cards': 49
            },
            'threads': 2,
            'time_limit': 5.0
        }
        requests.append(handle_solve_request(request))
    
    # 併發執行
    print(f"發送 {len(requests)} 個併發請求...")
    start_time = asyncio.get_event_loop().time()
    
    responses = await asyncio.gather(*requests)
    
    end_time = asyncio.get_event_loop().time()
    total_time = end_time - start_time
    
    # 顯示結果
    print(f"\n所有請求完成，總耗時: {total_time:.2f} 秒")
    print(f"平均響應時間: {total_time/len(requests):.2f} 秒/請求\n")
    
    # 顯示每個請求的結果
    for i, response in enumerate(responses):
        if response['success']:
            result = response['result']
            print(f"請求 {i+1}: 成功")
            print(f"  - 期望分數: {result['expected_score']:.2f}")
            print(f"  - 模擬次數: {result['simulations']}")
            print(f"  - 置信度: {result['confidence']:.2%}")
        else:
            print(f"請求 {i+1}: 失敗 - {response['error']}")


def demonstrate_log_patterns():
    """演示常見的日誌模式"""
    print("\n=== 常見日誌模式示例 ===\n")
    
    solver = OFCSolver()
    logger = solver.logger
    
    # 1. 業務流程日誌
    print("1. 業務流程日誌:")
    with LogContext(logger, operation="game_flow", game_id="game-123") as ctx:
        ctx.log("info", "Game started", players=2, variant="pineapple")
        ctx.log("info", "Round 1 completed", scores=[10, -5])
        ctx.log("info", "Game ended", winner="player1", duration=300)
    
    # 2. 性能監控日誌
    print("\n2. 性能監控日誌:")
    logger.info(
        "Performance metrics",
        extra={
            'component': 'solver',
            'context': {
                'cpu_usage': 75.5,
                'memory_mb': 256,
                'active_threads': 4,
                'queue_size': 10
            }
        }
    )
    
    # 3. 審計日誌
    print("\n3. 審計日誌:")
    logger.info(
        "User action",
        extra={
            'component': 'audit',
            'context': {
                'user_id': 'user-456',
                'action': 'solve_request',
                'resource': 'ofc_solver',
                'result': 'success',
                'ip_address': '[IP_MASKED]'  # 已遮蔽
            }
        }
    )
    
    # 4. 錯誤追蹤日誌
    print("\n4. 錯誤追蹤日誌:")
    try:
        # 模擬錯誤
        raise ValueError("Invalid card combination")
    except Exception as e:
        logger.error(
            "Validation error occurred",
            extra={
                'component': 'validator',
                'context': {
                    'error_code': 'INVALID_COMBO',
                    'user_input': '[CARDS_MASKED]',  # 已遮蔽
                    'validation_rule': 'no_duplicates'
                }
            },
            exc_info=True
        )
    
    print("\n所有日誌模式已記錄到日誌文件中")


def main():
    """主函數"""
    # 設置環境變量
    os.environ['OFC_LOG_LEVEL'] = 'DEBUG'
    os.environ['OFC_LOG_DIR'] = 'logs'
    os.environ['OFC_MASK_SENSITIVE'] = 'true'
    
    print("OFC Solver 結構化日誌系統使用示例")
    print("=" * 50)
    
    # 運行異步示例
    asyncio.run(simulate_concurrent_requests())
    
    # 演示日誌模式
    demonstrate_log_patterns()
    
    print("\n查看 logs/ 目錄中的日誌文件以查看詳細的日誌記錄")


if __name__ == "__main__":
    main()