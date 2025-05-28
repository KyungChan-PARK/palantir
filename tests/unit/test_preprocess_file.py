import io as _io
import json
import sys
import tempfile
import types

import pandas as _pd
import pytest
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
    ("test.pdf", "application/pdf",  PDF_BYTES,"pdf"),
    ("test.png", "image/png",    IMG_BYTES,  "image"),
    ("test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", XLSX_BYTES,"table"),
    ("test.bin", "application/octet-stream", b"rawdata", "raw"),
])
async def test_preprocess_file_branches(filename, mime, content, expect, tmp_path):
    # 임시 파일 생성 및 삭제를 tmp_path로 대체
    file_path = tmp_path / filename
    with open(file_path, "wb") as f:
        f.write(content)
    res = await pf.preprocess_file(str(file_path), mime, content, job_id=123)
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
