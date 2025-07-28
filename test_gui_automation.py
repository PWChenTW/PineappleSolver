#!/usr/bin/env python3
"""
GUI 自動化測試套件
使用 Selenium WebDriver 測試 Streamlit GUI
"""

import unittest
import time
import json
from typing import List, Dict, Any
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from test_gui_config import TestConfig, TEST_CARDS, TEST_SCENARIOS
from gui_test_utils import (
    WebDriverManager, StreamlitHelper, GameHelper, 
    TestRecorder, PerformanceMonitor
)

class TestPineappleGUI(unittest.TestCase):
    """Pineapple OFC GUI 測試類"""
    
    @classmethod
    def setUpClass(cls):
        """測試類設置"""
        TestConfig.ensure_directories()
        cls.driver = WebDriverManager.create_driver()
        cls.base_url = TestConfig.BASE_URL
    
    @classmethod
    def tearDownClass(cls):
        """測試類清理"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def setUp(self):
        """每個測試方法前的設置"""
        self.driver.get(self.base_url)
        self.streamlit = StreamlitHelper(self.driver)
        self.game = GameHelper(self.driver)
        self.recorder = TestRecorder(self._testMethodName)
        self.performance = PerformanceMonitor(self.driver)
        
        self.recorder.start()
        self.streamlit.wait_for_app_loaded()
        
        # 開始新遊戲
        self.game.start_new_game()
    
    def tearDown(self):
        """每個測試方法後的清理"""
        if TestConfig.SCREENSHOT_ON_FAILURE and hasattr(self, '_outcome'):
            if not self._outcome.success:
                self.recorder.take_screenshot(self.driver, "failure")
        
        self.recorder.save_report()
    
    def test_new_game_initialization(self):
        """測試新遊戲初始化"""
        self.recorder.log_event("test_new_game_start")
        
        # 檢查初始狀態
        front_cards = self.game.get_hand_cards("front")
        middle_cards = self.game.get_hand_cards("middle")
        back_cards = self.game.get_hand_cards("back")
        
        self.assertEqual(len(front_cards), 0, "前墩應該為空")
        self.assertEqual(len(middle_cards), 0, "中墩應該為空")
        self.assertEqual(len(back_cards), 0, "後墩應該為空")
        
        # 測試發牌功能
        self.game.deal_initial_cards()
        
        # 檢查是否有5張牌顯示
        initial_cards = self.game.get_cards(TestConfig.GAME_SELECTORS["card"])
        self.assertEqual(len(initial_cards), 5, "應該發5張初始牌")
        
        self.recorder.log_event("test_new_game_success")
    
    def test_card_placement(self):
        """測試牌放置功能"""
        self.recorder.log_event("test_card_placement_start")
        
        # 發初始牌
        self.game.deal_initial_cards()
        time.sleep(1)
        
        # 獲取第一張牌
        cards = self.game.get_cards(TestConfig.GAME_SELECTORS["card"])
        self.assertGreater(len(cards), 0, "應該有可用的牌")
        
        first_card_text = self.game.get_card_text(cards[0])
        
        # 測試放置到前墩
        cards[0].click()
        self.streamlit.select_dropdown("放置位置", "front")
        self.streamlit.click_button("放置牌")
        time.sleep(1)
        
        # 驗證牌已放置
        front_cards = self.game.get_hand_cards("front")
        self.assertEqual(len(front_cards), 1, "前墩應該有1張牌")
        
        self.recorder.log_event("test_card_placement_success", {
            "card": first_card_text,
            "position": "front"
        })
    
    def test_ai_suggestion(self):
        """測試 AI 建議功能"""
        self.recorder.log_event("test_ai_suggestion_start")
        
        # 發初始牌
        self.game.deal_initial_cards()
        
        # 測量 AI 計算時間
        result, metric = self.performance.measure_action(
            "get_ai_suggestion",
            lambda: self.game.get_ai_suggestion()
        )
        
        self.recorder.log_event("ai_computation_complete", metric)
        
        # 檢查是否顯示建議
        success_message = self.streamlit.get_alert_message("success")
        self.assertIn("AI 建議", success_message, "應該顯示 AI 建議")
        
        # 應用建議
        self.game.apply_ai_suggestion()
        
        # 驗證牌已按建議放置
        total_cards = (len(self.game.get_hand_cards("front")) + 
                      len(self.game.get_hand_cards("middle")) + 
                      len(self.game.get_hand_cards("back")))
        
        self.assertEqual(total_cards, 5, "應該放置了5張牌")
        
        self.recorder.log_event("test_ai_suggestion_success")
    
    def test_complete_game_flow(self):
        """測試完整遊戲流程"""
        self.recorder.log_event("test_complete_game_start")
        
        # 第一階段：初始5張牌
        self.game.deal_initial_cards()
        self.game.get_ai_suggestion()
        self.game.apply_ai_suggestion()
        
        # 街道階段
        for street in range(1, 5):
            self.recorder.log_event(f"street_{street}_start")
            
            # 抽牌
            self.game.draw_street(street)
            
            # 獲取並應用 AI 建議
            self.game.get_ai_suggestion()
            self.game.apply_ai_suggestion()
            
            self.recorder.log_event(f"street_{street}_complete")
        
        # 檢查遊戲完成
        success_message = self.streamlit.get_alert_message("success")
        self.assertIn("遊戲完成", success_message, "遊戲應該完成")
        
        # 檢查手牌強度顯示
        front_strength = self.streamlit.get_metric_value("前墩")
        middle_strength = self.streamlit.get_metric_value("中墩")
        back_strength = self.streamlit.get_metric_value("後墩")
        
        self.assertTrue(front_strength, "應該顯示前墩強度")
        self.assertTrue(middle_strength, "應該顯示中墩強度")
        self.assertTrue(back_strength, "應該顯示後墩強度")
        
        self.recorder.log_event("test_complete_game_success")
    
    def test_settings_adjustment(self):
        """測試設置調整功能"""
        self.recorder.log_event("test_settings_start")
        
        # 測試模擬次數調整
        self.streamlit.set_slider("MCTS 模擬次數", 50000)
        time.sleep(1)
        
        # 測試鬼牌開關
        self.streamlit.toggle_checkbox("包含鬼牌", False)
        time.sleep(1)
        
        self.streamlit.toggle_checkbox("包含鬼牌", True)
        time.sleep(1)
        
        # 測試顯示 AI 思考過程
        self.streamlit.toggle_checkbox("顯示 AI 思考過程", True)
        
        self.recorder.log_event("test_settings_success")
    
    def test_save_load_game(self):
        """測試保存和載入遊戲功能"""
        self.recorder.log_event("test_save_load_start")
        
        # 進行一些遊戲操作
        self.game.deal_initial_cards()
        self.game.get_ai_suggestion()
        self.game.apply_ai_suggestion()
        
        # 保存遊戲
        download_link = self.game.save_game()
        self.assertTrue(download_link, "應該生成下載鏈接")
        
        self.recorder.log_event("test_save_load_success")
    
    def test_error_handling(self):
        """測試錯誤處理"""
        self.recorder.log_event("test_error_handling_start")
        
        try:
            # 嘗試在沒有發牌的情況下放置牌
            self.streamlit.click_button("放置牌")
            time.sleep(1)
            
            # 應該顯示錯誤或沒有反應
            error_message = self.streamlit.get_alert_message("error")
            # 根據實際實現調整斷言
            
        except Exception as e:
            self.recorder.log_event("expected_error", {"error": str(e)})
        
        self.recorder.log_event("test_error_handling_success")
    
    def test_ui_responsiveness(self):
        """測試 UI 響應性"""
        self.recorder.log_event("test_ui_responsiveness_start")
        
        # 測試快速連續操作
        self.game.deal_initial_cards()
        
        # 快速點擊多張牌
        cards = self.game.get_cards(TestConfig.GAME_SELECTORS["card"])
        for i, card in enumerate(cards[:3]):
            card.click()
            time.sleep(0.1)
        
        # 測試頁面是否仍然響應
        self.streamlit.click_button("獲取 AI 建議")
        
        self.recorder.log_event("test_ui_responsiveness_success")

class TestGameScenarios(unittest.TestCase):
    """遊戲場景測試"""
    
    @classmethod
    def setUpClass(cls):
        """測試類設置"""
        cls.driver = WebDriverManager.create_driver()
        cls.base_url = TestConfig.BASE_URL
    
    @classmethod
    def tearDownClass(cls):
        """測試類清理"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def setUp(self):
        """測試設置"""
        self.driver.get(self.base_url)
        self.streamlit = StreamlitHelper(self.driver)
        self.game = GameHelper(self.driver)
        self.recorder = TestRecorder(self._testMethodName)
        
        self.recorder.start()
        self.streamlit.wait_for_app_loaded()
        self.game.start_new_game()
    
    def test_fantasy_land_scenario(self):
        """測試 Fantasy Land 場景"""
        self.recorder.log_event("test_fantasy_land_start")
        
        # 發牌並手動放置以達到 Fantasy Land
        self.game.deal_initial_cards()
        
        # 嘗試在前墩放置 QQ+
        # 注意：實際測試中可能需要多次嘗試才能獲得合適的牌
        
        # 使用 AI 建議
        self.game.get_ai_suggestion()
        self.game.apply_ai_suggestion()
        
        # 完成遊戲
        for street in range(1, 5):
            self.game.draw_street(street)
            self.game.get_ai_suggestion()
            self.game.apply_ai_suggestion()
        
        # 檢查是否有 Fantasy Land 提示
        info_messages = self.driver.find_elements_by_css_selector(
            TestConfig.STREAMLIT_SELECTORS["info_message"]
        )
        
        fantasy_land_found = any("Fantasy Land" in msg.text for msg in info_messages)
        
        self.recorder.log_event("test_fantasy_land_complete", {
            "fantasy_land_achieved": fantasy_land_found
        })
    
    def test_foul_prevention(self):
        """測試犯規預防"""
        self.recorder.log_event("test_foul_prevention_start")
        
        # AI 應該避免犯規擺放
        self.game.deal_initial_cards()
        self.game.get_ai_suggestion()
        self.game.apply_ai_suggestion()
        
        # 完成遊戲
        for street in range(1, 5):
            self.game.draw_street(street)
            self.game.get_ai_suggestion()
            self.game.apply_ai_suggestion()
        
        # 檢查是否有犯規
        error_messages = self.driver.find_elements_by_css_selector(
            TestConfig.STREAMLIT_SELECTORS["error_message"]
        )
        
        foul_found = any("犯規" in msg.text for msg in error_messages)
        
        self.assertFalse(foul_found, "AI 不應該導致犯規")
        
        self.recorder.log_event("test_foul_prevention_success")

