# OFC Solver 算法架構設計

## 搜索算法架構

### 核心算法選擇：Monte Carlo Tree Search (MCTS) + 領域啟發式

```
┌─────────────────────────────────────────────────────────────┐
│                    Search Controller                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │Time Manager │  │Thread Pool   │  │ Result Collector│   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      MCTS Engine                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Selection  │  │  Expansion   │  │   Simulation    │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │Backpropagation│ │UCB Formula  │  │  Tree Policy    │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Evaluation Layer                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │Hand Evaluator│ │Score Calculator│ │ EV Estimator   │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Optimization Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Pruning     │  │Transposition │  │  Cache System   │   │
│  │ Strategies  │  │    Table     │  │                 │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## MCTS 實現細節

### 搜索節點定義
```python
@dataclass
class MCTSNode:
    """MCTS搜索節點"""
    state: GameState
    parent: Optional['MCTSNode']
    action: Optional[Action]  # 導致此狀態的動作
    
    # MCTS統計
    visits: int = 0
    total_value: float = 0.0
    
    # 子節點
    children: Dict[Action, 'MCTSNode'] = field(default_factory=dict)
    untried_actions: List[Action] = field(default_factory=list)
    
    # 優化用
    is_terminal: bool = False
    cached_value: Optional[float] = None
    
    @property
    def avg_value(self) -> float:
        """平均價值"""
        return self.total_value / self.visits if self.visits > 0 else 0.0
    
    @property
    def uct_value(self, c: float = 1.414) -> float:
        """UCT值計算（Upper Confidence Bound for Trees）"""
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.avg_value
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        
        return exploitation + exploration

class Action:
    """動作定義"""
    def __init__(self, placements: Dict[Position, List[Card]], 
                 discard: Optional[Card] = None):
        self.placements = placements
        self.discard = discard
        self._hash = self._compute_hash()
    
    def _compute_hash(self) -> int:
        """計算動作的哈希值用於去重"""
        items = []
        for pos, cards in sorted(self.placements.items()):
            items.append((pos, tuple(sorted(c.value for c in cards))))
        if self.discard:
            items.append(('discard', self.discard.value))
        return hash(tuple(items))
    
    def __hash__(self):
        return self._hash
    
    def __eq__(self, other):
        return isinstance(other, Action) and self._hash == other._hash
```

### MCTS主算法
```python
class MCTSEngine:
    """MCTS搜索引擎"""
    
    def __init__(self, config: MCTSConfig):
        self.config = config
        self.evaluator = PositionEvaluator()
        self.action_generator = ActionGenerator()
        self.transposition_table = TranspositionTable(size=config.tt_size)
        
    def search(self, root_state: GameState, time_limit: float) -> Solution:
        """執行MCTS搜索"""
        root = MCTSNode(state=root_state, parent=None, action=None)
        root.untried_actions = self.action_generator.get_legal_actions(root_state)
        
        start_time = time.time()
        iteration = 0
        
        while time.time() - start_time < time_limit:
            # 1. 選擇
            node = self._select(root)
            
            # 2. 擴展
            if not node.is_terminal and node.untried_actions:
                node = self._expand(node)
            
            # 3. 模擬
            value = self._simulate(node)
            
            # 4. 反向傳播
            self._backpropagate(node, value)
            
            iteration += 1
            
            # 定期檢查和報告進度
            if iteration % 1000 == 0:
                self._report_progress(root, time.time() - start_time, time_limit)
        
        # 返回最佳解決方案
        return self._extract_solution(root)
    
    def _select(self, node: MCTSNode) -> MCTSNode:
        """選擇階段：使用UCT選擇最有希望的節點"""
        while not node.is_terminal and not node.untried_actions:
            # 使用UCT公式選擇子節點
            node = max(node.children.values(), 
                      key=lambda n: n.uct_value(self.config.exploration_constant))
        return node
    
    def _expand(self, node: MCTSNode) -> MCTSNode:
        """擴展階段：添加一個新的子節點"""
        # 選擇一個未嘗試的動作
        action = self._select_expansion_action(node)
        node.untried_actions.remove(action)
        
        # 創建新狀態
        new_state = self._apply_action(node.state, action)
        
        # 檢查換位表
        tt_entry = self.transposition_table.get(new_state)
        if tt_entry:
            # 使用已有的評估結果
            child = MCTSNode(state=new_state, parent=node, action=action)
            child.cached_value = tt_entry.value
        else:
            child = MCTSNode(state=new_state, parent=node, action=action)
            child.untried_actions = self.action_generator.get_legal_actions(new_state)
            child.is_terminal = (new_state.phase == GamePhase.COMPLETED)
        
        node.children[action] = child
        return child
    
    def _simulate(self, node: MCTSNode) -> float:
        """模擬階段：快速評估節點價值"""
        if node.cached_value is not None:
            return node.cached_value
        
        if node.is_terminal:
            # 終局評估
            value = self.evaluator.evaluate_final_position(node.state)
        else:
            # 使用啟發式評估 + 輕量級模擬
            value = self._heuristic_simulation(node.state)
        
        # 存儲到換位表
        self.transposition_table.store(node.state, value)
        node.cached_value = value
        
        return value
    
    def _backpropagate(self, node: MCTSNode, value: float):
        """反向傳播階段：更新路徑上的所有節點"""
        while node is not None:
            node.visits += 1
            node.total_value += value
            node = node.parent
    
    def _select_expansion_action(self, node: MCTSNode) -> Action:
        """選擇擴展動作（使用領域知識）"""
        if self.config.use_heuristics:
            # 基於啟發式評分選擇動作
            action_scores = []
            for action in node.untried_actions:
                score = self._evaluate_action_heuristic(node.state, action)
                action_scores.append((action, score))
            
            # 使用概率選擇（更好的動作有更高概率被選中）
            actions, scores = zip(*action_scores)
            probabilities = softmax(scores, temperature=self.config.action_temperature)
            
            return np.random.choice(actions, p=probabilities)
        else:
            # 隨機選擇
            return random.choice(node.untried_actions)
