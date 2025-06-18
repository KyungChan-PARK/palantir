from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import uuid
from datetime import datetime
import asyncio

from ..core.state import AgentState, StateStore
from .task_manager import AgentTaskManager

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """모든 에이전트의 공통 인터페이스"""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        state_store: Optional[StateStore] = None,
        max_workers: int = 10,
        task_timeout: int = 300,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.state_store = state_store or StateStore()
        self.state = AgentState(self.state_store, self.agent_id)
        self.task_manager = AgentTaskManager(
            state_store=self.state_store,
            process_func=self._process_task_impl,
            max_workers=max_workers,
            task_timeout=task_timeout,
        )
        self._initialize_state()

    def _initialize_state(self):
        """초기 상태 설정"""
        self.state.set_status({
            "status": "initialized",
            "started_at": datetime.utcnow().isoformat(),
        })
        self.state.update_metrics({
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_processing_time": 0,
        })

    async def start(self):
        """에이전트 시작"""
        logger.info(f"Starting agent {self.agent_id}")
        self.state.set_status({"status": "running"})
        self._start_heartbeat()
        await self.task_manager.start()

    async def stop(self):
        """에이전트 중지"""
        logger.info(f"Stopping agent {self.agent_id}")
        await self.task_manager.stop()
        self.state.set_status({"status": "stopped"})

    def _start_heartbeat(self):
        """하트비트 시작"""
        self.state.update_heartbeat()

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """작업 처리"""
        logger.info(f"Submitting task to agent {self.agent_id}")
        
        # 작업 제출
        task_id = await self.task_manager.submit_task(task)
        self.state.add_task(task_id)
        
        try:
            # 작업 완료 대기
            while True:
                status = await self.task_manager.get_task_status(task_id)
                if not status:
                    raise Exception(f"Task {task_id} not found")
                
                if status["status"] in ["completed", "failed", "timeout"]:
                    if status["status"] == "completed":
                        self.state.increment_metric("tasks_completed")
                        if "processing_time" in status:
                            self._update_processing_time(status["processing_time"])
                        return status["result"]
                    else:
                        self.state.increment_metric("tasks_failed")
                        raise Exception(status.get("error", "Unknown error"))
                
                await asyncio.sleep(0.1)
                
        finally:
            self.state.remove_task(task_id)

    async def _process_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """작업 처리 구현 (하위 클래스에서 오버라이드)"""
        raise NotImplementedError()

    def _update_processing_time(self, processing_time: float):
        """처리 시간 메트릭 업데이트"""
        metrics = self.state.get_metrics() or {}
        total_time = metrics.get("total_processing_time", 0) + processing_time
        self.state.update_metrics({
            "total_processing_time": total_time,
            "avg_processing_time": total_time / metrics.get("tasks_completed", 1),
        })

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        status = self.state.get_status() or {}
        metrics = self.state.get_metrics() or {}
        tasks = self.state.get_task_queue()
        task_stats = self.task_manager.get_stats()
        
        return {
            "agent_id": self.agent_id,
            "status": status.get("status", "unknown"),
            "metrics": metrics,
            "task_stats": task_stats,
            "pending_tasks": list(tasks),
            "is_alive": self.state.is_alive(),
            "last_heartbeat": self.state.get_last_heartbeat(),
        }
