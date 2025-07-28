#!/usr/bin/env python3
"""
GUI 測試工具函數
提供 Selenium 測試的輔助功能
"""

import os
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from test_gui_config import TestConfig, BrowserType

class WebDriverManager:
    """WebDriver 管理器"""
    
    @staticmethod
    def create_driver(browser_type: BrowserType = TestConfig.BROWSER) -> WebDriver:
        """創建 WebDriver 實例"""
        if browser_type == BrowserType.CHROME:
            return WebDriverManager._create_chrome_driver()
        elif browser_type == BrowserType.FIREFOX:
            return WebDriverManager._create_firefox_driver()
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
    
    @staticmethod
    def _create_chrome_driver() -> WebDriver:
        """創建 Chrome WebDriver"""
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        options = Options()
        browser_options = TestConfig.get_browser_options(BrowserType.CHROME)
        
        # 添加參數
        for arg in browser_options.get("arguments", []):
            options.add_argument(arg)
        
        # 添加偏好設置
        for key, value in browser_options.get("prefs", {}).items():
            options.add_experimental_option("prefs", {key: value})
        
        # 創建 driver
        if WEBDRIVER_MANAGER_AVAILABLE and not TestConfig.CHROME_DRIVER_PATH:
            # 使用 webdriver-manager 自動管理 ChromeDriver
            service = Service(ChromeDriverManager().install())
        else:
            # 使用手動指定的路徑或系統 PATH
            service_args = {}
            if TestConfig.CHROME_DRIVER_PATH:
                service_args["executable_path"] = TestConfig.CHROME_DRIVER_PATH
            service = Service(**service_args) if service_args else None
        
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
        driver.set_page_load_timeout(TestConfig.PAGE_LOAD_TIMEOUT)
        
        return driver
    
    @staticmethod
    def _create_firefox_driver() -> WebDriver:
        """創建 Firefox WebDriver"""
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service
        
        options = Options()
        browser_options = TestConfig.get_browser_options(BrowserType.FIREFOX)
        
        # 添加參數
        for arg in browser_options.get("arguments", []):
            options.add_argument(arg)
        
        # 創建 driver
        if WEBDRIVER_MANAGER_AVAILABLE and not TestConfig.FIREFOX_DRIVER_PATH:
            # 使用 webdriver-manager 自動管理 GeckoDriver
            service = Service(GeckoDriverManager().install())
        else:
            # 使用手動指定的路徑或系統 PATH
            service_args = {}
            if TestConfig.FIREFOX_DRIVER_PATH:
                service_args["executable_path"] = TestConfig.FIREFOX_DRIVER_PATH
            service = Service(**service_args) if service_args else None
        
        driver = webdriver.Firefox(service=service, options=options)
        
        driver.implicitly_wait(TestConfig.IMPLICIT_WAIT)
        driver.set_page_load_timeout(TestConfig.PAGE_LOAD_TIMEOUT)
        
        return driver

