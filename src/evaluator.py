"""
OFC 手牌評估器（帶結構化日誌）

這是一個示例實現，展示如何在評估過程中使用結構化日誌
"""

from typing import List, Dict, Any, Tuple
from enum import Enum
import time

from .logging_config import (
    get_evaluator_logger,
    get_performance_logger,
    LogContext
)
from .ofc_solver import Card


class HandType(Enum):
    """手牌類型"""
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


class HandEvaluator:
    """手牌評估器"""
    
    RANK_VALUES = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
        '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }
    
    def __init__(self):
        self.logger = get_evaluator_logger()
        self.perf_logger = get_performance_logger("evaluator")
        
        # 緩存評估結果
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        self.logger.info(
            "Hand Evaluator initialized",
            extra={
                'component': 'evaluator',
                'context': {
                    'cache_enabled': True
                }
            }
        )
    
    @property
    def cache_hit_rate(self) -> float:
        """緩存命中率"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    def evaluate_hand(self, cards: List[Card]) -> Tuple[HandType, int]:
        """
        評估手牌
        
        Args:
            cards: 手牌列表
            
        Returns:
            (手牌類型, 強度值)
        """
        # 創建緩存鍵（遮蔽實際手牌）
        cache_key = self._create_cache_key(cards)
        
        # 檢查緩存
        if cache_key in self.cache:
            self.cache_hits += 1
            result = self.cache[cache_key]
            
            self.logger.debug(
                "Cache hit for hand evaluation",
                extra={
                    'component': 'evaluator',
                    'context': {
                        'cache_hit_rate': self.cache_hit_rate,
                        'hand_size': len(cards)
                    }
                }
            )
            
            return result
        
        # 緩存未命中，執行評估
        self.cache_misses += 1
        
        with LogContext(self.logger, operation="evaluate_hand") as log_ctx:
            log_ctx.log("debug", "Evaluating hand",
                       hand_size=len(cards),
                       cache_hit_rate=self.cache_hit_rate)
            
            # 使用性能日誌
            @self.perf_logger.log_timing("hand_evaluation")
            def _evaluate():
                return self._do_evaluate(cards, log_ctx)
            
            result = _evaluate()
            
            # 存入緩存
            self.cache[cache_key] = result
            
            return result
    
    def _create_cache_key(self, cards: List[Card]) -> str:
        """創建緩存鍵（不包含實際手牌信息）"""
        # 使用排序後的手牌創建唯一鍵
        sorted_cards = sorted(cards, key=lambda c: (self.RANK_VALUES[c.rank], c.suit))
        return ''.join(f"{c.rank}{c.suit}" for c in sorted_cards)
    
    def _do_evaluate(self, cards: List[Card], log_ctx: LogContext) -> Tuple[HandType, int]:
        """執行實際的手牌評估"""
        if not cards:
            return HandType.HIGH_CARD, 0
        
        # 統計牌面和花色
        rank_counts = {}
        suit_counts = {}
        
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        
        # 檢查各種牌型
        is_flush = any(count >= 5 for count in suit_counts.values())
        is_straight, straight_high = self._check_straight(cards)
        
        # 獲取相同牌面的數量
        counts = sorted(rank_counts.values(), reverse=True)
        
        # 判斷牌型
        hand_type = self._determine_hand_type(
            counts, is_flush, is_straight, log_ctx
        )
        
        # 計算強度值
        strength = self._calculate_strength(hand_type, cards, rank_counts)
        
        log_ctx.log("debug", "Hand evaluation complete",
                   hand_type=hand_type.name,
                   strength=strength)
        
        return hand_type, strength
    
    def _check_straight(self, cards: List[Card]) -> Tuple[bool, int]:
        """檢查是否為順子"""
        if len(cards) < 5:
            return False, 0
        
        ranks = sorted([self.RANK_VALUES[c.rank] for c in cards])
        
        # 檢查連續的5張牌
        for i in range(len(ranks) - 4):
            if ranks[i+4] - ranks[i] == 4:
                # 檢查中間是否都存在
                is_straight = all(
                    any(r == ranks[i] + j for r in ranks)
                    for j in range(5)
                )
                if is_straight:
                    return True, ranks[i+4]
        
        # 檢查 A-2-3-4-5 的特殊情況
        if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
            return True, 5
        
        return False, 0
    
    def _determine_hand_type(self, counts: List[int], is_flush: bool, 
                           is_straight: bool, log_ctx: LogContext) -> HandType:
        """確定手牌類型"""
        if is_straight and is_flush:
            hand_type = HandType.STRAIGHT_FLUSH
        elif counts[0] == 4:
            hand_type = HandType.FOUR_OF_A_KIND
        elif counts[0] == 3 and counts[1] == 2:
            hand_type = HandType.FULL_HOUSE
        elif is_flush:
            hand_type = HandType.FLUSH
        elif is_straight:
            hand_type = HandType.STRAIGHT
        elif counts[0] == 3:
            hand_type = HandType.THREE_OF_A_KIND
        elif counts[0] == 2 and counts[1] == 2:
            hand_type = HandType.TWO_PAIR
        elif counts[0] == 2:
            hand_type = HandType.PAIR
        else:
            hand_type = HandType.HIGH_CARD
        
        log_ctx.log("debug", "Hand type determined",
                   hand_type=hand_type.name,
                   is_flush=is_flush,
                   is_straight=is_straight)
        
        return hand_type
    
    def _calculate_strength(self, hand_type: HandType, cards: List[Card], 
                          rank_counts: Dict[str, int]) -> int:
        """計算手牌強度值"""
        # 基礎分數
        base_score = hand_type.value * 10000
        
        # 根據牌型添加額外分數
        if hand_type == HandType.HIGH_CARD:
            # 高牌：最大的5張牌
            ranks = sorted([self.RANK_VALUES[c.rank] for c in cards], reverse=True)[:5]
            strength = base_score + sum(r * (100 ** i) for i, r in enumerate(reversed(ranks)))
        
        elif hand_type == HandType.PAIR:
            # 對子：對子大小 + 踢腳牌
            pair_rank = max(r for r, c in rank_counts.items() if c == 2)
            kickers = sorted([self.RANK_VALUES[c.rank] for c in cards 
                            if c.rank != pair_rank], reverse=True)[:3]
            strength = base_score + self.RANK_VALUES[pair_rank] * 1000
            strength += sum(k * (10 ** i) for i, k in enumerate(reversed(kickers)))
        
        else:
            # 簡化處理其他牌型
            strength = base_score
        
        return strength
    
    def compare_hands(self, hand1: List[Card], hand2: List[Card]) -> int:
        """
        比較兩手牌
        
        Returns:
            1 if hand1 > hand2
            -1 if hand1 < hand2
            0 if hand1 == hand2
        """
        with LogContext(self.logger, operation="compare_hands") as log_ctx:
            log_ctx.log("debug", "Comparing two hands",
                       hand1_size=len(hand1),
                       hand2_size=len(hand2))
            
            type1, strength1 = self.evaluate_hand(hand1)
            type2, strength2 = self.evaluate_hand(hand2)
            
            result = 0
            if strength1 > strength2:
                result = 1
            elif strength1 < strength2:
                result = -1
            
            log_ctx.log("debug", "Comparison complete",
                       hand1_type=type1.name,
                       hand2_type=type2.name,
                       result=result)
            
            return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取評估器統計信息"""
        stats = {
            'cache_size': len(self.cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hit_rate,
            'total_evaluations': self.cache_hits + self.cache_misses
        }
        
        self.logger.info(
            "Evaluator statistics retrieved",
            extra={
                'component': 'evaluator',
                'context': stats
            }
        )
        
        return stats
    
    def clear_cache(self):
        """清空緩存"""
        old_size = len(self.cache)
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        
        self.logger.info(
            "Cache cleared",
            extra={
                'component': 'evaluator',
                'context': {
                    'old_cache_size': old_size
                }
            }
        )