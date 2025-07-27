# OFC Solver 系統架構設計

## 架構概覽

### 整體架構圖
```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Game API   │  │ Solver API   │  │  Analysis API   │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │Game Manager │  │Solver Engine │  │Strategy Analyzer│   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Game Rules  │  │  Evaluation  │  │  Search Logic   │   │
│  │   Engine    │  │    Engine    │  │    & Pruning    │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   Cache     │  │  State Store │  │    Logging &    │   │
│  │  Manager    │  │  (Memory)    │  │   Monitoring    │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 關鍵組件說明

#### 1. API Layer (接口層)
- **Game API**: 管理遊戲狀態、處理玩家輸入
- **Solver API**: 提供求解接口、返回最優解
- **Analysis API**: 提供策略分析、統計數據

#### 2. Application Layer (應用層)
- **Game Manager**: 遊戲流程控制、狀態管理
- **Solver Engine**: 核心求解引擎、協調各組件
- **Strategy Analyzer**: 策略分析、期望值計算

#### 3. Domain Layer (領域層)
- **Game Rules Engine**: 規則驗證、合法性檢查
- **Evaluation Engine**: 牌型評估、分數計算
- **Search Logic**: 搜索算法、剪枝策略

#### 4. Infrastructure Layer (基礎設施層)
- **Cache Manager**: 緩存常見牌型評估結果
- **State Store**: 高效的遊戲狀態存儲
- **Logging & Monitoring**: 性能監控、調試支持

## 領域模型設計

### 核心實體

```python
# 值對象
@dataclass(frozen=True)
class Card:
    """撲克牌值對象"""
    rank: int  # 2-14 (2-A)
    suit: str  # 'h', 'd', 'c', 's'
    
    def __post_init__(self):
        if not (2 <= self.rank <= 14):
            raise ValueError("Invalid rank")
        if self.suit not in ['h', 'd', 'c', 's']:
            raise ValueError("Invalid suit")

@dataclass(frozen=True)
class HandType(Enum):
    """牌型枚舉"""
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

# 實體
class Hand(Entity):
    """手牌實體"""
    def __init__(self, hand_id: str, cards: List[Card], position: str):
        super().__init__(hand_id)
        self.cards = cards
        self.position = position  # 'front', 'middle', 'back'
        self._hand_type = None
        self._strength = None
    
    @property
    def hand_type(self) -> HandType:
        """延遲計算牌型"""
        if self._hand_type is None:
            self._hand_type = self._evaluate_hand_type()
        return self._hand_type
    
    def is_valid_size(self) -> bool:
        """驗證手牌數量"""
        expected_sizes = {'front': 3, 'middle': 5, 'back': 5}
        return len(self.cards) == expected_sizes[self.position]

# 聚合根
class GameState(AggregateRoot):
    """遊戲狀態聚合根"""
    def __init__(self, game_id: str):
        super().__init__(game_id)
        self.round_number = 0
        self.dealt_cards: List[Card] = []
        self.used_cards: Set[Card] = set()
        self.player_arrangement = PlayerArrangement()
        self.opponent_used_cards: Set[Card] = set()
        
    def deal_cards(self, cards: List[Card]):
        """發牌"""
        self.dealt_cards.extend(cards)
        self.raise_domain_event(CardsDealtEvent(self.id, cards))
    
    def place_cards(self, placement: CardPlacement):
        """放置卡牌"""
        # 驗證合法性
        if not self._validate_placement(placement):
            raise DomainException("Invalid placement")
        
        # 更新狀態
        self.player_arrangement.apply_placement(placement)
        self.used_cards.update(placement.cards)
        
        self.raise_domain_event(CardsPlacedEvent(self.id, placement))
    
    def record_opponent_cards(self, cards: List[Card]):
        """記錄對手使用的牌"""
        self.opponent_used_cards.update(cards)

class PlayerArrangement:
    """玩家牌型安排"""
    def __init__(self):
        self.front_hand: Optional[Hand] = None
        self.middle_hand: Optional[Hand] = None
        self.back_hand: Optional[Hand] = None
        
    def is_valid(self) -> bool:
        """驗證牌型大小關係"""
        if not all([self.front_hand, self.middle_hand, self.back_hand]):
            return False
        
        return (self.back_hand.strength >= self.middle_hand.strength >= 
                self.front_hand.strength)
