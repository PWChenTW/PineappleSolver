"""
街道求解器 API 適配器
將逐街求解器整合到 API 系統中
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from ofc_solver_street import (
    StreetByStreetSolver, Street, OpponentTracker,
    Card, PineappleState, StreetState,
    InitialStreetSolver, DrawStreetSolver
)


@dataclass
class StreetSolverRequest:
    """街道求解請求"""
    street: str  # 'initial', 'first', 'second', 'third', 'fourth'
    current_cards: List[str]  # 當前抽到的牌
    player_state: Dict[str, List[str]]  # 玩家當前狀態
    opponent_state: Optional[Dict[str, Any]] = None  # 對手狀態
    include_jokers: bool = True


@dataclass
class StreetSolverResponse:
    """街道求解響應"""
    success: bool
    placements: Optional[List[Dict[str, str]]] = None  # [{'card': 'As', 'position': 'back'}]
    discard: Optional[str] = None
    player_state: Optional[Dict[str, Any]] = None
    opponent_state: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StreetSolverAdapter:
    """街道求解器適配器"""
    
    def __init__(self):
        self.solver = StreetByStreetSolver(include_jokers=True)
        self.game_sessions = {}  # 存儲遊戲會話
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        """創建新的遊戲會話"""
        self.game_sessions[session_id] = {
            'player_state': PineappleState(),
            'opponent_tracker': OpponentTracker(),
            'remaining_deck': None,
            'street': Street.INITIAL
        }
        return {'session_id': session_id, 'status': 'created'}
    
    def solve_street(self, request: StreetSolverRequest, 
                    session_id: Optional[str] = None) -> StreetSolverResponse:
        """求解單個街道"""
        try:
            # 解析街道
            street = self._parse_street(request.street)
            
            # 解析牌
            current_cards = [self._parse_card(c) for c in request.current_cards]
            
            # 獲取或創建玩家狀態
            if session_id and session_id in self.game_sessions:
                session = self.game_sessions[session_id]
                player_state = session['player_state']
                opponent_tracker = session['opponent_tracker']
            else:
                player_state = self._create_player_state(request.player_state)
                opponent_tracker = OpponentTracker()
            
            # 創建街道狀態
            street_state = StreetState(
                street=street,
                player_state=player_state,
                opponent_tracker=opponent_tracker,
                remaining_deck=[],  # API 模式下不需要完整牌堆
                street_cards=current_cards
            )
            
            # 根據街道類型選擇求解器
            if street == Street.INITIAL:
                result = self.solver.initial_solver.solve_street(street_state)
                
                # 轉換結果
                placements = []
                for card, position in result['placement']:
                    placements.append({
                        'card': str(card),
                        'position': position
                    })
                
                response = StreetSolverResponse(
                    success=True,
                    placements=placements,
                    player_state=self._export_player_state(player_state),
                    metadata={'fantasy_land': result.get('fantasy_land', False)}
                )
            else:
                # 抽牌街道
                result = self.solver.draw_solver.solve_street(street_state)
                
                placements = []
                for card, position in result['placements']:
                    placements.append({
                        'card': str(card),
                        'position': position
                    })
                
                response = StreetSolverResponse(
                    success=True,
                    placements=placements,
                    discard=str(result['discard']),
                    player_state=self._export_player_state(player_state)
                )
            
            # 更新會話
            if session_id and session_id in self.game_sessions:
                self.game_sessions[session_id]['player_state'] = player_state
                self.game_sessions[session_id]['street'] = Street(street.value + 1)
            
            return response
            
        except Exception as e:
            return StreetSolverResponse(
                success=False,
                error=str(e)
            )
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """獲取會話狀態"""
        if session_id not in self.game_sessions:
            return {'error': 'Session not found'}
        
        session = self.game_sessions[session_id]
        player_state = session['player_state']
        
        return {
            'session_id': session_id,
            'street': session['street'].name,
            'player_state': self._export_player_state(player_state),
            'is_complete': player_state.is_complete(),
            'is_valid': player_state.is_valid(),
            'fantasy_land': player_state.has_fantasy_land()
        }
    
    def _parse_street(self, street_str: str) -> Street:
        """解析街道字符串"""
        street_map = {
            'initial': Street.INITIAL,
            'first': Street.FIRST,
            'second': Street.SECOND,
            'third': Street.THIRD,
            'fourth': Street.FOURTH
        }
        
        street_lower = street_str.lower()
        if street_lower not in street_map:
            raise ValueError(f"Invalid street: {street_str}")
        
        return street_map[street_lower]
    
    def _parse_card(self, card_str: str) -> Card:
        """解析牌字符串"""
        if card_str.upper() == 'XJ':  # 鬼牌
            return Card.joker()
        return Card.from_string(card_str)
    
    def _create_player_state(self, state_dict: Dict[str, List[str]]) -> PineappleState:
        """從字典創建玩家狀態"""
        player_state = PineappleState()
        
        # 放置前墩
        for card_str in state_dict.get('front', []):
            card = self._parse_card(card_str)
            player_state.front_hand.add_card(card)
        
        # 放置中墩
        for card_str in state_dict.get('middle', []):
            card = self._parse_card(card_str)
            player_state.middle_hand.add_card(card)
        
        # 放置後墩
        for card_str in state_dict.get('back', []):
            card = self._parse_card(card_str)
            player_state.back_hand.add_card(card)
        
        # 處理棄牌
        for card_str in state_dict.get('discarded', []):
            card = self._parse_card(card_str)
            player_state.discarded.append(card)
        
        return player_state
    
    def _export_player_state(self, player_state: PineappleState) -> Dict[str, Any]:
        """導出玩家狀態為字典"""
        return {
            'front': [str(c) for c in player_state.front_hand.cards],
            'middle': [str(c) for c in player_state.middle_hand.cards],
            'back': [str(c) for c in player_state.back_hand.cards],
            'discarded': [str(c) for c in player_state.discarded],
            'available_positions': player_state.get_available_positions(),
            'is_complete': player_state.is_complete(),
            'is_valid': player_state.is_valid(),
            'fantasy_land': player_state.has_fantasy_land()
        }


# API 路由處理函數
def solve_street_api(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """API 端點處理函數"""
    adapter = StreetSolverAdapter()
    
    # 創建請求對象
    request = StreetSolverRequest(
        street=request_data['street'],
        current_cards=request_data['current_cards'],
        player_state=request_data.get('player_state', {
            'front': [], 'middle': [], 'back': [], 'discarded': []
        }),
        opponent_state=request_data.get('opponent_state'),
        include_jokers=request_data.get('include_jokers', True)
    )
    
    # 求解
    session_id = request_data.get('session_id')
    response = adapter.solve_street(request, session_id)
    
    # 轉換為字典
    return {
        'success': response.success,
        'placements': response.placements,
        'discard': response.discard,
        'player_state': response.player_state,
        'opponent_state': response.opponent_state,
        'error': response.error,
        'metadata': response.metadata
    }


# 示例用法
if __name__ == "__main__":
    # 測試初始街道
    request1 = {
        'street': 'initial',
        'current_cards': ['As', 'Ah', 'Kd', 'Kc', 'Xj'],  # 包含一張鬼牌
        'player_state': {
            'front': [],
            'middle': [],
            'back': [],
            'discarded': []
        }
    }
    
    result1 = solve_street_api(request1)
    print("初始街道結果:")
    print(f"  擺放: {result1['placements']}")
    print(f"  玩家狀態: {result1['player_state']}")
    
    # 測試第一街
    request2 = {
        'street': 'first',
        'current_cards': ['Qs', 'Jh', '5d'],
        'player_state': result1['player_state']  # 使用上一街的結果
    }
    
    result2 = solve_street_api(request2)
    print("\n第一街結果:")
    print(f"  擺放: {result2['placements']}")
    print(f"  棄牌: {result2['discard']}")
    print(f"  玩家狀態: {result2['player_state']}")