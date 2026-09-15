"""客户、跟进记录、站内通知。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, id_column, str_column, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = str_column(200, index=True)  # 公司名称
    contact_name: Mapped[str | None] = str_column(100, nullable=True)
    phone: Mapped[str | None] = str_column(50, nullable=True, index=True)
    wechat: Mapped[str | None] = str_column(80, nullable=True)
    source: Mapped[str | None] = str_column(50, nullable=True)  # 转介绍/微信/电话/自然到访
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False, index=True)
    owner_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    quote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    followups: Mapped[list["Followup"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", order_by="Followup.created_at.desc()"
    )


class Followup(Base, TimestampMixin):
    __tablename__ = "followups"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    quote_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("quotes.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="communicating", nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), default="wechat", nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="followups")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="system", nullable=False)
    title: Mapped[str] = str_column(200)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = str_column(300, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

