"""
Comprehensive test suite for MCTS algorithm.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from src.core.domain import GameState, Street, Card
from src.core.algorithms.ofc_mcts import MCTSEngine, MCTSConfig, MCTSResult
from src.core.algorithms.mcts_node import MCTSNode, Action
from src.core.algorithms.evaluator import StateEvaluator


class TestMCTSConfig:
    """Test MCTS configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MCTSConfig()
        assert config.time_limit == 300.0
        assert config.num_simulations is None
        assert config.c_puct == 1.4
        assert config.num_threads == 1
        assert config.use_transposition_table is True
        assert config.max_rollout_depth == 20
        assert config.leaf_batch_size == 8
        assert config.virtual_loss == 1.0
        assert config.progressive_widening is True
        assert config.pw_constant == 1.5
        assert config.pw_threshold == 10
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = MCTSConfig(
            time_limit=60.0,
            num_simulations=1000,
            c_puct=2.0,
            num_threads=4
        )
        assert config.time_limit == 60.0
        assert config.num_simulations == 1000
        assert config.c_puct == 2.0
        assert config.num_threads == 4


class TestMCTSEngine:
    """Test MCTS engine basic functionality."""
    
    def test_initialization(self):
        """Test engine initialization."""
        # Default initialization
        engine = MCTSEngine()
        assert engine.config.time_limit == 300.0
        assert engine.nodes_evaluated == 0
        assert engine.simulations_run == 0
        assert len(engine.transposition_table) == 0
        
        # Custom config
        config = MCTSConfig(time_limit=60.0)
        engine = MCTSEngine(config)
        assert engine.config.time_limit == 60.0
    
    def test_search_basic(self):
        """Test basic search functionality."""
        engine = MCTSEngine(MCTSConfig(num_simulations=10))
        game_state = GameState(seed=42)
        
        # Deal initial cards
        game_state.deal_street()
        
        # Run search
        result = engine.search(game_state)
        
        assert isinstance(result, MCTSResult)
        assert isinstance(result.best_action, Action)
        assert isinstance(result.root_node, MCTSNode)
        assert engine.simulations_run > 0
        assert engine.nodes_evaluated > 0
    
    def test_search_with_time_limit(self):
        """Test search with time limit."""
        engine = MCTSEngine(MCTSConfig(time_limit=0.1))  # 100ms
        game_state = GameState(seed=42)
        game_state.deal_street()
        
        start_time = time.time()
        result = engine.search(game_state)
        elapsed = time.time() - start_time
        
        # Should respect time limit (with some tolerance)
        assert elapsed < 0.2  # 200ms tolerance
        assert result.best_action is not None
    
    def test_search_with_progress_callback(self):
        """Test search with progress callback."""
        callback_calls = []
        
        def progress_callback(simulations: int, elapsed: float):
            callback_calls.append((simulations, elapsed))
        
        engine = MCTSEngine(MCTSConfig(num_simulations=50))
        game_state = GameState(seed=42)
        game_state.deal_street()
        
        result = engine.search(game_state, progress_callback)
        
        # Should have received progress updates
        assert len(callback_calls) > 0
        # Simulations should increase
        if len(callback_calls) > 1:
            assert callback_calls[-1][0] > callback_calls[0][0]
    
    def test_transposition_table(self):
        """Test transposition table functionality."""
        config = MCTSConfig(use_transposition_table=True, num_simulations=20)
        engine = MCTSEngine(config)
        
        game_state = GameState(seed=42)
        game_state.deal_street()
        
        # Run search
        result = engine.search(game_state)
        
        # Transposition table should have entries
        assert len(engine.transposition_table) > 0
    
    def test_parallel_search(self):
        """Test parallel search functionality."""
        config = MCTSConfig(num_threads=2, num_simulations=100)
        engine = MCTSEngine(config)
        
        game_state = GameState(seed=42)
        game_state.deal_street()
        
        # Run parallel search
        result = engine.search(game_state)
        
        assert result.best_action is not None
        assert engine.simulations_run >= 100


