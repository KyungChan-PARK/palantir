from typing import Any, Dict
from langchain.vectorstores import Weaviate
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA


def get_rag_qa_chain(
    weaviate_url: str,
    openai_api_key: str,
    llm_model: str = "gpt-4-turbo-preview",
    temperature: float = 0.2,
    top_k: int = 5,
) -> RetrievalQA:
    """
    Weaviate + LLM 기반 RetrievalQA 체인 생성
    """
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vector_store = Weaviate(
        url=weaviate_url,
        embedding=embeddings,
        by_text=True,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    llm = ChatOpenAI(model_name=llm_model, temperature=temperature, openai_api_key=openai_api_key)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
    return qa_chain


def run_rag_qa(
    query: str,
    weaviate_url: str,
    openai_api_key: str,
    llm_model: str = "gpt-4-turbo-preview",
    temperature: float = 0.2,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    자연어 쿼리를 받아 RAG QA 결과 반환
    """
    chain = get_rag_qa_chain(
        weaviate_url=weaviate_url,
        openai_api_key=openai_api_key,
        llm_model=llm_model,
        temperature=temperature,
        top_k=top_k,
    )
    result = chain({"query": query})
    return result 