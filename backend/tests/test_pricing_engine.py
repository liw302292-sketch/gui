"""验收 9：规则引擎计算正确（固定/面积/体积/重量/成本加成/毛利率/损耗/人工/运输/取整）。"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.pricing.pricing_engine import pricing_engine
from app.services.pricing.profit_calculator import apply_rounding, effective_margin, price_by_margin
from app.services.pricing.schemas import QuoteInput, QuoteItemInput


def test_fixed_price_calculation():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="发光字", unit="个", pricing_mode="fixed", quantity=12, unit_price=100, cost_price=40
        ),
    )
    assert result.billable_quantity == Decimal("12")
    assert result.rule_price == Decimal("1200.00")
    assert result.material_cost == Decimal("480.00")
    assert result.final_price == Decimal("1200.00")


def test_area_price_calculation():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="铝塑板门头",
            unit="平方米",
            pricing_mode="area",
            width=10,
            height=1.5,
            quantity=1,
            unit_price=200,
            cost_price=100,
            loss_rate=0.05,
            min_profit_margin=0.2,
        ),
    )
    assert result.billable_quantity == Decimal("15.0")
    assert result.material_cost == Decimal("1500.00")
    assert result.loss_cost == Decimal("75.00")
    assert result.total_cost == Decimal("1575.00")
    assert result.rule_price == Decimal("3000.00")
    assert result.final_price == Decimal("3000.00")


def test_volume_price_calculation():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="立体箱体",
            unit="立方米",
            pricing_mode="volume",
            width=1,
            height=1,
            depth=0.5,
            quantity=2,
            unit_price=1000,
            cost_price=400,
        ),
    )
    assert result.billable_quantity == Decimal("1.0")
    assert result.rule_price == Decimal("1000.00")


def test_weight_price_calculation():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="钢材", unit="公斤", pricing_mode="weight", weight=50, quantity=2, unit_price=8, cost_price=5
        ),
    )
    assert result.billable_quantity == Decimal("100.0")
    assert result.rule_price == Decimal("800.00")


def test_cost_plus_pricing():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="定制件",
            unit="项",
            pricing_mode="cost_plus",
            quantity=1,
            cost_price=1000,
            markup_rate=0.4,
            min_profit_margin=0.2,
            unit_price=0,
        ),
    )
    assert result.total_cost == Decimal("1000.00")
    assert result.final_price == Decimal("1400.00")


def test_margin_pricing_keeps_min_margin():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="低毛利产品",
            unit="项",
            pricing_mode="margin",
            quantity=1,
            unit_price=100,
            cost_price=900,
            min_profit_margin=0.3,
        ),
    )
    assert result.margin_price == Decimal("1285.71")
    assert result.final_price >= result.margin_price
    assert result.profit_margin >= Decimal("0.30")


def test_labor_transport_and_other_costs():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="门头",
            unit="平方米",
            pricing_mode="area",
            width=10,
            height=2,
            quantity=1,
            unit_price=300,
            cost_price=100,
            labor_price_per_unit=50,
            labor_cost=200,
            transport_cost=300,
            other_cost=100,
        ),
    )
    assert result.material_cost == Decimal("2000.00")
    assert result.labor_cost == Decimal("1200.00")
    assert result.transport_cost == Decimal("300.00")
    assert result.other_cost == Decimal("100.00")
    assert result.total_cost == Decimal("3600.00")


@pytest.mark.parametrize(
    ("mode", "expected"),
    [("1", "10858.00"), ("10", "10860.00"), ("100", "10900.00"), ("psychological", "10880.00")],
)
def test_rounding_rules(mode: str, expected: str):
    rounded, adjustment = apply_rounding(Decimal("10857.14"), mode)
    assert rounded == Decimal(expected)
    assert rounded >= Decimal("10857.14")
    assert adjustment >= 0


def test_margin_helpers():
    assert price_by_margin(Decimal("700"), Decimal("0.3")) == Decimal("1000.00")
    assert effective_margin(Decimal("1000"), Decimal("700")) == Decimal("0.3000")


def test_quote_level_totals_and_tiers():
    payload = QuoteInput(
        items=[
            QuoteItemInput(
                product_name="门头", unit="平方米", pricing_mode="area", width=10, height=1.5, unit_price=280, cost_price=145
            ),
            QuoteItemInput(
                product_name="发光字", unit="个", pricing_mode="fixed", quantity=12, unit_price=95, cost_price=45
            ),
        ],
        rounding_mode="10",
    )
    calculation = pricing_engine.calculate(None, None, payload)
    assert calculation.total_amount > 0
    assert calculation.total_cost > 0
    assert calculation.gross_margin > Decimal("0.2")

    tiers = pricing_engine.calculate_tiers(None, None, payload)
    assert tiers["economy"].total_amount < tiers["standard"].total_amount < tiers["premium"].total_amount


def test_formula_trace_is_explainable():
    result = pricing_engine.calculate_item(
        None,
        None,
        QuoteItemInput(
            product_name="门头", unit="平方米", pricing_mode="area", width=10, height=1.55,
            unit_price=280, cost_price=145, loss_rate=0.06, labor_price_per_unit=55, min_profit_margin=0.28,
        ),
    )
    assert "计价数量" in result.formula
    assert "材料成本" in result.formula
    assert "总成本" in result.formula
    assert result.breakdown["mode"] == "area"
    assert Decimal(result.breakdown["total_cost"]) == result.total_cost

