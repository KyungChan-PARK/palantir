import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta

import requests
import weaviate

SLACK_WEBHOOK_URL = os.environ.get(
    "SLACK_WEBHOOK_URL",
    "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
)
BACKUP_ROOT = "C:/palantir/backups"
WEAVIATE_URL = "http://localhost:8080"
NEO4J_ADMIN = "neo4j-admin"  # PATH에 있다고 가정
NEO4J_DB = "neo4j"
NEO4J_USER = "neo4j"
NEO4J_PASS = "test"


def backup_weaviate():
    today = datetime.now().strftime("%Y%m%d")
    backup_dir = os.path.join(BACKUP_ROOT, today)
    os.makedirs(backup_dir, exist_ok=True)
    try:
        client = weaviate.Client(WEAVIATE_URL)
        client.backup.create(name=today, backend="filesystem")
        with open(os.path.join(backup_dir, "weaviate_snapshot.txt"), "w") as f:
            f.write("[OK] weaviate snapshot success")
        print(f"[BACKUP] weaviate → {backup_dir}")
        notify_slack(f"Weaviate 백업 완료: {backup_dir}")
    except Exception:
        logging.exception("[BACKUP][ERROR] weaviate")
        raise


def backup_neo4j():
    today = datetime.now().strftime("%Y%m%d")
    backup_dir = os.path.join(BACKUP_ROOT, today)
    os.makedirs(backup_dir, exist_ok=True)
    try:
        cmd = f"{NEO4J_ADMIN} database backup --backup-dir={backup_dir} --database={NEO4J_DB} --user={NEO4J_USER} --password={NEO4J_PASS}"
        subprocess.check_call(cmd, shell=True)
        print(f"[BACKUP] neo4j → {backup_dir}")
        notify_slack(f"Neo4j 백업 완료: {backup_dir}")
    except Exception:
        logging.exception("[BACKUP][ERROR] neo4j")
        raise


def rolling_delete(days=30):
    cutoff = datetime.now() - timedelta(days=days)
    for d in os.listdir(BACKUP_ROOT):
        dir_path = os.path.join(BACKUP_ROOT, d)
        if os.path.isdir(dir_path):
            try:
                dt = datetime.strptime(d, "%Y%m%d")
                if dt < cutoff:
                    shutil.rmtree(dir_path)
                    print(f"[BACKUP] 롤링 삭제: {dir_path}")
            except Exception:
                continue


def notify_slack(msg):
    # 실제 슬랙 Webhook 대신 print + 요청
    print(f"[SLACK][MOCK] {msg}")
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": msg}, timeout=2)
    except Exception:
        pass


def register_backup_jobs(scheduler):
    scheduler.add_job(backup_weaviate, "cron", day_of_week="sun", hour=3)
    scheduler.add_job(backup_neo4j, "cron", day_of_week="sun", hour=4)
    scheduler.add_job(rolling_delete, "cron", day_of_week="sun", hour=5)
