import streamlit as st
import pandas as pd
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import plotly.graph_objects as go

API_URL = "http://localhost:8000/ontology"

def create_object_api(obj_type, data):
    resp = requests.post(f"{API_URL}/objects/{obj_type}", json=data)
    return resp.json()

def get_objects_api(obj_type):
    resp = requests.post(f"{API_URL}/search", json={"obj_type": obj_type})
    return resp.json()

def get_object_embedding(obj_id):
    obj = requests.get(f"{API_URL}/objects/{obj_id}").json()
    return np.array(obj.get("embedding", []))

def recommend_similar_objects(obj_id, obj_type, top_k=5):
    target_emb = get_object_embedding(obj_id)
    objs = get_objects_api(obj_type)
    sims = []
    for o in objs:
        emb = np.array(o.get("embedding", []))
        if emb.size > 0 and target_emb.size > 0:
            sim = cosine_similarity([target_emb], [emb])[0][0]
            sims.append((o, sim))
    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:top_k]

st.title("Palantir AIP 에이전트 상태 대시보드")

# 에이전트 상태
st.header("에이전트 상태")
current_task = st.session_state.get("current_task", "N/A")
st.metric("현재 태스크", current_task)
progress = st.session_state.get("progress", 0.0)
st.progress(progress)

# 테스트/린트/정적분석 결과
st.header("테스트/린트/정적분석 결과")
test_log = st.session_state.get("test_log", "")
st.code(test_log, language="bash")

# 온톨로지 객체 실시간 생성/조회
st.header("Payment 객체 생성")
payment_data = {
    "order_id": st.text_input("Order ID"),
    "amount": st.number_input("Amount", value=0.0),
    "method": st.selectbox("Method", ["card", "bank"]),
    "status": st.selectbox("Status", ["pending", "completed", "failed", "refunded"])
}
if st.button("Payment 생성"):
    result = create_object_api("Payment", payment_data)
    st.write(result)

st.header("모든 Payment 조회")
if st.button("Payment 리스트"):
    payments = get_objects_api("Payment")
    st.dataframe(payments)

# Delivery 객체 실시간 생성/조회
st.header("Delivery 객체 생성")
delivery_data = {
    "order_id": st.text_input("[Delivery] Order ID"),
    "address": st.text_input("[Delivery] Address"),
    "status": st.selectbox("[Delivery] Status", ["preparing", "shipped", "delivered", "failed"]),
    "tracking_number": st.text_input("[Delivery] Tracking Number")
}
if st.button("Delivery 생성"):
    result = create_object_api("Delivery", delivery_data)
    st.write(result)

st.header("모든 Delivery 조회")
if st.button("Delivery 리스트"):
    deliveries = get_objects_api("Delivery")
    st.dataframe(deliveries)

# Event 객체 실시간 생성/조회
st.header("Event 객체 생성")
event_data = {
    "object_id": st.text_input("[Event] Object ID"),
    "event_type": st.text_input("[Event] Type"),
    "description": st.text_area("[Event] Description")
}
if st.button("Event 생성"):
    result = create_object_api("Event", event_data)
    st.write(result)

st.header("모든 Event 조회")
if st.button("Event 리스트"):
    events = get_objects_api("Event")
    st.dataframe(events)

# 온톨로지 객체/관계 시각화
st.header("온톨로지 데이터")
if "ontology_df" in st.session_state:
    st.dataframe(st.session_state["ontology_df"])

# 실시간 로그
st.header("실시간 로그")
if "log" in st.session_state:
    st.text(st.session_state["log"])

# 사용자 질의/분석
st.header("온톨로지 질의/분석")
query = st.text_input("질문을 입력하세요")
if st.button("질의"):
    st.write("질의 결과: ...")

# 온톨로지 객체 간 관계(링크) 실시간 생성/조회
st.header("온톨로지 관계(링크) 생성")
link_data = {
    "source_id": st.text_input("[Link] Source Object ID"),
    "target_id": st.text_input("[Link] Target Object ID"),
    "relationship_type": st.text_input("[Link] Relationship Type")
}
if st.button("관계(링크) 생성"):
    resp = requests.post(f"{API_URL}/links", json=link_data)
    st.write(resp.json())

st.header("특정 객체의 관계(링크) 조회")
link_obj_id = st.text_input("[Link] 조회할 Object ID")
link_direction = st.selectbox("[Link] 방향", ["out", "in"])
if st.button("관계(링크) 리스트") and link_obj_id:
    resp = requests.get(f"{API_URL}/objects/{link_obj_id}/links", params={"direction": link_direction})
    st.write(resp.json())

st.header("유사 Payment 추천")
target_id = st.text_input("대상 Payment ID")
if st.button("유사 Payment 추천") and target_id:
    recs = recommend_similar_objects(target_id, "Payment")
    st.write(recs)

st.header("Event 이력 타임라인")
event_obj_id = st.text_input("[Event] 타임라인 Object ID")
if st.button("이벤트 타임라인 조회") and event_obj_id:
    resp = requests.get(f"{API_URL}/objects/{event_obj_id}/links", params={"direction": "in"})
    events = [l["object"] for l in resp.json() if l["relationship"]["type"] == "classification"]
    events = sorted(events, key=lambda e: e.get("created_at", ""))
    for e in events:
        st.write(f"{e.get('created_at', '')}: {e.get('event_type', '')} - {e.get('description', '')}")

st.header("객체 관계 네트워크 시각화")
net_obj_id = st.text_input("[네트워크] 중심 Object ID")
if st.button("관계 네트워크 시각화") and net_obj_id:
    resp = requests.get(f"{API_URL}/objects/{net_obj_id}/links", params={"direction": "out"})
    links = resp.json()
    G = nx.DiGraph()
    G.add_node(net_obj_id)
    for l in links:
        target = l["object"]["id"]
        rel = l["relationship"]["type"]
        G.add_node(target)
        G.add_edge(net_obj_id, target, label=rel)
    pos = nx.spring_layout(G)
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='#888'), hoverinfo='none'))
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text', marker=dict(size=10, color='skyblue'), text=list(G.nodes()), textposition='top center'))
    st.plotly_chart(fig) 