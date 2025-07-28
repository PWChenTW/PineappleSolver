# OFC Solver 錯誤處理指南

本指南詳細介紹 OFC Solver 的錯誤處理系統，包括所有自定義異常類型、錯誤恢復機制和最佳實踐。

## 錯誤類型概覽

### 1. InvalidInputError
無效輸入時拋出，包括：
- 無效的卡牌表示
- 重複的卡牌
- 錯誤的數據格式

```python
try:
    cards = validate_card_list(["AS", "XX", "KH"])
except InvalidInputError as e:
    print(f"Error: {e}")
    print(f"Details: {e.details}")
```

### 2. TimeoutError
操作超時時拋出，支持部分結果返回：

```python
solver = OFCSolver(SolverConfig(
    time_limit=10.0,
    return_partial_on_timeout=True
))

try:
    result = solver.solve(game_state)
except TimeoutError as e:
    if e.partial_result:
        print(f"Partial result available: {e.partial_result}")
```

### 3. ResourceError
系統資源不足時拋出：
- 內存不足
- 線程池耗盡
- 文件系統問題

```python
try:
    result = solver.solve(game_state)
except ResourceError as e:
    print(f"Resource type: {e.details['resource_type']}")
    print(f"Available: {e.details['available']}")
    print(f"Required: {e.details['required']}")
```

### 4. GameRuleViolationError
違反遊戲規則時拋出：
- 無效的卡牌放置
- 違反 OFC 手牌排序規則
- 非法動作

```python
try:
    validate_placement("front", 0, arrangement)
except GameRuleViolationError as e:
    print(f"Rule violated: {e.details['rule_violated']}")
```

### 5. ConfigurationError
配置錯誤時拋出：
- 無效的參數值
- 衝突的設置
- 缺少必要配置

```python
try:
    config = SolverConfig(time_limit=-1.0)
except ConfigurationError as e:
    print(f"Invalid parameter: {e.details['parameter']}")
```

### 6. StateError
狀態錯誤時拋出：
- 在錯誤狀態下執行操作
- 無效的狀態轉換

```python
try:
    game_state.deal_street()
except StateError as e:
    print(f"Current state: {e.details['current_state']}")
    print(f"Expected state: {e.details['expected_state']}")
```

## 錯誤恢復機制

### 1. 超時部分結果
當求解超時時，可以返回部分結果：

```python
config = SolverConfig(
    time_limit=30.0,
    return_partial_on_timeout=True  # 啟用部分結果
)

solver = OFCSolver(config)
result = solver.solve(game_state)

if not result.is_complete:
    print(f"Partial result: {result.num_simulations} simulations")
    print(f"Best action so far: {result.best_action}")
```

### 2. 資源降級
當資源不足時，自動降級到單線程模式：

```python
# 初始配置使用 8 線程
solver = OFCSolver(SolverConfig(num_threads=8))

# 如果內存不足，會自動降級到單線程
# 這是自動處理的，無需手動干預
result = solver.solve(game_state)
```

### 3. 錯誤恢復裝飾器
使用裝飾器自動處理可恢復的錯誤：

```python
from src.validation import with_error_recovery

@with_error_recovery(
    default_return=None,
    recoverable_errors=(ResourceError, TimeoutError)
)
def process_game(game_state):
    # 可能拋出 ResourceError 或 TimeoutError
    return solver.solve(game_state)

# 錯誤會被自動恢復
result = process_game(game_state)
```

## 驗證裝飾器

### 1. @validate_input
驗證函數輸入：

```python
@validate_input(lambda x: x > 0, "Value must be positive")
def process_value(value: int) -> int:
    return value * 2
```

### 2. @validate_game_state
驗證遊戲狀態：

```python
@validate_game_state
def analyze_game(game_state: GameState):
    # 自動驗證 game_state 的有效性
    return game_state.analyze()
```

### 3. @ensure_resources
確保資源充足：

```python
@ensure_resources(memory_mb=100, threads=4)
def memory_intensive_task():
    # 執行前會檢查是否有 100MB 內存和 4 個線程可用
    pass
```

### 4. @with_timeout
設置操作超時：

```python
@with_timeout(10.0, operation_name="analysis")
def analyze_position(game_state):
    # 超過 10 秒會拋出 TimeoutError
    return deep_analysis(game_state)
```

## 錯誤處理最佳實踐

