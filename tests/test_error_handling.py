"""
Test suite for error handling in OFC Solver.

This module tests all custom exceptions and error handling mechanisms,
ensuring they provide clear error messages and proper recovery options.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
import threading
import psutil

from src.exceptions import (
    OFCError, InvalidInputError, TimeoutError, ResourceError,
    GameRuleViolationError, SolverError, ConfigurationError, StateError,
    invalid_card_error, duplicate_card_error, timeout_error,
    memory_error, invalid_placement_error
)
from src.validation import (
    validate_card, validate_card_list, validate_game_state,
    with_timeout, with_error_recovery, ensure_resources,
    validate_placement, validate_config
)
from src.core.domain import Card, GameState, PlayerArrangement, Street
from src.ofc_solver import OFCSolver, SolverConfig, SolveResult


class TestExceptions(unittest.TestCase):
    """Test custom exception classes."""
    
    def test_base_exception(self):
        """Test OFCError base exception."""
        error = OFCError("Test error", {"key": "value"}, "TEST_CODE")
        
        self.assertEqual(str(error), "Test error (key=value)")
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.details, {"key": "value"})
        self.assertEqual(error.error_code, "TEST_CODE")
    
    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        error = InvalidInputError("Invalid card", input_value="XX", expected_format="[R][S]")
        
        self.assertIn("Invalid card", str(error))
        self.assertEqual(error.details["input_value"], "XX")
        self.assertEqual(error.details["expected_format"], "[R][S]")
        self.assertEqual(error.error_code, "INVALID_INPUT")
    
    def test_timeout_error_with_partial_result(self):
        """Test TimeoutError with partial results."""
        partial = {"best_action": Mock(), "simulations": 1000}
        error = TimeoutError("Search timeout", 10.0, 15.5, partial_result=partial)
        
        self.assertIn("Search timeout", str(error))
        self.assertEqual(error.details["time_limit"], 10.0)
        self.assertEqual(error.details["elapsed_time"], 15.5)
        self.assertTrue(error.details["has_partial_result"])
        self.assertEqual(error.partial_result, partial)
    
    def test_resource_error(self):
        """Test ResourceError."""
        error = ResourceError("Out of memory", "memory", available=100.0, required=500.0)
        
        self.assertIn("Out of memory", str(error))
        self.assertEqual(error.details["resource_type"], "memory")
        self.assertEqual(error.details["available"], 100.0)
        self.assertEqual(error.details["required"], 500.0)
    
    def test_game_rule_violation_error(self):
        """Test GameRuleViolationError."""
        game_state = Mock()
        error = GameRuleViolationError(
            "Invalid placement", 
            "card_placement",
            game_state=game_state,
            position="front"
        )
        
        self.assertIn("Invalid placement", str(error))
        self.assertEqual(error.details["rule_violated"], "card_placement")
        self.assertTrue(error.details["has_game_state"])
        self.assertEqual(error.game_state, game_state)
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid time limit", parameter="time_limit", value=-1)
        
        self.assertIn("Invalid time limit", str(error))
        self.assertEqual(error.details["parameter"], "time_limit")
        self.assertEqual(error.details["value"], "-1")
    
    def test_state_error(self):
        """Test StateError."""
        error = StateError("Invalid transition", "playing", expected_state="waiting")
        
        self.assertIn("Invalid transition", str(error))
        self.assertEqual(error.details["current_state"], "playing")
        self.assertEqual(error.details["expected_state"], "waiting")


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience error creation functions."""
    
    def test_invalid_card_error(self):
        """Test invalid_card_error helper."""
        error = invalid_card_error("XX")
        
        self.assertIsInstance(error, InvalidInputError)
        self.assertIn("Invalid card representation", str(error))
        self.assertEqual(error.details["input_value"], "XX")
        self.assertIn("expected_format", error.details)
    
    def test_duplicate_card_error(self):
        """Test duplicate_card_error helper."""
        card = Card.from_string("AS")
        error = duplicate_card_error(card)
        
        self.assertIsInstance(error, InvalidInputError)
        self.assertIn("Duplicate card detected", str(error))
        self.assertEqual(error.details["error_type"], "duplicate")
    
    def test_timeout_error_helper(self):
        """Test timeout_error helper."""
        partial = {"simulations": 1000}
        error = timeout_error("search", 10.0, 15.0, partial)
        
        self.assertIsInstance(error, TimeoutError)
        self.assertIn("search", str(error))
        self.assertEqual(error.partial_result, partial)
    
    def test_memory_error_helper(self):
        """Test memory_error helper."""
        error = memory_error(500.0, 100.0)
        
        self.assertIsInstance(error, ResourceError)
        self.assertIn("Insufficient memory", str(error))
        self.assertEqual(error.details["required"], 500.0)
        self.assertEqual(error.details["available"], 100.0)
    
    def test_invalid_placement_error(self):
        """Test invalid_placement_error helper."""
        card = Card.from_string("KH")
        error = invalid_placement_error(card, "front", "position occupied")
        
        self.assertIsInstance(error, GameRuleViolationError)
        self.assertIn("Cannot place", str(error))
        self.assertEqual(error.details["position"], "front")
        self.assertEqual(error.details["reason"], "position occupied")


