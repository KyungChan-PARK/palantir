"""Business object definitions for the ontology system."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

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

    def recommend_products(self, orders: list, products: list) -> list:
        """고객의 주문 이력 기반으로 추천 상품 리스트 반환 (유사도 기반 예시)"""
        purchased = set()
        for order in orders:
            if order.customer_id == self.id:
                for item in order.items:
                    purchased.add(item["product_id"])
        # 단순: 구매하지 않은 상품 중 카테고리/태그가 겹치는 상품 추천
        recommendations = []
        for p in products:
            if p.id not in purchased:
                # 태그/카테고리 유사도 예시
                if (
                    hasattr(p, "category")
                    and p.category
                    and any(
                        hasattr(o, "category") and o.category == p.category
                        for o in products
                        if o.id in purchased
                    )
                ):
                    recommendations.append(p)
        return recommendations


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

    def similar_products(self, products: list) -> list:
        """유사 카테고리/태그 기반 유사 상품 추천"""
        sims = []
        for p in products:
            if p.id != self.id:
                score = 0
                if self.category and p.category == self.category:
                    score += 1
                score += len(set(self.tags) & set(p.tags))
                if score > 0:
                    sims.append((p, score))
        sims.sort(key=lambda x: -x[1])
        return [p for p, _ in sims]


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

    def link_payment(self, payment) -> bool:
        """주문-결제 연결 유효성 체크"""
        return (
            payment
            and self.total_amount == payment.amount
            and self.status != "cancelled"
            and payment.order_id == self.id
        )

    def link_delivery(self, delivery) -> bool:
        """주문-배송 연결 유효성 체크"""
        return (
            delivery
            and delivery.order_id == self.id
            and self.status in ["shipped", "delivered"]
        )

    def related_events(self, events: list) -> list:
        """이 주문과 관련된 이벤트 리스트 반환"""
        return [e for e in events if e.related_id == self.id]


class Payment(BaseModel):
    """Payment object representation."""

    id: str
    order_id: str
    amount: float
    method: str
    status: str
    timestamp: datetime

    @validator("amount")
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("결제 금액은 0보다 커야 합니다.")
        return v

    def is_valid(self) -> bool:
        try:
            self.amount_positive(self.amount)
            return True
        except Exception:
            return False

    def is_valid_for_order(self, order) -> bool:
        """결제-주문 연결 유효성 체크"""
        return self.order_id == order.id and self.amount == order.total_amount


class Delivery(BaseModel):
    """Delivery object representation."""

    id: str
    order_id: str
    address: str
    status: str
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]

    def is_delivered(self) -> bool:
        return self.status == "delivered" and self.delivered_at is not None

    def is_valid_for_order(self, order) -> bool:
        """배송-주문 연결 유효성 체크"""
        return self.order_id == order.id


class Event(BaseModel):
    """Event object representation (e.g. order status change, payment, delivery, etc.)"""

    id: str
    type: str
    related_id: str
    timestamp: datetime
    description: Optional[str] = None

    def is_recent(self, days: int = 7) -> bool:
        return (datetime.now() - self.timestamp).days <= days

    @staticmethod
    def filter_events(
        events: list, event_type: str = None, related_id: UUID = None
    ) -> list:
        """이벤트 타입/연관 객체 기준 필터링"""
        return [
            e
            for e in events
            if (not event_type or e.type == event_type)
            and (not related_id or e.related_id == related_id)
        ]

    @staticmethod
    def timeline(events: list) -> list:
        """이벤트 타임라인(시간순 정렬)"""
        return sorted(events, key=lambda e: e.timestamp)


# 관계/유효성 메서드 예시 (Order와 Payment/Delivery 연결)
def link_order_payment(order: Order, payment: Payment) -> bool:
    return (
        order
        and payment
        and order.total_amount == payment.amount
        and order.status != "cancelled"
    )


def link_order_delivery(order: Order, delivery: Delivery) -> bool:
    return (
        order
        and delivery
        and order.status in ["shipped", "delivered"]
        and delivery.order_id == order.customer_id
    )


# 관계/유효성/이벤트 자동화 함수 예시
def link_payment_delivery(payment: Payment, delivery: Delivery) -> dict:
    if payment.order_id == delivery.order_id:
        return {
            "relation": "order-payment-delivery",
            "order_id": payment.order_id,
            "payment_id": payment.id,
            "delivery_id": delivery.id,
        }
    return {"relation": None}


def validate_event(event: Event) -> bool:
    return event.is_recent(30)
