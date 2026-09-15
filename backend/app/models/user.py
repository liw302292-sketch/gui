"""用户账号。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, id_column, str_column, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = id_column()
    email: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True, index=True)
    name: Mapped[str] = str_column(100, default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = str_column(500, nullable=True)

    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 预留微信登录结构（第一版不强依赖）
    wechat_openid: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    wechat_unionid: Mapped[str | None] = mapped_column(String(120), nullable=True)

