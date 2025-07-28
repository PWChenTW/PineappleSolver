# OFC Solver Test Suite

## Overview

This directory contains the comprehensive test suite for the OFC Solver, achieving over 80% code coverage through unit tests, integration tests, performance benchmarks, and edge case testing.

## Test Structure

### Core Domain Tests
- `test_card.py` - Tests for Card, Rank, and Suit classes
- `test_card_set.py` - Tests for efficient CardSet operations
- `test_hand.py` - Tests for hand evaluation logic
- `test_game_state.py` - Tests for game state management

### Algorithm Tests
- `test_mcts.py` - Tests for Monte Carlo Tree Search implementation
- `test_basic_engine.py` - Tests for basic game engine
- `test_solver.py` - Tests for main solver interface

### Solver Implementation Tests
- `test_simple_solver.py` - Tests for simple solver strategy
- `test_quick_solver.py` - Tests for quick solver heuristics

### Quality Assurance Tests
- `test_error_handling.py` - Tests for exception handling
- `test_edge_cases.py` - Tests for boundary conditions and unusual scenarios
- `test_performance.py` - Performance benchmarks and profiling

### Bug Fix Tests
- `test_todo_fixes.py` - Tests for specific bug fixes

## Running Tests

### Run All Tests with Coverage
```bash
python run_tests_coverage.py
```

### Run Specific Test Module
```bash
pytest tests/test_card.py -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
```

### Run Performance Tests
```bash
pytest tests/test_performance.py -v -s
```

### Run Edge Case Tests
```bash
pytest tests/test_edge_cases.py -v
```

## Coverage Goals

- **Target**: 80% overall coverage
- **Core Modules**: 90%+ coverage for critical components
- **Algorithms**: 85%+ coverage for MCTS and evaluation
- **Error Paths**: 100% coverage for exception handling

## Test Categories

### 1. Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution (< 0.1s per test)
- Examples: Card creation, hand evaluation

### 2. Integration Tests
- Test component interactions
- Use real implementations
- Moderate execution time (< 1s per test)
- Examples: Complete game simulation, MCTS search

### 3. Performance Tests
- Benchmark critical operations
- Profile for bottlenecks
- Ensure performance requirements
- Examples: Hand evaluation speed, MCTS simulation rate

### 4. Edge Case Tests
- Test boundary conditions
- Unusual input scenarios
- Error recovery
- Examples: Empty sets, invalid states

## Key Test Patterns

### Fixture Usage
```python
@pytest.fixture
def sample_game_state():
    gs = GameState(seed=42)
    gs.deal_street()
    return gs
```

### Parametrized Tests
```python
@pytest.mark.parametrize("hand_str,expected_type", [
    (["As", "Ks", "Qs", "Js", "Ts"], HandCategory.ROYAL_FLUSH),
    (["9s", "8s", "7s", "6s", "5s"], HandCategory.STRAIGHT_FLUSH),
])
def test_hand_types(hand_str, expected_type):
    hand = Hand.from_strings(hand_str)
    assert hand.hand_type.category == expected_type
```

### Performance Assertions
```python
with time_limit(0.1):  # 100ms limit
    for _ in range(1000):
        hand.evaluate()
```

### Mock Usage
```python
@patch('src.external_api.fetch_data')
def test_with_mock(mock_fetch):
    mock_fetch.return_value = {"status": "ok"}
    result = function_under_test()
    assert result.success
```

## Continuous Improvement

### Adding New Tests
1. Identify uncovered code using coverage report
2. Write focused test for specific functionality
3. Include both positive and negative test cases
4. Add performance test if applicable

### Test Maintenance
1. Keep tests independent and isolated
2. Use meaningful test names
3. Document complex test scenarios
4. Regular cleanup of obsolete tests

### Performance Monitoring
1. Run benchmarks regularly
2. Track performance regressions
3. Profile hot paths
4. Optimize based on data

## Test Utilities

### Coverage Report Script
- `run_tests_coverage.py` - Automated test runner with coverage analysis

### Helper Functions
- Time limit context manager
- Profile code context manager
- Test data factories
- Assertion helpers

## Best Practices

1. **Fast Tests First**: Run unit tests before integration tests
2. **Descriptive Names**: Test names should explain what they test
3. **Single Responsibility**: Each test should verify one thing
4. **No Test Dependencies**: Tests should not depend on each other
5. **Clean Test Data**: Use fresh data for each test
6. **Meaningful Assertions**: Assert on behavior, not implementation
7. **Error Messages**: Include context in assertion messages
8. **Test Documentation**: Document complex test scenarios

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes project root
2. **Slow Tests**: Use pytest markers to skip slow tests
3. **Flaky Tests**: Fix or mark as flaky for investigation
4. **Coverage Gaps**: Check branch coverage, not just line coverage

### Debug Commands

```bash
# Run single test with debugging
pytest tests/test_card.py::TestCard::test_card_creation -vv -s

# Run with pdb on failure
pytest tests/test_mcts.py --pdb

# Generate detailed coverage report
coverage run -m pytest tests/
coverage report -m
coverage html
```