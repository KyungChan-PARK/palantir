"""메인 애플리케이션 모듈."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from palantir.core.api import router as api_router
from palantir.core.config import settings
from palantir.core.database import init_db
from palantir.core.docs import setup_docs
from palantir.core.security import RateLimitMiddleware, SecurityMiddleware

# 로깅 설정
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url=None,  # Swagger UI 비활성화 (커스텀 경로 사용)
    redoc_url=None  # ReDoc 비활성화 (커스텀 경로 사용)
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# 보안 미들웨어 설정
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
    period=settings.RATE_LIMIT_PERIOD
)

# API 라우터 등록
app.include_router(api_router, prefix=settings.API_PREFIX)

# API 문서 설정
setup_docs(app)

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트."""
    logger.info("애플리케이션 시작")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트."""
    logger.info("애플리케이션 종료")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트."""
    return {"status": "healthy"}
