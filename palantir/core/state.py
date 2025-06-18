from typing import Any, Dict, Optional, Set
import json
import logging
from datetime import datetime, timedelta

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class StateStore:
    """중앙 집중식 상태 관리를 위한 Redis 기반 상태 저장소"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "palantir:state:",
        default_ttl: int = 3600,
    ):
        """
        Args:
            redis_url: Redis 연결 URL
            prefix: 키 접두사
            default_ttl: 기본 TTL (초)
        """
        self.redis = redis.from_url(redis_url)
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """Redis 키 생성"""
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """상태 값 조회"""
        try:
            value = self.redis.get(self._make_key(key))
            return json.loads(value) if value else None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get state for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """상태 값 설정"""
        try:
            json_value = json.dumps(value)
            return bool(
                self.redis.set(
                    self._make_key(key),
                    json_value,
                    ex=ttl or self.default_ttl,
                )
            )
        except (RedisError, TypeError) as e:
            logger.error(f"Failed to set state for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """상태 값 삭제"""
        try:
            return bool(self.redis.delete(self._make_key(key)))
        except RedisError as e:
            logger.error(f"Failed to delete state for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """상태 키 존재 여부 확인"""
        try:
            return bool(self.redis.exists(self._make_key(key)))
        except RedisError as e:
            logger.error(f"Failed to check existence for key {key}: {e}")
            return False

    def get_ttl(self, key: str) -> Optional[int]:
        """상태 값의 TTL 조회"""
        try:
            ttl = self.redis.ttl(self._make_key(key))
            return ttl if ttl > -1 else None
        except RedisError as e:
            logger.error(f"Failed to get TTL for key {key}: {e}")
            return None

    def extend_ttl(self, key: str, ttl: Optional[int] = None) -> bool:
        """상태 값의 TTL 연장"""
        try:
            return bool(
                self.redis.expire(
                    self._make_key(key),
                    ttl or self.default_ttl,
                )
            )
        except RedisError as e:
            logger.error(f"Failed to extend TTL for key {key}: {e}")
            return False

    def add_to_set(self, key: str, *values: Any) -> bool:
        """Set에 값 추가"""
        try:
            json_values = [json.dumps(v) for v in values]
            return bool(self.redis.sadd(self._make_key(key), *json_values))
        except (RedisError, TypeError) as e:
            logger.error(f"Failed to add to set {key}: {e}")
            return False

    def remove_from_set(self, key: str, *values: Any) -> bool:
        """Set에서 값 제거"""
        try:
            json_values = [json.dumps(v) for v in values]
            return bool(self.redis.srem(self._make_key(key), *json_values))
        except (RedisError, TypeError) as e:
            logger.error(f"Failed to remove from set {key}: {e}")
            return False

    def get_set_members(self, key: str) -> Set[Any]:
        """Set의 모든 멤버 조회"""
        try:
            members = self.redis.smembers(self._make_key(key))
            return {json.loads(m) for m in members}
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get set members for key {key}: {e}")
            return set()

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """카운터 증가"""
        try:
            return self.redis.incrby(self._make_key(key), amount)
        except RedisError as e:
            logger.error(f"Failed to increment counter {key}: {e}")
            return None

    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """카운터 감소"""
        try:
            return self.redis.decrby(self._make_key(key), amount)
        except RedisError as e:
            logger.error(f"Failed to decrement counter {key}: {e}")
            return None

    def clear_all(self, pattern: Optional[str] = None) -> bool:
        """모든 상태 값 삭제"""
        try:
            pattern = pattern or f"{self.prefix}*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except RedisError as e:
            logger.error(f"Failed to clear all states: {e}")
            return False


class AgentState:
    """에이전트 상태 관리를 위한 클래스"""

    def __init__(self, store: StateStore, agent_id: str):
        self.store = store
        self.agent_id = agent_id
        self.base_key = f"agent:{agent_id}"

    def get_status(self) -> Optional[Dict[str, Any]]:
        """에이전트 상태 조회"""
        return self.store.get(f"{self.base_key}:status")

    def set_status(self, status: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """에이전트 상태 설정"""
        status["updated_at"] = datetime.utcnow().isoformat()
        return self.store.set(f"{self.base_key}:status", status, ttl)

    def get_task_queue(self) -> Set[str]:
        """작업 큐 조회"""
        return self.store.get_set_members(f"{self.base_key}:tasks")

    def add_task(self, task_id: str) -> bool:
        """작업 추가"""
        return self.store.add_to_set(f"{self.base_key}:tasks", task_id)

    def remove_task(self, task_id: str) -> bool:
        """작업 제거"""
        return self.store.remove_from_set(f"{self.base_key}:tasks", task_id)

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """메트릭 조회"""
        return self.store.get(f"{self.base_key}:metrics")

    def update_metrics(self, metrics: Dict[str, Any]) -> bool:
        """메트릭 업데이트"""
        current = self.get_metrics() or {}
        current.update(metrics)
        current["updated_at"] = datetime.utcnow().isoformat()
        return self.store.set(f"{self.base_key}:metrics", current)

    def increment_metric(self, metric_name: str, amount: int = 1) -> Optional[int]:
        """메트릭 증가"""
        return self.store.increment(f"{self.base_key}:metric:{metric_name}", amount)

    def get_last_heartbeat(self) -> Optional[str]:
        """마지막 하트비트 시간 조회"""
        return self.store.get(f"{self.base_key}:heartbeat")

    def update_heartbeat(self) -> bool:
        """하트비트 업데이트"""
        return self.store.set(
            f"{self.base_key}:heartbeat",
            datetime.utcnow().isoformat(),
            ttl=60,  # 1분
        )

    def is_alive(self, timeout: int = 60) -> bool:
        """에이전트 활성 상태 확인"""
        last_heartbeat = self.get_last_heartbeat()
        if not last_heartbeat:
            return False
        try:
            last_time = datetime.fromisoformat(last_heartbeat)
            return datetime.utcnow() - last_time < timedelta(seconds=timeout)
        except ValueError:
            return False 