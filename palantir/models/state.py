from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class ImprovementHistory(BaseModel):
    improvement: Any
    fail_loop: int
    review: Any

class TaskState(BaseModel):
    task: str
    fail_history: List[ImprovementHistory] = []
    test_results: List[Any] = []
    improvement_history: List[Any] = []
    alert_sent: bool = False

class OrchestratorState(BaseModel):
    plan: List[str]
    current_task_idx: int = 0
    results: List[TaskState] = []
    fail_count: int = 0
    history: List[Any] = []
    alerts: List[Dict[str, Any]] = []
    policy_triggered: bool = False
    # 추가: 루프 중단/롤백/최종 리포트 등 확장 가능
    aborted: bool = False
    rollbacked: bool = False
    final_report: Optional[Any] = None 