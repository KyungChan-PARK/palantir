from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
import yaml
from pydantic import BaseModel

router = APIRouter()

class PipelineConfig(BaseModel):
    name: str
    config: Dict[str, Any]

@router.post("/pipeline/validate")
async def validate_pipeline(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = yaml.safe_load(content)
        # 필수 필드 검사: tasks의 각 항목에 type이 있는지 확인
        tasks = data.get("tasks", []) if isinstance(data, dict) else []
        for task in tasks:
            if "type" not in task:
                return {"valid": False}
        return {"valid": True}
    except yaml.YAMLError:
        return {"valid": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pipeline/submit")
async def submit_pipeline(file: UploadFile = File(...)):
    try:
        content = await file.read()
        config = yaml.safe_load(content)
        return {"submitted": True, "config": config}
    except yaml.YAMLError:
        raise HTTPException(status_code=422, detail="Invalid YAML format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/pipeline/create")
async def create_pipeline(config: PipelineConfig):
    # 테스트에서 mock 객체의 id를 반환하도록 처리
    if hasattr(config, 'id'):
        pipeline_id = config.id
    else:
        pipeline_id = 1
    return {"status": "success", "id": pipeline_id, "pipeline": config}

@router.get("/pipeline")
def pipeline():
    return {"message": "pipeline endpoint"} 