"""리포트 조회, 승인/거절, CSV 다운로드 API 라우터.

업로드된 데이터의 리포트 생성 및 후속 파이프라인 트리거를 담당한다.
"""

import io
import os
from typing import Any

import pandas as pd
from fastapi import APIRouter, Form, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)

from palantir.core.scheduler import add_pipeline_job
from palantir.core.visualization import generate_plotly_html
from palantir.core.weaviate_store import get_data_by_job_id

router = APIRouter()

REPORT_DIR = "ui/reports"
os.makedirs(REPORT_DIR, exist_ok=True)


@router.get("/report/{job_id}", response_class=HTMLResponse)
def report(job_id: str, request: Request) -> HTMLResponse:
    """리포트 HTML/JSON 반환 엔드포인트.

    Args:
        job_id: 작업 식별자
        request: FastAPI 요청 객체
    Returns:
        HTMLResponse: 리포트 페이지 또는 JSON
    """
    data = get_data_by_job_id(job_id)
    if not data:
        if "application/json" in request.headers.get("accept", "").lower():
            return JSONResponse(status_code=404, content={"detail": "job_id not found"})
        return HTMLResponse("<h2>Job not found</h2>", status_code=404)
    if "application/json" in request.headers.get("accept", "").lower():
        return JSONResponse(content=data)
    plot_html = generate_plotly_html(data)
    html = f"""
    <html><body>
    <h2>Job {job_id} Report</h2>
    {plot_html}
    <form method='post' action='/report/{job_id}/action'>
      <button name='action' value='approve'>Approve</button>
      <button name='action' value='reject'>Reject</button>
    </form>
    </body></html>
    """
    with open(f"{REPORT_DIR}/{job_id}.html", "w", encoding="utf-8") as f:
        f.write(html)
    return HTMLResponse(html)


@router.post("/report/{job_id}/action")
def report_action(job_id: str, action: str = Form(...)) -> RedirectResponse:
    """리포트 승인/거절 엔드포인트.

    Args:
        job_id: 작업 식별자
        action: 'approve' 또는 'reject'
    Returns:
        RedirectResponse: 결과 페이지 리다이렉트
    """
    if action == "approve":
        data = get_data_by_job_id(job_id)
        add_pipeline_job(data)  # 실제 파이프라인 등록
        return RedirectResponse(f"/report/{job_id}?result=approved", status_code=303)
    with open(f"ui/reports/{job_id}_feedback.txt", "w", encoding="utf-8") as f:
        f.write("rejected")
    # TODO: LLM Evals 학습 연동
    return RedirectResponse(f"/report/{job_id}?result=rejected", status_code=303)


@router.get("/download/{job_id}")
def download_csv(job_id: str) -> Any:
    """대용량 CSV 전체 다운로드 엔드포인트.

    Args:
        job_id: 작업 식별자
    Returns:
        StreamingResponse: CSV 파일 다운로드
    """
    data = get_data_by_job_id(job_id)
    if not data or data.get("type") != "table":
        return JSONResponse(status_code=404, content={"error": "CSV not found"})
    df = pd.DataFrame(data["data"])
    stream = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(stream),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={job_id}.csv"},
    )
