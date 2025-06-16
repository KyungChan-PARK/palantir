import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter()

# 임시 저장소 (실제로는 데이터베이스를 사용해야 함)
_memory_store: Dict[str, Any] = {}


@router.get("/report/{job_id}")
async def get_report(job_id: str, request: Request):
    if job_id not in _memory_store:
        if request.headers.get("accept") == "application/json":
            raise HTTPException(status_code=404, detail="job_id not found")
        return Response(content="Job not found", status_code=404)

    report = _memory_store[job_id]
    if request.headers.get("accept") == "application/json":
        return report
    return Response(content=str(report), media_type="text/html")


@router.post("/report")
async def create_report(data: Dict[str, Any]):
    job_id = data.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    _memory_store[job_id] = data
    return {"status": "success", "job_id": job_id}