class TestValidation(unittest.TestCase):
    """Test validation functions and decorators."""
    
    def test_validate_card_with_valid_string(self):
        """Test validate_card with valid string."""
        card = validate_card("AS")
        
        self.assertIsInstance(card, Card)
        self.assertEqual(str(card), "A♠")
    
    def test_validate_card_with_card_object(self):
        """Test validate_card with Card object."""
        original = Card.from_string("KH")
        card = validate_card(original)
        
        self.assertEqual(card, original)
    
    def test_validate_card_with_invalid_input(self):
        """Test validate_card with invalid inputs."""
        with self.assertRaises(InvalidInputError) as ctx:
            validate_card(123)
        self.assertIn("must be a string or Card object", str(ctx.exception))
        
        with self.assertRaises(InvalidInputError) as ctx:
            validate_card("XX")
        self.assertIn("Invalid card string", str(ctx.exception))
    
    def test_validate_card_list(self):
        """Test validate_card_list."""
        cards = validate_card_list(["AS", "KH", "QD"])
        
        self.assertEqual(len(cards), 3)
        self.assertEqual(str(cards[0]), "A♠")
        self.assertEqual(str(cards[1]), "K♥")
        self.assertEqual(str(cards[2]), "Q♦")
    
    def test_validate_card_list_with_duplicates(self):
        """Test validate_card_list with duplicate cards."""
        with self.assertRaises(InvalidInputError) as ctx:
            validate_card_list(["AS", "KH", "AS"])
        
        self.assertIn("Duplicate card", str(ctx.exception))
        self.assertEqual(ctx.exception.details["duplicate_index"], 2)
    
    def test_validate_card_list_invalid_type(self):
        """Test validate_card_list with invalid type."""
        with self.assertRaises(InvalidInputError) as ctx:
            validate_card_list("not a list")
        
        self.assertIn("must be a list", str(ctx.exception))
    
    def test_validate_placement(self):
        """Test validate_placement function."""
        arrangement = PlayerArrangement()
        
        # Valid placement
        validate_placement("front", 0, arrangement)  # Should not raise
        
        # Invalid position name
        with self.assertRaises(GameRuleViolationError) as ctx:
            validate_placement("invalid", 0, arrangement)
        self.assertIn("Invalid position", str(ctx.exception))
        
        # Invalid index
        with self.assertRaises(GameRuleViolationError) as ctx:
            validate_placement("front", 5, arrangement)
        self.assertIn("Invalid index", str(ctx.exception))
        
        # Occupied position
        arrangement.front[0] = Card.from_string("AS")
        with self.assertRaises(GameRuleViolationError) as ctx:
            validate_placement("front", 0, arrangement)
        self.assertIn("already occupied", str(ctx.exception))


