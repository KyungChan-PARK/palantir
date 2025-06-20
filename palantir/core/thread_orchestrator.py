import threading
import queue
import logging
from typing import Dict, Any, Callable, Optional
from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class Task:
    id: str
    func: Callable
    args: tuple
    kwargs: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None

class ThreadOrchestrator:
    def __init__(self, max_workers: int = 5):
        """
        스레드 기반 오케스트레이터 초기화
        
        Args:
            max_workers: 최대 작업자 스레드 수
        """
        self.max_workers = max_workers
        self.task_queue = queue.Queue()
        self.tasks: Dict[str, Task] = {}
        self.workers: list[threading.Thread] = []
        self.running = False
        self.lock = threading.Lock()
        
    def start(self):
        """오케스트레이터 시작"""
        with self.lock:
            if self.running:
                return
                
            self.running = True
            for _ in range(self.max_workers):
                worker = threading.Thread(target=self._worker_loop)
                worker.daemon = True
                worker.start()
                self.workers.append(worker)
            logger.info(f"오케스트레이터가 {self.max_workers}개의 작업자로 시작되었습니다.")
                
    def stop(self):
        """오케스트레이터 중지"""
        with self.lock:
            if not self.running:
                return
                
            self.running = False
            # 남은 작업 처리를 위해 빈 작업 추가
            for _ in self.workers:
                self.task_queue.put(None)
                
            for worker in self.workers:
                worker.join()
            self.workers.clear()
            logger.info("오케스트레이터가 중지되었습니다.")
            
    def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> Task:
        """
        새 작업 제출
        
        Args:
            task_id: 작업 ID
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
            
        Returns:
            Task: 생성된 작업 객체
        """
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        with self.lock:
            if task_id in self.tasks:
                raise ValueError(f"이미 존재하는 작업 ID입니다: {task_id}")
            self.tasks[task_id] = task
            self.task_queue.put(task)
            logger.info(f"새 작업이 제출되었습니다: {task_id}")
            
        return task
        
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """
        작업 상태 조회
        
        Args:
            task_id: 작업 ID
            
        Returns:
            Optional[Task]: 작업 객체 또는 None
        """
        return self.tasks.get(task_id)
        
    def _worker_loop(self):
        """작업자 스레드 메인 루프"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:  # 종료 신호
                    break
                    
                # 작업 실행
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                try:
                    task.result = task.func(*task.args, **task.kwargs)
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.error = e
                    task.status = TaskStatus.FAILED
                    logger.error(f"작업 실행 중 오류 발생 ({task.id}): {str(e)}")
                finally:
                    task.completed_at = datetime.now()
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"작업자 스레드에서 예기치 않은 오류 발생: {str(e)}")
                
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Task:
        """
        작업 완료 대기
        
        Args:
            task_id: 작업 ID
            timeout: 최대 대기 시간 (초)
            
        Returns:
            Task: 완료된 작업 객체
            
        Raises:
            TimeoutError: 제한 시간 초과
            KeyError: 존재하지 않는 작업 ID
        """
        if task_id not in self.tasks:
            raise KeyError(f"존재하지 않는 작업 ID입니다: {task_id}")
            
        task = self.tasks[task_id]
        start_time = datetime.now()
        
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            if timeout is not None:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    raise TimeoutError(f"작업 대기 시간 초과: {task_id}")
            threading.Event().wait(0.1)  # CPU 부하 방지
            
        return task 