class TestPerformance(unittest.TestCase):
    """性能測試"""
    
    @classmethod
    def setUpClass(cls):
        """測試類設置"""
        cls.driver = WebDriverManager.create_driver()
        cls.base_url = TestConfig.BASE_URL
    
    @classmethod
    def tearDownClass(cls):
        """測試類清理"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def setUp(self):
        """測試設置"""
        self.driver.get(self.base_url)
        self.streamlit = StreamlitHelper(self.driver)
        self.game = GameHelper(self.driver)
        self.performance = PerformanceMonitor(self.driver)
        self.recorder = TestRecorder(self._testMethodName)
        
        self.recorder.start()
        self.streamlit.wait_for_app_loaded()
    
    def test_page_load_performance(self):
        """測試頁面加載性能"""
        metrics = self.performance.measure_page_load()
        
        self.assertLess(
            metrics["page_load_time"] * 1000,
            TestConfig.PERFORMANCE_CONFIG["max_page_load_time"],
            f"頁面加載時間過長: {metrics['page_load_time']:.2f}秒"
        )
        
        self.recorder.log_event("page_load_performance", metrics)
    
    def test_ai_computation_performance(self):
        """測試 AI 計算性能"""
        self.game.start_new_game()
        self.game.deal_initial_cards()
        
        # 測試不同模擬次數下的性能
        simulation_counts = [1000, 10000, 50000]
        
        for count in simulation_counts:
            self.streamlit.set_slider("MCTS 模擬次數", count)
            time.sleep(1)
            
            result, metric = self.performance.measure_action(
                f"ai_suggestion_{count}",
                lambda: self.game.get_ai_suggestion()
            )
            
            self.recorder.log_event(f"ai_performance_{count}", metric)
            
            # 重置遊戲狀態
            self.game.start_new_game()
            self.game.deal_initial_cards()
    
    def test_stress_test(self):
        """壓力測試"""
        iterations = min(TestConfig.PERFORMANCE_CONFIG["stress_test_iterations"], 10)
        
        for i in range(iterations):
            self.recorder.log_event(f"stress_test_iteration_{i}")
            
            # 執行一輪完整遊戲
            self.game.start_new_game()
            self.game.deal_initial_cards()
            
            # 使用較低的模擬次數以加快測試
            self.streamlit.set_slider("MCTS 模擬次數", 1000)
            
            self.game.get_ai_suggestion()
            self.game.apply_ai_suggestion()
            
            # 簡化的街道測試
            for street in range(1, 3):  # 只測試前兩街
                self.game.draw_street(street)
                self.game.get_ai_suggestion()
                self.game.apply_ai_suggestion()
        
        # 生成性能報告
        report = self.performance.generate_report()
        self.recorder.log_event("stress_test_complete", report)
        
        # 檢查平均響應時間
        avg_duration = report["summary"]["average_duration"]
        self.assertLess(avg_duration, 5.0, f"平均響應時間過長: {avg_duration:.2f}秒")

if __name__ == "__main__":
    unittest.main(verbosity=2)