# ChromeDriver 安裝指南

本指南幫助您安裝和配置 ChromeDriver 以運行 Selenium 自動化測試。

## 什麼是 ChromeDriver？

ChromeDriver 是一個獨立的服務器，實現了 WebDriver 協議，用於自動化 Chrome 瀏覽器。

## 安裝方法

### 方法 1：使用 Homebrew（macOS）

```bash
# 安裝 ChromeDriver
brew install chromedriver

# 驗證安裝
chromedriver --version
```

### 方法 2：使用 pip 安裝 webdriver-manager（推薦）

```bash
# 安裝 webdriver-manager
pip install webdriver-manager

# 在測試代碼中使用：
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

### 方法 3：手動下載

1. 檢查您的 Chrome 版本：
   - 打開 Chrome
   - 訪問 `chrome://version/`
   - 記下版本號（例如：120.0.6099.71）

2. 下載對應版本的 ChromeDriver：
   - 訪問 https://chromedriver.chromium.org/downloads
   - 或新版本訪問 https://googlechromelabs.github.io/chrome-for-testing/
   - 下載與您的 Chrome 版本匹配的 ChromeDriver

3. 安裝 ChromeDriver：
   ```bash
   # macOS/Linux
   sudo mv chromedriver /usr/local/bin/
   sudo chmod +x /usr/local/bin/chromedriver
   
   # Windows
   # 將 chromedriver.exe 添加到系統 PATH
   ```

### 方法 4：使用系統包管理器

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

**CentOS/RHEL:**
```bash
sudo yum install chromedriver
```

## 配置測試環境

### 修改測試文件使用 webdriver-manager（推薦）

編輯 `gui_test_utils.py`：

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class WebDriverManager:
    @staticmethod
    def create_driver():
        """創建 Chrome WebDriver 實例"""
        options = Options()
        if TestConfig.HEADLESS:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--window-size={TestConfig.WINDOW_WIDTH},{TestConfig.WINDOW_HEIGHT}')
        
        # 使用 webdriver-manager 自動下載和管理 ChromeDriver
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
```

### 環境變量配置（可選）

如果手動安裝，可能需要設置環境變量：

```bash
# macOS/Linux
export PATH=$PATH:/path/to/chromedriver

# Windows
set PATH=%PATH%;C:\path\to\chromedriver
```

## 常見問題

### 1. ChromeDriver 版本不匹配

錯誤信息：`SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version XX`

解決方案：
- 下載與您的 Chrome 版本匹配的 ChromeDriver
- 使用 webdriver-manager 自動管理版本

### 2. ChromeDriver 權限問題（macOS）

錯誤信息：`"chromedriver" cannot be opened because the developer cannot be verified`

解決方案：
```bash
# 允許執行
xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

### 3. 找不到 ChromeDriver

錯誤信息：`WebDriverException: Message: 'chromedriver' executable needs to be in PATH`

解決方案：
- 確保 ChromeDriver 在系統 PATH 中
- 或使用絕對路徑指定 ChromeDriver 位置
- 使用 webdriver-manager 自動處理

## 驗證安裝

創建測試腳本 `test_chromedriver.py`：

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

try:
    # 創建 driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # 訪問網頁
    driver.get("https://www.google.com")
    print(f"成功！頁面標題：{driver.title}")
    
    # 關閉瀏覽器
    driver.quit()
    
except Exception as e:
    print(f"錯誤：{e}")
```

運行測試：
```bash
python test_chromedriver.py
```

## 在 CI/CD 環境中使用

### GitHub Actions

```yaml
- name: Setup Chrome
  uses: browser-actions/setup-chrome@latest
  
- name: Setup ChromeDriver
  uses: nanasess/setup-chromedriver@v2
```

### Docker

```dockerfile
FROM python:3.9

# 安裝 Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update && apt-get install -y google-chrome-stable

# 安裝 ChromeDriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install -r requirements.txt
```

## 相關資源

- [ChromeDriver 官方文檔](https://chromedriver.chromium.org/)
- [Selenium 文檔](https://www.selenium.dev/documentation/)
- [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
- [webdriver-manager GitHub](https://github.com/SergeyPirogov/webdriver_manager)