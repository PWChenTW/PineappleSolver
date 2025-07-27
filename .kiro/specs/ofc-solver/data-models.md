# OFC Solver 核心數據模型設計

## 數據模型概覽

### 模型層次結構
```
┌─────────────────────────────────────────────────────────┐
│                    Value Objects                         │
│  Card, CardSet, HandType, Position, Score              │
└─────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────┐
│                      Entities                           │
│  Hand, PlayerArrangement, OpponentInfo                 │
└─────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────┐
│                   Aggregate Roots                       │
│  GameState, SolverSession                              │
└─────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────┐
│                   Domain Events                         │
│  CardsDealt, CardsPlaced, RoundCompleted              │
└─────────────────────────────────────────────────────────┘
```

## 值對象 (Value Objects)

### Card - 撲克牌
```python
@dataclass(frozen=True)
class Card:
    """
    不可變的撲克牌值對象
    使用整數表示以優化性能
    """
    value: int  # 0-51, 使用單一整數表示
    
    def __post_init__(self):
        if not 0 <= self.value <= 51:
            raise ValueError(f"Invalid card value: {self.value}")
    
    @property
    def rank(self) -> int:
        """返回牌面值 2-14 (2-A)"""
        return (self.value % 13) + 2
    
    @property
    def suit(self) -> int:
        """返回花色 0-3 (♣♦♥♠)"""
        return self.value // 13
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """從字符串創建 '2h', 'As', 'Kc', etc."""
        rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, 
                   '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        suit_map = {'c': 0, 'd': 1, 'h': 2, 's': 3}
        
        rank = rank_map[card_str[0]]
        suit = suit_map[card_str[1]]
        value = suit * 13 + (rank - 2)
        
        return cls(value)
    
    def to_string(self) -> str:
        """轉換為字符串表示"""
        ranks = '23456789TJQKA'
        suits = 'cdhs'
        return ranks[self.rank - 2] + suits[self.suit]
```

### CardSet - 卡牌集合
```python
@dataclass(frozen=True)
class CardSet:
    """
    不可變的卡牌集合，使用位掩碼優化
    """
    mask: int  # 52位的位掩碼表示
    
    def __post_init__(self):
        if self.mask < 0 or self.mask >= (1 << 52):
            raise ValueError("Invalid card set mask")
    
    @classmethod
    def from_cards(cls, cards: List[Card]) -> 'CardSet':
        """從卡牌列表創建"""
        mask = 0
        for card in cards:
            mask |= (1 << card.value)
        return cls(mask)
    
    def contains(self, card: Card) -> bool:
        """檢查是否包含某張牌"""
        return bool(self.mask & (1 << card.value))
    
    def add(self, card: Card) -> 'CardSet':
        """添加一張牌（返回新對象）"""
        return CardSet(self.mask | (1 << card.value))
    
    def remove(self, card: Card) -> 'CardSet':
        """移除一張牌（返回新對象）"""
        return CardSet(self.mask & ~(1 << card.value))
    
    def intersection(self, other: 'CardSet') -> 'CardSet':
        """交集"""
        return CardSet(self.mask & other.mask)
    
    def union(self, other: 'CardSet') -> 'CardSet':
        """並集"""
        return CardSet(self.mask | other.mask)
    
    @property
    def size(self) -> int:
        """集合大小"""
        return bin(self.mask).count('1')
    
    def to_list(self) -> List[Card]:
        """轉換為卡牌列表"""
        cards = []
        for i in range(52):
            if self.mask & (1 << i):
                cards.append(Card(i))
        return cards
```

### HandType - 牌型
```python
@dataclass(frozen=True)
class HandType:
    """牌型值對象"""
    category: int  # 0-9 對應高牌到皇家同花順
    ranks: Tuple[int, ...]  # 關鍵牌的rank，用於同類型比較
    
    # 牌型常量
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9
    
    @property
    def strength(self) -> int:
        """
        計算牌型強度值（用於快速比較）
        高16位存儲category，低48位存儲ranks信息
        """
        strength = self.category << 48
        shift = 44
        for rank in self.ranks[:4]:  # 最多比較4個關鍵牌
            strength |= (rank << shift)
            shift -= 11
        return strength
    
    def __lt__(self, other: 'HandType') -> bool:
        return self.strength < other.strength
```

### Score - 分數
```python
@dataclass(frozen=True)
class Score:
    """分數值對象"""
    street_scores: Tuple[int, int, int]  # 前中後三條街的基本分
    bonus_scores: Dict[str, int]  # 各種獎勵分
    fantasy_land: bool  # 是否進入夢幻島
    
    @property
    def total(self) -> int:
        """總分"""
        return sum(self.street_scores) + sum(self.bonus_scores.values())
    
    def __add__(self, other: 'Score') -> 'Score':
        """分數相加"""
        new_street = tuple(a + b for a, b in zip(self.street_scores, other.street_scores))
        new_bonus = {k: self.bonus_scores.get(k, 0) + other.bonus_scores.get(k, 0) 
                    for k in set(self.bonus_scores) | set(other.bonus_scores)}
        new_fantasy = self.fantasy_land or other.fantasy_land
        return Score(new_street, new_bonus, new_fantasy)
```

