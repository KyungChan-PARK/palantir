"""ETL flow definitions using Prefect."""

from datetime import datetime
from pathlib import Path
from typing import Optional
import os

import chromadb
import pandas as pd
import requests
import polars as pl
import httpx
from prefect import flow, task
from prefect.schedules import CronSchedule
from prefect_aws.s3 import S3Bucket
from prefect.logging import get_run_logger
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

from palantir.ontology.objects import (Customer, Delivery, Event, Order,
                                       Payment, Product)
from palantir.ontology.repository import OntologyRepository, embedding_node


@task
def extract_csv(file_path: Path) -> pl.DataFrame:
    """Extract data from CSV file."""
    logger = get_run_logger()
    logger.info(f"Extracting data from {file_path}")
    return pl.read_csv(file_path)


@task
def extract_s3(key: str, block_name: str) -> pl.DataFrame:
    """Download CSV data from S3 using Prefect block."""
    logger = get_run_logger()
    block = S3Bucket.load(block_name)
    local_path = Path("/tmp") / Path(key).name
    block.download_object_to_path(key, local_path)
    logger.info(f"Downloaded {key} from S3")
    return pl.read_csv(local_path)


@task
def extract_api(url: str) -> pl.DataFrame:
    """Fetch JSON data from an HTTP API."""
    logger = get_run_logger()
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()
    return pl.DataFrame(data)


@task
def transform_data(df: pl.DataFrame) -> pl.DataFrame:
    """Transform the extracted data."""
    logger = get_run_logger()
    logger.info("Transforming data")

    # Add your transformation logic here
    # Example: Basic cleaning
    df = df.drop_nulls()
    df = df.unique()

    return df


@task
def load_to_duckdb(
    df: pl.DataFrame,
    table_name: str,
    db_path: Optional[str] = None,
) -> None:
    """Load transformed data to DuckDB."""
    import duckdb

    logger = get_run_logger()
    logger.info(f"Loading data to table {table_name}")

    # Resolve DB path from env if not provided
    db_path = db_path or os.getenv("DUCKDB_PATH")

    # Connect to DuckDB (in-memory if no path provided)
    conn = duckdb.connect(db_path) if db_path else duckdb.connect()

    # Load dataframe (register temporary view to handle Polars)
    conn.register("df_view", df.to_pandas())
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df_view")
    conn.unregister("df_view")
    conn.close()

    logger.info("Data loaded successfully")


@flow(name="csv_to_duckdb")
def csv_to_duckdb_flow(
    csv_path: str, table_name: str, db_path: Optional[str] = None
) -> None:
    """Main ETL flow for processing CSV files to DuckDB."""
    # Convert string path to Path object
    file_path = Path(csv_path)

    # Execute the ETL pipeline
    raw_data = extract_csv(file_path)
    transformed_data = transform_data(raw_data)
    load_to_duckdb(transformed_data, table_name, db_path)


@flow(
    name="multi_source_to_duckdb",
    retries=2,
    retry_delay_seconds=30,
    log_prints=True,
    schedule=CronSchedule(cron="0 3 * * *"),
)
def multi_source_to_duckdb_flow(
    s3_key: str,
    api_url: str,
    table_name: str,
    db_path: Optional[str] = None,
    s3_block: str = os.getenv("S3_BLOCK", "etl-bucket"),
) -> None:
    """ETL flow handling S3 and API sources."""
    csv_df = extract_s3(s3_key, s3_block)
    api_df = extract_api(api_url)
    merged = pl.concat([csv_df, api_df], how="diagonal")
    transformed = transform_data(merged)
    load_to_duckdb(transformed, table_name, db_path)


@task
def load_to_sqlite(df: pl.DataFrame, table_name: str, db_path: str):
    import sqlite3

    conn = sqlite3.connect(db_path)
    df.to_pandas().to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()