class TestDecorators(unittest.TestCase):
    """Test validation decorators."""
    
    def test_validate_input_decorator(self):
        """Test @validate_input decorator."""
        from src.validation import validate_input
        
        @validate_input(lambda x: x > 0, "Value must be positive")
        def process_value(value: int) -> int:
            return value * 2
        
        # Valid input
        self.assertEqual(process_value(5), 10)
        
        # Invalid input
        with self.assertRaises(InvalidInputError) as ctx:
            process_value(-1)
        self.assertIn("Value must be positive", str(ctx.exception))
    
    def test_validate_game_state_decorator(self):
        """Test @validate_game_state decorator."""
        @validate_game_state
        def process_game(game_state: GameState) -> str:
            return f"Processing {game_state.current_street.name}"
        
        # Valid game state
        game = GameState(num_players=2, player_index=0)
        result = process_game(game)
        self.assertIn("INITIAL", result)
        
        # Completed game state
        game.is_complete = True
        with self.assertRaises(StateError) as ctx:
            process_game(game)
        self.assertIn("completed game", str(ctx.exception))
        
        # Invalid player index
        game = GameState(num_players=2, player_index=5)
        game.is_complete = False
        with self.assertRaises(InvalidInputError) as ctx:
            process_game(game)
        self.assertIn("Invalid player index", str(ctx.exception))
    
    def test_with_timeout_decorator(self):
        """Test @with_timeout decorator."""
        @with_timeout(0.5, operation_name="test_operation")
        def slow_function(duration: float) -> str:
            time.sleep(duration)
            return "completed"
        
        # Within timeout
        result = slow_function(0.1)
        self.assertEqual(result, "completed")
        
        # Exceeds timeout
        with self.assertRaises(TimeoutError) as ctx:
            slow_function(1.0)
        self.assertIn("test_operation", str(ctx.exception))
        self.assertEqual(ctx.exception.details["time_limit"], 0.5)
    
    def test_with_error_recovery_decorator(self):
        """Test @with_error_recovery decorator."""
        @with_error_recovery(default_return="recovered", 
                           recoverable_errors=(ResourceError, TimeoutError))
        def risky_function(should_fail: bool) -> str:
            if should_fail:
                raise ResourceError("Out of memory", "memory")
            return "success"
        
        # Normal execution
        self.assertEqual(risky_function(False), "success")
        
        # Recoverable error
        self.assertEqual(risky_function(True), "recovered")
        
        # Non-recoverable error
        @with_error_recovery(default_return="recovered",
                           recoverable_errors=(TimeoutError,))
        def other_risky_function():
            raise ValueError("Unrecoverable")
        
        with self.assertRaises(ValueError):
            other_risky_function()
    
    @patch('psutil.virtual_memory')
    def test_ensure_resources_decorator(self, mock_memory):
        """Test @ensure_resources decorator."""
        # Mock memory info
        mock_memory.return_value = Mock(available=200 * 1024 * 1024)  # 200MB
        
        @ensure_resources(memory_mb=100)
        def memory_intensive_task() -> str:
            return "completed"
        
        # Sufficient memory
        result = memory_intensive_task()
        self.assertEqual(result, "completed")
        
        # Insufficient memory
        @ensure_resources(memory_mb=500)
        def very_memory_intensive_task() -> str:
            return "completed"
        
        with self.assertRaises(ResourceError) as ctx:
            very_memory_intensive_task()
        self.assertIn("Insufficient memory", str(ctx.exception))


