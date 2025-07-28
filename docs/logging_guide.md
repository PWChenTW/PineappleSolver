# OFC Solver 結構化日誌系統指南

## 概述

OFC Solver 使用結構化的 JSON 日誌格式，提供：
- 統一的日誌格式
- 自動日誌輪轉
- 敏感信息過濾
- 性能監控
- 組件級別的日誌器

## 日誌格式

### 基本格式
```json
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
}
```

### 錯誤格式
```json
{
  "timestamp": "2025-01-27T10:30:00Z",
  "level": "ERROR",
  "component": "solver",
  "message": "Solve failed: Invalid game state",
  "exception": {
    "type": "ValueError",
    "message": "Too many cards: 15",
    "traceback": ["...stack trace..."]
  }
}
```

## 使用方法

### 1. 獲取組件日誌器

```python
from src.logging_config import (
    get_solver_logger,
    get_mcts_logger,
    get_evaluator_logger,
    get_api_logger
)

# 獲取特定組件的日誌器
logger = get_solver_logger()
```

### 2. 基本日誌記錄

```python
# 簡單日誌
logger.info("Operation completed")

# 帶上下文的日誌
logger.info(
    "Search completed",
    extra={
        'component': 'mcts_engine',
        'context': {
            'simulations': 65000,
            'time_taken': 10.5
        }
    }
)
```

### 3. 使用日誌上下文

```python
from src.logging_config import LogContext

with LogContext(logger, request_id="req-123", user_id="user-456") as ctx:
    ctx.log("info", "Processing request")
    # 所有在此上下文中的日誌都會包含 request_id 和 user_id
    ctx.log("debug", "Step 1 completed")
    ctx.log("info", "Request completed", result="success")
```

### 4. 性能日誌

```python
from src.logging_config import get_performance_logger

perf_logger = get_performance_logger("my_component")

@perf_logger.log_timing("expensive_operation")
def process_data(data):
    # 自動記錄執行時間
    result = complex_calculation(data)
    return result
```

### 5. 敏感信息過濾

日誌系統會自動過濾以下敏感信息：
- 撲克牌手牌（例如：`['As', 'Kd', 'Qh']` → `[CARDS_MASKED]`）
- 單張牌（例如：`As` → `XX`）
- API 金鑰
- IP 地址

## 配置選項

### 環境變量

```bash
# 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export OFC_LOG_LEVEL=INFO

# 日誌目錄
export OFC_LOG_DIR=logs

# 是否遮蔽敏感信息
export OFC_MASK_SENSITIVE=true
```

### 程式碼配置

```python
from src.logging_config import setup_logger

logger = setup_logger(
    name="custom.component",
    component="custom",
    log_level="DEBUG",
    log_dir="custom_logs",
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5,
    mask_sensitive_data=True
)
```

## 日誌級別指南

- **DEBUG**: 詳細的調試信息（例如：MCTS 搜索進度）
- **INFO**: 一般信息（例如：請求開始/完成）
- **WARNING**: 警告信息（例如：接近時間限制）
- **ERROR**: 錯誤信息（例如：請求失敗）
- **CRITICAL**: 嚴重錯誤（例如：系統崩潰）

## 最佳實踐

### 1. 結構化上下文

```python
# 好的做法
logger.info(
    "Game completed",
    extra={
        'component': 'game_engine',
        'context': {
            'game_id': 'game-123',
            'duration': 300,
            'winner': 'player1',
            'final_scores': [50, -20]
        }
    }
)

# 避免
logger.info(f"Game game-123 completed in 300s, winner: player1")
```

### 2. 使用請求 ID

```python
import uuid

request_id = str(uuid.uuid4())

with LogContext(logger, request_id=request_id) as ctx:
    ctx.log("info", "Processing started")
    # 所有操作都使用相同的 request_id
    result = process_request()
    ctx.log("info", "Processing completed", result=result)
```

### 3. 錯誤處理

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(
        "Operation failed",
        extra={
            'component': 'processor',
            'context': {
                'error_type': type(e).__name__,
                'error_code': 'OP_001',
                'recovery_action': 'retry'
            }
        },
        exc_info=True  # 包含完整的堆棧跟踪
    )
```

### 4. 性能監控

```python
# 定期記錄性能指標
async def monitor_performance():
    while True:
        stats = get_system_stats()
        logger.info(
            "Performance metrics",
            extra={
                'component': 'monitor',
                'context': {
                    'cpu_percent': stats.cpu,
                    'memory_mb': stats.memory,
                    'active_connections': stats.connections,
                    'queue_size': stats.queue_size
                }
            }
        )
        await asyncio.sleep(60)  # 每分鐘記錄一次
```

## 日誌分析

### 查看日誌

```bash
# 查看所有日誌
tail -f logs/solver.log

# 查看特定級別的日誌
grep '"level": "ERROR"' logs/solver.log

# 查看特定請求的日誌
grep '"request_id": "req-123"' logs/*.log

# 使用 jq 格式化 JSON
tail -f logs/solver.log | jq '.'
```

### 統計分析

```bash
# 統計錯誤數量
grep '"level": "ERROR"' logs/solver.log | wc -l

# 查看最慢的操作
jq -r 'select(.context.elapsed_time > 10) | "\(.timestamp) \(.message) \(.context.elapsed_time)s"' logs/performance.log

# 計算平均響應時間
jq -r 'select(.message == "Request completed") | .context.response_time' logs/api.log | awk '{sum+=$1; count++} END {print sum/count}'
```

## 故障排除

### 日誌文件未創建
- 檢查日誌目錄權限
- 確認環境變量設置正確
- 檢查磁盤空間

### 敏感信息未過濾
- 確認 `OFC_MASK_SENSITIVE=true`
- 檢查過濾模式是否匹配

### 性能影響
- 調整日誌級別（生產環境使用 INFO）
- 減少日誌頻率
- 使用異步日誌處理

## 示例程式

完整的使用示例請參考：
- `/test_logging_system.py` - 測試所有日誌功能
- `/logging_example.py` - 實際應用示例