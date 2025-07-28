# PineappleSolver - OFC AI 求解器

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![API](https://img.shields.io/badge/API-FastAPI-009688.svg)](http://localhost:8000/docs)
[![GUI](https://img.shields.io/badge/GUI-Streamlit-FF6B6B.svg)](http://localhost:8501)

專為 Open Face Chinese Poker (OFC) / 大菠蘿撲克開發的 AI 求解器，使用 Monte Carlo Tree Search (MCTS) 算法實現。

## 🎯 專案特色

- **高性能**: 6500+ 模擬/秒，5分鐘內完成求解
- **智能算法**: MCTS with UCB selection + 領域特定優化
- **並行計算**: 多線程支持，充分利用多核心 CPU
- **完整分析**: 期望值計算、犯規風險評估、獎勵分預測
- **RESTful API**: 完整的 FastAPI 端點支持
- **圖形界面**: 直觀的 Web GUI，支持點擊式輸入
- **生產就緒**: 錯誤處理、日誌記錄、監控系統完整

## 🚀 快速開始

### 安裝
```bash
git clone git@github.com:PWChenTW/PineappleSolver.git
cd PineappleSolver
pip install -r requirements.txt
```

### 使用方式

#### 1. Web GUI（推薦）
```bash
# 啟動 API 服務器
python run_api.py

# 啟動圖形界面
streamlit run gui/app_v2.py
```

#### 2. RESTful API
```bash
# 啟動 API 服務器
python run_api.py

# 訪問 API 文檔
open http://localhost:8000/docs
```

#### 3. Python API
```python
from src.ofc_solver import create_solver
from src.core.domain import GameState

# 創建求解器
solver = create_solver(time_limit=30.0, num_threads=4)

# 求解遊戲
game = GameState(num_players=2, player_index=0)
result = solver.solve(game)
```

### 運行範例
```bash
# GUI 使用範例
python examples/api_quick_start.py

# 完整使用範例
python example_usage.py
```

## 📖 詳細文檔

### 使用指南
- [GUI 使用說明書](GUI_USER_GUIDE.md)
- [API 快速指南](docs/api/quickstart.md)
- [監控系統指南](docs/monitoring_guide.md)
- [錯誤處理指南](docs/error_handling_guide.md)

### 專案文檔
- [專案進度追蹤](PROJECT_PROGRESS.md)
- [開發總結](DEVELOPMENT_SUMMARY.md)
- [OFC 遊戲規則](OFC_GAME_RULES.md)
- [測試文檔](tests/README.md)

## 🏗️ 專案結構

```
PineappleSolver/
├── src/
│   ├── api/                # FastAPI 端點和中間件
│   ├── core/
│   │   ├── domain/         # 領域模型（Card, Hand, GameState）
│   │   └── algorithms/     # 核心算法（MCTS, 評估器）
│   ├── ofc_solver.py      # 主要求解器介面
│   ├── exceptions.py      # 自定義異常類
│   ├── validation.py      # 輸入驗證
│   └── logging_config.py  # 日誌配置
├── gui/                   # Streamlit Web GUI
├── tests/                 # 測試套件
├── docs/                  # 技術文檔
├── monitoring/            # Prometheus + Grafana 監控
└── examples/              # 使用範例
```

## 🔧 核心組件

### 遊戲引擎
- 完整的 OFC 規則實現
- 牌型識別和比較
- 犯規檢測和計分系統
- 智能初始擺放策略

### MCTS 搜索
- 優化的搜索樹管理
- 漸進式展開（Progressive Widening）
- 虛擬損失（Virtual Loss）並行化
- 期望分數和最佳動作統計

### RESTful API
- FastAPI 框架實現
- 同步/異步求解端點
- 批量處理支持
- 自動 API 文檔生成

### Web GUI
- Streamlit 圖形界面
- 點擊式卡牌輸入
- 實時結果顯示
- 多種使用場景支持

### 監控系統
- Prometheus 指標收集
- Grafana 儀表板
- Docker Compose 部署
- 完整的告警規則

## 📊 性能指標

- 單次牌型評估: < 1μs
- MCTS 模擬速度: 6500+ sims/秒
- 初始擺放求解: ~10 秒（65,000+ 模擬）
- 完整遊戲求解: < 5 分鐘

## 🛠️ 開發狀態

**專案完成度：75%**

- ✅ 核心功能完成（100%）
- ✅ MCTS 搜索算法（85%）
- ✅ RESTful API（100%）
- ✅ Web GUI（100%）
- ✅ 錯誤處理系統（100%）
- ✅ 日誌系統（100%）
- ✅ 監控系統（100%）
- 🔄 測試覆蓋（60%）
- 🔄 性能優化（70%）
- ⏳ 生產部署（計劃中）

## 🤝 貢獻指南

歡迎貢獻！請查看 [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) 了解當前的開發狀態。

### 開發流程
1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📝 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件

## 🙏 致謝

- 使用 Claude AI 協助開發
- 參考了德州撲克 solver 的設計理念
- 感謝 OFC 社群的規則說明

---

**作者**: PWChenTW  
**聯絡方式**: [GitHub](https://github.com/PWChenTW)

🤖 *Built with AI assistance from Claude*