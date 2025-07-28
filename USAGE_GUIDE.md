# OFC Solver 使用指南

## 📋 概述

PineappleSolver 是一個專為 Open Face Chinese Poker (OFC) / 大菠蘿撲克開發的 AI 求解器，提供三種使用方式：

1. **Web GUI** - 直觀的圖形界面，支持點擊式卡牌輸入
2. **RESTful API** - 完整的 FastAPI 端點，支持程式化調用
3. **Python SDK** - 直接在代碼中調用求解器功能
4. **監控系統** - Prometheus + Grafana 的完整可觀測性
5. **生產就緒** - 結構化錯誤處理、日誌記錄、性能優化

## 🎯 使用場景

### 適合的使用者
✅ **OFC 玩家** - 學習最佳策略和提升技巧
✅ **撲克教練** - 分析牌局和教學工具
✅ **遊戲開發者** - 集成 AI 求解功能到應用中
✅ **研究人員** - 分析 OFC 數學和策略
✅ **軟體開發者** - 學習 MCTS 算法實現
✅ **AI 愛好者** - 探索遊戲 AI 的應用

### 主要功能
- 初始5張牌的最佳放置策略
- 中後期牌局的最優決策分析
- 犯規風險評估和避免建議
- 期望分數計算和置信度評估
- 多線程並行計算支持
- 實時求解結果展示

## 🚀 快速開始三步驟

### Step 1: 安裝與設置
```bash
# 克隆項目
git clone git@github.com:PWChenTW/PineappleSolver.git
cd PineappleSolver

# 安裝依賴
pip install -r requirements.txt
```

### Step 2: 啟動服務
```bash
# 啟動 API 服務器（必需）
python run_api.py

# 在新終端啟動 GUI（可選）
streamlit run gui/app_v2.py
```

### Step 3: 開始使用
```bash
# 方式1: 使用 Web GUI
# 瀏覽器訪問 http://localhost:8501

# 方式2: 使用 API
# 瀏覽器訪問 http://localhost:8000/docs

# 方式3: Python 代碼調用
python examples/api_quick_start.py
```

## 📖 詳細使用說明

### 方式一：Web GUI 使用

#### 基本操作流程
1. **啟動服務**
   ```bash
   # 終端1: API 服務
   python run_api.py
   
   # 終端2: GUI 界面
   streamlit run gui/app_v2.py
   ```

2. **訪問界面**
   - 瀏覽器打開 http://localhost:8501
   - 檢查 API 連接狀態（側邊欄）

3. **輸入牌局**
   - 選擇輸入位置（當前抽到的牌、玩家1/2各墩位）
   - 點擊卡牌網格選擇卡牌
   - 灰色按鈕表示已使用的卡牌

4. **求解策略**
   - 設定求解參數（時間限制、線程數、模擬次數） 
   - 點擊"🎯 求解最佳strategy"
   - 查看結果和評估信息

#### GUI 功能特色
- **點擊式輸入**: 無需記憶卡牌格式，直接點擊選擇
- **即時反饋**: 已使用卡牌自動標記，避免重複選擇
- **視覺化結果**: 卡牌結果以圖像形式顯示
- **參數調整**: 可自訂求解時間和精度
- **狀態追蹤**: 顯示所有玩家的牌局狀態

### 方式二：RESTful API 使用

#### 基本端點
```bash
# 健康檢查
GET /api/v1/health

# 求解最佳策略  
POST /api/v1/solve

# 批量求解
POST /api/v1/solve_batch

# API 文檔
GET /docs
```

#### 求解請求範例
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
        }
      ],
      "current_player_index": 0,
      "drawn_cards": [
        {"rank": "A", "suit": "s"},
        {"rank": "K", "suit": "h"}
      ]
    },
    "options": {
      "time_limit": 10.0,
      "threads": 4
    }
  }'
```

#### Python 客戶端範例
```python
import requests

# 初始化客戶端
api_url = "http://localhost:8000"
headers = {"X-API-Key": "test_key"}

# 健康檢查
response = requests.get(f"{api_url}/api/v1/health")
print(f"API 狀態: {response.json()}")

# 求解請求
game_data = {
    "game_state": {
        "drawn_cards": [
            {"rank": "A", "suit": "s"},
            {"rank": "K", "suit": "h"}
        ]
    },
    "options": {
        "time_limit": 30.0,
        "threads": 4
    }
}

response = requests.post(
    f"{api_url}/api/v1/solve",
    json=game_data,
    headers=headers
)

result = response.json()
print(f"最佳策略: {result['move']}")
print(f"期望分數: {result['evaluation']}")
```

### 方式三：Python SDK 使用

#### 直接調用求解器
```python
from src.ofc_solver import create_solver
from src.core.domain import GameState, Card

# 創建求解器
solver = create_solver(
    time_limit=30.0,
    num_threads=4,
    simulations=100000
)

# 創建遊戲狀態
game = GameState(num_players=2, player_index=0)

# 添加抽到的牌
drawn_cards = [
    Card("A", "s"),  # A♠
    Card("K", "h"),  # K♥
    Card("Q", "d"),  # Q♦
    Card("J", "c"),  # J♣
    Card("T", "s")   # T♠
]
game.set_drawn_cards(drawn_cards)

# 求解最佳策略
result = solver.solve(game)