```

### 啟發式評估器
```python
class PositionEvaluator:
    """位置評估器"""
    
    def __init__(self):
        self.hand_evaluator = HandEvaluator()
        self.bonus_calculator = BonusCalculator()
        self.pattern_matcher = PatternMatcher()
        
    def evaluate_final_position(self, state: GameState) -> float:
        """評估最終位置的期望值"""
        arrangement = state.player_arrangement
        
        if not arrangement.is_complete or not arrangement.is_valid:
            return -1000.0  # 無效擺放
        
        # 計算對陣所有可能對手的期望值
        opponent_distribution = self._estimate_opponent_distribution(state)
        expected_value = 0.0
        
        for opponent_arrangement, probability in opponent_distribution:
            score = self._calculate_matchup_score(arrangement, opponent_arrangement)
            expected_value += score * probability
        
        return expected_value
    
    def evaluate_partial_position(self, state: GameState) -> float:
        """評估部分完成的位置"""
        # 已完成部分的確定價值
        completed_value = self._evaluate_completed_streets(state)
        
        # 未完成部分的期望價值
        potential_value = self._evaluate_potential(state)
        
        # 風險調整
        risk_penalty = self._calculate_risk_penalty(state)
        
        return completed_value + potential_value - risk_penalty
    
    def _evaluate_completed_streets(self, state: GameState) -> float:
        """評估已完成的街道"""
        value = 0.0
        arrangement = state.player_arrangement
        
        # 評估每條街的強度
        if arrangement.front and arrangement.front.is_valid_size():
            value += self._street_strength_value(arrangement.front, Position.FRONT)
        
        if arrangement.middle and arrangement.middle.is_valid_size():
            value += self._street_strength_value(arrangement.middle, Position.MIDDLE)
        
        if arrangement.back and arrangement.back.is_valid_size():
            value += self._street_strength_value(arrangement.back, Position.BACK)
        
        return value
    
    def _street_strength_value(self, hand: Hand, position: Position) -> float:
        """計算街道強度的價值"""
        hand_type = hand.hand_type
        
        # 基礎價值表
        base_values = {
            Position.FRONT: {
                HandType.HIGH_CARD: 0,
                HandType.PAIR: 3,
                HandType.THREE_OF_KIND: 10,
            },
            Position.MIDDLE: {
                HandType.HIGH_CARD: 0,
                HandType.PAIR: 1,
                HandType.TWO_PAIR: 2,
                HandType.THREE_OF_KIND: 4,
                HandType.STRAIGHT: 6,
                HandType.FLUSH: 8,
                HandType.FULL_HOUSE: 12,
                HandType.FOUR_OF_KIND: 20,
                HandType.STRAIGHT_FLUSH: 30,
            },
            Position.BACK: {
                HandType.HIGH_CARD: 0,
                HandType.PAIR: 0.5,
                HandType.TWO_PAIR: 1,
                HandType.THREE_OF_KIND: 2,
                HandType.STRAIGHT: 3,
                HandType.FLUSH: 4,
                HandType.FULL_HOUSE: 6,
                HandType.FOUR_OF_KIND: 10,
                HandType.STRAIGHT_FLUSH: 15,
            }
        }
        
        position_values = base_values.get(position, {})
        return position_values.get(hand_type.category, 0)
