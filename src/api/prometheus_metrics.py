"""
Prometheus metrics for OFC Solver API monitoring.
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps
from typing import Callable, Any

# API Metrics
api_request_total = Counter(
    'ofc_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration_seconds = Histogram(
    'ofc_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

api_request_size_bytes = Summary(
    'ofc_api_request_size_bytes',
    'API request size in bytes',
    ['method', 'endpoint']
)

api_response_size_bytes = Summary(
    'ofc_api_response_size_bytes',
    'API response size in bytes',
    ['method', 'endpoint']
)

api_active_requests = Gauge(
    'ofc_api_active_requests',
    'Number of active API requests',
    ['method', 'endpoint']
)

# Solver Metrics
solver_solve_requests_total = Counter(
    'ofc_solver_solve_requests_total',
    'Total number of solve requests',
    ['status']
)

solver_solve_duration_seconds = Histogram(
    'ofc_solver_solve_duration_seconds',
    'Solver execution time in seconds',
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

solver_simulations_total = Counter(
    'ofc_solver_simulations_total',
    'Total number of MCTS simulations'
)

solver_simulation_rate = Gauge(
    'ofc_solver_simulation_rate',
    'Current simulation rate per second'
)

solver_expected_score = Histogram(
    'ofc_solver_expected_score',
    'Expected score from solver',
    buckets=(-50, -25, -10, 0, 10, 25, 50, 75, 100, 150)
)

solver_confidence = Histogram(
    'ofc_solver_confidence',
    'Solver confidence level',
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0)
)

# MCTS Metrics
mcts_nodes_evaluated_total = Counter(
    'ofc_mcts_nodes_evaluated_total',
    'Total number of MCTS nodes evaluated'
)

mcts_rollout_depth = Histogram(
    'ofc_mcts_rollout_depth',
    'MCTS rollout depth',
    buckets=(1, 2, 3, 5, 8, 10, 15, 20, 25, 30)
)

mcts_tree_size = Gauge(
    'ofc_mcts_tree_size',
    'Current MCTS tree size (number of nodes)'
)

mcts_thread_utilization = Gauge(
    'ofc_mcts_thread_utilization',
    'MCTS thread pool utilization',
    ['thread_id']
)

# System Metrics
system_cpu_usage_percent = Gauge(
    'ofc_system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage_bytes = Gauge(
    'ofc_system_memory_usage_bytes',
    'System memory usage in bytes',
    ['type']  # 'rss', 'vms', 'available'
)

system_thread_count = Gauge(
    'ofc_system_thread_count',
    'Number of active threads'
)

# Error Metrics
error_count_total = Counter(
    'ofc_error_count_total',
    'Total number of errors',
    ['error_type', 'component']
)

# Rate Limit Metrics
rate_limit_exceeded_total = Counter(
    'ofc_rate_limit_exceeded_total',
    'Total number of rate limit exceeded responses',
    ['api_key_owner']
)

# Queue Metrics
async_queue_size = Gauge(
    'ofc_async_queue_size',
    'Current size of async task queue'
)

async_task_duration_seconds = Histogram(
    'ofc_async_task_duration_seconds',
    'Async task execution duration',
    ['task_type'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
)


# Decorator for timing functions
def measure_time(metric: Histogram, labels: dict = None):
    """Decorator to measure function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        return wrapper
    return decorator


# Context manager for tracking active requests
class track_active_requests:
    """Context manager to track active requests."""
    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        self.labels = {'method': method, 'endpoint': endpoint}
    
    def __enter__(self):
        api_active_requests.labels(**self.labels).inc()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        api_active_requests.labels(**self.labels).dec()


# Helper function to record API metrics
def record_api_metrics(method: str, endpoint: str, status_code: int, 
                      duration: float, request_size: int = 0, response_size: int = 0):
    """Record API request metrics."""
    api_request_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    if request_size > 0:
        api_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)
    
    if response_size > 0:
        api_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)


# Helper function to record solver metrics
def record_solver_metrics(status: str, duration: float, simulations: int, 
                         expected_score: float, confidence: float):
    """Record solver execution metrics."""
    solver_solve_requests_total.labels(status=status).inc()
    solver_solve_duration_seconds.observe(duration)
    solver_simulations_total.inc(simulations)
    solver_expected_score.observe(expected_score)
    solver_confidence.observe(confidence)
    
    # Calculate simulation rate
    if duration > 0:
        rate = simulations / duration
        solver_simulation_rate.set(rate)


# Helper function to record MCTS metrics
def record_mcts_metrics(nodes_evaluated: int, tree_size: int):
    """Record MCTS algorithm metrics."""
    mcts_nodes_evaluated_total.inc(nodes_evaluated)
    mcts_tree_size.set(tree_size)


# Helper function to record error
def record_error(error_type: str, component: str):
    """Record error occurrence."""
    error_count_total.labels(error_type=error_type, component=component).inc()