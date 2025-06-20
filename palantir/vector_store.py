import os
from typing import List, Dict, Any
import pinecone
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt

class VectorStore:
    def __init__(self):
        """Pinecone 벡터 저장소 초기화"""
        pinecone.init(
            api_key=os.environ["PINECONE_API_KEY"],
            environment=os.environ["PINECONE_ENV"]
        )
        self.index_name = os.environ["PINECONE_INDEX"]
        self.index = pinecone.Index(self.index_name)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(3))
    def embed(self, text: str) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            List[float]: 1536차원 임베딩 벡터
        """
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input=text
        )
        return response["data"][0]["embedding"]

    def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        """
        벡터와 메타데이터를 저장소에 업서트
        
        Args:
            id: 문서 ID
            vector: 임베딩 벡터
            metadata: 문서 메타데이터
        """
        self.index.upsert([(id, vector, metadata)])

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        쿼리와 가장 유사한 문서 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            
        Returns:
            List[Dict]: 검색 결과 목록
        """
        query_vector = self.embed(query)
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        return results["matches"]

    def delete(self, ids: List[str]) -> None:
        """
        지정된 ID의 문서들을 삭제
        
        Args:
            ids: 삭제할 문서 ID 목록
        """
        self.index.delete(ids) 