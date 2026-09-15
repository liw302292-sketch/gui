"""产品、分类、价格规则 Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    code: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    code: str | None = None
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True
    product_count: int = 0


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category_id: int | None = None
    model: str | None = Field(default=None, max_length=100)
    spec: str | None = Field(default=None, max_length=200)
    unit: str = Field(default="平方米", max_length=20)
    description: str | None = None
    remark: str | None = None
    pricing_mode: str = Field(default="area", pattern="^(fixed|area|volume|weight|cost_plus|margin|tiered)$")
    cost_price: float = Field(default=0, ge=0)
    default_price: float = Field(default=0, ge=0)
    min_price: float = Field(default=0, ge=0)
    loss_rate: float = Field(default=0, ge=0, le=1)
    labor_cost: float = Field(default=0, ge=0)
    labor_price_per_unit: float = Field(default=0, ge=0)
    transport_cost: float = Field(default=0, ge=0)
    other_cost: float = Field(default=0, ge=0)
    min_profit_margin: float = Field(default=0.25, ge=0, le=0.95)
    markup_rate: float = Field(default=0.35, ge=0, le=5)
    tax_rate: float = Field(default=0, ge=0, le=1)
    is_active: bool = True
    sort_order: int = 0
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    category_id: int | None = None
    model: str | None = None
    spec: str | None = None
    unit: str | None = None
    description: str | None = None
    remark: str | None = None
    pricing_mode: str | None = None
    cost_price: float | None = Field(default=None, ge=0)
    default_price: float | None = Field(default=None, ge=0)
    min_price: float | None = Field(default=None, ge=0)
    loss_rate: float | None = Field(default=None, ge=0, le=1)
    labor_cost: float | None = Field(default=None, ge=0)
    labor_price_per_unit: float | None = Field(default=None, ge=0)
    transport_cost: float | None = Field(default=None, ge=0)
    other_cost: float | None = Field(default=None, ge=0)
    min_profit_margin: float | None = Field(default=None, ge=0, le=0.95)
    markup_rate: float | None = Field(default=None, ge=0, le=5)
    tax_rate: float | None = Field(default=None, ge=0, le=1)
    is_active: bool | None = None
    sort_order: int | None = None
    attributes: dict[str, Any] | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    category_id: int | None = None
    category_name: str | None = None
    model: str | None = None
    spec: str | None = None
    unit: str
    pricing_mode: str
    cost_price: float
    default_price: float
    min_price: float = 0
    loss_rate: float = 0
    labor_cost: float = 0
    labor_price_per_unit: float = 0
    transport_cost: float = 0
    other_cost: float = 0
    min_profit_margin: float = 0.25
    markup_rate: float = 0.35
    tax_rate: float = 0
    gross_margin_preview: float = 0
    is_active: bool = True
    remark: str | None = None
    created_at: datetime | None = None


class PriceRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    product_id: int | None = None
    category_id: int | None = None
    rule_type: str = Field(
        default="area",
        pattern="^(fixed|area|volume|weight|cost_plus|margin|loss|labor|transport|condition|tiered)$",
    )
    priority: int = Field(default=100, ge=0, le=9999)
    conditions: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def _check_scope(self) -> "PriceRuleCreate":
        if self.product_id and self.category_id:
            raise ValueError("规则只能绑定产品或分类其中之一")
        return self


class PriceRuleUpdate(BaseModel):
    name: str | None = None
    product_id: int | None = None
    category_id: int | None = None
    rule_type: str | None = None
    priority: int | None = None
    conditions: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    description: str | None = None
    is_active: bool | None = None


class PriceRuleOut(BaseModel):
    id: int
    name: str
    product_id: int | None = None
    product_name: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    rule_type: str
    priority: int
    conditions: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

