"""
메트릭 수집 및 모니터링을 위한 모듈
"""

import logging
import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# 메트릭 정의
REQUEST_COUNT = Counter('palantir_request_total', 'Total number of requests', ['endpoint'])
REQUEST_LATENCY = Histogram('palantir_request_latency_seconds', 'Request latency in seconds', ['endpoint'])
ACTIVE_USERS = Gauge('palantir_active_users', 'Number of active users')
ERROR_COUNT = Counter('palantir_error_total', 'Total number of errors', ['type'])

class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self):
        self._start_time: Optional[float] = None
        
    def start_request(self, endpoint: str):
        """요청 시작 시간 기록"""
        self._start_time = time.time()
        REQUEST_COUNT.labels(endpoint=endpoint).inc()
        
    def end_request(self, endpoint: str):
        """요청 종료 및 지연 시간 기록"""
        if self._start_time is not None:
            latency = time.time() - self._start_time
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency)
            self._start_time = None
            
    def record_error(self, error_type: str):
        """에러 발생 기록"""
        ERROR_COUNT.labels(type=error_type).inc()
        
    def update_active_users(self, count: int):
        """활성 사용자 수 업데이트"""
        ACTIVE_USERS.set(count)
        
    def get_metrics(self) -> Dict[str, Any]:
        """현재 메트릭 상태 반환"""
        return {
            'request_count': REQUEST_COUNT._value.sum(),
            'error_count': ERROR_COUNT._value.sum(),
            'active_users': ACTIVE_USERS._value
        }

# 글로벌 메트릭 수집기 인스턴스
metrics = MetricsCollector() 