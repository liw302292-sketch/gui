"""企业、成员、行业、系统设置。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, id_column, str_column, TimestampMixin


class Industry(Base, TimestampMixin):
    """行业模板注册表。第一版只开放 advertising，其余为未来扩展预留。"""

    __tablename__ = "industries"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = str_column(100)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id = id_column()
    name: Mapped[str] = str_column(200, index=True)
    short_name: Mapped[str | None] = str_column(100, nullable=True)
    industry_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("industries.id"), default="advertising", nullable=False, index=True
    )
    slug: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)

    # 企业 Logo 文件 ID。这里刻意不加外键约束：files 表反向依赖 companies，
    # 两者互相引用会形成循环外键，导致全新数据库无法按顺序建表。
    # Logo 的企业归属由 API 层校验（只能引用本企业文件）。
    logo_file_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contact_name: Mapped[str | None] = str_column(100, nullable=True)
    contact_phone: Mapped[str | None] = str_column(50, nullable=True)
    contact_wechat: Mapped[str | None] = str_column(80, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    credit_code: Mapped[str | None] = str_column(50, nullable=True)

    default_tax_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)
    default_profit_margin: Mapped[float] = mapped_column(Numeric(6, 4), default=0.3, nullable=False)
    default_quote_valid_days: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    default_payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_service_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_footer: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 报价取整规则：none / 1 / 10 / 100 / psychological
    rounding_mode: Mapped[str] = mapped_column(String(20), default="10", nullable=False)
    quote_no_prefix: Mapped[str] = mapped_column(String(20), default="Q", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)

    ai_monthly_quota: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False, index=True)
    onboarded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    members: Mapped[list["Member"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Member(Base, TimestampMixin):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("company_id", "user_id", name="uq_member_company_user"),)

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="owner", nullable=False)  # owner/admin/sales
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    nickname: Mapped[str | None] = str_column(100, nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    company: Mapped[Company] = relationship(back_populates="members")


class SystemSetting(Base, TimestampMixin):
    """管理员可编辑的运行期设置（数据库驱动，不允许写死代码）。"""

    __tablename__ = "system_settings"

    id = id_column()
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
