"""
高效的OFC手牌評估器

使用位運算和查找表實現快速牌型識別和強度計算
支持增量更新和並行評估
"""

import numpy as np
from typing import List, Tuple, Dict, Set
from functools import lru_cache
import numba
from enum import IntEnum


class Rank(IntEnum):
    """牌面大小"""
    TWO = 0
    THREE = 1
    FOUR = 2
    FIVE = 3
    SIX = 4
    SEVEN = 5
    EIGHT = 6
    NINE = 7
    TEN = 8
    JACK = 9
    QUEEN = 10
    KING = 11
    ACE = 12


class Suit(IntEnum):
    """花色"""
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3


class HandType(IntEnum):
    """牌型等級"""
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


class Card:
    """撲克牌表示
    
    使用6位整數表示：
    - 高4位：牌面 (0-12)
    - 低2位：花色 (0-3)
    """
    def __init__(self, rank: int, suit: int):
        self.value = (rank << 2) | suit
    
    @property
    def rank(self) -> int:
        return self.value >> 2
    
    @property
    def suit(self) -> int:
        return self.value & 0x3
    
    def __eq__(self, other):
        return self.value == other.value
    
    def __hash__(self):
        return self.value


class HandEvaluator:
    """手牌評估器
    
    核心特性：
    1. 使用預計算的查找表加速評估
    2. 位運算實現O(1)的牌型判斷
    3. 支持增量更新評估結果
    """
    
    # 預計算的查找表
    STRAIGHT_TABLE = {}  # rank_mask -> is_straight
    FLUSH_CHECK_TABLE = {}  # suit_counts -> is_flush
    
    def __init__(self):
        self._initialize_lookup_tables()
        
    def _initialize_lookup_tables(self):
        """初始化查找表"""
        # 順子查找表：使用13位掩碼表示各rank是否存在
        straights = [
            0b1111100000000,  # A-K-Q-J-10
            0b0111110000000,  # K-Q-J-10-9
            0b0011111000000,  # Q-J-10-9-8
            0b0001111100000,  # J-10-9-8-7
            0b0000111110000,  # 10-9-8-7-6
            0b0000011111000,  # 9-8-7-6-5
            0b0000001111100,  # 8-7-6-5-4
            0b0000000111110,  # 7-6-5-4-3
            0b0000000011111,  # 6-5-4-3-2
            0b1000000001111,  # A-5-4-3-2 (特殊順子)
        ]
        
        for straight in straights:
            self.STRAIGHT_TABLE[straight] = True
    
    @numba.jit(nopython=True, cache=True)
    def evaluate_hand_fast(self, cards: np.ndarray) -> Tuple[int, int]:
        """快速評估手牌（使用Numba加速）
        
        參數:
            cards: shape=(n,) 的numpy數組，每個元素是Card.value
            
        返回:
            (hand_type, tie_breaker)
        """
        n = len(cards)
        
        # 統計各rank和suit的數量
        rank_counts = np.zeros(13, dtype=np.int32)
        suit_counts = np.zeros(4, dtype=np.int32)
        rank_mask = 0
        
        for card_value in cards:
            rank = card_value >> 2
            suit = card_value & 0x3
            rank_counts[rank] += 1
            suit_counts[suit] += 1
            rank_mask |= (1 << rank)
        
        # 檢查同花
        is_flush = np.max(suit_counts) >= 5
        
        # 檢查順子（需要改進以支持查找表）
        is_straight = False
        straight_high = -1
        
        # 簡化的順子檢查邏輯
        for start in range(13 - 4):
            if all(rank_mask & (1 << (start + i)) for i in range(5)):
                is_straight = True
                straight_high = start + 4
                break
        
        # 特殊檢查A-2-3-4-5
        if (rank_mask & 0b1000000001111) == 0b1000000001111:
            is_straight = True
            straight_high = 3  # 5 high straight
        
        # 統計對子、三條、四條
        pairs = 0
        trips = 0
        quads = 0
        pair_ranks = []
        trip_rank = -1
        quad_rank = -1
        
        for rank in range(13):
            count = rank_counts[rank]
            if count == 2:
                pairs += 1
                pair_ranks.append(rank)
            elif count == 3:
                trips += 1
                trip_rank = rank
            elif count == 4:
                quads += 1
                quad_rank = rank
        
        # 判斷牌型
        if is_straight and is_flush:
            if straight_high == 12:  # Ace high
                return (HandType.ROYAL_FLUSH, 0)
            return (HandType.STRAIGHT_FLUSH, straight_high)
        
        if quads > 0:
            return (HandType.FOUR_OF_KIND, quad_rank)
        
        if trips > 0 and pairs > 0:
            return (HandType.FULL_HOUSE, trip_rank * 13 + pair_ranks[0])
        
        if is_flush:
            # 計算同花的tie breaker
            flush_cards = []
            for card_value in cards:
                suit = card_value & 0x3
                if suit_counts[suit] >= 5:
                    flush_cards.append(card_value >> 2)
            flush_cards.sort(reverse=True)
            tie_breaker = sum(flush_cards[i] * (13 ** (4-i)) for i in range(5))
            return (HandType.FLUSH, tie_breaker)
        
        if is_straight:
            return (HandType.STRAIGHT, straight_high)
        
        if trips > 0:
            return (HandType.THREE_OF_KIND, trip_rank)
        
        if pairs >= 2:
            pair_ranks.sort(reverse=True)
            return (HandType.TWO_PAIR, pair_ranks[0] * 13 + pair_ranks[1])
        
        if pairs == 1:
            return (HandType.ONE_PAIR, pair_ranks[0])
        
        # 高牌
        high_cards = []
        for rank in range(12, -1, -1):
            if rank_counts[rank] > 0:
                high_cards.append(rank)
                if len(high_cards) == 5:
                    break
        
        tie_breaker = sum(high_cards[i] * (13 ** (4-i)) for i in range(min(5, len(high_cards))))
        return (HandType.HIGH_CARD, tie_breaker)
    
    def evaluate_hand(self, cards: List[Card]) -> Tuple[HandType, int, float]:
        """評估手牌
        
        返回:
            (hand_type, tie_breaker, strength_score)
        """
        if not cards:
            return (HandType.HIGH_CARD, 0, 0.0)
        
        # 轉換為numpy數組
        card_values = np.array([c.value for c in cards], dtype=np.int32)
        
        # 快速評估
        hand_type_int, tie_breaker = self.evaluate_hand_fast(card_values)
        hand_type = HandType(hand_type_int)
        
        # 計算絕對強度分數 (0-1之間)
        strength_score = self._calculate_strength_score(hand_type, tie_breaker, len(cards))
        
        return (hand_type, tie_breaker, strength_score)
    
    def _calculate_strength_score(self, hand_type: HandType, tie_breaker: int, 
                                 num_cards: int) -> float:
        """計算手牌強度分數
        
        公式：
        score = (hand_type_weight + tie_breaker_normalized) * card_count_factor
        
        其中：
        - hand_type_weight: 牌型基礎權重
        - tie_breaker_normalized: 歸一化的tie breaker值
        - card_count_factor: 考慮牌數的調整因子
        """
        # 牌型基礎權重
        type_weights = {
            HandType.HIGH_CARD: 0.0,
            HandType.ONE_PAIR: 0.1,
            HandType.TWO_PAIR: 0.2,
            HandType.THREE_OF_KIND: 0.3,
            HandType.STRAIGHT: 0.4,
            HandType.FLUSH: 0.5,
            HandType.FULL_HOUSE: 0.6,
            HandType.FOUR_OF_KIND: 0.8,
            HandType.STRAIGHT_FLUSH: 0.9,
            HandType.ROYAL_FLUSH: 1.0
        }
        
        base_weight = type_weights[hand_type]
        
        # 歸一化tie breaker（假設最大值為13^5）
        max_tie_breaker = 13 ** 5
        normalized_tie = tie_breaker / max_tie_breaker * 0.1  # 最多貢獻0.1
        
        # 牌數因子（牌越少，相同牌型價值越高）
        card_factor = 1.0 + (7 - num_cards) * 0.05
        
        return min(1.0, (base_weight + normalized_tie) * card_factor)
    
    @lru_cache(maxsize=10000)
    def get_outs(self, current_cards: Tuple[int, ...], 
                 target_hand_type: HandType) -> Set[int]:
        """計算達到目標牌型的outs
        
        使用緩存加速重複計算
        """
        outs = set()
        used_cards = set(current_cards)
        
        # 遍歷所有可能的牌
        for rank in range(13):
            for suit in range(4):
                card_value = (rank << 2) | suit
                if card_value in used_cards:
                    continue
                
                # 測試添加這張牌
                test_cards = list(current_cards) + [card_value]
                test_array = np.array(test_cards, dtype=np.int32)
                hand_type_int, _ = self.evaluate_hand_fast(test_array)
                
                if hand_type_int >= target_hand_type:
                    outs.add(card_value)
        
        return outs
    
    def calculate_equity(self, my_cards: List[Card], opp_cards: List[Card],
                        remaining_cards: List[Card], num_simulations: int = 1000) -> float:
        """蒙特卡洛模擬計算勝率
        
        使用向量化操作加速
        """
        wins = 0
        ties = 0
        
        remaining_values = [c.value for c in remaining_cards]
        my_values = [c.value for c in my_cards]
        opp_values = [c.value for c in opp_cards]
        
        for _ in range(num_simulations):
            # 隨機發剩餘的牌
            np.random.shuffle(remaining_values)
            
            # 完成雙方手牌
            my_final = my_values + remaining_values[:5-len(my_values)]
            opp_final = opp_values + remaining_values[5-len(my_values):10-len(my_values)-len(opp_values)]
            
            # 評估
            my_hand = self.evaluate_hand_fast(np.array(my_final, dtype=np.int32))
            opp_hand = self.evaluate_hand_fast(np.array(opp_final, dtype=np.int32))
            
            # 比較結果
            if my_hand > opp_hand:
                wins += 1
            elif my_hand == opp_hand:
                ties += 1
        
        return (wins + ties * 0.5) / num_simulations


