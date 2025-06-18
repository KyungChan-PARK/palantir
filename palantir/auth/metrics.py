from prometheus_client import Counter, Histogram
from typing import Optional

# Authentication metrics
AUTH_LOGIN_ATTEMPTS = Counter(
    "auth_login_attempts_total",
    "Total number of login attempts",
    ["status"]  # success/failure
)

AUTH_REGISTRATION_ATTEMPTS = Counter(
    "auth_registration_attempts_total",
    "Total number of registration attempts",
    ["status"]  # success/failure
)

AUTH_TOKEN_VALIDATION = Counter(
    "auth_token_validation_total",
    "Total number of token validation attempts",
    ["status"]  # success/failure/expired
)

# Authorization metrics
AUTH_PERMISSION_CHECKS = Counter(
    "auth_permission_checks_total",
    "Total number of permission checks",
    ["status", "permission"]  # granted/denied, permission name
)

AUTH_ROLE_UPDATES = Counter(
    "auth_role_updates_total",
    "Total number of role updates",
    ["status", "role"]  # success/failure, role name
)

# Performance metrics
AUTH_REQUEST_DURATION = Histogram(
    "auth_request_duration_seconds",
    "Time spent processing auth requests",
    ["endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)


def record_login_attempt(success: bool):
    """Record a login attempt."""
    status = "success" if success else "failure"
    AUTH_LOGIN_ATTEMPTS.labels(status=status).inc()


def record_registration_attempt(success: bool):
    """Record a registration attempt."""
    status = "success" if success else "failure"
    AUTH_REGISTRATION_ATTEMPTS.labels(status=status).inc()


def record_token_validation(status: str):
    """Record a token validation attempt."""
    AUTH_TOKEN_VALIDATION.labels(status=status).inc()


def record_permission_check(granted: bool, permission: str):
    """Record a permission check."""
    status = "granted" if granted else "denied"
    AUTH_PERMISSION_CHECKS.labels(status=status, permission=permission).inc()


def record_role_update(success: bool, role: str):
    """Record a role update."""
    status = "success" if success else "failure"
    AUTH_ROLE_UPDATES.labels(status=status, role=role).inc()


class AuthMetricsMiddleware:
    """Middleware to record auth request durations."""
    
    async def __call__(self, request, call_next):
        if not request.url.path.startswith("/auth/"):
            return await call_next(request)
            
        with AUTH_REQUEST_DURATION.labels(
            endpoint=request.url.path
        ).time():
            response = await call_next(request)
            
        return response 