```

### 動作生成器
```python
class ActionGenerator:
    """動作生成器：生成合法的動作"""
    
    def __init__(self):
        self.placement_patterns = self._init_placement_patterns()
        
    def get_legal_actions(self, state: GameState) -> List[Action]:
        """生成所有合法動作"""
        if state.phase == GamePhase.INITIAL_DEAL:
            return self._generate_initial_placement_actions(state)
        elif state.phase == GamePhase.PLACEMENT:
            return self._generate_round_placement_actions(state)
        else:
            return []
    
    def _generate_initial_placement_actions(self, state: GameState) -> List[Action]:
        """生成初始5張牌的所有擺放方式"""
        cards = state.dealt_cards
        actions = []
        
        # 使用預定義的擺放模式
        for pattern in self.placement_patterns['initial']:
            if self._is_pattern_applicable(pattern, cards):
                action = self._apply_pattern(pattern, cards)
                if self._is_valid_placement(state, action):
                    actions.append(action)
        
        # 如果模式不夠，生成更多
        if len(actions) < 100:
            actions.extend(self._generate_exhaustive_placements(state, cards))
        
        return actions
    
    def _generate_round_placement_actions(self, state: GameState) -> List[Action]:
        """生成每輪3張牌的擺放方式（2張擺放+1張棄牌）"""
        available_cards = [c for c in state.dealt_cards if c not in state.placed_cards.to_list()]
        
        if len(available_cards) != 3:
            return []
        
        actions = []
        
        # 枚舉所有2張牌的組合
        for placed_cards in itertools.combinations(available_cards, 2):
            discard = [c for c in available_cards if c not in placed_cards][0]
            
            # 枚舉這2張牌的所有可能擺放位置
            for placement in self._generate_two_card_placements(state, list(placed_cards)):
                action = Action(placement, discard)
                if self._is_valid_placement(state, action):
                    actions.append(action)
        
        return actions
    
    def _generate_two_card_placements(self, state: GameState, 
                                    cards: List[Card]) -> List[Dict[Position, List[Card]]]:
        """生成2張牌的所有可能擺放方式"""
        placements = []
        positions = [Position.FRONT, Position.MIDDLE, Position.BACK]
        
        # 兩張牌放在同一位置
        for pos in positions:
            if self._can_place_cards_at(state, cards, pos):
                placements.append({pos: cards})
        
        # 兩張牌分別放在不同位置
        for pos1, pos2 in itertools.combinations(positions, 2):
            if (self._can_place_cards_at(state, [cards[0]], pos1) and
                self._can_place_cards_at(state, [cards[1]], pos2)):
                placements.append({pos1: [cards[0]], pos2: [cards[1]]})
            
            if (self._can_place_cards_at(state, [cards[1]], pos1) and
                self._can_place_cards_at(state, [cards[0]], pos2)):
                placements.append({pos1: [cards[1]], pos2: [cards[0]]})
        
        return placements
