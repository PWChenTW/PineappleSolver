#!/usr/bin/env python3
"""
GUI 測試配置文件
配置 Selenium WebDriver 和測試參數
"""

import os
from typing import Dict, Any
from enum import Enum

class BrowserType(Enum):
    """瀏覽器類型枚舉"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"
    SAFARI = "safari"

class TestConfig:
    """測試配置類"""
    
    # 基本配置
    BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8501")
    HEADLESS = os.getenv("TEST_HEADLESS", "true").lower() == "true"
    BROWSER = BrowserType(os.getenv("TEST_BROWSER", "chrome"))
    
    # 超時設置（秒）
    DEFAULT_TIMEOUT = 10
    PAGE_LOAD_TIMEOUT = 30
    IMPLICIT_WAIT = 5
    ELEMENT_WAIT = 10
    AI_COMPUTATION_TIMEOUT = 60  # AI 計算可能需要較長時間
    
    # 截圖設置
    SCREENSHOT_ON_FAILURE = True
    SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "test_screenshots")
    
    # 測試數據
    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")
    
    # WebDriver 路徑（可選，如果不在 PATH 中）
    CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH", None)
    FIREFOX_DRIVER_PATH = os.getenv("FIREFOX_DRIVER_PATH", None)
    
    # 瀏覽器選項
    BROWSER_OPTIONS = {
        BrowserType.CHROME: {
            "arguments": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ],
            "prefs": {
                "download.default_directory": TEST_DATA_DIR,
                "download.prompt_for_download": False,
                "profile.default_content_setting_values.notifications": 2
            }
        },
        BrowserType.FIREFOX: {
            "arguments": [
                "--width=1920",
                "--height=1080"
            ],
            "prefs": {
                "browser.download.folderList": 2,
                "browser.download.dir": TEST_DATA_DIR,
                "browser.download.useDownloadDir": True,
                "browser.helperApps.neverAsk.saveToDisk": "application/json"
            }
        }
    }
    
    # Streamlit 特定選擇器
    STREAMLIT_SELECTORS = {
        "app_loaded": '[data-testid="stApp"]',
        "button": 'button[kind="primary"]',
        "select_box": '[data-testid="stSelectbox"]',
        "slider": '[data-testid="stSlider"]',
        "checkbox": '[data-testid="stCheckbox"]',
        "file_uploader": '[data-testid="stFileUploader"]',
        "download_button": '[data-testid="stDownloadButton"]',
        "metric": '[data-testid="metric-container"]',
        "spinner": '[data-testid="stSpinner"]',
        "success_message": '[data-testid="stAlert"][data-baseweb="notification"][kind="success"]',
        "error_message": '[data-testid="stAlert"][data-baseweb="notification"][kind="error"]',
        "info_message": '[data-testid="stAlert"][data-baseweb="notification"][kind="info"]',
        "expander": '[data-testid="stExpander"]',
        "column": '[data-testid="column"]',
        "markdown": '[data-testid="stMarkdown"]'
    }
    
    # 遊戲特定選擇器
    GAME_SELECTORS = {
        "card": '.card',
        "selected_card": '.card.selected',
        "hand_container": '.hand-container',
        "front_hand": '.hand-container:nth-of-type(1)',
        "middle_hand": '.hand-container:nth-of-type(2)',
        "back_hand": '.hand-container:nth-of-type(3)',
        "new_game_button": 'button:contains("新遊戲")',
        "deal_initial_button": 'button:contains("發初始5張牌")',
        "get_ai_suggestion_button": 'button:contains("獲取 AI 建議")',
        "apply_ai_suggestion_button": 'button:contains("採用 AI 建議")',
        "place_card_button": 'button:contains("放置牌")',
        "draw_street_button": 'button:contains("抽第")',
        "save_game_button": 'button:contains("保存遊戲")'
    }
    
    # 性能測試配置
    PERFORMANCE_CONFIG = {
        "max_page_load_time": 5000,  # 毫秒
        "max_ai_response_time": 30000,  # 毫秒
        "max_card_placement_time": 1000,  # 毫秒
        "stress_test_iterations": 100,
        "concurrent_users": 5
    }
    
    # CI/CD 環境檢測
    IS_CI = any([
        os.getenv("CI"),
        os.getenv("GITHUB_ACTIONS"),
        os.getenv("JENKINS_HOME"),
        os.getenv("GITLAB_CI")
    ])
    
    @classmethod
    def get_browser_options(cls, browser_type: BrowserType) -> Dict[str, Any]:
        """獲取瀏覽器選項"""
        options = cls.BROWSER_OPTIONS.get(browser_type, {}).copy()
        
        # CI 環境下強制使用 headless
        if cls.IS_CI or cls.HEADLESS:
            if browser_type == BrowserType.CHROME:
                options["arguments"].append("--headless")
            elif browser_type == BrowserType.FIREFOX:
                options["arguments"].append("--headless")
        
        return options
    
    @classmethod
    def ensure_directories(cls):
        """確保必要的目錄存在"""
        os.makedirs(cls.SCREENSHOT_DIR, exist_ok=True)
        os.makedirs(cls.TEST_DATA_DIR, exist_ok=True)

# 測試數據
TEST_CARDS = {
    "royal_flush": ["As", "Ks", "Qs", "Js", "10s"],
    "straight_flush": ["9h", "8h", "7h", "6h", "5h"],
    "four_of_kind": ["Ah", "Ad", "Ac", "As", "Kh"],
    "full_house": ["Kh", "Kd", "Kc", "Qh", "Qd"],
    "flush": ["Ah", "9h", "7h", "5h", "3h"],
    "straight": ["10h", "9d", "8c", "7s", "6h"],
    "three_of_kind": ["Qh", "Qd", "Qc", "Jh", "10d"],
    "two_pair": ["Jh", "Jd", "10h", "10d", "9c"],
    "one_pair": ["Ah", "Ad", "Kh", "Qd", "Jc"],
    "high_card": ["Ah", "Kd", "Qc", "Js", "9h"]
}

# 測試場景
TEST_SCENARIOS = {
    "valid_game": {
        "initial_cards": ["Ah", "Kh", "Qh", "Jh", "10h"],
        "placement": {
            "front": ["Ah", "Kh", "Qh"],
            "middle": ["Jh", "10h"],
            "back": []
        },
        "streets": [
            {
                "cards": ["9h", "9d", "9c"],
                "place": [("9h", "middle"), ("9d", "middle")],
                "discard": "9c"
            },
            {
                "cards": ["8h", "8d", "8c"],
                "place": [("8h", "middle"), ("8d", "back")],
                "discard": "8c"
            },
            {
                "cards": ["7h", "7d", "7c"],
                "place": [("7h", "back"), ("7d", "back")],
                "discard": "7c"
            },
            {
                "cards": ["6h", "6d", "6c"],
                "place": [("6h", "back"), ("6d", "back")],
                "discard": "6c"
            }
        ]
    },
    "foul_game": {
        "initial_cards": ["2h", "2d", "3h", "3d", "4h"],
        "placement": {
            "front": ["2h", "2d", "3h"],  # 兩對放前墩（犯規）
            "middle": ["3d", "4h"],
            "back": []
        }
    },
    "fantasy_land": {
        "initial_cards": ["Qh", "Qd", "Kh", "Kd", "Ah"],
        "placement": {
            "front": ["Qh", "Qd", "Kh"],  # QQ+ 在前墩
            "middle": ["Kd", "Ah"],
            "back": []
        }
    }
}