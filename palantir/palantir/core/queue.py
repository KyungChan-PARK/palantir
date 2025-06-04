"""비동기 작업 큐 모듈."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class AsyncQueue:
    """비동기 작업 큐 클래스."""

    def __init__(self, max_workers: int = 10):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self.workers: List[asyncio.Task] = []
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.task_results: Dict[str, Any] = {}

    async def start(self):
        """작업 큐를 시작합니다."""
        self.running = True
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
        logger.info(f"Started {self.max_workers} workers")

    async def stop(self):
        """작업 큐를 중지합니다."""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        self.executor.shutdown()
        logger.info("Queue stopped")

    async def _worker(self):
        """작업자 프로세스."""
        while self.running:
            try:
                task = await self.queue.get()
                if task is None:
                    break

                task_id, func, args, kwargs = task
                try:
                    # CPU 바운드 작업은 스레드 풀에서 실행
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = await asyncio.get_event_loop().run_in_executor(
                            self.executor, func, *args, **kwargs
                        )
                    self.task_results[task_id] = {
                        "status": "completed",
                        "result": result,
                        "completed_at": datetime.now().isoformat(),
                    }
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {str(e)}")
                    self.task_results[task_id] = {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.now().isoformat(),
                    }
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")

    async def enqueue(self, func: Callable, *args, **kwargs) -> str:
        """작업을 큐에 추가합니다."""
        task_id = f"task_{datetime.now().timestamp()}"
        await self.queue.put((task_id, func, args, kwargs))
        return task_id

    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """작업 결과를 조회합니다."""
        return self.task_results.get(task_id, {"status": "not_found"})

    def get_queue_stats(self) -> Dict[str, Any]:
        """큐 통계를 반환합니다."""
        return {
            "queue_size": self.queue.qsize(),
            "active_workers": len(self.workers),
            "completed_tasks": len(
                [t for t in self.task_results.values() if t["status"] == "completed"]
            ),
            "failed_tasks": len(
                [t for t in self.task_results.values() if t["status"] == "failed"]
            ),
        }


def async_task(func: Callable):
    """비동기 작업 데코레이터."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        queue = AsyncQueue()
        await queue.start()
        try:
            task_id = await queue.enqueue(func, *args, **kwargs)
            return task_id
        finally:
            await queue.stop()

    return wrapper


# 전역 작업 큐 인스턴스
task_queue = AsyncQueue()


async def process_background_task(func: Callable, *args, **kwargs) -> str:
    """백그라운드 작업을 처리합니다."""
    return await task_queue.enqueue(func, *args, **kwargs)


def get_task_status(task_id: str) -> Dict[str, Any]:
    """작업 상태를 조회합니다."""
    return task_queue.get_task_result(task_id)


def get_queue_status() -> Dict[str, Any]:
    """큐 상태를 조회합니다."""
    return task_queue.get_queue_stats()
