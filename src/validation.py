"""
Input validation utilities and decorators for OFC Solver.

Provides decorators and functions for validating inputs to ensure
data integrity and provide clear error messages.
"""

import functools
import time
from typing import Callable, Any, Optional, List, Union, TypeVar, cast
import logging

from src.exceptions import (
    InvalidInputError, TimeoutError, ResourceError, 
    GameRuleViolationError, ConfigurationError, StateError
)
from src.core.domain import Card, GameState, PlayerArrangement

logger = logging.getLogger(__name__)

T = TypeVar('T')


def validate_input(validation_func: Optional[Callable] = None,
                   error_message: str = "Invalid input",
                   log_errors: bool = True):
    """
    Decorator for input validation.
    
    Args:
        validation_func: Optional function to validate input
        error_message: Error message to use on validation failure
        log_errors: Whether to log validation errors
    
    Example:
        @validate_input(lambda x: x > 0, "Value must be positive")
        def process_value(value: int):
            return value * 2
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Run custom validation if provided
                if validation_func:
                    # Apply validation to first argument (after self if method)
                    arg_to_validate = args[1] if args and hasattr(args[0], '__class__') else args[0] if args else None
                    if arg_to_validate is not None and not validation_func(arg_to_validate):
                        raise InvalidInputError(error_message, input_value=arg_to_validate)
                
                return func(*args, **kwargs)
            
            except InvalidInputError:
                raise
            except Exception as e:
                if log_errors:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


def validate_card(card_input: Union[str, Card]) -> Card:
    """
    Validate and convert card input.
    
    Args:
        card_input: String representation or Card object
        
    Returns:
        Valid Card object
        
    Raises:
        InvalidInputError: If card is invalid
    """
    if isinstance(card_input, Card):
        return card_input
    
    if not isinstance(card_input, str):
        raise InvalidInputError(
            "Card must be a string or Card object",
            input_value=card_input,
            expected_types=["str", "Card"]
        )
    
    try:
        return Card.from_string(card_input)
    except ValueError as e:
        raise InvalidInputError(
            f"Invalid card string: {card_input}",
            input_value=card_input,
            error=str(e)
        )


def validate_card_list(cards: List[Union[str, Card]]) -> List[Card]:
    """
    Validate a list of cards.
    
    Args:
        cards: List of card representations
        
    Returns:
        List of valid Card objects
        
    Raises:
        InvalidInputError: If any card is invalid or duplicates exist
    """
    if not isinstance(cards, list):
        raise InvalidInputError(
            "Cards must be a list",
            input_value=type(cards).__name__,
            expected_type="list"
        )
    
    validated_cards = []
    seen_cards = set()
    
    for i, card in enumerate(cards):
        try:
            validated_card = validate_card(card)
            
            # Check for duplicates
            card_str = str(validated_card)
            if card_str in seen_cards:
                raise InvalidInputError(
                    f"Duplicate card: {card_str}",
                    input_value=cards,
                    duplicate_index=i,
                    duplicate_card=card_str
                )
            
            seen_cards.add(card_str)
            validated_cards.append(validated_card)
            
        except InvalidInputError as e:
            e.details['card_index'] = i
            raise
    
    return validated_cards


def validate_game_state(func: Callable) -> Callable:
    """
    Decorator to validate GameState arguments.
    
    Ensures GameState is valid before processing.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Find GameState in arguments
        game_state = None
        for arg in args:
            if isinstance(arg, GameState):
                game_state = arg
                break
        
        if not game_state:
            for value in kwargs.values():
                if isinstance(value, GameState):
                    game_state = value
                    break
        
        if game_state:
            # Validate game state
            if game_state.is_complete:
                raise StateError(
                    "Cannot perform operation on completed game",
                    current_state="completed",
                    expected_state="in_progress"
                )
            
            # Check for basic validity
            if game_state.player_index < 0 or game_state.player_index >= game_state.num_players:
                raise InvalidInputError(
                    "Invalid player index",
                    input_value=game_state.player_index,
                    valid_range=f"0-{game_state.num_players-1}"
                )
        
        return func(*args, **kwargs)
    
    return wrapper


