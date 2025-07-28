"""
OFC Solver - 主求解器介面
使用真正的 MCTS 整合而不是模擬實現
"""

import time
import uuid
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .logging_config import get_solver_logger, get_performance_logger, LogContext
from .ofc_solver_integration import OFCSolverIntegration, SolveResult as IntegrationResult
from .validation import validate_game_state
from .core.domain import GameState as DomainGameState, Street, Card as DomainCard


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
    """OFC 求解器主類 - 使用真正的 MCTS 整合"""
    
    def __init__(self, 
                 threads: int = 4,
                 time_limit: float = 30.0,
                 simulations_limit: int = 100000):
        self.threads = threads
        self.time_limit = time_limit
        self.simulations_limit = simulations_limit
        
        # 創建 MCTS 整合實例
        self.integration = OFCSolverIntegration(
            threads=threads,
            time_limit=time_limit,
            simulations_limit=simulations_limit
        )
        
        # 獲取日誌器
        self.logger = get_solver_logger()
        self.perf_logger = get_performance_logger("solver")
        
        # 記錄初始化
        self.logger.info(
            "OFC Solver initialized with real MCTS integration",
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
                    
                    # 轉換為領域 GameState
                    domain_state = self._convert_to_domain_state(game_state)
                    
                    # 使用真正的 MCTS 整合求解
                    integration_result = self.integration.solve(domain_state, options)
                    
                    # 轉換結果格式
                    result = SolveResult(
                        best_placement=integration_result.best_placement,
                        expected_score=integration_result.expected_score,
                        confidence=integration_result.confidence,
                        simulations=integration_result.simulations,
                        time_taken=integration_result.time_taken,
                        top_actions=integration_result.top_actions
                    )
                    
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
    
    def _validate_game_state(self, game_state: GameState, log_ctx: LogContext):
        """驗證遊戲狀態"""
        try:
            # 使用驗證模塊進行驗證
            validate_game_state(game_state)
            log_ctx.log("debug", "Game state validation passed")
        except ValueError as e:
            log_ctx.log("error", f"Game state validation failed: {str(e)}")
            raise
    
    def _convert_to_domain_state(self, simple_state: GameState) -> DomainGameState:
        """將簡單的 GameState 轉換為領域 GameState"""
        # 創建領域遊戲狀態
        domain_state = DomainGameState()
        
        # 設置當前街道（如果是初始5張牌）
        if len(simple_state.current_cards) == 5 and not simple_state.front_hand and not simple_state.middle_hand and not simple_state.back_hand:
            domain_state.current_street = Street.INITIAL
        else:
            # 根據已擺放的牌數判斷街道
            total_placed = len(simple_state.front_hand) + len(simple_state.middle_hand) + len(simple_state.back_hand)
            if total_placed < 5:
                domain_state.current_street = Street.INITIAL
            else:
                domain_state.current_street = Street.FIRST + ((total_placed - 5) // 2)
        
        # 設置當前手牌
        domain_state.current_hand = [
            DomainCard.from_string(f"{card.rank}{card.suit}")
            for card in simple_state.current_cards
        ]
        
        # 設置玩家擺放
        if hasattr(domain_state, 'player_arrangement'):
            for card in simple_state.front_hand:
                domain_card = DomainCard.from_string(f"{card.rank}{card.suit}")
                domain_state.player_arrangement.add_card_to_hand('front', domain_card)
            
            for card in simple_state.middle_hand:
                domain_card = DomainCard.from_string(f"{card.rank}{card.suit}")
                domain_state.player_arrangement.add_card_to_hand('middle', domain_card)
                
            for card in simple_state.back_hand:
                domain_card = DomainCard.from_string(f"{card.rank}{card.suit}")
                domain_state.player_arrangement.add_card_to_hand('back', domain_card)
        
        return domain_state


# 為了兼容性，導出工廠函數
def create_solver(**kwargs):
    """創建求解器實例"""
    return OFCSolver(**kwargs)


# 導出接口
__all__ = ['OFCSolver', 'create_solver', 'SolveResult', 'GameState', 'Card']