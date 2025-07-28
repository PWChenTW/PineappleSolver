# OFC Solver API 使用場景分析

## 概述

本文檔詳細描述 OFC Solver API 的各種使用場景，幫助不同類型的用戶理解如何最有效地使用 API。

## 核心用戶群體

### 1. 專業玩家
- **需求**：深度分析，最優策略，長期統計
- **特點**：願意等待較長計算時間，需要詳細數據

### 2. 休閒玩家
- **需求**：快速建議，易於理解，即時反饋
- **特點**：對速度敏感，需要簡單明瞭的建議

### 3. 開發者
- **需求**：穩定可靠，易於集成，良好文檔
- **特點**：需要批量處理，錯誤處理，性能監控

### 4. 研究人員
- **需求**：大量數據分析，算法驗證，統計研究
- **特點**：批量處理，歷史數據，詳細統計

## 詳細使用場景

### 場景 1：實時對戰決策支持

**用戶故事**
```
作為一名正在進行線上對戰的玩家
我希望在 5 秒內獲得當前位置的最佳打法建議
以便在時間限制內做出正確決策
```

**API 使用方式**
```python
# 使用快速分析端點
response = client.analyze(
    game_state=current_position,
    depth=2,  # 較淺的搜索深度以保證速度
    include_alternatives=True
)

# 獲取前三個建議
for rec in response['recommendations'][:3]:
    print(f"{rec['move']} - {rec['reasoning']}")
```

**關鍵需求**
- 響應時間 < 5 秒
- 清晰的打法理由說明
- 至少 3 個備選方案

### 場景 2：賽後復盤分析

**用戶故事**
```
作為一名想要提升水平的玩家
我希望對完成的牌局進行深度分析
以便了解每個決策點的最優選擇並學習改進
```

**API 使用方式**
```python
# 批量提交所有決策點
positions = []
for decision_point in game_history:
    positions.append({
        "id": f"round_{decision_point['round']}",
        "game_state": decision_point['state'],
        "options": {
            "time_limit": 60,  # 允許更長時間深度分析
            "threads": 8
        }
    })

# 提交批量分析
batch_job = client.batch_solve(
    positions=positions,
    priority="normal"
)

# 等待完成並分析結果
results = client.wait_for_batch_completion(batch_job['job_id'])
analyze_game_decisions(results)
```

**關鍵需求**
- 支持批量處理多個位置
- 深度分析每個決策點
- 能夠對比實際打法與最優打法

### 場景 3：AI 訓練數據生成

**用戶故事**
```
作為一名 AI 研究者
我需要大量高質量的 OFC 對局數據
以便訓練和改進我的 AI 模型
```

**API 使用方式**
```python
# 生成隨機遊戲狀態並求解
training_data = []

for _ in range(1000):
    game_state = generate_random_position()
    
    # 異步求解以提高效率
    result = client.solve(
        game_state=game_state,
        time_limit=30,
        async_mode=True
    )
    
    training_data.append({
        'task_id': result['task_id'],
        'game_state': game_state
    })

# 批量收集結果
for data in training_data:
    result = client.wait_for_task(data['task_id'])
    save_training_example(data['game_state'], result)
```

**關鍵需求**
- 高吞吐量處理能力
- 異步處理支持
- 詳細的統計信息

### 場景 4：即時戰術建議

**用戶故事**
```
作為一名教練或顧問
我需要為學員提供即時的戰術建議
並解釋每個建議背後的邏輯
```

**API 使用方式**
```python
# 獲取詳細分析
analysis = client.analyze(
    game_state=current_position,
    depth=3,
    include_alternatives=True
)

# 生成教學建議
teaching_points = []

# 分析手牌強度
for hand, strength in analysis['hand_strengths'].items():
    if strength['current_strength'] < 0.3:
        teaching_points.append(
            f"{hand} 手牌較弱 ({strength['current_rank']})，"
            f"需要改進機會：{strength['potential_improvements']}"
        )

# 風險評估
if analysis['foul_probability'] > 0.2:
    teaching_points.append(
        f"注意！犯規風險較高 ({analysis['foul_probability']:.1%})，"
        "建議保守打法"
    )

# Just miss Fantasy Land 機會
if 0.3 < analysis['fantasy_land_probability'] < 0.7:
    teaching_points.append(
        f"有 {analysis['fantasy_land_probability']:.1%} 機會進入幻想世界，"
        "值得冒險嘗試"
    )
```