### 1. 提供清晰的錯誤信息
```python
raise InvalidInputError(
    "Invalid card representation",
    input_value=card_str,
    expected_format="[Rank][Suit] e.g., 'AS', 'KH'"
)
```

### 2. 使用錯誤詳情
```python
try:
    result = solver.solve(game_state)
except OFCError as e:
    logger.error(f"Error: {e}")
    logger.error(f"Code: {e.error_code}")
    logger.error(f"Details: {e.details}")
```

### 3. 記錄錯誤上下文
```python
try:
    game_state.place_cards(placements, discard)
except GameRuleViolationError as e:
    logger.error(f"Failed to place cards: {e}")
    logger.error(f"Current street: {game_state.current_street}")
    logger.error(f"Cards placed: {game_state.player_arrangement.cards_placed}")
    raise
```

### 4. 優雅降級
```python
try:
    # 嘗試並行處理
    result = parallel_solve(game_state, threads=8)
except ResourceError:
    logger.warning("Falling back to single-threaded mode")
    # 降級到單線程
    result = single_thread_solve(game_state)
```

## 錯誤代碼參考

| 錯誤代碼 | 描述 | 恢復建議 |
|---------|------|---------|
| INVALID_INPUT | 輸入數據無效 | 檢查並修正輸入格式 |
| TIMEOUT | 操作超時 | 增加時間限制或使用部分結果 |
| RESOURCE_ERROR | 資源不足 | 減少資源需求或升級系統 |
| RULE_VIOLATION | 違反遊戲規則 | 檢查遊戲邏輯和規則 |
| CONFIG_ERROR | 配置錯誤 | 修正配置參數 |
| STATE_ERROR | 狀態錯誤 | 確保正確的操作順序 |
| SOLVER_ERROR | 一般求解器錯誤 | 查看詳細錯誤信息 |

## 示例：完整的錯誤處理流程

```python
import logging
from src.ofc_solver import OFCSolver, SolverConfig
from src.core.domain import GameState
from src.exceptions import *

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def solve_with_full_error_handling(game_state: GameState):
    """展示完整的錯誤處理流程"""
    
    try:
        # 創建配置
        config = SolverConfig(
            time_limit=30.0,
            num_threads=4,
            return_partial_on_timeout=True,
            memory_limit_mb=500
        )
        
        # 創建求解器
        solver = OFCSolver(config)
        
        # 求解
        result = solver.solve(game_state)
        
        if result.is_complete:
            logger.info(f"Solution found: {result.best_action}")
            logger.info(f"Expected score: {result.expected_score}")
        else:
            logger.warning("Partial solution due to timeout")
            logger.info(f"Simulations completed: {result.num_simulations}")
            
        return result
        
    except InvalidInputError as e:
        logger.error(f"Invalid input: {e}")
        logger.error(f"Input value: {e.details.get('input_value')}")
        # 可能需要提示用戶修正輸入
        raise
        
    except TimeoutError as e:
        logger.warning(f"Solver timeout after {e.details['elapsed_time']:.1f}s")
        if e.partial_result:
            logger.info("Using partial result")
            return e.partial_result
        raise
        
    except ResourceError as e:
        logger.error(f"Resource shortage: {e}")
        # 嘗試降級恢復
        if e.details['resource_type'] == 'memory':
            logger.info("Retrying with reduced resources")
            config.num_threads = 1
            solver = OFCSolver(config)
            return solver.solve(game_state)
        raise
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        logger.error(f"Parameter: {e.details.get('parameter')}")
        logger.error(f"Value: {e.details.get('value')}")
        raise
        
    except GameRuleViolationError as e:
        logger.error(f"Game rule violation: {e}")
        logger.error(f"Rule: {e.details.get('rule_violated')}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        raise

# 使用示例
if __name__ == "__main__":
    game = GameState(num_players=2, player_index=0)
    
    try:
        result = solve_with_full_error_handling(game)
        print(f"Success! Best action: {result.best_action}")
    except Exception as e:
        print(f"Failed to solve: {e}")
```

## 總結

OFC Solver 的錯誤處理系統提供了：

1. **清晰的錯誤分類**：每種錯誤都有明確的類型和含義
2. **詳細的錯誤信息**：包含錯誤代碼、詳情和上下文
3. **自動恢復機制**：超時部分結果、資源降級等
4. **豐富的驗證工具**：裝飾器和驗證函數
5. **生產級的穩定性**：確保系統在各種情況下都能正常運行

通過合理使用這些錯誤處理機制，可以構建健壯、可靠的 OFC 求解應用。