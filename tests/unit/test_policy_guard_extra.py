import pytest

from palantir.core import policy_guard as pg


@pytest.mark.asyncio
async def test_cache_response_hit():
    class DummyReq:
        url = "dummy"
        async def body(self): return b""
    req = DummyReq()
    key = str(req.url) + str(await req.body())
    pg.cache[key] = "cached"
    @pg.cache_response
    async def f(request=None):
        return "notcached"
    result = await f(request=req)
    assert result == "cached"
