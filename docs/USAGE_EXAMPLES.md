# Palantir AIP 실전 활용 예시 (USAGE_EXAMPLES.md)

## 1. 실전 데이터 연동 및 온톨로지 자동화
- CSV/DB/API 등에서 실전 데이터를 ETL 파이프라인으로 적재
- Prefect Flow에서 Payment, Delivery, Event 등 객체를 온톨로지 API로 자동 등록
- 객체 등록 후 주문-결제, 주문-배송 등 관계(링크)도 자동 생성

### 예시 코드 (flows.py)
```python
@task
def etl_and_register_payments_with_links(csv_path):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        payment = {...}
        payment_obj = register_payment_to_ontology(payment)
        create_link_api(row["order_id"], payment_obj["id"], "has_payment")
```

## 2. 임베딩/ML 결과 온톨로지 반영
- 텍스트/문서/고객/상품 등 임베딩을 객체 속성(embedding)으로 저장
- 분류/예측 결과를 Event로 기록

### 예시 코드
```python
def update_object_embedding(obj_id, obj_type, embedding):
    obj = requests.get(f"{API_URL}/objects/{obj_id}").json()
    obj["embedding"] = embedding.tolist()
    requests.put(f"{API_URL}/objects/{obj_id}", json=obj)
```

## 3. 대시보드/분석/추천 활용
- Streamlit 대시보드에서 객체 생성/조회/관계/이벤트/임베딩/유사도 추천/네트워크 시각화 등 실시간 분석
- FastAPI API와 연동하여 실시간 CRUD/분석/관계/추천/이력 타임라인 등 활용

### 예시: 유사 Payment 추천
```python
st.header("유사 Payment 추천")
target_id = st.text_input("대상 Payment ID")
if st.button("유사 Payment 추천") and target_id:
    recs = recommend_similar_objects(target_id, "Payment")
    st.write(recs)
```

## 4. 운영/자동화/모니터링/정책
- run_all.sh로 FastAPI, Streamlit, Prefect를 한 번에 실행
- Prometheus, Grafana, docker-compose 등으로 상태/이벤트/로그 모니터링
- .cursorrules 정책에 따라 위험 명령은 차단, 3회 연속 실패 시 자동 중단 및 Planner 재계획
- 정책 위반/운영 이벤트는 실시간 대시보드 및 Slack/이메일 등으로 알림

## 5. 확장/테스트/보안/정책
- 새로운 온톨로지 객체/관계/분석/추천/정책 등 자유롭게 확장
- 통합 테스트: pytest, Prefect Flow, API, 대시보드, ETL/ML, 관계/이벤트 생성 등 자동화
- .cursorrules, POLICY.md, FAQ.md, README.md 등 정책/보안/운영 문서 참고 