from typing import List, Dict, Any
from .vector_store import VectorStore
from .ai_integration import call_llm, Message, create_system_message, create_user_message

class RAG:
    def __init__(self):
        """RAG 시스템 초기화"""
        self.vector_store = VectorStore()

    def _format_context(self, matches: List[Dict[str, Any]]) -> str:
        """
        검색 결과를 컨텍스트 문자열로 포맷팅
        
        Args:
            matches: Pinecone 검색 결과
            
        Returns:
            str: 포맷팅된 컨텍스트
        """
        contexts = []
        for i, match in enumerate(matches, 1):
            text = match["metadata"]["text"]
            score = match["score"]
            contexts.append(f"[{i}] (유사도: {score:.2f}) {text}")
        return "\n\n".join(contexts)

    def answer(self, query: str, top_k: int = 3) -> str:
        """
        쿼리에 대한 답변 생성
        
        Args:
            query: 사용자 질문
            top_k: 검색할 문서 수
            
        Returns:
            str: 생성된 답변
        """
        # 관련 문서 검색
        matches = self.vector_store.search(query, top_k=top_k)
        context = self._format_context(matches)
        
        # 프롬프트 구성
        messages = [
            create_system_message("주어진 컨텍스트를 기반으로 질문에 답변하세요. 컨텍스트에 없는 내용은 '정보가 없습니다'라고 답변하세요.").to_dict(),
            create_user_message(f"컨텍스트:\n{context}\n\n질문: {query}").to_dict()
        ]
        
        # LLM으로 답변 생성
        return call_llm(messages)

    def add_document(self, text: str, metadata: Dict[str, Any] = None) -> None:
        """
        문서를 벡터 저장소에 추가
        
        Args:
            text: 문서 텍스트
            metadata: 추가 메타데이터
        """
        from uuid import uuid4
        
        doc_id = str(uuid4())
        vector = self.vector_store.embed(text)
        
        metadata = metadata or {}
        metadata["text"] = text
        
        self.vector_store.upsert(doc_id, vector, metadata) 