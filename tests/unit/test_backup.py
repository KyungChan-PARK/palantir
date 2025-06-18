from palantir.core import backup


def test_rolling_delete_no_files(monkeypatch):
    monkeypatch.setattr(backup.os, "listdir", lambda *_: [])
    monkeypatch.setattr(backup.os, "path", backup.os.path)
    monkeypatch.setattr(backup.os.path, "isdir", lambda *_: True)
    monkeypatch.setattr(backup.shutil, "rmtree", lambda *_: None)
    backup.rolling_delete(days=0)


def test_notify_slack_exception(monkeypatch):
    monkeypatch.setattr(
        backup.requests,
        "post",
        lambda *a, **k: (_ for _ in ()).throw(Exception("fail")),
    )
    backup.notify_slack("msg")


def test_notify_slack():
    backup.notify_slack("테스트 메시지")  # 예외 없이 print만 되면 통과


def test_rolling_delete(tmp_path):
    # 오래된 폴더 생성
    old_dir = tmp_path / "20200101"
    old_dir.mkdir()
    # 최근 폴더 생성
    recent_dir = tmp_path / "20990101"
    recent_dir.mkdir()
    orig_backup_root = backup.BACKUP_ROOT
    backup.BACKUP_ROOT = str(tmp_path)
    backup.rolling_delete(days=30)
    assert not old_dir.exists()
    assert recent_dir.exists()
    backup.BACKUP_ROOT = orig_backup_root


def test_backup_weaviate_mock(monkeypatch, tmp_path):
    class DummyClient:
        class Backup:
            @staticmethod
            def create(name, backend):
                return None

    monkeypatch.setattr(backup.weaviate, "Client", lambda url: DummyClient())
    monkeypatch.setattr(backup, "WEAVIATE_URL", "dummy")
    monkeypatch.setattr(backup, "BACKUP_ROOT", str(tmp_path))
    backup.backup_weaviate()
    assert (
        tmp_path
        / f"{backup.datetime.now().strftime('%Y%m%d')}"
        / "weaviate_snapshot.txt"
    ).exists()


def test_backup_neo4j_mock(monkeypatch, tmp_path):
    monkeypatch.setattr(backup, "NEO4J_ADMIN", "echo")
    monkeypatch.setattr(backup, "BACKUP_ROOT", str(tmp_path))
    backup.backup_neo4j()
    # 파일 생성은 안되지만 예외 없이 통과하면 성공


def test_backup_neo4j_exception(monkeypatch):
    monkeypatch.setattr(backup, "notify_slack", lambda msg: None)
    monkeypatch.setattr(
        backup.subprocess,
        "check_call",
        lambda *a, **k: (_ for _ in ()).throw(Exception("fail")),
    )
    with pytest.raises(Exception):
        backup.backup_neo4j() 