import asyncio
from typing import Any, Callable, Dict, List, Optional, Set
import logging
from datetime import datetime
import uuid

from .state import StateStore

logger = logging.getLogger(__name__)


class Task:
    """작업 클래스"""

    def __init__(
        self,
        task_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 0,
    ):
        self.task_id = task_id or str(uuid.uuid4())
        self.payload = payload or {}
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.status = "pending"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """작업 정보를 딕셔너리로 변환"""
        return {
            "task_id": self.task_id,
            "payload": self.payload,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "result": self.result,
            "error": self.error,
        }


class TaskManager:
    """병렬 작업 관리자"""

    def __init__(
        self,
        state_store: StateStore,
        max_workers: int = 10,
        task_timeout: int = 300,
    ):
        self.state_store = state_store
        self.max_workers = max_workers
        self.task_timeout = task_timeout
        self.tasks: Dict[str, Task] = {}
        self.pending_tasks: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_tasks: Set[str] = set()
        self.workers: List[asyncio.Task] = []
        self._stop_event = asyncio.Event()

    async def start(self):
        """작업 관리자 시작"""
        logger.info("Starting task manager")
        self._stop_event.clear()
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]

    async def stop(self):
        """작업 관리자 중지"""
        logger.info("Stopping task manager")
        self._stop_event.set()
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def submit_task(
        self,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
        priority: int = 0,
    ) -> str:
        """작업 제출"""
        task = Task(task_id, payload, priority)
        self.tasks[task.task_id] = task
        await self.pending_tasks.put((priority, task.task_id))
        logger.info(f"Submitted task {task.task_id} with priority {priority}")
        return task.task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

    async def cancel_task(self, task_id: str) -> bool:
        """작업 취소"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status == "pending":
                task.status = "cancelled"
                task.completed_at = datetime.utcnow()
                return True
        return False

    async def _worker(self, worker_id: int):
        """작업자 코루틴"""
        logger.info(f"Starting worker {worker_id}")
        
        while not self._stop_event.is_set():
            try:
                # 작업 가져오기
                priority, task_id = await asyncio.wait_for(
                    self.pending_tasks.get(),
                    timeout=1.0,
                )
                
                # 작업이 여전히 유효한지 확인
                if task_id not in self.tasks:
                    continue
                    
                task = self.tasks[task_id]
                if task.status != "pending":
                    continue

                # 작업 실행
                self.active_tasks.add(task_id)
                task.status = "running"
                task.started_at = datetime.utcnow()
                
                try:
                    # 작업 처리 (실제 구현은 하위 클래스에서)
                    result = await self._process_task(task)
                    
                    # 성공 처리
                    task.status = "completed"
                    task.result = result
                    
                except asyncio.TimeoutError:
                    task.status = "timeout"
                    task.error = "Task execution timed out"
                    
                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
                    logger.error(f"Task {task_id} failed: {e}")
                    
                finally:
                    task.completed_at = datetime.utcnow()
                    self.active_tasks.remove(task_id)
                    
            except asyncio.TimeoutError:
                continue
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")

    async def _process_task(self, task: Task) -> Dict[str, Any]:
        """작업 처리 (하위 클래스에서 구현)"""
        raise NotImplementedError()

    def get_stats(self) -> Dict[str, Any]:
        """작업 관리자 통계"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed_tasks = sum(1 for t in self.tasks.values() if t.status in ["failed", "timeout"])
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "active_tasks": len(self.active_tasks),
            "pending_tasks": self.pending_tasks.qsize(),
            "workers": len(self.workers),
        }


class AgentTaskManager(TaskManager):
    """에이전트 작업 관리자"""

    def __init__(
        self,
        state_store: StateStore,
        process_func: Callable[[Dict[str, Any]], Any],
        max_workers: int = 10,
        task_timeout: int = 300,
    ):
        super().__init__(state_store, max_workers, task_timeout)
        self.process_func = process_func

    async def _process_task(self, task: Task) -> Dict[str, Any]:
        """에이전트 작업 처리"""
        try:
            result = await asyncio.wait_for(
                self.process_func(task.payload),
                timeout=self.task_timeout,
            )
            return {"result": result}
            
        except asyncio.TimeoutError:
            raise
            
        except Exception as e:
            logger.error(f"Task processing error: {e}")
            raise 