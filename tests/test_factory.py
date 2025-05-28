import jsonimport pandas as pdimport pytestfrom palantir.core.preprocessor_factory import preprocess_file@pytest.mark.asyncio
async def test_preprocess_csv():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    content = df.to_csv(index=False).encode()
    result = await preprocess_file("test.csv", "text/csv", content, "job1")
    assert result["type"] == "table"
    assert "a" in result["data"]

@pytest.mark.asyncio
async def test_preprocess_json():
    data = {"x": 1, "y": 2}
    content = json.dumps(data).encode()
    result = await preprocess_file("test.json", "application/json", content, "job2")
    assert result["type"] == "json"
    assert result["data"]["x"] == 1

@pytest.mark.asyncio
async def test_preprocess_excel():
    df = pd.DataFrame({"a": [1, 2]})
    import io
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    content = buf.getvalue()
    result = await preprocess_file("test.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", content, "job3")
    assert result["type"] == "table"
    assert "a" in result["data"]