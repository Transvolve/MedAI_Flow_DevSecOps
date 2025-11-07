"""Prometheus metrics for rate limiting and Redis monitoring."""
from prometheus_client import Counter, Histogram, Gauge
import time

# Rate limiting metrics
RATE_LIMIT_HITS = Counter(
    'rate_limit_hits_total',
    'Total number of rate limit hits',
    ['endpoint', 'client_ip']
)

RATE_LIMIT_EXCEEDED = Counter(
    'rate_limit_exceeded_total',
    'Total number of rate limit exceeded events',
    ['endpoint', 'client_ip']
)

RATE_LIMIT_REMAINING = Gauge(
    'rate_limit_remaining',
    'Remaining requests in current window',
    ['endpoint', 'client_ip']
)

# Redis connection metrics
REDIS_CONNECTED = Gauge(
    'redis_connected',
    'Indicates if Redis is connected'
)

REDIS_OPERATION_LATENCY = Histogram(
    'redis_operation_latency_seconds',
    'Latency of Redis operations',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0)
)

REDIS_POOL_SIZE = Gauge(
    'redis_pool_size',
    'Current size of the Redis connection pool'
)

REDIS_POOL_MAXSIZE = Gauge(
    'redis_pool_maxsize',
    'Maximum size of the Redis connection pool'
)

def track_rate_limit_hit(endpoint: str, client_ip: str, remaining: int):
    """Track a successful rate limit check."""
    RATE_LIMIT_HITS.labels(endpoint=endpoint, client_ip=client_ip).inc()
    RATE_LIMIT_REMAINING.labels(endpoint=endpoint, client_ip=client_ip).set(remaining)

def track_rate_limit_exceeded(endpoint: str, client_ip: str):
    """Track a rate limit exceeded event."""
    RATE_LIMIT_EXCEEDED.labels(endpoint=endpoint, client_ip=client_ip).inc()

def track_redis_operation(operation_name: str):
    """Decorator to track Redis operation latency."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                REDIS_OPERATION_LATENCY.labels(operation=operation_name).observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                # Track failed operations with -1 latency
                REDIS_OPERATION_LATENCY.labels(operation=operation_name).observe(-1)
                raise
        return wrapper
    return decorator

def update_redis_pool_metrics(pool_size: int, max_size: int):
    """Update Redis connection pool metrics."""
    REDIS_POOL_SIZE.set(pool_size)
    REDIS_POOL_MAXSIZE.set(max_size)

def set_redis_connected(connected: bool):
    """Update Redis connection status."""
    REDIS_CONNECTED.set(1 if connected else 0)