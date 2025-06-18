import os
import platform
from datetime import datetime
from typing import Dict, Any, List

import psutil
from fastapi import APIRouter, HTTPException

from palantir.core.orchestrator import Orchestrator
from palantir.models.state import OrchestratorState

router = APIRouter()

# 오케스트레이터 인스턴스 저장
orchestrator: Orchestrator = None


@router.get("/status")
def status():
    return {
        "status": "ok",
        "version": "5.0.0",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
        },
    }


@router.post("/orchestrator/run")
async def run_orchestrator(user_input: str) -> Dict[str, Any]:
    global orchestrator
    if not orchestrator:
        orchestrator = Orchestrator()
    
    result = await orchestrator.run(user_input)
    return {
        "status": "success",
        "state": result.dict(),
        "improvements": [imp for task in result.results for imp in task.improvement_history]
    }


@router.get("/orchestrator/history")
def get_orchestrator_history() -> Dict[str, Any]:
    global orchestrator
    if not orchestrator or not hasattr(orchestrator, "state"):
        return {
            "history": [],
            "state": None,
            "improvements": [],
            "rollbacked": [],
            "rollback_reasons": [],
            "policy_violations": []
        }

    state = orchestrator.state
    
    # 태스크별 개선/롤백/정책 이력 추출
    improvements: List[Dict[str, Any]] = []
    rollbacked: List[Dict[str, Any]] = []
    rollback_reasons: List[str] = []
    policy_violations: List[Dict[str, Any]] = []
    
    for task_state in state.results:
        # 개선 이력
        if task_state.improvement_history:
            improvements.append({
                "task": task_state.task,
                "improvements": task_state.improvement_history
            })
        
        # 롤백 이력
        if task_state.fail_history:
            for fail in task_state.fail_history:
                if isinstance(fail.improvement, dict) and fail.improvement.get("rollbacked"):
                    rollbacked.append({
                        "task": task_state.task,
                        "fail_loop": fail.fail_loop
                    })
                    if "rollback_reason" in fail.improvement:
                        rollback_reasons.append(fail.improvement["rollback_reason"])
        
        # 정책 위반 이력
        if state.policy_triggered:
            policy_violations.append({"task": task_state.task})

    return {
        "history": state.history,
        "state": state.dict(),
        "improvements": improvements,
        "rollbacked": rollbacked,
        "rollback_reasons": rollback_reasons,
        "policy_violations": policy_violations
    }