class TestSolverErrorHandling(unittest.TestCase):
    """Test error handling in OFCSolver."""
    
    def test_solver_config_validation(self):
        """Test SolverConfig validation."""
        # Valid config
        config = SolverConfig(time_limit=10.0, num_threads=4)
        self.assertEqual(config.time_limit, 10.0)
        
        # Invalid time limit
        with self.assertRaises(ConfigurationError) as ctx:
            SolverConfig(time_limit=-1.0)
        self.assertIn("Time limit must be positive", str(ctx.exception))
        
        # Invalid thread count
        with self.assertRaises(ConfigurationError) as ctx:
            SolverConfig(num_threads=0)
        self.assertIn("threads must be at least 1", str(ctx.exception))
        
        # Invalid exploration constant
        with self.assertRaises(ConfigurationError) as ctx:
            SolverConfig(c_puct=-0.5)
        self.assertIn("must be positive", str(ctx.exception))
    
    def test_solver_initialization_error(self):
        """Test error handling during solver initialization."""
        with patch('src.ofc_solver.ActionGenerator', side_effect=Exception("Init failed")):
            with self.assertRaises(SolverError) as ctx:
                OFCSolver(SolverConfig(use_action_generator=True))
            self.assertIn("Failed to initialize solver", str(ctx.exception))
    
    def test_solve_invalid_input(self):
        """Test solve() with invalid input."""
        solver = OFCSolver(SolverConfig(time_limit=1.0))
        
        # Not a GameState
        with self.assertRaises(InvalidInputError) as ctx:
            solver.solve("not a game state")
        self.assertIn("must be a GameState instance", str(ctx.exception))
    
    @patch('src.ofc_solver.MCTSEngine')
    def test_solve_with_timeout(self, mock_mcts):
        """Test solve() handling timeout."""
        solver = OFCSolver(SolverConfig(time_limit=1.0, return_partial_on_timeout=True))
        game = GameState(num_players=2, player_index=0)
        
        # Mock MCTS to raise timeout
        mock_engine = Mock()
        mock_mcts.return_value = mock_engine
        mock_engine.search.side_effect = TimeoutError(
            "Search timeout", 1.0, 1.5,
            partial_result={
                'best_action': Mock(),
                'expected_score': 5.0,
                'simulations': 1000,
                'top_actions': [],
                'statistics': {}
            }
        )
        
        # Should return partial result
        result = solver.solve(game)
        self.assertFalse(result.is_complete)
        self.assertEqual(result.expected_score, 5.0)
        self.assertEqual(result.num_simulations, 1000)
        self.assertIsNotNone(result.error_info)
    
    @patch('src.ofc_solver.psutil.Process')
    @patch('src.ofc_solver.psutil.virtual_memory')
    def test_solve_with_resource_error(self, mock_vm, mock_process):
        """Test solve() handling resource errors."""
        # Mock memory shortage
        mock_process.return_value.memory_info.return_value = Mock(rss=1000 * 1024 * 1024)
        mock_vm.return_value = Mock(available=50 * 1024 * 1024)
        
        solver = OFCSolver(SolverConfig(memory_limit_mb=100))
        game = GameState(num_players=2, player_index=0)
        
        # Should attempt recovery with single thread
        with patch.object(solver, '_resource_monitor') as mock_monitor:
            mock_monitor.check_memory.side_effect = [
                ResourceError("Out of memory", "memory", available=50, required=100),
                None  # Success on retry
            ]
            
            with patch('src.ofc_solver.MCTSEngine') as mock_mcts:
                mock_engine = Mock()
                mock_mcts.return_value = mock_engine
                mock_result = Mock()
                mock_result.root_node = Mock(average_reward=10.0, visit_count=100)
                mock_result.root_node.get_action_statistics.return_value = []
                mock_result.best_action = Mock()
                mock_engine.search.return_value = mock_result
                mock_engine.get_statistics.return_value = {'simulations': 1000}
                
                result = solver.solve(game)
                
                # Should have reduced to single thread
                self.assertEqual(solver.mcts_config.num_threads, 1)
    
    def test_solve_game_error_handling(self):
        """Test solve_game() error handling."""
        solver = OFCSolver(SolverConfig(time_limit=1.0))
        
        # Invalid initial state
        with self.assertRaises(InvalidInputError) as ctx:
            solver.solve_game(initial_state="invalid")
        self.assertIn("must be a GameState instance", str(ctx.exception))
        
        # Test with mock game state that fails on deal
        game = Mock(spec=GameState)
        game.is_complete = False
        game.current_hand = []
        game.current_street = Mock(name="INITIAL")
        game.deal_street.side_effect = Exception("Deal failed")
        
        with self.assertRaises(StateError) as ctx:
            solver.solve_game(game)
        self.assertIn("Failed to deal cards", str(ctx.exception))
    
    def test_analyze_position_error_handling(self):
        """Test analyze_position() error handling."""
        solver = OFCSolver()
        
        # Invalid input
        with self.assertRaises(InvalidInputError):
            solver.analyze_position("not a game state")
        
        # Test with mock that fails evaluation
        game = Mock(spec=GameState)
        game.current_street = Mock(name="FLOP")
        game.current_hand = []
        game.player_arrangement = Mock(cards_placed=5)
        game.is_complete = False
        game.player_arrangement.is_valid_progressive.side_effect = Exception("Validation failed")
        
        result = solver.analyze_position(game)
        self.assertIn("Validation failed", result['errors'][0])