**關鍵需求**
- 詳細的位置評估
- 風險和機會分析
- 易於理解的建議理由

### 場景 5：錦標賽準備

**用戶故事**
```
作為準備參加錦標賽的選手
我需要針對特定對手風格準備策略
並練習各種可能遇到的局面
```

**API 使用方式**
```python
# 分析對手常見開局
opponent_patterns = load_opponent_openings()

for pattern in opponent_patterns:
    # 設置對手的典型位置
    game_state = create_game_state_from_pattern(pattern)
    
    # 深度分析最佳應對
    result = client.solve(
        game_state=game_state,
        time_limit=120,  # 充分時間找到最優解
        threads=16,      # 使用更多資源
        use_neural_network=True  # 啟用神經網絡評估
    )
    
    # 保存針對性策略
    save_counter_strategy(pattern, result)
```

**關鍵需求**
- 超深度分析能力
- 支持特定局面研究
- 高質量解決方案

### 場景 6：直播解說輔助

**用戶故事**
```
作為 OFC 比賽的直播解說員
我需要快速獲得當前局面的評估
以便為觀眾提供專業的解說
```

**API 使用方式**
```python
# 實時監控比賽進程
def on_game_update(game_state):
    # 快速評估當前局面
    analysis = client.analyze(
        game_state=game_state,
        depth=2,  # 快速分析
        include_alternatives=True
    )
    
    # 生成解說要點
    commentary = {
        'evaluation': f"當前局面評分：{analysis['evaluation']:.2f}",
        'leader': "玩家1領先" if analysis['evaluation'] > 0 else "玩家2領先",
        'key_decisions': []
    }
    
    # 添加關鍵決策點
    for rec in analysis['recommendations'][:2]:
        commentary['key_decisions'].append({
            'move': format_move_for_viewers(rec['move']),
            'explanation': rec['reasoning']
        })
    
    return commentary
```

**關鍵需求**
- 極快的響應速度（< 2秒）
- 易於解釋的評估結果
- 觀眾友好的輸出格式

## API 使用最佳實踐

### 1. 選擇合適的端點

| 場景類型 | 推薦端點 | 時間預算 | 深度要求 |
|---------|---------|---------|---------|
| 實時決策 | /analyze | < 5s | 低 |
| 深度分析 | /solve | 30-120s | 高 |
| 批量研究 | /batch | 不限 | 高 |
| 快速驗證 | /analyze | < 2s | 低 |

### 2. 優化請求參數

```python
# 實時場景
quick_options = {
    "time_limit": 5,
    "threads": 4,
    "max_iterations": 10000
}

# 深度分析
deep_options = {
    "time_limit": 60,
    "threads": 8,
    "max_iterations": 100000,
    "use_neural_network": True
}

# 批量處理
batch_options = {
    "priority": "low",  # 不急需結果
    "notification_webhook": "https://myapp.com/webhook"
}
```

### 3. 錯誤處理策略

```python
def safe_api_call(func, *args, **kwargs):
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except RateLimitError:
            # 等待並重試
            time.sleep(retry_delay * (2 ** attempt))
        except ValidationError as e:
            # 記錄並修正輸入
            log_validation_error(e)
            kwargs = fix_validation_issues(kwargs, e)
        except NetworkError:
            # 切換到備用端點
            client.switch_to_backup_endpoint()
    
    raise MaxRetriesExceeded()
```

## 性能優化建議

### 1. 批量處理優化
- 將相似複雜度的請求分組
- 使用優先級隊列管理緊急請求
- 實施請求去重機制

### 2. 緩存策略
- 緩存常見開局位置的分析結果
- 實施 LRU 緩存管理相似位置
- 使用 ETW 標籤驗證緩存有效性

### 3. 並發控制
- 限制同時進行的異步請求數
- 實施請求隊列避免超載
- 監控 API 配額使用情況

## 總結

OFC Solver API 的設計充分考慮了各種使用場景，從快速實時建議到深度批量分析。通過選擇合適的端點和參數配置，不同類型的用戶都能獲得滿意的體驗。關鍵是理解自己的需求，選擇正確的使用模式，並實施適當的優化策略。