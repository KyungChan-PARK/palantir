"""캐시 시스템 모듈."""

import hashlib
import json
import logging
import os
from functools import wraps
from typing import Any, Dict, List, Optional

import redis
from redis.exceptions import RedisError

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CacheError(Exception):
    """캐시 관련 예외 클래스."""
    pass

class Cache:
    """Redis 기반 캐시 클래스."""

    def __init__(
        self,
        ttl: int = 300,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None,
        max_retries: int = 3
    ):
        """캐시 인스턴스를 초기화합니다.
        
        Args:
            ttl: 기본 캐시 유효 시간 (초)
            host: Redis 호스트
            port: Redis 포트
            db: Redis 데이터베이스 번호
            password: Redis 비밀번호
            max_retries: 최대 재시도 횟수
        """
        self.ttl = ttl
        self.max_retries = max_retries
        
        # Redis 연결 설정
        self.redis = redis.Redis(
            host=host or os.getenv("REDIS_HOST", "localhost"),
            port=int(port or os.getenv("REDIS_PORT", 6379)),
            db=int(db or os.getenv("REDIS_DB", 0)),
            password=password or os.getenv("REDIS_PASSWORD"),
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        
        # 연결 테스트
        try:
            self.redis.ping()
            logger.info("Redis 연결 성공")
        except RedisError as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise CacheError(f"Redis 연결 실패: {e}")

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키를 생성합니다.
        
        Args:
            prefix: 키 접두사
            *args: 위치 인자
            **kwargs: 키워드 인자
            
        Returns:
            생성된 캐시 키
        """
        key_parts = [prefix]
        
        # 위치 인자 추가
        if args:
            key_parts.extend([str(arg) for arg in args])
        
        # 키워드 인자 추가 (정렬된 순서로)
        if kwargs:
            sorted_items = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_items])
        
        # 키 생성
        key_string = ":".join(key_parts)
        return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값을 가져옵니다.
        
        Args:
            key: 캐시 키
            
        Returns:
            캐시된 값 또는 None
        """
        for attempt in range(self.max_retries):
            try:
                value = self.redis.get(key)
                if value is None:
                    return None
                return json.loads(value)
            except (RedisError, json.JSONDecodeError) as e:
                logger.error(f"캐시 조회 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise CacheError(f"캐시 조회 실패: {e}")

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """캐시에 값을 저장합니다.
        
        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: 유효 시간 (초)
            nx: 키가 없을 때만 저장
            xx: 키가 있을 때만 저장
            
        Returns:
            저장 성공 여부
        """
        for attempt in range(self.max_retries):
            try:
                return self.redis.setex(
                    key,
                    ttl or self.ttl,
                    json.dumps(value),
                    nx=nx,
                    xx=xx
                )
            except (RedisError, TypeError) as e:
                logger.error(f"캐시 저장 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise CacheError(f"캐시 저장 실패: {e}")

    async def delete(self, key: str) -> bool:
        """캐시에서 값을 삭제합니다.
        
        Args:
            key: 캐시 키
            
        Returns:
            삭제 성공 여부
        """
        for attempt in range(self.max_retries):
            try:
                return bool(self.redis.delete(key))
            except RedisError as e:
                logger.error(f"캐시 삭제 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise CacheError(f"캐시 삭제 실패: {e}")

    async def clear(self) -> None:
        """모든 캐시를 삭제합니다."""
        for attempt in range(self.max_retries):
            try:
                self.redis.flushdb()
                logger.info("캐시 초기화 완료")
                return
            except RedisError as e:
                logger.error(f"캐시 초기화 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise CacheError(f"캐시 초기화 실패: {e}")

    async def exists(self, key: str) -> bool:
        """키의 존재 여부를 확인합니다.
        
        Args:
            key: 캐시 키
            
        Returns:
            키 존재 여부
        """
        for attempt in range(self.max_retries):
            try:
                return bool(self.redis.exists(key))
            except RedisError as e:
                logger.error(f"키 존재 확인 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise CacheError(f"키 존재 확인 실패: {e}")

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """여러 키의 값을 한 번에 가져옵니다.
        
        Args:
            keys: 캐시 키 목록
            
        Returns:
            키-값 쌍의 딕셔너리
        """
        for attempt in range(self.max_retries):
            try:
                values = self.redis.mget(keys)
                result = {}
                for key, value in zip(keys, values):
                    if value is not None:
                        try:
                            result[key] = json.loads(value)
                        except json.JSONDecodeError:
                            result[key] = value
                return result
            except RedisError as e:
                logger.error(f"다중 캐시 조회 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise CacheError(f"다중 캐시 조회 실패: {e}")

    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """여러 키-값 쌍을 한 번에 저장합니다.
        
        Args:
            mapping: 키-값 쌍의 딕셔너리
            ttl: 유효 시간 (초)
        """
        for attempt in range(self.max_retries):
            try:
                pipeline = self.redis.pipeline()
                for key, value in mapping.items():
                    pipeline.setex(
                        key,
                        ttl or self.ttl,
                        json.dumps(value)
                    )
                pipeline.execute()
                return
            except (RedisError, TypeError) as e:
                logger.error(f"다중 캐시 저장 실패 (시도 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise CacheError(f"다중 캐시 저장 실패: {e}")

def cached(
    prefix: str = "cache",
    ttl: Optional[int] = None,
    key_builder: Optional[callable] = None
):
    """함수 결과를 캐시하는 데코레이터.
    
    Args:
        prefix: 캐시 키 접두사
        ttl: 캐시 유효 시간 (초)
        key_builder: 커스텀 키 생성 함수
        
    Returns:
        데코레이터 함수
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # 캐시 키 생성
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = cache._generate_key(prefix, *args, **kwargs)
            
            # 캐시된 값 확인
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # 함수 실행 및 결과 캐시
            result = await func(*args, **kwargs)
            await cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator

def get_cache(
    ttl: int = 300,
    host: str = None,
    port: int = None,
    db: int = None,
    password: str = None
) -> Cache:
    """캐시 인스턴스를 생성합니다.
    
    Args:
        ttl: 기본 캐시 유효 시간 (초)
        host: Redis 호스트
        port: Redis 포트
        db: Redis 데이터베이스 번호
        password: Redis 비밀번호
        
    Returns:
        Cache 인스턴스
    """
    return Cache(
        ttl=ttl,
        host=host,
        port=port,
        db=db,
        password=password
    )
