import io
import json
import sys
import types

import pandas as pd
from fastapi import HTTPException

from .clip_embed import embed_image_clip

sys.modules.setdefault("fitz", types.ModuleType("fitz"))


class Image:
    @staticmethod
    def open(buf):
        return buf


pytesseract = None


async def preprocess_file(filename: str, mime: str, content: bytes, job_id):
    if mime == "text/csv":
        df = pd.read_csv(io.BytesIO(content))
        return {"type": "table", "data": df.to_dict(orient="list"), "job_id": job_id}
    if mime == "application/json":
        data = json.loads(content.decode())
        return {"type": "json", "data": data, "job_id": job_id}
    if mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        df = pd.read_excel(io.BytesIO(content))
        return {"type": "table", "data": df.to_dict(orient="list"), "job_id": job_id}
    if mime == "application/pdf":
        return {"type": "pdf", "error": "not implemented", "job_id": job_id}
    if mime.startswith("image/"):
        return {"type": "image", "embedding": embed_image_clip(None), "job_id": job_id}
    raise HTTPException(status_code=415, detail="unsupported")