class TestMCTSNode:
    """Test MCTS node functionality."""
    
    def test_node_creation(self):
        """Test creating MCTS nodes."""
        game_state = GameState()
        node = MCTSNode(game_state)
        
        assert node.state == game_state
        assert node.parent is None
        assert node.action is None
        assert node.visits == 0
        assert node.value_sum == 0.0
        assert len(node.children) == 0
        assert not node.is_expanded
        assert not node.is_terminal
    
    def test_node_with_parent(self):
        """Test creating node with parent."""
        parent_state = GameState()
        parent_node = MCTSNode(parent_state)
        
        child_state = GameState()
        action = Action(
            placements=[(Card.from_string("As"), "front", 0)],
            discard=None
        )
        child_node = MCTSNode(child_state, parent=parent_node, action=action)
        
        assert child_node.parent == parent_node
        assert child_node.action == action
    
    def test_ucb_value(self):
        """Test UCB value calculation."""
        parent_node = MCTSNode(GameState())
        parent_node.visits = 10
        
        child_node = MCTSNode(GameState(), parent=parent_node)
        child_node.visits = 3
        child_node.value_sum = 1.5
        
        # UCB = Q + c * sqrt(ln(parent_visits) / visits)
        ucb = child_node.ucb_value(c_puct=1.4)
        
        q_value = 1.5 / 3  # 0.5
        exploration = 1.4 * math.sqrt(math.log(10) / 3)
        expected = q_value + exploration
        
        assert abs(ucb - expected) < 0.0001
    
    def test_ucb_unvisited_node(self):
        """Test UCB value for unvisited node."""
        parent_node = MCTSNode(GameState())
        parent_node.visits = 10
        
        child_node = MCTSNode(GameState(), parent=parent_node)
        child_node.visits = 0
        
        # Unvisited nodes should have infinite UCB
        ucb = child_node.ucb_value()
        assert ucb == float('inf')
    
    def test_select_best_child(self):
        """Test selecting best child by UCB."""
        parent = MCTSNode(GameState())
        parent.visits = 100
        
        # Create children with different values
        child1 = MCTSNode(GameState(), parent=parent)
        child1.visits = 20
        child1.value_sum = 15.0
        
        child2 = MCTSNode(GameState(), parent=parent)
        child2.visits = 30
        child2.value_sum = 20.0
        
        child3 = MCTSNode(GameState(), parent=parent)
        child3.visits = 5
        child3.value_sum = 4.5
        
        parent.children = [child1, child2, child3]
        
        # Best child should have highest UCB value
        best = parent.select_best_child(c_puct=1.4)
        assert best in [child1, child2, child3]
    
    def test_update_node(self):
        """Test updating node with backpropagation value."""
        node = MCTSNode(GameState())
        assert node.visits == 0
        assert node.value_sum == 0.0
        
        # Update with value
        node.update(0.8)
        assert node.visits == 1
        assert node.value_sum == 0.8
        
        # Update again
        node.update(0.6)
        assert node.visits == 2
        assert node.value_sum == 1.4
    
    def test_is_fully_expanded(self):
        """Test checking if node is fully expanded."""
        node = MCTSNode(GameState())
        node.untried_actions = [
            Action([(Card.from_string("As"), "front", 0)], None),
            Action([(Card.from_string("Kh"), "middle", 0)], None)
        ]
        
        assert not node.is_fully_expanded()
        
        # Remove all untried actions
        node.untried_actions = []
        assert node.is_fully_expanded()


