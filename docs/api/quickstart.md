# OFC Solver API 快速入門指南

## 歡迎使用 OFC Solver API

OFC Solver API 是一個強大的大菠蘿撲克求解服務，幫助您找到最優打法策略。本指南將帶您快速上手。

## 第一步：獲取 API 密鑰

在開始之前，您需要一個 API 密鑰：

1. 訪問 [OFC Solver 開發者平台](https://ofcsolver.com/developers)
2. 註冊開發者賬號
3. 創建新應用並獲取 API 密鑰
4. 保存好您的密鑰，後續所有請求都需要使用

## 第二步：選擇使用方式

### 方式 1：使用官方 Python 客戶端（推薦）

```bash
# 安裝客戶端
pip install ofc-solver-client
```

```python
from ofc_solver import OFCSolverClient

# 初始化客戶端
client = OFCSolverClient(
    api_key="your-api-key-here"
)

# 測試連接
health = client.health_check()
print(f"API 狀態: {health['status']}")
```

### 方式 2：直接使用 HTTP 請求

```bash
# 使用 curl 測試
curl -X GET https://api.ofcsolver.com/api/v1/health \
  -H "X-API-Key: your-api-key-here"
```

## 第三步：理解遊戲狀態格式

OFC Solver API 使用結構化的 JSON 格式表示遊戲狀態：

```python
# 最小化的遊戲狀態示例
game_state = {
    "current_round": 1,  # 當前回合 (1-17)
    "current_player_index": 0,  # 當前玩家索引
    "players": [
        {
            "player_id": "player1",
            "top_hand": {
                "cards": [],  # 上路手牌
                "max_size": 3
            },
            "middle_hand": {
                "cards": [],  # 中路手牌
                "max_size": 5
            },
            "bottom_hand": {
                "cards": [],  # 下路手牌
                "max_size": 5
            },
            "in_fantasy_land": False
        }
    ],
    "remaining_deck": [
        {"rank": "A", "suit": "s"},
        {"rank": "K", "suit": "h"},
        # ... 其他剩餘牌
    ]
}
```

### 牌面表示法

- **花色**：`s` (黑桃), `h` (紅心), `d` (方塊), `c` (梅花)
- **點數**：`2-9`, `T` (10), `J`, `Q`, `K`, `A`

## 第四步：您的第一個 API 調用

### 快速分析當前局面

```python
# 準備一個簡單的遊戲狀態
game_state = {
    "current_round": 5,
    "current_player_index": 0,
    "players": [
        {
            "player_id": "me",
            "top_hand": {
                "cards": [
                    {"rank": "K", "suit": "h"},
                    {"rank": "K", "suit": "d"}
                ],
                "max_size": 3
            },
            "middle_hand": {
                "cards": [
                    {"rank": "9", "suit": "s"},
                    {"rank": "9", "suit": "c"}
                ],
                "max_size": 5
            },
            "bottom_hand": {
                "cards": [
                    {"rank": "A", "suit": "s"},
                    {"rank": "A", "suit": "c"}
                ],
                "max_size": 5
            },
            "in_fantasy_land": False
        }
    ],
    "remaining_deck": [
        {"rank": "Q", "suit": "s"},
        {"rank": "J", "suit": "h"},
        {"rank": "T", "suit": "d"}
    ]
}

# 分析局面
analysis = client.analyze(game_state)

# 查看結果
print(f"局面評分: {analysis['evaluation']}")
print(f"進入幻想世界概率: {analysis['fantasy_land_probability']:.1%}")
print("\n建議打法:")
for rec in analysis['recommendations']:
    print(f"- {rec['reasoning']}")
```

### 深度求解最佳策略

```python
# 使用更多計算時間找到最優解
result = client.solve(
    game_state=game_state,
    time_limit=30,  # 30秒計算時間
    threads=4       # 使用4個線程
)

# 顯示最佳打法
print("最佳打法:")
for placement in result['best_move']['card_placements']:
    card = placement['card']
    hand = placement['hand']
    print(f"  {card['rank']}{card['suit']} → {hand}")

print(f"\n評估分數: {result['evaluation']}")
print(f"置信度: {result['confidence']:.1%}")
```

## 第五步：處理常見場景

### 場景 1：開局擺牌

```python
# 第一回合，5張牌
initial_cards = [
    {"rank": "A", "suit": "s"},
    {"rank": "A", "suit": "h"},
    {"rank": "K", "suit": "s"},
    {"rank": "Q", "suit": "s"},
    {"rank": "J", "suit": "s"}
]

# 創建開局狀態
opening_state = {
    "current_round": 1,
    "current_player_index": 0,
    "players": [{
        "player_id": "me",
        "top_hand": {"cards": [], "max_size": 3},
        "middle_hand": {"cards": [], "max_size": 5},
        "bottom_hand": {"cards": [], "max_size": 5},
        "in_fantasy_land": False
    }],
    "remaining_deck": initial_cards
}

# 求解開局
result = client.solve(opening_state, time_limit=60)
print("建議的開局擺法:")
for p in result['best_move']['card_placements']:
    print(f"{p['card']['rank']}{p['card']['suit']} → {p['hand']}")
```

### 場景 2：關鍵決策點

```python
# 檢查是否應該冒險進入幻想世界
def should_risk_fantasy_land(game_state):
    analysis = client.analyze(game_state)
    
    fl_prob = analysis['fantasy_land_probability']
    foul_prob = analysis['foul_probability']
    
    if fl_prob > 0.6 and foul_prob < 0.2:
        return "強烈建議嘗試進入幻想世界"
    elif fl_prob > 0.4 and foul_prob < 0.3:
        return "可以考慮冒險"
    else:
        return "建議穩健打法"
```

### 場景 3：批量分析多個選項

```python
# 比較不同打法
def compare_moves(game_state, possible_moves):
    results = []
    
    for move in possible_moves:
        # 應用移動到遊戲狀態
        new_state = apply_move(game_state, move)
        
        # 快速評估
        analysis = client.analyze(new_state, depth=2)
        
        results.append({
            'move': move,
            'evaluation': analysis['evaluation'],
            'risk': analysis['foul_probability']
        })
    
    # 排序並返回最佳選項
    return sorted(results, key=lambda x: x['evaluation'], reverse=True)
```

## 錯誤處理

### 常見錯誤及解決方案

```python
try:
    result = client.solve(game_state)
except ValidationError as e:
    print(f"輸入驗證失敗: {e.message}")
    # 檢查遊戲狀態格式
    
except RateLimitError as e:
    print(f"請求過於頻繁，請等待 {e.retry_after} 秒")
    # 實施退避策略
    
except TimeoutError:
    print("計算超時，嘗試減少計算時間或使用異步模式")
    # 使用異步模式處理長時間計算
```

### 異步模式處理

```python
# 對於需要長時間計算的複雜局面
async_result = client.solve(
    game_state=complex_state,
    time_limit=300,  # 5分鐘
    async_mode=True
)

task_id = async_result['task_id']
print(f"任務已提交，ID: {task_id}")

# 輪詢檢查結果
import time
while True:
    status = client.get_task_status(task_id)
    if status['status'] == 'completed':
        result = status['result']
        break
    elif status['status'] == 'failed':
        print(f"任務失敗: {status['error']}")
        break
    else:
        print(f"進度: {status.get('progress', 0)}%")
        time.sleep(5)
```

## 性能優化技巧

### 1. 使用適當的時間限制

```python
# 根據場景選擇時間限制
TIME_LIMITS = {
    'realtime': 5,      # 實時對戰
    'normal': 30,       # 標準分析
    'deep': 120,        # 深度分析
    'research': 300     # 研究模式
}
```

### 2. 緩存常見位置

```python
# 實施簡單緩存
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_analysis(game_state_hash):
    return client.analyze(game_state)
```

### 3. 批量處理

```python
# 同時分析多個位置
positions = [state1, state2, state3]
batch_job = client.batch_solve(
    positions=[
        {"id": f"pos_{i}", "game_state": state}
        for i, state in enumerate(positions)
    ]
)

# 等待所有結果
results = client.wait_for_batch(batch_job['job_id'])
```

## 下一步

恭喜！您已經掌握了 OFC Solver API 的基本使用方法。接下來您可以：

1. **深入學習**：閱讀[完整 API 文檔](./api_reference.md)
2. **探索場景**：查看[使用場景指南](./usage_scenarios.md)
3. **優化集成**：學習[最佳實踐](./best_practices.md)
4. **獲取支持**：加入[開發者社區](https://ofcsolver.com/community)

## 需要幫助？

- 📧 技術支持：support@ofcsolver.com
- 💬 Discord 社區：[加入我們](https://discord.gg/ofcsolver)
- 📚 文檔中心：[docs.ofcsolver.com](https://docs.ofcsolver.com)

祝您使用愉快！🎯