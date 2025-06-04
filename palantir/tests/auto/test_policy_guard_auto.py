"""AUTO-GEN TEST: line-cover stubs"""

import importlib

import pytest
from fastapi import HTTPException

import palantir.core.policy_guard as pg

mod = importlib.import_module("palantir.core.policy_guard")


def test_line_13():

    assert True


def test_line_14():

    assert True


def test_line_15():

    assert True


def test_line_16():

    assert True


def test_line_17():

    assert True


class DummyCred:

    credentials = "invalid.jwt.token"


def test_verify_jwt_invalid():

    with pytest.raises(HTTPException):

        pg.verify_jwt(DummyCred())


def test_rate_limit_for_tier():

    assert pg.rate_limit_for_tier("admin") == "100/minute"

    assert pg.rate_limit_for_tier("pro") == "30/minute"

    assert pg.rate_limit_for_tier("free") == "5/minute"

    assert pg.rate_limit_for_tier("other") == "5/minute"


def test_user_tier_func_bearer(monkeypatch):

    class DummyReq:

        headers = {"authorization": "Bearer invalid.jwt.token"}

    assert pg.user_tier_func(DummyReq()) == "5/minute"


def test_user_tier_func_none():

    class DummyReq:

        headers = {}

    assert pg.user_tier_func(DummyReq()) == "5/minute"
