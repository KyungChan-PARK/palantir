import io
import json
import tempfile

import fitz  # PyMuPDF
import pandas as pd
import pytesseract
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


async def preprocess_file(filename, mime, content, job_id):
    detect_mime(mime)
    if (
        mime.startswith("text/csv")
        or mime.startswith("application/vnd.ms-excel")
        or filename.endswith((".csv", ".xls", ".xlsx"))
    ):
        df = (
            pd.read_csv(io.BytesIO(content))
            if filename.endswith(".csv")
            else pd.read_excel(io.BytesIO(content), engine="openpyxl")
        )
        return {"type": "table", "data": df.to_dict(), "job_id": job_id}
    elif mime.startswith("application/json") or filename.endswith(".json"):
        data = json.loads(content.decode())
        return {"type": "json", "data": data, "job_id": job_id}
    elif mime.startswith("application/pdf") or filename.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp.flush()
            tmp.seek(0)
            with fitz.open(stream=tmp.read(), filetype="pdf") as doc:
                text = "\n".join(page.get_text() for page in doc)
                try:
                    # OCR (pytesseract) 보조
                    images = []
                    for page in doc:
                        pix = page.get_pixmap()
                        img = Image.frombytes(
                            "RGB", [pix.width, pix.height], pix.samples
                        )
                        images.append(pytesseract.image_to_string(img))
                    ocr_text = "\n".join(images)
                    text += "\n" + ocr_text
                except Exception:
                    pass
            return {"type": "pdf", "text": text, "job_id": job_id}
    elif mime.startswith("image/"):
        img = Image.open(io.BytesIO(content))
        vector = embed_image_clip(img)
        return {"type": "image", "vector": vector, "job_id": job_id}
    elif mime.startswith("application/vnd.openxmlformats-officedocument"):
        df = pd.read_excel(io.BytesIO(content))
        return {"type": "table", "data": df.to_dict(), "job_id": job_id}
    else:
        return {"type": "raw", "data": content, "job_id": job_id}
