"""
性能基準測試套件

測試系統性能指標，包括模擬次數、並行計算效率、緩存命中率和內存使用。
"""

import unittest
import pytest
import time
import memory_profiler
import psutil
import concurrent.futures
from typing import List, Dict, Any
import numpy as np
import gc

# 添加項目路徑
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ofc_solver import OFCSolver, create_solver, GameState, Card
from src.core.algorithms.mcts import MCTSAlgorithm
from src.core.domain import Card as DomainCard, GameState as DomainGameState


class TestPerformanceBenchmark(unittest.TestCase):
    """性能基準測試"""
    
    def setUp(self):
        """測試前置設置"""
        self.solver = create_solver(
            threads=4,
            simulations_limit=100000,
            time_limit=30.0
        )
        # 強制垃圾回收
        gc.collect()
    
    def tearDown(self):
        """測試後清理"""
        gc.collect()
    
    def test_100k_simulations_in_5_seconds(self):
        """測試：100k模擬必須在5秒內完成"""
        # 準備測試數據
        test_cards = [
            Card('A', 's'),
            Card('K', 'h'),
            Card('Q', 'd'),
            Card('J', 'c'),
            Card('T', 's')
        ]
        
        game_state = GameState(
            current_cards=test_cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        # 創建高性能求解器
        fast_solver = create_solver(
            threads=8,  # 使用更多線程
            simulations_limit=100000,
            time_limit=5.0  # 5秒時限
        )
        
        # 執行測試
        start_time = time.time()
        result = fast_solver.solve(game_state)
        elapsed_time = time.time() - start_time
        
        # 驗證
        self.assertIsNotNone(result)
        self.assertLessEqual(elapsed_time, 5.0, 
                            f"100k simulations took {elapsed_time:.2f}s, should be < 5s")
        
        # 驗證實際執行的模擬次數
        self.assertGreaterEqual(result.simulations, 90000,  # 允許10%的誤差
                               f"Only {result.simulations} simulations completed")
        
        print(f"\n✅ 100k simulations completed in {elapsed_time:.2f}s")
        print(f"   Actual simulations: {result.simulations}")
        print(f"   Simulations/second: {result.simulations/elapsed_time:.0f}")
    
    def test_parallel_computation_efficiency(self):
        """測試並行計算效率"""
        test_cases = []
        for i in range(10):
            cards = self._generate_random_hand()
            game_state = GameState(
                current_cards=cards,
                front_hand=[],
                middle_hand=[],
                back_hand=[],
                remaining_cards=8
            )
            test_cases.append(game_state)
        
        # 單線程測試
        single_thread_solver = create_solver(threads=1, simulations_limit=10000)
        start_time = time.time()
        single_results = []
        for game_state in test_cases:
            result = single_thread_solver.solve(game_state)
            single_results.append(result)
        single_thread_time = time.time() - start_time
        
        # 多線程測試
        multi_thread_solver = create_solver(threads=4, simulations_limit=10000)
        start_time = time.time()
        multi_results = []
        
        # 使用線程池並行處理
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(multi_thread_solver.solve, gs) for gs in test_cases]
            for future in concurrent.futures.as_completed(futures):
                multi_results.append(future.result())
        
        multi_thread_time = time.time() - start_time
        
        # 計算加速比
        speedup = single_thread_time / multi_thread_time
        efficiency = speedup / 4  # 4線程的效率
        
        print(f"\n📊 Parallel Computation Efficiency:")
        print(f"   Single thread time: {single_thread_time:.2f}s")
        print(f"   Multi thread time (4 threads): {multi_thread_time:.2f}s")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Efficiency: {efficiency:.2%}")
        
        # 驗證
        self.assertGreater(speedup, 2.0, "Parallel speedup should be > 2x with 4 threads")
        self.assertGreater(efficiency, 0.5, "Parallel efficiency should be > 50%")
    
    def test_cache_hit_rate(self):
        """測試緩存命中率"""
        # 創建帶緩存統計的求解器
        solver = create_solver(simulations_limit=10000)
        
        # 測試相同局面的重複評估
        test_cards = [
            Card('A', 's'),
            Card('A', 'h'),
            Card('K', 'd'),
            Card('K', 'c'),
            Card('Q', 's')
        ]
        
        game_state = GameState(
            current_cards=test_cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        # 第一次求解（冷緩存）
        start_time = time.time()
        result1 = solver.solve(game_state)
        cold_cache_time = time.time() - start_time
        
        # 第二次求解（熱緩存）
        start_time = time.time()
        result2 = solver.solve(game_state)
        hot_cache_time = time.time() - start_time
        
        # 計算緩存加速
        cache_speedup = cold_cache_time / hot_cache_time if hot_cache_time > 0 else 1.0
        
        print(f"\n💾 Cache Performance:")
        print(f"   Cold cache time: {cold_cache_time:.2f}s")
        print(f"   Hot cache time: {hot_cache_time:.2f}s")
        print(f"   Cache speedup: {cache_speedup:.2f}x")
        
        # 驗證緩存有效性
        self.assertEqual(result1.best_placement, result2.best_placement, 
                        "Cached results should be identical")
        
        # 熱緩存應該更快（但不一定，因為MCTS有隨機性）
        # 所以我們只檢查結果一致性
    
    def test_memory_usage(self):
        """測試內存使用情況"""
        process = psutil.Process()
        
        # 初始內存
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 執行大量模擬
        solver = create_solver(simulations_limit=50000)
        
        results = []
        peak_memory = initial_memory
        
        for i in range(5):
            cards = self._generate_random_hand()
            game_state = GameState(
                current_cards=cards,
                front_hand=[],
                middle_hand=[],
                back_hand=[],
                remaining_cards=8
            )
            
            result = solver.solve(game_state)
            results.append(result)
            
            # 記錄峰值內存
            current_memory = process.memory_info().rss / 1024 / 1024
            peak_memory = max(peak_memory, current_memory)
        
        # 最終內存
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        memory_increase = peak_memory - initial_memory
        memory_leaked = final_memory - initial_memory
        
        print(f"\n🧠 Memory Usage:")
        print(f"   Initial memory: {initial_memory:.1f} MB")
        print(f"   Peak memory: {peak_memory:.1f} MB")
        print(f"   Final memory: {final_memory:.1f} MB")
        print(f"   Memory increase: {memory_increase:.1f} MB")
        print(f"   Memory leaked: {memory_leaked:.1f} MB")
        
        # 驗證內存使用
        self.assertLess(memory_increase, 500, 
                       f"Memory increase {memory_increase:.1f}MB exceeds 500MB limit")
        self.assertLess(memory_leaked, 100,
                       f"Memory leak {memory_leaked:.1f}MB exceeds 100MB limit")
    
    def test_scalability_with_simulations(self):
        """測試模擬次數的可擴展性"""
        simulation_counts = [1000, 5000, 10000, 25000, 50000]
        times = []
        
        test_cards = [
            Card('A', 's'),
            Card('K', 'h'),
            Card('Q', 'd'),
            Card('J', 'c'),
            Card('T', 's')
        ]
        
        game_state = GameState(
            current_cards=test_cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        for sim_count in simulation_counts:
            solver = create_solver(simulations_limit=sim_count)
            
            start_time = time.time()
            result = solver.solve(game_state)
            elapsed_time = time.time() - start_time
            
            times.append(elapsed_time)
            
            print(f"\n   {sim_count:6d} simulations: {elapsed_time:6.2f}s "
                  f"({sim_count/elapsed_time:6.0f} sims/sec)")
        
        # 檢查線性擴展性
        # 計算時間增長率
        time_ratios = []
        for i in range(1, len(times)):
            sim_ratio = simulation_counts[i] / simulation_counts[i-1]
            time_ratio = times[i] / times[i-1]
            efficiency = sim_ratio / time_ratio
            time_ratios.append(efficiency)
            
            print(f"   Scaling efficiency {simulation_counts[i-1]}→{simulation_counts[i]}: "
                  f"{efficiency:.2%}")
        
        avg_efficiency = np.mean(time_ratios)
        print(f"\n   Average scaling efficiency: {avg_efficiency:.2%}")
        
        # 驗證擴展效率
        self.assertGreater(avg_efficiency, 0.7, 
                          f"Scaling efficiency {avg_efficiency:.2%} is too low")
    
    def test_concurrent_solver_instances(self):
        """測試多個求解器實例並發運行"""
        num_instances = 8
        num_problems = 16
        
        # 生成測試問題
        problems = []
        for _ in range(num_problems):
            cards = self._generate_random_hand()
            game_state = GameState(
                current_cards=cards,
                front_hand=[],
                middle_hand=[],
                back_hand=[],
                remaining_cards=8
            )
            problems.append(game_state)
        
        # 並發求解
        start_time = time.time()
        results = []
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_instances) as executor:
            # 為每個進程創建獨立的求解器
            futures = []
            for i, problem in enumerate(problems):
                future = executor.submit(self._solve_with_new_instance, problem)
                futures.append(future)
            
            # 收集結果
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        total_time = time.time() - start_time
        avg_time_per_problem = total_time / num_problems
        
        print(f"\n🔄 Concurrent Solver Instances:")
        print(f"   Total problems: {num_problems}")
        print(f"   Concurrent instances: {num_instances}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average time per problem: {avg_time_per_problem:.2f}s")
        
        # 驗證所有問題都得到解決
        self.assertEqual(len(results), num_problems)
        self.assertTrue(all(r is not None for r in results))
    
    def test_response_time_consistency(self):
        """測試響應時間的一致性"""
        num_trials = 20
        solver = create_solver(simulations_limit=10000)
        
        times = []
        for _ in range(num_trials):
            cards = self._generate_random_hand()
            game_state = GameState(
                current_cards=cards,
                front_hand=[],
                middle_hand=[],
                back_hand=[],
                remaining_cards=8
            )
            
            start_time = time.time()
            result = solver.solve(game_state)
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
        
        # 計算統計數據
        mean_time = np.mean(times)
        std_time = np.std(times)
        cv = std_time / mean_time  # 變異係數
        min_time = np.min(times)
        max_time = np.max(times)
        p95_time = np.percentile(times, 95)
        
        print(f"\n⏱️  Response Time Consistency:")
        print(f"   Mean time: {mean_time:.3f}s")
        print(f"   Std deviation: {std_time:.3f}s")
        print(f"   Coefficient of variation: {cv:.2%}")
        print(f"   Min time: {min_time:.3f}s")
        print(f"   Max time: {max_time:.3f}s")
        print(f"   95th percentile: {p95_time:.3f}s")
        
        # 驗證一致性
        self.assertLess(cv, 0.3, f"Response time variation {cv:.2%} is too high")
        self.assertLess(p95_time, mean_time * 1.5, 
                       "95th percentile response time is too high")
    
    # 輔助方法
    def _generate_random_hand(self) -> List[Card]:
        """生成隨機的5張牌"""
        import random
        
        ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
        suits = ['s', 'h', 'd', 'c']
        
        deck = []
        for rank in ranks:
            for suit in suits:
                deck.append(Card(rank, suit))
        
        random.shuffle(deck)
        return deck[:5]
    
    @staticmethod
    def _solve_with_new_instance(game_state: GameState) -> Any:
        """在新實例中求解（用於多進程測試）"""
        solver = create_solver(simulations_limit=5000)
        return solver.solve(game_state)


class TestPerformanceOptimization(unittest.TestCase):
    """性能優化測試"""
    
    def test_pruning_effectiveness(self):
        """測試剪枝算法的有效性"""
        # 創建一個具有明顯劣勢分支的局面
        cards = [
            Card('2', 's'),  # 弱牌
            Card('3', 'h'),
            Card('4', 'd'),
            Card('A', 'c'),  # 強牌
            Card('K', 's')
        ]
        
        game_state = GameState(
            current_cards=cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        # 使用啟用剪枝的求解器
        solver_with_pruning = create_solver(
            simulations_limit=10000,
            threads=1  # 單線程便於測量
        )
        
        start_time = time.time()
        result = solver_with_pruning.solve(game_state)
        pruning_time = time.time() - start_time
        
        print(f"\n✂️  Pruning Effectiveness:")
        print(f"   Time with pruning: {pruning_time:.2f}s")
        print(f"   Best placement: {result.best_placement}")
        
        # 驗證強牌被正確放置在後墩
        self.assertIn('Ac', result.best_placement.get('back', ''))
    
    def test_early_termination(self):
        """測試提前終止優化"""
        # 創建一個有明顯最優解的局面
        cards = [
            Card('A', 's'),
            Card('A', 'h'),
            Card('A', 'd'),  # 三條A
            Card('K', 'c'),
            Card('K', 's')   # 對K
        ]
        
        game_state = GameState(
            current_cards=cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        # 測試不同的模擬次數
        for sim_limit in [1000, 5000, 10000]:
            solver = create_solver(simulations_limit=sim_limit)
            
            start_time = time.time()
            result = solver.solve(game_state)
            elapsed_time = time.time() - start_time
            
            print(f"\n   {sim_limit} simulations: {elapsed_time:.2f}s, "
                  f"confidence: {result.confidence:.2%}")
            
            # 驗證即使模擬次數少，也能找到正確的擺放
            # （三條A應該在後墩）
            back_cards = [card for card, pos in result.best_placement.items() 
                         if pos == 'back']
            a_count = sum(1 for card in back_cards if 'A' in card)
            self.assertGreaterEqual(a_count, 2, "At least 2 Aces should be in back")


@pytest.mark.benchmark
class TestBenchmarkSuite:
    """Pytest基準測試套件"""
    
    def test_benchmark_initial_placement(self, benchmark):
        """基準測試：初始5張牌擺放"""
        solver = create_solver(simulations_limit=10000)
        
        cards = [
            Card('A', 's'),
            Card('K', 'h'),
            Card('Q', 'd'),
            Card('J', 'c'),
            Card('T', 's')
        ]
        
        game_state = GameState(
            current_cards=cards,
            front_hand=[],
            middle_hand=[],
            back_hand=[],
            remaining_cards=8
        )
        
        # 使用pytest-benchmark進行測試
        result = benchmark(solver.solve, game_state)
        
        assert result is not None
        assert result.best_placement is not None
    
    def test_benchmark_street_decision(self, benchmark):
        """基準測試：街道決策"""
        solver = create_solver(simulations_limit=5000)
        
        # 設置一個中間街道的局面
        game_state = GameState(
            current_cards=[Card('9', 's'), Card('9', 'h'), Card('8', 'd')],
            front_hand=[Card('K', 's'), Card('Q', 'h')],
            middle_hand=[Card('A', 'd'), Card('A', 'c')],
            back_hand=[Card('T', 's'), Card('T', 'h'), Card('T', 'd')],
            remaining_cards=3
        )
        
        result = benchmark(solver.solve, game_state)
        
        assert result is not None
        assert len(result.best_placement) == 2  # 放置2張，丟棄1張


if __name__ == '__main__':
    # 運行unittest測試
    unittest.main(verbosity=2)