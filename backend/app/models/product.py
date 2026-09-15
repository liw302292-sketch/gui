"""产品与价格库、价格规则。"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, id_column, str_column, TimestampMixin


class ProductCategory(Base, TimestampMixin):
    __tablename__ = "product_categories"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    industry_id: Mapped[str] = mapped_column(String(50), default="advertising", nullable=False, index=True)
    name: Mapped[str] = str_column(100)
    code: Mapped[str | None] = str_column(50, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    industry_id: Mapped[str] = mapped_column(String(50), default="advertising", nullable=False, index=True)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    name: Mapped[str] = str_column(200, index=True)
    model: Mapped[str | None] = str_column(100, nullable=True)  # 型号
    spec: Mapped[str | None] = str_column(200, nullable=True)  # 规格
    unit: Mapped[str] = mapped_column(String(20), default="平方米", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    pricing_mode: Mapped[str] = mapped_column(String(30), default="area", nullable=False)
    # fixed / area / volume / weight / cost_plus / margin / tiered

    cost_price: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    default_price: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    min_price: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    loss_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)
    labor_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    labor_price_per_unit: Mapped[float] = mapped_column(Numeric(14, 4), default=0, nullable=False)
    transport_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    other_cost: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    min_profit_margin: Mapped[float] = mapped_column(Numeric(6, 4), default=0.25, nullable=False)
    markup_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0.35, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(6, 4), default=0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    category: Mapped[ProductCategory | None] = relationship(back_populates="products")


class PriceRule(Base, TimestampMixin):
    """报价规则：与 AI 完全解耦，价格只由规则引擎计算。"""

    __tablename__ = "price_rules"

    id = id_column()
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("product_categories.id", ondelete="CASCADE"), nullable=True, index=True
    )

    name: Mapped[str] = str_column(200)
    rule_type: Mapped[str] = mapped_column(String(30), default="area", nullable=False)
    # fixed | area | volume | weight | cost_plus | margin | loss | labor | transport | condition | tiered
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False, index=True)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

