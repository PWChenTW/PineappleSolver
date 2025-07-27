# PineappleSolver - OFC AI 求解器

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

專為 Open Face Chinese Poker (OFC) / 大菠蘿撲克開發的 AI 求解器，使用 Monte Carlo Tree Search (MCTS) 算法實現。

## 🎯 專案特色

- **高性能**: 6500+ 模擬/秒，5分鐘內完成求解
- **智能算法**: MCTS with UCB selection + 領域特定優化
- **並行計算**: 多線程支持，充分利用多核心 CPU
- **完整分析**: 期望值計算、犯規風險評估、獎勵分預測
- **易於使用**: 簡潔的 Python API

## 🚀 快速開始

### 安裝
```bash
git clone git@github.com:PWChenTW/PineappleSolver.git
cd PineappleSolver
pip install numpy  # 唯一依賴
```

### 基本使用
```python
from src.ofc_solver import create_solver
from src.core.domain import GameState

# 創建求解器
solver = create_solver(time_limit=30.0, num_threads=4)

# 求解完整遊戲
game = GameState(num_players=2, player_index=0)
results = solver.solve_game(game)
```

### 運行範例
```bash
# 完整使用範例
python example_usage.py

# 快速測試
python test_solver.py
```

## 📖 詳細文檔

- [快速開始指南](QUICK_START.md)
- [專案進度追蹤](PROJECT_PROGRESS.md)
- [執行計劃](EXECUTION_PLAN.md)
- [OFC 遊戲規則](OFC_GAME_RULES.md)

## 🏗️ 專案結構

```
PineappleSolver/
├── src/
│   ├── core/
│   │   ├── domain/          # 領域模型（Card, Hand, GameState）
│   │   └── algorithms/      # 核心算法（MCTS, 評估器）
│   └── ofc_solver.py       # 主要 API 介面
├── tests/                  # 測試套件
├── docs/                   # 技術文檔
└── .kiro/specs/           # 規格文檔（SDD/BDD/DDD）
```

## 🔧 核心組件

### 遊戲引擎
- 完整的 OFC 規則實現
- 牌型識別和比較
- 犯規檢測和計分系統

### MCTS 搜索
- 優化的搜索樹管理
- 漸進式展開（Progressive Widening）
- 虛擬損失（Virtual Loss）並行化

### 評估系統
- 手牌強度評估
- 獎勵分潛力計算
- 犯規風險分析

## 📊 性能指標

- 單次牌型評估: < 1μs
- MCTS 模擬速度: 6500+ sims/秒
- 初始擺放求解: ~10 秒（65,000+ 模擬）
- 完整遊戲求解: < 5 分鐘

## 🛠️ 開發狀態

- ✅ 核心功能完成（60%）
- ✅ 基礎遊戲引擎
- ✅ MCTS 搜索算法
- ✅ 性能優化
- 🔄 測試覆蓋（進行中）
- ⏳ API 開發（計劃中）
- ⏳ Docker 部署（計劃中）

## 🤝 貢獻指南

歡迎貢獻！請查看 [EXECUTION_PLAN.md](EXECUTION_PLAN.md) 了解當前的開發計劃。

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