from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
import mimetypes

router = APIRouter()

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    content_type = file.content_type
    if not content_type:
        content_type = mimetypes.guess_type(file.filename)[0]
    
    return {
        "type": content_type.split('/')[0] if content_type else "raw",
        "filename": file.filename,
        "size": file.size
    } 