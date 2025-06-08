from typing import Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Simple in-memory metrics storage
_total_requests: int = 0
_successful_requests: int = 0
_active_tokens: Set[str] = set()


def record_request(success: bool, token: Optional[str] = None) -> None:
    global _total_requests, _successful_requests
    _total_requests += 1
    if success:
        _successful_requests += 1
    if token:
        _active_tokens.add(token)


def get_metrics() -> dict:
    success_rate = (
        (_successful_requests / _total_requests * 100) if _total_requests else 0.0
    )
    return {
        "active_users": len(_active_tokens),
        "total_requests": _total_requests,
        "success_rate": round(success_rate, 2),
    }


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        token = request.headers.get("Authorization")
        if token and token.lower().startswith("bearer "):
            token = token.split()[1]
        else:
            token = None
        record_request(response.status_code < 500, token)
        return response
