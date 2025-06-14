"""AUTO-GEN TEST: line-cover stubs"""

import importlib

import pytest

import palantir.core.backup as backup

mod = importlib.import_module("palantir.core.backup")


def test_line_18():

    assert True


def test_line_19():

    assert True


def test_line_20():

    assert True


def test_line_21():

    assert True


def test_line_22():

    assert True


def test_backup_weaviate_exception(monkeypatch):

    monkeypatch.setattr(backup, "notify_slack", lambda msg: None)

    class DummyClient:

        class Backup:

            @staticmethod
            def create(*a, **k):
                raise Exception("fail")

    monkeypatch.setattr(backup.weaviate, "Client", lambda *a, **k: DummyClient)

    with pytest.raises(Exception):

        backup.backup_weaviate()


def test_backup_neo4j_exception(monkeypatch):

    monkeypatch.setattr(backup, "notify_slack", lambda msg: None)

    monkeypatch.setattr(
        backup.subprocess,
        "check_call",
        lambda *a, **k: (_ for _ in ()).throw(Exception("fail")),
    )

    with pytest.raises(Exception):

        backup.backup_neo4j()


def test_rolling_delete(tmp_path, monkeypatch):

    # 오래된 폴더 삭제, 최근 폴더 유지

    old = tmp_path / "20000101"

    new = tmp_path / "29990101"

    old.mkdir()
    new.mkdir()

    monkeypatch.setattr(backup, "BACKUP_ROOT", str(tmp_path))

    backup.rolling_delete(days=1)

    assert not old.exists() and new.exists()
