from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..rag import RAG

router = APIRouter(prefix="/ai", tags=["AI"])
rag = RAG()

class Query(BaseModel):
    text: str
    top_k: Optional[int] = 3

class Document(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None

class Answer(BaseModel):
    answer: str

@router.post("/answer", response_model=Answer)
async def get_answer(query: Query) -> Answer:
    """
    RAG 시스템을 사용하여 질문에 답변
    
    Args:
        query: 질문 텍스트와 검색할 문서 수
        
    Returns:
        Answer: 생성된 답변
    """
    try:
        answer_text = rag.answer(query.text, query.top_k)
        return Answer(answer=answer_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents")
async def add_document(document: Document) -> Dict[str, str]:
    """
    새 문서를 RAG 시스템에 추가
    
    Args:
        document: 문서 텍스트와 메타데이터
        
    Returns:
        Dict: 성공 메시지
    """
    try:
        rag.add_document(document.text, document.metadata)
        return {"message": "문서가 성공적으로 추가되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 