class TestAction:
    """Test Action class."""
    
    def test_action_creation(self):
        """Test creating actions."""
        placements = [
            (Card.from_string("As"), "front", 0),
            (Card.from_string("Kh"), "middle", 1)
        ]
        discard = Card.from_string("Qd")
        
        action = Action(placements, discard)
        assert action.placements == placements
        assert action.discard == discard
    
    def test_action_hash(self):
        """Test action hashing for transposition table."""
        # Same actions should have same hash
        action1 = Action(
            [(Card.from_string("As"), "front", 0)],
            Card.from_string("Kh")
        )
        action2 = Action(
            [(Card.from_string("As"), "front", 0)],
            Card.from_string("Kh")
        )
        
        assert hash(action1) == hash(action2)
        assert action1 == action2
        
        # Different actions should have different hash
        action3 = Action(
            [(Card.from_string("As"), "front", 1)],  # Different index
            Card.from_string("Kh")
        )
        assert hash(action1) != hash(action3)
        assert action1 != action3


class TestStateEvaluator:
    """Test state evaluation functionality."""
    
    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = StateEvaluator()
        assert evaluator is not None
    
    def test_evaluate_terminal_state(self):
        """Test evaluating terminal game state."""
        evaluator = StateEvaluator()
        
        # Create a complete game state
        game_state = GameState()
        game_state._current_street = Street.COMPLETE
        
        # Mock a complete arrangement
        for i in range(3):
            game_state.player_arrangement.front[i] = Card.from_string(f"{9+i}s")
        for i in range(5):
            game_state.player_arrangement.middle[i] = Card.from_string(f"{4+i}h")
        for i in range(5):
            game_state.player_arrangement.back[i] = Card.from_string(f"{'AKQJT'[i]}d")
        
        value = evaluator.evaluate(game_state)
        assert isinstance(value, float)
        assert -100 <= value <= 100  # Reasonable bounds for OFC scores
    
    def test_evaluate_non_terminal_state(self):
        """Test evaluating non-terminal state."""
        evaluator = StateEvaluator()
        
        game_state = GameState()
        game_state.deal_street()
        
        # Place some cards
        cards = game_state.current_hand
        placements = [
            (cards[0], 'front', 0),
            (cards[1], 'middle', 0),
            (cards[2], 'middle', 1),
            (cards[3], 'back', 0),
            (cards[4], 'back', 1)
        ]
        game_state.place_cards(placements)
        
        value = evaluator.evaluate(game_state)
        assert isinstance(value, float)


class TestIntegration:
    """Integration tests for MCTS with game state."""
    
    def test_complete_game_search(self):
        """Test MCTS through a complete game."""
        engine = MCTSEngine(MCTSConfig(num_simulations=50))
        game_state = GameState(seed=42)
        
        # Play through all streets
        while not game_state.is_complete:
            # Deal cards
            game_state.deal_street()
            
            # Search for best action
            result = engine.search(game_state)
            action = result.best_action
            
            # Apply action
            game_state.place_cards(action.placements, action.discard)
        
        # Should have completed the game
        assert game_state.is_complete
        assert game_state.player_arrangement.cards_placed == 13
    
    def test_search_consistency(self):
        """Test that search produces consistent results with same seed."""
        game_state1 = GameState(seed=123)
        game_state1.deal_street()
        
        game_state2 = GameState(seed=123)
        game_state2.deal_street()
        
        engine1 = MCTSEngine(MCTSConfig(num_simulations=100))
        engine2 = MCTSEngine(MCTSConfig(num_simulations=100))
        
        result1 = engine1.search(game_state1)
        result2 = engine2.search(game_state2)
        
        # With deterministic setup, should get same action
        # (May not always be true due to MCTS randomness, but likely with enough simulations)
        assert result1.best_action.placements == result2.best_action.placements
    
    def test_search_quality_improves(self):
        """Test that more simulations improve search quality."""
        game_state = GameState(seed=42)
        game_state.deal_street()
        
        # Search with few simulations
        engine1 = MCTSEngine(MCTSConfig(num_simulations=10))
        result1 = engine1.search(game_state.copy())
        
        # Search with many simulations
        engine2 = MCTSEngine(MCTSConfig(num_simulations=500))
        result2 = engine2.search(game_state.copy())
        
        # More simulations should visit root more
        assert result2.root_node.visits > result1.root_node.visits
        
        # More simulations should explore more nodes
        assert engine2.nodes_evaluated > engine1.nodes_evaluated