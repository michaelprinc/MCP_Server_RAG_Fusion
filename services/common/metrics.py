"""
Prometheus metrics instrumentation for microservices.

Provides common metrics for all services:
- Request count
- Request duration
- Error count
- Active requests
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
from typing import Callable

# Common metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

error_count = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['method', 'endpoint', 'error_type']
)


def track_metrics(endpoint: str):
    """
    Decorator to track metrics for an endpoint.
    
    Usage:
        @app.get("/my-endpoint")
        @track_metrics("/my-endpoint")
        async def my_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = "GET"  # Default, can be extracted from request
            
            # Track active requests
            active_requests.labels(method=method, endpoint=endpoint).inc()
            
            # Track duration
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Track success
                duration = time.time() - start_time
                request_duration.labels(method=method, endpoint=endpoint).observe(duration)
                request_count.labels(method=method, endpoint=endpoint, status="200").inc()
                
                return result
                
            except Exception as e:
                # Track error
                duration = time.time() - start_time
                request_duration.labels(method=method, endpoint=endpoint).observe(duration)
                error_count.labels(method=method, endpoint=endpoint, error_type=type(e).__name__).inc()
                request_count.labels(method=method, endpoint=endpoint, status="500").inc()
                raise
                
            finally:
                # Decrease active requests
                active_requests.labels(method=method, endpoint=endpoint).dec()
        
        return wrapper
    return decorator


def get_metrics() -> bytes:
    """Get Prometheus metrics in text format."""
    return generate_latest()


def get_metrics_content_type() -> str:
    """Get content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
