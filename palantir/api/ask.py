from fastapi import APIRouter, Depends, Request
from typing import Annotated
from pydantic import (
    BaseModel,
)

from palantir.core.llm_manager import LLMManager
from palantir.core.policy_guard import cache_response, limiter, verify_jwt

router = APIRouter()

def get_llm_manager() -> LLMManager:
    return LLMManager()

class AskRequest(BaseModel):
    query: str
    mode: str = "sql"  # sql | pyspark

@router.post("/ask")
@limiter.limit("5/minute")
@cache_response
async def ask_endpoint(
    request: Request,
    body: AskRequest,
    user=Depends(verify_jwt),
    llm=Depends(get_llm_manager)
):
    code = llm.generate_code(body.query, body.mode)
    # 실제 DB 실행은 mock
    result = f"[MOCK EXECUTE] {body.mode}: {code}"
    return {"result": result, "code": code}
