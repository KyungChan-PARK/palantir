from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
from palantir.core.action_executor import run_deployment
from palantir.ontology.base import OntologyAction

router = APIRouter()

actions_db: Dict[str, OntologyAction] = {}  # 실제 환경에서는 DB에서 조회

class TriggerRequest(BaseModel):
    parameters: Dict[str, Any] = {}

@router.post("/actions/{id}/trigger")
async def trigger_action(
    id: str = Path(..., description="액션 ID"),
    req: TriggerRequest = Body(...)
):
    # 실제 환경에서는 DB에서 액션 조회
    action = actions_db.get(id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    flow_run_id = await run_deployment(action.handler, req.parameters)
    return {"flow_run_id": flow_run_id} 