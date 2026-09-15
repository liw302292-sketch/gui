"""报价规则引擎编排层。

计算链路：
  1. 规则匹配（产品 / 分类 / 通用规则）
  2. 公式计算（计价数量、材料成本、损耗、人工、运输、其他）
  3. 定价（规则价 / 成本加成 / 毛利率，取对客户与对企业都合理的价格）
  4. 利润率校验与取整
  5. 输出完整明细，保证“为什么是这个价格”可追溯
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.services.pricing import formula_engine as fe
from app.services.pricing.profit_calculator import (
    apply_rounding,
    clamp_margin,
    effective_margin,
    price_by_margin,
    price_by_markup,
    tier_margin_delta,
    tier_price_factor,
)
from app.services.pricing.rule_matcher import apply_rules, find_product, load_rules
from app.services.pricing.schemas import (
    PlanTierResult,
    QuoteCalculation,
    QuoteInput,
    QuoteItemCalculation,
    QuoteItemInput,
)

ZERO = Decimal("0")

TIER_NAMES = {"economy": "经济版", "standard": "标准版", "premium": "高级版"}


class PricingEngine:
    """无状态规则引擎。所有输入显式传入，便于单元测试。"""

    def calculate_item(
        self,
        db: Session | None,
        company_id: int | None,
        item: QuoteItemInput,
        *,
        rounding_mode: str = "10",
        global_margin: Decimal | None = None,
        tier: str = "standard",
    ) -> QuoteItemCalculation:
        product = None
        category = None
        match_confidence = item.match_confidence
        applied_rules: list[str] = []

        # ---------- 1. 产品匹配 + 规则匹配 ----------
        mode = fe.infer_pricing_mode(item)
        outcome = None
        if db is not None and company_id is not None:
            matched = find_product(
                db,
                company_id,
                product_name=item.product_name,
                category_name=item.category_name,
                product_id=item.product_id,
            )
            product = matched.product
            category = matched.category
            if match_confidence is None:
                match_confidence = matched.confidence
            applied_rules.append(matched.reason)

            rules = load_rules(
                db,
                company_id,
                product.id if product else None,
                category.id if category else None,
            )
            context = {
                "area": (item.width or ZERO) * (item.height or ZERO),
                "quantity": item.quantity,
                "width": item.width or ZERO,
                "height": item.height or ZERO,
                "depth": item.depth or ZERO,
                "weight": item.weight or ZERO,
            }
            outcome = apply_rules(rules, context)
            applied_rules.extend(outcome.applied)

        # ---------- 2. 生效参数：显式输入 > 规则 > 产品 > 兜底 ----------
        def pick(explicit: Decimal | None, rule_value: Decimal | None, product_value: Any, default: str = "0") -> Decimal:
            if explicit is not None:
                return fe.d(explicit)
            if rule_value is not None:
                return fe.d(rule_value)
            if product is not None and product_value is not None:
                return fe.d(getattr(product, product_value))
            return fe.d(default)

        # 计价方式优先级：需求显式指定 > 价格规则 > 产品设置 > 按尺寸推断
        # 产品设了「按个计价」，即使需求里带了尺寸也不能被误判成按面积计价。
        if item.pricing_mode is None:
            if outcome is not None and outcome.pricing_mode:
                mode = outcome.pricing_mode
            elif product is not None and product.pricing_mode:
                mode = product.pricing_mode
        billable, quantity_formula = fe.billable_quantity(item, mode)

        unit_price = pick(item.unit_price, outcome.unit_price if outcome else None, "default_price")
        cost_price = pick(item.cost_price, outcome.cost_price if outcome else None, "cost_price")
        loss_rate = pick(item.loss_rate, outcome.loss_rate if outcome else None, "loss_rate")
        if item.loss_rate is None and (outcome is None or outcome.loss_rate is None) and product is not None:
            loss_rate = fe.d(product.loss_rate)
        labor_price_per_unit = pick(
            item.labor_price_per_unit,
            outcome.labor_price_per_unit if outcome else None,
            "labor_price_per_unit",
        )
        fixed_labor = pick(item.labor_cost, outcome.labor_cost if outcome else None, "labor_cost")
        transport = pick(item.transport_cost, outcome.transport_cost if outcome else None, "transport_cost")
        other = pick(item.other_cost, outcome.other_cost if outcome else None, "other_cost")
        min_margin = pick(
            item.min_profit_margin, outcome.min_profit_margin if outcome else None, "min_profit_margin", "0.25"
        )
        markup = pick(item.markup_rate, outcome.markup_rate if outcome else None, "markup_rate", "0.35")

        # ---------- 3. 成本结构 ----------
        material_cost = fe.money(billable * cost_price)
        loss_cost = fe.money(material_cost * loss_rate)
        labor_item = item.model_copy(update={"labor_cost": fixed_labor, "labor_price_per_unit": labor_price_per_unit})
        labor_cost, labor_note = fe.labor_cost_for(labor_item, billable)
        transport_cost, transport_note = fe.transport_cost_for(item.model_copy(update={"transport_cost": transport}), billable)
        other_cost = fe.money(other)
        total_cost = material_cost + loss_cost + labor_cost + transport_cost + other_cost

        # ---------- 4. 定价 ----------
        rule_price = fe.money(billable * unit_price)
        target_margin = clamp_margin(
            (item.target_margin if item.target_margin is not None else (global_margin if global_margin is not None else min_margin))
            + tier_margin_delta(tier)
        )

        # 定价方式严格按产品/规则配置执行，然后用保底毛利率兜底：
        #   成本加成 → 成本 × (1 + 加价率)
        #   毛利率   → 成本 / (1 - 毛利率)
        #   其余     → 计价数量 × 单价（固定/面积/体积/重量）
        if mode == "cost_plus" and total_cost > 0:
            base_price = price_by_markup(total_cost, markup)
            chosen_name = f"成本加成 {fe.fmt(markup * 100)}%"
        elif (mode == "margin" or rule_price <= 0) and total_cost > 0:
            base_price = price_by_margin(total_cost, target_margin)
            chosen_name = f"毛利率 {fe.fmt(target_margin * 100)}%"
        else:
            base_price = rule_price if rule_price > 0 else fe.money(billable * unit_price)
            chosen_name = "计价数量 × 单价"

        tier_factor = tier_price_factor(tier)
        if tier_factor != Decimal("1"):
            base_price = fe.money(base_price * tier_factor)

        margin_price = price_by_margin(total_cost, target_margin) if total_cost > 0 else ZERO
        raw_price = max(base_price, margin_price, ZERO)
        final_price, rounding_adjustment = apply_rounding(raw_price, rounding_mode)
        profit_margin = effective_margin(final_price, total_cost)

        formula_parts = [
            f"计价数量：{quantity_formula}",
            f"单价：{fe.fmt(unit_price)} 元/{item.unit}",
            f"材料成本 {fe.fmt(material_cost)} = {fe.fmt(billable)} × {fe.fmt(cost_price)}",
        ]
        if loss_cost > 0:
            formula_parts.append(f"损耗 {fe.fmt(loss_cost)} = 材料成本 × {fe.fmt(loss_rate * 100)}%")
        if labor_note:
            formula_parts.append(f"人工：{labor_note}")
        if transport_note:
            formula_parts.append(f"运输：{transport_note}")
        if other_cost > 0:
            formula_parts.append(f"其他费用 {fe.fmt(other_cost)}")
        formula_parts.append(f"总成本 {fe.fmt(total_cost)}")
        formula_parts.append(f"定价依据：{chosen_name}")
        if margin_price > 0 and margin_price >= base_price:
            formula_parts.append(f"保底毛利率 {fe.fmt(target_margin * 100)}% → {fe.fmt(margin_price)}")
        if rounding_adjustment != 0:
            formula_parts.append(f"取整（{rounding_mode}）+{fe.fmt(rounding_adjustment)}")
        formula_parts.append(f"最终售价 {fe.fmt(final_price)}")

        breakdown: dict[str, Any] = {
            "mode": mode,
            "billable_quantity": str(billable),
            "unit_price": str(unit_price),
            "cost_price": str(cost_price),
            "material_cost": str(material_cost),
            "loss_rate": str(loss_rate),
            "loss_cost": str(loss_cost),
            "labor_cost": str(labor_cost),
            "transport_cost": str(transport_cost),
            "other_cost": str(other_cost),
            "total_cost": str(total_cost),
            "rule_price": str(rule_price),
            "margin_price": str(margin_price),
            "target_margin": str(target_margin),
            "markup_rate": str(markup),
            "raw_price": str(raw_price),
            "final_price": str(final_price),
            "rounding_adjustment": str(rounding_adjustment),
            "pricing_basis": chosen_name,
            "applied_rules": applied_rules,
            "tier": tier,
        }

        return QuoteItemCalculation(
            product_id=product.id if product else item.product_id,
            product_name=product.name if product else item.product_name,
            category_name=category.name if category else item.category_name,
            spec=item.spec or (product.spec if product else None),
            unit=item.unit or (product.unit if product else "平方米"),
            plan_level=tier,  # type: ignore[arg-type]
            billable_quantity=billable,
            quantity=item.quantity,
            width=item.width,
            height=item.height,
            depth=item.depth,
            weight=item.weight,
            unit_price=unit_price,
            cost_price=cost_price,
            material_cost=material_cost,
            loss_rate=loss_rate,
            loss_cost=loss_cost,
            labor_cost=labor_cost,
            transport_cost=transport_cost,
            other_cost=other_cost,
            total_cost=total_cost,
            rule_price=rule_price,
            margin_price=margin_price,
            subtotal=final_price,
            profit_margin=profit_margin,
            gross_profit=fe.money(final_price - total_cost),
            final_price=final_price,
            rounding_adjustment=rounding_adjustment,
            formula="；".join(formula_parts),
            applied_rules=applied_rules,
            breakdown=breakdown,
            remark=item.remark,
            match_confidence=match_confidence,
        )

    # ------------------------------------------------------------------
    def calculate(
        self,
        db: Session | None,
        company_id: int | None,
        payload: QuoteInput,
        *,
        tier: str = "standard",
    ) -> QuoteCalculation:
        items: list[QuoteItemCalculation] = []
        for item in payload.items:
            if item.plan_level != tier:
                item = item.model_copy(update={"plan_level": tier})
            items.append(
                self.calculate_item(
                    db,
                    company_id,
                    item,
                    rounding_mode=payload.rounding_mode,
                    global_margin=payload.global_margin,
                    tier=tier,
                )
            )

        subtotal = fe.money(sum((item.final_price for item in items), ZERO))
        total_cost = fe.money(sum((item.total_cost for item in items), ZERO))
        discount = fe.money(payload.discount_amount or ZERO)
        taxable = max(subtotal - discount, ZERO)
        tax_rate = fe.d(payload.tax_rate)
        tax_amount = fe.money(taxable * tax_rate)
        total_amount = fe.money(taxable + tax_amount)
        gross_profit = fe.money(total_amount - tax_amount - total_cost)
        gross_margin = effective_margin(total_amount - tax_amount, total_cost)

        return QuoteCalculation(
            items=items,
            subtotal=subtotal,
            discount_amount=discount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            total_cost=total_cost,
            gross_profit=gross_profit,
            gross_margin=gross_margin,
            rounding_mode=payload.rounding_mode,
        )

    def calculate_tiers(
        self, db: Session | None, company_id: int | None, payload: QuoteInput
    ) -> dict[str, PlanTierResult]:
        """生成经济版 / 标准版 / 高级版三档方案。"""
        results: dict[str, PlanTierResult] = {}
        for level in ("economy", "standard", "premium"):
            calculation = self.calculate(db, company_id, payload, tier=level)
            results[level] = PlanTierResult(
                level=level,  # type: ignore[arg-type]
                name=TIER_NAMES[level],
                total_amount=calculation.total_amount,
                total_cost=calculation.total_cost,
                gross_margin=calculation.gross_margin,
                items=calculation.items,
            )
        return results


pricing_engine = PricingEngine()
