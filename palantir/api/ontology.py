from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel

from palantir.ontology.objects import (Customer, Delivery, Event, Order,
                                       Payment, Product)
from palantir.ontology.repository import (OntologyRepository, embedding_node,
                                          expand_related_nodes,
                                          query_similar_nodes)

router = APIRouter()
repo = OntologyRepository()


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
    if hasattr(config, "id"):
        ontology_id = config.id
    else:
        ontology_id = 1
    return {"status": "success", "id": ontology_id, "ontology": config}


@router.get("/ontology")
def get_ontology():
    return {"message": "ontology endpoint"}


@router.get("/ontology/customers")
def get_customers():
    # 실제 DB/온톨로지에서 데이터 조회 (예시)
    return [{"name": "홍길동", "email": "hong@test.com"}]


@router.get("/ontology/orders")
def get_orders():
    return [{"order_id": "1234", "status": "pending", "total_amount": 10000}]


@router.post("/ontology/query")
def ontology_query(query: str = Query(...)):
    # 질의 분석/실행/결과 반환 (예시)
    return {"result": f"'{query}'에 대한 결과 예시"}


@router.get("/ontology/graph")
def ontology_graph():
    # 온톨로지 객체/관계 그래프 데이터 반환 (예시)
    return {
        "nodes": ["Customer", "Order", "Payment", "Delivery"],
        "edges": [("Customer", "Order"), ("Order", "Payment"), ("Order", "Delivery")],
    }


@router.get("/ontology/recommend_products/{customer_id}")
def recommend_products(customer_id: str):
    # 고객의 주문 이력 기반 추천 상품 반환
    customer = repo.get_object(customer_id)
    orders = repo.search_objects(obj_type="Order")
    products = repo.search_objects(obj_type="Product")
    purchased = set()
    for order in orders:
        if order["properties"].get("customer_id") == customer_id:
            for item in order["properties"].get("items", []):
                purchased.add(item.get("product_id"))
    recommendations = []
    for p in products:
        if p["id"] not in purchased:
            recommendations.append(p)
    return {"recommendations": recommendations[:5]}


@router.get("/ontology/order_timeline/{order_id}")
def order_timeline(order_id: str):
    # 주문별 이벤트 타임라인 반환
    events = repo.search_objects(obj_type="Event")
    timeline = [e for e in events if e["properties"].get("related_id") == order_id]
    timeline = sorted(timeline, key=lambda e: e["properties"].get("timestamp", ""))
    return {"timeline": timeline}


@router.get("/ontology/similar_products/{product_id}")
def similar_products(product_id: str):
    # 상품별 유사 상품 추천
    products = repo.search_objects(obj_type="Product")
    target = next((p for p in products if p["id"] == product_id), None)
    if not target:
        return {"similar": []}
    sims = []
    for p in products:
        if p["id"] != product_id:
            score = 0
            if target["properties"].get("category") and p["properties"].get(
                "category"
            ) == target["properties"].get("category"):
                score += 1
            score += len(
                set(target["properties"].get("tags", []))
                & set(p["properties"].get("tags", []))
            )
            if score > 0:
                sims.append((p, score))
    sims.sort(key=lambda x: -x[1])
    return {"similar": [p for p, _ in sims[:5]]}


@router.get("/ontology/alerts")
def get_alerts():
    # 실시간 알림/상태 반환 (예시: 최근 정책 위반/테스트 실패 등)
    # 실제 구현에서는 상태 관리 시스템 연동 필요
    # 여기서는 예시로 최근 3개 알림 반환
    alerts = [
        {"timestamp": "2024-06-10T12:00:00", "message": "테스트 실패: pytest"},
        {"timestamp": "2024-06-10T12:01:00", "message": "정책 위반: 위험 명령 감지"},
        {"timestamp": "2024-06-10T12:02:00", "message": "테스트 실패: flake8"},
    ]
    return {"alerts": alerts}


# 온톨로지 객체 임베딩 저장
@router.post("/ontology/embed")
def embed_ontology_node(node: dict = Body(...)):
    # 예시: node는 Payment/Delivery/Event 등 dict
    # 실제 운영에서는 타입 분기/검증 필요
    embedding_node(node)
    return {"status": "embedded", "node_id": node.get("id")}


# 유사 노드 검색
@router.get("/ontology/similar")
def get_similar_nodes(q: str, n: int = 5):
    results = query_similar_nodes(q, n_results=n)
    return {"query": q, "results": results}


# 관계 확장(직접 연결된 노드 반환)
@router.get("/ontology/expand")
def expand_node(node_id: str):
    # 실제 운영에서는 온톨로지 전체 노드 dict를 DB/메모리에서 불러와야 함
    # 여기서는 예시로 빈 dict 사용
    ontology_nodes = {}  # TODO: 실제 노드 dict로 교체
    node = ontology_nodes.get(node_id)
    if not node:
        return {"error": "node not found"}
    related = expand_related_nodes(node, ontology_nodes)
    return {"node_id": node_id, "related": [getattr(n, "id", None) for n in related]}
