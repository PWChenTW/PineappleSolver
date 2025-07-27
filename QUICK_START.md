# OFC Solver 快速開始指南

## 安裝與設置

### 1. 環境要求
- Python 3.11 或更高版本
- 4GB+ RAM（建議 8GB）
- 多核心 CPU（建議 4 核心以上）

### 2. 安裝依賴
```bash
pip install numpy
```

## 基本使用

### 最簡單的例子
```python
from src.core.domain import GameState
from src.ofc_solver import create_solver

# 創建 solver
solver = create_solver()

# 解決一手牌
game = GameState(num_players=2, player_index=0)
results = solver.solve_game(game)
```

### 運行範例
```bash
# 運行完整範例
python example_usage.py

# 運行測試
python test_solver.py
```

## 主要功能

### 1. 解決初始 5 張牌
```python
# 創建遊戲
game = GameState()
cards = game.deal_street()  # 發 5 張牌

# 求解最佳擺放
result = solver.solve(game)

# 查看結果
for card, position, index in result.best_action.placements:
    print(f"{card} 放到 {position} 第 {index} 位")
```

### 2. 解決中局位置
```python
# 設置已有的牌
game.player_arrangement.place_card(Card.from_string("Kh"), 'front', 0)
game.player_arrangement.place_card(Card.from_string("Kd"), 'front', 1)
# ... 更多牌

# 發下一輪牌
game.deal_street()

# 求解
result = solver.solve(game)
```

### 3. 分析局面
```python
# 快速分析當前局面
analysis = solver.analyze_position(game)

print(f"犯規風險: {analysis['foul_risk']:.1%}")
print(f"期望得分: {analysis['expected_score']:.2f}")
```

## 配置選項

### Solver 配置
```python
solver = create_solver(
    time_limit=300.0,      # 時間限制（秒），默認 5 分鐘
    num_threads=4,         # 線程數，默認 4
    use_action_generator=True  # 使用智能動作生成，默認開啟
)
```

### 性能建議
- **快速分析**: `time_limit=10.0`（10 秒）
- **標準分析**: `time_limit=30.0`（30 秒）
- **深度分析**: `time_limit=300.0`（5 分鐘）

## 進階用法

### 1. 自定義進度回調
```python
def progress_callback(simulations, elapsed_time, status):
    print(f"進度: {simulations} 次模擬, {elapsed_time:.1f} 秒")

result = solver.solve(game, progress_callback)
```

### 2. 批量分析
```python
# 分析多個不同的起手牌
for seed in range(10):
    game = GameState(seed=seed)
    game.deal_street()
    result = solver.solve(game)
    print(f"Seed {seed}: 期望得分 {result.expected_score:.2f}")
```

### 3. 保存和載入狀態
```python
# 保存當前狀態（需自行實現序列化）
state_data = {
    'front': [(c.value, i) for i, c in enumerate(game.player_arrangement.front_cards) if c],
    'middle': [(c.value, i) for i, c in enumerate(game.player_arrangement.middle_cards) if c],
    'back': [(c.value, i) for i, c in enumerate(game.player_arrangement.back_cards) if c],
}

# 載入狀態
new_game = GameState()
for card_value, index in state_data['front']:
    new_game.player_arrangement.place_card(Card(card_value), 'front', index)
# ... 其他位置
```

## 常見問題

### Q: 求解時間太長？
A: 減少 `time_limit` 或使用更少的 `num_threads`（如果 CPU 較弱）

### Q: 如何提高精確度？
A: 增加 `time_limit`，讓 solver 有更多時間搜索

### Q: 支持夢幻樂園嗎？
A: 基礎引擎支持檢測夢幻樂園資格，但目前不支持夢幻樂園模式的求解

### Q: 可以分析對手的牌嗎？
A: 目前是單人最優化，只考慮對手用過的牌，不分析對手的具體擺放

## 輸出解釋

### SolveResult 包含：
- `best_action`: 最佳動作（放置哪些牌、棄哪張）
- `expected_score`: 預期得分（對戰平均對手）
- `num_simulations`: 運行的模擬次數
- `time_taken`: 花費時間
- `top_actions`: 前幾名的動作選項

### 分析結果包含：
- `foul_risk`: 犯規風險（0-100%）
- `expected_score`: 當前局面的期望得分
- `royalties`: 已獲得的獎勵分

## 範例輸出

```
Initial cards: As Ah Kd Kc Qs

Optimal placement:
  As → front[0]
  Ah → front[1]
  Kd → middle[0]
  Kc → middle[1]
  Qs → back[0]

Expected score: 15.3
Simulations run: 45,231
Time taken: 28.5 seconds
```

---

開始使用：
```bash
python example_usage.py
```

有問題請參考完整文檔或查看源代碼！