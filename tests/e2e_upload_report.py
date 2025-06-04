import io
import os
import random
import string
import tempfile

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def random_string(n=8):
    return "".join(random.choices(string.ascii_letters, k=n))


def test_txt_upload():
    resp = client.post(
        "/upload", files={"file": ("test.txt", b"hello world", "text/plain")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "text"
    job_id = data["job_id"]
    r = client.get(f"/report/{job_id}")
    assert "hello world" in r.text


def test_broken_excel():
    resp = client.post(
        "/upload",
        files={
            "file": (
                "broken.xlsx",
                b"not an excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 200 or resp.status_code == 400
    if resp.status_code == 400:
        assert "error" in resp.json()
    else:
        job_id = resp.json()["job_id"]
        r = client.get(f"/report/{job_id}")
        assert "error" in r.text or "unsupported file type" in r.text


def test_jpeg_upload():
    from PIL import Image

    img = Image.fromarray((255 * np.random.rand(128, 128, 3)).astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    resp = client.post(
        "/upload", files={"file": ("test.jpg", buf.read(), "image/jpeg")}
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    r = client.get(f"/report/{job_id}")
    assert "CLIP" in r.text
    assert "img" in r.text or "base64" in r.text


def test_pdf_upload():
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="test pdf", ln=True)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    tmp.close()
    with open(tmp.name, "rb") as f:
        resp = client.post(
            "/upload", files={"file": ("test.pdf", f.read(), "application/pdf")}
        )
    os.unlink(tmp.name)
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    r = client.get(f"/report/{job_id}")
    assert "test pdf" in r.text or "텍스트 추출 실패" in r.text


def test_large_csv():
    df = pd.DataFrame({"a": range(1001), "b": range(1001)})
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    resp = client.post(
        "/upload", files={"file": ("big.csv", buf.read().encode(), "text/csv")}
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    r = client.get(f"/report/{job_id}")
    assert "1000행" in r.text and "/download/" in r.text
    # 다운로드 링크 동작 확인
    dl = client.get(f"/download/{job_id}")
    assert dl.status_code == 200
    assert b"a,b" in dl.content


def test_approve():
    resp = client.post(
        "/upload", files={"file": ("test.txt", b"approve test", "text/plain")}
    )
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]
    r = client.post(
        f"/report/{job_id}/action", data={"action": "approve"}, follow_redirects=False
    )
    assert r.status_code == 303
