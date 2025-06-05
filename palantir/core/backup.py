import os
import shutil
from datetime import datetime

BACKUP_ROOT = "backups"
WEAVIATE_URL = "http://localhost:8080"
NEO4J_ADMIN = "neo4j-admin"


def notify_slack(msg: str):
    print(msg)


def rolling_delete(days: int = 30):
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
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    fname = datetime.now().strftime("%Y%m%d")
    path = os.path.join(BACKUP_ROOT, fname)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "weaviate_snapshot.txt"), "w") as f:
        f.write("ok")


def backup_neo4j():
    pass


def register_backup_jobs(scheduler):
    scheduler.add_job(backup_weaviate, "cron")
    scheduler.add_job(backup_neo4j, "cron")
