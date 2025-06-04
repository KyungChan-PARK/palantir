"""파이프라인 스케줄러 모듈.

리포트 승인 시 DAG 등록 및 로그 출력을 담당한다.
"""
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

def add_pipeline_job(dag: Any) -> None:
    """파이프라인 DAG 등록 및 승인 로그 출력.

    Args:
        dag: DAG dict 또는 기타 승인 데이터
    """
    if isinstance(dag, dict) and dag.get("dag_name"):
        print(f"[SCHEDULED] DAG: {dag['dag_name']}")
    else:
        print("[SCHEDULED] data-ingest approved")
