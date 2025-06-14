from fastapi.testclient import TestClient

from main import app


def test_metrics_endpoint():
    cli = TestClient(app)
    res = cli.get("/metrics")
    assert res.status_code in (200, 404)
