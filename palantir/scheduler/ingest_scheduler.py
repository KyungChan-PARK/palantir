from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional, Dict, Any
import logging

from ..ingest.document_ingester import DocumentIngester

logger = logging.getLogger(__name__)

class IngestScheduler:
    def __init__(self):
        """문서 수집 스케줄러 초기화"""
        self.scheduler = BackgroundScheduler()
        self.ingester = DocumentIngester()
        
    def start(self):
        """스케줄러 시작"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("문서 수집 스케줄러가 시작되었습니다.")
            
    def stop(self):
        """스케줄러 중지"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("문서 수집 스케줄러가 중지되었습니다.")
            
    def schedule_directory_ingest(self, directory: str,
                                schedule: str = "0 3 * * *",  # 매일 새벽 3시
                                metadata: Optional[Dict[str, Any]] = None,
                                file_types: Optional[list[str]] = None) -> None:
        """
        디렉토리 수집 작업 스케줄링
        
        Args:
            directory: 감시할 디렉토리
            schedule: Cron 형식 스케줄 (기본값: 매일 새벽 3시)
            metadata: 공통 메타데이터
            file_types: 처리할 파일 확장자 목록
        """
        def ingest_job():
            try:
                logger.info(f"디렉토리 수집 시작: {directory}")
                self.ingester.ingest_directory(directory, metadata, file_types)
                logger.info("디렉토리 수집 완료")
            except Exception as e:
                logger.error(f"디렉토리 수집 중 오류 발생: {str(e)}")
        
        # 작업 스케줄링
        self.scheduler.add_job(
            ingest_job,
            trigger=CronTrigger.from_crontab(schedule),
            id=f"ingest_{directory}",
            replace_existing=True
        )
        logger.info(f"디렉토리 수집 작업이 스케줄링되었습니다: {directory} (스케줄: {schedule})")
        
    def schedule_file_ingest(self, file_path: str,
                           schedule: str = "0 3 * * *",  # 매일 새벽 3시
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        단일 파일 수집 작업 스케줄링
        
        Args:
            file_path: 감시할 파일
            schedule: Cron 형식 스케줄
            metadata: 추가 메타데이터
        """
        def ingest_job():
            try:
                logger.info(f"파일 수집 시작: {file_path}")
                self.ingester.ingest_file(file_path, metadata)
                logger.info("파일 수집 완료")
            except Exception as e:
                logger.error(f"파일 수집 중 오류 발생: {str(e)}")
        
        # 작업 스케줄링
        self.scheduler.add_job(
            ingest_job,
            trigger=CronTrigger.from_crontab(schedule),
            id=f"ingest_{file_path}",
            replace_existing=True
        )
        logger.info(f"파일 수집 작업이 스케줄링되었습니다: {file_path} (스케줄: {schedule})") 