import os
import sys
import logging
import warnings
import requests
from loguru import logger
from loguru_handler_loki import LokiHandler

# Sentry 연동
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

SENSITIVE_KEYS = {"ssn", "password", "email", "phone", "token"}

# 민감정보 마스킹 함수
def filter_sensitive(record):
    extra = record["extra"]
    for key in SENSITIVE_KEYS:
        if key in extra:
            extra[key] = "***MASKED***"
    record["extra"] = extra
    return record

# 슬랙 알림 sink 함수
def slack_notify(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return
    # 에러/예외만 전송
    if message.record["level"].name not in ("ERROR", "CRITICAL"): 
        return
    text = f"[Palantir-API][{message.record['level'].name}] {message.record['message']}\n{message.record['extra']}"
    try:
        requests.post(webhook_url, json={"text": text}, timeout=3)
    except Exception:
        pass

# Sentry sink 함수
def sentry_notify(message):
    if not SENTRY_AVAILABLE:
        return
    if message.record["level"].name not in ("ERROR", "CRITICAL"):
        return
    try:
        sentry_sdk.capture_message(f"{message.record['level'].name}: {message.record['message']}\n{message.record['extra']}")
    except Exception:
        pass

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # loguru 레벨 매핑
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logger():
    loki_url = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")
    handler = LokiHandler(
        url=loki_url,
        tags={"app": "palantir-api"},
        version="1",
        serialize=True,
    )
    logger.remove()
    logger.add(handler, serialize=True, patch=filter_sensitive)
    logger.add(sys.stderr, serialize=True, patch=filter_sensitive)
    # 슬랙 알림 sink 추가 (에러/예외만)
    logger.add(slack_notify, level="ERROR")
    # Sentry 연동
    sentry_dsn = os.getenv("SENTRY_DSN")
    if SENTRY_AVAILABLE and sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)
        logger.add(sentry_notify, level="ERROR")
        logger.info("Sentry 연동 활성화됨.")
    logger.info(f"Loki handler registered: {loki_url}")

    # 표준 logging → loguru로 리디렉션
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # warnings → loguru로 리디렉션
    def showwarning(message, category, filename, lineno, file=None, line=None):
        log_msg = warnings.formatwarning(message, category, filename, lineno, line)
        logger.warning(log_msg)
    warnings.showwarning = showwarning 