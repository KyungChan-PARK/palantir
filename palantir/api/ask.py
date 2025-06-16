from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from palantir.core.auth import get_current_user


class AskRequest(BaseModel):
    query: str
    mode: Optional[str] = "default"


def get_llm_manager():
    return None


router = APIRouter()


@router.get("/ask")
def ask():
    return {"message": "ask endpoint"}


@router.post("/ask")
async def ask_post(request: AskRequest, current_user=Depends(get_current_user)):
    if request.mode == "sql":
        # SQL 모드 처리
        return {"result": "SQL query result"}
    return {"result": "Default query result"}
