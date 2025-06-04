import pytest
from fastapi import HTTPException
from jose import jwt

from palantir.core import policy_guard


class DummyRequest:
    def __init__(self, headers):
        self.headers = headers
        self.url = "http://test"

        async def body():
            return b"body"

        self.body = body


def test_user_tier_func_gold():
    token = jwt.encode(
        {"tier": "gold"}, policy_guard.SECRET_KEY, algorithm=policy_guard.ALGORITHM
    )
    req = DummyRequest({"authorization": f"Bearer {token}"})
    assert policy_guard.user_tier_func(req) == "10/minute"


def test_user_tier_func_free():
    token = jwt.encode({}, policy_guard.SECRET_KEY, algorithm=policy_guard.ALGORITHM)
    req = DummyRequest({"authorization": f"Bearer {token}"})
    assert policy_guard.user_tier_func(req) == "5/minute"


def test_user_tier_func_invalid():
    req = DummyRequest({"authorization": "Bearer invalidtoken"})
    assert policy_guard.user_tier_func(req) == "5/minute"


def test_user_tier_func_none():
    req = DummyRequest({})
    assert policy_guard.user_tier_func(req) == "5/minute"


def test_verify_jwt_valid():
    token = jwt.encode(
        {"sub": "test"}, policy_guard.SECRET_KEY, algorithm=policy_guard.ALGORITHM
    )
    creds = type("C", (), {"credentials": token})()
    assert policy_guard.verify_jwt(creds)["sub"] == "test"


def test_verify_jwt_invalid():
    creds = type("C", (), {"credentials": "invalidtoken"})()
    with pytest.raises(HTTPException):
        policy_guard.verify_jwt(creds)


@pytest.mark.asyncio
async def test_cache_response():
    called = {}

    @policy_guard.cache_response
    async def dummy(request=None):
        called["x"] = True
        return 42

    req = DummyRequest({})
    result1 = await dummy(request=req)
    result2 = await dummy(request=req)
    assert result1 == 42 and result2 == 42 and called["x"]
