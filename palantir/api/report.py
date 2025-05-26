from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from palantir.core.weaviate_store import get_data_by_job_id
from palantir.core.visualization import generate_plotly_html
from palantir.core.scheduler import add_pipeline_job
import os

router = APIRouter()

REPORT_DIR = "ui/reports"
os.makedirs(REPORT_DIR, exist_ok=True)


@router.get("/report/{job_id}", response_class=HTMLResponse)
def report(job_id: str, request: Request):
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
def report_action(job_id: str, action: str = Form(...)):
    if action == "approve":
        data = get_data_by_job_id(job_id)
        add_pipeline_job(data)  # 실제 파이프라인 등록
        return RedirectResponse(f"/report/{job_id}?result=approved", status_code=303)
    else:
        with open(f"ui/reports/{job_id}_feedback.txt", "w", encoding="utf-8") as f:
            f.write("rejected")
        # TODO: LLM Evals 학습 연동
        return RedirectResponse(f"/report/{job_id}?result=rejected", status_code=303)
