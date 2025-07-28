# GUI 自動化測試套件使用指南

這個測試套件使用 Selenium WebDriver 對 Pineapple OFC GUI (Streamlit) 進行全面的自動化測試。

## 快速開始

### 1. 安裝依賴

```bash
# 安裝基本依賴
pip install selenium streamlit pytest

# Chrome 瀏覽器（推薦）
# macOS
brew install chromedriver

# Linux
sudo apt-get install chromium-chromedriver

# Windows
# 下載 ChromeDriver: https://chromedriver.chromium.org/
```

### 2. 運行測試

```bash
# 運行所有測試（自動啟動 Streamlit）
python run_gui_tests.py

# 使用 headless 模式
python run_gui_tests.py --headless

# 指定瀏覽器
python run_gui_tests.py --browser firefox

# 運行特定測試套件
python run_gui_tests.py --suite basic       # 基本功能測試
python run_gui_tests.py --suite scenarios   # 場景測試
python run_gui_tests.py --suite performance # 性能測試

# CI 模式（生成 JUnit XML）
python run_gui_tests.py --ci --headless
```

### 3. 手動運行（已有 Streamlit 運行中）

```bash
# 先啟動 Streamlit
streamlit run pineapple_ofc_gui.py

# 在另一個終端運行測試
python run_gui_tests.py --no-app
```

## 測試結構

### 文件說明

- `test_gui_config.py` - 測試配置（瀏覽器選項、超時設置、選擇器等）
- `gui_test_utils.py` - 測試工具函數（WebDriver 管理、Streamlit 輔助、遊戲輔助等）
- `test_gui_automation.py` - 主測試套件（包含所有測試用例）
- `run_gui_tests.py` - 測試執行腳本（管理測試運行和報告生成）
- `generate_test_data.py` - 測試數據生成腳本

### 測試類別

1. **TestPineappleGUI** - 基本功能測試
   - 新遊戲初始化
   - 發牌功能
   - 牌放置
   - AI 建議
   - 設置調整
   - 保存/載入

2. **TestGameScenarios** - 遊戲場景測試
   - Fantasy Land 場景
   - 犯規預防
   - 完整遊戲流程

3. **TestPerformance** - 性能測試
   - 頁面加載時間
   - AI 計算響應時間
   - 壓力測試

## 配置選項

### 環境變量

```bash
# 測試基礎 URL
export TEST_BASE_URL="http://localhost:8501"

# 瀏覽器類型
export TEST_BROWSER="chrome"  # chrome, firefox, edge, safari

# Headless 模式
export TEST_HEADLESS="true"

# WebDriver 路徑（可選）
export CHROME_DRIVER_PATH="/path/to/chromedriver"
export FIREFOX_DRIVER_PATH="/path/to/geckodriver"
```

### 測試配置

編輯 `test_gui_config.py`：

```python
# 超時設置
DEFAULT_TIMEOUT = 10  # 默認等待時間
AI_COMPUTATION_TIMEOUT = 60  # AI 計算超時

# 性能測試配置
PERFORMANCE_CONFIG = {
    "max_page_load_time": 5000,  # 最大頁面加載時間（毫秒）
    "max_ai_response_time": 30000,  # 最大 AI 響應時間
    "stress_test_iterations": 100,  # 壓力測試迭代次數
}
```

## 測試報告

### HTML 報告

測試完成後會生成 HTML 報告：
- 位置：`test_reports/gui_test_report_[timestamp].html`
- 包含：測試摘要、詳細結果、執行時間

### JUnit XML（CI/CD）

使用 `--ci` 參數生成 JUnit XML：
- 位置：`test_reports/junit_report_[timestamp].xml`
- 可用於 Jenkins、GitHub Actions 等

### 截圖

測試失敗時自動截圖：
- 位置：`test_screenshots/[test_name]_failure_[timestamp].png`

## CI/CD 集成

### GitHub Actions

```yaml
# .github/workflows/gui_tests.yml
- name: Run GUI Tests
  run: |
    python run_gui_tests.py --browser chrome --headless --ci
```

### Jenkins

```groovy
stage('GUI Tests') {
    steps {
        sh 'python run_gui_tests.py --browser chrome --headless --ci'
        junit 'test_reports/junit_report_*.xml'
    }
}
```

### GitLab CI

```yaml
gui_tests:
  script:
    - python run_gui_tests.py --browser chrome --headless --ci
  artifacts:
    reports:
      junit: test_reports/junit_report_*.xml
```

## 常見問題

### 1. WebDriver 找不到

```bash
# 檢查 WebDriver 是否在 PATH 中
which chromedriver

# 或設置環境變量
export CHROME_DRIVER_PATH="/usr/local/bin/chromedriver"
```

### 2. Streamlit 連接失敗

```bash
# 檢查 Streamlit 是否運行
curl http://localhost:8501

# 檢查端口是否被佔用
lsof -i :8501
```

### 3. 測試超時

增加超時設置：
```python
# test_gui_config.py
AI_COMPUTATION_TIMEOUT = 120  # 增加到 2 分鐘
```

### 4. Headless 模式問題

某些功能在 headless 模式下可能不工作，嘗試：
```bash
# 使用 GUI 模式調試
python run_gui_tests.py --browser chrome
```

## 擴展測試

### 添加新測試用例

```python
# 在 test_gui_automation.py 中添加
def test_new_feature(self):
    """測試新功能"""
    self.recorder.log_event("test_new_feature_start")
    
    # 測試邏輯
    self.game.start_new_game()
    # ...
    
    self.recorder.log_event("test_new_feature_success")
```

### 添加新的測試場景

編輯 `generate_test_data.py` 添加新場景：

```python
scenarios.append({
    "name": "new_scenario",
    "description": "新測試場景",
    "steps": [
        {"action": "new_game"},
        # 添加步驟...
    ]
})
```

## 性能優化建議

1. **並行測試**
   ```bash
   pytest test_gui_automation.py -n 4  # 使用 4 個進程
   ```

2. **重用瀏覽器實例**
   - 使用 `setUpClass` 和 `tearDownClass`
   - 減少瀏覽器啟動/關閉次數

3. **智能等待**
   - 使用顯式等待而非固定 sleep
   - 調整等待策略

4. **測試數據緩存**
   - 預生成測試數據
   - 避免重複計算

## 貢獻指南

歡迎貢獻新的測試用例！請確保：

1. 遵循現有的代碼風格
2. 添加適當的文檔
3. 測試新添加的功能
4. 更新相關文檔

## 授權

MIT License