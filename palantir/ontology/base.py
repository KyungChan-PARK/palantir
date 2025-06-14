"""Base classes for the ontology system."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OntologyObject(BaseModel):
    """Base class for all ontology objects."""
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    type: str = Field(...)  # Object type (e.g., "Customer", "Order", "Product")
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class OntologyLink(BaseModel):
    """Represents a relationship between two ontology objects."""
    
    id: UUID = Field(default_factory=uuid4)
    source_id: UUID = Field(...)
    target_id: UUID = Field(...)
    relationship_type: str = Field(...)  # e.g., "OWNS", "CONTAINS", "RELATED_TO"
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class OntologyAction(BaseModel):
    """Represents an action that can be performed on ontology objects."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(...)
    description: Optional[str] = None
    object_types: List[str] = Field(...)  # Object types this action can be applied to
    parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class OntologyFunction(BaseModel):
    """Represents a function that can process ontology objects."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(...)
    description: Optional[str] = None
    input_types: List[str] = Field(...)
    output_type: str = Field(...)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True 