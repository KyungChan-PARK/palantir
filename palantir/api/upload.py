from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import mimetypes
import uuid

from .report import _memory_store

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    content_type = file.content_type
    if not content_type:
        content_type = mimetypes.guess_type(file.filename)[0]
    
    job_id = uuid.uuid4().hex
    entry = {
        "type": content_type.split("/")[0] if content_type else "raw",
        "filename": file.filename,
        "size": file.size,
    }
    _memory_store[job_id] = entry | {"content": (await file.read()).decode("utf-8", "ignore")}
    return {"job_id": job_id, **entry}
