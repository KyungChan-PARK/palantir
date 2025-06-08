from fastapi import APIRouter
import os
import json

router = APIRouter()

COMPONENTS_JSON = os.path.join(os.path.dirname(__file__), "../sdk/components/components.json")

@router.get("/registry/components")
def get_components():
    if not os.path.exists(COMPONENTS_JSON):
        return []
    with open(COMPONENTS_JSON, encoding="utf-8") as f:
        return json.load(f) 