from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from palantir.core.auth import get_current_user
from palantir.core.database import SessionLocal, get_db
from palantir.core.models import LLMFeedback
from sqlalchemy.orm import Session

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
    return {"result": "Default query result"}

@router.post("/ask/feedback")
async def ask_feedback(data: FeedbackRequest, db: Session = Depends(get_db)):
    record = LLMFeedback(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"status": "ok", "id": record.id} 