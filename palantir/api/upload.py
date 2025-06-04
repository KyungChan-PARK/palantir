"""파일 업로드 및 전처리 API 라우터.

업로드 파일의 MIME 타입을 검사하고, 전처리 후 저장한다.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from palantir.core.preprocessor_factory import preprocess_file
from palantir.core.weaviate_store import _memory_store, store_to_weaviate

router = APIRouter()

ALLOWED_MIME = [
    "text/plain",
    "text/csv",
    "application/json",
    "application/pdf",
    "image/",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

def allowed_mime(mime: Optional[str]) -> bool:
    """허용된 MIME 타입인지 검사.

    Args:
        mime: Content-Type 문자열
    Returns:
        bool: 허용 여부
    """
    if not mime:
        return False
    # Word/PPT는 명시적으로 거부
    if (
        mime.startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        or mime.startswith("application/vnd.openxmlformats-officedocument.presentationml.presentation")
    ):
        return False
    return any(mime.startswith(m) for m in ALLOWED_MIME)

@router.post("/upload")
async def upload(file: UploadFile = File(...)) -> JSONResponse:
    """파일 업로드 엔드포인트.

    Args:
        file: 업로드 파일
    Returns:
        JSONResponse: 처리 결과(job_id)
    """
    if not file.content_type or not allowed_mime(file.content_type):
        raise HTTPException(status_code=415, detail="unsupported media type")
    job_id = str(uuid.uuid4())
    content = await file.read()
    result = await preprocess_file(file.filename, file.content_type, content, job_id)
    # 업로드 직후 반드시 메모리/Weaviate에 저장
    _memory_store[job_id] = result
    store_to_weaviate(result)
    if result.get("type") == "error":
        return JSONResponse(status_code=400, content=result)
    return JSONResponse(content={"job_id": job_id, **({"type": result.get("type")} if "type" in result else {})})
