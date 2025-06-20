from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/status")
def status():
    return {"app": "ok"}

client = TestClient(app)

def test_status_endpoint():
    resp = client.get('/status')
    assert resp.status_code == 200
    assert 'app' in resp.json()
