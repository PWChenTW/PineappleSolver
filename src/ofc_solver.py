"""
OFC Solver 主求解器實現

整合了 MCTS 算法、錯誤處理和結構化日誌系統。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .ofc_solver_simple import (
    SimpleOFCSolver,
    SimpleSolveResult as SolveResult,
    create_solver as create_simple_solver
)
from .core.domain import Card as DomainCard, GameState as DomainGameState
from .logging_config import get_solver_logger


# 保留原有的 Card 和 GameState 類以保持 API 兼容性
@dataclass
class Card:
    """撲克牌類"""
    rank: str  # 2-9, T, J, Q, K, A
    suit: str  # s, h, d, c
    
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return str(self)
    
    def to_domain_card(self) -> DomainCard:
        """轉換為領域模型的 Card"""
        from .core.domain import Rank, Suit
        
        # 映射 rank
        rank_map = {
            '2': Rank.TWO, '3': Rank.THREE, '4': Rank.FOUR, '5': Rank.FIVE,
            '6': Rank.SIX, '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
            'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN, 'K': Rank.KING, 'A': Rank.ACE
        }
        
        # 映射 suit
        suit_map = {
            's': Suit.SPADES, 'h': Suit.HEARTS, 'd': Suit.DIAMONDS, 'c': Suit.CLUBS
        }
        
        # Card takes a single integer value: rank + suit * 13
        rank_val = rank_map[self.rank]
        suit_val = suit_map[self.suit]
        card_value = rank_val + suit_val * 13
        
        return DomainCard(card_value)


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
    
    def to_domain_game_state(self) -> DomainGameState:
        """轉換為領域模型的 GameState"""
        from .core.domain import Street
        
        # 創建領域 GameState
        domain_state = DomainGameState(num_players=2, player_index=0)
        
        # 設置當前手牌
        domain_state.current_hand = [card.to_domain_card() for card in self.current_cards]
        
        # 設置玩家安排
        player_arrangement = domain_state.player_arrangement
        
        # 放置已有的牌
        for i, card in enumerate(self.front_hand):
            player_arrangement.place_card(card.to_domain_card(), 'front', i)
        
        for i, card in enumerate(self.middle_hand):
            player_arrangement.place_card(card.to_domain_card(), 'middle', i)
            
        for i, card in enumerate(self.back_hand):
            player_arrangement.place_card(card.to_domain_card(), 'back', i)
        
        # 設置街道
        total_cards = (len(self.front_hand) + len(self.middle_hand) + 
                      len(self.back_hand) + len(self.current_cards))
        
        if total_cards == 5:
            domain_state.current_street = Street.INITIAL
        elif total_cards == 8:
            domain_state.current_street = Street.FIRST
        elif total_cards == 10:
            domain_state.current_street = Street.SECOND
        elif total_cards == 12:
            domain_state.current_street = Street.THIRD
        elif total_cards == 13:
            domain_state.current_street = Street.FOURTH
        else:
            domain_state.current_street = Street.COMPLETE
        
        return domain_state


class OFCSolver:
    """
    OFC 求解器主類
    
    這是一個包裝類，使用真正的 MCTS 整合實現。
    """
    
    def __init__(self, 
                 threads: int = 4,
                 time_limit: float = 30.0,
                 simulations_limit: int = 100000):
        # 創建簡單的 MCTS 求解器
        self._solver = SimpleOFCSolver(num_simulations=simulations_limit)
        
        # 保存配置
        self.threads = threads
        self.time_limit = time_limit
        self.simulations_limit = simulations_limit
        
        # 獲取日誌器
        self.logger = get_solver_logger()
    
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
        # 直接使用簡單求解器
        result = self._solver.solve(game_state, options)
        
        return result


# 為了兼容性，從兼容層導入
try:
    from .ofc_solver_compat import create_solver as create_compat_solver, SolverConfig as RealSolverConfig
    
    def create_solver(**kwargs):
        """創建求解器，優先使用真正的 MCTS 實現"""
        return OFCSolver(**kwargs)
    
    # 導出兼容接口
    __all__ = ['OFCSolver', 'create_solver', 'RealSolverConfig', 'SolveResult']
except ImportError:
    # 如果導入失敗，定義簡單的 create_solver
    def create_solver(**kwargs):
        return OFCSolver(**kwargs)
    RealSolverConfig = None
    __all__ = ['OFCSolver', 'create_solver', 'SolveResult']