# 街道求解器使用指南

## 概述

街道求解器（`ofc_cli_street.py`）是一個強大的命令行工具，用於逐街求解 Pineapple OFC 遊戲。它支持自動發牌、對手牌追蹤和交互式求解。

## 新功能

### 1. 自動發牌功能
- **默認行為**：如果不提供初始牌，系統會自動發牌
- **智能排除**：自動排除已使用的牌和對手的牌
- **完整遊戲流程**：從初始5張到最後一街，全程自動發牌

### 2. 對手牌追蹤
- **記錄對手的牌**：避免發到對手已經擁有的牌
- **實時更新**：每一街都可以更新對手的牌
- **準確計算**：確保剩餘牌數計算準確

### 3. 靈活的輸入模式
- **自動模式**：按 Enter 自動發下一街的牌
- **手動模式**：手動輸入特定的牌
- **混合模式**：隨時在兩種模式間切換

## 使用方法

### 基本用法

```bash
# 完全自動模式（推薦）
python ofc_cli_street.py --continue

# 手動輸入初始牌
python ofc_cli_street.py As Kh Qd Jc 10s --continue

# 指定對手的牌
python ofc_cli_street.py --opponent-cards 2h 3h 4h --continue

# 手動模式
python ofc_cli_street.py --manual --continue
```

### 參數說明

- `cards`：初始5張牌（可選，留空則自動發牌）
- `--continue`：啟用連續模式，逐街進行遊戲
- `--manual`：啟用手動輸入模式
- `--opponent-cards`：指定對手的牌（空格分隔）
- `--simulations`：MCTS 模擬次數（默認 10000）
- `--save-history`：保存遊戲歷史到文件

## 使用示例

### 示例 1：完全自動遊戲

```bash
$ python ofc_cli_street.py --continue

自動發初始5張牌...
=== 初始5張牌 ===
牌: Ah Kd Qs Jh 10c

最佳擺放:
前墩: Qs
中墩: Jh 10c
後墩: Ah Kd
✓ 有效擺放

繼續模式已啟用。輸入3張牌來模擬下一街，或輸入 'quit' 退出。

按 Enter 發第 1 街的牌...
發到: 9h 8s 7d

=== 第 1 街 ===
抽到: 9h 8s 7d
評估 21 種可能的動作...

最佳動作:
  9h → middle
  8s → back
  棄牌: 7d

當前狀態:
前墩 (1/3): Qs
中墩 (3/5): Jh 10c 9h
後墩 (3/5): Ah Kd 8s
✓ 有效擺放
```

### 示例 2：追蹤對手的牌

```bash
$ python ofc_cli_street.py --opponent-cards As Ks Qs Js 10s 9s 8s 7s 6s 5s 4s 3s 2s --continue

已記錄對手的 13 張牌
自動發初始5張牌...
# 系統不會發出任何黑桃，因為對手已經擁有所有黑桃
```

### 示例 3：混合模式

```bash
$ python ofc_cli_street.py --manual --continue

# 手動輸入初始牌
初始5張牌: Ah Kh Qh Jh 10h

# 第一街手動輸入
第 1 街 (3張牌，或 'auto' 切換到自動模式): 9h 8h 7h

# 切換到自動模式
第 2 街 (3張牌，或 'auto' 切換到自動模式): auto
已切換到自動發牌模式

按 Enter 發第 2 街的牌...
發到: 6d 5c 4s
```

## 進階功能

### 1. 遊戲狀態追蹤

求解器會追蹤以下信息：
- 已使用的牌（玩家擺放的牌）
- 對手的牌
- 棄掉的牌
- 剩餘可用牌數

### 2. 智能決策

使用 MCTS 算法評估每個可能的動作：
- 考慮所有可能的擺放組合
- 評估每個組合的期望得分
- 選擇最優的擺放和棄牌策略

### 3. 歷史記錄

可以保存完整的遊戲歷史：
```bash
python ofc_cli_street.py --continue --save-history game_history.json
```

歷史文件包含：
- 每一街的牌
- 每個決策和理由
- 最終的遊戲狀態

## 常見問題

### Q: 如何查看剩餘的牌？
A: 在每一街後，系統會自動顯示遊戲狀態，包括剩餘可用牌數。

### Q: 可以撤銷上一步嗎？
A: 目前不支持撤銷功能，建議謹慎決策。

### Q: 如何提高求解速度？
A: 減少模擬次數：`--simulations 1000`（犧牲一些準確性換取速度）

### Q: 支持鬼牌嗎？
A: 是的，底層求解器支持鬼牌，但 CLI 界面目前還在開發中。

## 技術細節

### 牌組管理
- 初始創建52張牌的完整牌組
- 使用集合追蹤各類已使用的牌
- 實時更新可用牌列表

### 發牌算法
```python
def _deal_cards(self, num_cards: int) -> List[Card]:
    # 獲取所有可用牌
    available_cards = []
    for card in self.deck:
        if card not in used_cards and card not in opponent_cards:
            available_cards.append(card)
    
    # 隨機選擇
    random.shuffle(available_cards)
    return available_cards[:num_cards]
```

### 性能優化
- 使用緩存減少重複計算
- 並行化 MCTS 模擬
- 智能剪枝減少搜索空間