import os
from datetime import datetime

import psutil
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST

from palantir.core.metrics import get_metrics

router = APIRouter()


@router.get("/metrics")
def metrics():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    business = get_metrics()
    business["last_updated"] = datetime.now().isoformat()
    return {
        "system": {
            "cpu": cpu_percent,
            "cpu_percent": cpu_percent,
            "memory": memory_percent,
            "memory_percent": memory_percent,
            "disk_usage": psutil.disk_usage("/").percent,
        },
        "business": business,
    }


@router.get("/metrics/self_improve")
def self_improve_metrics():
    metrics_file = "logs/self_improve_metrics.prom"
    if not os.path.exists(metrics_file):
        return Response(status_code=204)

    with open(metrics_file, "r") as f:
        content = f.read()
    return Response(content=content, media_type=CONTENT_TYPE_LATEST)