class StreamlitHelper:
    """Streamlit 特定的輔助函數"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TestConfig.DEFAULT_TIMEOUT)
    
    def wait_for_app_loaded(self):
        """等待 Streamlit 應用載入完成"""
        self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, TestConfig.STREAMLIT_SELECTORS["app_loaded"])
            )
        )
        # 額外等待以確保所有元素載入
        time.sleep(2)
    
    def click_button(self, button_text: str, timeout: int = TestConfig.ELEMENT_WAIT):
        """點擊包含特定文字的按鈕"""
        # Streamlit 按鈕可能需要特殊處理
        buttons = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.TAG_NAME, "button")
            )
        )
        
        for button in buttons:
            if button_text in button.text:
                # 滾動到按鈕位置
                self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(0.5)
                # 使用 JavaScript 點擊以避免元素被遮擋
                self.driver.execute_script("arguments[0].click();", button)
                return True
        
        raise NoSuchElementException(f"Button with text '{button_text}' not found")
    
    def select_dropdown(self, label: str, value: str):
        """選擇下拉菜單選項"""
        # 找到包含標籤的選擇框
        select_containers = self.driver.find_elements(
            By.CSS_SELECTOR, TestConfig.STREAMLIT_SELECTORS["select_box"]
        )
        
        for container in select_containers:
            try:
                label_element = container.find_element(By.TAG_NAME, "label")
                if label in label_element.text:
                    # 點擊選擇框
                    select_element = container.find_element(By.TAG_NAME, "div[role='button']")
                    select_element.click()
                    time.sleep(0.5)
                    
                    # 選擇選項
                    options = self.driver.find_elements(By.CSS_SELECTOR, "[role='option']")
                    for option in options:
                        if value in option.text:
                            option.click()
                            return True
            except:
                continue
        
        raise NoSuchElementException(f"Dropdown with label '{label}' not found")
    
    def set_slider(self, label: str, value: int):
        """設置滑塊值"""
        sliders = self.driver.find_elements(
            By.CSS_SELECTOR, TestConfig.STREAMLIT_SELECTORS["slider"]
        )
        
        for slider_container in sliders:
            try:
                label_element = slider_container.find_element(By.TAG_NAME, "label")
                if label in label_element.text:
                    # 獲取滑塊元素
                    slider = slider_container.find_element(By.CSS_SELECTOR, "[role='slider']")
                    
                    # 使用 JavaScript 設置值
                    self.driver.execute_script(
                        "arguments[0].setAttribute('aria-valuenow', arguments[1]);",
                        slider, value
                    )
                    
                    # 觸發變更事件
                    self.driver.execute_script(
                        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        slider
                    )
                    return True
            except:
                continue
        
        raise NoSuchElementException(f"Slider with label '{label}' not found")
    
    def toggle_checkbox(self, label: str, checked: bool):
        """切換複選框狀態"""
        checkboxes = self.driver.find_elements(
            By.CSS_SELECTOR, TestConfig.STREAMLIT_SELECTORS["checkbox"]
        )
        
        for checkbox_container in checkboxes:
            try:
                label_element = checkbox_container.find_element(By.TAG_NAME, "label")
                if label in label_element.text:
                    checkbox = checkbox_container.find_element(By.TAG_NAME, "input[type='checkbox']")
                    
                    # 檢查當前狀態
                    is_checked = checkbox.is_selected()
                    if is_checked != checked:
                        # 使用 JavaScript 點擊
                        self.driver.execute_script("arguments[0].click();", checkbox)
                    return True
            except:
                continue
        
        raise NoSuchElementException(f"Checkbox with label '{label}' not found")
    
    def wait_for_spinner_disappear(self, timeout: int = TestConfig.AI_COMPUTATION_TIMEOUT):
        """等待加載動畫消失"""
        try:
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, TestConfig.STREAMLIT_SELECTORS["spinner"])
                )
            )
        except TimeoutException:
            pass  # Spinner 可能已經消失
    
    def get_metric_value(self, label: str) -> str:
        """獲取指標值"""
        metrics = self.driver.find_elements(
            By.CSS_SELECTOR, TestConfig.STREAMLIT_SELECTORS["metric"]
        )
        
        for metric in metrics:
            try:
                label_element = metric.find_element(By.CSS_SELECTOR, "[data-testid='stMetricLabel']")
                if label in label_element.text:
                    value_element = metric.find_element(By.CSS_SELECTOR, "[data-testid='stMetricValue']")
                    return value_element.text
            except:
                continue
        
        raise NoSuchElementException(f"Metric with label '{label}' not found")
    
    def get_alert_message(self, alert_type: str = "success") -> str:
        """獲取警報消息"""
        selector = TestConfig.STREAMLIT_SELECTORS.get(f"{alert_type}_message")
        if not selector:
            raise ValueError(f"Invalid alert type: {alert_type}")
        
        try:
            alert = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return alert.text
        except TimeoutException:
            return ""

class GameHelper:
    """遊戲特定的輔助函數"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, TestConfig.DEFAULT_TIMEOUT)
        self.streamlit = StreamlitHelper(driver)
    
    def get_cards(self, selector: str) -> List[WebElement]:
        """獲取卡牌元素"""
        return self.driver.find_elements(By.CSS_SELECTOR, selector)
    
    def click_card(self, card_element: WebElement):
        """點擊卡牌"""
        self.driver.execute_script("arguments[0].scrollIntoView(true);", card_element)
        time.sleep(0.5)
        card_element.click()
    
    def get_card_text(self, card_element: WebElement) -> str:
        """獲取卡牌文字"""
        return card_element.text.strip()
    
    def select_card_by_value(self, card_value: str) -> bool:
        """根據值選擇卡牌"""
        cards = self.get_cards(TestConfig.GAME_SELECTORS["card"])
        for card in cards:
            if card_value in self.get_card_text(card):
                self.click_card(card)
                return True
        return False
    
    def get_hand_cards(self, hand_type: str) -> List[str]:
        """獲取特定手牌的卡牌"""
        selector = TestConfig.GAME_SELECTORS.get(f"{hand_type}_hand")
        if not selector:
            raise ValueError(f"Invalid hand type: {hand_type}")
        
        try:
            hand_container = self.driver.find_element(By.CSS_SELECTOR, selector)
            cards = hand_container.find_elements(By.CSS_SELECTOR, ".card")
            return [self.get_card_text(card) for card in cards if self.get_card_text(card) != "_"]
        except NoSuchElementException:
            return []
    
    def place_card(self, card_value: str, position: str):
        """放置卡牌到指定位置"""
        # 選擇卡牌
        if not self.select_card_by_value(card_value):
            raise ValueError(f"Card {card_value} not found")
        
        # 選擇位置
        self.streamlit.select_dropdown("放置位置", position)
        
        # 點擊放置按鈕
        self.streamlit.click_button("放置牌")
    
    def start_new_game(self):
        """開始新遊戲"""
        self.streamlit.click_button("新遊戲")
        time.sleep(1)
    
    def deal_initial_cards(self):
        """發初始牌"""
        self.streamlit.click_button("發初始5張牌")
        time.sleep(1)
    
    def draw_street(self, street_number: int):
        """抽街道牌"""
        self.streamlit.click_button(f"抽第{street_number}街")
        time.sleep(1)
    
    def get_ai_suggestion(self):
        """獲取 AI 建議"""
        self.streamlit.click_button("獲取 AI 建議")
        self.streamlit.wait_for_spinner_disappear()
    
    def apply_ai_suggestion(self):
        """應用 AI 建議"""
        self.streamlit.click_button("採用 AI 建議")
        time.sleep(1)
    
    def save_game(self) -> str:
        """保存遊戲並返回下載鏈接"""
        self.streamlit.click_button("保存遊戲")
        time.sleep(1)
        
        # 獲取下載按鈕
        download_button = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, TestConfig.STREAMLIT_SELECTORS["download_button"])
            )
        )
        
        # 獲取下載鏈接
        return download_button.get_attribute("href")

