"""
Custom exceptions for OFC Solver.

This module defines all custom exceptions used throughout the OFC Solver system.
Each exception provides clear error messages and relevant context for debugging.
"""

from typing import Optional, Any, Dict


class OFCError(Exception):
    """
    Base exception class for all OFC Solver errors.
    
    Attributes:
        message: Human-readable error message
        details: Additional error details for debugging
        error_code: Unique error code for categorization
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
    
    def __str__(self):
        if self.details:
            detail_str = ', '.join(f'{k}={v}' for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class InvalidInputError(OFCError):
    """
    Raised when invalid input is provided to the solver.
    
    This includes:
    - Invalid card representations
    - Duplicate cards
    - Invalid game states
    - Malformed requests
    """
    
    def __init__(self, message: str, input_value: Any = None, **kwargs):
        details = {'input_value': str(input_value)} if input_value is not None else {}
        details.update(kwargs)
        super().__init__(message, details, 'INVALID_INPUT')


class TimeoutError(OFCError):
    """
    Raised when solver operations exceed time limits.
    
    Includes partial results when available.
    """
    
    def __init__(self, message: str, time_limit: float, elapsed_time: float,
                 partial_result: Optional[Any] = None, **kwargs):
        details = {
            'time_limit': time_limit,
            'elapsed_time': elapsed_time,
            'has_partial_result': partial_result is not None
        }
        details.update(kwargs)
        super().__init__(message, details, 'TIMEOUT')
        self.partial_result = partial_result


class ResourceError(OFCError):
    """
    Raised when system resources are insufficient.
    
    This includes:
    - Memory allocation failures
    - Thread pool exhaustion
    - File system issues
    """
    
    def __init__(self, message: str, resource_type: str, 
                 available: Optional[float] = None, required: Optional[float] = None,
                 **kwargs):
        details = {
            'resource_type': resource_type,
            'available': available,
            'required': required
        }
        details.update(kwargs)
        super().__init__(message, details, 'RESOURCE_ERROR')


class GameRuleViolationError(OFCError):
    """
    Raised when game rules are violated.
    
    This includes:
    - Invalid card placements
    - Attempting illegal moves
    - Violating OFC hand ranking rules
    """
    
    def __init__(self, message: str, rule_violated: str, 
                 game_state: Optional[Any] = None, **kwargs):
        details = {
            'rule_violated': rule_violated,
            'has_game_state': game_state is not None
        }
        details.update(kwargs)
        super().__init__(message, details, 'RULE_VIOLATION')
        self.game_state = game_state


class SolverError(OFCError):
    """
    General solver error for unexpected conditions.
    
    This is used for errors that don't fit other categories.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        details = {'operation': operation} if operation else {}
        details.update(kwargs)
        super().__init__(message, details, 'SOLVER_ERROR')


class ConfigurationError(OFCError):
    """
    Raised when solver configuration is invalid.
    
    This includes:
    - Invalid parameter values
    - Conflicting settings
    - Missing required configuration
    """
    
    def __init__(self, message: str, parameter: Optional[str] = None,
                 value: Any = None, **kwargs):
        details = {}
        if parameter:
            details['parameter'] = parameter
        if value is not None:
            details['value'] = str(value)
        details.update(kwargs)
        super().__init__(message, details, 'CONFIG_ERROR')


class StateError(OFCError):
    """
    Raised when operations are attempted in invalid states.
    
    This includes:
    - Attempting to deal cards when hand is full
    - Placing cards after game completion
    - Invalid state transitions
    """
    
    def __init__(self, message: str, current_state: str, 
                 expected_state: Optional[str] = None, **kwargs):
        details = {
            'current_state': current_state,
            'expected_state': expected_state
        }
        details.update(kwargs)
        super().__init__(message, details, 'STATE_ERROR')


# Convenience functions for common error scenarios

def invalid_card_error(card_str: str) -> InvalidInputError:
    """Create error for invalid card string."""
    return InvalidInputError(
        f"Invalid card representation: '{card_str}'",
        input_value=card_str,
        expected_format="[Rank][Suit] e.g., 'AS', 'KH', '2C'"
    )


def duplicate_card_error(card: Any) -> InvalidInputError:
    """Create error for duplicate card."""
    return InvalidInputError(
        f"Duplicate card detected: {card}",
        input_value=card,
        error_type="duplicate"
    )


def timeout_error(operation: str, time_limit: float, elapsed: float,
                  partial_result: Optional[Any] = None) -> TimeoutError:
    """Create error for operation timeout."""
    return TimeoutError(
        f"Operation '{operation}' exceeded time limit of {time_limit:.1f}s",
        time_limit=time_limit,
        elapsed_time=elapsed,
        partial_result=partial_result,
        operation=operation
    )


def memory_error(required_mb: float, available_mb: float) -> ResourceError:
    """Create error for insufficient memory."""
    return ResourceError(
        f"Insufficient memory: required {required_mb:.1f}MB, available {available_mb:.1f}MB",
        resource_type="memory",
        required=required_mb,
        available=available_mb
    )


def invalid_placement_error(card: Any, position: str, reason: str) -> GameRuleViolationError:
    """Create error for invalid card placement."""
    return GameRuleViolationError(
        f"Cannot place {card} at {position}: {reason}",
        rule_violated="card_placement",
        card=str(card),
        position=position,
        reason=reason
    )