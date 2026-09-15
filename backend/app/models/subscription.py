"""套餐、订单、订阅。套餐完全由数据库驱动，不写死。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, id_column, str_column, TimestampMixin


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id = id_column()
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    name: Mapped[str] = str_column(100)
    tagline: Mapped[str | None] = str_column(200, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(20), default="year", nullable=False)  # month/year/forever
    max_users: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_quotes: Mapped[int] = mapped_column(Integer, default=20, nullable=False)  # 每月报价数，0 = 不限
    ai_quota: Mapped[int] = mapped_column(Integer, default=50, nullable=False)  # 每月 AI 调用额度，0 = 不限
    storage_quota_mb: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    features: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id = id_column()
    order_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    plan_code: Mapped[str] = str_column(30, default="")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), default="mock", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    # pending/paid/failed/refunded/cancelled
    external_trade_no: Mapped[str | None] = str_column(120, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    # active / expired / cancelled
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

