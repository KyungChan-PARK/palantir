"""임시 메모리 기반 Weaviate 데이터 저장/조회 모듈.

job_id별 데이터 저장 및 조회를 담당한다. (weaviate-embedded 미사용)
"""

import os
from typing import Any, Dict, Optional

WEAVIATE_PATH = os.path.join(os.getcwd(), "weaviate_data")

# client = weaviate.embedded.WeaviateEmbedded(persistence_data_path=WEAVIATE_PATH)
client = None  # weaviate-embedded 비활성화 (호환성 문제로 임시 조치)

_memory_store: Dict[str, Any] = {}


def store_to_weaviate(obj: dict) -> None:
    """Weaviate에 데이터 저장. 환경변수 없으면 noop."""
    if not os.getenv("WEAVIATE_ENDPOINT"):
        return
    import weaviate

    client = weaviate.Client(os.getenv("WEAVIATE_ENDPOINT"))
    client.batch.add_data_object(obj, class_name="Upload")


def get_data_by_job_id(job_id: str) -> Optional[Any]:
    """job_id로 데이터 조회.

    Args:
        job_id: 작업 식별자
    Returns:
        Optional[Any]: 저장된 데이터 또는 None
    """
    return _memory_store.get(job_id)