```

### 剪枝策略
```python
class PruningStrategy:
    """剪枝策略"""
    
    def __init__(self, config: PruningConfig):
        self.config = config
        self.bound_calculator = BoundCalculator()
        
    def should_prune(self, node: MCTSNode, best_value: float) -> bool:
        """判斷是否應該剪枝此節點"""
        # 1. Alpha-Beta剪枝
        if self.config.use_alpha_beta:
            upper_bound = self.bound_calculator.calculate_upper_bound(node.state)
            if upper_bound < best_value - self.config.pruning_margin:
                return True
        
        # 2. 無效擺放剪枝
        if node.state.player_arrangement.is_complete:
            if not node.state.player_arrangement.is_valid:
                return True
        
        # 3. 統計顯著性剪枝
        if self.config.use_statistical_pruning and node.visits > 100:
            confidence_interval = self._calculate_confidence_interval(node)
            if confidence_interval.upper < best_value - self.config.confidence_margin:
                return True
        
        return False
    
    def order_children(self, children: List[MCTSNode]) -> List[MCTSNode]:
        """對子節點排序以提高剪枝效率"""
        # 使用多個標準排序
        def sort_key(node):
            # 優先訪問次數多的
            visit_score = math.log(node.visits + 1)
            
            # 其次是平均價值高的
            value_score = node.avg_value
            
            # 考慮啟發式評分
            heuristic_score = self._get_heuristic_score(node)
            
            return (visit_score * 0.3 + value_score * 0.5 + heuristic_score * 0.2)
        
        return sorted(children, key=sort_key, reverse=True)
```

### 並行化策略
```python
class ParallelMCTS:
    """並行MCTS實現"""
    
    def __init__(self, config: ParallelConfig):
        self.config = config
        self.thread_pool = ThreadPoolExecutor(max_workers=config.num_threads)
        self.shared_tree = SharedTree()  # 線程安全的共享樹
        
    def search_parallel(self, root_state: GameState, time_limit: float) -> Solution:
        """並行搜索"""
        # 1. Root並行化：多個線程從根節點開始搜索
        if self.config.parallelization_type == "root":
            return self._root_parallel_search(root_state, time_limit)
        
        # 2. Leaf並行化：並行評估葉節點
        elif self.config.parallelization_type == "leaf":
            return self._leaf_parallel_search(root_state, time_limit)
        
        # 3. Tree並行化：每個線程維護自己的樹
        else:
            return self._tree_parallel_search(root_state, time_limit)
    
    def _root_parallel_search(self, root_state: GameState, time_limit: float):
        """Root並行化：所有線程共享同一棵樹"""
        root = self.shared_tree.create_root(root_state)
        
        # 創建多個搜索任務
        futures = []
        for i in range(self.config.num_threads):
            future = self.thread_pool.submit(
                self._worker_search,
                root,
                time_limit / self.config.num_threads,
                worker_id=i
            )
            futures.append(future)
        
        # 等待所有任務完成
        for future in futures:
            future.result()
        
        return self._extract_solution(root)
    
    def _worker_search(self, root: MCTSNode, time_limit: float, worker_id: int):
        """工作線程的搜索邏輯"""
        engine = MCTSEngine(self.config.mcts_config)
        start_time = time.time()
        
        while time.time() - start_time < time_limit:
            # 使用虛擬損失避免多個線程選擇相同路徑
            with self.shared_tree.virtual_loss(root):
                node = engine._select(root)
                
                if not node.is_terminal and node.untried_actions:
                    node = engine._expand(node)
                
                value = engine._simulate(node)
                engine._backpropagate(node, value)
```

## 性能優化實現

### 緩存系統
```python
class CacheSystem:
    """多級緩存系統"""
    
    def __init__(self, config: CacheConfig):
        # L1: 手牌評估緩存
        self.hand_cache = LRUCache(maxsize=config.hand_cache_size)
        
        # L2: 位置評估緩存
        self.position_cache = LRUCache(maxsize=config.position_cache_size)
        
        # L3: 動作評估緩存
        self.action_cache = TTLCache(maxsize=config.action_cache_size, ttl=300)
        
        # 預計算常見牌型
        self._precompute_common_hands()
    
    def _precompute_common_hands(self):
        """預計算常見牌型的評估結果"""
        # 預計算所有可能的3張牌組合（前墩）
        for cards in itertools.combinations(range(52), 3):
            hand = Hand("precompute", [Card(c) for c in cards], Position.FRONT)
            self.hand_cache.set(hand.cache_key(), hand.hand_type)
        
        # 預計算高價值5張牌組合
        valuable_patterns = [
            # 同花順
            lambda cards: self._is_straight_flush(cards),
            # 四條
            lambda cards: self._is_four_of_kind(cards),
            # 葫蘆
            lambda cards: self._is_full_house(cards),
        ]
        
        for pattern in valuable_patterns:
            self._precompute_pattern(pattern)
