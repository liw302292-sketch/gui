"""密码哈希、JWT 签发校验、CSRF/可信来源校验。"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import AuthError

TokenType = Literal["access", "refresh"]


# --------------------------------------------------------------------------
# 密码
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def password_strength_error(password: str) -> str | None:
    if len(password) < 8:
        return "密码至少需要 8 位"
    if not any(ch.isdigit() for ch in password):
        return "密码需要包含数字"
    if not any(ch.isalpha() for ch in password):
        return "密码需要包含字母"
    return None


# --------------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------------
def create_token(
    subject: str | int,
    token_type: TokenType,
    *,
    company_id: int | None = None,
    role: str = "member",
    extra: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    if token_type == "access":
        expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    else:
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": secrets.token_urlsafe(12),
        "company_id": company_id,
        "role": role,
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def decode_token(token: str, *, expected_type: TokenType | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("登录状态已过期，请重新登录", code="token_expired") from exc
    except jwt.PyJWTError as exc:
        raise AuthError("登录凭证无效，请重新登录", code="token_invalid") from exc
    if expected_type and payload.get("type") != expected_type:
        raise AuthError("登录凭证类型不正确", code="token_type_mismatch")
    return payload


# --------------------------------------------------------------------------
# Token / 签名工具
# --------------------------------------------------------------------------
def generate_public_token(length: int = 32) -> str:
    """公开报价链接 token：URL 安全、不可预测，绝不暴露数据库 ID。"""
    return secrets.token_urlsafe(length)


def sign_payload(payload: str) -> str:
    return hmac.new(settings.app_secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def safe_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode(), right.encode())


def csrf_token_for(session_id: str) -> str:
    return sign_payload(f"csrf::{session_id}")


def verify_csrf(session_id: str, token: str) -> bool:
    return safe_compare(csrf_token_for(session_id), token)