## 實體 (Entities)

### Hand - 手牌
```python
class Hand(Entity):
    """手牌實體"""
    
    def __init__(self, hand_id: str, cards: List[Card], position: Position):
        super().__init__(hand_id)
        self._cards = sorted(cards, key=lambda c: c.rank, reverse=True)
        self.position = position
        self._hand_type: Optional[HandType] = None
        self._evaluator = HandEvaluator()
    
    @property
    def cards(self) -> List[Card]:
        """返回卡牌的不可變視圖"""
        return self._cards.copy()
    
    @property
    def hand_type(self) -> HandType:
        """延遲計算並緩存牌型"""
        if self._hand_type is None:
            self._hand_type = self._evaluator.evaluate(self._cards)
        return self._hand_type
    
    def is_valid_size(self) -> bool:
        """驗證手牌數量是否正確"""
        expected = {Position.FRONT: 3, Position.MIDDLE: 5, Position.BACK: 5}
        return len(self._cards) == expected[self.position]
    
    def can_add_card(self, card: Card) -> bool:
        """檢查是否可以添加卡牌"""
        expected = {Position.FRONT: 3, Position.MIDDLE: 5, Position.BACK: 5}
        return len(self._cards) < expected[self.position]
    
    def with_card(self, card: Card) -> 'Hand':
        """返回添加了新卡牌的手牌副本"""
        if not self.can_add_card(card):
            raise ValueError("Hand is full")
        new_cards = self._cards + [card]
        return Hand(f"{self.id}_with_{card.to_string()}", new_cards, self.position)
```

### PlayerArrangement - 玩家牌型安排
```python
class PlayerArrangement(Entity):
    """玩家的完整牌型安排"""
    
    def __init__(self, arrangement_id: str):
        super().__init__(arrangement_id)
        self.front: Optional[Hand] = None
        self.middle: Optional[Hand] = None
        self.back: Optional[Hand] = None
        self._is_complete = False
        self._is_valid = None
    
    def set_hand(self, position: Position, hand: Hand):
        """設置某個位置的手牌"""
        if position == Position.FRONT:
            self.front = hand
        elif position == Position.MIDDLE:
            self.middle = hand
        elif position == Position.BACK:
            self.back = hand
        
        self._is_valid = None  # 重置驗證緩存
        self._check_completeness()
    
    def _check_completeness(self):
        """檢查是否所有位置都已設置"""
        self._is_complete = all([self.front, self.middle, self.back])
    
    @property
    def is_complete(self) -> bool:
        """是否完整"""
        return self._is_complete
    
    @property
    def is_valid(self) -> bool:
        """驗證牌型大小關係（緩存結果）"""
        if self._is_valid is None:
            if not self.is_complete:
                self._is_valid = False
            else:
                # 後墩 >= 中墩 >= 前墩
                self._is_valid = (
                    self.back.hand_type >= self.middle.hand_type >= self.front.hand_type
                )
        return self._is_valid
    
    def get_all_cards(self) -> List[Card]:
        """獲取所有卡牌"""
        cards = []
        if self.front:
            cards.extend(self.front.cards)
        if self.middle:
            cards.extend(self.middle.cards)
        if self.back:
            cards.extend(self.back.cards)
        return cards
    
    def calculate_bonus(self) -> Dict[str, int]:
        """計算獎勵分數"""
        bonus = {}
        
        # 前墩獎勵
        if self.front:
            front_type = self.front.hand_type.category
            if front_type >= HandType.PAIR:
                bonus['front'] = FRONT_BONUS_TABLE[front_type]
        
        # 中墩獎勵
        if self.middle:
            middle_type = self.middle.hand_type.category
            if middle_type >= HandType.THREE_OF_KIND:
                bonus['middle'] = MIDDLE_BONUS_TABLE[middle_type]
        
        # 後墩獎勵
        if self.back:
            back_type = self.back.hand_type.category
            if back_type >= HandType.STRAIGHT:
                bonus['back'] = BACK_BONUS_TABLE[back_type]
        
        return bonus
```

### OpponentInfo - 對手信息
```python
class OpponentInfo(Entity):
    """對手信息實體"""
    
    def __init__(self, opponent_id: str):
        super().__init__(opponent_id)
        self.shown_cards = CardSet(0)  # 已展示的牌
        self.arrangement: Optional[PlayerArrangement] = None
        self.last_update_round = -1
    
    def update_shown_cards(self, cards: List[Card], round_number: int):
        """更新對手展示的牌"""
        for card in cards:
            self.shown_cards = self.shown_cards.add(card)
        self.last_update_round = round_number
    
    def set_final_arrangement(self, arrangement: PlayerArrangement):
        """設置對手的最終牌型"""
        self.arrangement = arrangement
```