class TestRecorder:
    """測試記錄器"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = None
        self.events = []
    
    def start(self):
        """開始記錄"""
        self.start_time = time.time()
        self.log_event("Test started", {"test_name": self.test_name})
    
    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """記錄事件"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_time": time.time() - self.start_time if self.start_time else 0,
            "event_type": event_type,
            "data": data or {}
        }
        self.events.append(event)
    
    def take_screenshot(self, driver: WebDriver, name: str = None):
        """截圖"""
        TestConfig.ensure_directories()
        
        filename = f"{self.test_name}_{name or 'screenshot'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(TestConfig.SCREENSHOT_DIR, filename)
        
        driver.save_screenshot(filepath)
        self.log_event("screenshot_taken", {"filepath": filepath})
        
        return filepath
    
    def save_report(self):
        """保存測試報告"""
        TestConfig.ensure_directories()
        
        report = {
            "test_name": self.test_name,
            "start_time": self.start_time,
            "duration": time.time() - self.start_time if self.start_time else 0,
            "events": self.events
        }
        
        filename = f"{self.test_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(TestConfig.TEST_DATA_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filepath

class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.metrics = []
    
    def measure_page_load(self) -> Dict[str, float]:
        """測量頁面加載時間"""
        navigation_start = self.driver.execute_script("return window.performance.timing.navigationStart")
        dom_complete = self.driver.execute_script("return window.performance.timing.domComplete")
        
        return {
            "page_load_time": (dom_complete - navigation_start) / 1000.0
        }
    
    def measure_action(self, action_name: str, action_func):
        """測量操作執行時間"""
        start_time = time.time()
        result = action_func()
        end_time = time.time()
        
        metric = {
            "action": action_name,
            "duration": end_time - start_time,
            "timestamp": datetime.now().isoformat()
        }
        
        self.metrics.append(metric)
        return result, metric
    
    def get_browser_metrics(self) -> Dict[str, Any]:
        """獲取瀏覽器性能指標"""
        return {
            "memory": self.driver.execute_script("return performance.memory") if self.driver.name == "chrome" else {},
            "timing": self.driver.execute_script("return performance.timing"),
            "navigation": self.driver.execute_script("return performance.navigation")
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能報告"""
        return {
            "metrics": self.metrics,
            "browser_metrics": self.get_browser_metrics(),
            "summary": {
                "total_actions": len(self.metrics),
                "average_duration": sum(m["duration"] for m in self.metrics) / len(self.metrics) if self.metrics else 0,
                "max_duration": max((m["duration"] for m in self.metrics), default=0),
                "min_duration": min((m["duration"] for m in self.metrics), default=0)
            }
        }