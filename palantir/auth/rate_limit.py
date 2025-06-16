import time
from collections import defaultdict

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_counts = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # 인증 관련 엔드포인트만 레이트 리미팅 적용
        if not request.url.path.startswith("/auth/"):
            return await call_next(request)

        client_ip = request.client.host
        now = time.time()

        # 1분 이내의 요청만 유지
        self.request_counts[client_ip] = [
            timestamp
            for timestamp in self.request_counts[client_ip]
            if now - timestamp < 60
        ]

        # 요청 수 확인
        if len(self.request_counts[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요."
                },
            )

        # 현재 요청 추가
        self.request_counts[client_ip].append(now)

        return await call_next(request)
