from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from chromadb import Client
from chromadb.config import Settings

from palantir.services.mcp.llm_mcp import LLMMCP
from models.predict import predict

router = APIRouter()

EMBED_MODEL = "all-MiniLM-L6-v2"
chroma_client = Client(
    Settings(persist_directory="./data/chroma_db", anonymized_telemetry=False)
)
embedding = SentenceTransformerEmbeddings(model_name=EMBED_MODEL)
vectorstore = Chroma(
    client=chroma_client, collection_name="project_docs", embedding_function=embedding
)

llm = LLMMCP()


class QARequest(BaseModel):
    question: str
    features: Optional[Dict] = None


@router.post("/qa")
async def qa(request: QARequest):
    """Vector search + LLM + ML 예측을 통합한 QA 엔드포인트."""
    try:
        answer = llm.retrieval_qa(request.question, vectorstore)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    prediction = None
    if request.features:
        try:
            prediction = predict(request.features)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ML prediction failed: {e}")

    return {"answer": answer, "prediction": prediction}
