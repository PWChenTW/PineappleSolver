# 🍍 Pineapple OFC Solver - 快速開始指南

## 功能總覽

本求解器現已支持以下完整功能：

1. **鬼牌支持** - 54張牌（含2張鬼牌）
2. **逐街求解** - 支持街道式求解，可追蹤對手牌
3. **性能優化** - 10萬次模擬在5秒內完成
4. **多種界面** - CLI、互動式CLI、GUI
5. **隨機發牌** - 自動發牌或手動輸入

## 快速開始

### 1. 基本 CLI 使用

```bash
# 求解初始5張牌（支持鬼牌）
python3 ofc_cli.py As Kh Qd Jc Xj -s 10000

# 不使用鬼牌
python3 ofc_cli.py As Kh Qd Jc Th -s 10000
```

### 2. 逐街求解（新功能！）

```bash
# 啟動逐街求解模式
python3 ofc_cli_street.py As Kh Qd Jc Xj --continue
```

在此模式下：
- 初始5張牌會自動求解
- 之後每街會自動發3張牌
- 可選擇輸入對手的牌來追蹤
- 自動選擇最佳的2張擺放，1張棄牌
- 直到13張牌擺滿為止

### 3. GUI 使用

```bash
# 啟動 Streamlit GUI
streamlit run pineapple_ofc_gui.py
```

GUI 功能：
- 視覺化牌桌界面
- 點擊放置牌
- AI 建議功能
- 保存/載入遊戲
- 統計數據顯示

### 4. 進階功能

#### 對手牌追蹤
在逐街模式中，可以輸入對手每輪使用的牌：
```
輸入對手這輪的牌（可選，直接按 Enter 跳過）: 3d 4c 5h
```

#### 保存遊戲歷史
```bash
python3 ofc_cli_street.py As Kh Qd Jc Xj --continue --save-history game1.json
```

## 鬼牌規則

- 鬼牌表示為 `Xj`（X = 任意點數，j = joker）
- 鬼牌可以代替任何牌
- 求解器會自動找出鬼牌的最佳使用方式

## 性能說明

- 1,000次模擬：< 0.1秒
- 10,000次模擬：< 1秒
- 100,000次模擬：< 10秒

## 常見問題

### Q: 如何安裝 ChromeDriver？
A: 參見 `docs/CHROMEDRIVER_SETUP.md`

### Q: GUI 無法啟動？
A: 確保已安裝 streamlit：`pip install streamlit`

### Q: 想要更詳細的日誌？
A: 使用 `-v` 參數：`python3 ofc_cli.py As Kh Qd Jc Xj -s 10000 -v`

## 完整文檔

- [街道求解器使用指南](docs/STREET_SOLVER_USAGE.md)
- [ChromeDriver 安裝指南](docs/CHROMEDRIVER_SETUP.md)
- [用戶手冊（中文）](USER_MANUAL_CN.md)
- [用戶手冊（英文）](USER_MANUAL_EN.md)

## 測試驗證

運行完整測試：
```bash
python3 verify_all_features.py
```

## 聯繫支持

如有問題，請查看項目 GitHub Issues 或聯繫開發團隊。