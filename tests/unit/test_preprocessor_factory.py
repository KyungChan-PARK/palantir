import pytest, io, json
from palantir.core.preprocessor_factory import detect_mime, handle_csv, handle_json

def test_detect_mime_success():
    assert detect_mime('text/csv') == 'csv'
    assert detect_mime('application/json') == 'json'

def test_detect_mime_error():
    assert detect_mime('unknown/xyz') == 'raw'

def test_handle_csv_roundtrip():
    data = 'a,b\n1,2'
    df = handle_csv(io.BytesIO(data.encode()))
    assert df.to_csv(index=False, lineterminator='\n').strip() == data

def test_handle_json_dict():
    data = json.dumps({"x":1})
    df = handle_json(io.BytesIO(data.encode()))
    assert df.iloc[0]['x'] == 1 