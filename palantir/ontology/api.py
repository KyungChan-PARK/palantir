"""API endpoints for the ontology system."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .base import OntologyLink, OntologyObject
from .objects import Customer, Order, Product, Payment, Delivery, Event
from .repository import OntologyRepository

router = APIRouter(prefix="/ontology", tags=["ontology"])
repo = OntologyRepository()


class SearchQuery(BaseModel):
    """Search query parameters."""
    
    obj_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


@router.post("/objects/{obj_type}")
async def create_object(obj_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new ontology object."""
    model_map = {
        "Customer": Customer,
        "Order": Order,
        "Product": Product,
        "Payment": Payment,
        "Delivery": Delivery,
        "Event": Event
    }
    
    if obj_type not in model_map:
        raise HTTPException(status_code=400, detail=f"Unknown object type: {obj_type}")
    
    model_cls = model_map[obj_type]
    obj = model_cls(**data)
    repo.add_object(obj)
    
    return obj.dict()


@router.get("/objects/{obj_id}")
async def get_object(obj_id: UUID) -> Dict[str, Any]:
    """Get an object by ID."""
    # Try each model type
    for model_cls in model_map.values():
        obj = repo.get_object(obj_id, model_cls)
        if obj:
            return obj.dict()
    
    raise HTTPException(status_code=404, detail=f"Object not found: {obj_id}")


@router.put("/objects/{obj_id}")
async def update_object(obj_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing object."""
    # Get existing object to determine its type
    existing = await get_object(obj_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Object not found: {obj_id}")
    
    model_cls = model_map[existing["type"]]
    obj = model_cls(**{**data, "id": obj_id})
    repo.update_object(obj)
    
    return obj.dict()


@router.delete("/objects/{obj_id}")
async def delete_object(obj_id: UUID) -> Dict[str, str]:
    """Delete an object."""
    try:
        repo.delete_object(obj_id)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/links")
async def create_link(link: OntologyLink) -> Dict[str, Any]:
    """Create a new relationship between objects."""
    # Verify both objects exist
    source = await get_object(link.source_id)
    target = await get_object(link.target_id)
    
    if not source or not target:
        raise HTTPException(
            status_code=400,
            detail="Both source and target objects must exist"
        )
    
    repo.add_link(link)
    return link.dict()


@router.get("/objects/{obj_id}/links")
async def get_links(
    obj_id: UUID,
    relationship_type: Optional[str] = None,
    direction: str = "out"
) -> List[Dict[str, Any]]:
    """Get relationships for an object."""
    if direction not in ["in", "out"]:
        raise HTTPException(
            status_code=400,
            detail="Direction must be either 'in' or 'out'"
        )
    
    return repo.get_linked_objects(obj_id, relationship_type, direction)


@router.post("/search")
async def search_objects(query: SearchQuery) -> List[Dict[str, Any]]:
    """Search for objects matching criteria."""
    return repo.search_objects(
        obj_type=query.obj_type,
        properties=query.properties
    ) 