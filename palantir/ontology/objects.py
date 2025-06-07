"""Business object definitions for the ontology system."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field

from .base import OntologyObject


class Customer(OntologyObject):
    """Customer object representation."""
    
    type: str = "Customer"
    email: EmailStr
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    customer_since: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def display_name(self) -> str:
        """Get a human-readable display name."""
        return f"{self.name} ({self.email})"


class Product(OntologyObject):
    """Product object representation."""
    
    type: str = "Product"
    name: str
    description: Optional[str] = None
    price: Decimal
    sku: str
    stock: int = 0
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    @property
    def is_in_stock(self) -> bool:
        """Check if the product is available in stock."""
        return self.stock > 0


class Order(OntologyObject):
    """Order object representation."""
    
    type: str = "Order"
    customer_id: UUID
    order_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # pending, processing, shipped, delivered, cancelled
    total_amount: Decimal
    items: List[dict]  # List of {product_id: UUID, quantity: int, price: Decimal}
    shipping_address: str
    tracking_number: Optional[str] = None
    
    @property
    def is_active(self) -> bool:
        """Check if the order is still active."""
        return self.status not in ["delivered", "cancelled"]
    
    def calculate_total(self) -> Decimal:
        """Calculate the total amount of the order."""
        return sum(item["price"] * item["quantity"] for item in self.items) 