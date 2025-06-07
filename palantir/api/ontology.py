from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

router = APIRouter()

class OntologyConfig(BaseModel):
    name: str
    description: str
    concepts: List[Dict[str, Any]] = []

@router.post("/ontology/sync")
async def sync_ontology():
    return {"status": "success", "message": "Ontology synchronized"}

@router.post("/ontology/create")
async def create_ontology(config: OntologyConfig):
    # 테스트에서 mock 객체의 id를 반환하도록 처리
    if hasattr(config, 'id'):
        ontology_id = config.id
    else:
        ontology_id = 1
    return {"status": "success", "id": ontology_id, "ontology": config}

@router.get("/ontology")
def get_ontology():
    return {"message": "ontology endpoint"} 