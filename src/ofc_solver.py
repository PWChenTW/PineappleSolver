"""
OFC Solver 主求解器實現（帶結構化日誌）

這是一個示例實現，展示如何整合結構化日誌系統
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import random
import uuid

from .logging_config import (
    get_solver_logger, 
    get_performance_logger,
    LogContext
)


@dataclass
class Card:
    """撲克牌類"""
    rank: str  # 2-9, T, J, Q, K, A
    suit: str  # s, h, d, c
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return str(self)


@dataclass
class GameState:
    """遊戲狀態"""
    current_cards: List[Card]
    front_hand: List[Card]
    middle_hand: List[Card]  
    back_hand: List[Card]
    remaining_cards: int
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式（用於日誌）"""
        return {
            'current_cards': len(self.current_cards),
            'front_hand': len(self.front_hand),
            'middle_hand': len(self.middle_hand),
            'back_hand': len(self.back_hand),
            'remaining_cards': self.remaining_cards
        }


@dataclass
class SolveResult:
    """求解結果"""
    best_placement: Dict[str, str]  # card -> position
    expected_score: float
    confidence: float
    simulations: int
    time_taken: float
    top_actions: List[Dict[str, Any]]


class OFCSolver:
    """OFC 求解器主類"""
    
    def __init__(self, 
                 threads: int = 4,
                 time_limit: float = 30.0,
                 simulations_limit: int = 100000):
        self.threads = threads
        self.time_limit = time_limit
        self.simulations_limit = simulations_limit
        
        # 獲取日誌器
        self.logger = get_solver_logger()
        self.perf_logger = get_performance_logger("solver")
        
        # 記錄初始化
        self.logger.info(
            "OFC Solver initialized",
            extra={
                'component': 'solver',
                'context': {
                    'threads': threads,
                    'time_limit': time_limit,
                    'simulations_limit': simulations_limit
                }
            }
        )
    
    def solve(self, game_state: GameState, 
              options: Optional[Dict[str, Any]] = None) -> SolveResult:
        """
        求解 OFC 局面
        
        Args:
            game_state: 當前遊戲狀態
            options: 求解選項
            
        Returns:
            求解結果
        """
        # 使用性能日誌裝飾器
        @self.perf_logger.log_timing("solve")
        def _solve():
            request_id = str(uuid.uuid4())
            
            # 創建日誌上下文
            with LogContext(self.logger, request_id=request_id, 
                           operation="solve") as log_ctx:
                
                # 記錄求解開始
                log_ctx.log("info", "Starting OFC solve", 
                           game_state=game_state.to_dict(),
                           options=options or {})
                
                try:
                    # 驗證輸入
                    self._validate_game_state(game_state, log_ctx)
                    
                    # 執行 MCTS 搜索（這裡是模擬）
                    result = self._run_mcts_search(game_state, options, log_ctx)
                    
                    # 記錄成功
                    log_ctx.log("info", "Solve completed successfully",
                               expected_score=result.expected_score,
                               simulations=result.simulations,
                               time_taken=result.time_taken)
                    
                    return result
                    
                except Exception as e:
                    # 記錄錯誤
                    log_ctx.log("error", f"Solve failed: {str(e)}",
                               error_type=type(e).__name__)
                    raise
        
        return _solve()
    
    def _validate_game_state(self, game_state: GameState, 
                           log_ctx: LogContext) -> None:
        """驗證遊戲狀態"""
        log_ctx.log("debug", "Validating game state")
        
        # 檢查手牌數量
        total_cards = (len(game_state.front_hand) + 
                      len(game_state.middle_hand) + 
                      len(game_state.back_hand) +
                      len(game_state.current_cards))
        
        if total_cards > 13:
            raise ValueError(f"Too many cards: {total_cards}")
        
        # 檢查每手牌的限制
        if len(game_state.front_hand) > 3:
            raise ValueError("Front hand cannot have more than 3 cards")
        if len(game_state.middle_hand) > 5:
            raise ValueError("Middle hand cannot have more than 5 cards")
        if len(game_state.back_hand) > 5:
            raise ValueError("Back hand cannot have more than 5 cards")
        
        log_ctx.log("debug", "Game state validation passed")
    
    def _run_mcts_search(self, game_state: GameState, 
                        options: Optional[Dict[str, Any]],
                        log_ctx: LogContext) -> SolveResult:
        """運行 MCTS 搜索（模擬實現）"""
        start_time = time.time()
        
        # 獲取選項
        options = options or {}
        time_limit = options.get('time_limit', self.time_limit)
        
        # 記錄搜索開始
        log_ctx.log("info", "Starting MCTS search",
                   time_limit=time_limit,
                   threads=self.threads)
        
        # 模擬搜索過程
        simulations = 0
        best_placement = {}
        
        # 模擬一些放置決策
        for card in game_state.current_cards:
            # 隨機選擇位置（實際應該用 MCTS）
            position = random.choice(['front', 'middle', 'back'])
            best_placement[str(card)] = position
            
        # 模擬運行時間
        while time.time() - start_time < min(time_limit, 1.0):  # 最多1秒模擬
            simulations += random.randint(1000, 5000)
            time.sleep(0.1)
            
            # 定期記錄進度
            if simulations % 10000 == 0:
                log_ctx.log("debug", "MCTS progress",
                           simulations=simulations,
                           elapsed=time.time() - start_time)
        
        elapsed_time = time.time() - start_time
        
        # 生成模擬結果
        expected_score = random.uniform(-20, 100)
        confidence = min(simulations / 100000, 0.99)
        
        # 生成 top actions
        top_actions = []
        for i, (card, position) in enumerate(best_placement.items()):
            if i < 3:  # 只返回前3個動作
                top_actions.append({
                    'card': card,
                    'position': position,
                    'visits': random.randint(10000, 50000),
                    'avg_reward': random.uniform(-5, 20)
                })
        
        # 記錄搜索完成
        log_ctx.log("info", "MCTS search completed",
                   simulations=simulations,
                   elapsed_time=elapsed_time,
                   expected_score=expected_score)
        
        return SolveResult(
            best_placement=best_placement,
            expected_score=expected_score,
            confidence=confidence,
            simulations=simulations,
            time_taken=elapsed_time,
            top_actions=top_actions
        )