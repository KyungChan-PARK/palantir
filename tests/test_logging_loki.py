from fastapi import FastAPI, Request
from loguru import logger
from asgi_correlation_id import correlation_id
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/log-test")
def log_test(request: Request):
    cid = correlation_id.get()
    logger.info("[LOKI_TEST] 샘플 로그입니다.", extra={"correlation_id": cid, "testcase": "loki_logging"})
    return {"message": "로그가 기록되었습니다.", "correlation_id": cid}

def test_loki_logging():
    client = TestClient(app)
    response = client.get("/log-test")
    assert response.status_code == 200
    data = response.json()
    assert "correlation_id" in data
    # 안내: Grafana Loki에서 {app="palantir-api", correlation_id="..."}로 로그를 추적하세요. 