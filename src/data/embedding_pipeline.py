import os
import glob
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class EmbeddingPipeline:
    def __init__(self, db_path: str = "./data/chroma_db"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.Client(Settings(
            persist_directory=db_path,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection("project_docs")

    def embed_files(self, file_patterns: List[str]) -> List[Dict]:
        """지정된 파일 패턴의 모든 파일을 임베딩하여 ChromaDB에 저장"""
        docs = []
        for pattern in file_patterns:
            for file_path in glob.glob(pattern, recursive=True):
                if not os.path.isfile(file_path):
                    continue
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                embedding = self.model.encode(content)
                doc_id = os.path.relpath(file_path)
                self.collection.upsert(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[{"file": doc_id}]
                )
                docs.append({"file": doc_id, "len": len(content)})
        self.client.persist()
        return docs

    def query(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """쿼리 텍스트와 가장 유사한 문서/코드 top_k개 반환"""
        query_emb = self.model.encode(query_text)
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k
        )
        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "file": results["metadatas"][0][i]["file"],
                "content": results["documents"][0][i],
                "score": results["distances"][0][i]
            })
        return hits

if __name__ == "__main__":
    # 예시: src/ 및 docs/ 내 모든 .py, .md 파일 임베딩
    pipe = EmbeddingPipeline()
    indexed = pipe.embed_files(["src/**/*.py", "docs/**/*.md", "README.md"])
    print(f"임베딩 완료: {indexed}")
    # 예시 쿼리
    results = pipe.query("코드 자동화 루프")
    print("쿼리 결과:", results) 