print(f"最佳動作: {result.move}")
print(f"期望分數: {result.evaluation}")
print(f"置信度: {result.confidence}")
print(f"計算時間: {result.computation_time}")
```

#### 高級用法
```python
# 設定對手已知牌
game.players[1].add_card_to_hand("bottom", Card("9", "h"))
game.players[1].add_card_to_hand("middle", Card("8", "d"))

# 分析特定手牌組合
from src.core.hand_evaluator import HandEvaluator

evaluator = HandEvaluator()
hand_cards = [Card("A", "s"), Card("A", "h"), Card("K", "s")]
strength = evaluator.evaluate_hand(hand_cards)
print(f"手牌強度: {strength}")

# 批量分析多個方案
scenarios = [
    {"cards": [Card("A", "s")], "position": "bottom"},
    {"cards": [Card("A", "s")], "position": "middle"},
    {"cards": [Card("A", "s")], "position": "top"}
]

for scenario in scenarios:
    test_game = game.copy()
    # 設定測試方案並求解
    result = solver.solve(test_game)
    print(f"方案 {scenario}: 分數 {result.evaluation}")
```

## 🔧 高級配置

### 性能調整
```python
# 快速分析（10秒內）
solver_fast = create_solver(
    time_limit=10.0,
    num_threads=4,
    simulations=50000
)

# 標準分析（平衡速度與精度）
solver_standard = create_solver(
    time_limit=30.0,
    num_threads=4,
    simulations=100000
)

# 深度分析（最高精度）
solver_deep = create_solver(
    time_limit=60.0,
    num_threads=8,
    simulations=500000
)
```

### 監控系統設置
```bash
# 啟動完整監控（需要 Docker）
cd monitoring
docker-compose -f docker-compose-monitoring-only.yml up -d

# 訪問監控面板
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### 日誌配置
```python
import logging
from src.logging_config import setup_logging

# 設置日誌級別
setup_logging(level=logging.INFO)

# 自定義日誌格式
setup_logging(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## 📊 結果分析與解釋

### GUI 結果理解
- **最佳放置策略**: 每張牌的推薦位置
- **期望分數**: 預期的總得分
- **置信度**: 結果的可信程度（85%+ 為高置信度）
- **計算時間**: 實際求解耗時
- **模擬次數**: 完成的 MCTS 模擬數量

### API 響應格式
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
  "computation_time_seconds": 10.2,
  "simulations": 65432,
  "expected_score": 15.3
}
```

### 策略建議解讀
- **期望分數 > 0**: 總體有利，建議繼續遊戲
- **期望分數 < -10**: 劣勢明顯，考慮保守策略
- **置信度 < 60%**: 不確定性高，需要更長計算時間
- **is_fold = true**: 建議棄牌（極劣勢情況）

## 🛠️ 故障排除

### 常見問題

#### 1. API 服務無法啟動
```bash
# 檢查端口是否被占用
lsof -i :8000

# 使用不同端口
python run_api.py --host 0.0.0.0 --port 8001
```

#### 2. GUI 無法連接 API
```bash
# 確保 API 服務正在運行
curl http://localhost:8000/api/v1/health

# 檢查防火牆設置
# 確認 8000 和 8501 端口開放
```

#### 3. 求解速度太慢
```python
# 降低模擬次數
solver = create_solver(simulations=10000)

# 減少線程數（避免過度競爭）
solver = create_solver(num_threads=2)

# 設置更短的時間限制
solver = create_solver(time_limit=5.0)
```

#### 4. 記憶體使用過高
```python
# 使用較小的搜索樹
solver = create_solver(
    max_tree_nodes=50000,
    memory_limit_mb=1024
)
```

### 調試技巧
```bash
# 啟用詳細日誌
export OFC_LOG_LEVEL=DEBUG
python run_api.py

# 查看性能統計
python -m cProfile -o profile.stats run_api.py

# 監控記憶體使用
python -m memory_profiler examples/api_quick_start.py
```

## 📚 最佳實踐

### 求解器使用
1. **合理設置時間限制**: 初學者 10-30 秒，高手 30-60 秒
2. **根據硬體調整線程**: 通常等於 CPU 核心數
3. **分階段求解**: 複雜局面可分步驟分析
4. **結合人類直覺**: AI 建議需要結合實戰經驗

### 性能優化
1. **預熱求解器**: 首次使用前進行一次求解預熱
2. **批量處理**: 多個局面使用 batch API
3. **結果緩存**: 相似局面可重複使用結果
4. **監控資源**: 使用監控系統追蹤性能

### 學習建議
1. **從簡單開始**: 先分析初始 5 張牌的放置
2. **對比結果**: 將 AI 建議與個人直覺對比
3. **理解原理**: 學習 OFC 基本策略和數學原理
4. **實戰驗證**: 在實際遊戲中驗證 AI 建議的效果

---

## 🎯 總結

PineappleSolver 為 OFC 玩家提供了專業級的 AI 分析工具，無論是學習提升、教學分析還是軟體集成，都能滿足不同層次的需求。通過 Web GUI、RESTful API 和 Python SDK 三種使用方式，讓每個用戶都能找到最適合的使用方法。

詳細文檔請參考：
- [GUI 使用手冊](GUI_USER_GUIDE.md)
- [API 快速指南](QUICK_START.md)
- [專案技術文檔](docs/)
- [遊戲規則說明](OFC_GAME_RULES.md)