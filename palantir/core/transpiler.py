from typing import Dict, Any
from .config import settings
import logging
logger = logging.getLogger(__name__)

def transpile_yaml_to_dag(yaml_dict: Dict[str, Any]):
    # 실제로는 DAG 객체를 생성해야 함. 여기선 예시로 dict 반환
    if getattr(settings, "OFFLINE_MODE", False) and getattr(settings, "LLM_PROVIDER", "openai").lower() == "openai":
        logger.warning("OpenAI API 호출이 오프라인 모드에서 건너뛰어졌습니다.")
        return "OpenAI 기능은 오프라인 모드에서 비활성화되었습니다." # 또는 적절한 모의 응답/예외 처리
    return {
        "dag_name": yaml_dict.get("name"),
        "tasks": yaml_dict.get("tasks", []),
    } 