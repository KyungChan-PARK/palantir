import os
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from palantir.ontology.repository import (
    OntologyRepository,
)

router = APIRouter()
repo = OntologyRepository()


class OntologyConfig(BaseModel):
    name: str
    description: str
    concepts: List[Dict[str, Any]] = []


@router.post("/ontology/sync")
async def sync_ontology():
    from palantir.core.ontology_sync import sync_ontology_to_neo4j

    sync_ontology_to_neo4j(
        os.getenv("NEO4J_URL", "bolt://localhost:7687"),
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASS", "test"),
    )
    return {"synced": True}
