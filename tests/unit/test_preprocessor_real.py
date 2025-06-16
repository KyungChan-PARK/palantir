import json

import pytest

from palantir.core import preprocessor_factory as pf


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename,mime,content,expect",
    [
        ("sample.csv", "text/csv", b"a,b\n1,2", "table"),
        ("sample.json", "application/json", json.dumps({"x": 1}).encode(), "json"),
    ],
)
async def test_preprocess_real(filename, mime, content, expect):

    res = await pf.preprocess_file(filename, mime, content, job_id="job")

    assert res["type"] == expect
