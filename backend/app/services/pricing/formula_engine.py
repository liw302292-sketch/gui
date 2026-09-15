"""公式引擎：把“产品 + 数量 + 尺寸 + 单位”换算成计价数量与成本构成。

支持的计价方式：
  fixed      固定单价       数量 × 单价
  area       面积           宽 × 高 × 数量 × 单价
  volume     体积           长 × 宽 × 高 × 数量 × 单价
  weight     重量           重量 × 数量 × 单价
  cost_plus  成本加成       成本 × (1 + 加价率)
  margin     毛利率         售价 = 成本 / (1 - 毛利率)
  tiered     条件/阶梯价    由 rule_matcher 决定单价后按面积/数量计价
"""

from __future__ import annotations

from decimal import Decimal

from app.services.pricing.schemas import QuoteItemInput

ZERO = Decimal("0")
ONE = Decimal("1")

ROUNDING = Decimal("0.01")


def d(value: Decimal | float | int | str | None, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def money(value: Decimal) -> Decimal:
    """金额统一保留两位小数（四舍五入）。"""
    return value.quantize(ROUNDING, rounding="ROUND_HALF_UP")


def infer_pricing_mode(item: QuoteItemInput) -> str:
    """未显式指定时，按尺寸信息推断最合理的计价方式。"""
    if item.pricing_mode:
        return item.pricing_mode
    if item.weight and not (item.width and item.height):
        return "weight"
    if item.width and item.height and item.depth:
        return "volume"
    if item.width and item.height:
        return "area"
    return "fixed"


def billable_quantity(item: QuoteItemInput, mode: str) -> tuple[Decimal, str]:
    """返回（计价数量，公式说明）。"""
    quantity = d(item.quantity, "1")
    width = d(item.width)
    height = d(item.height)
    depth = d(item.depth)
    weight = d(item.weight)

    if mode == "area":
        area = width * height
        if area <= 0:
            return quantity, f"{quantity} 件（未提供尺寸，按数量计价）"
        return area * quantity, f"{fmt(width)}m × {fmt(height)}m × {fmt(quantity)} = {fmt(area * quantity)} {item.unit}"

    if mode == "volume":
        volume = width * height * depth
        if volume <= 0:
            return quantity, f"{quantity} 件（未提供完整尺寸，按数量计价）"
        return (
            volume * quantity,
            f"{fmt(width)}m × {fmt(height)}m × {fmt(depth)}m × {fmt(quantity)} = {fmt(volume * quantity)} {item.unit}",
        )

    if mode == "weight":
        if weight <= 0:
            return quantity, f"{quantity} 件（未提供重量，按数量计价）"
        return weight * quantity, f"{fmt(weight)}kg × {fmt(quantity)} = {fmt(weight * quantity)} kg"

    return quantity, f"{fmt(quantity)} {item.unit}"


def fmt(value: Decimal) -> str:
    """去掉无意义的小数尾零，用于公式展示。"""
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def labor_cost_for(item: QuoteItemInput, billable: Decimal) -> tuple[Decimal, str | None]:
    """人工费：固定人工费 + 按计价单位的人工单价。"""
    fixed = d(item.labor_cost)
    per_unit = d(item.labor_price_per_unit)
    if per_unit > 0:
        total = fixed + per_unit * billable
        note = f"固定人工 {fmt(fixed)} + {fmt(per_unit)}/{item.unit} × {fmt(billable)} = {fmt(total)}"
        return money(total), note
    if fixed > 0:
        return money(fixed), f"固定人工费 {fmt(fixed)}"
    return ZERO, None


def transport_cost_for(item: QuoteItemInput, quantity: Decimal) -> tuple[Decimal, str | None]:
    """运输费：支持固定运输费，也支持 rule_matcher 注入的按公里/按趟结果。"""
    fixed = d(item.transport_cost)
    if fixed > 0:
        return money(fixed), f"运输费 {fmt(fixed)}"
    return ZERO, None

