import pytest

from fastapi.testclient import TestClient

from palantir import app



client = TestClient(app)



def test_status_keys():

    response = client.get("/status")

    assert response.status_code == 200

    data = response.json()

    for key in ["app", "weaviate", "neo4j", "self_improve"]:

        assert key in data 