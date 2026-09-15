"""认证 Cookie 管理：HttpOnly + SameSite=Lax，兼顾安全与同源代理场景。"""

from __future__ import annotations

from fastapi import Response

from app.core.config import settings
from app.core.deps import ACCESS_COOKIE, REFRESH_COOKIE


def set_auth_cookies(response: Response, *, access_token: str, refresh_token: str, remember: bool = True) -> None:
    secure = settings.is_production
    max_age = settings.refresh_token_expire_days * 24 * 3600 if remember else None
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")

