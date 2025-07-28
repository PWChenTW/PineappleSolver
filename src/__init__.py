"""
OFC Solver 包初始化文件
"""

from .logging_config import (
    LoggerManager,
    get_solver_logger,
    get_mcts_logger,
    get_evaluator_logger,
    get_api_logger,
    get_performance_logger,
    LogContext
)

from .ofc_solver import (
    Card,
    GameState,
    SolveResult,
    OFCSolver
)

from .mcts_engine import (
    MCTSNode,
    MCTSEngine
)

from .evaluator import (
    HandType,
    HandEvaluator
)

__all__ = [
    # 日誌相關
    'LoggerManager',
    'get_solver_logger',
    'get_mcts_logger',
    'get_evaluator_logger',
    'get_api_logger',
    'get_performance_logger',
    'LogContext',
    
    # 求解器相關
    'Card',
    'GameState',
    'SolveResult',
    'OFCSolver',
    
    # MCTS 相關
    'MCTSNode',
    'MCTSEngine',
    
    # 評估器相關
    'HandType',
    'HandEvaluator'
]

# 版本信息
__version__ = '1.0.0'