## 聚合根 (Aggregate Roots)

### GameState - 遊戲狀態
```python
class GameState(AggregateRoot):
    """遊戲狀態聚合根"""
    
    def __init__(self, game_id: str, player_count: int = 2):
        super().__init__(game_id)
        self.player_count = player_count
        self.round_number = 0
        self.phase = GamePhase.INITIAL_DEAL
        
        # 牌的狀態
        self.deck = self._create_full_deck()
        self.dealt_cards: List[Card] = []
        self.available_cards = CardSet.from_cards(self.deck)
        
        # 玩家狀態
        self.player_arrangement = PlayerArrangement(f"{game_id}_player")
        self.placed_cards = CardSet(0)
        self.discarded_cards = CardSet(0)
        
        # 對手信息
        self.opponents: Dict[str, OpponentInfo] = {}
        for i in range(player_count - 1):
            opponent_id = f"opponent_{i}"
            self.opponents[opponent_id] = OpponentInfo(opponent_id)
    
    def _create_full_deck(self) -> List[Card]:
        """創建完整的52張牌"""
        return [Card(i) for i in range(52)]
    
    def deal_initial_cards(self, cards: List[Card]):
        """發初始5張牌"""
        if self.phase != GamePhase.INITIAL_DEAL:
            raise DomainException("Not in initial deal phase")
        if len(cards) != 5:
            raise DomainException("Initial deal must be 5 cards")
        
        self.dealt_cards = cards
        for card in cards:
            self.available_cards = self.available_cards.remove(card)
        
        self.phase = GamePhase.PLACEMENT
        self.raise_domain_event(InitialCardsDealt(self.id, cards))
    
    def deal_round_cards(self, cards: List[Card]):
        """發每輪3張牌"""
        if self.phase != GamePhase.DRAW:
            raise DomainException("Not in draw phase")
        if len(cards) != 3:
            raise DomainException("Round deal must be 3 cards")
        
        self.dealt_cards.extend(cards)
        for card in cards:
            self.available_cards = self.available_cards.remove(card)
        
        self.phase = GamePhase.PLACEMENT
        self.raise_domain_event(RoundCardsDealt(self.id, self.round_number, cards))
    
    def place_cards(self, placements: Dict[Position, List[Card]], discard: Optional[Card] = None):
        """放置卡牌"""
        if self.phase != GamePhase.PLACEMENT:
            raise DomainException("Not in placement phase")
        
        # 驗證卡牌
        all_cards = []
        for cards in placements.values():
            all_cards.extend(cards)
        if discard:
            all_cards.append(discard)
        
        # 檢查是否都是手上的牌
        for card in all_cards:
            if card not in self.dealt_cards:
                raise DomainException(f"Card {card.to_string()} not in hand")
        
        # 放置卡牌
        for position, cards in placements.items():
            for card in cards:
                self._place_card_at_position(card, position)
        
        # 棄牌
        if discard:
            self.discarded_cards = self.discarded_cards.add(discard)
            self.dealt_cards.remove(discard)
        
        # 檢查是否進入下一階段
        if self.round_number < 4:
            self.round_number += 1
            self.phase = GamePhase.DRAW
        else:
            self.phase = GamePhase.COMPLETED
            
        self.raise_domain_event(CardsPlaced(self.id, placements, discard))
    
    def _place_card_at_position(self, card: Card, position: Position):
        """在指定位置放置卡牌"""
        # 獲取當前位置的手牌
        current_hand = getattr(self.player_arrangement, position.value.lower())
        
        if current_hand is None:
            # 創建新手牌
            new_hand = Hand(f"{self.id}_{position.value}", [card], position)
        else:
            # 添加到現有手牌
            new_hand = current_hand.with_card(card)
        
        # 更新安排
        self.player_arrangement.set_hand(position, new_hand)
        self.placed_cards = self.placed_cards.add(card)
        self.dealt_cards.remove(card)
    
    def update_opponent_cards(self, opponent_id: str, cards: List[Card]):
        """更新對手展示的牌"""
        if opponent_id not in self.opponents:
            raise DomainException(f"Unknown opponent: {opponent_id}")
        
        opponent = self.opponents[opponent_id]
        opponent.update_shown_cards(cards, self.round_number)
        
        # 更新可用牌
        for card in cards:
            self.available_cards = self.available_cards.remove(card)
    
    def get_unknown_cards(self) -> CardSet:
        """獲取未知的牌（可能在對手手中或牌堆中）"""
        known_cards = self.placed_cards.union(self.discarded_cards)
        for opponent in self.opponents.values():
            known_cards = known_cards.union(opponent.shown_cards)
        
        all_cards = CardSet.from_cards(self.deck)
        return all_cards.intersection(self.available_cards)
```

