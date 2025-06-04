"""백업 시스템 모듈."""

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import requests
import weaviate

# 환경 변수에서 설정 가져오기
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
BACKUP_ROOT = os.environ.get("BACKUP_ROOT", "C:/palantir/backups")
WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
NEO4J_ADMIN = os.environ.get("NEO4J_ADMIN", "neo4j-admin")
NEO4J_DB = os.environ.get("NEO4J_DB", "neo4j")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASS = os.environ.get("NEO4J_PASS", "test")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BackupError(Exception):
    """백업 관련 예외 클래스."""

    pass


def create_backup_dir() -> Path:
    """백업 디렉토리를 생성합니다."""
    today = datetime.now().strftime("%Y%m%d")
    backup_dir = Path(BACKUP_ROOT) / today
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def backup_weaviate(retry_count: int = 3) -> Dict[str, Any]:
    """Weaviate 데이터베이스를 백업합니다.

    Args:
        retry_count: 재시도 횟수

    Returns:
        백업 결과 정보

    Raises:
        BackupError: 백업 실패 시
    """
    backup_dir = create_backup_dir()
    backup_info = {
        "timestamp": datetime.now().isoformat(),
        "type": "weaviate",
        "status": "failed",
        "path": str(backup_dir),
        "error": None,
    }

    for attempt in range(retry_count):
        try:
            client = weaviate.Client(WEAVIATE_URL)
            client.backup.create(name=backup_dir.name, backend="filesystem")

            # 백업 메타데이터 저장
            backup_info["status"] = "success"
            with open(backup_dir / "weaviate_metadata.json", "w") as f:
                json.dump(backup_info, f, indent=2)

            logger.info(f"Weaviate 백업 완료: {backup_dir}")
            notify_slack(f"Weaviate 백업 완료: {backup_dir}")
            return backup_info

        except Exception as e:
            backup_info["error"] = str(e)
            logger.error(f"Weaviate 백업 실패 (시도 {attempt + 1}/{retry_count}): {e}")
            if attempt == retry_count - 1:
                notify_slack(f"Weaviate 백업 실패: {e}")
                raise BackupError(f"Weaviate 백업 실패: {e}")


def backup_neo4j(retry_count: int = 3) -> Dict[str, Any]:
    """Neo4j 데이터베이스를 백업합니다.

    Args:
        retry_count: 재시도 횟수

    Returns:
        백업 결과 정보

    Raises:
        BackupError: 백업 실패 시
    """
    backup_dir = create_backup_dir()
    backup_info = {
        "timestamp": datetime.now().isoformat(),
        "type": "neo4j",
        "status": "failed",
        "path": str(backup_dir),
        "error": None,
    }

    for attempt in range(retry_count):
        try:
            cmd = [
                NEO4J_ADMIN,
                "database",
                "backup",
                f"--backup-dir={backup_dir}",
                f"--database={NEO4J_DB}",
                f"--user={NEO4J_USER}",
                f"--password={NEO4J_PASS}",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # 백업 메타데이터 저장
            backup_info["status"] = "success"
            backup_info["output"] = result.stdout
            with open(backup_dir / "neo4j_metadata.json", "w") as f:
                json.dump(backup_info, f, indent=2)

            logger.info(f"Neo4j 백업 완료: {backup_dir}")
            notify_slack(f"Neo4j 백업 완료: {backup_dir}")
            return backup_info

        except subprocess.CalledProcessError as e:
            backup_info["error"] = e.stderr
            logger.error(
                f"Neo4j 백업 실패 (시도 {attempt + 1}/{retry_count}): {e.stderr}"
            )
            if attempt == retry_count - 1:
                notify_slack(f"Neo4j 백업 실패: {e.stderr}")
                raise BackupError(f"Neo4j 백업 실패: {e.stderr}")
        except Exception as e:
            backup_info["error"] = str(e)
            logger.error(f"Neo4j 백업 실패 (시도 {attempt + 1}/{retry_count}): {e}")
            if attempt == retry_count - 1:
                notify_slack(f"Neo4j 백업 실패: {e}")
                raise BackupError(f"Neo4j 백업 실패: {e}")


def rolling_delete(days: int = 30) -> None:
    """오래된 백업을 삭제합니다.

    Args:
        days: 보관 기간 (일)
    """
    cutoff = datetime.now() - timedelta(days=days)
    backup_root = Path(BACKUP_ROOT)

    for backup_dir in backup_root.iterdir():
        if not backup_dir.is_dir():
            continue

        try:
            dt = datetime.strptime(backup_dir.name, "%Y%m%d")
            if dt < cutoff:
                shutil.rmtree(backup_dir)
                logger.info(f"오래된 백업 삭제: {backup_dir}")
                notify_slack(f"오래된 백업 삭제: {backup_dir}")
        except ValueError:
            logger.warning(f"잘못된 백업 디렉토리 이름: {backup_dir}")
            continue


def notify_slack(msg: str) -> None:
    """Slack으로 알림을 보냅니다.

    Args:
        msg: 알림 메시지
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack Webhook URL이 설정되지 않았습니다.")
        return

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": msg}, timeout=5)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Slack 알림 전송 실패: {e}")


def register_backup_jobs(scheduler) -> None:
    """백업 작업을 스케줄러에 등록합니다.

    Args:
        scheduler: APScheduler 인스턴스
    """
    # 매주 일요일 새벽 3시에 Weaviate 백업
    scheduler.add_job(
        backup_weaviate, "cron", day_of_week="sun", hour=3, id="weaviate_backup"
    )

    # 매주 일요일 새벽 4시에 Neo4j 백업
    scheduler.add_job(
        backup_neo4j, "cron", day_of_week="sun", hour=4, id="neo4j_backup"
    )

    # 매주 일요일 새벽 5시에 오래된 백업 삭제
    scheduler.add_job(
        rolling_delete, "cron", day_of_week="sun", hour=5, id="backup_cleanup"
    )
