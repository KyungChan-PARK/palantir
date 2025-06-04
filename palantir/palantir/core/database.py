"""데이터베이스 연결 및 캐싱 설정 모듈."""

import asyncio
import json
import logging
import os
import time
from functools import lru_cache, wraps
from typing import Generator, Optional

import asyncpg
import redis.asyncio as redis
from asyncpg.pool import Pool
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .user import UserDB

logger = logging.getLogger(__name__)

# 데이터베이스 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/palantir")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 데이터베이스 엔진 설정
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # 최대 연결 수
    max_overflow=10,  # 추가 연결 허용 수
    pool_timeout=30,  # 연결 대기 시간
    pool_recycle=1800,  # 연결 재사용 시간
    pool_pre_ping=True,  # 연결 상태 확인
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis 클라이언트 설정
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

class DatabaseManager:
    _instance = None
    _pool: Optional[Pool] = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(cls, dsn: str, redis_url: str):
        """데이터베이스 연결 풀과 Redis 클라이언트를 초기화합니다."""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                dsn,
                min_size=5,  # 최소 연결 수
                max_size=20,  # 최대 연결 수
                command_timeout=60,  # 명령 타임아웃
                statement_cache_size=100,  # 문장 캐시 크기
                max_cached_statement_lifetime=300,  # 캐시된 문장 수명
                max_queries=50000,  # 연결당 최대 쿼리 수
                max_inactive_connection_lifetime=300.0  # 비활성 연결 수명
            )
            logger.info("데이터베이스 연결 풀이 초기화되었습니다.")
        
        if cls._redis_client is None:
            cls._redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,  # 최대 연결 수
                socket_timeout=5,  # 소켓 타임아웃
                socket_connect_timeout=5,  # 연결 타임아웃
                retry_on_timeout=True  # 타임아웃 시 재시도
            )
            logger.info("Redis 클라이언트가 초기화되었습니다.")
    
    @classmethod
    async def get_pool(cls) -> Pool:
        """데이터베이스 연결 풀을 반환합니다."""
        if cls._pool is None:
            raise RuntimeError("데이터베이스 연결 풀이 초기화되지 않았습니다.")
        return cls._pool
    
    @classmethod
    async def get_redis(cls) -> redis.Redis:
        """Redis 클라이언트를 반환합니다."""
        if cls._redis_client is None:
            raise RuntimeError("Redis 클라이언트가 초기화되지 않았습니다.")
        return cls._redis_client
    
    @classmethod
    async def close(cls):
        """데이터베이스 연결 풀과 Redis 클라이언트를 종료합니다."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("데이터베이스 연결 풀이 종료되었습니다.")
        
        if cls._redis_client:
            await cls._redis_client.close()
            cls._redis_client = None
            logger.info("Redis 클라이언트가 종료되었습니다.")

def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션을 생성합니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@lru_cache(maxsize=1000)
def get_cached_user(user_id: str) -> dict:
    """캐시된 사용자 정보를 조회합니다."""
    # Redis에서 사용자 정보 조회
    user_data = redis_client.get(f"user:{user_id}")
    if user_data:
        return eval(user_data)  # 문자열을 딕셔너리로 변환
    
    # 데이터베이스에서 사용자 정보 조회
    db = SessionLocal()
    try:
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if user:
            user_dict = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "scopes": user.scopes,
                "disabled": user.disabled
            }
            # Redis에 사용자 정보 캐싱 (1시간)
            redis_client.setex(f"user:{user_id}", 3600, str(user_dict))
            return user_dict
    finally:
        db.close()
    return None

def invalidate_user_cache(user_id: str) -> None:
    """사용자 캐시를 무효화합니다."""
    redis_client.delete(f"user:{user_id}")
    get_cached_user.cache_clear()  # LRU 캐시 초기화

def get_db_stats() -> dict:
    """데이터베이스 연결 풀 통계를 반환합니다."""
    return {
        "pool_size": engine.pool.size(),
        "checkedin": engine.pool.checkedin(),
        "checkedout": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "checkedin_connections": len(engine.pool._pool),
        "checkedout_connections": len(engine.pool._checked_out)
    }

def get_redis_stats() -> dict:
    """Redis 통계를 반환합니다."""
    info = redis_client.info()
    return {
        "connected_clients": info["connected_clients"],
        "used_memory": info["used_memory"],
        "used_memory_peak": info["used_memory_peak"],
        "total_connections_received": info["total_connections_received"],
        "total_commands_processed": info["total_commands_processed"]
    }

def with_cache(ttl: int = 300):
    """Redis 캐시를 사용하는 데코레이터입니다."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Redis 클라이언트 가져오기
            redis_client = await DatabaseManager.get_redis()
            
            # 캐시된 결과 확인
            cached_result = await redis_client.get(cache_key)
            if cached_result:
                logger.debug(f"캐시에서 결과를 가져왔습니다: {cache_key}")
                return json.loads(cached_result)
            
            # 함수 실행
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 결과 캐싱
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            
            logger.debug(f"결과를 캐시에 저장했습니다: {cache_key} (실행 시간: {execution_time:.2f}초)")
            return result
        return wrapper
    return decorator

def with_retry(max_retries: int = 3, delay: float = 1.0):
    """재시도 로직을 포함하는 데코레이터입니다."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                        logger.warning(f"재시도 중... (시도 {attempt + 1}/{max_retries})")
            
            logger.error(f"최대 재시도 횟수를 초과했습니다: {str(last_error)}")
            raise last_error
        return wrapper
    return decorator

class QueryBuilder:
    """SQL 쿼리 빌더 클래스입니다."""
    
    def __init__(self, table: str):
        self.table = table
        self._select = ["*"]
        self._where = []
        self._order_by = []
        self._limit = None
        self._offset = None
        self._params = {}
        self._param_counter = 0
    
    def select(self, *columns: str) -> 'QueryBuilder':
        """SELECT 절을 설정합니다."""
        self._select = list(columns) if columns else ["*"]
        return self
    
    def where(self, condition: str, **params) -> 'QueryBuilder':
        """WHERE 절을 추가합니다."""
        self._where.append(condition)
        self._params.update(params)
        return self
    
    def order_by(self, column: str, direction: str = "ASC") -> 'QueryBuilder':
        """ORDER BY 절을 추가합니다."""
        self._order_by.append(f"{column} {direction}")
        return self
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """LIMIT 절을 설정합니다."""
        self._limit = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """OFFSET 절을 설정합니다."""
        self._offset = offset
        return self
    
    def build(self) -> tuple[str, dict]:
        """SQL 쿼리를 생성합니다."""
        query_parts = ["SELECT", ", ".join(self._select), "FROM", self.table]
        
        if self._where:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(self._where))
        
        if self._order_by:
            query_parts.append("ORDER BY")
            query_parts.append(", ".join(self._order_by))
        
        if self._limit is not None:
            query_parts.append(f"LIMIT {self._limit}")
        
        if self._offset is not None:
            query_parts.append(f"OFFSET {self._offset}")
        
        return " ".join(query_parts), self._params 