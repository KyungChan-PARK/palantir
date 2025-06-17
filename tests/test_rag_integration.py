from fastapi.testclient import TestClient
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from chromadb import Client
from chromadb.config import Settings

from main import app
import palantir.api.qa as qa_module


def test_rag_answer_contains_context(tmp_path, monkeypatch):
    client = Client(
        Settings(persist_directory=str(tmp_path), anonymized_telemetry=False)
    )
    embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    store = Chroma(client=client, collection_name="test", embedding_function=embedding)
    store.add_texts(["The capital of France is Paris."], metadatas=[{"id": 1}])

    monkeypatch.setattr(qa_module, "vectorstore", store)

    api = TestClient(app)
    resp = api.post("/qa", json={"question": "What is the capital of France?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "Paris" in data["answer"]
