import weaviate.embedded
import os

WEAVIATE_PATH = os.path.join(os.getcwd(), "weaviate_data")

# client = weaviate.embedded.WeaviateEmbedded(persistence_data_path=WEAVIATE_PATH)
client = None  # weaviate-embedded 비활성화 (호환성 문제로 임시 조치)

_memory_store = {}

def store_to_weaviate(job_id, data):
    _memory_store[job_id] = data

def get_data_by_job_id(job_id):
    return _memory_store.get(job_id) 