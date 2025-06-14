from .config import settings


def transpile_yaml_to_dag(d: dict):
    if getattr(settings, "OFFLINE_MODE", False):
        return "비활성화 상태"
    return {"dag_name": d.get("name"), "tasks": d.get("tasks")}
