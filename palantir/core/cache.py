from functools import wraps
import json
from typing import Any, Optional
import redis
from .config import settings

# Redis 연결
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

async def get_cache(key: str) -> Optional[str]:
    """캐시에서 값을 가져옵니다."""
    try:
        return redis_client.get(key)
    except Exception:
        return None

async def set_cache(key: str, value: str, ttl: int = 300) -> bool:
    """캐시에 값을 저장합니다."""
    try:
        redis_client.setex(key, ttl, value)
        return True
    except Exception:
        return False

def cache_response(func):
    """함수 결과를 캐시하는 데코레이터입니다."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 캐시 키 생성
        key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
        
        # 캐시된 결과 확인
        cached_result = await get_cache(key)
        if cached_result:
            return json.loads(cached_result)
        
        # 함수 실행 및 결과 캐시
        result = await func(*args, **kwargs)
        await set_cache(key, json.dumps(result))
        return result
    
    return wrapper
