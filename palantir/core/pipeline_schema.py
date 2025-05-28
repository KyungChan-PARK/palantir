from typing import Any, Dict, List

from pydantic import BaseModel


class Task(BaseModel):
    id: str
    type: str
    params: Dict[str, Any]
    depends_on: List[str] = []


class PipelineSchema(BaseModel):
    name: str
    description: str = ""
    tasks: List[Task]
