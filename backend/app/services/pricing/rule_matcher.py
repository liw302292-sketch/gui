"""规则匹配：为每个需求项找到产品、单价与适用的价格规则。

规则优先级：产品专属规则 > 分类规则 > 企业通用规则（priority 越小越优先）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.product import PriceRule, Product, ProductCategory


@dataclass
class MatchedProduct:
    product: Product | None
    category: ProductCategory | None
    confidence: float
    reason: str


@dataclass
class RuleOutcome:
    unit_price: Decimal | None = None
    cost_price: Decimal | None = None
    loss_rate: Decimal | None = None
    labor_cost: Decimal | None = None
    labor_price_per_unit: Decimal | None = None
    transport_cost: Decimal | None = None
    other_cost: Decimal | None = None
    min_profit_margin: Decimal | None = None
    markup_rate: Decimal | None = None
    pricing_mode: str | None = None
    applied: list[str] = field(default_factory=list)


def _norm(text: str | None) -> str:
    return (text or "").strip().lower().replace(" ", "")


def find_product(
    db: Session, company_id: int, *, product_name: str | None, category_name: str | None, product_id: int | None = None
) -> MatchedProduct:
    """按产品名/分类名做保守匹配，匹配不到绝不编造产品。"""
    if product_id:
        product = db.scalar(select(Product).where(Product.id == product_id, Product.company_id == company_id))
        if product:
            category = db.get(ProductCategory, product.category_id) if product.category_id else None
            return MatchedProduct(product, category, 1.0, "指定产品 ID 精确匹配")

    target = _norm(product_name)
    category_target = _norm(category_name)

    if not target and not category_target:
        return MatchedProduct(None, None, 0.0, "需求中没有产品信息")

    conditions = []
    if target:
        conditions.append(Product.name.ilike(f"%{product_name}%"))
        conditions.append(Product.model.ilike(f"%{product_name}%"))
    stmt = select(Product).where(Product.company_id == company_id, Product.is_active.is_(True))
    if conditions:
        stmt = stmt.where(or_(*conditions))
    candidates = list(db.scalars(stmt.limit(50)))

    if not candidates and category_target:
        stmt = (
            select(Product)
            .join(ProductCategory, Product.category_id == ProductCategory.id)
            .where(
                Product.company_id == company_id,
                Product.is_active.is_(True),
                ProductCategory.name.ilike(f"%{category_name}%"),
            )
            .limit(20)
        )
        candidates = list(db.scalars(stmt))
        if candidates:
            category = db.get(ProductCategory, candidates[0].category_id)
            return MatchedProduct(candidates[0], category, 0.72, f"按分类「{category_name}」匹配")

    if not candidates:
        # 仅按分类匹配（产品名不认识）
        if category_target:
            category = db.scalar(
                select(ProductCategory).where(
                    ProductCategory.company_id == company_id, ProductCategory.name.ilike(f"%{category_name}%")
                )
            )
            if category:
                return MatchedProduct(None, category, 0.4, f"仅匹配到分类「{category.name}」，需人工确认产品")
        return MatchedProduct(None, None, 0.0, "价格库中没有找到对应产品")

    def score(product: Product) -> tuple[int, int]:
        product_key = _norm(product.name)
        exact = 1 if target and product_key == target else 0
        contains = 1 if target and (target in product_key or product_key in target) else 0
        category_hit = 1 if category_target and product.category and category_target in _norm(product.category.name) else 0
        return (exact * 2 + contains + category_hit, 1)

    best = max(candidates, key=lambda product: score(product)[0])
    best_score = score(best)[0]
    category = db.get(ProductCategory, best.category_id) if best.category_id else None

    if best_score >= 3:
        confidence, reason = 0.96, f"产品名「{best.name}」精确匹配"
    elif best_score == 2:
        confidence, reason = 0.88, f"产品名「{best.name}」高度匹配"
    elif best_score == 1:
        confidence, reason = 0.7, f"产品名「{best.name}」模糊匹配"
    else:
        confidence, reason = 0.5, f"按分类回退匹配「{best.name}」"
    return MatchedProduct(best, category, confidence, reason)


def load_rules(db: Session, company_id: int, product_id: int | None, category_id: int | None) -> list[PriceRule]:
    stmt = select(PriceRule).where(PriceRule.company_id == company_id, PriceRule.is_active.is_(True))
    conditions = []
    if product_id:
        conditions.append(PriceRule.product_id == product_id)
    if category_id:
        conditions.append(PriceRule.category_id == category_id)
    conditions.append(and_(PriceRule.product_id.is_(None), PriceRule.category_id.is_(None)))
    stmt = stmt.where(or_(*conditions)).order_by(PriceRule.priority.asc(), PriceRule.id.asc())
    return list(db.scalars(stmt))


def _condition_pass(conditions: dict[str, Any], context: dict[str, Decimal]) -> bool:
    """条件判断，例如 {"field": "area", "op": ">", "value": 20}。"""
    if not conditions:
        return True
    rules = conditions.get("all") or conditions.get("any")
    if isinstance(rules, list):
        results = []
        for rule in rules:
            field_name = rule.get("field")
            op = rule.get("op", ">")
            expected = Decimal(str(rule.get("value", 0)))
            actual = context.get(field_name, Decimal("0"))
            if op == ">":
                results.append(actual > expected)
            elif op == ">=":
                results.append(actual >= expected)
            elif op == "<":
                results.append(actual < expected)
            elif op == "<=":
                results.append(actual <= expected)
            elif op == "==":
                results.append(actual == expected)
            elif op == "!=":
                results.append(actual != expected)
            else:
                results.append(False)
        return all(results) if conditions.get("all") else any(results)

    # 单条件写法
    field_name = conditions.get("field")
    if not field_name:
        return True
    return _condition_pass({"all": [conditions]}, context)


def apply_rules(
    rules: list[PriceRule], context: dict[str, Decimal]
) -> RuleOutcome:
    outcome = RuleOutcome()
    for rule in rules:
        if not _condition_pass(rule.conditions or {}, context):
            continue
        params = rule.params or {}
        rule_type = rule.rule_type
        touched = False

        def take(key: str, target: str) -> None:
            nonlocal touched
            if key in params and params[key] is not None:
                setattr(outcome, target, Decimal(str(params[key])))
                touched = True

        if rule_type in ("fixed", "area", "volume", "weight", "tiered"):
            take("unit_price", "unit_price")
            outcome.pricing_mode = rule_type if rule_type != "tiered" else outcome.pricing_mode
            take("cost_price", "cost_price")
        elif rule_type == "cost_plus":
            take("markup_rate", "markup_rate")
            outcome.pricing_mode = "cost_plus"
        elif rule_type == "margin":
            take("target_margin", "min_profit_margin")
            outcome.pricing_mode = "margin"
        elif rule_type == "loss":
            take("loss_rate", "loss_rate")
        elif rule_type == "labor":
            take("labor_cost", "labor_cost")
            take("labor_price_per_unit", "labor_price_per_unit")
        elif rule_type == "transport":
            take("transport_cost", "transport_cost")
        elif rule_type == "condition":
            take("unit_price", "unit_price")
            take("cost_price", "cost_price")
            take("loss_rate", "loss_rate")
            take("labor_cost", "labor_cost")
            take("transport_cost", "transport_cost")
            take("other_cost", "other_cost")
            take("min_profit_margin", "min_profit_margin")
            touched = True

        if touched:
            outcome.applied.append(f"{rule.name}({rule_type})")
    return outcome
