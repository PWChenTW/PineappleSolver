#!/usr/bin/env python3
"""
優化版 OFC Solver 性能測試
測試 100k MCTS 模擬的性能表現
"""

import time
import statistics
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any
import multiprocessing as mp

from ofc_solver_optimized import (
    OptimizedStreetByStreetSolver, ParallelMCTS, CacheManager,
    PineappleState, Card
)
from ofc_solver_joker import create_full_deck


class PerformanceBenchmark:
    """性能基準測試類"""
    
    def __init__(self):
        self.results = []
    
    def run_benchmark(self, name: str, test_func, iterations: int = 5):
        """運行基準測試"""
        print(f"\n=== {name} ===")
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            result = test_func()
            elapsed = time.time() - start_time
            times.append(elapsed)
            print(f"  迭代 {i+1}: {elapsed:.3f}秒")
        
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        
        benchmark_result = {
            'name': name,
            'times': times,
            'average': avg_time,
            'std_dev': std_dev,
            'min': min(times),
            'max': max(times)
        }
        
        self.results.append(benchmark_result)
        
        print(f"  平均: {avg_time:.3f}秒 (±{std_dev:.3f})")
        print(f"  最快: {min(times):.3f}秒, 最慢: {max(times):.3f}秒")
        
        return benchmark_result
    
    def compare_results(self):
        """比較測試結果"""
        if not self.results:
            return
        
        print("\n=== 性能比較總結 ===")
        print(f"{'測試名稱':<30} {'平均時間':<10} {'標準差':<10} {'最快':<10} {'最慢':<10}")
        print("-" * 70)
        
        for result in self.results:
            print(f"{result['name']:<30} "
                  f"{result['average']:<10.3f} "
                  f"{result['std_dev']:<10.3f} "
                  f"{result['min']:<10.3f} "
                  f"{result['max']:<10.3f}")
    
    def plot_results(self):
        """繪製結果圖表"""
        if not self.results:
            return
        
        names = [r['name'] for r in self.results]
        averages = [r['average'] for r in self.results]
        std_devs = [r['std_dev'] for r in self.results]
        
        plt.figure(figsize=(10, 6))
        plt.bar(names, averages, yerr=std_devs, capsize=5)
        plt.xlabel('測試類型')
        plt.ylabel('時間 (秒)')
        plt.title('OFC Solver 性能測試結果')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('performance_results.png')
        print("\n性能圖表已保存為 performance_results.png")


def test_mcts_scaling():
    """測試 MCTS 性能隨模擬次數的擴展性"""
    print("\n=== MCTS 擴展性測試 ===")
    
    # 準備測試數據
    deck = create_full_deck(include_jokers=True)
    initial_cards = deck[:5]
    remaining_cards = deck[5:25]
    
    # 測試不同的模擬次數
    simulation_counts = [1000, 5000, 10000, 25000, 50000, 100000]
    times = []
    speeds = []
    
    for num_sims in simulation_counts:
        print(f"\n測試 {num_sims:,} 次模擬:")
        
        # 創建 MCTS 實例
        mcts = ParallelMCTS(num_simulations=num_sims)
        initial_state = PineappleState()
        
        # 運行測試
        start_time = time.time()
        result = mcts.search(initial_state, remaining_cards, time_limit=10.0)
        elapsed = time.time() - start_time
        
        actual_sims = result['stats']['total_simulations']
        sim_speed = actual_sims / elapsed if elapsed > 0 else 0
        
        times.append(elapsed)
        speeds.append(sim_speed)
        
        print(f"  時間: {elapsed:.3f}秒")
        print(f"  實際模擬: {actual_sims:,}")
        print(f"  速度: {sim_speed:,.0f} 模擬/秒")
    
    # 繪製擴展性圖表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 時間 vs 模擬次數
    ax1.plot(simulation_counts, times, 'b-o')
    ax1.set_xlabel('模擬次數')
    ax1.set_ylabel('時間 (秒)')
    ax1.set_title('MCTS 運行時間')
    ax1.set_xscale('log')
    ax1.grid(True)
    
    # 速度 vs 模擬次數
    ax2.plot(simulation_counts, speeds, 'r-o')
    ax2.set_xlabel('模擬次數')
    ax2.set_ylabel('模擬速度 (次/秒)')
    ax2.set_title('MCTS 模擬速度')
    ax2.set_xscale('log')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('mcts_scaling.png')
    print("\nMCTS 擴展性圖表已保存為 mcts_scaling.png")


