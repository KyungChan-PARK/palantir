_memory_store = {}


def store_to_weaviate(obj: dict) -> None:
    _memory_store[obj.get("job_id")] = obj


def get_data_by_job_id(job_id: str):
    return _memory_store.get(job_id)
