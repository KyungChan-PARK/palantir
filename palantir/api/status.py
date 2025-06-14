from fastapi import APIRouter
import psutil
import platform
import os
from datetime import datetime
from palantir.core.orchestrator import Orchestrator
from palantir.models.state import OrchestratorState

router = APIRouter()

# 임시 글로벌 상태 (실제 운영에서는 세션/DB/캐시 등으로 확장 필요)
global_orch_state: OrchestratorState = None

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
            "disk_usage": psutil.disk_usage('/').percent
        }
    }

@router.post("/orchestrator/run")
def run_orchestrator(user_input: str):
    global global_orch_state
    orch = Orchestrator()
    result = orch.run(user_input)
    # Orchestrator 내부에서 state를 반환하도록 되어 있으므로, 마지막 state를 저장
    if hasattr(orch, 'state'):
        global_orch_state = orch.state
    else:
        # fallback: result가 state라면 저장
        global_orch_state = result if isinstance(result, OrchestratorState) else None
    return {"result": result}

@router.get("/orchestrator/history")
def get_orchestrator_history():
    if global_orch_state:
        # 태스크별 개선/롤백/정책 이력 추출
        improvements = []
        rollbacked = []
        rollback_reasons = []
        policy_violations = []
        for t in getattr(global_orch_state, 'results', []):
            # 개선 이력
            if hasattr(t, 'improvement_history') and t.improvement_history:
                improvements.append({"task": t.task, "improvements": t.improvement_history})
            # 롤백 이력(실패 이력에 롤백 사유 포함)
            if hasattr(t, 'fail_history') and t.fail_history:
                for fh in t.fail_history:
                    if hasattr(fh, 'improvement') and isinstance(fh.improvement, dict):
                        if fh.improvement.get('rollbacked'):
                            rollbacked.append({"task": t.task, "fail_loop": fh.fail_loop})
                            rollback_reasons.append(fh.improvement.get('rollback_reason'))
            # 정책 위반 이력
            if hasattr(global_orch_state, 'policy_triggered') and global_orch_state.policy_triggered:
                policy_violations.append({"task": t.task})
        return {
            "history": global_orch_state.history,
            "state": global_orch_state.dict(),
            "improvements": improvements,
            "rollbacked": rollbacked,
            "rollback_reasons": rollback_reasons,
            "policy_violations": policy_violations
        }
    else:
        return {"history": [], "state": None, "improvements": [], "rollbacked": [], "rollback_reasons": [], "policy_violations": []} 