class IncrementalEvaluator:
    """支持增量更新的評估器
    
    維護內部狀態，支持高效的添加/移除牌操作
    """
    def __init__(self, evaluator: HandEvaluator):
        self.evaluator = evaluator
        self.cards: List[Card] = []
        self.rank_counts = np.zeros(13, dtype=np.int32)
        self.suit_counts = np.zeros(4, dtype=np.int32)
        self.rank_mask = 0
        self._cached_result = None
    
    def add_card(self, card: Card):
        """添加一張牌"""
        self.cards.append(card)
        self.rank_counts[card.rank] += 1
        self.suit_counts[card.suit] += 1
        self.rank_mask |= (1 << card.rank)
        self._cached_result = None  # 清除緩存
    
    def remove_card(self, card: Card):
        """移除一張牌"""
        self.cards.remove(card)
        self.rank_counts[card.rank] -= 1
        self.suit_counts[card.suit] -= 1
        if self.rank_counts[card.rank] == 0:
            self.rank_mask &= ~(1 << card.rank)
        self._cached_result = None
    
    def evaluate(self) -> Tuple[HandType, int, float]:
        """評估當前手牌"""
        if self._cached_result is None:
            self._cached_result = self.evaluator.evaluate_hand(self.cards)
        return self._cached_result
    
    def get_potential_score(self, remaining_cards: int) -> float:
        """計算潛在分數
        
        考慮剩餘牌數和當前牌型的提升潛力
        """
        current_type, _, current_score = self.evaluate()
        
        # 基於剩餘牌數的提升潛力
        improvement_potential = {
            HandType.HIGH_CARD: 0.8,
            HandType.ONE_PAIR: 0.6,
            HandType.TWO_PAIR: 0.4,
            HandType.THREE_OF_KIND: 0.3,
            HandType.STRAIGHT: 0.2,
            HandType.FLUSH: 0.15,
            HandType.FULL_HOUSE: 0.1,
            HandType.FOUR_OF_KIND: 0.05,
            HandType.STRAIGHT_FLUSH: 0.02,
            HandType.ROYAL_FLUSH: 0.0
        }
        
        potential = improvement_potential.get(current_type, 0.0)
        remaining_factor = remaining_cards / 52.0
        
        return current_score + potential * remaining_factor