#!/usr/bin/env python3
"""
GUI 測試執行腳本
運行所有 GUI 自動化測試並生成報告
"""

import os
import sys
import time
import argparse
import unittest
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any
import xml.etree.ElementTree as ET

from test_gui_config import TestConfig, BrowserType

class StreamlitAppManager:
    """管理 Streamlit 應用的啟動和關閉"""
    
    def __init__(self, app_path: str = "pineapple_ofc_gui.py"):
        self.app_path = app_path
        self.process = None
        self.port = 8501
    
    def start(self):
        """啟動 Streamlit 應用"""
        print(f"Starting Streamlit app on port {self.port}...")
        
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            self.app_path,
            "--server.port", str(self.port),
            "--server.headless", "true",
            "--server.address", "localhost"
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待應用啟動
        time.sleep(5)
        
        # 檢查應用是否成功啟動
        if self.process.poll() is not None:
            stdout, stderr = self.process.communicate()
            raise RuntimeError(f"Failed to start Streamlit app:\n{stderr.decode()}")
        
        print(f"Streamlit app started successfully on http://localhost:{self.port}")
    
    def stop(self):
        """停止 Streamlit 應用"""
        if self.process:
            print("Stopping Streamlit app...")
            self.process.terminate()
            self.process.wait(timeout=10)
            self.process = None
            print("Streamlit app stopped")

