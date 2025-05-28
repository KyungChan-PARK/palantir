import uuid

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from palantir.core.preprocessor_factory import preprocess_file
from palantir.core.weaviate_store import store_to_weaviate

router = APIRouter()

ALLOWED_MIME = [
    "text/csv",
    "application/vnd.ms-excel",
    "application/json",
    "application/pdf",
    "image/",
    "application/vnd.openxmlformats-officedocument",
]


def allowed_mime(mime):
    if not mime:
        return False
    return any(mime.startswith(m) for m in ALLOWED_MIME)


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.content_type or not allowed_mime(file.content_type):
        return JSONResponse(
            status_code=400, content={"error": "Invalid or missing content_type"}
        )
    job_id = str(uuid.uuid4())
    content = await file.read()
    result = await preprocess_file(file.filename, file.content_type, content, job_id)
    store_to_weaviate(job_id, result)
    return {"job_id": job_id}
