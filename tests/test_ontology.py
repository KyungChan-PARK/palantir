import pytest

from fastapi.testclient import TestClient

from palantir import app



client = TestClient(app)

 

def test_ontology_sync():

    res = client.post("/ontology/sync")

    assert res.status_code == 200

    assert res.json()["synced"] is True 