import pytest

from fastapi.testclient import TestClient

from palantir import app

from jose import jwt



SECRET_KEY = "palantir-secret"

ALGORITHM = "HS256"



def make_token():

    return jwt.encode({"sub": "testuser"}, SECRET_KEY, algorithm=ALGORITHM)



client = TestClient(app)



def test_ask_sql():

    token = make_token()

    res = client.post(

        "/ask",

        json={"query": "hello", "mode": "sql"},

        headers={"Authorization": f"Bearer {token}"},

    )

    assert res.status_code == 200

    assert "SELECT" in res.json()["code"]



def test_ask_unauthorized():

    res = client.post("/ask", json={"query": "hi"})

    assert res.status_code == 403 or res.status_code == 401 