```

### 位運算優化
```python
class BitOperations:
    """位運算優化的牌型識別"""
    
    # 預計算表
    RANK_MASKS = [1 << i for i in range(13)]
    SUIT_MASKS = [0x1111111111111 << i for i in range(4)]
    
    @staticmethod
    def cards_to_bitmask(cards: List[Card]) -> int:
        """將卡牌列表轉換為位掩碼"""
        mask = 0
        for card in cards:
            mask |= 1 << card.value
        return mask
    
    @staticmethod
    def is_flush(mask: int) -> bool:
        """檢測是否為同花"""
        for suit_mask in BitOperations.SUIT_MASKS:
            if bin(mask & suit_mask).count('1') >= 5:
                return True
        return False
    
    @staticmethod
    def is_straight(mask: int) -> bool:
        """檢測是否為順子"""
        # 提取所有rank
        ranks = 0
        for i in range(52):
            if mask & (1 << i):
                ranks |= 1 << (i % 13)
        
        # 檢查5連續位
        straight_mask = 0b11111
        for i in range(9):
            if (ranks >> i) & straight_mask == straight_mask:
                return True
        
        # 檢查A-2-3-4-5
        if ranks & 0b1000000001111 == 0b1000000001111:
            return True
        
        return False
```

### 內存池
```python
class ObjectPool:
    """對象池減少GC壓力"""
    
    def __init__(self, factory, max_size=10000):
        self.factory = factory
        self.pool = []
        self.max_size = max_size
        self.created = 0
        self.reused = 0
    
    def acquire(self):
        """獲取對象"""
        if self.pool:
            self.reused += 1
            return self.pool.pop()
        else:
            self.created += 1
            return self.factory()
    
    def release(self, obj):
        """釋放對象"""
        if len(self.pool) < self.max_size:
            # 重置對象狀態
            if hasattr(obj, 'reset'):
                obj.reset()
            self.pool.append(obj)

# 使用對象池
node_pool = ObjectPool(lambda: MCTSNode(None, None, None))
action_pool = ObjectPool(lambda: Action({}, None))
```

## 性能基準測試

### 測試場景
```python
class PerformanceBenchmark:
    """性能基準測試"""
    
    def __init__(self):
        self.scenarios = {
            'initial_placement': self._create_initial_placement_scenario,
            'mid_game': self._create_mid_game_scenario,
            'end_game': self._create_end_game_scenario,
            'complex_decision': self._create_complex_decision_scenario,
        }
    
    def run_benchmark(self, solver: Solver, scenario_name: str, iterations: int = 100):
        """運行基準測試"""
        scenario_creator = self.scenarios[scenario_name]
        times = []
        qualities = []
        
        for i in range(iterations):
            game_state = scenario_creator()
            
            start_time = time.time()
            solution = solver.solve(game_state, time_limit=300)
            elapsed = time.time() - start_time
            
            times.append(elapsed)
            qualities.append(solution.expected_value)
        
        return {
            'scenario': scenario_name,
            'avg_time': np.mean(times),
            'std_time': np.std(times),
            'avg_quality': np.mean(qualities),
            'std_quality': np.std(qualities),
            'min_time': np.min(times),
            'max_time': np.max(times),
        }
```

### 性能指標
```yaml
performance_targets:
  initial_placement:
    time_limit: 60s
    expected_quality: 0.8  # 相對於最優解的比率
    
  per_round:
    time_limit: 60s
    expected_quality: 0.85
    
  end_game:
    time_limit: 30s
    expected_quality: 0.9
    
  memory_usage:
    max_heap: 2GB
    max_cache: 500MB
    
  cpu_usage:
    utilization: 80-95%  # 多核利用率
    
  scalability:
    threads: 1-8
    speedup: near-linear  # 理想加速比
```

## 算法改進路線圖

### 短期優化 (1-2週)
1. 實現基礎MCTS框架
2. 添加簡單啟發式評估
3. 實現位運算優化
4. 基礎緩存系統

### 中期優化 (1個月)
1. 完善剪枝策略
2. 實現並行搜索
3. 優化內存使用
4. 添加機器學習評估器

### 長期優化 (3個月)
1. 神經網絡指導的MCTS
2. 開局庫和殘局庫
3. 自適應搜索深度
4. 對手建模

這個算法架構設計提供了一個高性能、可擴展的OFC求解器實現方案，能夠在5分鐘內找到高質量的解決方案。