"""성능 모니터링 모듈."""

import os
import psutil
import logging
import time
from typing import Dict, Any
from datetime import datetime
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_client.exposition import start_http_server

logger = logging.getLogger(__name__)

# 시스템 메트릭
SYSTEM_METRICS = {
    "cpu_usage": Gauge("system_cpu_usage", "CPU usage percentage"),
    "memory_usage": Gauge("system_memory_usage", "Memory usage in bytes"),
    "disk_usage": Gauge("system_disk_usage", "Disk usage in bytes"),
    "network_io": Gauge("system_network_io", "Network I/O in bytes")
}

# 비즈니스 메트릭
BUSINESS_METRICS = {
    "active_users": Gauge("active_users", "Number of active users"),
    "pipeline_executions": Counter("pipeline_executions_total", "Total pipeline executions"),
    "llm_requests": Counter("llm_requests_total", "Total LLM requests"),
    "api_requests": Counter(
        "api_requests_total",
        "Total API requests",
        ["endpoint", "method", "status"]
    ),
    "request_duration": Histogram(
        "request_duration_seconds",
        "Request duration in seconds",
        ["endpoint"]
    )
}

# 메트릭 정의
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

DB_OPERATION_LATENCY = Histogram(
    'db_operation_duration_seconds',
    'Database operation latency',
    ['operation']
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

ACTIVE_CONNECTIONS = Gauge(
    'db_active_connections',
    'Number of active database connections'
)

# 사용자 관련 메트릭 추가
user_signup_total = Counter(
    'user_signup_total',
    '신규 가입자 수'
)
user_active_total = Gauge(
    'user_active_total',
    '활성 사용자 수'
)
user_auth_success_total = Counter(
    'user_auth_success_total',
    '인증 성공 횟수'
)
user_auth_fail_total = Counter(
    'user_auth_fail_total',
    '인증 실패 횟수'
)

def update_system_metrics():
    try:
        SYSTEM_METRICS["cpu_usage"].set(psutil.cpu_percent())
        SYSTEM_METRICS["memory_usage"].set(psutil.virtual_memory().used)
        SYSTEM_METRICS["disk_usage"].set(psutil.disk_usage('/').used)
        net_io = psutil.net_io_counters()
        SYSTEM_METRICS["network_io"].set(net_io.bytes_sent + net_io.bytes_recv)
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")

def setup_monitoring(app):
    # 기본 메트릭 설정
    Instrumentator().instrument(app).expose(app)

    # 커스텀 메트릭 추가
    @app.on_event("startup")
    async def startup_event():
        # 시스템 메트릭 업데이트 시작
        update_system_metrics()

    # API 요청 메트릭
    @app.middleware("http")
    async def track_requests(request, call_next):
        start_time = datetime.now()
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        
        BUSINESS_METRICS["api_requests"].labels(
            endpoint=request.url.path,
            method=request.method,
            status=response.status_code
        ).inc()
        
        BUSINESS_METRICS["request_duration"].labels(
            endpoint=request.url.path
        ).observe(duration)
        
        return response

def get_metrics() -> Dict[str, Any]:
    """현재 시스템 상태를 반환"""
    return {
        "system": {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage('/')._asdict(),
            "network": psutil.net_io_counters()._asdict()
        },
        "timestamp": datetime.now().isoformat()
    }

def monitor_request(method: str, endpoint: str):
    """HTTP 요청 모니터링 데코레이터."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status = response.status_code
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
                return response
            except Exception as e:
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=500).inc()
                raise e
            finally:
                duration = time.time() - start_time
                REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
        return wrapper
    return decorator

def monitor_db_operation(operation: str):
    """데이터베이스 작업 모니터링 데코레이터."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                DB_OPERATION_LATENCY.labels(operation=operation).observe(duration)
        return wrapper
    return decorator

def monitor_cache(cache_type: str):
    """캐시 작업 모니터링 데코레이터."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result is not None:
                    CACHE_HITS.labels(cache_type=cache_type).inc()
                else:
                    CACHE_MISSES.labels(cache_type=cache_type).inc()
                return result
            except Exception as e:
                CACHE_MISSES.labels(cache_type=cache_type).inc()
                raise e
        return wrapper
    return decorator

def update_connection_metrics():
    """데이터베이스 연결 메트릭을 업데이트합니다."""
    from .database import get_db_stats
    stats = get_db_stats()
    ACTIVE_CONNECTIONS.set(stats['checkedout_connections'])

def start_monitoring_server(port: int = 8000):
    """모니터링 서버를 시작합니다."""
    start_http_server(port)
    logger.info(f"Prometheus metrics server started on port {port}")

def update_user_metrics(active_user_count: int):
    """활성 사용자 수를 갱신합니다."""
    user_active_total.set(active_user_count)

class PerformanceMonitor:
    """성능 모니터링 클래스."""
    
    def __init__(self):
        self.start_time = time.time()
        self.operation_times = {}
    
    def start_operation(self, operation_name: str):
        """작업 시작 시간을 기록합니다."""
        self.operation_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str) -> float:
        """작업 종료 시간을 기록하고 소요 시간을 반환합니다."""
        if operation_name in self.operation_times:
            duration = time.time() - self.operation_times[operation_name]
            del self.operation_times[operation_name]
            return duration
        return 0.0
    
    def get_operation_stats(self) -> dict:
        """작업 통계를 반환합니다."""
        return {
            "total_runtime": time.time() - self.start_time,
            "active_operations": len(self.operation_times)
        } 