### SolverSession - 求解會話
```python
class SolverSession(AggregateRoot):
    """求解器會話聚合根"""
    
    def __init__(self, session_id: str, game_state: GameState):
        super().__init__(session_id)
        self.game_state = game_state
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        
        # 求解配置
        self.time_limit = 300  # 5分鐘
        self.search_algorithm = "MCTS"
        self.evaluation_cache = {}
        
        # 求解結果
        self.best_solution: Optional[Solution] = None
        self.search_stats = SearchStats()
        
        # 狀態
        self.status = SolverStatus.INITIALIZED
        self.progress = 0.0
    
    def start_solving(self):
        """開始求解"""
        if self.status != SolverStatus.INITIALIZED:
            raise DomainException("Solver already started")
        
        self.status = SolverStatus.RUNNING
        self.raise_domain_event(SolvingStarted(self.id, self.game_state.id))
    
    def update_progress(self, progress: float, current_best: Optional[Solution] = None):
        """更新求解進度"""
        self.progress = progress
        if current_best and (not self.best_solution or 
                           current_best.expected_value > self.best_solution.expected_value):
            self.best_solution = current_best
            self.raise_domain_event(BetterSolutionFound(self.id, current_best))
    
    def complete_solving(self, final_solution: Solution, stats: SearchStats):
        """完成求解"""
        self.end_time = datetime.now()
        self.best_solution = final_solution
        self.search_stats = stats
        self.status = SolverStatus.COMPLETED
        self.progress = 1.0
        
        self.raise_domain_event(SolvingCompleted(
            self.id, 
            final_solution,
            (self.end_time - self.start_time).total_seconds()
        ))
    
    def abort_solving(self, reason: str):
        """中止求解"""
        self.end_time = datetime.now()
        self.status = SolverStatus.ABORTED
        
        self.raise_domain_event(SolvingAborted(self.id, reason))
```

## 領域事件 (Domain Events)

```python
@dataclass(frozen=True)
class DomainEvent:
    """領域事件基類"""
    aggregate_id: str
    occurred_at: datetime = field(default_factory=datetime.now)
    event_version: int = 1

@dataclass(frozen=True)
class InitialCardsDealt(DomainEvent):
    """初始發牌事件"""
    cards: List[Card]

@dataclass(frozen=True)
class RoundCardsDealt(DomainEvent):
    """每輪發牌事件"""
    round_number: int
    cards: List[Card]

@dataclass(frozen=True)
class CardsPlaced(DomainEvent):
    """卡牌放置事件"""
    placements: Dict[Position, List[Card]]
    discarded_card: Optional[Card]

@dataclass(frozen=True)
class SolvingStarted(DomainEvent):
    """求解開始事件"""
    game_state_id: str

@dataclass(frozen=True)
class BetterSolutionFound(DomainEvent):
    """發現更優解事件"""
    solution: Solution

@dataclass(frozen=True)
class SolvingCompleted(DomainEvent):
    """求解完成事件"""
    final_solution: Solution
    time_elapsed: float

@dataclass(frozen=True)
class SolvingAborted(DomainEvent):
    """求解中止事件"""
    reason: str
```

## 性能優化考慮

### 1. 內存優化
- 使用整數位運算表示卡牌集合
- 共享不可變對象（值對象）
- 使用對象池減少GC壓力

### 2. 計算優化
- 緩存牌型評估結果
- 預計算常見牌型組合
- 使用查找表加速

### 3. 並發優化
- 不可變值對象支持並發
- 事件驅動支持異步處理
- 無鎖數據結構設計

## 數據模型使用示例

```python
# 創建遊戲狀態
game = GameState("game_001")

# 初始發牌
initial_cards = [
    Card.from_string("As"), Card.from_string("Ks"), 
    Card.from_string("Qs"), Card.from_string("Js"), 
    Card.from_string("Ts")
]
game.deal_initial_cards(initial_cards)

# 放置卡牌
placements = {
    Position.BACK: [Card.from_string("As"), Card.from_string("Ks"), 
                   Card.from_string("Qs"), Card.from_string("Js"), 
                   Card.from_string("Ts")]
}
game.place_cards(placements)

# 創建求解會話
session = SolverSession("session_001", game)
session.start_solving()

# 更新進度
solution = Solution(
    arrangement=game.player_arrangement,
    expected_value=15.5,
    confidence=0.95
)
session.update_progress(0.3, solution)
```

這個數據模型設計提供了高性能、類型安全和領域表達力的平衡，能夠有效支持OFC求解器的實現。