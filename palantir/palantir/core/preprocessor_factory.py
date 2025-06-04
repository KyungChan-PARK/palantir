"""파일 업로드 전처리 및 MIME별 파서 모듈.

각 파일 유형별로 데이터 추출 및 예외처리를 담당한다.
"""
import io
import json
import tempfile
from typing import Any, Dict

import fitz  # PyMuPDF
import pandas as pd
import pytesseract
from fastapi import HTTPException
from PIL import Image

from palantir.core.clip_embed import embed_image_clip

# ---------- Added by auto-patch ----------
_MIME_MAP = {
    "text/csv": "csv",
    "application/json": "json",
    "application/vnd.ms-excel": "excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "application/pdf": "pdf",
}


def detect_mime(content_type: str) -> str:
    """Return short token for known MIME. Raise ValueError otherwise."""
    if content_type in _MIME_MAP:
        return _MIME_MAP[content_type]
    return "raw"


def handle_csv(buffer):
    df = pd.read_csv(
        io.BytesIO(buffer) if isinstance(buffer, (bytes, bytearray)) else buffer
    )
    return df


def handle_json(buffer):
    data = (
        json.load(io.TextIOWrapper(io.BytesIO(buffer)))
        if isinstance(buffer, (bytes, bytearray))
        else json.load(buffer)
    )
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.json_normalize(data)


# ---------- auto-patch end ----------

ALLOWED_MIME = [
    "text/plain",
    "text/csv",
    "application/json",
    "application/pdf",
    "image/",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

def parse_text_plain(content: bytes) -> str:
    """text/plain 파일을 UTF-8로 디코딩."""
    return content.decode("utf-8", 'ignore')

def parse_csv(content: bytes) -> pd.DataFrame:
    """CSV 파일을 DataFrame으로 파싱."""
    return pd.read_csv(io.BytesIO(content))

def parse_json(content: bytes) -> Any:
    """JSON 파일을 파싱."""
    return json.loads(content.decode())

def parse_pdf(content: bytes) -> str:
    """PDF 파일에서 텍스트 및 OCR 추출."""
    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp.flush()
        tmp.seek(0)
        with fitz.open(stream=tmp.read(), filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc)
            try:
                images = []
                for page in doc:
                    pix = page.get_pixmap()
                    img = Image.frombytes(
                        "RGB", [pix.width, pix.height], pix.samples
                    )
                    images.append(pytesseract.image_to_string(img))
                ocr_text = "\n".join(images)
                text += "\n" + ocr_text
            except (ValueError, OSError):
                # OCR 실패는 무시
                pass
        if len(text.strip()) == 0:
            text = "텍스트 추출 실패 (OCR 불가)"
        return text

def parse_image(content: bytes) -> Dict[str, Any]:
    """이미지 파일에서 벡터 및 원본 바이트 추출."""
    img = Image.open(io.BytesIO(content))
    vector = embed_image_clip(img)
    return {"vector": vector, "content": content}

def parse_xlsx(content: bytes) -> pd.DataFrame:
    """OpenXML Excel(xlsx) 파일을 DataFrame으로 파싱."""
    return pd.read_excel(io.BytesIO(content), engine="openpyxl")

MIME_HANDLERS = {
    "text/plain": parse_text_plain,
    "text/csv": parse_csv,
    "application/json": parse_json,
    "application/pdf": None,  # 별도 분기
    "image/": parse_image,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": parse_xlsx,
}

async def preprocess_file(
    filename: str, mime: str, content: bytes, job_id: str
) -> dict:
    """업로드 파일을 MIME별로 파싱하여 표준 dict 또는 오류 메시지 반환."""
    # FastAPI/StackOverflow: https://fastapi.tiangolo.com/tutorial/handling-errors/
    # https://github.com/fastapi/fastapi/discussions/6680
    # 1. 미지원 MIME은 415
    if not any(mime.startswith(k) for k in MIME_HANDLERS):
        raise HTTPException(status_code=415, detail="unsupported media type")
    try:
        # 2. PDF는 별도 분기 (파싱 실패해도 type: pdf)
        if mime.startswith("application/pdf") or filename.endswith(".pdf"):
            try:
                text = parse_pdf(content)
                return {"type": "pdf", "text": text, "job_id": job_id}
            except Exception as exc:
                return {"type": "pdf", "error": str(exc), "job_id": job_id}
        # 3. 나머지 핸들러 매핑
        for k, handler in MIME_HANDLERS.items():
            if mime.startswith(k):
                if handler is None:
                    break
                data = handler(content)
                if k == "text/csv" or k == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                    return {"type": "table", "data": data.to_dict(), "job_id": job_id}
                if k == "image/":
                    return {"type": "image", **data, "job_id": job_id}
                if k == "application/json":
                    return {"type": "json", "data": data, "job_id": job_id}
                if k == "text/plain":
                    return {"type": "text", "data": data, "job_id": job_id}
        # 4. Word/PPT 등 명시적 거부
        if (
            mime.startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            or filename.endswith(".docx")
            or mime.startswith("application/vnd.openxmlformats-officedocument.presentationml.presentation")
            or filename.endswith(".pptx")
        ):
            raise HTTPException(status_code=415, detail="unsupported file type")
        # 5. 기타(알 수 없는 MIME)
        return {"type": "raw", "data": content, "job_id": job_id}
    except (ValueError, OSError, KeyError, pd.errors.ParserError) as exc:
        return {"type": "error", "message": str(exc), "job_id": job_id}