```

### 領域服務

```python
class HandEvaluator(DomainService):
    """手牌評估服務"""
    
    @staticmethod
    @lru_cache(maxsize=100000)
    def evaluate_hand(cards: Tuple[Card, ...]) -> HandEvaluation:
        """評估手牌強度和類型"""
        # 使用tuple以支持緩存
        hand_type = HandEvaluator._determine_hand_type(cards)
        strength = HandEvaluator._calculate_strength(cards, hand_type)
        
        return HandEvaluation(
            hand_type=hand_type,
            strength=strength,
            high_cards=HandEvaluator._get_high_cards(cards, hand_type)
        )
    
    @staticmethod
    def compare_hands(hand1: Hand, hand2: Hand) -> int:
        """比較兩手牌的大小"""
        eval1 = HandEvaluator.evaluate_hand(tuple(hand1.cards))
        eval2 = HandEvaluator.evaluate_hand(tuple(hand2.cards))
        
        if eval1.strength > eval2.strength:
            return 1
        elif eval1.strength < eval2.strength:
            return -1
        else:
            return 0

class ScoringCalculator(DomainService):
    """計分服務"""
    
    def calculate_street_score(self, 
                             player_hand: Hand, 
                             opponent_hand: Hand,
                             position: str) -> int:
        """計算單條街的得分"""
        comparison = HandEvaluator.compare_hands(player_hand, opponent_hand)
        
        if comparison > 0:
            return 1 if position != 'front' else 2
        elif comparison < 0:
            return -1 if position != 'front' else -2
        else:
            return 0
    
    def calculate_bonus_points(self, arrangement: PlayerArrangement) -> Dict[str, int]:
        """計算獎勵分數"""
        bonuses = {}
        
        # 前墩獎勵
        if arrangement.front_hand:
            front_eval = HandEvaluator.evaluate_hand(tuple(arrangement.front_hand.cards))
            bonuses['front'] = self._get_front_bonus(front_eval.hand_type)
        
        # 中墩獎勵
        if arrangement.middle_hand:
            middle_eval = HandEvaluator.evaluate_hand(tuple(arrangement.middle_hand.cards))
            bonuses['middle'] = self._get_middle_bonus(middle_eval.hand_type)
        
        # 後墩獎勵
        if arrangement.back_hand:
            back_eval = HandEvaluator.evaluate_hand(tuple(arrangement.back_hand.cards))
            bonuses['back'] = self._get_back_bonus(back_eval.hand_type)
        
        return bonuses
```

## 技術架構

### 分層架構設計

```yaml
layers:
  presentation:
    - RESTful API (FastAPI)
    - WebSocket for real-time updates
    - JSON response format
    
  application:
    - Command handlers
    - Query handlers
    - Event handlers
    - Coordination logic
    
  domain:
    - Business entities
    - Value objects
    - Domain services
    - Domain events
    
  infrastructure:
    - In-memory data store
    - Cache implementation
    - Logging framework
    - Performance monitoring
```

### 模組依賴關係

```
api
├── depends on → application
│
application  
├── depends on → domain
├── uses → infrastructure
│
domain (pure, no dependencies)
│
infrastructure
├── implements → domain.interfaces
```

### 核心接口定義

```python
# 求解器接口
class ISolver(Protocol):
    """求解器接口"""
    
    def solve(self, game_state: GameState) -> Solution:
        """求解最優擺放"""
        ...
    
    def evaluate_placement(self, 
                         game_state: GameState, 
                         placement: CardPlacement) -> float:
        """評估特定擺放的期望值"""
        ...

# 搜索策略接口
class ISearchStrategy(Protocol):
    """搜索策略接口"""
    
    def search(self, 
              initial_state: SearchNode,
              time_limit: float) -> SearchResult:
        """執行搜索"""
        ...
    
    def should_prune(self, node: SearchNode) -> bool:
        """判斷是否剪枝"""
        ...

# 緩存接口
class ICache(Protocol):
    """緩存接口"""
    
    def get(self, key: str) -> Optional[Any]:
        """獲取緩存值"""
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """設置緩存值"""
        ...
    
    def invalidate(self, pattern: str):
        """使緩存失效"""
        ...
```

## 部署架構

### 環境規劃

```yaml
environments:
  development:
    - Local development
    - SQLite for persistence (if needed)
    - Debug logging enabled
    
  testing:
    - Automated testing environment
    - In-memory data only
    - Performance profiling enabled
    
  production:
    - Optimized build
    - Redis for caching
    - Minimal logging
```

### 擴展策略

```yaml
scaling:
  vertical:
    - CPU optimization (multi-core utilization)
    - Memory optimization (efficient data structures)
    - Cache size tuning
    
  horizontal:
    - Stateless solver instances
    - Load balancing for multiple games
    - Distributed cache (if needed)
```

### 監控方案

```yaml
monitoring:
  metrics:
    - Solver execution time
    - Memory usage
    - Cache hit rate
    - API response time
    
  logging:
    - Structured logging (JSON format)
    - Log levels: ERROR, WARNING, INFO, DEBUG
    - Sensitive data masking
    
  alerts:
    - Solver timeout (> 5 minutes)
    - Memory usage > 80%
    - Error rate > 1%
