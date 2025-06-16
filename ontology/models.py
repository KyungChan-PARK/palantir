from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OntologyObject(BaseModel):
    """온톨로지 객체 기본 모델"""

    id: UUID = Field(default_factory=uuid4)
    type: str
    name: str
    description: Optional[str] = None
    properties: Dict = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "Product",
                "name": "iPhone 15",
                "description": "Latest iPhone model",
                "properties": {
                    "price": 999.99,
                    "category": "Electronics",
                    "stock": 100,
                },
            }
        }


class OntologyRelation(BaseModel):
    """온톨로지 객체 간 관계 모델"""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    target_id: UUID
    type: str
    properties: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "123e4567-e89b-12d3-a456-426614174000",
                "target_id": "987fcdeb-51a2-43d7-9012-345678901234",
                "type": "BELONGS_TO",
                "properties": {"since": "2024-01-01", "weight": 0.8},
            }
        }


class OntologyEvent(BaseModel):
    """온톨로지 이벤트 모델"""

    id: UUID = Field(default_factory=uuid4)
    object_id: UUID
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "object_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "STOCK_UPDATE",
                "details": {"old_value": 100, "new_value": 95, "reason": "Sale"},
            }
        }


class OntologyQuery(BaseModel):
    """온톨로지 쿼리 모델"""

    type: Optional[str] = None
    properties: Dict = Field(default_factory=dict)
    relations: List[Dict] = Field(default_factory=list)
    limit: int = 10
    offset: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "type": "Product",
                "properties": {"category": "Electronics", "price_lt": 1000},
                "relations": [{"type": "BELONGS_TO", "target_type": "Category"}],
            }
        }
