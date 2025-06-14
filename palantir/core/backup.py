import os
import shutil
import requests
import subprocess
from datetime import datetime
import weaviate

BACKUP_ROOT = "backups"
WEAVIATE_URL = "http://localhost:8080"
NEO4J_ADMIN = "neo4j-admin"


def notify_slack(msg: str):
    """Slack으로 알림을 보냅니다."""
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if webhook_url:
            requests.post(webhook_url, json={"text": msg})
    except Exception as e:
        print(f"Slack 알림 전송 실패: {e}")


def rolling_delete(days: int = 30):
    """오래된 백업을 삭제합니다."""
    cutoff = datetime.now().timestamp() - days * 86400
    if not os.path.exists(BACKUP_ROOT):
        return
    for name in os.listdir(BACKUP_ROOT):
        path = os.path.join(BACKUP_ROOT, name)
        if os.path.isdir(path):
            t = datetime.strptime(name, "%Y%m%d").timestamp()
            if t < cutoff:
                shutil.rmtree(path)


def backup_weaviate():
    """Weaviate 데이터베이스를 백업합니다."""
    try:
        client = weaviate.Client(WEAVIATE_URL)
        os.makedirs(BACKUP_ROOT, exist_ok=True)
        fname = datetime.now().strftime("%Y%m%d")
        path = os.path.join(BACKUP_ROOT, fname)
        os.makedirs(path, exist_ok=True)
        
        # Weaviate 백업 생성
        backup = client.backup.create(
            backup_id=fname,
            backend="filesystem",
            include_classes=["*"]
        )
        
        with open(os.path.join(path, "weaviate_snapshot.txt"), "w") as f:
            f.write("ok")
    except Exception as e:
        notify_slack(f"Weaviate 백업 실패: {e}")


def backup_neo4j():
    """Neo4j 데이터베이스를 백업합니다."""
    try:
        os.makedirs(BACKUP_ROOT, exist_ok=True)
        fname = datetime.now().strftime("%Y%m%d")
        path = os.path.join(BACKUP_ROOT, fname)
        os.makedirs(path, exist_ok=True)
        
        # Neo4j 백업 실행
        subprocess.run([
            NEO4J_ADMIN,
            "backup",
            "--backup-dir", path,
            "--name", fname
        ], check=True)
    except Exception as e:
        notify_slack(f"Neo4j 백업 실패: {e}")


def register_backup_jobs(scheduler):
    """백업 작업을 스케줄러에 등록합니다."""
    scheduler.add_job(backup_weaviate, "cron", hour=0)
    scheduler.add_job(backup_neo4j, "cron", hour=1)
