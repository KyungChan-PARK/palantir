from fastapi import APIRouter, Response
import os
import psutil
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime

router = APIRouter()


@router.get("/metrics")
def metrics():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    return {
        "system": {
            "cpu": cpu_percent,
            "cpu_percent": cpu_percent,
            "memory": memory_percent,
            "memory_percent": memory_percent,
            "disk_usage": psutil.disk_usage("/").percent,
        },
        "business": {
            "active_users": 0,  # TODO: 실제 사용자 수 추적 구현
            "total_requests": 0,  # TODO: 요청 수 추적 구현
            "success_rate": 100.0,  # TODO: 성공률 추적 구현
            "last_updated": datetime.now().isoformat(),
        },
    }


@router.get("/metrics/self_improve")
def self_improve_metrics():
    metrics_file = "logs/self_improve_metrics.prom"
    if not os.path.exists(metrics_file):
        return Response(status_code=204)

    with open(metrics_file, "r") as f:
        content = f.read()
    return Response(content=content, media_type=CONTENT_TYPE_LATEST)
