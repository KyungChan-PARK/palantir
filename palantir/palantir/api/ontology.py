from fastapi import APIRouter

from palantir.core.ontology_sync import sync_ontology_to_neo4j

router = APIRouter()

@router.post("/ontology/sync")
def ontology_sync():
    # 실제 환경에서는 환경변수/시크릿에서 정보 주입
    sync_ontology_to_neo4j(
        neo4j_url="bolt://localhost:7687",
        user="neo4j",
        password="test",
        ontology_dir="ontology/",
    )
    return {"synced": True}
