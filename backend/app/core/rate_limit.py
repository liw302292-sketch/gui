"""限流与登录失败保护。Redis 可用时用 Redis，否则用进程内计数。"""

from __future__ import annotations

import hashlib
import time

from fastapi import Request

from app.core.config import settings
from app.core.errors import AppError
from app.core.redis_client import get_store


class RateLimitedError(AppError):
    status_code = 429
    code = "rate_limited"
    message = "操作过于频繁，请稍后再试"


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def hash_ip(ip: str) -> str:
    return hashlib.sha256(f"quote-engine::{ip}".encode()).hexdigest()[:32]


def _hit(key: str, limit: int, window: int = 60) -> tuple[bool, int]:
    store = get_store()
    count = store.incr(key)
    if count == 1:
        store.expire(key, window)
    return count <= limit, count


def enforce_rate_limit(request: Request, *, bucket: str, limit: int | None = None, window: int = 60) -> None:
    limit = limit or settings.rate_limit_per_minute
    key = f"rl:{bucket}:{hash_ip(client_ip(request))}:{int(time.time() // window)}"
    allowed, count = _hit(key, limit, window)
    if not allowed:
        raise RateLimitedError(f"操作过于频繁（每分钟上限 {limit} 次），请稍后再试")


def enforce_ai_rate_limit(request: Request) -> None:
    enforce_rate_limit(request, bucket="ai", limit=settings.ai_rate_limit_per_minute)


def register_login_failure(identifier: str) -> int:
    store = get_store()
    key = f"login_fail:{hashlib.sha256(identifier.encode()).hexdigest()}"
    count = store.incr(key)
    if count == 1:
        store.expire(key, settings.login_lockout_minutes * 60)
    return count


def is_login_locked(identifier: str) -> bool:
    store = get_store()
    key = f"login_fail:{hashlib.sha256(identifier.encode()).hexdigest()}"
    value = store.get(key)
    return bool(value and int(value) >= settings.login_max_failures)


def clear_login_failures(identifier: str) -> None:
    store = get_store()
    key = f"login_fail:{hashlib.sha256(identifier.encode()).hexdigest()}"
    store.delete(key)

