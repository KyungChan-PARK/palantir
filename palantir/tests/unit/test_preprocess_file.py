import io as _io
import json
import sys
import tempfile
import types

import pandas as _pd
import pytest
from fastapi import HTTPException
from pytest import MonkeyPatch

# 스텁: embed_image_clip → 고정 벡터
import palantir.core.preprocessor_factory as pf

pf.embed_image_clip = lambda img: [0.1]*512



# 스텁: Pillow.Image.open

class DummyImg:
    pass



pf.Image = types.SimpleNamespace(open=lambda *a, **k: DummyImg())



# 스텁: pytesseract

pf.pytesseract = types.SimpleNamespace(image_to_string=lambda img: "OCR")



# 스텁: fitz( PyMuPDF )

class DummyPage:

    def get_text(self): return 'PDF TEXT'

    def get_pixmap(self): return types.SimpleNamespace(width=1, height=1, samples=b"\x00"*3)

class DummyDoc(list):

    def __init__(self): super().__init__([DummyPage()])

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_val, exc_tb): pass

sys.modules['fitz'].open = lambda *a, **k: DummyDoc()

class DummyTmp:

    def __init__(self): self.name = 'dummy.pdf'

    def write(self, x): pass

    def flush(self): pass

    def close(self): pass

    def __enter__(self): return self

    def __exit__(self, exc_type, exc_val, exc_tb): pass

    def seek(self,*a,**kw): return 0

    def read(self,*a,**kw): return b'%PDF-1.4'

tempfile.NamedTemporaryFile = lambda *a, **k: DummyTmp()



# ---- runtime mocks for heavy parsers ----

sys.modules['fitz'].open = lambda *a, **k: DummyDoc()



_buf = _io.BytesIO()

_pd.DataFrame({'a':[1,2]}).to_excel(_buf, index=False)

XLSX_BYTES = _buf.getvalue()



CSV_BYTES = b"a,b\n1,2"

JSON_BYTES = json.dumps({"foo": "bar"}).encode()

PDF_BYTES = b"%PDF-1.4\n%%EOF"

IMG_BYTES = __import__('base64').b64decode("iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAADklEQVQI12P4//8/AwAI/AL+dp1AOwAAAABJRU5ErkJggg==")



@pytest.mark.asyncio
@pytest.mark.parametrize("filename,mime,content,expect",[
    ("test.csv", "text/csv",    CSV_BYTES,  "table"),
    ("test.json", "application/json", JSON_BYTES,"json"),
    ("test.pdf", "application/pdf",  PDF_BYTES, "pdf"),
    ("test.png", "image/png",    IMG_BYTES,  "image"),
    ("test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", XLSX_BYTES,"table"),
    ("test.bin", "application/octet-stream", b"rawdata", "raw"),
])
async def test_preprocess_file_branches(filename, mime, content, expect, tmp_path):
    # 임시 파일 생성 및 삭제를 tmp_path로 대체
    file_path = tmp_path / filename
    with open(file_path, "wb") as f:
        f.write(content)
    if expect == "raw":
        with pytest.raises(HTTPException) as excinfo:
            await pf.preprocess_file(str(file_path), mime, content, job_id=123)
        assert excinfo.value.status_code == 415
    else:
        res = await pf.preprocess_file(str(file_path), mime, content, job_id=123)
        if expect == "pdf" and "error" in res:
            assert res["type"] == "pdf"
            assert "error" in res
        else:
            assert res["type"] == expect
        assert res["job_id"] == 123



@pytest.mark.asyncio
async def test_preprocess_excel_local_mock(monkeypatch: MonkeyPatch):

    import pandas as pd

    monkeypatch.setattr(pd, "read_excel", lambda *a, **k: pd.DataFrame({"a":[1]}))

    from palantir.core.preprocessor_factory import preprocess_file

    xlsx = b'PK\x03\x04'  # minimal fake zip header

    res = await preprocess_file("test.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",xlsx,job_id=1)

    assert res["type"]=="table"

    assert "a" in res["data"]



@pytest.mark.asyncio
async def test_preprocess_file_csv():
    df = _pd.DataFrame({"a": [1,2]})
    buf = df.to_csv(index=False).encode()
    out = await pf.preprocess_file("test.csv", "text/csv", buf, "job1")
    assert out["type"] == "table" and out["job_id"] == "job1"

@pytest.mark.asyncio
async def test_preprocess_file_json():
    import json
    data = [{"a": 1}, {"a": 2}]
    buf = json.dumps(data).encode()
    out = await pf.preprocess_file("test.json", "application/json", buf, "job2")
    assert out["type"] == "json"

@pytest.mark.asyncio
async def test_preprocess_file_pdf(monkeypatch):
    # fitz.open, pytesseract.image_to_string 모킹
    class DummyPage:
        def get_text(self): return "page text"
        def get_pixmap(self):
            class Pix:
                width = 1
                height = 1
                samples = b"a" * 3
            return Pix()
    class DummyDoc:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def __iter__(self): return iter([DummyPage()])
        def __getitem__(self, idx): return DummyPage()
    monkeypatch.setattr("fitz.open", lambda *a, **k: DummyDoc())
    monkeypatch.setattr("pytesseract.image_to_string", lambda img: "ocr text")
    out = await pf.preprocess_file("test.pdf", "application/pdf", b"%PDF", "job3")
    assert out["type"] == "pdf"
    assert "error" in out

@pytest.mark.asyncio
async def test_preprocess_file_image(monkeypatch):
    class DummyImg:
        pass
    monkeypatch.setattr("PIL.Image.open", lambda buf: DummyImg())
    monkeypatch.setattr("palantir.core.clip_embed.embed_image_clip", lambda img: [0]*512)
    out = await pf.preprocess_file("test.png", "image/png", b"img", "job4")
    assert out["type"] == "image"

@pytest.mark.asyncio
async def test_preprocess_file_excel(monkeypatch):
    monkeypatch.setattr("pandas.read_excel", lambda buf, engine=None: _pd.DataFrame({"a": [1]}))
    out = await pf.preprocess_file("test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"excel", "job5")
    assert out["type"] == "table"

@pytest.mark.asyncio
async def test_preprocess_file_raw():
    with pytest.raises(HTTPException) as excinfo:
        await pf.preprocess_file("test.bin", "application/octet-stream", b"rawdata", "job6")
    assert excinfo.value.status_code == 415
