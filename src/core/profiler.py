"""
코드 프로파일링을 위한 모듈
"""

import logging
import time
import cProfile
import pstats
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

class Profiler:
    """코드 프로파일러"""
    
    def __init__(self):
        self._profiler = cProfile.Profile()
        self._stats: Optional[pstats.Stats] = None
        self._start_time: Optional[float] = None
        
    def start(self):
        """프로파일링 시작"""
        self._start_time = time.time()
        self._profiler.enable()
        
    def stop(self) -> Dict[str, Any]:
        """프로파일링 종료 및 결과 반환"""
        self._profiler.disable()
        if self._start_time is None:
            return {}
            
        execution_time = time.time() - self._start_time
        self._stats = pstats.Stats(self._profiler)
        
        # 상위 10개 함수 추출
        stats_dict = {}
        for func, (cc, nc, tt, ct, callers) in self._stats.stats.items():
            stats_dict[func] = {
                'calls': cc,
                'time': tt,
                'cumtime': ct
            }
            
        sorted_funcs = sorted(stats_dict.items(), key=lambda x: x[1]['cumtime'], reverse=True)[:10]
        
        return {
            'execution_time': execution_time,
            'top_functions': [{
                'name': f"{func[2]}:{func[1]} ({func[0]})",
                'stats': stats
            } for func, stats in sorted_funcs]
        }
        
    def profile(self, func: Callable) -> Callable:
        """함수 프로파일링 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.start()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                stats = self.stop()
                logger.debug(f"Profile results for {func.__name__}: {stats}")
        return wrapper

# 글로벌 프로파일러 인스턴스
profiler = Profiler() 