@task
def generate_embeddings(texts: list, model_name: str = "all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts)
    return embeddings


@task
def load_embeddings_to_chroma(embeddings, metadatas, collection_name: str = "default"):
    client = chromadb.Client()
    collection = client.get_or_create_collection(collection_name)
    for emb, meta in zip(embeddings, metadatas):
        collection.add(emb, metadata=meta)


@flow(name="csv_to_sqlite_and_embed")
def csv_to_sqlite_and_embed_flow(
    csv_path: str, table_name: str, db_path: str, text_column: str = "text"
):
    file_path = Path(csv_path)
    raw_data = extract_csv(file_path)
    transformed_data = transform_data(raw_data)
    load_to_sqlite(transformed_data, table_name, db_path)
    if text_column in transformed_data.columns:
        texts = transformed_data[text_column].astype(str).tolist()
        embeddings = generate_embeddings(texts)
        metadatas = transformed_data.to_dict(orient="records")
        load_embeddings_to_chroma(embeddings, metadatas)


# ML 실험 예시 (간단한 분류)
@task
def train_simple_classifier(df: pd.DataFrame, label_column: str):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split

    X = df.drop(columns=[label_column])
    y = df[label_column]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    clf = RandomForestClassifier()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    return {"accuracy": acc}


ONTOLOGY_API_URL = "http://localhost:8000/ontology"


def register_payment_to_ontology(payment_dict):
    resp = requests.post(f"{ONTOLOGY_API_URL}/objects/Payment", json=payment_dict)
    return resp.json()


def register_delivery_to_ontology(delivery_dict):
    resp = requests.post(f"{ONTOLOGY_API_URL}/objects/Delivery", json=delivery_dict)
    return resp.json()


def register_event_to_ontology(event_dict):
    resp = requests.post(f"{ONTOLOGY_API_URL}/objects/Event", json=event_dict)
    return resp.json()


def create_link_api(source_id, target_id, relationship_type):
    data = {
        "source_id": source_id,
        "target_id": target_id,
        "relationship_type": relationship_type,
    }
    resp = requests.post(f"{ONTOLOGY_API_URL}/links", json=data)
    return resp.json()


@task
def etl_and_register_payments_with_links(csv_path):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        payment = {
            "order_id": row["order_id"],
            "amount": row["amount"],
            "method": row["method"],
            "status": row["status"],
        }
        payment_obj = register_payment_to_ontology(payment)
        # 주문-결제 관계 생성
        if "order_id" in row and "id" in payment_obj:
            create_link_api(row["order_id"], payment_obj["id"], "has_payment")


@task
def etl_and_register_deliveries_with_links(csv_path):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        delivery = {
            "order_id": row["order_id"],
            "address": row["address"],
            "status": row["status"],
            "tracking_number": row.get("tracking_number", ""),
        }
        delivery_obj = register_delivery_to_ontology(delivery)
        # 주문-배송 관계 생성
        if "order_id" in row and "id" in delivery_obj:
            create_link_api(row["order_id"], delivery_obj["id"], "has_delivery")


@task
def etl_and_register_events(csv_path):
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        event = {
            "object_id": row["object_id"],
            "event_type": row["event_type"],
            "description": row["description"],
        }
        register_event_to_ontology(event)


def update_object_embedding(obj_id, obj_type, embedding):
    # 객체 조회 후 embedding 속성 추가/업데이트
    obj = requests.get(f"{ONTOLOGY_API_URL}/objects/{obj_id}").json()
    obj["embedding"] = embedding.tolist() if hasattr(embedding, "tolist") else embedding
    requests.put(f"{ONTOLOGY_API_URL}/objects/{obj_id}", json=obj)


def register_event_for_prediction(obj_id, event_type, description):
    event = {"object_id": obj_id, "event_type": event_type, "description": description}
    register_event_to_ontology(event)


@task
def generate_and_register_embeddings(obj_type, text_field="description"):
    objs = get_objects_api(obj_type)
    texts = [o.get(text_field, "") for o in objs]
    embeddings = generate_embeddings.fn(texts)  # Prefect task의 .fn으로 직접 호출
    for obj, emb in zip(objs, embeddings):
        update_object_embedding(obj["id"], obj_type, emb)


@task
def register_classification_events(
    obj_type, predictions, label_field="predicted_label"
):
    objs = get_objects_api(obj_type)
    for obj, pred in zip(objs, predictions):
        desc = f"{label_field}: {pred}"
        register_event_for_prediction(obj["id"], "classification", desc)


def load_customers_from_csv(path: str) -> list:
    df = pd.read_csv(path)
    customers = [
        Customer(id=row["id"], email=row["email"], name=row["name"])
        for _, row in df.iterrows()
    ]
    return customers


def embed_and_store_customers(customers: list, chroma_path: str = "chroma_customers"):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c.display_name for c in customers]
    embeddings = model.encode(texts)
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection("customers")
    for c, emb in zip(customers, embeddings):
        collection.add(
            documents=[c.display_name], embeddings=[emb.tolist()], ids=[str(c.id)]
        )
    return collection.count()


def cluster_customers(
    customers: list, n_clusters: int = 3, chroma_path: str = "chroma_customers"
):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c.display_name for c in customers]
    embeddings = model.encode(texts)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(embeddings)
    # 온톨로지/이벤트 기록
    events = []
    for c, label in zip(customers, labels):
        c.cluster_label = int(label)
        events.append(
            Event(
                event_type="customer_clustered",
                related_id=c.id,
                timestamp=datetime.utcnow(),
                description=f"Cluster: {label}",
            )
        )
    return labels, events


def update_ontology_with_events(repo: OntologyRepository, events: list):
    for e in events:
        repo.add_event(e)


def etl_embedding_ml_pipeline(csv_path: str, repo: OntologyRepository):
    customers = load_customers_from_csv(csv_path)
    embed_and_store_customers(customers)
    labels, events = cluster_customers(customers)
    update_ontology_with_events(repo, events)
    return customers, labels, events


@task
def load_data_task():
    # 예시: CSV 등에서 데이터 적재
    # 실제 구현에서는 파일/DB/외부 API 등에서 데이터 로드
    return [
        {
            "id": "pay1",
            "order_id": "order1",
            "amount": 10000,
            "method": "card",
            "status": "completed",
        },
        {"id": "del1", "order_id": "order1", "address": "서울", "status": "delivered"},
    ]


@task
def embedding_and_ontology_task(data):
    # 데이터에서 온톨로지 객체 생성 및 임베딩
    for d in data:
        if "amount" in d:
            obj = Payment(**d, timestamp=None)
        elif "address" in d:
            obj = Delivery(**d, shipped_at=None, delivered_at=None)
        else:
            obj = Event(**d, timestamp=None)
        embedding_node(obj)
    return True


@flow
def add_ontology_from_etl_flow():
    data = load_data_task()
    embedding_and_ontology_task(data)
    # 추후 ML/분류/예측 결과도 온톨로지 객체/관계/이벤트로 자동 반영 가능
    return "ETL→임베딩→온톨로지 연동 완료"


if __name__ == "__main__":
    # Example usage
    csv_to_duckdb_flow(
        csv_path="sample.csv", table_name="example_table", db_path="data.db"
    )