def with_timeout(timeout_seconds: float, 
                 return_partial: bool = True,
                 operation_name: Optional[str] = None):
    """
    Decorator to enforce timeout on function execution.
    
    Args:
        timeout_seconds: Maximum execution time
        return_partial: Whether to return partial results on timeout
        operation_name: Name of operation for error messages
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = operation_name or func.__name__
            
            # For simplicity, we'll use a time check approach
            # In production, you might use threading.Timer or signal
            
            try:
                # Add timeout info to kwargs if the function accepts it
                if 'timeout_info' in func.__code__.co_varnames:
                    kwargs['timeout_info'] = {
                        'start_time': start_time,
                        'timeout': timeout_seconds
                    }
                
                result = func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    partial_result = result if return_partial else None
                    raise TimeoutError(
                        f"Operation '{operation}' exceeded timeout",
                        time_limit=timeout_seconds,
                        elapsed_time=elapsed,
                        partial_result=partial_result
                    )
                
                return result
                
            except TimeoutError:
                raise
            except Exception as e:
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    raise TimeoutError(
                        f"Operation '{operation}' exceeded timeout during error handling",
                        time_limit=timeout_seconds,
                        elapsed_time=elapsed,
                        partial_result=None,
                        original_error=str(e)
                    )
                raise
        
        return wrapper
    return decorator


def validate_config(config_class: type) -> Callable:
    """
    Decorator to validate configuration objects.
    
    Args:
        config_class: Expected configuration class
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Find config in arguments
            config = None
            config_index = None
            
            for i, arg in enumerate(args):
                if isinstance(arg, config_class):
                    config = arg
                    config_index = i
                    break
            
            if config:
                # Validate specific config parameters
                if hasattr(config, 'time_limit') and config.time_limit <= 0:
                    raise ConfigurationError(
                        "Time limit must be positive",
                        parameter='time_limit',
                        value=config.time_limit
                    )
                
                if hasattr(config, 'num_threads') and config.num_threads < 1:
                    raise ConfigurationError(
                        "Number of threads must be at least 1",
                        parameter='num_threads',
                        value=config.num_threads
                    )
                
                if hasattr(config, 'c_puct') and config.c_puct <= 0:
                    raise ConfigurationError(
                        "Exploration constant (c_puct) must be positive",
                        parameter='c_puct',
                        value=config.c_puct
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_placement(position: str, index: int, arrangement: PlayerArrangement) -> None:
    """
    Validate a card placement.
    
    Args:
        position: 'front', 'middle', or 'back'
        index: Position within the row
        arrangement: Current player arrangement
        
    Raises:
        GameRuleViolationError: If placement is invalid
    """
    valid_positions = ['front', 'middle', 'back']
    if position not in valid_positions:
        raise GameRuleViolationError(
            f"Invalid position: {position}",
            rule_violated="position_name",
            valid_positions=valid_positions,
            provided=position
        )
    
    # Check index bounds
    max_cards = {'front': 3, 'middle': 5, 'back': 5}
    if index < 0 or index >= max_cards[position]:
        raise GameRuleViolationError(
            f"Invalid index {index} for {position} (max: {max_cards[position]-1})",
            rule_violated="position_index",
            position=position,
            index=index,
            valid_range=f"0-{max_cards[position]-1}"
        )
    
    # Check if position is already occupied
    row = getattr(arrangement, position)
    if row[index] is not None:
        raise GameRuleViolationError(
            f"Position {position}[{index}] is already occupied by {row[index]}",
            rule_violated="position_occupied",
            position=position,
            index=index,
            existing_card=str(row[index])
        )


def validate_action_arguments(func: Callable) -> Callable:
    """
    Decorator to validate common action arguments.
    
    Validates cards, positions, and game state for action methods.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # This decorator is specifically for methods that take actions
        # Typically: place_cards(placements, discard)
        
        if len(args) > 0 and isinstance(args[0], list):
            # Validate placements
            placements = args[0]
            for i, placement in enumerate(placements):
                if not isinstance(placement, tuple) or len(placement) != 3:
                    raise InvalidInputError(
                        f"Invalid placement format at index {i}",
                        input_value=placement,
                        expected_format="(card, position, index)"
                    )
                
                card, position, index = placement
                
                # Validate card
                try:
                    validate_card(card)
                except InvalidInputError as e:
                    e.details['placement_index'] = i
                    raise
        
        return func(self, *args, **kwargs)
    
    return wrapper


# Error recovery utilities

def with_error_recovery(default_return: Any = None,
                       recoverable_errors: tuple = (ResourceError, TimeoutError),
                       log_recovery: bool = True):
    """
    Decorator to provide error recovery mechanism.
    
    Args:
        default_return: Value to return on recoverable error
        recoverable_errors: Tuple of exception types to recover from
        log_recovery: Whether to log recovery actions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except recoverable_errors as e:
                if log_recovery:
                    logger.warning(f"Recovering from {type(e).__name__} in {func.__name__}: {e}")
                
                # For TimeoutError, try to return partial result
                if isinstance(e, TimeoutError) and hasattr(e, 'partial_result') and e.partial_result:
                    return e.partial_result
                
                return default_return
            
        return wrapper
    return decorator


def ensure_resources(memory_mb: Optional[float] = None,
                    threads: Optional[int] = None):
    """
    Decorator to ensure sufficient resources before execution.
    
    Args:
        memory_mb: Required memory in MB
        threads: Required number of threads
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import psutil
            import threading
            
            # Check memory if specified
            if memory_mb:
                available_mb = psutil.virtual_memory().available / (1024 * 1024)
                if available_mb < memory_mb:
                    raise ResourceError(
                        f"Insufficient memory for {func.__name__}",
                        resource_type="memory",
                        required=memory_mb,
                        available=available_mb
                    )
            
            # Check thread availability if specified
            if threads:
                active_threads = threading.active_count()
                max_threads = 100  # Reasonable limit
                if active_threads + threads > max_threads:
                    raise ResourceError(
                        f"Insufficient threads for {func.__name__}",
                        resource_type="threads",
                        required=threads,
                        available=max_threads - active_threads
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator