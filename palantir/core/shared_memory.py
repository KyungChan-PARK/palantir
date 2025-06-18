"""공유 메모리 시스템 구현"""

import json
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
import redis
from pydantic import BaseModel

from .config import settings


class MemoryEntry(BaseModel):
    """메모리 엔트리 모델"""
    key: str
    value: Any
    type: str  # 'fact', 'task_result', 'error', 'metric' 등
    timestamp: datetime
    ttl: Optional[int] = None  # 초 단위 TTL, None은 영구 보관
    tags: Set[str] = set()
    metadata: Dict[str, Any] = {}


class SharedMemory:
    """분산 공유 메모리 시스템"""

    def __init__(self, redis_url: Optional[str] = None):
        """Redis 기반 공유 메모리 초기화"""
        self.redis = redis.Redis.from_url(
            redis_url or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

    async def store(
        self,
        key: str,
        value: Any,
        type: str,
        ttl: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """메모리에 데이터 저장"""
        try:
            entry = MemoryEntry(
                key=key,
                value=value,
                type=type,
                timestamp=datetime.utcnow(),
                ttl=ttl,
                tags=tags or set(),
                metadata=metadata or {}
            )
            
            # Redis에 저장
            success = self.redis.set(
                f"memory:{key}",
                json.dumps(entry.dict()),
                ex=ttl
            )
            
            # 태그 인덱스 업데이트
            if tags:
                for tag in tags:
                    self.redis.sadd(f"tag:{tag}", key)
            
            return bool(success)
        except Exception as e:
            print(f"메모리 저장 실패: {str(e)}")
            return False

    async def retrieve(
        self,
        key: str,
        default: Any = None
    ) -> Optional[MemoryEntry]:
        """메모리에서 데이터 검색"""
        try:
            data = self.redis.get(f"memory:{key}")
            if not data:
                return default
            
            entry_dict = json.loads(data)
            entry_dict["timestamp"] = datetime.fromisoformat(entry_dict["timestamp"])
            return MemoryEntry(**entry_dict)
        except Exception as e:
            print(f"메모리 검색 실패: {str(e)}")
            return default

    async def search_by_tags(
        self,
        tags: Set[str],
        match_all: bool = True
    ) -> List[MemoryEntry]:
        """태그로 메모리 검색"""
        try:
            # 태그별 키 집합 가져오기
            key_sets = [
                self.redis.smembers(f"tag:{tag}")
                for tag in tags
            ]
            
            if not key_sets:
                return []
            
            # 교집합 또는 합집합 연산
            if match_all:
                keys = set.intersection(*map(set, key_sets))
            else:
                keys = set.union(*map(set, key_sets))
            
            # 각 키에 대한 메모리 엔트리 검색
            entries = []
            for key in keys:
                entry = await self.retrieve(key)
                if entry:
                    entries.append(entry)
            
            return entries
        except Exception as e:
            print(f"태그 검색 실패: {str(e)}")
            return []

    async def update_ttl(self, key: str, new_ttl: int) -> bool:
        """메모리 엔트리의 TTL 업데이트"""
        try:
            entry = await self.retrieve(key)
            if not entry:
                return False
            
            entry.ttl = new_ttl
            return await self.store(
                key=key,
                value=entry.value,
                type=entry.type,
                ttl=new_ttl,
                tags=entry.tags,
                metadata=entry.metadata
            )
        except Exception as e:
            print(f"TTL 업데이트 실패: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """메모리 엔트리 삭제"""
        try:
            # 태그 인덱스에서 제거
            entry = await self.retrieve(key)
            if entry and entry.tags:
                for tag in entry.tags:
                    self.redis.srem(f"tag:{tag}", key)
            
            # 메모리 엔트리 삭제
            return bool(self.redis.delete(f"memory:{key}"))
        except Exception as e:
            print(f"메모리 삭제 실패: {str(e)}")
            return False

    async def cleanup_expired(self) -> int:
        """만료된 메모리 엔트리 정리"""
        try:
            pattern = "memory:*"
            cleaned = 0
            
            # 모든 메모리 키 스캔
            for key in self.redis.scan_iter(pattern):
                # TTL 확인
                ttl = self.redis.ttl(key)
                if ttl < 0:  # 만료되었거나 TTL이 설정되지 않은 경우
                    if await self.delete(key.split(":", 1)[1]):
                        cleaned += 1
            
            return cleaned
        except Exception as e:
            print(f"만료 정리 실패: {str(e)}")
            return 0 