class TestBDDScenarios(unittest.TestCase):
    """Test BDD scenarios from IMMEDIATE_ACTION_PLAN.md."""
    
    def test_invalid_hand_input_scenario(self):
        """Test Scenario: Invalid hand input."""
        solver = OFCSolver()
        game = GameState(num_players=2, player_index=0)
        
        # Create invalid game state
        game.current_hand = ["invalid", "cards"]
        
        with self.assertRaises(InvalidInputError) as ctx:
            # This will fail during card validation
            solver.analyze_position(game)
        
        # Error should have clear message
        self.assertIsNotNone(ctx.exception.message)
        self.assertIn("error", str(ctx.exception.details))
    
    @patch('time.time')
    def test_timeout_handling_scenario(self, mock_time):
        """Test Scenario: Timeout handling."""
        # Mock time to simulate timeout
        start_time = 100.0
        mock_time.side_effect = [
            start_time,  # Start time
            start_time + 5,  # First check
            start_time + 11,  # Timeout!
        ]
        
        solver = OFCSolver(SolverConfig(
            time_limit=10.0,
            return_partial_on_timeout=True
        ))
        
        game = GameState(num_players=2, player_index=0)
        
        with patch('src.ofc_solver.MCTSEngine') as mock_mcts:
            mock_engine = Mock()
            mock_mcts.return_value = mock_engine
            
            # Simulate timeout during search
            mock_engine.search.side_effect = TimeoutError(
                "Search timeout", 10.0, 11.0,
                partial_result={
                    'best_action': Mock(),
                    'expected_score': 3.5,
                    'simulations': 5000,
                    'top_actions': [],
                    'statistics': {'simulations': 5000}
                }
            )
            
            result = solver.solve(game)
            
            # Should return partial result
            self.assertFalse(result.is_complete)
            self.assertEqual(result.expected_score, 3.5)
            self.assertEqual(result.num_simulations, 5000)
            self.assertEqual(result.error_info['type'], 'timeout')
    
    @patch('src.ofc_solver.psutil.virtual_memory')
    def test_memory_shortage_scenario(self, mock_vm):
        """Test Scenario: Memory shortage."""
        # Simulate low memory
        mock_vm.return_value = Mock(available=10 * 1024 * 1024)  # 10MB
        
        solver = OFCSolver(SolverConfig(
            memory_limit_mb=500,
            num_threads=4
        ))
        
        game = GameState(num_players=2, player_index=0)
        
        # First attempt should fail, then recover with single thread
        with patch.object(solver._resource_monitor, 'check_memory') as mock_check:
            call_count = 0
            def memory_check():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ResourceError(
                        "Memory limit exceeded",
                        resource_type="memory",
                        available=10,
                        required=500
                    )
                # Subsequent calls pass
            
            mock_check.side_effect = memory_check
            
            with patch('src.ofc_solver.MCTSEngine') as mock_mcts:
                # Mock successful search after recovery
                mock_engine = Mock()
                mock_mcts.return_value = mock_engine
                mock_result = Mock()
                mock_result.root_node = Mock(average_reward=5.0, visit_count=100)
                mock_result.root_node.get_action_statistics.return_value = []
                mock_result.best_action = Mock()
                mock_engine.search.return_value = mock_result
                mock_engine.get_statistics.return_value = {'simulations': 1000}
                
                # Should recover and complete
                result = solver.solve(game)
                
                # Should have reduced to single thread
                self.assertEqual(solver.mcts_config.num_threads, 1)
                # Should log warning (would need to check logs in real test)


