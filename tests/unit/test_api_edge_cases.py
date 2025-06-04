import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app

# pipeline.py: invalid yaml, invalid schema


def test_pipeline_validate_invalid_yaml():
    client = TestClient(app)
    res = client.post("/pipeline/validate", files={"file": ("bad.yaml", b"bad: [")})
    assert res.status_code in (400, 422) or res.json().get("valid") is False


def test_pipeline_submit_invalid_yaml():
    client = TestClient(app)
    res = client.post("/pipeline/submit", files={"file": ("bad.yaml", b"bad: [")})
    assert res.status_code in (400, 422) or res.json().get("submitted") is False


# report.py: not found, wrong accept header


def test_report_not_found_html():
    client = TestClient(app)
    res = client.get("/report/doesnotexist", headers={"accept": "text/html"})
    assert res.status_code == 404
    assert "Job not found" in res.text


def test_report_not_found_json():
    client = TestClient(app)
    res = client.get("/report/doesnotexist", headers={"accept": "application/json"})
    assert res.status_code == 404
    assert res.json()["detail"] == "job_id not found"


# upload.py: invalid content_type


def test_upload_invalid_content_type():
    client = TestClient(app)
    res = client.post("/upload", files={"file": ("file.txt", b"data", "text/plain")})
    assert res.status_code == 200
    assert res.json()["type"] == "text"


# core/auth.py: refresh token blacklisted


def test_auth_refresh_blacklisted():
    from palantir.core.auth import blacklist_refresh_token

    token = "tok"
    blacklist_refresh_token(token)
    client = TestClient(app)
    res = client.post("/auth/refresh", data={"refresh_token": token})
    assert res.status_code == 401


# core/preprocessor_factory.py: unknown mime


def test_preprocess_file_unknown_mime():
    import asyncio

    from palantir.core.preprocessor_factory import preprocess_file

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            preprocess_file("file.unknown", "application/x-unknown", b"data", "jid")
        )
    assert excinfo.value.status_code == 415