def test_parallel_efficiency():
    """測試並行效率"""
    print("\n=== 並行效率測試 ===")
    
    num_simulations = 50000
    process_counts = [1, 2, 4, 8]
    
    # 準備測試數據
    deck = create_full_deck(include_jokers=True)
    initial_cards = deck[:5]
    remaining_cards = deck[5:25]
    initial_state = PineappleState()
    
    results = []
    
    for num_processes in process_counts:
        if num_processes > mp.cpu_count():
            continue
            
        print(f"\n使用 {num_processes} 個進程:")
        
        # 創建 MCTS 實例
        mcts = ParallelMCTS(
            num_simulations=num_simulations,
            num_processes=num_processes
        )
        
        # 運行測試
        times = []
        for _ in range(3):
            start_time = time.time()
            result = mcts.search(initial_state, remaining_cards, time_limit=10.0)
            elapsed = time.time() - start_time
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        speedup = times[0] / avg_time if len(results) > 0 else 1.0
        
        results.append({
            'processes': num_processes,
            'time': avg_time,
            'speedup': speedup
        })
        
        print(f"  平均時間: {avg_time:.3f}秒")
        if len(results) > 1:
            print(f"  加速比: {speedup:.2f}x")
    
    # 繪製並行效率圖表
    processes = [r['processes'] for r in results]
    times = [r['time'] for r in results]
    speedups = [r.get('speedup', 1.0) for r in results]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 時間 vs 進程數
    ax1.plot(processes, times, 'b-o')
    ax1.set_xlabel('進程數')
    ax1.set_ylabel('時間 (秒)')
    ax1.set_title('並行運行時間')
    ax1.grid(True)
    
    # 加速比 vs 進程數
    ax2.plot(processes, speedups, 'r-o')
    ax2.plot(processes, processes, 'k--', label='理想加速比')
    ax2.set_xlabel('進程數')
    ax2.set_ylabel('加速比')
    ax2.set_title('並行加速比')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('parallel_efficiency.png')
    print("\n並行效率圖表已保存為 parallel_efficiency.png")


def test_cache_effectiveness():
    """測試緩存效果"""
    print("\n=== 緩存效果測試 ===")
    
    # 創建帶緩存的求解器
    solver_with_cache = OptimizedStreetByStreetSolver(
        include_jokers=True,
        num_simulations=10000
    )
    
    # 使用相同的初始手牌多次求解
    initial_cards = solver_with_cache.deal_random_initial()
    
    print("測試緩存命中率:")
    for i in range(5):
        print(f"\n第 {i+1} 次求解:")
        start_time = time.time()
        result = solver_with_cache.solve_game(
            initial_five_cards=initial_cards,
            use_mcts_for_initial=True
        )
        elapsed = time.time() - start_time
        
        cache_stats = result['performance']['cache_stats']
        print(f"  時間: {elapsed:.3f}秒")
        print(f"  緩存大小: {cache_stats['size']}")
        print(f"  命中率: {cache_stats['hit_rate']:.2%}")


def test_pruning_effectiveness():
    """測試剪枝效果"""
    print("\n=== 剪枝效果測試 ===")
    
    # 準備測試數據
    deck = create_full_deck(include_jokers=True)
    initial_state = PineappleState()
    
    # 測試不同的剪枝策略
    strategies = [
        ("無剪枝", lambda s, c, p: True),
        ("基礎剪枝", lambda s, c, p: not (c.is_joker() and p == 'back')),
        ("激進剪枝", lambda s, c, p: (
            not (c.is_joker() and p == 'back') and
            not (not c.is_joker() and p == 'back' and c.rank in ['2', '3', '4', '5'])
        ))
    ]
    
    for name, pruning_func in strategies:
        print(f"\n{name}:")
        
        # 創建自定義 MCTS
        mcts = ParallelMCTS(num_simulations=10000)
        mcts._is_reasonable_placement = pruning_func
        
        start_time = time.time()
        result = mcts.search(initial_state, deck[:20], time_limit=5.0)
        elapsed = time.time() - start_time
        
        stats = result['stats']
        print(f"  時間: {elapsed:.3f}秒")
        print(f"  模擬次數: {stats['total_simulations']:,}")
        print(f"  速度: {stats['simulations_per_second']:,.0f} 模擬/秒")


def main():
    """主測試函數"""
    print("=" * 70)
    print("OFC 優化求解器性能測試")
    print("=" * 70)
    
    # 創建基準測試器
    benchmark = PerformanceBenchmark()
    
    # 測試1：基礎 100k 模擬性能
    def test_100k_basic():
        solver = OptimizedStreetByStreetSolver(
            include_jokers=True,
            num_simulations=100000
        )
        initial_cards = solver.deal_random_initial()
        player_state = PineappleState()
        remaining_deck = solver.full_deck.copy()
        for card in initial_cards:
            remaining_deck.remove(card)
        
        return solver._solve_initial_with_mcts(
            initial_cards, player_state, remaining_deck
        )
    
    benchmark.run_benchmark("100k 模擬 (基礎)", test_100k_basic, iterations=3)
    
    # 測試2：50k 模擬性能
    def test_50k():
        solver = OptimizedStreetByStreetSolver(
            include_jokers=True,
            num_simulations=50000
        )
        initial_cards = solver.deal_random_initial()
        player_state = PineappleState()
        remaining_deck = solver.full_deck.copy()
        for card in initial_cards:
            remaining_deck.remove(card)
        
        return solver._solve_initial_with_mcts(
            initial_cards, player_state, remaining_deck
        )
    
    benchmark.run_benchmark("50k 模擬", test_50k, iterations=3)
    
    # 測試3：10k 模擬性能
    def test_10k():
        solver = OptimizedStreetByStreetSolver(
            include_jokers=True,
            num_simulations=10000
        )
        initial_cards = solver.deal_random_initial()
        player_state = PineappleState()
        remaining_deck = solver.full_deck.copy()
        for card in initial_cards:
            remaining_deck.remove(card)
        
        return solver._solve_initial_with_mcts(
            initial_cards, player_state, remaining_deck
        )
    
    benchmark.run_benchmark("10k 模擬", test_10k, iterations=5)
    
    # 比較結果
    benchmark.compare_results()
    
    # 額外測試
    test_mcts_scaling()
    test_parallel_efficiency()
    test_cache_effectiveness()
    test_pruning_effectiveness()
    
    print("\n" + "=" * 70)
    print("測試完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()