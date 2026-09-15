"""规则引擎输入输出契约（Pydantic，强校验）。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PricingMode = Literal["fixed", "area", "volume", "weight", "cost_plus", "margin", "tiered"]
PlanLevel = Literal["economy", "standard", "premium"]


class QuoteItemInput(BaseModel):
    """单个报价项的输入。尺寸单位统一为米，重量为千克。"""

    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    product_id: int | None = None
    product_name: str = "未命名产品"
    category_name: str | None = None
    spec: str | None = None
    unit: str = "平方米"
    pricing_mode: PricingMode | None = None

    quantity: Decimal = Decimal("1")
    width: Decimal | None = None
    height: Decimal | None = None
    depth: Decimal | None = None
    weight: Decimal | None = None

    unit_price: Decimal | None = None
    cost_price: Decimal | None = None
    loss_rate: Decimal | None = None
    labor_cost: Decimal | None = None
    labor_price_per_unit: Decimal | None = None
    transport_cost: Decimal | None = None
    other_cost: Decimal | None = None
    min_profit_margin: Decimal | None = None
    markup_rate: Decimal | None = None
    target_margin: Decimal | None = None
    tax_rate: Decimal | None = None

    plan_level: PlanLevel = "standard"
    remark: str | None = None
    match_confidence: float | None = None

    @field_validator("quantity")
    @classmethod
    def _positive_quantity(cls, value: Decimal) -> Decimal:
        if value is None or value <= 0:
            return Decimal("1")
        return value

    @field_validator("width", "height", "depth", "weight", mode="before")
    @classmethod
    def _clean_number(cls, value: Any) -> Any:
        if value in ("", "null", "None"):
            return None
        return value


class QuoteInput(BaseModel):
    """整单输入。"""

    model_config = ConfigDict(extra="ignore")

    items: list[QuoteItemInput] = Field(default_factory=list)
    rounding_mode: str = "10"
    global_margin: Decimal | None = None
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal | None = None
    tier_mode: PlanLevel = "standard"


class QuoteItemCalculation(BaseModel):
    """单行计算结果，保留全部明细，保证价格可追溯。"""

    product_id: int | None = None
    product_name: str
    category_name: str | None = None
    spec: str | None = None
    unit: str
    plan_level: PlanLevel = "standard"

    billable_quantity: Decimal
    quantity: Decimal
    width: Decimal | None = None
    height: Decimal | None = None
    depth: Decimal | None = None
    weight: Decimal | None = None

    unit_price: Decimal
    cost_price: Decimal
    material_cost: Decimal
    loss_rate: Decimal
    loss_cost: Decimal
    labor_cost: Decimal
    transport_cost: Decimal
    other_cost: Decimal
    total_cost: Decimal

    rule_price: Decimal
    margin_price: Decimal
    subtotal: Decimal
    profit_margin: Decimal
    gross_profit: Decimal
    final_price: Decimal
    rounding_adjustment: Decimal

    formula: str
    applied_rules: list[str] = Field(default_factory=list)
    breakdown: dict[str, Any] = Field(default_factory=dict)
    remark: str | None = None
    match_confidence: float | None = None


class QuoteCalculation(BaseModel):
    """整单计算结果。"""

    items: list[QuoteItemCalculation] = Field(default_factory=list)
    subtotal: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    gross_profit: Decimal = Decimal("0")
    gross_margin: Decimal = Decimal("0")
    currency: str = "CNY"
    rounding_mode: str = "10"


class PlanTierResult(BaseModel):
    """经济/标准/高级三档方案。"""

    level: PlanLevel
    name: str
    total_amount: Decimal
    total_cost: Decimal
    gross_margin: Decimal
    items: list[QuoteItemCalculation] = Field(default_factory=list)

