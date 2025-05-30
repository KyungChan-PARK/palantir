"""파이프라인 YAML 검증/등록 API 라우터.

YAML 파싱, 스키마 검증, DAG 변환 및 등록을 담당한다.
"""
import yaml
from fastapi import APIRouter, File, UploadFile, HTTPException

from palantir.core.pipeline_schema import PipelineSchema
from palantir.core.pipeline_transpiler import transpile_yaml_to_dag
from palantir.core.scheduler import add_pipeline_job

router = APIRouter()


@router.post("/pipeline/validate")
def validate_pipeline(file: UploadFile = File(...)) -> dict:
    """파이프라인 YAML 유효성 검증 엔드포인트.

    Args:
        file: 업로드된 YAML 파일
    Returns:
        dict: 유효성 결과
    """
    content = file.file.read()
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=400, detail=f"YAML parsing error: {exc}") from exc
    try:
        PipelineSchema(**data)
        return {"valid": True}
    except Exception as exc:
        return {"valid": False, "error": str(exc)}


@router.post("/pipeline/submit")
def submit_pipeline(file: UploadFile = File(...)) -> dict:
    """파이프라인 등록 엔드포인트.

    Args:
        file: 업로드된 YAML 파일
    Returns:
        dict: 등록 결과
    """
    content = file.file.read()
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=400, detail=f"YAML parsing error: {exc}") from exc
    try:
        PipelineSchema(**data)
        dag = transpile_yaml_to_dag(data)
        add_pipeline_job(dag)
        return {"submitted": True}
    except Exception as exc:
        return {"submitted": False, "error": str(exc)}
