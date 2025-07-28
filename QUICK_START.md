# OFC Solver 快速開始指南

## 安裝與設置

### 1. 環境要求
- Python 3.11 或更高版本
- 4GB+ RAM（建議 8GB）
- 多核心 CPU（建議 4 核心以上）

### 2. 安裝依賴
```bash
git clone git@github.com:PWChenTW/PineappleSolver.git
cd PineappleSolver
pip install -r requirements.txt
```

## 使用方式

### 方式一：Web GUI（推薦新手）

```bash
# 第一個終端：啟動 API 服務器
python run_api.py

# 第二個終端：啟動圖形界面
streamlit run gui/app_v2.py
```

然後在瀏覽器中打開 http://localhost:8501 使用點擊式界面。

### 方式二：RESTful API

```bash
# 啟動 API 服務器
python run_api.py

# 瀏覽器訪問 API 文檔
open http://localhost:8000/docs
```

### 方式三：Python API（進階用戶）

```python
from src.ofc_solver import create_solver
from src.core.domain import GameState

# 創建求解器
solver = create_solver(time_limit=30.0, num_threads=4)

# 創建遊戲狀態
game = GameState(num_players=2, player_index=0)

# 求解
result = solver.solve(game)
print(f"最佳動作: {result.move}")
print(f"期望分數: {result.evaluation}")
```

## GUI 使用指南

### 基本操作
1. **選擇輸入位置**：點擊頂部按鈕選擇要輸入的位置
2. **點擊選擇卡牌**：在卡牌網格中點擊選擇
3. **求解策略**：點擊右側的"🎯 求解最佳策略"

### 輸入範例
- 初始5張牌：選擇"📥 當前抽到的牌"，然後點擊 A♠ K♥ Q♦ J♣ T♠
- 已擺放的牌：選擇對應位置（如玩家1前墩），點擊相應卡牌

## API 使用範例

### 基本求解請求
```bash
curl -X POST http://localhost:8000/api/v1/solve \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_key" \
  -d '{
    "game_state": {
      "current_round": 1,
      "players": [
        {
          "player_id": "player1",
          "top_hand": {"cards": [], "max_size": 3},
          "middle_hand": {"cards": [], "max_size": 5},
          "bottom_hand": {"cards": [], "max_size": 5},
          "in_fantasy_land": false,
          "next_fantasy_land": false,
          "is_folded": false
        },
        {
          "player_id": "player2",
          "top_hand": {"cards": [], "max_size": 3},
          "middle_hand": {"cards": [], "max_size": 5},
          "bottom_hand": {"cards": [], "max_size": 5},
          "in_fantasy_land": false,
          "next_fantasy_land": false,
          "is_folded": false
        }
      ],
      "current_player_index": 0,
      "drawn_cards": [
        {"rank": "A", "suit": "s"},
        {"rank": "K", "suit": "h"},
        {"rank": "Q", "suit": "d"},
        {"rank": "J", "suit": "c"},
        {"rank": "T", "suit": "s"}
      ],
      "remaining_deck": []
    },
    "options": {
      "time_limit": 10.0,
      "threads": 4
    }
  }'
```

### Python 客戶端範例
```python
import requests

# 健康檢查
response = requests.get("http://localhost:8000/api/v1/health")
print(response.json())

# 求解請求
game_data = {
    "game_state": {
        # ... 遊戲狀態數據
    },
    "options": {
        "time_limit": 30.0,
        "threads": 4
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/solve",
    json=game_data,
    headers={"X-API-Key": "test_key"}
)

result = response.json()
print(f"最佳放置: {result['move']}")
```

## 配置選項

### 求解器參數
- `time_limit`: 求解時間限制（秒），建議 10-60 秒
- `threads`: 並行線程數，建議等於 CPU 核心數
- `simulations`: 最大模擬次數，建議 100,000+

### 性能建議
- **快速分析**: 10 秒，適合實時使用
- **標準分析**: 30 秒，平衡速度和精度
- **深度分析**: 60 秒，追求最高精度

## 監控系統（可選）

### 啟動監控
```bash
cd monitoring
docker-compose -f docker-compose-monitoring-only.yml up -d
```

### 訪問監控面板
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API 指標**: http://localhost:8000/metrics

## 常見問題

### Q: GUI 無法訪問？
A: 確保先運行 `python run_api.py` 啟動 API 服務器

### Q: 求解時間太長？
A: 降低時間限制或減少線程數

### Q: API 連接失敗？
A: 檢查 API 服務器是否正常運行，訪問 http://localhost:8000/api/v1/health

### Q: 卡牌格式怎麼輸入？
A: 使用 GUI 點擊選擇，或者 API 中使用 {"rank": "A", "suit": "s"} 格式

### Q: 支持多人遊戲嗎？
A: 目前支持 2 人遊戲，可以輸入對手已知的牌

## 範例輸出

### GUI 結果顯示
```
最佳放置策略:
A♠ → 後墩
K♥ → 中墩  
Q♦ → 中墩
J♣ → 中墩
T♠ → 前墩

期望分數: 15.3
置信度: 85%
計算時間: 10.2秒
```

### API 響應範例
```json
{
  "move": {
    "card_placements": [
      {
        "card": {"rank": "A", "suit": "s"},
        "hand": "bottom"
      }
    ],
    "is_fold": false
  },
  "evaluation": 15.3,
  "confidence": 0.85,
  "computation_time_seconds": 10.2
}
```

## 運行範例

```bash
# 運行 API 客戶端範例
python examples/api_quick_start.py

# 運行完整使用範例
python example_usage.py

# 運行測試
python run_tests_coverage.py
```

---

更多詳細資訊請參考：
- [GUI 使用說明書](GUI_USER_GUIDE.md)
- [API 文檔](docs/api/quickstart.md)
- [專案進度](PROJECT_PROGRESS.md)