class TestErrorRecoveryMechanisms(unittest.TestCase):
    """Test error recovery mechanisms."""
    
    def test_partial_result_on_timeout(self):
        """Test returning partial results on timeout."""
        solver = OFCSolver(SolverConfig(
            time_limit=1.0,
            return_partial_on_timeout=True
        ))
        
        game = GameState(num_players=2, player_index=0)
        
        with patch('src.ofc_solver.MCTSEngine') as mock_mcts:
            mock_engine = Mock()
            mock_mcts.return_value = mock_engine
            
            # Create partial result
            partial_result = {
                'best_action': Mock(placements=[]),
                'expected_score': 2.5,
                'simulations': 500,
                'top_actions': [],
                'statistics': {'simulations': 500}
            }
            
            mock_engine.search.side_effect = TimeoutError(
                "Timeout", 1.0, 1.5,
                partial_result=partial_result
            )
            
            result = solver.solve(game)
            
            self.assertFalse(result.is_complete)
            self.assertEqual(result.expected_score, 2.5)
            self.assertEqual(result.num_simulations, 500)
    
    def test_graceful_degradation_on_resource_error(self):
        """Test graceful degradation when resources are limited."""
        solver = OFCSolver(SolverConfig(num_threads=8))
        game = GameState(num_players=2, player_index=0)
        
        with patch.object(solver._resource_monitor, 'check_memory') as mock_check:
            # First call raises ResourceError
            mock_check.side_effect = [
                ResourceError("Low memory", "memory", available=50, required=200),
                None  # Second call succeeds
            ]
            
            with patch('src.ofc_solver.MCTSEngine') as mock_mcts:
                mock_engine = Mock()
                mock_mcts.return_value = mock_engine
                mock_result = Mock()
                mock_result.root_node = Mock(average_reward=3.0, visit_count=50)
                mock_result.root_node.get_action_statistics.return_value = []
                mock_result.best_action = Mock()
                mock_engine.search.return_value = mock_result
                mock_engine.get_statistics.return_value = {'simulations': 500}
                
                result = solver.solve(game)
                
                # Should complete with reduced threads
                self.assertEqual(solver.mcts_config.num_threads, 1)
                self.assertTrue(result.is_complete)
    
    def test_error_recovery_in_solve_game(self):
        """Test error recovery in solve_game()."""
        solver = OFCSolver(SolverConfig(time_limit=1.0))
        
        with patch.object(solver, 'solve') as mock_solve:
            # First solve times out with partial result
            timeout_error = TimeoutError(
                "Timeout", 1.0, 1.5,
                partial_result=SolveResult(
                    best_action=Mock(placements=[], discard=None),
                    expected_score=1.0,
                    num_simulations=100,
                    time_taken=1.5,
                    top_actions=[],
                    statistics={},
                    is_complete=False
                )
            )
            
            # Second solve succeeds
            success_result = SolveResult(
                best_action=Mock(placements=[], discard=None),
                expected_score=2.0,
                num_simulations=200,
                time_taken=0.8,
                top_actions=[],
                statistics={},
                is_complete=True
            )
            
            mock_solve.side_effect = [timeout_error, success_result]
            
            # Mock game state
            game = Mock(spec=GameState)
            game.is_complete = False
            game.current_street = Mock(name="INITIAL")
            game.current_hand = [Mock()]
            game.copy.return_value = game
            game.place_cards.return_value = None
            
            # Run solve_game
            results = solver.solve_game(game)
            
            # Should have recovered and continued
            self.assertEqual(len(results), 2)
            self.assertFalse(results[0].is_complete)  # Timeout result
            self.assertTrue(results[1].is_complete)   # Success result


if __name__ == '__main__':
    unittest.main()