"""利润、利润率与取整规则计算。"""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Any

from app.services.pricing.formula_engine import ZERO, money


def _decimal(value: Any) -> Decimal:
    """统一转 Decimal：避免 float / int / str 混用导致精度或类型错误。"""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def price_by_margin(cost: Any, margin: Any) -> Decimal:
    """毛利率定价：售价 = 成本 / (1 - 毛利率)。"""
    cost = _decimal(cost)
    margin = _decimal(margin)
    margin = max(min(margin, Decimal("0.95")), ZERO)
    if cost <= 0:
        return ZERO
    return money(cost / (Decimal("1") - margin))


def price_by_markup(cost: Any, markup: Any) -> Decimal:
    """成本加成定价：成本 × (1 + 加价率)。"""
    cost = _decimal(cost)
    markup = _decimal(markup)
    if cost <= 0:
        return ZERO
    return money(cost * (Decimal("1") + markup))


def effective_margin(price: Any, cost: Any) -> Decimal:
    """实际毛利率 = （售价 - 成本）/ 售价。"""
    price = _decimal(price)
    cost = _decimal(cost)
    if price <= 0:
        return ZERO
    return ((price - cost) / price).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def apply_rounding(amount: Decimal, mode: str) -> tuple[Decimal, Decimal]:
    """返回（取整后金额，取整差额）。"""
    if amount <= 0:
        return ZERO, ZERO

    step_map = {
        "none": Decimal("0.01"),
        "1": Decimal("1"),
        "yuan": Decimal("1"),
        "10": Decimal("10"),
        "100": Decimal("100"),
    }

    if mode == "psychological":
        # 心理价：向上取到整百后 -20，例如 10857 → 10880
        hundreds = (amount / Decimal("100")).to_integral_value(rounding=ROUND_CEILING) * Decimal("100")
        candidate = hundreds - Decimal("20")
        if candidate < amount:
            candidate = hundreds + Decimal("80")
        return candidate, candidate - amount

    step = step_map.get(mode, Decimal("10"))
    rounded = (amount / step).to_integral_value(rounding=ROUND_CEILING) * step
    return money(rounded), money(rounded - amount)


def tier_margin_delta(level: str) -> Decimal:
    """经济版/标准版/高级版的利润率调整。"""
    return {
        "economy": Decimal("-0.06"),
        "standard": Decimal("0"),
        "premium": Decimal("0.08"),
    }.get(level, Decimal("0"))


def tier_price_factor(level: str) -> Decimal:
    """经济版/标准版/高级版的售价系数。

    经济版改用更经济的材料与工艺，高级版使用更高规格配置，
    因此三档方案的价格必须有实质差异，而不是同一个价格的文字游戏。
    """
    return {
        "economy": Decimal("0.90"),
        "standard": Decimal("1.00"),
        "premium": Decimal("1.12"),
    }.get(level, Decimal("1"))


def clamp_margin(margin: Decimal, floor: Decimal = Decimal("0.05")) -> Decimal:
    """保证利润率不会低到亏本区间。"""
    return max(margin, floor)
