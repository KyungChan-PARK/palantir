import yaml
from fastapi import APIRouter, File, UploadFile, HTTPException

from palantir.core.pipeline_schema import PipelineSchema
from palantir.core.pipeline_transpiler import transpile_yaml_to_dag
from palantir.core.scheduler import add_pipeline_job

router = APIRouter()


@router.post("/pipeline/validate")
def validate_pipeline(file: UploadFile = File(...)):
    content = file.file.read()
    try:
        data = yaml.safe_load(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"YAML parsing error: {e}")
    try:
        PipelineSchema(**data)
        return {"valid": True}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.post("/pipeline/submit")
def submit_pipeline(file: UploadFile = File(...)):
    content = file.file.read()
    try:
        data = yaml.safe_load(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"YAML parsing error: {e}")
    try:
        PipelineSchema(**data)
        dag = transpile_yaml_to_dag(data)
        add_pipeline_job(dag)
        return {"submitted": True}
    except Exception as e:
        return {"submitted": False, "error": str(e)}
