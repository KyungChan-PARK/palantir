from fastapi import APIRouter
import psutil
import platform
import os
from datetime import datetime

router = APIRouter()

@router.get("/status")
def status():
    return {
        "status": "ok",
        "version": "5.0.0",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    } 