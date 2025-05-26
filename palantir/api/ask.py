from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ConfigDict
from palantir.core.llm_manager import LLMManager
from palantir.core.policy_guard import verify_jwt, limiter, cache_response
from slowapi.util import get_remote_address

router = APIRouter()
llm = LLMManager()

class AskRequest(BaseModel):
    query: str
    mode: str = "sql"  # sql | pyspark

@router.post("/ask")
@limiter.limit("5/minute")
@cache_response
async def ask_endpoint(request: Request, body: AskRequest, user=Depends(verify_jwt)):
    code = llm.generate_code(body.query, body.mode)
    # 실제 DB 실행은 mock
    result = f"[MOCK EXECUTE] {body.mode}: {code}"
    return {"result": result, "code": code} 