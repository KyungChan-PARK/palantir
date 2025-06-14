import io
import json
import sys
import types
from typing import Union, BinaryIO

import pandas as pd
from fastapi import HTTPException

from .clip_embed import embed_image_clip

sys.modules.setdefault("fitz", types.ModuleType("fitz"))


class Image:
    @staticmethod
    def open(buf):
        return buf


pytesseract = None


def detect_mime(mime_type: str) -> str:
    """MIME 타입을 기반으로 파일 형식을 감지합니다."""
    mime_map = {
        "text/csv": "csv",
        "application/json": "json",
        "application/x-json": "json",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
        "application/pdf": "pdf",
    }
    return mime_map.get(mime_type, "raw")


def handle_csv(data: Union[bytes, BinaryIO]) -> pd.DataFrame:
    """CSV 데이터를 처리하여 DataFrame으로 변환합니다."""
    if isinstance(data, bytes):
        data = io.BytesIO(data)
    return pd.read_csv(data)


def handle_json(data: Union[bytes, BinaryIO]) -> pd.DataFrame:
    """JSON 데이터를 처리하여 DataFrame으로 변환합니다."""
    if isinstance(data, bytes):
        data = io.BytesIO(data)
    json_data = json.load(data)
    if isinstance(json_data, dict):
        return pd.DataFrame([json_data])
    return pd.DataFrame(json_data)


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
