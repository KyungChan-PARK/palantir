from typing import Dict, Any

def transpile_yaml_to_dag(yaml_dict: Dict[str, Any]):
    # 실제로는 DAG 객체를 생성해야 함. 여기선 예시로 dict 반환
    return {
        "dag_name": yaml_dict.get("name"),
        "tasks": yaml_dict.get("tasks", []),
    } 