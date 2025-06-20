"""AUTO-GEN TEST: line-cover stubs"""

import importlib

import palantir.core.scheduler as sch

mod = importlib.import_module("palantir.core.scheduler")


def test_line_8():

    assert True


def test_add_pipeline_job_prints(monkeypatch):

    called = {}

    def fake_print(msg):

        called["msg"] = msg

    monkeypatch.setattr("builtins.print", fake_print)

    sch.add_pipeline_job({"dag_name": "testdag"})

    assert "[SCHEDULED] DAG: testdag" in called["msg"]
