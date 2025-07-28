#!/usr/bin/env python3
"""
運行所有測試並生成覆蓋率報告

使用方法：
    python run_tests_with_coverage.py
"""

import sys
import os
import subprocess
import coverage
import unittest
from datetime import datetime

# 添加項目路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def run_coverage_analysis():
    """運行測試覆蓋率分析"""
    print("=" * 80)
    print("OFC Solver Test Suite - Coverage Report")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 創建覆蓋率對象
    cov = coverage.Coverage(
        source=['src'],
        omit=[
            '*/tests/*',
            '*/test_*',
            '*/__pycache__/*',
            '*/venv/*',
            '*/examples/*',
            '*/gui/*'
        ]
    )
    
    # 開始覆蓋率測量
    cov.start()
    
    # 發現並運行所有測試
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 停止覆蓋率測量
    cov.stop()
    cov.save()
    
    # 生成覆蓋率報告
    print("\n" + "=" * 80)
    print("COVERAGE REPORT")
    print("=" * 80)
    
    # 控制台報告
    print("\n📊 Overall Coverage:")
    cov.report(show_missing=True)
    
    # HTML報告
    html_dir = os.path.join(project_root, 'htmlcov')
    cov.html_report(directory=html_dir)
    print(f"\n📄 HTML report generated at: {html_dir}/index.html")
    
    # 檢查關鍵模組的覆蓋率
    print("\n🔍 Critical Module Coverage:")
    critical_modules = [
        'src/ofc_solver.py',
        'src/core/domain/card.py',
        'src/core/domain/game_state.py',
        'src/core/algorithms/mcts_node.py'
    ]
    
    for module in critical_modules:
        try:
            analysis = cov.analysis2(module)
            if analysis:
                statements = analysis[1]
                missing = analysis[3]
                coverage_pct = ((len(statements) - len(missing)) / len(statements)) * 100 if statements else 0
                
                status = "✅" if coverage_pct >= 80 else "⚠️" if coverage_pct >= 60 else "❌"
                print(f"{status} {module}: {coverage_pct:.1f}%")
        except Exception as e:
            print(f"❓ {module}: Unable to analyze ({str(e)})")
    
    # 總體覆蓋率
    try:
        # cov.report() might return None or a float/int
        total_coverage = cov.report(show_missing=False)
        if total_coverage is None:
            total_coverage = 0.0
        else:
            # Ensure it's a float
            total_coverage = float(total_coverage)
    except Exception as e:
        print(f"Warning: Unable to calculate total coverage: {e}")
        total_coverage = 0.0
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # 測試結果總結
    print(f"\n📋 Test Results:")
    print(f"   Total tests run: {result.testsRun}")
    print(f"   ✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Failed: {len(result.failures)}")
    print(f"   💥 Errors: {len(result.errors)}")
    
    # 覆蓋率總結
    print(f"\n📊 Coverage Summary:")
    print(f"   Overall coverage: {total_coverage:.1f}%")
    
    if total_coverage >= 80:
        print(f"   Status: ✅ Excellent (>= 80%)")
    elif total_coverage >= 60:
        print(f"   Status: ⚠️  Good (>= 60%)")
    else:
        print(f"   Status: ❌ Needs improvement (< 60%)")
    
    # 性能測試提醒
    print(f"\n⚡ Performance Tests:")
    print(f"   Note: Performance benchmarks may vary based on system specs")
    print(f"   Run 'pytest tests/test_performance_benchmark.py -v' for detailed benchmarks")
    
    print(f"\n🏁 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 返回是否所有測試通過且覆蓋率達標
    tests_passed = len(result.failures) == 0 and len(result.errors) == 0
    coverage_ok = total_coverage >= 80
    
    return tests_passed and coverage_ok


def run_specific_test_suite(suite_name):
    """運行特定的測試套件"""
    test_files = {
        'joker': 'tests/test_joker_system.py',
        'performance': 'tests/test_performance_benchmark.py',
        'street': 'tests/test_street_solver.py'
    }
    
    if suite_name in test_files:
        print(f"\n🎯 Running {suite_name} test suite...")
        subprocess.run([sys.executable, test_files[suite_name], '-v'])
    else:
        print(f"❌ Unknown test suite: {suite_name}")
        print(f"   Available suites: {', '.join(test_files.keys())}")


def main():
    """主函數"""
    if len(sys.argv) > 1:
        # 運行特定測試套件
        suite_name = sys.argv[1]
        run_specific_test_suite(suite_name)
    else:
        # 運行所有測試並生成覆蓋率報告
        success = run_coverage_analysis()
        
        # 設置退出碼
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()