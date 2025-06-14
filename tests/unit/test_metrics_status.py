import builtins
import os

from fastapi.testclient import TestClient

from main import app


def test_metrics_endpoint_status():
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code in (200, 404)


def test_metrics_self_improve_204(tmp_path, monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    res = client.get("/metrics/self_improve")
    assert res.status_code == 204


def test_metrics_self_improve_200(tmp_path, monkeypatch):
    client = TestClient(app)
    fpath = tmp_path / "self_improve_metrics.prom"
    fpath.write_text("metrics")
    monkeypatch.setattr(os.path, "exists", lambda path: True)
    orig_open = builtins.open

    def fake_open(path, *a, **k):
        if path == "logs/self_improve_metrics.prom":
            return orig_open(fpath, *a, **k)
        return orig_open(path, *a, **k)

    monkeypatch.setattr(builtins, "open", fake_open)
    res = client.get("/metrics/self_improve")
    assert res.status_code == 200 and b"metrics" in res.content
