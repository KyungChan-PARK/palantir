"""LLM 질의/코드 생성 API 라우터.

쿼리→코드 변환 및 속도 제한, 캐시, 인증 적용.
"""

from fastapi import APIRouter, Depends, Request
from pydantic import (
    BaseModel,
)

from palantir.core.llm_manager import LLMManager
from palantir.core.policy_guard import cache_response, limiter, verify_jwt

router = APIRouter()

def get_llm_manager() -> LLMManager:
    """LLMManager 인스턴스 반환."""
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
) -> dict:
    """LLM 질의 및 코드 생성 엔드포인트.

    Args:
        request: FastAPI 요청 객체
        body: AskRequest (query, mode)
        user: 인증된 사용자
        llm: LLMManager 인스턴스
    Returns:
        dict: 실행 결과 및 생성 코드
    """
    code = llm.generate_code(body.query, body.mode)
    # 실제 DB 실행은 mock
    result = f"[MOCK EXECUTE] {body.mode}: {code}"
    return {"result": result, "code": code}