class TestReportGenerator:
    """測試報告生成器"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def add_result(self, result: unittest.TestResult):
        """添加測試結果"""
        self.results.append(result)
    
    def generate_html_report(self, output_path: str):
        """生成 HTML 報告"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GUI 測試報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-case {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background-color: #d4edda; }}
        .failure {{ background-color: #f8d7da; }}
        .error {{ background-color: #f8d7da; }}
        .skip {{ background-color: #fff3cd; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e9ecef; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>GUI 自動化測試報告</h1>
        <p>執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>測試環境: {TestConfig.BROWSER.value} | {'Headless' if TestConfig.HEADLESS else 'GUI'} | {'CI' if TestConfig.IS_CI else 'Local'}</p>
    </div>
"""
        
        # 添加測試摘要
        total_tests = sum(result.testsRun for result in self.results)
        total_failures = sum(len(result.failures) for result in self.results)
        total_errors = sum(len(result.errors) for result in self.results)
        total_skipped = sum(len(result.skipped) for result in self.results)
        
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        
        html_content += f"""
    <div class="summary">
        <h2>測試摘要</h2>
        <div class="metric">總測試: {total_tests}</div>
        <div class="metric">成功: {total_tests - total_failures - total_errors - total_skipped}</div>
        <div class="metric">失敗: {total_failures}</div>
        <div class="metric">錯誤: {total_errors}</div>
        <div class="metric">跳過: {total_skipped}</div>
        <div class="metric">成功率: {success_rate:.1f}%</div>
    </div>
"""
        
        # 添加詳細測試結果
        html_content += """
    <h2>詳細測試結果</h2>
    <table>
        <tr>
            <th>測試類</th>
            <th>測試方法</th>
            <th>狀態</th>
            <th>執行時間</th>
            <th>錯誤信息</th>
        </tr>
"""
        
        for result in self.results:
            # 處理成功的測試
            for test in result.testsRun:
                html_content += f"""
        <tr class="success">
            <td>{test.__class__.__name__}</td>
            <td>{test._testMethodName}</td>
            <td>✅ 成功</td>
            <td>-</td>
            <td>-</td>
        </tr>
"""
            
            # 處理失敗的測試
            for test, traceback in result.failures:
                html_content += f"""
        <tr class="failure">
            <td>{test.__class__.__name__}</td>
            <td>{test._testMethodName}</td>
            <td>❌ 失敗</td>
            <td>-</td>
            <td><pre>{traceback}</pre></td>
        </tr>
"""
            
            # 處理錯誤的測試
            for test, traceback in result.errors:
                html_content += f"""
        <tr class="error">
            <td>{test.__class__.__name__}</td>
            <td>{test._testMethodName}</td>
            <td>❌ 錯誤</td>
            <td>-</td>
            <td><pre>{traceback}</pre></td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report generated: {output_path}")
    
    def generate_junit_xml(self, output_path: str):
        """生成 JUnit XML 報告（用於 CI/CD）"""
        testsuites = ET.Element('testsuites')
        
        for idx, result in enumerate(self.results):
            testsuite = ET.SubElement(testsuites, 'testsuite')
            testsuite.set('name', f'TestSuite_{idx}')
            testsuite.set('tests', str(result.testsRun))
            testsuite.set('failures', str(len(result.failures)))
            testsuite.set('errors', str(len(result.errors)))
            testsuite.set('skipped', str(len(result.skipped)))
            
            # 添加測試用例
            for test in result.testsRun:
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('classname', test.__class__.__name__)
                testcase.set('name', test._testMethodName)
            
            # 添加失敗的測試
            for test, traceback in result.failures:
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('classname', test.__class__.__name__)
                testcase.set('name', test._testMethodName)
                
                failure = ET.SubElement(testcase, 'failure')
                failure.set('message', 'Test failed')
                failure.text = traceback
            
            # 添加錯誤的測試
            for test, traceback in result.errors:
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('classname', test.__class__.__name__)
                testcase.set('name', test._testMethodName)
                
                error = ET.SubElement(testcase, 'error')
                error.set('message', 'Test error')
                error.text = traceback
        
        tree = ET.ElementTree(testsuites)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        print(f"JUnit XML report generated: {output_path}")

def run_tests(test_modules: List[str], browser: str = None, headless: bool = None):
    """運行測試"""
    # 設置環境變量
    if browser:
        os.environ["TEST_BROWSER"] = browser
    if headless is not None:
        os.environ["TEST_HEADLESS"] = "true" if headless else "false"
    
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 加載測試模組
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            suite.addTests(loader.loadTestsFromModule(module))
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='運行 GUI 自動化測試')
    parser.add_argument(
        '--browser',
        choices=['chrome', 'firefox', 'edge', 'safari'],
        default='chrome',
        help='測試瀏覽器'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='使用 headless 模式'
    )
    parser.add_argument(
        '--no-app',
        action='store_true',
        help='不自動啟動 Streamlit 應用（假設已在運行）'
    )
    parser.add_argument(
        '--suite',
        choices=['all', 'basic', 'scenarios', 'performance'],
        default='all',
        help='要運行的測試套件'
    )
    parser.add_argument(
        '--report-dir',
        default='test_reports',
        help='報告輸出目錄'
    )
    parser.add_argument(
        '--ci',
        action='store_true',
        help='CI 模式（生成 JUnit XML）'
    )
    
    args = parser.parse_args()
    
    # 確保報告目錄存在
    os.makedirs(args.report_dir, exist_ok=True)
    
    # 設置測試模組
    test_modules = []
    if args.suite == 'all':
        test_modules = ['test_gui_automation']
    elif args.suite == 'basic':
        test_modules = ['test_gui_automation.TestPineappleGUI']
    elif args.suite == 'scenarios':
        test_modules = ['test_gui_automation.TestGameScenarios']
    elif args.suite == 'performance':
        test_modules = ['test_gui_automation.TestPerformance']
    
    # 啟動 Streamlit 應用（如果需要）
    app_manager = None
    if not args.no_app:
        app_manager = StreamlitAppManager()
        try:
            app_manager.start()
        except Exception as e:
            print(f"Error starting Streamlit app: {e}")
            return 1
    
    try:
        # 運行測試
        print(f"\nRunning {args.suite} tests with {args.browser} browser...")
        print(f"Headless mode: {args.headless}")
        print("-" * 80)
        
        result = run_tests(test_modules, args.browser, args.headless)
        
        # 生成報告
        report_generator = TestReportGenerator()
        report_generator.add_result(result)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # HTML 報告
        html_report_path = os.path.join(args.report_dir, f'gui_test_report_{timestamp}.html')
        report_generator.generate_html_report(html_report_path)
        
        # JUnit XML 報告（用於 CI）
        if args.ci:
            xml_report_path = os.path.join(args.report_dir, f'junit_report_{timestamp}.xml')
            report_generator.generate_junit_xml(xml_report_path)
        
        # 返回狀態碼
        return 0 if result.wasSuccessful() else 1
        
    finally:
        # 停止 Streamlit 應用
        if app_manager:
            app_manager.stop()

if __name__ == "__main__":
    sys.exit(main())