"""
兼容層，讓舊測試能夠運行
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Callable
import logging

# 導入真正的 domain 類
from src.core.domain import GameState as RealGameState
from src.core.algorithms.ofc_mcts import MCTSEngine, MCTSResult
from src.core.algorithms.action_generator import ActionGenerator
from src.core.algorithms.evaluator import StateEvaluator
from src.exceptions import InvalidInputError, TimeoutError, SolverError
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SolverConfig:
    """求解器配置"""
    time_limit: float = 30.0
    num_threads: int = 4
    simulations: int = 100000
    exploration_constant: float = 1.4
    use_cache: bool = True
    use_progressive_widening: bool = True
    use_progressive_bias: bool = True
    use_virtual_loss: bool = True
    use_domain_pruning: bool = True


@dataclass 
class SolveResult:
    """求解結果"""
    move: Any  # Action 對象
    evaluation: float
    confidence: float
    simulations: int
    computation_time_seconds: float
    expected_score: float
    request_id: str
    top_actions: List[Dict[str, Any]]


class OFCSolver:
    """OFC 求解器包裝類"""
    
    def __init__(self, config: SolverConfig):
        self.config = config
        
        # 創建內部組件
        self.mcts_engine = MCTSEngine(
            time_limit=config.time_limit,
            num_threads=config.num_threads,
            simulations_limit=config.simulations,
            exploration_constant=config.exploration_constant,
            use_progressive_widening=config.use_progressive_widening,
            use_progressive_bias=config.use_progressive_bias,
            use_virtual_loss=config.use_virtual_loss
        )
        
        self.action_generator = ActionGenerator(
            use_domain_pruning=config.use_domain_pruning
        )
        
        self.evaluator = StateEvaluator(
            use_cache=config.use_cache
        )
    
    def solve(self, 
              game_state: RealGameState,
              progress_callback: Optional[Callable[[float, int], None]] = None) -> SolveResult:
        """求解 OFC 局面"""
        
        try:
            # 驗證輸入
            if not game_state:
                raise InvalidInputError("Game state cannot be None")
            
            # 生成可能的動作
            actions = self.action_generator.generate_actions(game_state)
            if not actions:
                raise SolverError("No valid actions available")
            
            # 執行 MCTS 搜索
            result: MCTSResult = self.mcts_engine.search(
                game_state,
                progress_callback=progress_callback
            )
            
            # 從根節點獲取統計信息
            root_node = result.root_node
            expected_score = root_node.average_reward if root_node else 0.0
            top_actions = root_node.get_action_statistics()[:5] if root_node else []
            
            # 構建返回結果
            return SolveResult(
                move=result.best_action,
                evaluation=expected_score,
                confidence=min(result.simulations / self.config.simulations, 0.99),
                simulations=result.simulations,
                computation_time_seconds=result.time_elapsed,
                expected_score=expected_score,
                request_id="",
                top_actions=top_actions
            )
            
        except TimeoutError:
            logger.warning("Solver timeout, returning best result so far")
            # 返回部分結果
            if hasattr(self, '_partial_result'):
                return self._partial_result
            raise
        except Exception as e:
            logger.error(f"Solver error: {str(e)}")
            raise SolverError(f"Failed to solve position: {str(e)}")


def create_solver(time_limit: float = 30.0,
                  num_threads: int = 4,
                  simulations: int = 100000,
                  exploration_constant: float = 1.4,
                  use_cache: bool = True,
                  **kwargs) -> OFCSolver:
    """創建求解器的便捷函數"""
    config = SolverConfig(
        time_limit=time_limit,
        num_threads=num_threads,
        simulations=simulations,
        exploration_constant=exploration_constant,
        use_cache=use_cache,
        **kwargs
    )
    return OFCSolver(config)