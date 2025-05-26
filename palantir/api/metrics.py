from fastapi import APIRouter, Response
import os

router = APIRouter()

@router.get("/metrics/self_improve")
def metrics_self_improve():
    path = "logs/self_improve_metrics.prom"
    if not os.path.exists(path):
        return Response(status_code=204)
    with open(path) as f:
        return Response(f.read(), media_type="text/plain") 