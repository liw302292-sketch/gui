"""报价、报价明细、版本、模板、访问记录。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, id_column, str_column, TimestampMixin, utcnow


class QuoteTemplate(Base, TimestampMixin):
    __tablename__ = "quote_templates"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    industry_id: Mapped[str] = mapped_column(String(50), default="advertising", nullable=False)
    name: Mapped[str] = str_column(200)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accent_color: Mapped[str] = mapped_column(String(20), default="#635BFF", nullable=False)
    show_tiers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_unit_price: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    footer: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Quote(Base, TimestampMixin):
    __tablename__ = "quotes"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    industry_id: Mapped[str] = mapped_column(String(50), default="advertising", nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("quote_templates.id", ondelete="SET NULL"), nullable=True
    )
    owner_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ai_task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ai_tasks.id", ondelete="SET NULL"), nullable=True)

    quote_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    project_name: Mapped[str] = str_column(200, default="未命名项目")
    customer_name: Mapped[str | None] = str_column(200, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    # draft / sent / viewed / following / won / void

    currency: Mapped[str] = mapped_column(String(10), default="CNY", nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False, index=True)
    total_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    gross_profit: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    gross_margin: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)

    tiers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirement_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)

    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    won_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    public_token: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    public_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    public_access_password_hash: Mapped[str | None] = str_column(255, nullable=True)
    allow_download: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_viewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    items: Mapped[list["QuoteItem"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan", order_by="QuoteItem.sort_order"
    )
    versions: Mapped[list["QuoteVersion"]] = relationship(
        back_populates="quote", cascade="all, delete-orphan", order_by="QuoteVersion.version_no.desc()"
    )
    views: Mapped[list["QuoteView"]] = relationship(back_populates="quote", cascade="all, delete-orphan")


class QuoteItem(Base, TimestampMixin):
    """报价明细：完整保存成本构成，保证价格可追溯“为什么是这个价格”。"""

    __tablename__ = "quote_items"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )

    plan_level: Mapped[str] = mapped_column(String(20), default="standard", nullable=False)
    # economy / standard / premium

    category_name: Mapped[str | None] = str_column(100, nullable=True)
    product_name: Mapped[str] = str_column(200)
    spec: Mapped[str | None] = str_column(200, nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="平方米", nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), default=1, nullable=False)
    width: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    height: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    depth: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    weight: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)

    unit_price: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    cost_price: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    material_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    loss_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)
    loss_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    labor_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    transport_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    other_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    profit_margin: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)
    final_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    rounding_adjustment: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    breakdown: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    match_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    quote: Mapped[Quote] = relationship(back_populates="items")


class QuoteVersion(Base, TimestampMixin):
    __tablename__ = "quote_versions"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    gross_margin: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)
    tiers: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    quote: Mapped[Quote] = relationship(back_populates="versions")


class QuoteView(Base, TimestampMixin):
    __tablename__ = "quote_views"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    ip_hash: Mapped[str | None] = str_column(64, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_type: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    referer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_first_view: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    quote: Mapped[Quote] = relationship(back_populates="views")
