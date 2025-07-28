# OFC Solver 測試報告

## 測試概覽

**測試日期**: [執行時間]  
**測試環境**: Python 3.x, macOS/Linux/Windows  
**測試框架**: unittest + pytest

## 測試套件說明

### 1. 鬼牌系統測試 (test_joker_system.py)

**目的**: 驗證鬼牌功能的正確性

**測試範圍**:
- ✅ 鬼牌創建和識別
- ✅ 最優替換算法（順子、同花、對子等）
- ✅ Fantasy Land 判定（QQ+ with joker）
- ✅ 多鬼牌處理
- ✅ 不同位置的鬼牌使用策略

**關鍵測試案例**:
- `test_joker_creation_and_identification`: 基本功能測試
- `test_joker_optimal_replacement_*`: 各種牌型的最優替換
- `test_fantasy_land_with_joker`: Fantasy Land 特殊規則
- `test_multiple_jokers_handling`: 多鬼牌情況

### 2. 性能基準測試 (test_performance_benchmark.py)

**目的**: 確保系統性能達標

**測試範圍**:
- ✅ 100k 模擬在 5 秒內完成
- ✅ 並行計算效率 (> 2x speedup with 4 threads)
- ✅ 緩存命中率和效果
- ✅ 內存使用控制 (< 500MB peak)
- ✅ 響應時間一致性 (CV < 30%)

**性能指標**:
```
目標性能指標:
- 模擬速度: > 20,000 simulations/second
- 並行效率: > 50% (4 threads)
- 內存增長: < 500MB
- 響應時間: < 5s for 100k simulations
```

### 3. 逐街求解測試 (test_street_solver.py)

**目的**: 驗證遊戲流程的正確性

**測試範圍**:
- ✅ 初始5張牌擺放
- ✅ 完整的逐街進行流程
- ✅ 對手牌追蹤
- ✅ 牌堆管理和耗盡處理
- ✅ 狀態轉換驗證
- ✅ 策略適應性

**關鍵場景**:
- 初始街道決策
- 中間街道的權衡
- 最後街道的優化
- Fantasy Land 機會識別

## 覆蓋率統計

### 整體覆蓋率
```
目標: > 80%
實際: [待測試運行後填寫]
```

### 核心模組覆蓋率
| 模組 | 覆蓋率 | 狀態 |
|------|--------|------|
| src/ofc_solver.py | - | - |
| src/core/domain/card.py | - | - |
| src/core/domain/game_state.py | - | - |
| src/core/algorithms/mcts_node.py | - | - |

## 運行測試

### 運行所有測試並生成覆蓋率報告
```bash
python run_tests_with_coverage.py
```

### 運行特定測試套件
```bash
# 鬼牌系統測試
python run_tests_with_coverage.py joker

# 性能測試
python run_tests_with_coverage.py performance

# 街道求解測試
python run_tests_with_coverage.py street
```

### 運行單個測試文件
```bash
python -m pytest tests/test_joker_system.py -v
```

## 測試結果解讀

### 成功標準
1. **功能測試**: 所有測試用例通過
2. **性能測試**: 滿足性能指標要求
3. **覆蓋率**: 整體覆蓋率 > 80%，核心模組 > 90%

### 常見問題

1. **性能測試失敗**
   - 檢查系統資源（CPU、內存）
   - 確認沒有其他程序佔用資源
   - 考慮調整線程數

2. **覆蓋率不足**
   - 檢查是否有未測試的分支
   - 增加邊界條件測試
   - 補充異常情況測試

3. **隨機性導致的測試不穩定**
   - MCTS 算法有隨機性是正常的
   - 關注整體趨勢而非單次結果
   - 可以增加測試重複次數

## 持續改進

### 待增加的測試
- [ ] 壓力測試（長時間運行）
- [ ] 極端情況測試（異常輸入）
- [ ] 集成測試（與 API 和 GUI）
- [ ] 回歸測試（版本升級）

### 性能優化方向
- [ ] 算法優化（更好的剪枝）
- [ ] 並行化改進
- [ ] 緩存策略優化
- [ ] 內存使用優化

## 結論

[測試執行後填寫總結]