from fastapi import FastAPI
from datetime import datetime
import os
from palantir.api.pipeline import router as pipeline_router
from palantir.api.ontology import router as ontology_router
from palantir.api.ask import router as ask_router
from palantir.core.policy_guard import limiter
from prometheus_fastapi_instrumentator import Instrumentator
from palantir.core.scheduler import scheduler
from palantir.core.backup import register_backup_jobs
from palantir.core.auth import router as auth_router
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
from palantir.api.metrics import router as metrics_router
from palantir.api.upload import router as upload_router
from palantir.api.report import router as report_router

app = FastAPI()
app.state.limiter = limiter
Instrumentator().instrument(app).expose(app)
app.include_router(pipeline_router)
app.include_router(ask_router)
app.include_router(ontology_router)
app.include_router(auth_router)
app.include_router(metrics_router)
app.include_router(upload_router)
app.include_router(report_router)

scheduler = BackgroundScheduler()
scheduler.start()

def run_self_improve():
    subprocess.call(["python", "self_improve.py"])

scheduler.add_job(run_self_improve, "cron", hour=3, minute=0)

register_backup_jobs(scheduler)

@app.get("/status")
def get_status():
    today = datetime.now().strftime("%Y%m%d")
    self_improve_log = os.path.exists(f"logs/self_improve_{today}.md")
    return {
        "app": "ok",
        "weaviate": "ok",  # 실제 부트 시 헬스체크로 대체
        "neo4j": "ok",     # 실제 부트 시 헬스체크로 대체
        "self_improve": "ok" if self_improve_log else "pending",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 