import os
import subprocess
from datetime import datetime

import httpx
from fastapi import FastAPI
from neo4j import GraphDatabase

from palantir.api.ask import router as ask_router
from palantir.api.qa import router as qa_router
from palantir.api.metrics import router as metrics_router
from palantir.api.ontology import router as ontology_router
from palantir.api.pipeline import router as pipeline_router
from palantir.api.report import router as report_router
from palantir.api.upload import router as upload_router
from palantir.auth.rate_limit import RateLimitMiddleware
from palantir.auth.router import router as auth_router
from palantir.core.backup import register_backup_jobs
from palantir.core.error_handlers import register_error_handlers
from palantir.core.monitoring import setup_monitoring
from palantir.core.scheduler import scheduler

app = FastAPI(
    title="Palantir-Inspired Local AI Ops Suite",
    description="로컬 AI Ops 플랫폼",
    version="5.0.0",
)

# 레이트 리미팅 미들웨어 추가
app.add_middleware(RateLimitMiddleware)

# 에러 핸들러 등록
register_error_handlers(app)

# 모니터링 설정
setup_monitoring(app)

# 라우터 등록
app.include_router(pipeline_router)
app.include_router(ask_router)
app.include_router(qa_router)
app.include_router(ontology_router)
app.include_router(auth_router)
app.include_router(metrics_router)
app.include_router(upload_router)
app.include_router(report_router)

# 스케줄러 설정
scheduler.add_job(
    lambda: subprocess.call(["python", "self_improve.py"]),
    "cron",
    hour=3,
    minute=0,
    id="self_improve",
)

# 백업 작업 등록
register_backup_jobs(scheduler)


@app.get("/status")
async def get_status():
    """시스템 상태 확인 엔드포인트"""
    today = datetime.now().strftime("%Y%m%d")
    self_improve_log = os.path.exists(f"logs/self_improve_{today}.md")

    # Weaviate 헬스 체크
    weaviate_ok = False
    try:
        r = httpx.get(
            f"{os.getenv('WEAVIATE_URL', 'http://localhost:8080')}/v1/.well-known/ready",
            timeout=1,
        )
        weaviate_ok = r.status_code == 200
    except Exception as e:
        print(f"Weaviate health check failed: {e}")

    # Neo4j 헬스 체크
    neo4j_ok = False
    neo4j_url = os.getenv("NEO4J_URL", "bolt://localhost:7687")
    try:
        driver = GraphDatabase.driver(
            neo4j_url,
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASS", "test")),
        )
        with driver.session() as session:
            session.run("RETURN 1")
            neo4j_ok = True
        driver.close()
    except Exception as e:
        print(f"Neo4j health check failed: {e}")

    return {
        "app": "ok",
        "weaviate": "ok" if weaviate_ok else "error",
        "neo4j": "ok" if neo4j_ok else "error",
        "self_improve": "ok" if self_improve_log else "pending",
        "version": "5.0.0",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
