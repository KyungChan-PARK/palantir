import os
import subprocess
from datetime import datetime

import httpx
from fastapi import FastAPI
from neo4j import GraphDatabase
from prometheus_fastapi_instrumentator import Instrumentator

from palantir.api.ask import router as ask_router
from palantir.api.metrics import router as metrics_router
from palantir.api.ontology import router as ontology_router
from palantir.api.pipeline import router as pipeline_router
from palantir.api.report import router as report_router
from palantir.api.upload import router as upload_router
from palantir.core.auth import router as auth_router
from palantir.core.backup import register_backup_jobs
from palantir.core.policy_guard import limiter
from palantir.core.scheduler import scheduler

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


def run_self_improve():
    subprocess.call(["python", "self_improve.py"])


scheduler.add_job(run_self_improve, "cron", hour=3, minute=0)

register_backup_jobs(scheduler)


@app.get("/status")
def get_status():
    today = datetime.now().strftime("%Y%m%d")
    self_improve_log = os.path.exists(f"logs/self_improve_{today}.md")

    # Weaviate 헬스 체크
    weaviate_ok = False
    try:
        r = httpx.get(f"{os.getenv('WEAVIATE_URL', 'http://localhost:8080')}/v1/.well-known/ready", timeout=1)
        weaviate_ok = r.status_code == 200
    except Exception:
        weaviate_ok = False

    # Neo4j 헬스 체크 (선택적)
    neo4j_ok = False
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    try:
        driver = GraphDatabase.driver(neo4j_url, auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASS", "test")))
        with driver.session() as session:
            session.run("RETURN 1")
            neo4j_ok = True
        driver.close()
    except Exception:
        neo4j_ok = False

    return {
        "app": "ok",
        "weaviate": "ok" if weaviate_ok else "error",
        "neo4j": "ok" if neo4j_ok else "error",
        "self_improve": "ok" if self_improve_log else "pending",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
