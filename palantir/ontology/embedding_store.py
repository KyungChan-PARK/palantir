import os
from typing import Any, Dict, List

import chromadb
import weaviate
from chromadb.utils import embedding_functions

from palantir.core.config import settings


class EmbeddingStore:
    """Wrapper around Weaviate with Chroma fallback."""

    def __init__(self) -> None:
        offline = getattr(settings, "OFFLINE_MODE", False)
        self.use_chroma = offline
        if not offline:
            try:
                url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
                self.client = weaviate.Client(url)
                self.class_name = "OntologyNode"
                if not self.client.schema.exists(self.class_name):
                    self.client.schema.create_class({"class": self.class_name})
            except Exception:
                self.use_chroma = True
        if self.use_chroma:
            path = "chroma_data/"
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            client = chromadb.PersistentClient(path=path)
            self.collection = client.create_collection(
                name="ontology", embedding_function=embed_fn
            )

    def add(self, uid: str, text: str, metadata: Dict[str, Any]) -> None:
        if self.use_chroma:
            self.collection.add(documents=[text], metadatas=[metadata], ids=[uid])
        else:
            obj = {**metadata, "text": text}
            self.client.data_object.create(obj, self.class_name, uuid=uid)

    def query(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        if self.use_chroma:
            return self.collection.query(query_texts=[text], n_results=limit)
        result = (
            self.client.query.get(self.class_name, ["text"])
            .with_near_text({"concepts": [text]})
            .with_limit(limit)
            .do()
        )
        return result.get("data", {}).get("Get", {}).get(self.class_name, [])