```

## 架構決策記錄 (ADR)

### ADR-001: 選擇Python作為主要開發語言

**狀態**: accepted

**背景**: 
需要選擇適合實現OFC求解器的編程語言。

**決策**: 
選擇Python 3.11+作為主要開發語言。

**原因**:
- 豐富的科學計算庫（NumPy、SciPy）
- 強大的緩存支持（functools.lru_cache）
- 快速原型開發
- 團隊熟悉度高

**後果**:
- 正面：開發速度快、庫生態豐富
- 負面：性能可能不如C++，需要優化

**緩解措施**:
- 使用Cython優化關鍵路徑
- 考慮使用PyPy提升性能
- 關鍵算法可用C擴展實現

### ADR-002: 採用事件驅動架構

**狀態**: accepted

**背景**:
需要設計靈活、可擴展的系統架構。

**決策**:
採用事件驅動架構，使用領域事件解耦組件。

**原因**:
- 組件解耦，易於維護
- 支持異步處理
- 便於添加新功能
- 方便調試和重播

**後果**:
- 正面：系統靈活性高、易於擴展
- 負面：增加複雜度、可能影響性能

### ADR-003: 使用啟發式搜索而非暴力枚舉

**狀態**: accepted

**背景**:
OFC的搜索空間極大，需要高效的搜索策略。

**決策**:
使用Monte Carlo Tree Search (MCTS)結合領域特定啟發式。

**原因**:
- 能在有限時間內找到較優解
- 可以隨時中斷返回當前最優解
- 適合處理大搜索空間
- 可以結合領域知識

**後果**:
- 正面：性能可控、解質量好
- 負面：不保證找到全局最優解

### ADR-004: 內存數據存儲策略

**狀態**: accepted

**背景**:
需要高性能的數據存儲方案。

**決策**:
使用內存數據結構，不持久化遊戲狀態。

**原因**:
- 單局遊戲時間短
- 性能要求高
- 不需要歷史數據
- 簡化架構

**後果**:
- 正面：性能最優、架構簡單
- 負面：無法恢復中斷的遊戲

### ADR-005: 緩存策略

**狀態**: accepted

**背景**:
手牌評估是性能瓶頸，需要優化。

**決策**:
使用多級緩存策略：
1. LRU緩存手牌評估結果
2. 預計算常見牌型
3. 緩存搜索樹節點評估

**原因**:
- 手牌評估計算密集
- 很多牌型會重複出現
- 空間換時間策略有效

**後果**:
- 正面：顯著提升性能
- 負面：增加內存使用

## 性能優化策略

### 算法優化
1. **並行搜索**: 利用多核CPU並行探索搜索樹
2. **剪枝策略**: 基於上下界的Alpha-Beta剪枝
3. **遞增深化**: 逐步加深搜索深度
4. **換位表**: 存儲已評估的遊戲狀態

### 數據結構優化
1. **位運算表示**: 使用整數位運算表示牌和牌型
2. **緊湊存儲**: 優化內存佈局減少緩存未命中
3. **對象池**: 重用頻繁創建的對象
4. **Copy-on-Write**: 減少狀態複製開銷

### 系統優化
1. **異步I/O**: 使用異步處理提高並發
2. **批處理**: 批量評估多個狀態
3. **預熱緩存**: 啟動時預加載常用數據
4. **JIT編譯**: 使用Numba加速關鍵函數

## 關鍵技術選型

### 核心框架
- **Web框架**: FastAPI (高性能、自動文檔)
- **異步框架**: asyncio + uvloop
- **序列化**: msgpack (比JSON快)

### 算法庫
- **數值計算**: NumPy (向量化運算)
- **組合優化**: OR-Tools (可選)
- **機器學習**: scikit-learn (特徵提取)

### 開發工具
- **類型檢查**: mypy
- **代碼格式化**: black + isort
- **測試框架**: pytest + pytest-asyncio
- **性能分析**: cProfile + line_profiler

### 監控工具
- **APM**: Prometheus + Grafana
- **日誌**: structlog
- **追蹤**: OpenTelemetry

## 總結

本架構設計針對OFC Solver的特點，採用了高性能、可擴展的設計方案：

1. **清晰的分層架構**確保關注點分離
2. **領域驅動設計**準確建模遊戲規則
3. **事件驅動架構**提供靈活性和可擴展性
4. **多級緩存策略**優化性能瓶頸
5. **啟發式搜索算法**平衡解質量和性能

這個架構能夠滿足5分鐘內完成求解的性能要求，同時保持良好的可維護性和可擴展性。