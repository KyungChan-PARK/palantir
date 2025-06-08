from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from palantir.core.auth import get_current_user
from palantir.core.database import SessionLocal, get_db
from palantir.core.models import LLMFeedback
from sqlalchemy.orm import Session
from palantir.core.rag_pipeline import run_rag_qa
import os

class AskRequest(BaseModel):
    query: str
    mode: Optional[str] = "default"

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    feedback: str  # like / dislike

def get_llm_manager():
    return None

router = APIRouter()

@router.get("/ask")
def ask():
    return {"message": "ask endpoint"}

@router.post("/ask")
async def ask_post(request: AskRequest, current_user = Depends(get_current_user)):
    if request.mode == "sql":
        # SQL 모드 처리
        return {"result": "SQL query result"}
    if request.mode == "rag":
        # RAG 모드 처리
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return {"error": "OPENAI_API_KEY 환경변수가 필요합니다."}
        try:
            result = run_rag_qa(
                query=request.query,
                weaviate_url=weaviate_url,
                openai_api_key=openai_api_key,
            )
            return {"result": result["result"], "sources": result.get("source_documents", [])}
        except Exception as e:
            return {"error": str(e)}
    return {"result": "Default query result"}

@router.post("/ask/feedback")
async def ask_feedback(data: FeedbackRequest, db: Session = Depends(get_db)):
    record = LLMFeedback(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"status": "ok", "id": record.id} 