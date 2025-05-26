from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ConfigDict
from typing import List, Dict, Any


class Task(BaseModel):
    id: str
    type: str
    params: Dict[str, Any]
    depends_on: List[str] = []


class PipelineSchema(BaseModel):
    name: str
    description: str = ""
    tasks: List[Task]
