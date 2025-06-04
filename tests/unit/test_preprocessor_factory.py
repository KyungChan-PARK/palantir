import io
import json

import pandas as pd

from palantir.core import preprocessor_factory as pf


def test_detect_mime_success():

    assert pf.detect_mime("text/csv") == "csv"

    assert pf.detect_mime("application/json") == "json"


def test_detect_mime_error():

    assert pf.detect_mime("unknown/xyz") == "raw"


def test_handle_csv_roundtrip():

    data = "a,b\n1,2"

    df = pf.handle_csv(io.BytesIO(data.encode()))

    assert df.to_csv(index=False, lineterminator="\n").strip() == data


def test_handle_json_dict():

    data = json.dumps({"x": 1})

    df = pf.handle_json(io.BytesIO(data.encode()))

    assert df.iloc[0]["x"] == 1


def test_detect_mime_known():
    assert pf.detect_mime("text/csv") == "csv"
    assert pf.detect_mime("application/pdf") == "pdf"


def test_detect_mime_unknown():
    assert pf.detect_mime("unknown/type") == "raw"


def test_handle_csv_bytes():
    df = pd.DataFrame({"a": [1, 2]})
    buf = df.to_csv(index=False).encode()
    out = pf.handle_csv(buf)
    assert list(out["a"]) == [1, 2]


def test_handle_csv_filelike():
    df = pd.DataFrame({"a": [1, 2]})
    buf = io.StringIO(df.to_csv(index=False))
    out = pf.handle_csv(buf)
    assert list(out["a"]) == [1, 2]


def test_handle_json_bytes():
    data = [{"a": 1}, {"a": 2}]
    buf = json.dumps(data).encode()
    out = pf.handle_json(buf)
    assert list(out["a"]) == [1, 2]


def test_handle_json_filelike():
    data = [{"a": 1}, {"a": 2}]
    buf = io.StringIO(json.dumps(data))
    out = pf.handle_json(buf)
    assert list(out["a"]) == [1, 2]
