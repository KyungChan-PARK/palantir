import os
from typing import Optional


class LLMMCP:
    """여러 LLM을 일관된 방식으로 호출하는 MCP 계층"""

    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider = provider
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.api_key = os.getenv("OPENAI_API_KEY")
        # TODO: provider별 클라이언트 초기화(OpenAI, Azure, 로컬 등)

    def generate(
        self, prompt: str, system_message: Optional[str] = None, **kwargs
    ) -> str:
        """프롬프트를 LLM에 전달하고 응답을 반환한다."""
        if self.provider == "openai":
            try:
                import openai
            except ImportError:
                return "[LLM 오류] openai 패키지가 설치되어 있지 않습니다. pip install openai 필요"
            try:
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    api_key=self.api_key,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 512),
                )
                # 다양한 응답 형태에 대응
                if isinstance(response, dict):
                    return response["choices"][0]["message"]["content"]
                elif hasattr(response, "choices"):
                    return response.choices[0].message.content
                return str(response)
            except Exception as e:
                return f"[LLM 오류] {str(e)}"
        # TODO: Azure/로컬 등 확장
        return "(LLM 응답 예시)"

    def retrieval_qa(self, question: str, vectorstore) -> str:
        """주어진 벡터스토어에서 컨텍스트를 검색해 답변을 생성한다."""
        from langchain.vectorstores.base import VectorStore

        if not isinstance(vectorstore, VectorStore):
            raise TypeError("vectorstore must be a langchain VectorStore")

        docs = vectorstore.similarity_search(question, k=3)
        context = "\n\n".join([d.page_content for d in docs])
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        return self.generate(prompt)
