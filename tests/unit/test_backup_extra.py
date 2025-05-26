def test_rolling_delete_no_files(monkeypatch):
    from palantir.core import backup
    monkeypatch.setattr(backup.os, "listdir", lambda *_: [])
    monkeypatch.setattr(backup.os, "path", backup.os.path)
    monkeypatch.setattr(backup.os.path, "isdir", lambda *_: True)
    monkeypatch.setattr(backup.shutil, "rmtree", lambda *_: None)
    backup.rolling_delete(days=0)

def test_notify_slack_exception(monkeypatch):
    from palantir.core import backup
    monkeypatch.setattr(backup.requests, "post", lambda *a, **k: (_ for _ in ()).throw(Exception("fail")))
    backup.notify_slack("msg") 